from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .config import DEFAULT_REPO_ROOT, load_settings, save_settings
from .utils import repo_slug_from_url

RUNTIME_STATE: dict[str, subprocess.Popen] = {}


class RepoService:
    @staticmethod
    def get_repo_root() -> Path:
        settings = load_settings()
        repo_root = Path(settings.get("repo_root") or DEFAULT_REPO_ROOT)
        repo_root.mkdir(parents=True, exist_ok=True)
        return repo_root

    @staticmethod
    def set_repo_root(repo_root: str) -> None:
        settings = load_settings()
        root = Path(repo_root).expanduser()
        root.mkdir(parents=True, exist_ok=True)
        settings["repo_root"] = str(root)
        save_settings(settings)

    @staticmethod
    def list_repos() -> list[dict[str, Any]]:
        settings = load_settings()
        root = RepoService.get_repo_root()
        return [RepoService.enrich_repo(entry, root) for entry in settings.get("repos", [])]

    @staticmethod
    def enrich_repo(entry: dict[str, Any], root: Path) -> dict[str, Any]:
        slug = entry["slug"]
        local_path = root / slug
        manifest = {}
        manifest_path = local_path / "turbo-project.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                manifest = {}

        preview = manifest.get("preview") or ""
        preview_path = local_path / preview if preview else None
        preview_url = f"/repo-file/{slug}/{preview}" if preview_path and preview_path.exists() else ""
        running = slug in RUNTIME_STATE and RUNTIME_STATE[slug].poll() is None

        return {
            **entry,
            "name": manifest.get("name") or entry.get("name") or slug,
            "version": manifest.get("version") or "-",
            "description": manifest.get("description") or entry.get("description") or "",
            "start_command": manifest.get("start_command") or "",
            "preview_url": preview_url,
            "health_url": manifest.get("health_url") or "",
            "default_port": manifest.get("default_port") or "",
            "local_path": str(local_path),
            "exists": local_path.exists(),
            "git_status": RepoService.git_status(local_path) if local_path.exists() else "not-cloned",
            "is_running": running,
        }

    @staticmethod
    def add_repo(repo_url: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        slug = repo_slug_from_url(repo_url)
        if not slug:
            raise ValueError("Ongeldige GitHub URL")
        settings = load_settings()
        existing = next((r for r in settings["repos"] if r["slug"] == slug), None)
        if existing:
            if metadata:
                existing.update({key: value for key, value in metadata.items() if value is not None})
                save_settings(settings)
            return RepoService.enrich_repo(existing, RepoService.get_repo_root())
        entry = {
            "slug": slug,
            "repo_url": repo_url,
            "name": (metadata or {}).get("name") or slug.replace("-", " ").title(),
            "description": (metadata or {}).get("description") or "",
            "is_private": bool((metadata or {}).get("is_private", False)),
            "updated_at": (metadata or {}).get("updated_at") or "",
        }
        settings["repos"].append(entry)
        save_settings(settings)
        return RepoService.enrich_repo(entry, RepoService.get_repo_root())

    @staticmethod
    def get_repo(slug: str) -> dict[str, Any]:
        for repo in RepoService.list_repos():
            if repo["slug"] == slug:
                return repo
        raise FileNotFoundError(f"Repo {slug} niet gevonden")

    @staticmethod
    def run_command(command: list[str], cwd: Path | None = None) -> str:
        process = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0,
        )
        if process.returncode != 0:
            raise RuntimeError(process.stderr.strip() or process.stdout.strip() or "Commando mislukt")
        return process.stdout.strip()

    @staticmethod
    def github_cli_available() -> bool:
        return shutil.which("gh") is not None

    @staticmethod
    def github_status() -> dict[str, Any]:
        if not RepoService.github_cli_available():
            return {
                "cli_installed": False,
                "authenticated": False,
                "username": "",
                "message": "GitHub CLI is nog niet geïnstalleerd.",
            }
        try:
            RepoService.run_command(["gh", "auth", "status", "--hostname", "github.com"])
            username = RepoService.run_command(["gh", "api", "user", "--jq", ".login"])
            return {
                "cli_installed": True,
                "authenticated": True,
                "username": username,
                "message": f"Ingelogd als {username}",
            }
        except Exception as exc:
            return {
                "cli_installed": True,
                "authenticated": False,
                "username": "",
                "message": str(exc),
            }

    @staticmethod
    def install_github_cli() -> None:
        if RepoService.github_cli_available():
            return
        if not sys.platform.startswith("win"):
            raise RuntimeError("Installeer GitHub CLI handmatig op dit besturingssysteem.")
        subprocess.Popen(
            'start "GitHub CLI installatie" cmd /k "winget install --id GitHub.cli -e --source winget"',
            shell=True,
        )

    @staticmethod
    def start_github_login() -> None:
        if not RepoService.github_cli_available():
            raise RuntimeError("Installeer eerst GitHub CLI.")
        if sys.platform.startswith("win"):
            subprocess.Popen(
                'start "GitHub Login" cmd /k "gh auth login --web --hostname github.com --git-protocol https"',
                shell=True,
            )
        else:
            subprocess.Popen(["gh", "auth", "login", "--web", "--hostname", "github.com", "--git-protocol", "https"])

    @staticmethod
    def import_github_repos() -> dict[str, Any]:
        status = RepoService.github_status()
        if not status["authenticated"]:
            raise RuntimeError("Log eerst in bij GitHub.")

        raw = RepoService.run_command([
            "gh",
            "repo",
            "list",
            status["username"],
            "--limit",
            "1000",
            "--json",
            "name,url,description,isPrivate,updatedAt",
        ])
        discovered = json.loads(raw or "[]")
        imported = 0
        for item in discovered:
            before = len(load_settings().get("repos", []))
            RepoService.add_repo(
                item["url"],
                {
                    "name": item.get("name"),
                    "description": item.get("description") or "",
                    "is_private": item.get("isPrivate", False),
                    "updated_at": item.get("updatedAt") or "",
                },
            )
            after = len(load_settings().get("repos", []))
            if after > before:
                imported += 1
        return {
            "username": status["username"],
            "found": len(discovered),
            "imported": imported,
            "repos": RepoService.list_repos(),
        }

    @staticmethod
    def git_status(local_path: Path) -> str:
        if not (local_path / ".git").exists():
            return "not-git"
        try:
            return "local-changes" if RepoService.run_command(["git", "status", "--short"], local_path) else "clean"
        except Exception:
            return "unknown"

    @staticmethod
    def sync_repo(slug: str) -> dict[str, Any]:
        repo = RepoService.get_repo(slug)
        local_path = Path(repo["local_path"])
        root = RepoService.get_repo_root()
        if not local_path.exists():
            RepoService.run_command(["git", "clone", repo["repo_url"], str(local_path)], root)
        else:
            if RepoService.git_status(local_path) == "local-changes":
                raise RuntimeError("Lokale wijzigingen gevonden. Sync is geblokkeerd om werk niet te overschrijven.")
            RepoService.run_command(["git", "fetch"], local_path)
            RepoService.run_command(["git", "pull", "--ff-only"], local_path)
        return RepoService.get_repo(slug)

    @staticmethod
    def start_repo(slug: str) -> dict[str, Any]:
        repo = RepoService.get_repo(slug)
        local_path = Path(repo["local_path"])
        if not local_path.exists():
            raise FileNotFoundError("Synchroniseer de repo eerst")
        command = repo.get("start_command") or ""
        if not command:
            raise RuntimeError("Geen start_command gevonden in turbo-project.json")
        if slug in RUNTIME_STATE and RUNTIME_STATE[slug].poll() is None:
            return RepoService.get_repo(slug)
        if sys.platform.startswith("win"):
            proc = subprocess.Popen(f'cmd /c "{command}"', cwd=str(local_path), shell=True)
        else:
            proc = subprocess.Popen(command, cwd=str(local_path), shell=True)
        RUNTIME_STATE[slug] = proc
        time.sleep(1)
        return RepoService.get_repo(slug)

    @staticmethod
    def stop_repo(slug: str) -> dict[str, Any]:
        proc = RUNTIME_STATE.get(slug)
        if proc and proc.poll() is None:
            if sys.platform.startswith("win"):
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
            else:
                proc.terminate()
        RUNTIME_STATE.pop(slug, None)
        return RepoService.get_repo(slug)

    @staticmethod
    def open_folder(slug: str) -> None:
        path = RepoService.get_repo(slug)["local_path"]
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    @staticmethod
    def open_vscode(slug: str) -> None:
        subprocess.Popen(["code", RepoService.get_repo(slug)["local_path"])
