"""Field validation for the first signup step."""

from pyformatic import ValidationError, ValidationInfo


class Validator:
    """Validate username and password fields."""

    def username(self, value: str) -> str:
        """Return a cleaned username if valid."""
        cleaned = value.strip()
        if not cleaned:
            raise ValidationError("Username required")
        if cleaned != value:
            raise ValidationInfo("I adjusted your username", cleaned)
        return cleaned

    def password(self, value: str) -> str:
        """Ensure the password is long enough."""
        if len(value) < 6:
            raise ValidationError("Password must be at least 6 characters")
        return value

    def confirm_password(self, value: str, session_data: dict) -> str:
        """Check that the password confirmation matches."""
        if value != session_data.get("password"):
            raise ValidationError("Passwords do not match")
        return value
