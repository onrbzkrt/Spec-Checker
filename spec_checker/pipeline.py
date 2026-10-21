"""End-to-end processing of one spec file: download -> extract -> validate -> write to register.

Used by the CLI today and by the HTTP endpoint that Power Automate will call in the next step.
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import Settings
from .extract import ClaudeExtractor
from .graph import GraphClient
from .models import SpecData, ValidationResult
from .register import to_fields, upsert
from .rules import validate


@dataclass
class Outcome:
    file_name: str
    spec: SpecData
    result: ValidationResult
    action: str = "dry-run"
    item_id: str | None = None      # Part Register list item id


class SpecPipeline:
    def __init__(self, settings: Settings, graph: GraphClient, extractor: ClaudeExtractor):
        self.settings = settings
        self.graph = graph
        self.extractor = extractor
        site = graph.get_site(settings.site_host, settings.site_path)
        self.site_id = site["id"]
        self.drive_id = graph.get_drive(self.site_id, settings.specs_library)["id"]
        register = graph.find_list(self.site_id, settings.register_list)
        if register is None:
            raise LookupError(f"List '{settings.register_list}' not found. Run: python -m scripts.provision")
        self.list_id = register["id"]

    def files(self) -> list[dict]:
        return [f for f in self.graph.list_files(self.drive_id) if f["name"].lower().endswith(".pdf")]

    def process(self, file_item: dict, dry_run: bool = False) -> Outcome:
        data = self.graph.download(self.drive_id, file_item["id"])
        spec = self.extractor.extract_pdf(data)
        result = validate(spec)
        outcome = Outcome(file_item["name"], spec, result)
        if not dry_run:
            outcome.action, outcome.item_id = upsert(self.graph, self.site_id, self.list_id,
                                                     to_fields(spec, result, file_item))
        return outcome

    def find_file(self, file_name: str) -> dict | None:
        for f in self.files():
            if f["name"].lower() == file_name.lower():
                return f
        return None
