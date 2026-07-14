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

    class Meta:
        permissions = [
            ("can_invite_to_any_department", "Can invite users to any department"),
        ]

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
