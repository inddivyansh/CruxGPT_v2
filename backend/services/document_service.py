"""
Document service.

Handles the full upload -> validate -> store -> extract -> chunk -> embed ->
index pipeline (spec section 12/13/14/15), plus file-security requirements
from section 31: safe generated filenames (the original filename is only
ever used for display), size/type validation, storage outside any web root,
and per-user ownership checks before any read/delete.
"""
import json
import os
import uuid

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.errors import DocumentNotFoundError, FileTooLargeError, UnsupportedFileTypeError
from models.chunk import DocumentChunk
from models.document import Document
from rag.chunker import chunk_blocks
from rag.embeddings import get_embedding_service
from rag.parser import parse_document

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "text/plain": ".txt",
}


def _validate_upload(file: UploadFile, size: int) -> None:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise UnsupportedFileTypeError(
            f"'{file.content_type}' is not supported. Allowed types: PDF, DOC, DOCX, TXT."
        )
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if size > max_bytes:
        raise FileTooLargeError(f"File exceeds the {settings.max_file_size_mb}MB limit.")


async def save_upload(db: AsyncSession, user_id: str, file: UploadFile) -> Document:
    contents = await file.read()
    _validate_upload(file, len(contents))

    os.makedirs(settings.storage_path, exist_ok=True)

    # Safe, unguessable, generated filename - the original filename is never
    # used to build a filesystem path (prevents path traversal / collisions).
    ext = ALLOWED_MIME_TYPES[file.content_type]
    safe_filename = f"{uuid.uuid4()}{ext}"
    storage_path = os.path.join(settings.storage_path, safe_filename)

    with open(storage_path, "wb") as f:
        f.write(contents)

    document = Document(
        user_id=user_id,
        filename=safe_filename,
        original_filename=file.filename or "document",
        mime_type=file.content_type,
        file_size=len(contents),
        status="uploaded",
        storage_path=storage_path,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


async def process_document(db: AsyncSession, document_id: str) -> None:
    """
    Runs the extract -> chunk -> embed -> index pipeline for a document.
    Intended to run as a background task after upload so the API response
    isn't blocked on (potentially slow) embedding calls. Any failure marks
    the document 'failed' with a message instead of leaving it stuck.
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        return

    document.status = "processing"
    await db.commit()

    try:
        blocks = parse_document(document.storage_path, document.mime_type)
        chunks = chunk_blocks(blocks)
        if not chunks:
            raise ValueError("No chunkable content extracted from document.")

        embedding_service = get_embedding_service()
        embeddings = await embedding_service.embed_documents([c.text for c in chunks])

        for chunk, embedding in zip(chunks, embeddings):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    user_id=document.user_id,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    embedding_json=json.dumps(embedding),
                    embedding_dim=len(embedding),
                )
            )

        page_numbers = [b.page_number for b in blocks if b.page_number]
        document.page_count = max(page_numbers) if page_numbers else None
        document.status = "indexed"
        document.error_message = None
        await db.commit()

    except Exception as exc:
        document.status = "failed"
        document.error_message = str(exc)[:500]
        await db.commit()


async def get_user_document(db: AsyncSession, user_id: str, document_id: str) -> Document:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise DocumentNotFoundError()
    if document.user_id != user_id:
        # Deliberately reported as "not found" rather than "forbidden" so
        # existence of other users' documents is never leaked.
        raise DocumentNotFoundError()
    return document


async def list_user_documents(db: AsyncSession, user_id: str) -> list[Document]:
    result = await db.execute(
        select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_document(db: AsyncSession, user_id: str, document_id: str) -> None:
    document = await get_user_document(db, user_id, document_id)

    chunk_result = await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    for chunk in chunk_result.scalars().all():
        await db.delete(chunk)

    if os.path.exists(document.storage_path):
        try:
            os.remove(document.storage_path)
        except OSError:
            pass  # File already gone / permissions issue - don't block the delete

    await db.delete(document)
    await db.commit()
