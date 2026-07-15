from __future__ import annotations

from pydantic import BaseModel, Field


class RepoAddRequest(BaseModel):
    repo_url: str = Field(
        ...,
        examples=["https://github.com/tommyvercettiseh/palletoptimizer"],
    )


class RepoRootUpdateRequest(BaseModel):
    repo_root: str
