"""Data structures shared by extraction, validation and the SharePoint register."""
from __future__ import annotations

from dataclasses import dataclass, field, fields

PASS, WARNING, FAIL = "PASS", "WARNING", "FAIL"
SEVERITY = {PASS: 0, WARNING: 1, FAIL: 2}


@dataclass
class SpecData:
    """Design data extracted from one component specification document."""
    part_number: str | None = None
    part_name: str | None = None
    category: str | None = None
    material: str | None = None
    supplier: str | None = None
    engineer_approval: str | None = None
    revision: str | None = None
    mass_target_g: float | None = None
    mass_actual_g: float | None = None
    cost_target_usd: float | None = None
    cost_actual_usd: float | None = None
    burn_rate_mm_min: float | None = None
    odor_rating: float | None = None
    foam_density_kg_m3: float | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "SpecData":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class CheckResult:
    name: str        # material, mass, cost, flammability, odor, density, documentation
    status: str      # PASS / WARNING / FAIL
    message: str


@dataclass
class ValidationResult:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def status(self) -> str:
        """Overall result = the most severe individual result (CM-IDS-001 section 9)."""
        if not self.checks:
            return WARNING
        return max((c.status for c in self.checks), key=SEVERITY.__getitem__)

    @property
    def issues(self) -> list[CheckResult]:
        return [c for c in self.checks if c.status != PASS]

    def issue_names(self) -> list[str]:
        return [c.name for c in self.issues]
