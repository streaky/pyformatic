"""Tests for populating validator instances with extra context."""

import sys
from types import ModuleType

import pyformatic
from pyformatic import ValidationError


def test_validator_context_available():
    """Inline context is set on validator instances."""
    module_base = "dummyapp"
    step_name = "step"
    mod_name = f"{module_base}.validators.{step_name}"

    base_mod = ModuleType(module_base)
    validators_pkg = ModuleType(f"{module_base}.validators")
    step_mod = ModuleType(mod_name)

    class Validator:  # pylint: disable=too-few-public-methods  # minimal stub for tests
        """Simple validator used for testing."""

        flag: bool
        prefix: str

        def sample(self, value: str) -> str:
            """Return the value prefixed if flag set, else raise error."""
            if not self.flag:
                raise ValidationError('flag missing')
            return self.prefix + value

    step_mod.Validator = Validator

    sys.modules[module_base] = base_mod
    sys.modules[f"{module_base}.validators"] = validators_pkg
    sys.modules[mod_name] = step_mod

    cfg = {"name": step_name, "fields": [{"name": "sample"}]}
    step = pyformatic.formflow.Step(
        cfg,
        module_base,
        action="/",
        validator_context={"flag": True, "prefix": "ok-"},
    )
    val, level, msg = step.validate_field("sample", "data", {})
    assert val == "ok-data"
    assert level == "ok"
    assert msg == ""
