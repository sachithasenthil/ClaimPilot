import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError
from claimpilot.engine.crg import ClaimResolutionGraph
from claimpilot.models.cep import ClaimEvidencePackage
from claimpilot.models.enums import NodeKind, UncertaintyState as S
from claimpilot.models.graph import EvidenceEdge, EvidenceNode
from claimpilot.package.generator import export_cep
from claimpilot.package.validator import validate_and_replay

def test_signed_package_replays_and_predictions_rejected():
    g=ClaimResolutionGraph(); g.add_node(EvidenceNode(id="a",kind=NodeKind.DOCUMENT,state=S.VERIFIED,document_hash="abc")); g.add_node(EvidenceNode(id="b",kind=NodeKind.DERIVATION,state=S.UNVERIFIED)); g.add_edge(EvidenceEdge(source_id="a",target_id="b")); g.recompute()
    assert validate_and_replay(export_cep(g,Ed25519PrivateKey.generate()))
    with pytest.raises(ValidationError): ClaimEvidencePackage(nodes=[],edges=[],replay={"expected_state_digest":"x"},approval_probability=.5)
