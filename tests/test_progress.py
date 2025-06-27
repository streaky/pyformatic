"""Tests for progress bar display in form flows."""

import yaml
import pyformatic
from pyformatic.formflow import Step


def _make_simple_step(action: str) -> Step:
    """Return a single-step flow configuration."""
    cfg = {
        "name": "step",
        "fields": [{"name": "username", "type": "text", "label": "User"}],
    }
    return Step(cfg, "demo.myapp.forms.user_signup", action, is_last=True)


def test_progress_disabled_by_default():
    """Validate no progress bar is rendered when not configured."""
    step = _make_simple_step("/test")
    flow = pyformatic.FormFlow([step])
    html = flow.render(0)
    assert "progress-bar" not in html


def test_progress_enabled_via_yaml(tmp_path):
    """Validate progress bar rendering from YAML configuration."""
    cfg = {
        "module": "demo.myapp.forms.user_signup",
        "show_progress": True,
        "steps": [
            {
                "name": "step",
                "fields": [
                    {"name": "username", "type": "text", "label": "User"},
                ],
            }
        ],
    }
    yaml_file = tmp_path / "cfg.yaml"
    yaml_file.write_text(yaml.dump(cfg))
    flow = pyformatic.FormFlow.from_yaml(str(yaml_file), action="/test")
    html = flow.render(0)
    assert "progress-bar" in html
