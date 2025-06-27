"""Tests for validators defined inline in configuration."""

import pyformatic


def test_inline_validator_string():
    """Inline validator from string works as expected."""
    cfg = {
        "name": "step",
        "fields": [{"name": "foo"}],
        "validators": {
            "foo": "if not value:\n    raise ValidationError('missing')\nreturn value.upper()",
        },
    }
    step = pyformatic.formflow.Step(cfg, None, action="/")
    _val, level, msg = step.validate_field("foo", "", {})
    assert level == "error"
    assert msg == "missing"
    val, level, msg = step.validate_field("foo", "bar", {})
    assert val == "BAR"
    assert level == "ok"
    assert msg == ""


def test_inline_validator_callable():
    """Inline validator from callable is invoked."""
    def check(value, data):
        if value != data.get("expect"):
            raise pyformatic.ValidationError("bad")
        return value

    cfg = {
        "name": "step",
        "fields": [{"name": "foo", "validator": check}],
    }
    step = pyformatic.formflow.Step(cfg, None, action="/")
    val, level, msg = step.validate_field("foo", "ok", {"expect": "ok"})
    assert val == "ok"
    assert level == "ok"
    _val, level, msg = step.validate_field("foo", "no", {"expect": "ok"})
    assert level == "error"
    assert msg == "bad"


def test_validate_field_with_extra_data():
    """Extra data passed to validators is respected."""
    cfg = {
        "name": "step",
        "fields": [
            {"name": "password"},
            {"name": "confirm"},
        ],
        "validators": {
            "confirm": (
                "if value != data_store.get('password'):\n"
                "    raise ValidationError('mismatch')"
            ),
        },
    }
    step = pyformatic.formflow.Step(cfg, None, action="/")
    _val, level, msg = step.validate_field(
        "confirm",
        "secret",
        {},
        extra_fields={"password": "secret"},
    )
    assert level == "ok"
    _val, level, msg = step.validate_field(
        "confirm",
        "wrong",
        {},
        extra_fields={"password": "secret"},
    )
    assert level == "error"
    assert msg == "mismatch"
