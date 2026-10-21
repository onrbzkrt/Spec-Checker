from fastapi.testclient import TestClient

from spec_checker import api
from spec_checker.models import FAIL, CheckResult, SpecData, ValidationResult
from spec_checker.pipeline import Outcome


class FakePipeline:
    def find_file(self, name):
        return {"id": "1", "name": name} if name.startswith("INT-") else None

    def process(self, file_item):
        result = ValidationResult([CheckResult("cost", FAIL, "Actual $8.70 is 111.5% of target $7.80")])
        return Outcome(file_item["name"], SpecData(part_number="INT-CN-3002", part_name="Bin"),
                       result, action="created", item_id="7")


def client(monkeypatch):
    monkeypatch.setenv("SPEC_CHECKER_API_KEY", "secret")
    monkeypatch.setattr(api, "get_pipeline", lambda: FakePipeline())
    return TestClient(api.app)


def test_rejects_missing_api_key(monkeypatch):
    r = client(monkeypatch).post("/validate", json={"file_name": "INT-CN-3002.pdf"})
    assert r.status_code == 401


def test_validate_returns_result(monkeypatch):
    r = client(monkeypatch).post("/validate", json={"file_name": "INT-CN-3002.pdf"},
                                 headers={"X-API-Key": "secret"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "FAIL"
    assert body["issues"][0]["check"] == "cost"
    assert body["register_item_id"] == "7"


def test_unknown_file_is_404(monkeypatch):
    r = client(monkeypatch).post("/validate", json={"file_name": "nope.pdf"},
                                 headers={"X-API-Key": "secret"})
    assert r.status_code == 404
