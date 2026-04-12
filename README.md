# InApp Update Manager

A minimal, production-ready Django + DRF backend for managing Android in-app APK updates (InApp Update Manager).

Admins upload APK releases via Django Admin. A Flutter app polls a public REST endpoint to check for updates and download the latest APK.

---

## Project Structure

```
.
├── apps/
│   └── ota/                  # InApp update feature (Clean Architecture)
│       ├── domain/           # Domain layer (entities, exceptions, repositories)
│       │   ├── entities.py   # Domain entities
│       │   ├── exceptions.py # Domain exceptions
│       │   └── repositories.py # Abstract repositories
│       ├── infrastructure/   # Infrastructure layer (concrete implementations)
│       │   ├── admin.py      # Admin panel config
│       │   ├── di.py         # Dependency injection factory
│       │   ├── orm_models.py # Django ORM models
│       │   ├── repositories.py # Concrete repository implementations
│       │   ├── storage.py    # File storage backend
│       │   └── migrations/   # DB migrations
│       ├── interfaces/       # Interfaces layer (adapters)
│       │   ├── api/          # REST API adapters
│       │   │   ├── serializers.py # DRF serializers
│       │   │   └── views.py  # API views (controllers)
│       │   └── ui/           # UI adapters (if any)
│       └── use_cases/        # Use cases (application logic)
│           ├── get_latest_update.py
│           └── get_update_history.py
├── config/                   # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                     # Shared utilities (health checks, logging, exceptions)
├── test/                     # Tests
│   └── test_ota_api.py
├── media/                    # APK uploads (auto-created, git-ignored)
├── requirements/
│   └── base.txt
├── .env.example
├── Dockerfile
├── Makefile
└── manage.py
```

---

## Quick Start (Local Dev)

### 1. Clone & setup

```bash
git clone <repo-url>
cd django-app-ota-update

cp example.env .env
# Edit .env with your Postgres credentials
```

### 2. Create virtual environment & install deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/base.txt
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Create superuser (for admin panel)

```bash
python manage.py createsuperuser
```

### 5. Start dev server

```bash
python manage.py runserver
```

### Media storage (local vs MinIO)

- Default: uploaded APKs are stored on local disk under `media/apks/` and served via `MEDIA_URL`.
- To use MinIO (or any S3-compatible storage), set these env vars (see `.env.example`):
  ```bash
  MINIO_ENABLED=True
  MINIO_ENDPOINT_URL=http://localhost:9000   # or https://minio.yourdomain.com
  MINIO_BUCKET_NAME=ota-media
  MINIO_ACCESS_KEY_ID=...
  MINIO_SECRET_KEY=...
  MINIO_REGION_NAME=us-east-1
  MINIO_USE_SSL=False
  ```
- No model changes are required; the `FileField` writes to the configured storage backend.

### URLs

| URL | Description |
|---|---|
| `http://127.0.0.1:8000/admin/` | Django Admin (upload APKs here) |
| `http://127.0.0.1:8000/api/update/` | Latest APK release |
| `http://127.0.0.1:8000/api/updates/` | Full release history |
| `http://127.0.0.1:8000/docs/` | Swagger UI |
| `http://127.0.0.1:8000/health/` | Health check |
| `http://127.0.0.1:8000/health/db/` | Database health check |

---

## Docker Compose (Recommended)

```bash
make up        # Build and start (Django + PostgreSQL)
make migrate   # Run DB migrations
make superuser # Create admin user
make test      # Run tests
make down      # Stop containers
```

Notes (local compose):
- Exposes Django on `http://localhost:8003`, MinIO API on `http://localhost:9000`, console on `http://localhost:9001` (credentials: `minioadmin` / `minioadmin`).
- MinIO bucket `ota-media` is auto-created by the storage backend on first use. Toggle storage via `MINIO_ENABLED` envs in `docker/compose/local.yml`.

---

## API Reference

### `GET /api/update/`

Returns the latest APK release for the specified app.

**Query Parameters:**
- `package` (string, required): Android package name of the app, e.g., `com.example.merchant`.

**Response 200:**
```json
{
    "version": "1.2.0",
    "apk_url": "https://yourdomain.com/media/apks/app.apk",
    "force_update": true,
    "changelog": "Bug fixes and performance improvements",
    "min_supported_version": "1.0.0",
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Response 400** (missing package):
```json
{
    "detail": "Missing required query parameter: 'package'."
}
```

**Response 404** (app not found or no releases):
```json
{
    "detail": "App not found."  // or "No updates available."
}
```

---

### `GET /api/updates/`

Returns full release history for the specified app, newest first.

**Query Parameters:**
- `package` (string, required): Android package name of the app, e.g., `com.example.merchant`.

**Response 200:**
```json
[
    { "version": "1.2.0", "apk_url": "...", "force_update": true, ... },
    { "version": "1.1.0", "apk_url": "...", "force_update": false, ... }
]
```

**Response 400** (missing package):
```json
{
    "detail": "Missing required query parameter: 'package'."
}
```

**Response 404** (app not found):
```json
{
    "detail": "App not found."
}
```

---

## Optional: API Key Protection

Set a non-empty `API_KEY` in `.env`. Then send the key in every API request:

```
X-API-Key: your-secret-key
```

The key is available in `settings.OTA_API_KEY`. Wire it into a custom DRF permission class if you need enforced protection (the setting is ready for that).

---

## Model: `AppUpdate`

| Field | Type | Description |
|---|---|---|
| `version` | CharField (unique) | Semver string, e.g. `1.2.0` |
| `apk_file` | FileField | Uploaded to `media/apks/` (or MinIO bucket). Max 500 MB |
| `force_update` | BooleanField | If true, Flutter app must update |
| `changelog` | TextField | Release notes (optional) |
| `min_supported_version` | CharField | Minimum upgradeable version (optional) |
| `created_at` | DateTimeField | Set automatically |

---

## Running Tests

```bash
# Local (no DB required — Django's test runner uses SQLite)
source .venv/bin/activate
pytest

# Docker
make test
```

---

## Production Deployment

### Option A — Gunicorn + Nginx

1. **Set env vars** on the server (never commit `.env`):
   ```bash
   SECRET_KEY=<strong-random-key>
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com
   POSTGRES_HOST=<db-host>
   ...
   ```

2. **Collect static files:**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Start Gunicorn:**
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
   ```

4. **Nginx config snippet:**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location /media/ {
           alias /path/to/project/media/;
       }

       location /static/ {
           alias /path/to/project/staticfiles/;
       }

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

### Option B — AWS S3 for APK Storage (Recommended for Production)

Install `django-storages` and `boto3`:

```bash
pip install django-storages boto3
```

Add to `settings.py`:

```python
INSTALLED_APPS += ["storages"]

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_REGION", "ap-southeast-1")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "public-read"

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"
```

APKs will now be uploaded directly to S3 and served via CDN URL.

---

## Security Notes

- `DEBUG=False` in production
- Set a strong random `SECRET_KEY`
- Add your domain to `ALLOWED_HOSTS`
- Use HTTPS (Nginx + Let's Encrypt)
- Django Admin is protected by login — create only one superuser account
