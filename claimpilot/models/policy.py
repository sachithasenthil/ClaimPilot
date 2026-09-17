from __future__ import annotations
import hashlib, re, unicodedata
from pydantic import BaseModel, ConfigDict, Field
from .enums import RuleStatus, VerifierTier

def normalized_text_hash(text: str) -> str:
    """Stable clause key: NFKC, remove common page furniture, whitespace/case normalize."""
    value = unicodedata.normalize("NFKC", text)
    value = re.sub(r"(?im)^\s*(page\s+\d+(\s+of\s+\d+)?|\d+)\s*$", "", value)
    value = re.sub(r"\s+", " ", value).strip().casefold()
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

class PolicyIdentity(FrozenModel):
    insurer_id: str
    product_uin: str
    policy_version: str
    endorsement_set_hash: str

class PolicyClause(FrozenModel):
    structural_anchor: str
    text: str
    @property
    def normalized_text_hash(self) -> str: return normalized_text_hash(self.text)

class CandidateRule(FrozenModel):
    scope: PolicyIdentity
    clause: PolicyClause
    logic: str

class VerifiedRule(CandidateRule):
    verifier_tier: VerifierTier
    status: RuleStatus = RuleStatus.ACTIVE
    provenance: str
    @property
    def clause_key(self) -> tuple[str, str]:
        return self.clause.structural_anchor, self.clause.normalized_text_hash
