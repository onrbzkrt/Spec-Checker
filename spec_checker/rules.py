"""Rule-based validation against CM-IDS-001 Interior Component Design Standard (Rev C).

Design choice: the LLM only *extracts* values from the document. Every pass/fail decision is
made here, in plain, testable code, so results are deterministic and auditable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .models import FAIL, PASS, WARNING, CheckResult, SpecData, ValidationResult

EPS = 1e-9


def _norm(material: str) -> str:
    """Normalise material names so 'pp td20', 'PP-TD20' and 'PP TD20' compare equal."""
    return re.sub(r"[\s\-_]", "", material.upper())


@dataclass(frozen=True)
class Standard:
    name: str
    approved_materials: dict[str, tuple[str, ...]]
    mass_pass: float = 1.05     # actual/target
    mass_warn: float = 1.10
    cost_pass: float = 1.03
    cost_warn: float = 1.08
    burn_pass: float = 80.0     # mm/min, internal target
    burn_limit: float = 102.0   # mm/min, FMVSS 302
    odor_pass: float = 3.0      # VDA 270
    odor_fail: float = 4.0
    density_min: float = 45.0   # kg/m3, seat foam only
    density_max: float = 60.0
    foam_categories: tuple[str, ...] = field(default=("Seat Foam",))


CM_IDS_001 = Standard(
    name="CM-IDS-001 Rev C",
    approved_materials={
        "Instrument Panel": ("PP-TD20", "PC/ABS"),
        "Door Trim": ("PP-TD20", "PP-GF20"),
        "Console": ("ABS", "PC/ABS"),
        "Seat Foam": ("PU Foam",),
        "Headliner": ("PET Fiber Composite",),
        "Pillar Trim": ("PP-TD20", "TPO"),
    },
)


def _ratio_band(actual: float, target: float, pass_limit: float, warn_limit: float) -> str:
    ratio = actual / target
    if ratio <= pass_limit + EPS:
        return PASS
    if ratio <= warn_limit + EPS:
        return WARNING
    return FAIL


def check_documentation(spec: SpecData, std: Standard) -> CheckResult:
    problems = []
    if not spec.revision or spec.revision.strip().upper() == "DRAFT":
        problems.append("revision is DRAFT or missing")
    if not spec.engineer_approval:
        problems.append("engineer approval missing")
    if problems:
        msg = "; ".join(problems)
        return CheckResult("documentation", WARNING, msg[0].upper() + msg[1:])
    return CheckResult("documentation", PASS, f"Rev {spec.revision}, approved by {spec.engineer_approval}")


def check_material(spec: SpecData, std: Standard) -> CheckResult:
    approved = std.approved_materials.get(spec.category or "")
    if approved is None:
        return CheckResult("material", WARNING, f"Unknown component category '{spec.category}'")
    if not spec.material:
        return CheckResult("material", WARNING, "Material not stated")
    if _norm(spec.material) in {_norm(m) for m in approved}:
        return CheckResult("material", PASS, f"{spec.material} is approved for {spec.category}")
    return CheckResult("material", FAIL, f"{spec.material} is not approved for {spec.category} "
                                         f"(approved: {', '.join(approved)})")


def check_mass(spec: SpecData, std: Standard) -> CheckResult:
    if not spec.mass_target_g or spec.mass_actual_g is None:
        return CheckResult("mass", WARNING, "Target or actual mass missing")
    status = _ratio_band(spec.mass_actual_g, spec.mass_target_g, std.mass_pass, std.mass_warn)
    pct = spec.mass_actual_g / spec.mass_target_g * 100
    return CheckResult("mass", status, f"Actual {spec.mass_actual_g:,.0f} g is {pct:.1f}% of target "
                                       f"{spec.mass_target_g:,.0f} g")


def check_cost(spec: SpecData, std: Standard) -> CheckResult:
    if not spec.cost_target_usd or spec.cost_actual_usd is None:
        return CheckResult("cost", WARNING, "Target or actual cost missing")
    status = _ratio_band(spec.cost_actual_usd, spec.cost_target_usd, std.cost_pass, std.cost_warn)
    pct = spec.cost_actual_usd / spec.cost_target_usd * 100
    return CheckResult("cost", status, f"Actual ${spec.cost_actual_usd:.2f} is {pct:.1f}% of target "
                                       f"${spec.cost_target_usd:.2f}")


def check_flammability(spec: SpecData, std: Standard) -> CheckResult:
    rate = spec.burn_rate_mm_min
    if rate is None:
        return CheckResult("flammability", WARNING, "FMVSS 302 burn rate missing")
    if rate <= std.burn_pass:
        return CheckResult("flammability", PASS, f"Burn rate {rate:g} mm/min")
    if rate <= std.burn_limit:
        return CheckResult("flammability", WARNING, f"Burn rate {rate:g} mm/min exceeds internal "
                                                    f"target of {std.burn_pass:g}")
    return CheckResult("flammability", FAIL, f"Burn rate {rate:g} mm/min does not meet FMVSS 302 "
                                             f"(max {std.burn_limit:g})")


def check_odor(spec: SpecData, std: Standard) -> CheckResult:
    rating = spec.odor_rating
    if rating is None:
        return CheckResult("odor", WARNING, "VDA 270 odor rating missing")
    if rating <= std.odor_pass:
        return CheckResult("odor", PASS, f"Odor rating {rating:g}")
    if rating < std.odor_fail:
        return CheckResult("odor", WARNING, f"Odor rating {rating:g} above {std.odor_pass:g}")
    return CheckResult("odor", FAIL, f"Odor rating {rating:g} at or above {std.odor_fail:g}")


def check_density(spec: SpecData, std: Standard) -> CheckResult:
    d = spec.foam_density_kg_m3
    if d is None:
        return CheckResult("density", WARNING, "Foam density missing")
    if std.density_min <= d <= std.density_max:
        return CheckResult("density", PASS, f"Foam density {d:g} kg/m3")
    return CheckResult("density", FAIL, f"Foam density {d:g} kg/m3 outside "
                                        f"{std.density_min:g}-{std.density_max:g}")


def validate(spec: SpecData, std: Standard = CM_IDS_001) -> ValidationResult:
    checks = [check_documentation, check_material, check_mass, check_cost,
              check_flammability, check_odor]
    if spec.category in std.foam_categories:
        checks.append(check_density)
    return ValidationResult([check(spec, std) for check in checks])
