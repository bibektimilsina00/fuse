"""Workflow template seeds — JSON-backed library of canned workflows.

Templates live at ``apps/api/app/features/templates/seeds/<category>/<id>.json``.
Each file is a complete workflow definition that can be imported into
a workspace via ``POST /api/v1/templates/{id}/import``.

The first category we ship is ``loops/`` — the three starter agent
loops from the loop-engineering plan (Linear triage, Dependabot
auto-merger, Sentry → GitHub).
"""

from .models import Template, TemplatePurchase
from .registry import TemplateRegistry, get_template, list_templates
from .repository import TemplatePurchaseRepository, TemplateRepository
from .service import TemplateService

__all__ = [
    "Template",
    "TemplatePurchase",
    "TemplatePurchaseRepository",
    "TemplateRegistry",
    "TemplateRepository",
    "TemplateService",
    "get_template",
    "list_templates",
]
