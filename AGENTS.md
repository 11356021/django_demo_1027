# AGENTS.md (django-demo-1027)

## Structure
- Django project: settings/urls/wsgi/asgi in `config/` (`DJANGO_SETTINGS_MODULE=config.settings`)
- Entry: `manage.py` at repo root
- DB: SQLite (`db.sqlite3`) at `BASE_DIR`
- Apps: only Django contrib apps in `INSTALLED_APPS` (no custom apps yet)
- Email: console backend in `config/settings.py`

## Commands (exact)
- Run dev server: `python manage.py runserver`
- Migrations: `python manage.py makemigrations` / `python manage.py migrate`
- Admin/shell: `python manage.py createsuperuser` / `python manage.py shell`
- Tests: `python manage.py test`
- Check/deploy checks: `python manage.py check`

## Env / toolchain
- Python `>=3.14.7` (see `pyproject.toml`)
- Django `>=6.1.2`
- Virtualenv present: `.venv/` (use it)
- Dependencies managed via `pyproject.toml` + `uv.lock` (use `uv` if adding deps)
- Debug=True, SECRET_KEY committed (dev-only)
