from __future__ import annotations
import base64, hashlib, json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from claimpilot.engine.crg import ClaimResolutionGraph
from claimpilot.models.cep import ClaimEvidencePackage

def canonical_json(value: dict) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
def export_cep(graph: ClaimResolutionGraph, private_key: Ed25519PrivateKey, verified_rules: list[dict] | None = None) -> str:
    documents = {n.id: n.document_hash for n in graph.nodes.values() if n.document_hash}
    payload = {"nodes":[n.model_dump(mode="json") for n in graph.nodes.values()], "edges":[e.model_dump(mode="json") for e in graph.edges], "verified_rules":verified_rules or [], "documents":documents, "replay":{"expected_state_digest":graph.state_digest()}}
    digest=hashlib.sha256(canonical_json(payload)).digest(); signature=private_key.sign(digest)
    public=private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    cep=ClaimEvidencePackage(**payload, signature=base64.b64encode(signature).decode(), public_key=base64.b64encode(public).decode())
    return cep.model_dump_json()
