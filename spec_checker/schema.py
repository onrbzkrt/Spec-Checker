"""Column definitions for the 'Part Register' SharePoint list (Graph columnDefinition format).

The built-in Title column holds the part number.
"""
from __future__ import annotations

CATEGORIES = ["Instrument Panel", "Door Trim", "Console", "Seat Foam", "Headliner", "Pillar Trim"]
STATUSES = ["Pending", "PASS", "WARNING", "FAIL"]
ERB_DECISIONS = ["Deviation approved", "Rejected - redesign required"]


def _text(name: str, display: str, multiline: bool = False, indexed: bool = False) -> dict:
    col = {"name": name, "displayName": display, "text": {"allowMultipleLines": multiline}}
    if indexed:
        col["indexed"] = True
    return col


def _number(name: str, display: str) -> dict:
    return {"name": name, "displayName": display, "number": {}}


def _currency(name: str, display: str) -> dict:
    return {"name": name, "displayName": display, "currency": {"locale": "en-us"}}


def _choice(name: str, display: str, choices: list[str]) -> dict:
    return {"name": name, "displayName": display,
            "choice": {"choices": choices, "displayAs": "dropDownMenu", "allowTextEntry": False}}


def _datetime(name: str, display: str) -> dict:
    return {"name": name, "displayName": display, "dateTime": {"format": "dateTime"}}


PART_REGISTER_COLUMNS: list[dict] = [
    _text("PartName", "Part Name"),
    _choice("PartCategory", "Category", CATEGORIES),
    _text("Material", "Material"),
    _text("Supplier", "Supplier"),
    _text("Engineer", "Engineer"),
    _text("SpecRevision", "Revision"),
    _number("MassTarget", "Mass Target (g)"),
    _number("MassActual", "Mass Actual (g)"),
    _currency("CostTarget", "Cost Target"),
    _currency("CostActual", "Cost Actual"),
    _number("BurnRate", "Burn Rate (mm/min)"),
    _number("OdorRating", "Odor Rating (VDA 270)"),
    _number("FoamDensity", "Foam Density (kg/m3)"),
    _choice("ValidationStatus", "Validation Status", STATUSES),
    _text("FailedChecks", "Failed Checks", multiline=True),
    _text("ValidationNotes", "Validation Notes", multiline=True),
    _text("SpecFileName", "Spec File"),
    _text("SpecFileUrl", "Spec File URL"),
    _text("DriveItemId", "Drive Item Id", indexed=True),
    _datetime("LastValidated", "Last Validated"),
    # Filled in by the Power Automate approval flow for FAIL results
    _choice("ERBDecision", "ERB Decision", ERB_DECISIONS),
    _text("ERBComments", "ERB Comments", multiline=True),
]
