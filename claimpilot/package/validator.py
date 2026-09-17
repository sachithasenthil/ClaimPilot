from __future__ import annotations
import base64, hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from claimpilot.engine.crg import ClaimResolutionGraph
from claimpilot.models.cep import ClaimEvidencePackage
from claimpilot.models.graph import EvidenceEdge, EvidenceNode
from .generator import canonical_json

def validate_and_replay(cep_json: str) -> bool:
    cep=ClaimEvidencePackage.model_validate_json(cep_json)
    payload={"nodes":cep.nodes,"edges":cep.edges,"verified_rules":cep.verified_rules,"documents":cep.documents,"replay":cep.replay}
    if cep.signature and cep.public_key:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(cep.public_key)).verify(base64.b64decode(cep.signature), hashlib.sha256(canonical_json(payload)).digest())
    graph=ClaimResolutionGraph()
    for node in cep.nodes: graph.add_node(EvidenceNode.model_validate(node))
    for edge in cep.edges: graph.add_edge(EvidenceEdge.model_validate(edge))
    graph.recompute()
    return graph.state_digest() == cep.replay["expected_state_digest"]
