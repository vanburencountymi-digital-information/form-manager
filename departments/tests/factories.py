import factory

from accounts.tests.factories import UserFactory
from departments.models import Department


class DepartmentFactory(factory.django.DjangoModelFactory[Department]):
    """Parameters:
    `chain_depth` (int): create a chain of `chain_depth` child departments
        below this one.
    `parent` (Department): create this department as a child of the
        passed-in Department.
    `with_user` (True or User): add a member (not owner) to the department —
        True auto-generates a User, or pass a specific User instance to use that one.
    `with_owner` (True or User): add an owner (and therefore also a member) to the
        department — True auto-generates a User, or pass a specific User instance
        to use that one.
    `owners` (iterable of Users): add each passed-in user as both an owner and
        a member of the department.
    """

    class Meta:
        model = Department

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
        """owners=[user1, user2, ...] adds each user as both an owner and a
        member of the department."""
        if not create or not extracted:
            return
        for user in extracted:
            self.add_member(user)
            self.add_user_to_owners(user)

    @factory.post_generation
    def with_owner(self, create, extracted, **kwargs):
        """with_owner=True auto-generates a User and adds them as both a
        member and an owner; pass a specific User instance instead to use
        that one."""
        if not create or not extracted:
            return
        owner = extracted if extracted is not True else UserFactory()
        self.add_member(owner)
        self.add_user_to_owners(owner)

    @factory.post_generation
    def with_user(self, create, extracted, **kwargs):
        """with_user=True auto-generates a User and adds them as a member
        only (not an owner); pass a specific User instance instead to use
        that one."""
        if not create or not extracted:
            return
        user = extracted if extracted is not True else UserFactory()
        self.add_member(user)

    @factory.post_generation
    def chain_depth(self, create, extracted, **kwargs):
        """DepartmentFactory(chain_depth=3) chains 3 descendants below this one."""
        if not create or not extracted:
            return
        current = self
        for _ in range(extracted):
            current = DepartmentFactory(parent=current)
