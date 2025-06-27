"""Utility helpers for executing a :class:`~pyformatic.formflow.FormFlow`."""
from __future__ import annotations

from typing import Any, Tuple

from .csrf import ensure_csrf_token, validate_csrf_token

from .formflow import FormFlow, RequestLike


async def run_form_flow(
    form_flow: FormFlow,
    request: RequestLike,
) -> Tuple[str, Any]:
    """Handle a request for a multi-step form.

    Parameters
    ----------
    form_flow:
        The :class:`~pyformatic.formflow.FormFlow` instance to operate on.
    request:
        An object providing ``method``, ``headers`` and ``json``/``form``
        coroutine methods.

    Returns
    -------
    tuple
        ``("validation", payload)`` for AJAX validation requests,
        ``("form", html)`` for form pages and ``("complete", data)`` when the
        flow has finished.
    """
    data_store: dict[str, Any] = {}
    try:
        session = getattr(request, "session")
    except (AttributeError, AssertionError):
        session = None
    csrf_token = ensure_csrf_token(session) if session is not None else None

    if form_flow.is_validation_request(request):
        payload = await request.json()
        data_store = payload.get("fields", {})
        data_store[payload.get("field", "")] = payload.get("value", "")
        _is_val, payload = await form_flow.handle_request(request, data_store)
        assert _is_val is True
        return "validation", payload

    if request.method == "POST":
        form_data = await request.form()
        if session is not None:
            if not validate_csrf_token(session, form_data.get("csrf_token", "")):
                html = form_flow.render(0, data_store=data_store, csrf_token=csrf_token)
                return "form", html
        for k, v in form_data.items():
            if k not in {"next", "submit", "csrf_token"}:
                data_store[k] = v
        _is_val, result = await form_flow.handle_request(request, data_store)
        assert not _is_val
        step_index, messages, has_error = result
        if step_index >= form_flow.num_steps:
            return "complete", data_store
        if has_error:
            html = form_flow.render(step_index, messages, data_store, csrf_token=csrf_token)
        else:
            html = form_flow.render(step_index, data_store=data_store, csrf_token=csrf_token)
        return "form", html

    html = form_flow.render(0, data_store=data_store, csrf_token=csrf_token)
    return "form", html
