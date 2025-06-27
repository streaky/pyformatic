"""Playwright end-to-end test for the multi-step signup demo."""

# pylint: disable=R0801  # shared setup code with other e2e tests

import os
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("DEMO_BASE_URL", "http://demo:8000")


def test_signup_flow():
    """Complete the signup form across all steps."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{BASE_URL}/signup")

        page.fill("input[name=first_name]", "John")
        page.fill("input[name=last_name]", "Doe")
        page.fill("input[name=username]", "john")
        page.fill("input[name=password]", "secret12")
        page.fill("input[name=confirm_password]", "secret12")
        page.fill("input[name=promo]", "PROMO")
        page.click("text=Next")

        page.fill("input[name=email]", "john@example.com")
        page.fill("input[name=phone]", "123456")
        page.click("text=Next")

        page.check("input[name=terms]")
        page.click("text=Submit")
        page.wait_for_load_state("networkidle")

        assert "Done" in page.content()
        browser.close()
