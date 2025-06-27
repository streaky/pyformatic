"""Playwright tests for client-side field validation."""

# pylint: disable=R0801  # shared setup code with other e2e tests

import os
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("DEMO_BASE_URL", "http://demo:8000")


def test_username_ajax_validation():
    """Validate username field via AJAX."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{BASE_URL}/signup")
        username = page.locator("input[name=username]")
        username.fill(" john ")
        with page.expect_request("**/signup") as req_info:
            username.blur()
        req = req_info.value
        assert req.method == "POST"
        assert req.post_data_json == {"field": "username", "value": " john "}
        resp = req.response()
        assert resp.status == 200
        data = resp.json()
        assert data["level"] == "info"
        assert data["message"] == "I adjusted your username"
        assert data["value"] == "john"
        browser.close()


def test_confirm_password_ajax_validation():
    """Validate confirm password field via AJAX."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{BASE_URL}/signup")
        page.locator("input[name=password]").fill("secret12")
        confirm = page.locator("input[name=confirm_password]")
        confirm.fill("bad")
        with page.expect_request("**/signup") as req_info:
            confirm.blur()
        req = req_info.value
        assert req.post_data_json == {
            "field": "confirm_password",
            "value": "bad",
            "fields": {"password": "secret12"},
        }
        resp = req.response()
        assert resp.status == 200
        data = resp.json()
        assert data["level"] == "error"
        assert data["message"] == "Passwords do not match"
        browser.close()
