"""Tests for different validation message levels."""

import pyformatic


def test_warning_message_display():
    """Warnings are rendered correctly in the HTML."""
    cfg = {
        "name": "step",
        "fields": [{"name": "foo", "label": "Foo"}],
        "validators": {
            "foo": "if value == 'bad':\n    raise ValidationWarning('Warn!')\nreturn value"
        },
    }
    step = pyformatic.formflow.Step(cfg, None, action="/")
    messages, has_error = step.validate({"foo": "bad"}, {})
    assert messages == {"foo": {"level": "warning", "message": "Warn!", "value": "bad"}}
    assert has_error is False
    item = step.form.items[0]
    assert item.message == "Warn!"
    assert "warning" in item.classes_outer
    html = pyformatic.Display(step.form).get_html()
    assert "Warn!" in html
    assert "class=\"warning\"" in html


def test_error_message_display():
    """Errors are rendered correctly in the HTML."""
    cfg = {
        "name": "step",
        "fields": [{"name": "foo", "label": "Foo"}],
        "validators": {
            "foo": "if value == 'bad':\n    raise ValidationError('Bad!')\nreturn value"
        },
    }
    step = pyformatic.formflow.Step(cfg, None, action="/")
    messages, has_error = step.validate({"foo": "bad"}, {})
    assert messages == {"foo": {"level": "error", "message": "Bad!", "value": "bad"}}
    assert has_error is True
    item = step.form.items[0]
    assert item.message == "Bad!"
    assert "error" in item.classes_outer
    html = pyformatic.Display(step.form).get_html()
    assert "Bad!" in html
    assert "class=\"error\"" in html
