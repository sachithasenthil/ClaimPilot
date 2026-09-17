from __future__ import annotations
from typing import Any
from pydantic import Field
from .enums import IssueClass, NodeKind, UncertaintyState
from .policy import FrozenModel

class EvidenceNode(FrozenModel):
    id: str
    kind: NodeKind
    state: UncertaintyState
    value: Any = None
    document_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class EvidenceEdge(FrozenModel):
    source_id: str
    target_id: str
    required: bool = True
    stale: bool = False

class Issue(FrozenModel):
    id: str
    issue_class: IssueClass
    description: str
    authoritative_issuer: str | None = None

class ResolutionAction(FrozenModel):
    evidence_owner: str | None
    resolution_authority: str | None
    available_action: str | None
    resolution_owner: str | None
