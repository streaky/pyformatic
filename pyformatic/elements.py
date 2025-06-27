"""Form elements used by pyform."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class BaseElement:
    """Base class for all form elements."""
    # pylint: disable=too-many-instance-attributes  # dataclass with many UI fields

    name: str
    label: str
    value: str = ""
    element_id: Optional[str] = None
    help: str = ""
    placeholder: str = ""
    include: List[str] = field(default_factory=list)
    classes_outer: List[str] = field(default_factory=list)
    classes_input: List[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)
    message: Optional[str] = None

    def reset(self) -> None:
        """Reset value and classes to their defaults."""
        self.value = ""
        self.classes_outer.clear()
        self.classes_input.clear()
        self.message = None

    @property
    def id(self) -> str:
        """Return HTML element id."""
        return self.element_id or self.name


@dataclass
class InputElement(BaseElement):
    """Base element for input fields."""

    input_type: str = "text"
    options: List[Tuple[str, str]] = field(default_factory=list)
    rows: int = 3


@dataclass
class TextInput(InputElement):
    """Simple text input."""

    input_type: str = "text"


@dataclass
class Button(BaseElement):
    """Simple form button."""

    button_type: str = "submit"


@dataclass
class RawInput(InputElement):
    """Custom HTML used in place of the input element."""

    html: str = ""


@dataclass
class RawElement(BaseElement):
    """Raw HTML snippet replacing the entire element wrapper."""

    html: str = ""
