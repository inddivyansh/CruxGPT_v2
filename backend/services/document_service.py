"""
Document service.

Handles the full upload -> validate -> store -> extract -> chunk -> embed ->
index pipeline (spec section 12/13/14/15), plus file-security requirements
from section 31: safe generated filenames (the original filename is only
ever used for display), size/type validation, private object storage,
and per-user ownership checks before any read/delete.
"""
import asyncio
import hashlib
import json
import uuid

from fastapi import UploadFile
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import create_client

from app.config import settings
from app.errors import (
    ConversationNotFoundError,
    DocumentNotFoundError,
    DocumentProcessingFailedError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from models.chunk import DocumentChunk
from models.conversation import Conversation
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

MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024
MAX_CONVERSATION_STORAGE_BYTES = 100 * 1024 * 1024


def _validate_upload(file: UploadFile, size: int) -> None:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise UnsupportedFileTypeError(
            f"'{file.content_type}' is not supported. Allowed types: PDF, DOC, DOCX, TXT."
        )
    if size >= MAX_DOCUMENT_SIZE_BYTES:
        raise FileTooLargeError("File must be smaller than 10 MB. Please upload a file below 10 MB.")


async def _validate_conversation_storage(
    db: AsyncSession, user_id: str, conversation_id: str, file_size: int
) -> None:
    result = await db.execute(
        select(func.coalesce(func.sum(Document.file_size), 0)).where(
            Document.conversation_id == conversation_id,
            Document.user_id == user_id,
        )
    )
    existing_size = result.scalar_one()

    if existing_size + file_size > MAX_CONVERSATION_STORAGE_BYTES:
        remaining_bytes = max(MAX_CONVERSATION_STORAGE_BYTES - existing_size, 0)
        remaining_mib = remaining_bytes / (1024 * 1024)
        raise FileTooLargeError(
            "Adding this file would exceed this conversation's 100 MB document limit. "
            f"{remaining_bytes} bytes ({remaining_mib:.2f} MiB) remain."
        )


def _storage_bucket():
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise DocumentProcessingFailedError("Document storage is not configured on the server.")

    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return client.storage.from_(settings.supabase_storage_bucket)


async def _upload_storage_object(storage_path: str, contents: bytes, mime_type: str) -> None:
    def upload() -> None:
        _storage_bucket().upload(
            path=storage_path,
            file=contents,
            file_options={"content-type": mime_type, "upsert": "false"},
        )

    await asyncio.to_thread(upload)


async def _download_storage_object(storage_path: str) -> bytes:
    def download() -> bytes:
        return _storage_bucket().download(storage_path)

    return await asyncio.to_thread(download)


async def _delete_storage_object(storage_path: str) -> None:
    def delete() -> None:
        _storage_bucket().remove([storage_path])

    try:
        await asyncio.to_thread(delete)
    except Exception:
        pass


async def save_upload(
    db: AsyncSession, user_id: str, file: UploadFile, conversation_id: str
) -> Document:
    contents = await file.read()
    _validate_upload(file, len(contents))

    # Serialize quota checks for this conversation in PostgreSQL. The lock is
    # retained until the document metadata is committed below, so concurrent
    # uploads cannot both pass the same 100 MiB check.
    conversation_result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .with_for_update()
    )
    if conversation_result.scalar_one_or_none() is None:
        raise ConversationNotFoundError()
    await _validate_conversation_storage(db, user_id, conversation_id, len(contents))

    # Safe, unguessable, generated filename - the original filename is never
    # used to build a storage path (prevents path traversal / collisions).
    document_id = str(uuid.uuid4())
    ext = ALLOWED_MIME_TYPES[file.content_type]
    safe_filename = f"{uuid.uuid4()}{ext}"
    storage_path = f"{user_id}/{conversation_id}/{document_id}/{safe_filename}"

    try:
        await _upload_storage_object(storage_path, contents, file.content_type)
    except Exception as exc:
        await _delete_storage_object(storage_path)
        raise DocumentProcessingFailedError("Document upload failed. Please try again.") from exc

    document = Document(
        id=document_id,
        user_id=user_id,
        conversation_id=conversation_id,
        filename=safe_filename,
        original_filename=file.filename or "document",
        mime_type=file.content_type,
        file_size=len(contents),
        content_sha256=hashlib.sha256(contents).hexdigest(),
        embedding_model=settings.gemini_embedding_model,
        status="uploaded",
        storage_path=storage_path,
    )
    db.add(document)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        await _delete_storage_object(storage_path)
        raise
    await db.refresh(document)
    return document


def _has_valid_embedding(chunk: DocumentChunk) -> bool:
    """Validate a stored vector before copying it to another document."""
    if chunk.embedding_dim != settings.gemini_embedding_dimensions or chunk.embedding_dim <= 0:
        return False
    try:
        embedding = json.loads(chunk.embedding_json)
    except (TypeError, json.JSONDecodeError):
        return False
    return (
        isinstance(embedding, list)
        and len(embedding) == chunk.embedding_dim
        and all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in embedding)
    )


def _chunks_are_complete(chunks: list[DocumentChunk]) -> bool:
    return bool(chunks) and all(_has_valid_embedding(chunk) for chunk in chunks)


async def _load_document_chunks(db: AsyncSession, document_id: str) -> list[DocumentChunk]:
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )
    return list(result.scalars().all())


async def _prepare_document_for_indexing(db: AsyncSession, document_id: str) -> Document | None:
    """Claim a document for indexing without keeping a database lock during AI calls."""
    result = await db.execute(select(Document).where(Document.id == document_id).with_for_update())
    document = result.scalar_one_or_none()
    if document is None:
        return None

    existing_chunks = await _load_document_chunks(db, document.id)
    if document.status == "indexed" and _chunks_are_complete(existing_chunks):
        return None
    if document.status == "processing":
        return None

    # A failed or incomplete attempt must not leave rows that a retry could duplicate.
    if existing_chunks:
        await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    document.status = "processing"
    document.error_message = None
    document.embedding_model = settings.gemini_embedding_model
    await db.commit()
    return document


async def _find_reusable_source_document(
    db: AsyncSession, document: Document
) -> tuple[Document, list[DocumentChunk]] | None:
    """Find same-user, same-model, fully indexed content that can be copied safely."""
    if not document.content_sha256:
        return None

    result = await db.execute(
        select(Document)
        .where(
            Document.user_id == document.user_id,
            Document.id != document.id,
            Document.content_sha256 == document.content_sha256,
            Document.status == "indexed",
            Document.embedding_model == settings.gemini_embedding_model,
        )
        .order_by(Document.created_at.asc())
    )
    for source in result.scalars().all():
        source_chunks = await _load_document_chunks(db, source.id)
        if _chunks_are_complete(source_chunks):
            return source, source_chunks
    return None


async def _copy_reusable_chunks(
    db: AsyncSession,
    source: Document,
    source_chunks: list[DocumentChunk],
    destination: Document,
) -> None:
    for chunk in source_chunks:
        db.add(
            DocumentChunk(
                document_id=destination.id,
                user_id=destination.user_id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                page_number=chunk.page_number,
                section=chunk.section,
                embedding_json=chunk.embedding_json,
                embedding_dim=chunk.embedding_dim,
            )
        )
    destination.page_count = source.page_count
    destination.embedding_model = source.embedding_model
    destination.status = "indexed"
    destination.error_message = None
    await db.commit()


async def process_document(db: AsyncSession, document_id: str) -> None:
    """
    Runs the extract -> chunk -> embed -> index pipeline for a document.
    Intended to run as a background task after upload so the API response
    isn't blocked on (potentially slow) embedding calls. Any failure marks
    the document 'failed' with a message instead of leaving it stuck.
    """
    document = await _prepare_document_for_indexing(db, document_id)
    if document is None:
        return

    try:
        reusable_source = await _find_reusable_source_document(db, document)
        if reusable_source is not None:
            source, source_chunks = reusable_source
            await _copy_reusable_chunks(db, source, source_chunks, document)
            return

        contents = await _download_storage_object(document.storage_path)
        blocks = parse_document(contents, document.mime_type)
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
        document.embedding_model = settings.gemini_embedding_model
        document.status = "indexed"
        document.error_message = None
        await db.commit()

    except Exception as exc:
        await db.rollback()
        document_result = await db.execute(select(Document).where(Document.id == document_id))
        document = document_result.scalar_one_or_none()
        if document is None:
            return
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

    await _delete_storage_object(document.storage_path)

    await db.delete(document)
    await db.commit()
