from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import APP_NAME
from .models import RepoAddRequest, RepoRootUpdateRequest
from .services_fixed import RepoService

app = FastAPI(title=APP_NAME)
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/health")
def health() -> dict:
    return {"ok": True, "app": APP_NAME, "version": "0.3.1"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "app_name": APP_NAME,
        "repos": RepoService.list_repos(),
        "repo_root": str(RepoService.get_repo_root()),
    })


@app.get("/api/repos")
def list_repos():
    return {"repos": RepoService.list_repos(), "repo_root": str(RepoService.get_repo_root())}


@app.get("/api/github/status")
def github_status():
    return RepoService.github_status()


@app.post("/api/github/install")
def github_install():
    try:
        RepoService.install_github_cli()
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/github/login")
def github_login():
    try:
        RepoService.start_github_login()
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/github/import")
def github_import():
    try:
        return RepoService.import_github_repos()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/repos")
def add_repo(payload: RepoAddRequest):
    try:
        return {"repo": RepoService.add_repo(payload.repo_url)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/settings/repo-root")
def update_repo_root(payload: RepoRootUpdateRequest):
    try:
        RepoService.set_repo_root(payload.repo_root)
        return {"repo_root": str(RepoService.get_repo_root())}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/repos/{slug}/sync")
def sync_repo(slug: str):
    try:
        return {"repo": RepoService.sync_repo(slug)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/repos/{slug}/test")
def test_repo(slug: str):
    try:
        return RepoService.run_tests(slug)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/repos/{slug}/publish-plan")
def publish_plan(slug: str):
    try:
        return RepoService.deployment_plan(slug)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/repos/{slug}/start")
def start_repo(slug: str):
    try:
        return {"repo": RepoService.start_repo(slug)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/repos/{slug}/stop")
def stop_repo(slug: str):
    try:
        return {"repo": RepoService.stop_repo(slug)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/repos/{slug}/open-folder")
def open_folder(slug: str):
    try:
        RepoService.open_folder(slug)
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/repos/{slug}/open-vscode")
def open_vscode(slug: str):
    try:
        RepoService.open_vscode(slug)
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/repo-file/{slug}/{path:path}")
def repo_file(slug: str, path: str):
    repo = RepoService.get_repo(slug)
    base = Path(repo["local_path"]).resolve()
    file_path = (base / path).resolve()
    if base not in file_path.parents and file_path != base:
        raise HTTPException(status_code=400, detail="Ongeldig pad")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Bestand niet gevonden")
    return FileResponse(file_path)
