from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
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
    def run_command(command: list[str], cwd: Path | None = None, timeout: int = 90) -> str:
        process = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0,
        )
        if process.returncode != 0:
            raise RuntimeError(process.stderr.strip() or process.stdout.strip() or "Commando mislukt")
        return process.stdout.strip()

    @staticmethod
    def list_repos() -> list[dict[str, Any]]:
        settings = load_settings()
        root = RepoService.get_repo_root()
        repos = [RepoService.enrich_repo(entry, root) for entry in settings.get("repos", [])]
        return sorted(repos, key=lambda item: (not item["is_new"], not item["has_update"], item["name"].lower()))

    @staticmethod
    def read_json(path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    @staticmethod
    def first_changelog_line(local_path: Path) -> str:
        path = local_path / "CHANGELOG.md"
        if not path.exists():
            return ""
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip().lstrip("-• ")
            if stripped and not stripped.startswith("#"):
                return stripped[:140]
        return ""

    @staticmethod
    def git_summary(local_path: Path) -> dict[str, Any]:
        result: dict[str, Any] = {
            "git_status": "not-cloned",
            "local_sha": "",
            "remote_sha": "",
            "ahead": 0,
            "behind": 0,
            "has_update": False,
            "last_commit": "",
            "last_commit_at": "",
        }
        if not local_path.exists():
            return result
        if not (local_path / ".git").exists():
            result["git_status"] = "not-git"
            return result
        try:
            dirty = RepoService.run_command(["git", "status", "--short"], local_path)
            result["git_status"] = "local-changes" if dirty else "clean"
            result["local_sha"] = RepoService.run_command(["git", "rev-parse", "HEAD"], local_path)
            result["last_commit"] = RepoService.run_command(["git", "log", "-1", "--pretty=%s"], local_path)
            result["last_commit_at"] = RepoService.run_command(["git", "log", "-1", "--pretty=%cI"], local_path)
            RepoService.run_command(["git", "fetch", "--quiet"], local_path, timeout=30)
            remote = RepoService.run_command(["git", "rev-parse", "@{u}"], local_path)
            result["remote_sha"] = remote
            counts = RepoService.run_command(["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"], local_path)
            ahead, behind = [int(value) for value in counts.split()]
            result["ahead"] = ahead
            result["behind"] = behind
            result["has_update"] = behind > 0
        except Exception:
            if result["git_status"] == "not-cloned":
                result["git_status"] = "unknown"
        return result

    @staticmethod
    def health_status(url: str) -> str:
        if not url:
            return "not-configured"
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                return "healthy" if 200 <= response.status < 300 else "unhealthy"
        except (urllib.error.URLError, TimeoutError, ValueError):
            return "offline"

    @staticmethod
    def deployment_readiness(manifest: dict[str, Any], git_info: dict[str, Any]) -> dict[str, Any]:
        deployment = manifest.get("deployment") or {}
        security = manifest.get("security") or {}
        runtime = manifest.get("runtime") or {}
        checks = {
            "manifest": bool(manifest),
            "clean_git": git_info["git_status"] == "clean",
            "up_to_date": not git_info["has_update"],
            "runtime": bool(runtime or manifest.get("start_command")),
            "healthcheck": bool(runtime.get("health_path") or manifest.get("health_url")),
            "rate_limit_declared": security.get("rate_limiting") is True or not security.get("public_api", False),
            "deployment_configured": bool(deployment.get("provider") or deployment.get("public_url")),
        }
        required = ["manifest", "clean_git", "up_to_date", "runtime", "healthcheck", "rate_limit_declared"]
        ready = all(checks[key] for key in required)
        return {"ready": ready, "checks": checks}

    @staticmethod
    def enrich_repo(entry: dict[str, Any], root: Path) -> dict[str, Any]:
        slug = entry["slug"]
        local_path = root / slug
        manifest = RepoService.read_json(local_path / "turbo-project.json") if local_path.exists() else {}
        runtime = manifest.get("runtime") or {}
        deployment = manifest.get("deployment") or {}
        integrations = manifest.get("integrations") or {}
        preview = manifest.get("preview") or entry.get("preview") or ""
        preview_path = local_path / preview if preview else None
        git_info = RepoService.git_summary(local_path)
        running = slug in RUNTIME_STATE and RUNTIME_STATE[slug].poll() is None
        health_url = manifest.get("health_url") or (
            f"http://127.0.0.1:{runtime.get('port')}{runtime.get('health_path', '/health')}"
            if runtime.get("port") else ""
        )
        readiness = RepoService.deployment_readiness(manifest, git_info)
        updated_at = entry.get("updated_at") or git_info.get("last_commit_at") or ""
        return {
            **entry,
            **git_info,
            "name": manifest.get("name") or entry.get("name") or slug,
            "version": manifest.get("version") or entry.get("version") or "-",
            "description": manifest.get("description") or entry.get("description") or "",
            "start_command": runtime.get("start_command") or manifest.get("start_command") or "",
            "preview_url": f"/repo-file/{slug}/{preview}" if preview_path and preview_path.exists() else "",
            "health_url": health_url,
            "health_status": RepoService.health_status(health_url) if running else "offline",
            "default_port": runtime.get("port") or manifest.get("default_port") or "",
            "local_path": str(local_path),
            "exists": local_path.exists(),
            "is_new": not local_path.exists(),
            "is_running": running,
            "is_live": bool(deployment.get("public_url")),
            "public_url": deployment.get("public_url") or "",
            "deployment_provider": deployment.get("provider") or "",
            "deploy_ready": readiness["ready"],
            "deploy_checks": readiness["checks"],
            "changelog_summary": RepoService.first_changelog_line(local_path) if local_path.exists() else "",
            "updated_at": updated_at,
            "tags": manifest.get("tags") or entry.get("tags") or [],
            "integrations": integrations,
            "data_mode": (manifest.get("data") or {}).get("mode") or "none",
        }

    @staticmethod
    def add_repo(repo_url: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        slug = repo_slug_from_url(repo_url)
        if not slug:
            raise ValueError("Ongeldige GitHub URL")
        settings = load_settings()
        existing = next((item for item in settings["repos"] if item["slug"] == slug), None)
        if existing:
            if metadata:
                existing.update({key: value for key, value in metadata.items() if value is not None})
                save_settings(settings)
            return RepoService.enrich_repo(existing, RepoService.get_repo_root())
        metadata = metadata or {}
        entry = {
            "slug": slug,
            "repo_url": repo_url,
            "name": metadata.get("name") or slug.replace("-", " ").title(),
            "description": metadata.get("description") or "",
            "is_private": bool(metadata.get("is_private", False)),
            "updated_at": metadata.get("updated_at") or "",
            "tags": metadata.get("tags") or [],
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
        if RepoService.github_cli_available():
            return
        if not sys.platform.startswith("win"):
            raise RuntimeError("Installeer GitHub CLI handmatig op dit besturingssysteem.")
        subprocess.Popen('start "GitHub CLI installatie" cmd /k "winget install --id GitHub.cli -e --source winget"', shell=True)

    @staticmethod
    def start_github_login() -> None:
        if not RepoService.github_cli_available():
            raise RuntimeError("Installeer eerst GitHub CLI.")
        command = ["gh", "auth", "login", "--web", "--hostname", "github.com", "--git-protocol", "https"]
        if sys.platform.startswith("win"):
            subprocess.Popen('start "GitHub Login" cmd /k "gh auth login --web --hostname github.com --git-protocol https"', shell=True)
        else:
            subprocess.Popen(command)

    @staticmethod
    def import_github_repos() -> dict[str, Any]:
        status = RepoService.github_status()
        if not status["authenticated"]:
            raise RuntimeError("Log eerst in bij GitHub.")
        raw = RepoService.run_command([
            "gh", "repo", "list", status["username"], "--limit", "1000", "--json",
            "name,url,description,isPrivate,updatedAt,primaryLanguage"
        ])
        discovered = json.loads(raw or "[]")
        imported = 0
        for item in discovered:
            before = len(load_settings().get("repos", []))
            language = (item.get("primaryLanguage") or {}).get("name")
            RepoService.add_repo(item["url"], {
                "name": item.get("name"),
                "description": item.get("description") or "",
                "is_private": item.get("isPrivate", False),
                "updated_at": item.get("updatedAt") or "",
                "tags": [language] if language else [],
            })
            imported += int(len(load_settings().get("repos", [])) > before)
        return {"username": status["username"], "found": len(discovered), "imported": imported, "repos": RepoService.list_repos()}

    @staticmethod
    def sync_repo(slug: str) -> dict[str, Any]:
        repo = RepoService.get_repo(slug)
        local_path = Path(repo["local_path"])
        root = RepoService.get_repo_root()
        if not local_path.exists():
            RepoService.run_command(["git", "clone", repo["repo_url"], str(local_path)], root, timeout=180)
        else:
            if repo["git_status"] == "local-changes":
                raise RuntimeError("Lokale wijzigingen gevonden. Update is geblokkeerd om werk niet te overschrijven.")
            RepoService.run_command(["git", "fetch"], local_path)
            RepoService.run_command(["git", "pull", "--ff-only"], local_path)
        return RepoService.get_repo(slug)

    @staticmethod
    def run_tests(slug: str) -> dict[str, Any]:
        repo = RepoService.get_repo(slug)
        path = Path(repo["local_path"])
        if not path.exists():
            raise RuntimeError("Synchroniseer de repo eerst.")
        manifest = RepoService.read_json(path / "turbo-project.json")
        test_command = (manifest.get("testing") or {}).get("command")
        if not test_command:
            if (path / "tests").exists():
                test_command = "python -m pytest -q"
            else:
                raise RuntimeError("Geen testcommando geconfigureerd.")
        process = subprocess.run(test_command, cwd=str(path), shell=True, capture_output=True, text=True, timeout=300)
        return {"ok": process.returncode == 0, "output": (process.stdout + "\n" + process.stderr).strip()[-5000:]}

    @staticmethod
    def deployment_plan(slug: str) -> dict[str, Any]:
        repo = RepoService.get_repo(slug)
        if not repo["deploy_ready"]:
            failed = [key for key, value in repo["deploy_checks"].items() if not value]
            return {"ready": False, "failed_checks": failed, "message": "Los eerst de ontbrekende controles op."}
        return {
            "ready": True,
            "provider": repo["deployment_provider"] or "not-selected",
            "public_url": repo["public_url"],
            "message": "Repo is technisch klaar. Selecteer en configureer eerst bewust een hostingprovider.",
        }

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
        proc = subprocess.Popen(f'cmd /c "{command}"' if sys.platform.startswith("win") else command, cwd=str(local_path), shell=True)
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
