from __future__ import annotations

import re


def repo_slug_from_url(repo_url: str) -> str:
    cleaned = repo_url.strip().rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    slug = cleaned.split("/")[-1]
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", slug)
    return slug.lower()
