from __future__ import annotations

import json
from pathlib import Path

APP_NAME = "Turbo Repo Launcher"
APP_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = APP_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
CONFIG_FILE = DATA_DIR / "settings.json"
DEFAULT_REPO_ROOT = Path.home() / "TurboRepos"
DEFAULT_REPO_ROOT.mkdir(parents=True, exist_ok=True)

DEFAULT_SETTINGS = {
    "repo_root": str(DEFAULT_REPO_ROOT),
    "repos": [],
}


def load_settings() -> dict:
    if not CONFIG_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    CONFIG_FILE.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
