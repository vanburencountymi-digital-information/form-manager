from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import Department


@admin.register(Department)
class DepartmentAdmin(TreeAdmin):
    form = movenodeform_factory(Department)
