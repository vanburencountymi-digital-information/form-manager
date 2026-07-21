from __future__ import annotations

from django.template.defaultfilters import slugify
from django_forms_workflows.models import FormDefinition


def generate_unique_slug(name: str) -> str:
    """Slugifies name, appending -2, -3, ... on collision against
    FormDefinition.slug (unique=True) until one doesn't exist yet."""
    base_slug = slugify(name) or "form"
    slug = base_slug
    suffix = 2
    while FormDefinition.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug
