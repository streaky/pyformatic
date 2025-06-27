"""Render forms using Jinja2 templates."""

from __future__ import annotations

from importlib import resources

from typing import Mapping
from markupsafe import escape
from jinja2 import (
    Environment,
    FileSystemLoader,
    TemplateNotFound,
    select_autoescape,
)

from .form import Form
from .elements import InputElement, RawInput, RawElement


class Display:
    """Renders a form to HTML."""

    static_url = "/static"

    @classmethod
    def header_html(cls, static_url: str | None = None) -> str:
        """Return ``<link>`` tags for required assets."""
        url = static_url or cls.static_url
        url = url.rstrip("/")
        return f'<link rel="stylesheet" href="{url}/pyformatic.css">'

    @classmethod
    def footer_html(cls, static_url: str | None = None) -> str:
        """Return ``<script>`` tags for required assets."""
        url = static_url or cls.static_url
        url = url.rstrip("/")
        return f'<script src="{url}/pyformatic.js"></script>'

    @classmethod
    def setup_jinja(cls, env: Environment, static_url: str | None = None) -> None:
        """Register globals in a :class:`jinja2.Environment`."""
        env.globals["pyformatic_header"] = cls.header_html(static_url)
        env.globals["pyformatic_footer"] = cls.footer_html(static_url)

    def __init__(
        self,
        form: Form,
        *,
        template_dirs: list[str] | None = None,
        static_url: str | None = None,
    ) -> None:
        self.form = form
        self.static_url = static_url or self.__class__.static_url
        template_dir = resources.files(__package__) / "templates"
        search_paths = []
        if template_dirs:
            search_paths.extend(str(p) for p in template_dirs)
        search_paths.append(str(template_dir))
        self.env = Environment(
            loader=FileSystemLoader(search_paths),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def _get_input_template(self, input_type: str):
        """Return template for the given input type, falling back to default."""

        try:
            return self.env.get_template(f"ui/input_{input_type}.html")
        except TemplateNotFound:
            return self.env.get_template("ui/input.html")

    def _render_items(self) -> str:
        parts = []
        for item in self.form.items:
            if isinstance(item, RawElement):
                parts.append(item.html)
                continue
            if isinstance(item, InputElement):
                tpl = self._get_input_template(item.input_type)
                extra = dict(item.extra)
                if item.include:
                    extra["data-include"] = ",".join(item.include)
                extra_attrs = " ".join(f'{k}="{v}"' for k, v in extra.items())
                custom_html = item.html if isinstance(item, RawInput) else ""
                parts.append(
                    tpl.render(
                        item_id=item.id,
                        item_label=item.label,
                        item_name=item.name,
                        item_value=item.value,
                        item_help=item.help,
                        item_message=item.message or "",
                        item_type=item.input_type,
                        item_placeholder=item.placeholder,
                        item_outer_classes=" ".join(item.classes_outer),
                        item_input_classes=" ".join(item.classes_input),
                        item_options=item.options,
                        item_rows=item.rows,
                        extra_attrs=extra_attrs,
                        item_raw_html=custom_html,
                    )
                )
        return "\n".join(parts)

    def _render_buttons(self) -> str:
        if not self.form.buttons:
            return ""
        tpl_btn = self.env.get_template("ui/button.html")
        rendered = [tpl_btn.render(button=btn) for btn in self.form.buttons]
        outer = self.env.get_template("ui/buttons_outer.html")
        return outer.render(buttons="".join(rendered))

    def get_html(self, *, hidden_fields: Mapping[str, str] | None = None) -> str:
        """Return HTML string for the form."""

        tpl = self.env.get_template("ui/form.html")
        items = self._render_items()
        if hidden_fields:
            hidden = []
            for name, value in hidden_fields.items():
                hidden.append(
                    f'<input type="hidden" name="{escape(name)}" '
                    f'value="{escape(value)}">'
                )
            items += "\n".join(hidden)
        buttons = self._render_buttons()
        return tpl.render(
            form_id=self.form.id,
            form_action=self.form.action,
            form_method=self.form.method,
            form_autocomplete="off" if not self.form.autocomplete else "on",
            form_items=items,
            buttons=buttons,
        )
