from __future__ import annotations

import hashlib
import uuid


def normalize_teacher_email(email: str | None) -> str:
    return (email or "").strip().lower()


def generate_teacher_id(*, teacher_email: str | None = None) -> str:
    normalized_email = normalize_teacher_email(teacher_email)
    if normalized_email:
        digest = hashlib.sha256(normalized_email.encode()).hexdigest()[:16]
        return f"teacher_{digest}"

    return f"teacher_{uuid.uuid4().hex[:16]}"
