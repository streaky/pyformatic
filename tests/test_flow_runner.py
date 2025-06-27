"""Integration tests for the form flow runner."""

from pathlib import Path
import asyncio

import pyformatic
from tests import helpers


class DummyRequest:
    """Minimal async request-like object used in tests."""

    def __init__(
        self,
        method="GET",
        headers=None,
        json_data=None,
        form_data=None,
        session=None,
    ):  # pylint: disable=too-many-arguments,too-many-positional-arguments  # test helper
        self.method = method
        self.headers = headers or {}
        self._json_data = json_data or {}
        self._form_data = form_data or {}
        self.session = session

    async def json(self):
        """Return stored JSON data."""
        return self._json_data

    async def form(self):
        """Return stored form data."""
        return self._form_data


def test_run_form_flow_complete():
    """Complete flow returns final data after submission."""
    yaml_file = Path(__file__).parent.parent / "demo" / "user_login.yaml"
    form_flow = pyformatic.FormFlow.from_yaml(str(yaml_file), action="/login")
    # initial GET
    req = DummyRequest()
    state, body = asyncio.run(pyformatic.run_form_flow(form_flow, req))
    assert state == "form"
    assert "username" in body

    # submit valid data
    req = DummyRequest(
        method="POST",
        headers={"content-type": "application/x-www-form-urlencoded"},
        form_data={"username": "john", "password": "secret12", "submit": "Submit"},
    )
    state, data = asyncio.run(pyformatic.run_form_flow(form_flow, req))
    assert state == "complete"
    assert data["username"] == "john"
    assert data["password"] == "secret12"


def test_run_form_flow_error_banner():
    """Form flow adds banner when validation fails."""
    yaml_file = Path(__file__).parent.parent / "demo" / "user_login.yaml"
    form_flow = pyformatic.FormFlow.from_yaml(str(yaml_file), action="/login")

    req = DummyRequest(
        method="POST",
        headers={"content-type": "application/x-www-form-urlencoded"},
        form_data={"username": "", "password": "123", "submit": "Submit"},
    )
    state, body = asyncio.run(pyformatic.run_form_flow(form_flow, req))
    assert state == "form"
    assert "error-banner" in body
    assert "Please check Username" in body
    assert "Username required" in body


def test_run_form_flow_ajax_validation():
    """AJAX validation requests return structured payloads."""
    yaml_file = Path(__file__).parent.parent / "demo" / "user_login.yaml"
    form_flow = pyformatic.FormFlow.from_yaml(str(yaml_file), action="/login")

    req = DummyRequest(
        method="POST",
        headers={"content-type": "application/json"},
        json_data={"field": "username", "value": ""},
    )
    state, payload = asyncio.run(pyformatic.run_form_flow(form_flow, req))
    assert state == "validation"
    assert payload["level"] == "error"
    assert payload["message"] == "Username required"


def test_run_form_flow_multistep_progression():
    """Flow progresses through steps and stores state."""
    yaml_file = Path(__file__).parent.parent / "demo" / "user_signup.yaml"
    form_flow = pyformatic.FormFlow.from_yaml(str(yaml_file), action="/signup")

    req = DummyRequest()
    state, body = asyncio.run(pyformatic.run_form_flow(form_flow, req))
    assert state == "form"
    assert "step_one" in body

    req = DummyRequest(
        method="POST",
        headers={"content-type": "application/x-www-form-urlencoded"},
        form_data=helpers.step_one_data(),
    )
    state, body = asyncio.run(pyformatic.run_form_flow(form_flow, req))
    assert state == "form"
    assert "step_two" in body

    req = DummyRequest(
        method="POST",
        headers={"content-type": "application/x-www-form-urlencoded"},
        form_data=helpers.step_two_data(),
    )
    state, body = asyncio.run(pyformatic.run_form_flow(form_flow, req))
    assert state == "form"
    assert "step_three" in body

    req = DummyRequest(
        method="POST",
        headers={"content-type": "application/x-www-form-urlencoded"},
        form_data=helpers.final_step_data(),
    )
    state, data = asyncio.run(pyformatic.run_form_flow(form_flow, req))
    assert state == "complete"
    assert data["username"] == "john"
    assert data["email"] == "john@example.com"


def test_run_form_flow_csrf_token_required():
    """Flow includes and checks CSRF tokens when session is present."""
    yaml_file = Path(__file__).parent.parent / "demo" / "user_login.yaml"
    form_flow = pyformatic.FormFlow.from_yaml(str(yaml_file), action="/login")

    session = {}
    req = DummyRequest(session=session)
    state, body = asyncio.run(pyformatic.run_form_flow(form_flow, req))
    assert state == "form"
    token = session.get("_pyformatic_csrf_token")
    assert token in body

    form_data = {
        "username": "john",
        "password": "secret12",
        "submit": "Submit",
        "csrf_token": token,
    }
    req = DummyRequest(
        method="POST",
        headers={"content-type": "application/x-www-form-urlencoded"},
        form_data=form_data,
        session=session,
    )
    state, data = asyncio.run(pyformatic.run_form_flow(form_flow, req))
    assert state == "complete"
    assert data["username"] == "john"
