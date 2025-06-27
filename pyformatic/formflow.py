"""Multi-step form flow management."""
from __future__ import annotations

from importlib import import_module
from importlib import resources
from pathlib import Path
from types import MethodType, SimpleNamespace
from typing import Any, Awaitable, Callable, Mapping, Protocol
from inspect import signature

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .form import Form
from .elements import TextInput, Button, RawInput, RawElement
from .display import Display
from .exceptions import (
    ValidationError,
    ValidationInfo,
    ValidationMessage,
    ValidationWarning,
)


class RequestLike(Protocol):
    """Minimal request interface used by ``FormFlow``."""

    method: str
    headers: Mapping[str, str]

    def json(self) -> Awaitable[Any]:
        """Return the request body parsed as JSON."""
        raise NotImplementedError

    def form(self) -> Awaitable[Mapping[str, Any]]:
        """Return the request body parsed as form data."""
        raise NotImplementedError


class Step:
    """Represents a single stage of a multi-step form."""

    def __init__(  # pylint: disable=too-many-arguments  # initializer sets up many configurable options
        self,
        config: dict,
        module_base: str | None,
        action: str,
        *,
        is_last: bool = False,
        validator_context: dict | None = None,
    ) -> None:
        """Create a step instance from configuration."""
        # pylint: disable=too-many-locals  # splitting would reduce clarity here

        fields = [f for f in config.get("fields", []) if f.get("type") != "submit"]
        self.config = {**config, "fields": fields}
        self.validator = self._load_validator(module_base, config["name"])
        if validator_context:
            for name, value in validator_context.items():
                setattr(self.validator, name, value)
        self._setup_inline_validators(fields, config)
        self.form = Form(config['name'], action=action)
        for idx, field in enumerate(fields):
            self._add_field(field, idx)
        button_label = config.get("button_label", "Submit" if is_last else "Next")
        self.form.add_button(Button(name="submit" if is_last else "next", label=button_label))

    def _load_validator(self, module_base: str | None, name: str) -> Any:
        """Return validator instance from module or an empty namespace."""
        if not module_base:
            return SimpleNamespace()
        try:
            module_path = f"{module_base}.validators.{name}"
            module = import_module(module_path)
            return module.Validator()
        except ModuleNotFoundError:
            return SimpleNamespace()

    def _make_callable(self, spec: Any) -> Callable:
        """Return a callable implementing the validator."""
        # pylint: disable=function-redefined  # wrapper must match original callable signature
        if callable(spec):
            sig_len = len(signature(spec).parameters)
            if sig_len <= 1:
                def method(_, value):
                    return spec(value)
            else:
                def method(_, value, data_store):
                    return spec(value, data_store)
            return method
        code = str(spec)
        local: dict[str, Any] = {}
        body = "\n".join(f"    {line}" for line in code.splitlines())
        src = "def _v(value, data_store):\n" + body
        exec(  # pylint: disable=exec-used  # executing inline validator code from YAML
            src,
            {
                "ValidationError": ValidationError,
                "ValidationInfo": ValidationInfo,
                "ValidationWarning": ValidationWarning,
            },
            local,
        )
        def method(_, value, data_store):
            return local["_v"](value, data_store)

        return method

    def _setup_inline_validators(self, fields: list[dict], config: dict) -> None:
        """Bind inline validators defined in the configuration."""

        validators = dict(config.get("validators", {}))
        for field in fields:
            if "validator" in field:
                validators[field["name"]] = field["validator"]
        for name, spec in validators.items():
            func = self._make_callable(spec)
            bound = MethodType(func, self.validator)
            setattr(self.validator, name, bound)

    def _add_field(self, field: dict, idx: int) -> None:
        """Add a configured field to ``self.form``."""
        field_type = field.get('type', 'text')
        if field_type == 'raw_html':
            self.form.add_item(
                RawElement(
                    name=field.get('name', f'raw_{idx}'),
                    label='',
                    html=field.get('html', ''),
                )
            )
            return
        if field_type == 'raw_input':
            item = RawInput(
                name=field['name'],
                label=field.get('label', ''),
                html=field.get('html', ''),
            )
            item.include = field.get('include', [])
            self.form.add_item(item)
            return
        item = TextInput(name=field['name'], label=field.get('label', ''))
        item.input_type = field_type
        item.include = field.get('include', [])
        self.form.add_item(item)

    def validate_field(  # pylint: disable=too-many-arguments  # flexible API for custom validators
        self,
        name: str,
        value: str,
        data_store: dict,
        *,
        update_data: bool = False,
        extra_fields: Mapping[str, str] | None = None,
    ) -> tuple[str, str | None, str]:
        """Validate a single field.

        ``extra_fields`` may contain additional field values to temporarily
        merge into ``data_store`` for the validation call.

        Returns the possibly modified value, message level and message text.
        """
        func = getattr(self.validator, name, None)
        if not func:
            return value, None, ""
        data_view = data_store if not extra_fields else {**data_store, **extra_fields}
        try:
            if func.__code__.co_argcount == 2:
                new_value = func(value)
            else:
                new_value = func(value, data_view)
            if new_value is None:
                new_value = value
            level = "ok"
            message = ""
        except ValidationMessage as exc:  # catch info/warn/error
            new_value = exc.value if exc.value is not None else value
            level = exc.level
            message = exc.message
        if update_data:
            data_store[name] = new_value
            if extra_fields:
                data_store.update(extra_fields)
        item = next((i for i in self.form.items if i.name == name), None)
        if item:
            item.value = new_value
            item.message = message if level else None
            item.classes_outer = [
                c for c in item.classes_outer
                if c not in {"info", "warning", "error", "ok"}
            ]
            if level:
                item.classes_outer.append(level)
        return new_value, level, message

    def validate(self, data: dict, data_store: dict) -> tuple[dict, bool]:
        """Validate all fields in this step and update ``data_store``."""
        messages: dict[str, dict] = {}
        has_error = False
        for field in self.config.get('fields', []):
            if field.get('type') in {'submit', 'raw_html'}:
                continue
            name = field['name']
            value = data.get(name, '')
            new_val, level, msg = self.validate_field(
                name,
                value,
                data_store,
                update_data=True,
            )
            if level:
                messages[name] = {"level": level, "message": msg, "value": new_val}
                if level == "error":
                    has_error = True
        return messages, has_error


class FormFlow:
    """Manage rendering and validation of a form flow."""

    def __init__(  # pylint: disable=too-many-arguments  # flow setup requires several options
        self,
        steps: list[Step],
        *,
        template_dirs: list[str] | None = None,
        static_url: str | None = None,
        show_progress: bool = False,
    ) -> None:
        self.steps = steps
        template_dir = resources.files(__package__) / 'templates'
        search_paths = []
        if template_dirs:
            search_paths.extend(template_dirs)
        search_paths.append(str(template_dir))
        self.template_dirs = template_dirs or []
        self.env = Environment(
            loader=FileSystemLoader(search_paths),
            autoescape=select_autoescape(['html', 'xml']),
        )
        self.static_url = static_url or Display.static_url
        self.show_progress = show_progress

    @classmethod
    def from_yaml(  # pylint: disable=too-many-arguments  # method builds complex object from file
        cls,
        yaml_path: str,
        action: str,
        *,
        validator_context: dict | None = None,
        template_dirs: list[str] | None = None,
        static_url: str | None = None,
    ) -> 'FormFlow':
        """Construct a :class:`FormFlow` instance from a YAML definition."""
        with open(Path(yaml_path), 'r', encoding='utf-8') as fh:
            cfg = yaml.safe_load(fh)
        module_base = cfg['module']
        step_cfgs = cfg.get('steps', [])
        show_progress = cfg.get('show_progress', False)
        steps = [
            Step(
                step_cfg,
                module_base,
                action,
                is_last=idx == len(step_cfgs) - 1,
                validator_context=validator_context,
            )
            for idx, step_cfg in enumerate(step_cfgs)
        ]
        return cls(
            steps,
            template_dirs=template_dirs,
            static_url=static_url,
            show_progress=show_progress,
        )

    @staticmethod
    def is_validation_request(request: RequestLike) -> bool:
        """Return True if this request is for field validation."""
        content_type = request.headers.get("content-type", "").lower()
        return request.method == "POST" and content_type.startswith("application/json")


    async def handle_request(
        self,
        request: RequestLike,
        data_store: dict,
    ) -> tuple[bool, dict | tuple[int, dict | None, bool]]:
        """Process a web request and return the resulting action."""
        if self.is_validation_request(request):
            payload = await request.json()
            field = payload.get("field", "")
            data_store.update(payload.get("fields", {}))
            data_store[field] = payload.get("value", "")
            step_index = self.step_index_for_field(field)
            value, level, message = self.validate_field(
                step_index,
                field,
                payload.get("value", ""),
                data_store,
                extra_fields=payload.get("fields"),
            )
            return True, {"level": level or "", "message": message, "value": value}

        form_data = await request.form()
        for key, value in form_data.items():
            if key not in {"next", "submit"}:
                data_store[key] = value
        index, messages, has_error = self.current_step(data_store)
        return False, (index, messages, has_error)

    def render(
        self,
        index: int,
        messages: dict | None = None,
        data_store: dict | None = None,
        csrf_token: str | None = None,
    ) -> str:
        """Return HTML for the given step, applying validation messages."""

        step = self.steps[index]
        error_fields: list[str] = []
        if messages:
            for name, meta in messages.items():
                item = next((i for i in step.form.items if i.name == name), None)
                if item:
                    item.message = meta.get("message")
                    item.classes_outer = [
                        c
                        for c in item.classes_outer
                        if c not in {"info", "warning", "error", "ok"}
                    ]
                    if meta.get("level"):
                        item.classes_outer.append(meta["level"])
                    if "value" in meta:
                        item.value = meta["value"]
                    if meta.get("level") == "error":
                        error_fields.append(item.label or item.name)
        hidden = data_store or {}
        if csrf_token:
            hidden = {**hidden, "csrf_token": csrf_token}
        disp = Display(
            step.form,
            template_dirs=self.template_dirs,
            static_url=self.static_url,
        )
        form_html = disp.get_html(hidden_fields=hidden)
        tpl = self.env.get_template("multi_step/page.html")
        return tpl.render(
            form_html=form_html,
            messages=messages or {},
            form_id=step.form.id,
            error_fields=error_fields,
            show_progress=self.show_progress,
            step_index=index,
            total_steps=self.num_steps,
        )

    def validate_field(
        self,
        index: int,
        name: str,
        value: str,
        data_store: dict,
        *,
        extra_fields: Mapping[str, str] | None = None,
    ) -> tuple[str, str | None, str]:
        """Validate a field in the specified step."""  # pylint: disable=too-many-arguments  # passthrough helper
        return self.steps[index].validate_field(
            name,
            value,
            data_store,
            extra_fields=extra_fields,
        )

    def validate(self, index: int, data: dict, data_store: dict) -> tuple[dict, bool]:
        """Validate all fields for the given step."""
        return self.steps[index].validate(data, data_store)

    @property
    def num_steps(self) -> int:
        """Return the number of configured steps."""
        return len(self.steps)

    def _fields_for_step(self, index: int) -> list[str]:
        """Return names of non-button fields for the given step."""
        step = self.steps[index]
        return [
            f["name"]
            for f in step.config.get("fields", [])
            if f.get("type") not in {"submit", "raw_html"}
        ]

    def step_index_for_field(self, name: str) -> int:
        """Return the index of the step containing ``name``."""
        for idx in range(len(self.steps)):
            if name in self._fields_for_step(idx):
                return idx
        return 0

    def current_step(self, data_store: dict) -> tuple[int, dict | None, bool]:
        """Return step index, validation messages and failure state."""
        data = dict(data_store)
        for idx in range(len(self.steps)):
            names = self._fields_for_step(idx)
            if not any(n in data for n in names):
                return idx, None, False
            subset = {n: data.get(n, "") for n in names}
            messages, has_error = self.validate(idx, subset, data)
            if has_error:
                return idx, messages, True
        data_store.update(data)
        return len(self.steps), None, False
