# form-manager

Django app for department-scoped forms and approval workflows, built on
`django-forms-workflows`.

## Quick Setup

Requires Python 3.12. It's recommended to create your environment
outside of the project, so that it doesn't have to be added to gitignore.

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the repo root:

```
SECRET_KEY=<any-random-string>
DEBUG=True
USER_EMAIL_DOMAINS=example.com
```

Then:

```
python manage.py migrate
python manage.py createsuperuser   # optional
python manage.py runserver
```

## Linting & type checking

```
ruff check .     # lint
ruff format .    # format
mypy .           # type check
```

## Pre-commit hooks

```
pip install pre-commit
pre-commit install
```

Runs Ruff and mypy automatically before every commit — the commit is blocked
until both pass.

# Test coverage
Provided by Coverage.py.
Check coverage with:  coverage run manage.py test
Generate report with: coverage report
Create html report with: coverage html

## Forms-Manager Architecture

### Administrators

There is no dedicated Administrator model; instead, Administrator membership is managed via `permissions.services.AdminGroupService`, 
which uses the existing Django `Group` and `Permission` architecture to programmatically create an Administrator group. This primitive
service also checks if Users are members of the group as well as manages group membership.


### Departments
Departments are modeled as a single-parent heirarchy via the `django-treebeard` package `MPNode` class.

#### Deparment Owners
Department owners (a M2M to `User` defined on `departments.Department.owners()`) are granted the ability to invite and manage Users/Department membership.
They are also automatically granted each of the six department-scoped permissions below.

#### Inviting Users to Departments
- Users can be invited to a department by the department owner (`departments.Department.owners()`) or by an Administrator.

### Assigning Department-scoped Permissions to Users
- During the invitation process, an administrator or department owner can assign one or more of six department-scoped
permissions, as defined by `departments.models.DepartmentPermissions`: 
    - CAN_CREATE_FORMS, CAN_EDIT_FORMS, and CAN_ARCHIVE_FORMS refer to the `FormDefinition` object from django-forms-workflows, i.e., the ***schema*** of a form in which its fields and behavior are defined.
    - CAN_CREATE_WORKFLOWS, CAN_EDIT_WORKFLOWS, CAN_ARCHIVE_WORKFLOWS refer to the Approval Workflow object from django-forms-workflows.

- It is possible to invite a user to a deparment with ***no*** department-scoped permissions, as permissions can also be granted on the FormDefinition level
for each individual form (i.e., a User might not have the department-scoped ability to edit FormDefinition objects, but be granted that ability on a *specific* form.)

