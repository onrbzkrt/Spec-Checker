"""Settings loaded from environment variables (.env in local development)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

REQUIRED = ("TENANT_ID", "CLIENT_ID", "CLIENT_SECRET", "SITE_HOST", "SITE_PATH")
DEFAULT_MODEL = "claude-haiku-5-5"   # fast and cheap; extraction does not need a larger model


@dataclass(frozen=True)
class LLMSettings:
    api_key: str
    model: str
    workspace_id: str | None = None   # needed for API keys that are not scoped to one workspace


def llm_settings() -> LLMSettings:
    """Settings for the extraction LLM (Claude)."""
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ANTHROPIC_API_KEY in .env")
    return LLMSettings(api_key=api_key,
                       model=os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL),
                       workspace_id=os.getenv("ANTHROPIC_WORKSPACE_ID") or None)


@dataclass(frozen=True)
class Settings:
    tenant_id: str
    client_id: str
    client_secret: str
    site_host: str          # e.g. contoso.sharepoint.com
    site_path: str          # e.g. /sites/InteriorEngineering
    specs_library: str = "Part Specs"
    standards_library: str = "Standards"
    register_list: str = "Part Register"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        missing = [key for key in REQUIRED if not os.getenv(key)]
        if missing:
            raise RuntimeError(
                f"Missing environment variables: {', '.join(missing)}. "
                "Copy .env.example to .env and fill in the values."
            )
        return cls(
            tenant_id=os.environ["TENANT_ID"],
            client_id=os.environ["CLIENT_ID"],
            client_secret=os.environ["CLIENT_SECRET"],
            site_host=os.environ["SITE_HOST"],
            site_path=os.environ["SITE_PATH"],
            specs_library=os.getenv("SPECS_LIBRARY", "Part Specs"),
            standards_library=os.getenv("STANDARDS_LIBRARY", "Standards"),
            register_list=os.getenv("REGISTER_LIST", "Part Register"),
        )
