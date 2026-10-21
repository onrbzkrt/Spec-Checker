"""Extract structured design data from a spec PDF with Claude (forced tool use = typed JSON output)."""
from __future__ import annotations

import io

import anthropic
from pypdf import PdfReader

from .models import SpecData
from .rules import CM_IDS_001

CATEGORIES = list(CM_IDS_001.approved_materials)

SYSTEM_PROMPT = """You extract data from automotive interior component specification documents.
Rules:
- Copy values exactly as stated in the document. Never guess or calculate a value that is not there; use null.
- Report mass in grams. Convert kilograms to grams (1.79 kg -> 1790).
- Report costs as plain numbers in USD (no currency symbols).
- revision: the revision letter as written, or "DRAFT" if the document is a draft.
- engineer_approval: the approving engineer's name, or null if approval is pending or missing.
- category must be one of the allowed values.
- Ignore page headers, footers and disclaimers."""

RECORD_SPEC_TOOL = {
    "name": "record_spec",
    "description": "Record the design data found in the specification document.",
    "input_schema": {
        "type": "object",
        "properties": {
            "part_number": {"type": ["string", "null"]},
            "part_name": {"type": ["string", "null"]},
            "category": {"type": ["string", "null"], "enum": CATEGORIES + [None]},
            "material": {"type": ["string", "null"]},
            "supplier": {"type": ["string", "null"]},
            "engineer_approval": {"type": ["string", "null"]},
            "revision": {"type": ["string", "null"]},
            "mass_target_g": {"type": ["number", "null"]},
            "mass_actual_g": {"type": ["number", "null"]},
            "cost_target_usd": {"type": ["number", "null"]},
            "cost_actual_usd": {"type": ["number", "null"]},
            "burn_rate_mm_min": {"type": ["number", "null"]},
            "odor_rating": {"type": ["number", "null"]},
            "foam_density_kg_m3": {"type": ["number", "null"]},
        },
        "required": [
            "part_number", "part_name", "category", "material", "supplier", "engineer_approval",
            "revision", "mass_target_g", "mass_actual_g", "cost_target_usd", "cost_actual_usd",
            "burn_rate_mm_min", "odor_rating", "foam_density_kg_m3",
        ],
    },
}


def pdf_to_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


class ClaudeExtractor:
    def __init__(self, api_key: str, model: str, workspace_id: str | None = None,
                 client: anthropic.Anthropic | None = None):
        self.model = model
        headers = {"anthropic-workspace-id": workspace_id} if workspace_id else None
        self._client = client or anthropic.Anthropic(api_key=api_key, default_headers=headers)

    def extract(self, document_text: str) -> SpecData:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[RECORD_SPEC_TOOL],
            tool_choice={"type": "tool", "name": "record_spec"},
            messages=[{"role": "user", "content": f"<document>\n{document_text}\n</document>"}],
        )
        for block in response.content:
            if block.type == "tool_use":
                return SpecData.from_dict(block.input)
        raise RuntimeError("Model did not return structured spec data")

    def extract_pdf(self, data: bytes) -> SpecData:
        return self.extract(pdf_to_text(data))
