# Repository instructions

## Project shape

This repository is a Django project. `manage.py` sets `DJANGO_SETTINGS_MODULE` to `setup.settings`; `setup/` contains the project settings and the root URL configuration, while `finance/` is the domain app scaffold. The root URL configuration currently exposes only Django admin, and `finance` is not yet listed in `INSTALLED_APPS`.

The database is configured as SQLite at the repository root. Django template discovery has `APP_DIRS=True` but `TEMPLATES[0]["DIRS"]` is empty, so app-level templates are discovered while the top-level `templates/` directory is not currently configured. Static files use Django's `STATIC_URL`; there is no separate frontend build setup in the repository yet.

## Commands

Use the checked-in virtual environment from the repository root:

```sh
./venv/bin/python manage.py runserver
./venv/bin/python manage.py check
./venv/bin/python manage.py test
```

Run one app's tests or a single test by Django test label:

```sh
./venv/bin/python manage.py test finance
./venv/bin/python manage.py test finance.tests.TestCaseName.test_method_name
```

No separate build or lint command is configured in the repository.

## Project conventions

- Keep project-wide settings and URL routing in `setup/`; feature code belongs in Django apps such as `finance/`.
- The app uses Django's conventional module split (`models.py`, `views.py`, `admin.py`, `tests.py`, and `migrations/`). Add app-specific templates and static assets under that app if following Django's current discovery configuration.
- Register an app in `INSTALLED_APPS` before relying on its models, migrations, or app configuration being loaded.
- Add feature routes in the app's `urls.py` and include them from `setup/urls.py` when introducing app-level URL routing; the root URL configuration currently registers only `admin.site.urls`.
