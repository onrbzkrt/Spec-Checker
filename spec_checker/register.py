"""Map a validated spec to 'Part Register' list fields and upsert it (one row per spec file)."""
from __future__ import annotations

from datetime import datetime, timezone

from .graph import GraphClient
from .models import SpecData, ValidationResult


def to_fields(spec: SpecData, result: ValidationResult, file_item: dict) -> dict:
    fields = {
        "Title": spec.part_number or file_item["name"],
        "PartName": spec.part_name,
        "PartCategory": spec.category,
        "Material": spec.material,
        "Supplier": spec.supplier,
        "Engineer": spec.engineer_approval,
        "SpecRevision": spec.revision,
        "MassTarget": spec.mass_target_g,
        "MassActual": spec.mass_actual_g,
        "CostTarget": spec.cost_target_usd,
        "CostActual": spec.cost_actual_usd,
        "BurnRate": spec.burn_rate_mm_min,
        "OdorRating": spec.odor_rating,
        "FoamDensity": spec.foam_density_kg_m3,
        "ValidationStatus": result.status,
        "FailedChecks": "\n".join(f"{c.name.upper()} ({c.status}): {c.message}" for c in result.issues) or "None",
        "ValidationNotes": "\n".join(f"{c.name}: {c.status} - {c.message}" for c in result.checks),
        "SpecFileName": file_item["name"],
        "SpecFileUrl": file_item.get("webUrl"),
        "DriveItemId": file_item["id"],
        "LastValidated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    # Graph rejects nulls for some column types, so only send values we actually have.
    return {k: v for k, v in fields.items() if v is not None}


def upsert(graph: GraphClient, site_id: str, list_id: str, fields: dict) -> tuple[str, str]:
    """Create or update the row whose DriveItemId matches. Returns (action, item_id).

    The register is small, so reading all rows is simpler and more robust than a $filter query.
    """
    for item in graph.list_items(site_id, list_id):
        if item.get("fields", {}).get("DriveItemId") == fields["DriveItemId"]:
            graph.update_item(site_id, list_id, item["id"], fields)
            return "updated", item["id"]
    created = graph.create_item(site_id, list_id, fields)
    return "created", created["id"]
