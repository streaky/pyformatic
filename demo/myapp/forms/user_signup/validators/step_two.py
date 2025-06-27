"""Email validation step for user sign up."""

# pylint: disable=too-few-public-methods,R0801 \
# simple single-method validator; email step mirrors other steps

from pyformatic import ValidationError


class Validator:
    """Validate the email address entered by the user."""

    def email(self, value: str) -> str:
        """Return a stripped email if valid."""
        cleaned = value.strip()
        if not cleaned:
            raise ValidationError("Email required")
        if "@" not in cleaned:
            raise ValidationError("Invalid email")
        return cleaned
