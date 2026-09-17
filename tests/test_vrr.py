from claimpilot.models.enums import RuleStatus, VerifierTier
from claimpilot.models.policy import CandidateRule, PolicyClause, PolicyIdentity, VerifiedRule
from claimpilot.registry.vrr import VerifiedRuleRegistry
from claimpilot.engine.crg import ClaimResolutionGraph
from claimpilot.models.enums import NodeKind, UncertaintyState
from claimpilot.models.graph import EvidenceEdge, EvidenceNode

def test_tier_matching_confirmation_and_invalidation():
    scope=PolicyIdentity(insurer_id="I", product_uin="U", policy_version="1", endorsement_set_hash="e")
    rule=VerifiedRule(scope=scope, clause=PolicyClause(structural_anchor="1",text="Room   Rent"), logic="cap", verifier_tier=VerifierTier.TIER_1, provenance="p")
    registry=VerifiedRuleRegistry(); registry.add(rule)
    assert registry.lookup(CandidateRule(scope=scope, clause=PolicyClause(structural_anchor="other",text="ROOM RENT"),logic="x")).tier == "A"
    changed=CandidateRule(scope=scope,clause=PolicyClause(structural_anchor="1",text="Room rent excludes ICU"),logic="x")
    assert registry.lookup(changed).tier == "B"
    assert registry.confirm_diff(changed,rule,"confirmed").logic == "x"
    graph=ClaimResolutionGraph(); graph.add_node(EvidenceNode(id="rule",kind=NodeKind.RULE,state=UncertaintyState.VERIFIED,metadata={"rule_scope":scope.model_dump(mode="json")})); graph.add_node(EvidenceNode(id="derived",kind=NodeKind.DERIVATION,state=UncertaintyState.VERIFIED)); graph.add_edge(EvidenceEdge(source_id="rule",target_id="derived"))
    assert all(r.status == RuleStatus.NEEDS_REVERIFICATION for r in registry.invalidate_policy_version(scope, graph=graph))
    assert graph.edges[0].stale
    assert registry.lookup(changed).tier == "C"
