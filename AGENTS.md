# AGENTS.md (django-demo-1027)

Course-selection demo (Traditional Chinese UI) on Django 6.1 + SQLite. No README, CI, lint, or formatter config exists.

## Commands (use the venv interpreter)
- Run: `.venv/Scripts/python.exe manage.py runserver`
- Check: `.venv/Scripts/python.exe manage.py check`
- All tests: `.venv/Scripts/python.exe manage.py test`
- One test: `.venv/Scripts/python.exe manage.py test enrollments.tests.ClassName.test_method`
- Migrations: `.venv/Scripts/python.exe manage.py makemigrations` / `migrate`
- Admin/shell: `.venv/Scripts/python.exe manage.py createsuperuser` / `shell`
- Deps: `uv add <pkg>` updates `pyproject.toml`, `uv.lock`, and `.venv`
- Seed demo data: `.venv/Scripts/python.exe manage.py seed_demo` (idempotent; refreshes the enroll window)
- Bare `python` on PATH is Python 3.13 + Django 4.1.4, not the project env (3.14.8 + Django 6.1.2); its `check` output differs. Always use `.venv`.

## Layout
- `config/` project config: settings/urls/wsgi/asgi, `DJANGO_SETTINGS_MODULE=config.settings`.
- `accounts/`: `Profile` (OneToOne to built-in `User`; roles STUDENT/TEACHER/ADMIN; `credit_limit` default 18), plus registration (`/accounts/register/`) and profile (`/accounts/profile/`) pages. Profiles are created on demand via `accounts.services.get_or_create_profile`; nothing guarantees `user.profile` exists.
- `courses/`: `Semester`, `Course` (code/name/credits/department/`description`) -> `Section` -> `TimeSlot` catalog. Admin-only; `views.py` is a stub.
- `enrollments/`: all public web code — `urls.py`, `views.py`, `services.py`, `Enrollment`; history page at `/history/`; `course_list` supports `q`/`department`/`semester` filters; `my_schedule` builds a 7-day grid via `build_week_grid`.
- `templates/`: project-level dir (`TEMPLATES.DIRS`); every page extends `templates/base.html`. UI text is zh-Hant, Bootstrap via CDN. Site-styled auth pages live in `templates/registration/` and override the admin fallbacks.

## Enrollment rules
- Business rules live in `enrollments/services.py`; views just call `enroll_student` / `drop_student`, which return `(ok, message)`. Put new rules there, not in views; user-facing messages are zh-Hant.
- `enroll_student` checks, in order: existing enrollment (ENROLLED or DROPPED) -> semester active and inside `enroll_start`/`enroll_end` -> time conflict -> credit limit -> capacity.
- Drops are soft (`status=DROPPED`, `dropped_at` set) and never deleted; dropping is allowed only while the semester is active and inside the enroll window.
- Re-enrolling after a drop is rejected; the unique `(student, section)` row stays DROPPED.
- Capacity and the course-list count include only ENROLLED rows; `course_list.html` shows 已滿 / 已退選 instead of an enroll button.
- No role enforcement: any logged-in user can enroll/drop. `Profile.role` is stored but unused outside admin.

## Web / auth
- URLconf mounts `enrollments.urls` at `/`, `accounts.urls` + `django.contrib.auth.urls` at `/accounts/`; `/` redirects to `course_list`.
- All enrollment views are `@login_required`; custom login template is `templates/registration/login.html`; registration auto-logs in and creates a STUDENT profile; `LOGIN_REDIRECT_URL='/'`, `LOGOUT_REDIRECT_URL='/accounts/login/'`, logout is POST-only.
- Email uses Django 6.1's `MAILERS` dict in `config/settings.py` (console backend); `EMAIL_BACKEND` is deprecated, don't reintroduce it. Only password reset sends email; in dev the reset link is printed to the `runserver` console. Enrollment success does not send email.
- Password change/reset are the built-in auth views with project templates: `/accounts/password_change/`, `/accounts/password_reset/`, `/accounts/reset/<uidb64>/<token>/`. Password change uses `accounts.forms.PasswordChangeWithoutOldForm` (new password only, no old password). Logged-in users reach password change from the profile page; the login page links to password reset.
- `LANGUAGE_CODE='zh-hant'` and `TIME_ZONE='Asia/Taipei'`; keep UI text and new messages in Traditional Chinese.
- Dev-only settings: `DEBUG=True`, committed `SECRET_KEY`, empty `ALLOWED_HOSTS`.

## Data / git gotchas
- `courses/management/commands/seed_demo.py` seeds an active `115-1` semester (window = now -7d to now +30d), 18 courses (with zh-Hant descriptions) and time slots, and 11 teacher accounts with unusable passwords (TEACHER profiles). Some courses share time slots on purpose so conflict checking can be exercised. It is idempotent, and rerunning it refreshes the window. The committed `db.sqlite3` already contains this data.
- No `.gitignore`: `__pycache__/*.pyc` (25 tracked files) and `db.sqlite3` are committed. Don't `git add -A`; don't delete or rewrite `db.sqlite3`.
- `accounts/tests.py`, `courses/tests.py`, and `enrollments/tests.py` cover registration/profile, password change/reset, seed idempotency, course search/filter, course descriptions, the weekly grid, and all enrollment rules/views (42 tests). Run the full suite before finishing changes.
