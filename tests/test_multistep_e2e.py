"""End-to-end tests for the multi-step signup flow."""

from fastapi.testclient import TestClient
from demo.main import app
from tests import helpers

client = TestClient(app)


def test_multistep_flow():
    """Walk through the full signup process."""
    resp = client.get("/signup")
    assert resp.status_code == 200
    assert "step_one" in resp.text

    resp = client.post(
        "/signup",
        data=helpers.step_one_data(),
    )
    assert resp.status_code == 200
    assert "step_two" in resp.text

    resp = client.post(
        "/signup",
        data=helpers.step_two_data(),
    )
    assert resp.status_code == 200
    assert "step_three" in resp.text

    resp = client.post(
        "/signup",
        data=helpers.final_step_data(),
    )
    assert resp.status_code == 200
    assert "Done" in resp.text
