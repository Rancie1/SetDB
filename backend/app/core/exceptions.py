"""
Custom exception classes for the SetDB application.

These exceptions can be raised in the application and handled by
FastAPI's exception handlers to return appropriate HTTP responses.
"""

from fastapi import HTTPException, status


class DeckdException(HTTPException):
    """Base exception class for SetDB-specific errors."""
    pass


class SetNotFoundError(DeckdException):
    """Raised when a DJ set is not found."""
    
    def __init__(self, set_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DJ set with ID {set_id} not found"
        )


class UnauthorizedError(DeckdException):
    """Raised when user is not authenticated."""
    
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class ForbiddenError(DeckdException):
    """Raised when user doesn't have permission."""
    
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class DuplicateEntryError(DeckdException):
    """Raised when trying to create a duplicate entry."""
    
    def __init__(self, detail: str = "Entry already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class ExternalAPIError(DeckdException):
    """Raised when external API call fails."""
    
    def __init__(self, detail: str = "External API error"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail
        )


class ValidationError(DeckdException):
    """Raised when validation fails."""
    
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


