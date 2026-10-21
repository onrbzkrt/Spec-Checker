"""Unit tests for the CM-IDS-001 rules. Run with:  python -m pytest -q"""
from types import SimpleNamespace

import pytest

from spec_checker.extract import ClaudeExtractor
from spec_checker.models import FAIL, PASS, WARNING, SpecData
from spec_checker.register import to_fields
from spec_checker.rules import validate


def spec(**overrides) -> SpecData:
    base = dict(part_number="INT-XX-0001", part_name="Test Part", category="Door Trim",
                material="PP-TD20", supplier="Test Supplier", engineer_approval="J. Patel",
                revision="B", mass_target_g=1000, mass_actual_g=1000, cost_target_usd=10.0,
                cost_actual_usd=10.0, burn_rate_mm_min=50, odor_rating=2.5, foam_density_kg_m3=None)
    base.update(overrides)
    return SpecData(**base)


# The ten sample specs and their expected results (same data as the generated PDFs).
SAMPLES = [
    (dict(part_number="INT-IP-1001", category="Instrument Panel", material="PP-TD20", mass_target_g=2850, mass_actual_g=2910, cost_target_usd=18.40, cost_actual_usd=18.75, burn_rate_mm_min=62, odor_rating=2.5), PASS, []),
    (dict(part_number="INT-DR-2003", category="Door Trim", material="PP-TD20", mass_target_g=1650, mass_actual_g=1790, cost_target_usd=12.10, cost_actual_usd=12.30, burn_rate_mm_min=70, odor_rating=3.0), WARNING, ["mass"]),
    (dict(part_number="INT-CN-3002", category="Console", material="ABS", mass_target_g=980, mass_actual_g=975, cost_target_usd=7.80, cost_actual_usd=8.70, burn_rate_mm_min=55, odor_rating=2.5), FAIL, ["cost"]),
    (dict(part_number="INT-ST-4001", category="Seat Foam", material="PU Foam", foam_density_kg_m3=52, mass_target_g=1450, mass_actual_g=1460, cost_target_usd=21.00, cost_actual_usd=21.40, burn_rate_mm_min=95, odor_rating=3.5), WARNING, ["flammability", "odor"]),
    (dict(part_number="INT-HL-5001", category="Headliner", material="PET Fiber Composite", mass_target_g=2100, mass_actual_g=2080, cost_target_usd=15.50, cost_actual_usd=15.20, burn_rate_mm_min=48, odor_rating=2.0), PASS, []),
    (dict(part_number="INT-PL-6002", category="Pillar Trim", material="ABS", mass_target_g=420, mass_actual_g=430, cost_target_usd=3.10, cost_actual_usd=3.12, burn_rate_mm_min=60, odor_rating=2.5), FAIL, ["material"]),
    (dict(part_number="INT-DR-2004", category="Door Trim", material="PP-GF20", mass_target_g=1480, mass_actual_g=1520, cost_target_usd=10.90, cost_actual_usd=11.10, burn_rate_mm_min=110, odor_rating=3.0), FAIL, ["flammability"]),
    (dict(part_number="INT-CN-3005", category="Console", material="PC/ABS", mass_target_g=640, mass_actual_g=655, cost_target_usd=5.60, cost_actual_usd=5.75, burn_rate_mm_min=58, odor_rating=2.5, revision="DRAFT", engineer_approval=None), WARNING, ["documentation"]),
    (dict(part_number="INT-IP-1004", category="Instrument Panel", material="PC/ABS", mass_target_g=760, mass_actual_g=800, cost_target_usd=6.20, cost_actual_usd=6.45, burn_rate_mm_min=64, odor_rating=3.0), WARNING, ["mass", "cost"]),
    (dict(part_number="INT-ST-4003", category="Seat Foam", material="PU Foam", foam_density_kg_m3=41, mass_target_g=1210, mass_actual_g=1190, cost_target_usd=14.80, cost_actual_usd=14.60, burn_rate_mm_min=75, odor_rating=2.5), FAIL, ["density"]),
]


@pytest.mark.parametrize("data,expected,issues", SAMPLES, ids=[s[0]["part_number"] for s in SAMPLES])
def test_sample_specs(data, expected, issues):
    result = validate(spec(**data))
    assert result.status == expected
    assert sorted(result.issue_names()) == sorted(issues)


@pytest.mark.parametrize("actual,expected", [(1050, PASS), (1051, WARNING), (1100, WARNING), (1101, FAIL)])
def test_mass_boundaries(actual, expected):
    assert validate(spec(mass_actual_g=actual)).status == expected


@pytest.mark.parametrize("actual,expected", [(10.30, PASS), (10.31, WARNING), (10.80, WARNING), (10.81, FAIL)])
def test_cost_boundaries(actual, expected):
    assert validate(spec(cost_actual_usd=actual)).status == expected


@pytest.mark.parametrize("rate,expected", [(80, PASS), (80.5, WARNING), (102, WARNING), (103, FAIL)])
def test_flammability_boundaries(rate, expected):
    assert validate(spec(burn_rate_mm_min=rate)).status == expected


@pytest.mark.parametrize("rating,expected", [(3.0, PASS), (3.5, WARNING), (4.0, FAIL)])
def test_odor_boundaries(rating, expected):
    assert validate(spec(odor_rating=rating)).status == expected


@pytest.mark.parametrize("density,expected", [(45, PASS), (60, PASS), (44.9, FAIL), (60.1, FAIL)])
def test_foam_density(density, expected):
    s = spec(category="Seat Foam", material="PU Foam", foam_density_kg_m3=density)
    assert validate(s).status == expected


def test_material_names_are_normalised():
    assert validate(spec(material="pp td20")).status == PASS


def test_missing_values_are_warnings_not_crashes():
    result = validate(spec(mass_actual_g=None, burn_rate_mm_min=None))
    assert result.status == WARNING
    assert {"mass", "flammability"} <= set(result.issue_names())


def test_register_fields_skip_missing_values():
    s = spec(foam_density_kg_m3=None)
    fields = to_fields(s, validate(s), {"id": "abc", "name": "x.pdf", "webUrl": "https://x"})
    assert "FoamDensity" not in fields
    assert fields["ValidationStatus"] == PASS
    assert fields["DriveItemId"] == "abc"


def test_extractor_reads_tool_output():
    tool_block = SimpleNamespace(type="tool_use", input={"part_number": "INT-IP-1001", "mass_actual_g": 2910})
    fake_client = SimpleNamespace(messages=SimpleNamespace(
        create=lambda **kwargs: SimpleNamespace(content=[tool_block])))
    result = ClaudeExtractor("key", "model", client=fake_client).extract("text")
    assert result.part_number == "INT-IP-1001"
    assert result.mass_actual_g == 2910


def test_extractor_sends_workspace_header_when_configured():
    extractor = ClaudeExtractor("sk-test", "model", workspace_id="wrkspc_123")
    assert extractor._client.default_headers.get("anthropic-workspace-id") == "wrkspc_123"
    plain = ClaudeExtractor("sk-test", "model")
    assert "anthropic-workspace-id" not in plain._client.default_headers
