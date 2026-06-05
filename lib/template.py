"""Jinja2 email template loading and rendering."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
DEFAULT_TEMPLATE = "default.html"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_template(name: str, email: str, template_name: str = DEFAULT_TEMPLATE) -> str:
    env = _env()
    tmpl = env.get_template(template_name)
    return tmpl.render(name=name, email=email)
