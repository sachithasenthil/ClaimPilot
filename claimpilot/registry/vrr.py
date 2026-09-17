from __future__ import annotations
from dataclasses import dataclass
from claimpilot.models.enums import RuleStatus
from claimpilot.models.policy import CandidateRule, PolicyIdentity, VerifiedRule

@dataclass(frozen=True)
class LookupResult:
    tier: str
    rule: VerifiedRule | None = None
    message: str = ""

class VerifiedRuleRegistry:
    def __init__(self) -> None: self._rules: list[VerifiedRule] = []
    def add(self, rule: VerifiedRule) -> None: self._rules.append(rule)
    def lookup(self, candidate: CandidateRule) -> LookupResult:
        scoped = [r for r in self._rules if r.scope == candidate.scope and r.status == RuleStatus.ACTIVE]
        exact = next((r for r in scoped if r.clause.normalized_text_hash == candidate.clause.normalized_text_hash), None)
        if exact: return LookupResult("A", exact, "exact clause match; reuse verified logic and provenance")
        if scoped: return LookupResult("B", None, "DIFF_CONFIRMATION required before inheriting logic")
        return LookupResult("C", None, "unmatched; AI proposal requires Tier 1/2 human verification")
    def confirm_diff(self, candidate: CandidateRule, source: VerifiedRule, provenance: str) -> VerifiedRule:
        if candidate.scope != source.scope: raise ValueError("near-match confirmation requires identical RuleScope")
        rule = VerifiedRule(**candidate.model_dump(), verifier_tier=source.verifier_tier, provenance=provenance)
        self.add(rule); return rule
    def invalidate_policy_version(self, identity: PolicyIdentity, revoked: bool = False, graph: object | None = None) -> list[VerifiedRule]:
        status = RuleStatus.REVOKED if revoked else RuleStatus.NEEDS_REVERIFICATION
        changed=[]
        for i, rule in enumerate(self._rules):
            if rule.scope == identity:
                changed_rule = rule.model_copy(update={"status": status}); self._rules[i]=changed_rule; changed.append(changed_rule)
        if graph is not None:
            # Rule nodes conventionally carry their RuleScope in metadata; only matching
            # nodes can taint the graph, and every descendant edge is marked stale.
            scope = identity.model_dump(mode="json")
            sources = {n.id for n in graph.nodes.values() if n.metadata.get("rule_scope") == scope}
            graph.mark_downstream_stale(sources)
        return changed
