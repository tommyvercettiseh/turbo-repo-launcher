from __future__ import annotations

from pydantic import BaseModel, Field


class RepoAddRequest(BaseModel):
    repo_url: str = Field(
        ...,
        examples=["https://github.com/tommyvercettiseh/palletoptimizer"],
    )


class RepoRootUpdateRequest(BaseModel):
    repo_root: str


class FtpSettingsRequest(BaseModel):
    host: str
    username: str
    password: str = ""
    port: int = 21
    protocol: str = "ftps"
    base_directory: str = "/public_html/"


class ProjectFtpDirectoryRequest(BaseModel):
    directory: str
