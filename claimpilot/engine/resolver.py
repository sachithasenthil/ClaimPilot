from claimpilot.models.enums import IssueClass
from claimpilot.models.graph import Issue, ResolutionAction

def resolve_ownership(issue: Issue) -> ResolutionAction:
    if issue.issue_class == IssueClass.NON_CORRECTABLE_POLICY_CONDITION:
        return ResolutionAction(evidence_owner=None, resolution_authority=None, available_action=None, resolution_owner=None)
    if issue.issue_class == IssueClass.CONFLICT:
        return ResolutionAction(evidence_owner=issue.authoritative_issuer or "Authoritative issuer", resolution_authority=issue.authoritative_issuer or "Authoritative issuer", available_action="Request correction or clarification", resolution_owner="Claimant")
    if issue.issue_class == IssueClass.MISSING_DOCUMENT:
        return ResolutionAction(evidence_owner="Hospital", resolution_authority="Hospital", available_action="Request document through hospital channel", resolution_owner="Claimant")
    raise ValueError(f"unsupported issue class: {issue.issue_class}")
