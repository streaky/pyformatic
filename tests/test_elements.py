"""Unit tests for form element behaviours."""

import pyformatic


def test_base_element_reset_and_id():
    """Reset should restore defaults and update the derived ID."""
    element = pyformatic.TextInput(name="foo", label="Foo", element_id="bar")
    element.value = "data"
    element.classes_outer.extend(["error", "info"])
    element.classes_input.append("x")
    element.message = "Bad"
    assert element.id == "bar"

    element.reset()
    assert element.value == ""
    assert element.classes_outer == []
    assert element.classes_input == []
    assert element.message is None

    element.element_id = None
    assert element.id == "foo"
