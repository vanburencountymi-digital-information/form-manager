from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from treebeard.mp_tree import MP_Node


class Department(MP_Node):
    name = models.CharField(max_length=100, unique=True)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, editable=False)
    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="owned_departments",
        blank=True,
    )

    node_order_by = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        expected_group_name = f"dept-{self.name}"
        if not self.group_id:
            self.group = Group.objects.create(name=expected_group_name)
        elif self.group.name != expected_group_name:
            self.group.name = expected_group_name
            self.group.save()
        super().save(*args, **kwargs)
