from claimpilot.models.enums import UncertaintyState

PRECEDENCE = (UncertaintyState.CONFLICTED, UncertaintyState.MISSING,
              UncertaintyState.NEEDS_HUMAN_CONFIRMATION, UncertaintyState.UNVERIFIED)
def evaluate_required(states: list[UncertaintyState]) -> UncertaintyState:
    """Deterministic uncertainty join; empty inputs are unverified, never implicitly verified."""
    if states and all(state == UncertaintyState.VERIFIED for state in states):
        return UncertaintyState.VERIFIED
    for state in PRECEDENCE:
        if state in states: return state
    return UncertaintyState.UNVERIFIED
