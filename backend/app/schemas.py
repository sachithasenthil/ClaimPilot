from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UncertaintyState(StrEnum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONFLICTED = "CONFLICTED"
    MISSING = "MISSING"
    NEEDS_HUMAN_CONFIRMATION = "NEEDS_HUMAN_CONFIRMATION"


FORBIDDEN_KEY = re.compile(
    r"(?:approval|rejection|claim[_ -]?success).*(?:probability|likelihood|score)|"
    r"(?:probability|likelihood|score).*(?:approval|rejection|claim[_ -]?success)|"
    r"final[_ -]?admissibility|guaranteed[_ -]?coverage",
    re.IGNORECASE,
)
FORBIDDEN_VALUE = re.compile(
    r"(?:guaranteed|definitely|certainly)\s+(?:covered|approved|reimbursed)|"
    r"(?:approval|rejection|claim success)\s+(?:probability|likelihood|score)|"
    r"final\s+admissibility\s+(?:decision|result)|"
    r"(?:\d{1,3}(?:\.\d+)?\s*%|0?\.\d+)\s+(?:likely|chance|probability).*(?:approved|rejected|claim success)|"
    r"(?:likely|chance|probability).*(?:approved|rejected|claim success)",
    re.IGNORECASE,
)


def enforce_safety_boundary(value: Any) -> Any:
    """Reject predictive/adjudicative content recursively at the schema boundary."""
    if isinstance(value, dict):
        for key, child in value.items():
            if FORBIDDEN_KEY.search(str(key)):
                raise ValueError(f"Safety boundary rejected field: {key}")
            enforce_safety_boundary(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            enforce_safety_boundary(child)
    elif isinstance(value, str) and FORBIDDEN_VALUE.search(value):
        raise ValueError("Safety boundary rejected predictive or guaranteed language")
    return value


class SafeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def safety_boundary(cls, value: Any) -> Any:
        return enforce_safety_boundary(value)


class PolicyClauseOut(SafeModel):
    id: int
    source_page: int
    source_section: str
    raw_text: str
    structural_anchor: str


class CandidateRuleOut(SafeModel):
    id: int
    clause_id: int
    conditions: dict[str, Any]
    required_evidence: str
    affected_expense_type: str
    status: str


class VerifiedRuleOut(SafeModel):
    id: int
    candidate_rule_id: int
    rule_id: str
    rule_version: str
    verified_at: str
    verified_by: str


class GraphNode(SafeModel):
    id: str
    content: str
    state: UncertaintyState
    value: Any = None
    changed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(SafeModel):
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    edge_type: str
    rule_id: str | None = None


class GraphResponse(SafeModel):
    claim_id: str
    corrected: bool
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class IssueOut(SafeModel):
    id: str
    involved_nodes: list[str]
    issue_class: str
    state: str
    authority: str
    action_type: str
    resolution_owner: str
    explanation: str


class CorrectionRequest(SafeModel):
    admission_date: str = "04-Mar"
    mri_itemized: bool = True
    procedure_code: str = "MRI-BRAIN"
    procedure_date: str = "04-Mar"


class UploadResponse(SafeModel):
    id: int | str
    filename: str
    sha256: str
    page_count: int


class PackageEnvelope(SafeModel):
    package_version: str
    claim_metadata: dict[str, Any]
    source_documents: list[dict[str, Any]]
    extracted_evidence: list[dict[str, Any]]
    verified_rules: list[dict[str, Any]]
    evidence_dependencies: list[dict[str, Any]]
    resolution_actions: list[dict[str, Any]]
    replay: dict[str, Any]
    fingerprint_sha256: str
