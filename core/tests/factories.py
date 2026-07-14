import factory

from django_forms_workflows.models import FormDefinition


class FormDefinitionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FormDefinition

    name = factory.Sequence(lambda n: f"Form {n}")
    slug = factory.Sequence(lambda n: f"form-{n}")
    description = "Test form"
