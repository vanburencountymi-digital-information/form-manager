import factory
from django.contrib.auth import get_user_model

from permissions.services import AdministratorGroupService

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory[User]):
    """Pass in `is_administrator=True` to add the user to the Administrator
    group via AdministratorGroupService."""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.SelfAttribute("email")  # overwritten by User.save() anyway
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)

    @factory.post_generation
    def is_administrator(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        AdministratorGroupService.add_administrator(self)
