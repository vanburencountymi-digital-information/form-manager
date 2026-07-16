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
