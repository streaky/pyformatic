"""Unit tests for basic form rendering."""

import pyformatic

def test_render_form_basic():
    """Form renders with a text input and button."""
    form = pyformatic.Form("login", action="/submit")
    form.add_item(pyformatic.TextInput(name="username", label="Username"))
    form.add_button(pyformatic.Button(name="submit", label="Submit"))
    display = pyformatic.Display(form)
    html = display.get_html()
    assert "<form" in html
    assert "Username" in html
    assert "Submit" in html


def test_render_checkbox_default():
    """Checkbox fields render unchecked by default."""
    form = pyformatic.Form("agree", action="/submit")
    cb = pyformatic.TextInput(name="terms", label="Agree")
    cb.input_type = "checkbox"
    form.add_item(cb)
    display = pyformatic.Display(form)
    html = display.get_html()
    assert 'type="checkbox"' in html
    assert 'value="on"' in html
    assert "checked" not in html


def test_render_checkbox_checked():
    """Checkbox fields support a preset checked state."""
    form = pyformatic.Form("agree", action="/submit")
    cb = pyformatic.TextInput(name="terms", label="Agree", value="on")
    cb.input_type = "checkbox"
    form.add_item(cb)
    display = pyformatic.Display(form)
    html = display.get_html()
    assert 'type="checkbox"' in html
    assert 'value="on"' in html
    assert 'checked' in html


def test_render_raw_elements():
    """Raw input and elements appear verbatim in output."""
    form = pyformatic.Form("raw", action="/submit")
    raw_in = pyformatic.RawInput(
        name="promo",
        label="Promo",
        html="<label for='promo'>Promo</label><input id='promo' name='promo'>",
    )
    form.add_item(raw_in)
    raw_elem = pyformatic.RawElement(
        name="banner", label="", html="<div class='banner'>Hello</div>"
    )
    form.add_item(raw_elem)
    display = pyformatic.Display(form)
    html = display.get_html()
    assert "banner" in html
    assert "Promo" in html


def test_template_override(tmp_path):
    """Templates can be overridden via extra directories."""
    ui_dir = tmp_path / "ui"
    ui_dir.mkdir(parents=True)
    (ui_dir / "input_text.html").write_text("<div>OVERRIDE {{ item_name }}</div>")
    form = pyformatic.Form("f", action="/submit")
    form.add_item(pyformatic.TextInput(name="foo", label="Foo"))
    display = pyformatic.Display(form, template_dirs=[str(tmp_path)])
    html = display.get_html()
    assert "OVERRIDE foo" in html
