from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .config import DEFAULT_REPO_ROOT, load_settings, save_settings
from .utils import repo_slug_from_url

RUNTIME_STATE: dict[str, subprocess.Popen] = {}


class RepoService:
    @staticmethod
    def get_repo_root() -> Path:
        settings = load_settings()
        root = Path(settings.get("repo_root") or DEFAULT_REPO_ROOT).expanduser()
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def set_repo_root(repo_root: str) -> None:
        root = Path(repo_root).expanduser()
        root.mkdir(parents=True, exist_ok=True)
        settings = load_settings()
        settings["repo_root"] = str(root)
        save_settings(settings)

    @staticmethod
    def run_command(command: list[str], cwd: Path | None = None, timeout: int = 90) -> str:
        process = subprocess.run(command, cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=timeout)
        if process.returncode != 0:
            raise RuntimeError(process.stderr.strip() or process.stdout.strip() or "Commando mislukt")
        return process.stdout.strip()

    @staticmethod
    def read_json(path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    @staticmethod
    def git_info(path: Path) -> dict[str, Any]:
        result = {"git_status": "not-cloned", "has_update": False, "ahead": 0, "behind": 0, "last_commit": "", "last_commit_at": ""}
        if not path.exists():
            return result
        if not (path / ".git").exists():
            result["git_status"] = "not-git"
            return result
        try:
            result["git_status"] = "local-changes" if RepoService.run_command(["git", "status", "--short"], path) else "clean"
            result["last_commit"] = RepoService.run_command(["git", "log", "-1", "--pretty=%s"], path)
            result["last_commit_at"] = RepoService.run_command(["git", "log", "-1", "--pretty=%cI"], path)
            RepoService.run_command(["git", "fetch", "--quiet"], path, timeout=30)
            counts = RepoService.run_command(["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"], path)
            ahead, behind = [int(v) for v in counts.split()]
            result.update({"ahead": ahead, "behind": behind, "has_update": behind > 0})
        except Exception:
            pass
        return result

    @staticmethod
    def enrich_repo(entry: dict[str, Any], root: Path) -> dict[str, Any]:
        slug = entry["slug"]
        path = root / slug
        manifest = RepoService.read_json(path / "turbo-project.json") if path.exists() else {}
        runtime = manifest.get("runtime") or {}
        deployment = manifest.get("deployment") or {}
        preview = manifest.get("preview") or ""
        info = RepoService.git_info(path)
        running = slug in RUNTIME_STATE and RUNTIME_STATE[slug].poll() is None
        health_url = manifest.get("health_url") or (f"http://127.0.0.1:{runtime.get('port')}{runtime.get('health_path', '/health')}" if runtime.get("port") else "")
        return {
            **entry,
            **info,
            "name": manifest.get("name") or entry.get("name") or slug,
            "version": manifest.get("version") or entry.get("version") or "-",
            "description": manifest.get("description") or entry.get("description") or "",
            "start_command": runtime.get("start_command") or manifest.get("start_command") or "",
            "preview_url": f"/repo-file/{slug}/{preview}" if preview and (path / preview).exists() else "",
            "health_url": health_url,
            "health_status": "offline",
            "default_port": runtime.get("port") or manifest.get("default_port") or "",
            "local_path": str(path),
            "exists": path.exists(),
            "is_new": not path.exists(),
            "is_running": running,
            "is_live": bool(deployment.get("public_url")),
            "public_url": deployment.get("public_url") or "",
            "deployment_provider": deployment.get("provider") or "",
            "deploy_ready": bool(manifest) and info["git_status"] == "clean" and not info["has_update"],
            "deploy_checks": {},
            "changelog_summary": info.get("last_commit") or "",
            "updated_at": entry.get("updated_at") or info.get("last_commit_at") or "",
            "tags": manifest.get("tags") or entry.get("tags") or [],
            "integrations": manifest.get("integrations") or {},
            "data_mode": (manifest.get("data") or {}).get("mode") or "none",
        }

    @staticmethod
    def list_repos() -> list[dict[str, Any]]:
        root = RepoService.get_repo_root()
        repos = [RepoService.enrich_repo(item, root) for item in load_settings().get("repos", [])]
        return sorted(repos, key=lambda item: (not item["is_new"], not item["has_update"], item["name"].lower()))

    @staticmethod
    def add_repo(repo_url: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        slug = repo_slug_from_url(repo_url)
        if not slug:
            raise ValueError("Ongeldige GitHub URL")
        metadata = metadata or {}
        settings = load_settings()
        existing = next((x for x in settings.get("repos", []) if x["slug"] == slug), None)
        if existing:
            existing.update({k: v for k, v in metadata.items() if v is not None})
        else:
            settings.setdefault("repos", []).append({"slug": slug, "repo_url": repo_url, "name": metadata.get("name") or slug.replace("-", " ").title(), "description": metadata.get("description") or "", "is_private": bool(metadata.get("is_private", False)), "updated_at": metadata.get("updated_at") or "", "tags": metadata.get("tags") or []})
        save_settings(settings)
        return RepoService.get_repo(slug)

    @staticmethod
    def get_repo(slug: str) -> dict[str, Any]:
        for repo in RepoService.list_repos():
            if repo["slug"] == slug:
                return repo
        raise FileNotFoundError(f"Repo {slug} niet gevonden")

    @staticmethod
    def github_cli_available() -> bool:
        return shutil.which("gh") is not None

    @staticmethod
    def github_status() -> dict[str, Any]:
        if not RepoService.github_cli_available():
            return {"cli_installed": False, "authenticated": False, "username": "", "message": "GitHub CLI ontbreekt."}
        try:
            RepoService.run_command(["gh", "auth", "status", "--hostname", "github.com"])
            username = RepoService.run_command(["gh", "api", "user", "--jq", ".login"])
            return {"cli_installed": True, "authenticated": True, "username": username, "message": f"Ingelogd als {username}"}
        except Exception as exc:
            return {"cli_installed": True, "authenticated": False, "username": "", "message": str(exc)}

    @staticmethod
    def install_github_cli() -> None:
        if not RepoService.github_cli_available():
            subprocess.Popen('start "GitHub CLI installatie" cmd /k "winget install --id GitHub.cli -e --source winget"', shell=True)

    @staticmethod
    def start_github_login() -> None:
        if not RepoService.github_cli_available():
            raise RuntimeError("Installeer eerst GitHub CLI.")
        subprocess.Popen('start "GitHub Login" cmd /k "gh auth login --web --hostname github.com --git-protocol https"', shell=True)

    @staticmethod
    def import_github_repos() -> dict[str, Any]:
        status = RepoService.github_status()
        if not status["authenticated"]:
            raise RuntimeError("Log eerst in bij GitHub.")
        raw = RepoService.run_command(["gh", "repo", "list", status["username"], "--limit", "1000", "--json", "name,url,description,isPrivate,updatedAt,primaryLanguage"])
        discovered = json.loads(raw or "[]")
        before = len(load_settings().get("repos", []))
        for item in discovered:
            language = (item.get("primaryLanguage") or {}).get("name")
            RepoService.add_repo(item["url"], {"name": item.get("name"), "description": item.get("description") or "", "is_private": item.get("isPrivate", False), "updated_at": item.get("updatedAt") or "", "tags": [language] if language else []})
        after = len(load_settings().get("repos", []))
        return {"username": status["username"], "found": len(discovered), "imported": after - before, "repos": RepoService.list_repos()}

    @staticmethod
    def sync_repo(slug: str) -> dict[str, Any]:
        repo = RepoService.get_repo(slug)
        path = Path(repo["local_path"])
        if not path.exists():
            RepoService.run_command(["git", "clone", repo["repo_url"], str(path)], RepoService.get_repo_root(), timeout=180)
        else:
            if repo["git_status"] == "local-changes":
                raise RuntimeError("Lokale wijzigingen gevonden. Update is geblokkeerd.")
            RepoService.run_command(["git", "pull", "--ff-only"], path)
        return RepoService.get_repo(slug)

    @staticmethod
    def run_tests(slug: str) -> dict[str, Any]:
        repo = RepoService.get_repo(slug)
        path = Path(repo["local_path"])
        process = subprocess.run("python -m pytest -q", cwd=str(path), shell=True, capture_output=True, text=True, timeout=300)
        return {"ok": process.returncode == 0, "output": (process.stdout + "\n" + process.stderr).strip()[-5000:]}

    @staticmethod
    def deployment_plan(slug: str) -> dict[str, Any]:
        repo = RepoService.get_repo(slug)
        return {"ready": repo["deploy_ready"], "provider": repo["deployment_provider"] or "not-selected", "public_url": repo["public_url"], "message": "Repo is technisch klaar." if repo["deploy_ready"] else "Werk eerst de controles af."}

    @staticmethod
    def start_repo(slug: str) -> dict[str, Any]:
        repo = RepoService.get_repo(slug)
        path = Path(repo["local_path"])
        if not path.exists():
            raise RuntimeError("Synchroniseer de repo eerst.")
        command = repo.get("start_command")
        if not command:
            raise RuntimeError("Geen startcommando geconfigureerd.")
        proc = subprocess.Popen(f'cmd /c "{command}"' if sys.platform.startswith("win") else command, cwd=str(path), shell=True)
        RUNTIME_STATE[slug] = proc
        time.sleep(1)
        return RepoService.get_repo(slug)

    @staticmethod
    def stop_repo(slug: str) -> dict[str, Any]:
        proc = RUNTIME_STATE.get(slug)
        if proc and proc.poll() is None:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True) if sys.platform.startswith("win") else proc.terminate()
        RUNTIME_STATE.pop(slug, None)
        return RepoService.get_repo(slug)

    @staticmethod
    def open_folder(slug: str) -> None:
        path = RepoService.get_repo(slug)["local_path"]
        os.startfile(path) if sys.platform.startswith("win") else subprocess.Popen(["xdg-open", path])

    @staticmethod
    def open_vscode(slug: str) -> None:
        subprocess.Popen(["code", RepoService.get_repo(slug)["local_path"]])
