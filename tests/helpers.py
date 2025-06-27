# Helpers for test data used across modules.

"""Utility functions returning common signup form data."""


SIGNUP_BASE_DATA = {
    "username": "john",
    "password": "secret12",
    "confirm_password": "secret12",
}


def step_one_data():
    """Return data for the first signup step."""
    return {**SIGNUP_BASE_DATA, "next": "Next"}


def step_two_data():
    """Return data for the second signup step."""
    return {**step_one_data(), "email": "john@example.com"}


def final_step_data():
    """Return data for the final signup submission."""
    return {**step_two_data(), "terms": "on", "submit": "Submit"}
