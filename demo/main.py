"""Demo application to showcase Pyformatic forms."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from pyformatic.formflow import Step

import pyformatic

app = FastAPI()
static_dir = Path(__file__).with_name("static")
app.mount(
    "/static",
    StaticFiles(directory=str(static_dir), packages=[("pyformatic", "static")]),
    name="static",
)


TEMPLATE_DIR = Path(__file__).with_name("templates")
env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)
pyformatic.Display.setup_jinja(env)


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Return the landing page."""
    tpl = env.get_template("index.html")
    html = tpl.render(title="Home")
    return HTMLResponse(html)


@app.api_route("/login", methods=["GET", "POST"])
async def login_demo(request: Request):
    """Serve and process the login form demo."""
    login_yaml_file = Path(__file__).with_name("user_login.yaml")
    login_form = pyformatic.FormFlow.from_yaml(
        str(login_yaml_file),
        action="/login",
    )
    state, result = await pyformatic.run_form_flow(login_form, request)
    if state == "validation":
        return JSONResponse(result)
    if state == "complete":
        tpl = env.get_template("done.html")
        html = tpl.render(title="Complete", data=result)
        return HTMLResponse(html)
    tpl = env.get_template("form.html")
    html = tpl.render(title="Login Form Demo", form_html=result)
    return HTMLResponse(html)


@app.api_route("/signup", methods=["GET", "POST"])
async def signup_demo(request: Request):
    """Display the multi-step signup demo configured via YAML."""
    signup_yaml_file = Path(__file__).with_name("user_signup.yaml")
    signup_form = pyformatic.FormFlow.from_yaml(
        str(signup_yaml_file),
        action="/signup",
        template_dirs=[str(Path(__file__).with_name("templates") / "pyformatic")],
    )
    for item in signup_form.steps[0].form.items:
        if item.name in {"password", "confirm_password"}:
            item.classes_outer.append("password-field")
    state, result = await pyformatic.run_form_flow(signup_form, request)
    if state == "validation":
        return JSONResponse(result)
    if state == "complete":
        tpl = env.get_template("done.html")
        html = tpl.render(title="Complete", data=result)
        return HTMLResponse(html)
    tpl = env.get_template("form.html")
    html = tpl.render(title="Multi-Step Signup Form Demo", form_html=result)
    return HTMLResponse(html)


@app.api_route("/signup-python", methods=["GET", "POST"])
async def signup_python_demo(request: Request):
    """Show a signup form built purely in Python."""
    py_steps_cfg = [
        {
            "name": "step_one",
            "title": "Step One",
            "description": "This is the first step of the user signup process.",
            "fields": [
                {"name": "first_name", "type": "text", "label": "First Name", "required": True},
                {"name": "last_name", "type": "text", "label": "Last Name", "required": True},
                {"name": "username", "type": "text", "label": "Username", "required": True},
                {"name": "password", "type": "password", "label": "Password", "required": True},
                {
                    "name": "confirm_password",
                    "type": "password",
                    "label": "Confirm Password",
                    "required": True,
                    "include": ["password"],
                },
                {
                    "type": "raw_html",
                    "html": (
                        "<div class='signup-banner'>"
                        "<img src='/static/logo.svg' alt='Signup'></div>"
                    ),
                },
                {
                    "name": "promo",
                    "type": "raw_input",
                    "html": "<label for='promo'>Promo Code</label><input id='promo' name='promo'>",
                },
            ],
        },
        {
            "name": "step_two",
            "title": "Step Two",
            "description": "This is the second step of the user signup process.",
            "fields": [
                {
                    "name": "email",
                    "type": "email",
                    "label": "Email Address",
                    "required": True,
                    "validator": (
                        "cleaned = value.strip()\n"
                        "if not cleaned:\n"
                        "    raise ValidationError('Email required')\n"
                        "if '@' not in cleaned:\n"
                        "    raise ValidationError('Invalid email')\n"
                        "return cleaned"
                    ),
                },
                {"name": "phone", "type": "text", "label": "Phone Number", "required": True}
            ],
        },
        {
            "name": "step_three",
            "title": "Step Three",
            "description": "This is the final step of the user signup process.",
            "fields": [
                {
                    "name": "terms",
                    "type": "checkbox",
                    "label": "I agree to the terms and conditions",
                    "required": True,
                },
                {
                    "name": "marketing",
                    "type": "checkbox",
                    "label": "Send me occasional product updates",
                }
            ],
        },
    ]

    signup_form_py = pyformatic.FormFlow(
        [
            Step(
                cfg,
                "demo.myapp.forms.user_signup",
                action="/signup-python",
                is_last=i == len(py_steps_cfg) - 1,
            )
            for i, cfg in enumerate(py_steps_cfg)
        ],
        template_dirs=[str(Path(__file__).with_name("templates") / "pyformatic")],
    )

    for item in signup_form_py.steps[0].form.items:
        if item.name in {"password", "confirm_password"}:
            item.classes_outer.append("password-field")

    state, result = await pyformatic.run_form_flow(signup_form_py, request)
    if state == "validation":
        return JSONResponse(result)
    if state == "complete":
        tpl = env.get_template("done.html")
        html = tpl.render(title="Complete", data=result)
        return HTMLResponse(html)
    tpl = env.get_template("form.html")
    html = tpl.render(title="Multi-Step Signup Form (No YAML) Demo", form_html=result)
    return HTMLResponse(html)


@app.api_route("/elements", methods=["GET", "POST"])
async def elements_demo(request: Request):
    """Render the elements demo which showcases all field types."""
    elements_yaml = Path(__file__).with_name("elements.yaml")
    flow = pyformatic.FormFlow.from_yaml(
        str(elements_yaml),
        action="/elements",
    )
    form = flow.steps[0].form

    form.buttons.insert(0, pyformatic.Button(name="reset", label="Reset", button_type="reset"))

    if request.method == "POST":
        data = await request.form()
        tpl = env.get_template("done.html")
        html = tpl.render(title="Elements Submitted", data=dict(data))
        return HTMLResponse(html)

    form_html = pyformatic.Display(form).get_html()
    tpl = env.get_template("form.html")
    html = tpl.render(title="Elements Demo", form_html=form_html)
    return HTMLResponse(html)
