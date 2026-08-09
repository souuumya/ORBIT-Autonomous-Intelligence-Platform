class AppException(Exception):
    """Base exception for application-level errors."""


class NotFoundError(AppException):
    """Raised when a requested resource cannot be found."""


class ValidationError(AppException):
    """Raised when input validation fails."""


class MissionEngineError(AppException):
    """Raised when the mission engine cannot process a mission request."""
