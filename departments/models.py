from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from treebeard.mp_tree import MP_Node


class DepartmentHasChildrenError(Exception):
    """Raised by Department.archive() when the department still has child
    departments — the caller must move or archive them first."""


class Department(MP_Node):
    name = models.CharField(max_length=100, unique=True)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, editable=False)
    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="owned_departments",
        blank=True,
    )
    is_archived = models.BooleanField(default=False)

    node_order_by = ["name"]

    def __str__(self):
        return self.name

    @property
    def group_name(self):
        return f"dept-{self.name}"

    def sync_group_name(self):
        """Ensures this department has a Group whose name matches
        group_name — creates the Group if one doesn't exist yet, or
        updates and persists its name if it's drifted (e.g. after a
        rename). Safe to call whether or not self.group exists."""
        if not self.group_id:
            self.group = Group.objects.create(name=self.group_name)
        elif self.group.name != self.group_name:
            self.group.name = self.group_name
            self.group.save()

    def save(self, *args, **kwargs):
        self.sync_group_name()
        super().save(*args, **kwargs)

    def add_member(self, user):
        self.group.user_set.add(user)

    def remove_member(self, user):
        self.group.user_set.remove(user)

    @classmethod
    def get_departments_owned_by_user(cls, user):
        """Departments this user directly owns, plus every descendant of
        each — owning a department implies owning its sub-departments
        too, consistent with how department scoping works everywhere
        else in this project (e.g. FormPermissions flattening)."""
        department_ids = set()
        for department in user.owned_departments.all():
            department_ids.add(department.pk)
            department_ids.update(
                department.get_descendants().values_list("pk", flat=True)
            )
        return cls.objects.filter(pk__in=department_ids)

    def archive(self):
        """Archives this department. Raises DepartmentHasChildrenError if it
        still has any child departments — move or archive them first."""
        if self.get_children().exists():
            raise DepartmentHasChildrenError(
                f'"{self.name}" still has child departments; move or archive '
                "them before archiving this department."
            )
        self.is_archived = True
        self.save()


@receiver(pre_delete, sender=Department)
def prevent_department_deletion(sender, instance, **kwargs):
    raise PermissionError(
        "Departments cannot be deleted; call archive() instead to preserve "
        "audit history."
    )
