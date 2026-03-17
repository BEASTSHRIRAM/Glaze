"""Custom exception classes for Glaze."""


class GlazeError(Exception):
    """Base exception for Glaze application."""
    pass


# Authentication errors
class AuthenticationError(GlazeError):
    """OAuth flow failed or token invalid."""
    pass


class TokenExpiredError(AuthenticationError):
    """Access token expired and refresh failed."""
    pass


# File processing errors
class FileProcessingError(GlazeError):
    """Failed to extract text from file."""
    pass


class UnsupportedFileTypeError(FileProcessingError):
    """File MIME type not supported."""
    pass


class FileSizeExceededError(FileProcessingError):
    """File exceeds maximum size limit."""
    pass


# Embedding errors
class EmbeddingError(GlazeError):
    """Failed to generate embedding."""
    pass


class RateLimitError(EmbeddingError):
    """API rate limit exceeded."""
    pass


class QuotaExceededError(EmbeddingError):
    """API quota exhausted."""
    pass


# Storage errors
class StorageError(GlazeError):
    """Failed to store data."""
    pass


class QdrantConnectionError(StorageError):
    """Cannot connect to Qdrant."""
    pass


class DatabaseError(StorageError):
    """SQLite operation failed."""
    pass


# User-friendly error messages
ERROR_MESSAGES = {
    "auth_failed": "Authentication failed. Please try logging in again.",
    "drive_unavailable": "Cannot connect to Google Drive. Please check your connection.",
    "indexing_failed": "Some files could not be indexed. See details below.",
    "search_failed": "Search failed. Please try again.",
    "rate_limit": "Too many requests. Please wait a moment and try again.",
    "quota_exceeded": "API quota exceeded. Please try again later.",
    "unsupported_file": "This file type is not supported.",
    "file_too_large": "File is too large to process.",
    "no_text_content": "No text content could be extracted from this file.",
    "qdrant_unavailable": "Vector database is unavailable. Please try again later.",
    "database_error": "Database error occurred. Please try again."
}


def get_user_friendly_message(error: Exception) -> str:
    """
    Get user-friendly error message for an exception.
    
    Args:
        error: Exception instance
        
    Returns:
        User-friendly error message
    """
    if isinstance(error, AuthenticationError):
        return ERROR_MESSAGES["auth_failed"]
    elif isinstance(error, RateLimitError):
        return ERROR_MESSAGES["rate_limit"]
    elif isinstance(error, QuotaExceededError):
        return ERROR_MESSAGES["quota_exceeded"]
    elif isinstance(error, UnsupportedFileTypeError):
        return ERROR_MESSAGES["unsupported_file"]
    elif isinstance(error, FileSizeExceededError):
        return ERROR_MESSAGES["file_too_large"]
    elif isinstance(error, QdrantConnectionError):
        return ERROR_MESSAGES["qdrant_unavailable"]
    elif isinstance(error, DatabaseError):
        return ERROR_MESSAGES["database_error"]
    else:
        return "An unexpected error occurred. Please try again."
