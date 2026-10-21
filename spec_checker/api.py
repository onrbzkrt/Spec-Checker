"""HTTP API called by Power Automate when a spec PDF is uploaded.

Run locally:  uvicorn spec_checker.api:app --port 8000
Docs:         http://localhost:8000/docs
"""
from __future__ import annotations

import os
import secrets
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from .config import Settings, llm_settings
from .extract import ClaudeExtractor
from .graph import GraphClient
from .pipeline import SpecPipeline

load_dotenv()  # read .env before the first request so the API key check works

app = FastAPI(title="Spec Checker API", version="1.0")


class ValidateRequest(BaseModel):
    file_name: str


class Issue(BaseModel):
    check: str
    status: str
    message: str


class ValidateResponse(BaseModel):
    file_name: str
    part_number: str | None
    part_name: str | None
    status: str
    issues: list[Issue]
    summary: str
    register_item_id: str | None


@lru_cache(maxsize=1)
def get_pipeline() -> SpecPipeline:
    settings = Settings.from_env()
    llm = llm_settings()
    graph = GraphClient(settings.tenant_id, settings.client_id, settings.client_secret)
    return SpecPipeline(settings, graph, ClaudeExtractor(llm.api_key, llm.model, llm.workspace_id))


def require_api_key(x_api_key: str = Header(default="")) -> None:
    expected = os.getenv("SPEC_CHECKER_API_KEY", "")
    if not expected or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/validate", response_model=ValidateResponse, dependencies=[Depends(require_api_key)])
def validate_file(req: ValidateRequest) -> ValidateResponse:
    pipeline = get_pipeline()
    file_item = pipeline.find_file(req.file_name)
    if file_item is None:
        raise HTTPException(status_code=404, detail=f"'{req.file_name}' not found in the specs library")

    out = pipeline.process(file_item)
    issues = [Issue(check=c.name, status=c.status, message=c.message) for c in out.result.issues]
    summary = "; ".join(f"{i.check}: {i.message}" for i in issues) or "All checks passed"
    return ValidateResponse(
        file_name=out.file_name,
        part_number=out.spec.part_number,
        part_name=out.spec.part_name,
        status=out.result.status,
        issues=issues,
        summary=summary,
        register_item_id=out.item_id,
    )
