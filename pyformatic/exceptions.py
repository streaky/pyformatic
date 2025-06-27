"""Custom exception hierarchy used during validation."""


class ValidationMessage(Exception):
    """Base class for validation messages raised by validators."""

    level = "info"

    def __init__(self, message: str, value: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.value = value


class ValidationInfo(ValidationMessage):
    """Informational validation message."""

    level = "info"


class ValidationWarning(ValidationMessage):
    """Warning level validation message."""

    level = "warning"


class ValidationError(ValidationMessage):
    """Error level validation message."""

    level = "error"
