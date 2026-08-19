from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.dependencies import get_current_user
from models.user import User
from schemas.document import DocumentResponse
from services import document_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


async def _process_in_background(document_id: str):
    # Background tasks get their own DB session - the request-scoped one is
    # closed by the time this runs.
    async with AsyncSessionLocal() as db:
        await document_service.process_document(db, document_id)


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await document_service.save_upload(db, user.id, file)
    background_tasks.add_task(_process_in_background, document.id)
    return document


@router.get("", response_model=list[DocumentResponse])
async def list_documents(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await document_service.list_user_documents(db, user.id)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await document_service.get_user_document(db, user.id, document_id)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await document_service.delete_document(db, user.id, document_id)
    return None
