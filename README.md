# Pyformatic

Pyformatic is a lightweight Python library for building, rendering and validating
HTML forms. It supports plain Python definitions as well as multi‑step forms
described in YAML. A small FastAPI demo application is included to showcase the
library in action.

Pyformatic aims to stay minimal while providing convenient helpers for common
form workflows. It ships with Jinja templates but you are free to supply your
own. Form validators can access user‑provided context, making it easy to build
advanced validation rules.

## Features

* Define forms directly in Python or load them from YAML files
* Render forms using built‑in Jinja templates
* Validate user input and display informative messages
* Define validators inline with form fields
* Support multi‑step wizards via `FormFlow`
* Optional progress indicator for multi-step flows
* Helper `run_form_flow` to manage multi‑step state in any framework
* Easily integrate into FastAPI or any ASGI framework
* Inject raw HTML snippets as inputs or standalone blocks
* Built-in CSRF protection using session tokens

## Roadmap

* Internationalization support
* Possibly integration with Pydantic
* Custom field plugins

## Installation

Install the library from PyPI:

```bash
pip install pyformatic
```

Alternatively, clone this repository and install it in editable mode for local
development:

```bash
git clone https://github.com/streaky/pyformatic.git
cd pyformatic
pip install -e .
```

Pyformatic requires Python 3.10 or newer. The development environment and CI run
on Python 3.13.

## Quick start

Begin by defining a form in YAML and loading it with `FormFlow`:

```yaml
steps:
  - name: contact
    fields:
      - name: email
        type: text
        label: Email
```

```python
from pyformatic import formflow, Display

flow = formflow.FormFlow.from_file("contact.yaml")
html = Display(flow.steps[0]).get_html()
print(html)
```

Validation logic can be added inline in YAML:

```yaml
fields:
  - name: email
    type: text
    label: Email
    validator: |
      if "@" not in value:
          raise ValidationError("invalid email")
      return value
```

Validation can also be defined programmatically using callables:

```python
def check_email(value, _):
    if "@" not in value:
        raise ValidationError("invalid email")
    return value

cfg = {"name": "step", "fields": [{"name": "email", "validator": check_email}]}
step = pyformatic.formflow.Step(cfg, None, action="/")
```

You can also describe a multi‑step form in YAML and load it with `FormFlow`.
See the files in `demo/` for complete examples. To manage progress and
validation you can call `run_form_flow` inside your request handler.
Set `show_progress: true` in the YAML or pass `show_progress=True` to
`FormFlow` to display a progress bar. The YAML signup demo enables this
feature and the repository also includes a fully Python-defined multi-step
form served at `/signup-python`.
The YAML version demonstrates an inline validator for the email field.

Forms can also be created directly in Python:

```python
from pyformatic import Form, TextInput, Button, Display

form = Form("contact", action="/submit")
form.add_item(TextInput(name="email", label="Email"))
form.add_button(Button(name="submit", label="Send"))

html = Display(form).get_html()
print(html)
```

Fields can also list other field names under an ``include`` option. When a field
with this option is validated via AJAX, the values of the referenced fields are
sent along and made available in the ``data_store`` during validation.

When server‑side validation fails, a banner at the top of the page lists the
fields that require attention while each field still shows its individual
message inline.

### CSRF protection

If the request object passed to ``run_form_flow`` provides a ``session``
mapping, Pyformatic automatically includes a CSRF token in the rendered
form and validates it on submission. The token is stored in the session under
``_pyformatic_csrf_token``.

## Custom templates

`Display` accepts additional template directories. If a file named
`ui/input_<type>.html` exists in one of those directories it overrides the
default template for that input type. This allows applications to style specific
elements without modifying the bundled templates.

## Demo application

The repository includes a FastAPI demo showing how to serve forms and perform
AJAX validation. Pages are styled with [Pico CSS](https://picocss.com) and
`pyformatic/static/pyformatic.css` provides colours for validation messages.
Use ``pyformatic.Display.setup_jinja(env)`` to register template variables
``pyformatic_header`` and ``pyformatic_footer`` which include the required CSS
and JavaScript.
Start it using Docker:

```bash
make run
```

Then open `http://localhost:8000` in your browser.

To run the demo locally without Docker, create the development environment and
start the server:

```bash
make dev
source .dev-venv/bin/activate
uvicorn demo.main:app --reload
```

## Running tests

Unit and end‑to‑end tests are provided. Playwright is used for browser tests.
Execute them with:

```bash
make test
```

This command sets up the virtual environment, starts the demo server and runs
both unit and browser tests.

Lint the codebase with:

```bash
make lint
```

This runs pylint on the library, tests and demo directories.

## Repository layout

* `pyformatic/` – library source code and Jinja templates
* `demo/` – FastAPI demo application
* `tests/` – unit tests and Playwright end‑to‑end tests

## Source and support

The code lives on [GitHub](https://github.com/streaky/pyformatic). Contributions
via pull request are welcome. Please run the linter and tests before PR, though.

## Publishing to PyPI

Releases are published automatically when a tag matching `v*` is pushed. To
release a new version, create and push a tag:

```bash
git tag v0.1.0
git push --tags
```

The `.github/workflows/publish.yml` workflow builds the package and uploads it
to PyPI using the `PYPI_API_TOKEN` repository secret. Pushing a tag beginning
with `test-v` uploads the build to TestPyPI instead using the
`TEST_PYPI_API_TOKEN` secret.

## License

This project is distributed under the terms of the [Apache License 2.0](LICENSE).
