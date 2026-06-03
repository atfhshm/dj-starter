# Django Starterkit

A production-ready boilerplate for building API-first backends using django. The starterkit is shipped with an opinionated custom user model, Django REST framework, OpenAPI documentation, CORS configurations, Silk profiler for development, structured logging, caching using redis, background jobs with celery, celery beat and celey results, optional Websocket support using django channels, S3-compatible object storage wired using django-storages, SMTP configuration out of the box, i18n support for english (default) and arabi and Environment-based configurations.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** for installs and scripts
- **Python 3.14** (see `.python-version`)
- **PostgreSQL** — database name in the default `DATABASE_URL` is `dj-starter`
- **Redis** — used for cache, Celery, and Channels
- **S3-compatible storage** — required for media/static in the default config (R2, MinIO, AWS S3, etc.)

## Quick start

### 1. Clone and install dependencies

```bash
git clone git@github.com:atfhshm/dj-starter.git dj-starter
cd dj-starter
uv sync
```

### 2. Configure environment

Copy the example env file and edit values for your machine:

```bash
cp .env.example .env
```

At minimum, set:

- `SECRET_KEY` — a long random string (never commit the real `.env`)
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- Storage credentials
    - `ACCESS_KEY_ID`
    - `SECRET_ACCESS_KEY`
    - `STORAGE_BUCKET_NAME`
    - `ENDPOINT_URL` (not needed if using s3)
    - `STATIC_STORAGE_CUSTOM_DOMAIN` (for a public static URL)

### 3. Create the database

Create an empty PostgreSQL database matching your `DATABASE_URL`, for example:

```bash
createdb <db-name>
```

### 4. Run migrations

```bash
uv run manage.py migrate
```

### 5. Create a superuser

The custom user model requires **name**, **email**, and **phone number**:

```bash
uv run manage.py createsuperuser
```

### 6. Start the development server

```bash
make dev
```

The app listens at **http://127.0.0.1:8000/** by default.

### 7. (Optional) Start Celery worker and beat

In a second terminal:

```bash
make celery
```

This runs the Celery worker and beat scheduler (using the database-backed beat scheduler). Ensure migrations have been applied so `django_celery_beat` tables exist.

## Development URLs

When the corresponding flags are enabled in `.env`:

| URL             | Description                                    |
| --------------- | ---------------------------------------------- |
| `/admin/`       | Django admin (session auth)                    |
| `/api/swagger/` | Swagger UI (`ENABLE_OPENAPI=true`, admin-only) |
| `/api/redoc/`   | ReDoc (`ENABLE_OPENAPI=true`, admin-only)      |
| `/api/schema/`  | OpenAPI schema JSON                            |
| `/silk/`        | Request profiling UI (`SILK_ENABLED=true`)     |

OpenAPI UI is restricted to **admin users** via `SERVE_PERMISSIONS` in `core/openapi.py`.

## Project layout

```
dj-starter/
├── core/                 # Project package (settings, URLs, Celery, logging, storage)
│   ├── logging/          # structlog + stdlib logging configuration
│   ├── middlewares/      # Trace (request/correlation id), i18n, timezone, 404-JSON
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── storage.py        # S3 upload/static storage backends
├── user/                 # Custom auth app (`AUTH_USER_MODEL`)
├── templates/            # Base HTML templates
├── static/               # App static assets (dev)
├── manage.py
├── Makefile
├── pyproject.toml        # Dependencies and Python version
└── .env.example          # Documented environment variables
```

## Makefile commands

| Target   | Command                      | Purpose                                |
| -------- | ---------------------------- | -------------------------------------- |
| `dev`    | `uv run manage.py runserver` | Run Django development server          |
| `celery` | Worker + beat in background  | Process async tasks and scheduled jobs |

## REST Framework defaults

- Default permission: `IsAuthenticated` (unauthenticated API access is denied unless views override this).
- Default schema: drf-spectacular `AutoSchema`.
- Filtering: `DjangoFilterBackend`.

- Authentication: `SessionAuthentication` and `TokenAuthentication` are enabled by default. `POST /api-token-auth/` issues a token (DRF's `obtain_auth_token`). Add JWT or other classes to `DEFAULT_AUTHENTICATION_CLASSES` as your API grows.

## Celery

- **Broker / result**: Redis URL and Django database for results.
- **Beat**: `django_celery_beat.schedulers.DatabaseScheduler` — schedules are stored in the DB and editable from admin.
- **Tasks**: Auto-discovered from installed apps (see `user/tasks.py` for a sample `@shared_task`).
- **Logging**: Celery uses the same structlog setup as Django (`core/celery.py`).

Example task invocation:

```bash
uv run manage.py shell -c "from user.tasks import test_task; test_task.delay()"
```

## Storage

Uploaded files use `core.storage.UploadsStorage` (private ACL, `uploads/` prefix). Static files for collectstatic use `S3Boto3Storage` with public-read ACL under `static/`. Configure credentials and `ENDPOINT_URL` for your provider; `.env.example` documents Cloudflare R2-style endpoints.

For local-only development without S3, you would need to switch `STORAGES` in `core/settings.py` to Django's filesystem backends—this starter assumes object storage by default.

## Logging

- **Development** (`DEBUG=true`): human-readable, coloured console logs.
- **Production** (`DEBUG=false`): JSON lines via `django-structlog`, ready for log shippers.
- `django-structlog`'s request middleware binds per-request context (user id, client IP). `TraceMiddleware`'s `request_id` / `correlation_id` are bound onto every log line, so logs carry the same ids exposed on the `X-Request-ID` / `X-Correlation-ID` response headers.
- Celery workers share the same configuration (`core/celery.py`).
- Tune verbosity with `LOG_LEVEL` (default `INFO`).

## CORS and frontends

Default allowed origins include `http://localhost:3000` and `http://localhost:5173` (typical React/Vite ports). Adjust `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` in `.env` for your SPA. Credentials are allowed by default (`CORS_ALLOW_CREDENTIALS=true`).

## Environment variables

See [`.env.example`](.env.example) for the full list. Grouped overview:

| Group         | Variables                                                                                                                  |
| ------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Core          | `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`                                                                                     |
| CORS / CSRF   | `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOW_CREDENTIALS`                                                   |
| Data stores   | `DATABASE_URL`, `REDIS_URL`                                                                                                |
| Sessions      | `SESSION_COOKIE_*`                                                                                                         |
| Email         | `EMAIL_*`, `DEFAULT_FROM_EMAIL`                                                                                            |
| API docs      | `ENABLE_OPENAPI`                                                                                                           |
| Storage       | `ACCESS_KEY_ID`, `SECRET_ACCESS_KEY`, `STORAGE_BUCKET_NAME`, `REGION_NAME`, `ENDPOINT_URL`, `STATIC_STORAGE_CUSTOM_DOMAIN` |
| Upload limits | `DATA_UPLOAD_MAX_MEMORY_SIZE`                                                                                              |
| Profiling     | `SILK_ENABLED`                                                                                                             |
| Logging       | `LOG_LEVEL`                                                                                                                |

## Common management commands

```bash
uv run manage.py migrate          # Apply database migrations
uv run manage.py makemigrations   # Create migrations after model changes
uv run manage.py collectstatic    # Upload static files to configured storage
uv run manage.py shell            # Django shell (bpython available in deps)
uv run ruff check .               # Lint (ruff is a project dependency)
```

## Extending the starter

1. **New app** — `uv run manage.py startapp myapp`, add to `LOCAL_APPS` in `core/settings.py`, include URLs under `core/urls.py`.
2. **API routes** — Add DRF viewsets/routers and register them in `urlpatterns`.
3. **Auth** — Session + token auth are enabled by default; add JWT or other classes to `DEFAULT_AUTHENTICATION_CLASSES` and wire login endpoints as needed.
4. **WebSockets** — `CHANNEL_LAYERS` is configured; extend `core/asgi.py` with Channels routing when needed.
5. **Request tracing** — `TraceMiddleware` already issues server-generated `X-Request-ID` / `X-Correlation-ID` headers (inbound values are ignored) and binds them into structlog. Read them in app code via `core.middlewares.get_request_id()` / `get_correlation_id()`.

## Production checklist

- Set `DEBUG=false`, strong `SECRET_KEY`, and explicit `ALLOWED_HOSTS`
- Use HTTPS; set `SESSION_COOKIE_SECURE=true` and tighten cookie settings
- Disable or protect Silk (`SILK_ENABLED=false` or network-restricted)
- Run with **Gunicorn** + **Uvicorn** workers for ASGI, or WSGI-only if you do not use Channels
- Run Celery worker and beat as separate processes (systemd, Docker, or a process manager)
- Point `DATABASE_URL` and `REDIS_URL` at managed services
- Configure real SMTP credentials for email
- Review OpenAPI `SERVE_PERMISSIONS` if you expose docs publicly

## Pre-commit hooks

The repo ships with [`pre-commit`](https://pre-commit.com/) (installed as a dev
dependency) so every commit is linted, formatted, and type-checked automatically.
Hooks are defined in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

| Hook                          | What it does                                              |
| ----------------------------- | -------------------------------------------------------- |
| `ruff check --fix`            | Lint Python and auto-fix what it safely can              |
| `ruff format`                 | Format Python                                            |
| `ty`                          | Static type check                                        |
| file-hygiene (pre-commit-hooks) | Trailing whitespace, EOF newline, YAML/TOML/JSON, merge markers, large files, private keys, LF endings |

`ruff` and `ty` run as **local `uv run` hooks**, so they always use the exact
versions pinned in `uv.lock` — no drift between pre-commit and your project env.

```bash
make hooks-install   # one-time: install the git hook (uv run pre-commit install)
make hooks           # run all hooks against every file (uv run pre-commit run --all-files)
```

After `make hooks-install`, the hooks run automatically on each `git commit`.

## Atomic commits

This project favours **atomic commits**: each commit captures exactly one logical
change and leaves the tree in a working, checkable state. A good rule of thumb —
a commit is atomic when you cannot remove any part of it without breaking the
single idea it expresses, and you cannot add anything to it without introducing
a second idea.

### Why atomic commits

- **Reviewable** — a reviewer reasons about one change at a time.
- **Revertable** — `git revert <sha>` undoes one feature/fix without collateral damage.
- **Bisectable** — `git bisect` can pinpoint the commit that introduced a bug, because every commit builds and passes checks.
- **Readable history** — `git log` reads as a changelog, not a dumping ground.

### Principles

1. **One concern per commit.** A bug fix, a refactor, and a new feature are three commits, not one.
2. **Never break the build.** Each commit should pass `make check` (lint + format + types) on its own. Pre-commit hooks enforce this at commit time (see [Pre-commit hooks](#pre-commit-hooks)).
3. **Separate refactors from behaviour changes.** Move/rename code in one commit, change behaviour in the next — diffs stay readable.
4. **Keep migrations with their model change.** A model edit and its generated migration belong in the same commit so the schema is never out of sync.
5. **No "WIP" or "fix typo" noise on `main`.** Squash or `--fixup` such commits before merging (see [Fixing up commits](#fixing-up-commits)).

### Commit message format

This repo uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <short imperative summary>

<optional body: what changed and why, wrapped at ~72 cols>

<optional footer: BREAKING CHANGE / issue refs, e.g. Closes #42>
```

- Use the **imperative mood**: "add user export", not "added" / "adds".
- Keep the summary **≤ 50 chars**, no trailing period.
- Use the **body** to explain *why*, not *how* — the diff already shows how.

| Type       | Use for                                                        |
| ---------- | ------------------------------------------------------------- |
| `feat`     | A new user-facing feature                                     |
| `fix`      | A bug fix                                                     |
| `refactor` | Code change that neither fixes a bug nor adds a feature       |
| `perf`     | A performance improvement                                     |
| `docs`     | Documentation only                                            |
| `test`     | Adding or fixing tests                                        |
| `chore`    | Tooling, deps, config, CI (no `src` behaviour change)         |
| `style`    | Formatting/whitespace only (no logic change)                  |

Common scopes in this project: `user`, `core`, `celery`, `storage`, `settings`, `deps`.

**Examples**

```
feat(user): add phone-number verification on signup
fix(celery): bind structlog context inside task retries
refactor(core): extract S3 storage backends into storage.py
chore(deps): add pre-commit and wire ruff/ty hooks
```

### Creating an atomic commit

The key skill is **staging selectively** so a single commit holds only one change —
even when your working tree contains several.

```bash
# 1. See what changed.
git status
git diff                      # unstaged changes

# 2. Stage only what belongs in this commit.
git add user/models.py user/migrations/0002_add_phone_verified.py

# 3. Or stage individual hunks within a file (interactive).
git add -p user/views.py      # y/n per hunk; 's' to split, 'e' to edit

# 4. Confirm the staged set is exactly one logical change.
git diff --cached

# 5. Commit. Pre-commit hooks run automatically here.
git commit -m "feat(user): verify phone number on signup"
```

`git add -p` is the workhorse for atomic commits: it lets you commit two unrelated
edits that happen to live in the same file as two separate commits.

### Splitting a messy working tree into atomic commits

When you've already made several unrelated changes, peel them off one at a time:

```bash
git add -p                    # stage hunks for change #1 only
git commit -m "fix(core): ..."
git add -p                    # stage hunks for change #2
git commit -m "refactor(user): ..."
# repeat until `git status` is clean
```

To set aside everything and reapply piece by piece:

```bash
git stash                     # park all changes
git stash pop                 # bring them back, then stage selectively
```

### Pre-commit hooks and atomic commits

Every `git commit` runs the hooks configured in `.pre-commit-config.yaml`
(`ruff check --fix`, `ruff format`, `ty`, plus file-hygiene checks). Because
each commit is small, hook runs are fast and failures are easy to localise.

If a hook **modifies files** (ruff auto-fixing or reformatting), the commit is
aborted so you can review the fixes. Re-stage and commit again:

```bash
git commit -m "feat(user): ..."   # hook reformats a file, commit aborts
git add -u                         # re-stage the hook's fixes
git commit -m "feat(user): ..."   # now it passes
```

Run the full suite manually before committing a large change:

```bash
make hooks        # uv run pre-commit run --all-files
```

> First-time setup after cloning: `make hooks-install` (installs the git hook).

### Fixing up commits

Keep history atomic by amending instead of piling on "fix" commits:

```bash
# Forgot a file or made a typo in the last commit:
git add forgotten_file.py
git commit --amend --no-edit

# Fix something belonging to an earlier commit on your branch:
git commit --fixup <sha>           # creates a "fixup! ..." commit
git rebase -i --autosquash main    # folds fixups into their targets
```

Only amend/rebase commits that **haven't been pushed and shared** — rewriting
public history disrupts collaborators.

### Pre-commit checklist

- [ ] The diff expresses **one** logical change.
- [ ] `git diff --cached` contains nothing unrelated.
- [ ] Model changes ship with their migration.
- [ ] `make check` passes (hooks enforce this).
- [ ] The message follows `type(scope): imperative summary`.

## License

No license has been chosen yet. Until a `LICENSE` file is added and referenced
here, default copyright applies and reuse rights are not granted.
