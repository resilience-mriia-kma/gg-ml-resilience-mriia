---
name: Config values belong in .env
description: Configuration values like file paths should be loaded from .env via django-environ, not hardcoded in settings.py
type: feedback
---

Configuration values (file paths, API keys, feature flags) should be read from `.env` using `django-environ`, not hardcoded in `settings.py`.

**Why:** The user wants all environment-specific configuration centralized in `.env` files, keeping `settings.py` as a loader, not a source of truth.

**How to apply:** Always use `env()` calls in `settings.py` and add corresponding entries to `.env` / `.env.example`.
