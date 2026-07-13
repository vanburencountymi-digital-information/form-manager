import factory

from accounts.factories import UserFactory
from departments.models import Department


class DepartmentFactory(factory.django.DjangoModelFactory):
    """Factory for Department. Call with `chain_depth` to create a
    chain of child Departments."""

    class Meta:
        model = Department

    # Create department names with auto-incrementing numbers, e.g., Department 0, Department 1
    name = factory.Sequence(lambda n: f"Department {n}")
    parent = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        parent = kwargs.pop("parent", None)
        if parent is not None:
            return parent.add_child(*args, **kwargs)
        return model_class.add_root(*args, **kwargs)

    @factory.post_generation
    def owners(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.owners.add(*extracted)

    @factory.post_generation
    def with_owner(self, create, extracted, **kwargs):
        """with_owner=True auto-generates a User and adds them as an owner;
        pass a specific User instance instead to use that one."""
        if not create or not extracted:
            return
        owner = extracted if extracted is not True else UserFactory()
        self.owners.add(owner)

    @factory.post_generation
    def chain_depth(self, create, extracted, **kwargs):
        """DepartmentFactory(chain_depth=3) chains 3 descendants below this one."""
        if not create or not extracted:
            return
        current = self
        for _ in range(extracted):
            current = DepartmentFactory(parent=current)
