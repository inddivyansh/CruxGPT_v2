"""
Consistent error responses across the API.

Every error the API raises intentionally should be an AppError, which
FastAPI's exception handler (registered in main.py) turns into:

{
  "error": { "code": "DOCUMENT_NOT_FOUND", "message": "..." }
}
"""
from fastapi import status


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidFileError(AppError):
    def __init__(self, message: str = "The uploaded file is invalid."):
        super().__init__("INVALID_FILE", message, status.HTTP_400_BAD_REQUEST)


class FileTooLargeError(AppError):
    def __init__(self, message: str = "The uploaded file exceeds the size limit."):
        super().__init__("FILE_TOO_LARGE", message, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)


class UnsupportedFileTypeError(AppError):
    def __init__(self, message: str = "This file type is not supported."):
        super().__init__("UNSUPPORTED_FILE_TYPE", message, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)


class DocumentProcessingFailedError(AppError):
    def __init__(self, message: str = "The document could not be processed."):
        super().__init__("DOCUMENT_PROCESSING_FAILED", message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class EmbeddingFailedError(AppError):
    def __init__(self, message: str = "Embedding generation failed."):
        super().__init__("EMBEDDING_FAILED", message, status.HTTP_502_BAD_GATEWAY)


class VectorSearchFailedError(AppError):
    def __init__(self, message: str = "Vector search failed."):
        super().__init__("VECTOR_SEARCH_FAILED", message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class LLMError(AppError):
    def __init__(self, message: str = "The AI model failed to generate a response."):
        super().__init__("LLM_ERROR", message, status.HTTP_502_BAD_GATEWAY)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication is required."):
        super().__init__("UNAUTHORIZED", message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AppError):
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__("FORBIDDEN", message, status.HTTP_403_FORBIDDEN)


class ConversationNotFoundError(AppError):
    def __init__(self, message: str = "The requested conversation could not be found."):
        super().__init__("CONVERSATION_NOT_FOUND", message, status.HTTP_404_NOT_FOUND)


class DocumentNotFoundError(AppError):
    def __init__(self, message: str = "The requested document could not be found."):
        super().__init__("DOCUMENT_NOT_FOUND", message, status.HTTP_404_NOT_FOUND)


class DuplicateEmailError(AppError):
    def __init__(self, message: str = "An account with this email already exists."):
        super().__init__("DUPLICATE_EMAIL", message, status.HTTP_409_CONFLICT)


class InvalidCredentialsError(AppError):
    def __init__(self, message: str = "Invalid email or password."):
        super().__init__("INVALID_CREDENTIALS", message, status.HTTP_401_UNAUTHORIZED)
