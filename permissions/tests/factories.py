import factory

from core.tests.factories import FormDefinitionFactory
from permissions.models import FormPermissions


class FormPermissionsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FormPermissions

    form = factory.SubFactory(FormDefinitionFactory)

    @factory.post_generation
    def editor_departments(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.editor_departments.add(*extracted)

    @factory.post_generation
    def viewer_departments(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.viewer_departments.add(*extracted)
