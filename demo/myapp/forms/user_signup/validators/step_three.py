"""Acceptance of terms validation step."""

# pylint: disable=too-few-public-methods,R0801 \
# simple single-method validator; pattern matches other steps

from pyformatic import ValidationError


class Validator:
    """Validate that the user agreed to the terms of service."""

    def terms(self, value: str) -> str:
        """Return the value if the terms checkbox was ticked."""
        if value != 'on':
            raise ValidationError("You must agree to the terms")
        return value
