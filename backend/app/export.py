from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from .graph_engine import corrected_scenario
from .ownership import resolution_for
from .schemas import PackageEnvelope, enforce_safety_boundary
from .seed_data import EDGES, fresh_nodes


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def replay_state(nodes: dict) -> list[dict]:
    return [{"id": key, "state": node["state"].value if hasattr(node["state"], "value") else node["state"],
             "value": node.get("value"), "metadata": node.get("metadata", {})} for key, node in sorted(nodes.items())]


def state_digest(nodes: dict) -> str:
    return hashlib.sha256(canonical(replay_state(nodes))).hexdigest()


def build_package(claim_ref: str, documents: list[dict] | None = None, rules: list[dict] | None = None) -> PackageEnvelope:
    final = corrected_scenario(fresh_nodes())
    conflict = resolution_for("conflict_between_two_documents")
    payload = {
        "package_version": "1.0-hackathon",
        "claim_metadata": {"claim_ref": claim_ref, "generated_at": datetime.now(timezone.utc).isoformat()},
        "source_documents": documents or [],
        "extracted_evidence": replay_state(final),
        "verified_rules": rules or [],
        "evidence_dependencies": EDGES,
        "resolution_actions": [{"issue_id": "C1", "action_type": conflict["action_type"], "resolution_owner": conflict["resolution_owner"]}],
        "replay": {"scenario": "section-5-fixed", "expected_state_digest": state_digest(final),
                   "correction": {"admission_date": "04-Mar", "mri_itemized": True,
                                  "procedure_code": "MRI-BRAIN", "procedure_date": "04-Mar"}},
    }
    enforce_safety_boundary(payload)
    payload["fingerprint_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    return PackageEnvelope.model_validate(payload)

