import json

import pytest
from pydantic import ValidationError

from app.export import build_package
from app.export import canonical
from app.graph_engine import corrected_scenario, propagate_state
from app.replay_validator import validate_package
from app.schemas import PackageEnvelope, UncertaintyState as S
from app.seed_data import fresh_nodes


def test_uncertainty_never_disappears_downstream():
    assert propagate_state([S.VERIFIED, S.CONFLICTED]) == S.CONFLICTED
    assert propagate_state([S.VERIFIED, S.MISSING]) == S.MISSING
    assert propagate_state([S.VERIFIED, S.NEEDS_HUMAN_CONFIRMATION]) == S.NEEDS_HUMAN_CONFIRMATION
    assert propagate_state([S.VERIFIED, S.UNVERIFIED]) == S.UNVERIFIED
    assert propagate_state([S.VERIFIED, S.VERIFIED]) == S.VERIFIED


def test_exact_scripted_cascade():
    nodes = corrected_scenario(fresh_nodes())
    assert nodes["length_of_stay"]["value"] == 3
    assert nodes["E1"]["value"] == 15000
    assert nodes["E2"]["value"] is True and nodes["E2"]["metadata"]["boundary_sensitive"] is True
    assert nodes["E3"]["state"] == S.VERIFIED
    assert nodes["C1"]["state"] == S.CONFLICTED


def test_export_replays_without_database(tmp_path):
    package = build_package("DEMO-1")
    path = tmp_path / "package.json"
    path.write_bytes(canonical(package.model_dump(mode="json", by_alias=True)))
    assert validate_package(str(path))


@pytest.mark.parametrize("smuggled", [
    {"approval_probability": 0.8},
    {"nested": {"claim_success_score": 72}},
    {"note": "This claim is guaranteed covered"},
    {"final_admissibility_decision": "yes"},
])
def test_safety_boundary_rejects_smuggled_prediction(smuggled):
    valid = build_package("DEMO-1").model_dump(mode="json")
    valid["claim_metadata"].update(smuggled)
    with pytest.raises(ValidationError):
        PackageEnvelope.model_validate(valid)
