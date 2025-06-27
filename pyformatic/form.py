"""Form container for pyform."""

from __future__ import annotations

from typing import List, Optional

from .elements import BaseElement, Button


class Form:
    """Represents a form and contains elements."""
    # pylint: disable=too-many-instance-attributes  # tracks many field attributes

    def __init__(
        self,
        form_id: str,
        action: str,
        method: str = "POST",
        autocomplete: bool = True,
        validate: Optional[str] = None,
        validate_url: Optional[str] = None,
    ) -> None:
        # pylint: disable=too-many-arguments,too-many-positional-arguments  # constructor mirrors HTML form options
        self.id = form_id
        self.action = action
        self.method = method
        self.autocomplete = autocomplete
        self.validate = validate
        self.validate_url = validate_url
        self.help: str = ""
        self.items: List[BaseElement] = []
        self.buttons: List[Button] = []

    def add_item(self, item: BaseElement) -> None:
        """Add a form element."""
        self.items.append(item)

    def add_button(self, button: Button) -> None:
        """Add a button element."""
        self.buttons.append(button)

    def reset(self) -> None:
        """Reset all elements to default state."""
        for item in self.items:
            item.reset()
