"""Playwright check for the demo home page."""

import os
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("DEMO_BASE_URL", "http://demo:8000")

def test_homepage():
    """Ensure the home page loads correctly."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{BASE_URL}/")
        assert "Home" in page.content()
        browser.close()
