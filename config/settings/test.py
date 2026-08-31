from .base import *  # noqa: F403

DEBUG = False

# Fast in-memory SQLite database for rapid local pytest runs
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Fast in-memory cache for test environment
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "job-queue-test-cache",
    }
}

# In-memory synchronous Celery tasks for unit tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Fast password hashing to speed up test execution
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
