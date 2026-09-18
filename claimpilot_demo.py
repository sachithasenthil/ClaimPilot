"""ClaimPilot's deliberately small, non-predictive hackathon demo.

Run with: python claimpilot_demo.py
"""
from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any

from pydantic import BaseModel


class UncertaintyState(str, Enum):
    """A gate for whether a field may be acted on; never a probability."""

    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    CONFLICTED = "conflicted"
    MISSING = "missing"
    NEEDS_HUMAN_CONFIRMATION = "needs_human_confirmation"


class ResolutionOwner(str, Enum):
    CLAIMANT = "claimant"
    HOSPITAL_BILLING = "hospital_billing"
    INSURER = "insurer"
    NO_ACTION_EXISTS = "no_action_exists"


# Intentionally a fixed product lookup, not a rule/inference engine.
ISSUE_OWNER: dict[str, ResolutionOwner] = {
    "bill_date_conflicts_discharge_summary": ResolutionOwner.HOSPITAL_BILLING,
    "orphan_report_needs_itemized_bill_line": ResolutionOwner.HOSPITAL_BILLING,
    "pre_hospitalization_boundary_review": ResolutionOwner.CLAIMANT,
    "non_correctable_policy_condition": ResolutionOwner.NO_ACTION_EXISTS,
}


class OwnerResolution(BaseModel):
    issue_class: str
    owner: ResolutionOwner
    action_exists: bool


def resolve_owner(issue_class: str) -> OwnerResolution:
    """Return a fixed owner; non-correctable policy conditions have no action."""
    owner = ISSUE_OWNER.get(issue_class, ResolutionOwner.CLAIMANT)
    return OwnerResolution(
        issue_class=issue_class,
        owner=owner,
        action_exists=owner is not ResolutionOwner.NO_ACTION_EXISTS,
    )


class DemoNode(BaseModel):
    value: Any
    state: UncertaintyState
    explanation: str


class ScenarioState(BaseModel):
    room_rent: DemoNode
    pharmacy_boundary: DemoNode
    mri_report_link: DemoNode
    admission_date: DemoNode


def run_section_18() -> tuple[ScenarioState, ScenarioState]:
    """Hardcoded §18 scenario only. This is explicitly not a graph executor."""
    before = ScenarioState(
        room_rent=DemoNode(
            value={"length_of_stay_days": 4, "eligible_room_rent": 4000},
            state=UncertaintyState.VERIFIED,
            explanation="03-Mar admission produces four eligible room-rent days.",
        ),
        pharmacy_boundary=DemoNode(
            value={"bill_date": "02-Feb", "pre_hospitalization_window_start": "02-Feb", "at_boundary": False},
            state=UncertaintyState.UNVERIFIED,
            explanation="Window has not yet been recalculated for the corrected admission date.",
        ),
        mri_report_link=DemoNode(
            value={"itemized_mri_line": False, "orphan_mri_report": True, "matched": False},
            state=UncertaintyState.MISSING,
            explanation="MRI report is uploaded but its matching bill line is absent.",
        ),
        admission_date=DemoNode(
            value={"bill": "03-Mar", "discharge_summary": "03-Mar"},
            state=UncertaintyState.VERIFIED,
            explanation="Documents agree before the bill correction.",
        ),
    )

    # The one scripted update: bill admission date -> 04-Mar, with MRI itemized.
    after = ScenarioState(
        room_rent=DemoNode(
            value={"length_of_stay_days": 3, "eligible_room_rent": 3000},
            state=UncertaintyState.VERIFIED,
            explanation="Corrected admission drops stay from 4 to 3 days; eligible room-rent falls by 1000.",
        ),
        pharmacy_boundary=DemoNode(
            value={"bill_date": "02-Feb", "pre_hospitalization_window_start": "02-Feb", "at_boundary": True},
            state=UncertaintyState.NEEDS_HUMAN_CONFIRMATION,
            explanation="Pharmacy bill is exactly on the recalculated pre-hospitalization boundary.",
        ),
        mri_report_link=DemoNode(
            value={"itemized_mri_line": True, "orphan_mri_report": True, "matched": True},
            state=UncertaintyState.VERIFIED,
            explanation="New MRI bill line matches and clears the orphan MRI report blocker.",
        ),
        admission_date=DemoNode(
            value={"bill": "04-Mar", "discharge_summary": "03-Mar"},
            state=UncertaintyState.CONFLICTED,
            explanation="Corrected bill now conflicts with the hardcoded discharge-summary date.",
        ),
    )
    return before, after


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def state_hash(final_state: ScenarioState) -> str:
    return hashlib.sha256(_canonical(final_state.model_dump(mode="json")).encode()).hexdigest()


def export_cep() -> str:
    """Export plain JSON plus a SHA-256 recomputability check, not a signature."""
    before, after = run_section_18()
    return _canonical({
        "format": "claimpilot-simple-cep-v1",
        "scenario": "hardcoded-section-18",
        "update": {"bill_admission_date": "04-Mar", "mri_line_itemized": True},
        "before_nodes": before.model_dump(mode="json"),
        "final_nodes": after.model_dump(mode="json"),
        "final_state_sha256": state_hash(after),
    })


def replay_cep(exported_json: str) -> bool:
    """Re-run only the scripted scenario and verify its final state checksum."""
    package = json.loads(exported_json)
    if package["format"] != "claimpilot-simple-cep-v1":
        raise ValueError("Unsupported CEP format")
    _, recomputed = run_section_18()
    expected_nodes = recomputed.model_dump(mode="json")
    assert package["final_nodes"] == expected_nodes, "Export does not match the scripted scenario"
    assert package["final_state_sha256"] == state_hash(recomputed), "Replay hash mismatch"
    return True


def main() -> None:
    before, after = run_section_18()
    print("ClaimPilot Section 18 hardcoded demo (no prediction is performed)\n")
    for branch in ("room_rent", "pharmacy_boundary", "mri_report_link", "admission_date"):
        print(f"{branch}:\n  before: {before.model_dump(mode='json')[branch]}\n  after:  {after.model_dump(mode='json')[branch]}")
    exported = export_cep()
    assert replay_cep(exported)
    print(f"\nReplay validated: {json.loads(exported)['final_state_sha256']}")


if __name__ == "__main__":
    main()
