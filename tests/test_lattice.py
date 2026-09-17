import pytest
from claimpilot.engine.lattice import evaluate_required
from claimpilot.models.enums import UncertaintyState as S

@pytest.mark.parametrize(("states", "expected"), [
    ([S.VERIFIED, S.VERIFIED], S.VERIFIED), ([S.UNVERIFIED], S.UNVERIFIED),
    ([S.NEEDS_HUMAN_CONFIRMATION, S.UNVERIFIED], S.NEEDS_HUMAN_CONFIRMATION),
    ([S.MISSING, S.NEEDS_HUMAN_CONFIRMATION], S.MISSING),
    ([S.CONFLICTED, S.MISSING], S.CONFLICTED), ([], S.UNVERIFIED)])
def test_lattice_precedence(states, expected): assert evaluate_required(states) == expected
