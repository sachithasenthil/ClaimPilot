from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .export import build_package
from .extraction import extract_clauses, propose_rule
from .graph_engine import corrected_scenario
from .llm_client import LLMConfigurationError, LLMUpstreamError
from .models import CandidateRule, PolicyClause, SourceDocument, VerifiedRule, SessionLocal, init_db
from .ownership import resolution_for
from .schemas import (CandidateRuleOut, CorrectionRequest, GraphEdge, GraphNode, GraphResponse,
                      IssueOut, PackageEnvelope, PolicyClauseOut, UploadResponse, VerifiedRuleOut)
from .seed_data import EDGES, fresh_nodes

app = FastAPI(title="ClaimPilot", version="1.0-hackathon")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
CLAIM_STATE: dict[str, dict] = {}


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/policies/upload", response_model=UploadResponse)
async def upload_policy(file: UploadFile = File(...)) -> UploadResponse:
    data = await file.read()
    try:
        page_count, clauses = extract_clauses(data)
    except Exception as exc:
        raise HTTPException(400, "A readable PDF is required") from exc
    with SessionLocal.begin() as db:
        document = SourceDocument(kind="policy", filename=file.filename or "policy.pdf",
                                  sha256=hashlib.sha256(data).hexdigest(), page_count=page_count)
        db.add(document); db.flush()
        for clause in clauses:
            db.add(PolicyClause(**clause))
        return UploadResponse(id=document.id, filename=document.filename, sha256=document.sha256, page_count=page_count)


@app.get("/policies/{policy_id}/clauses", response_model=list[PolicyClauseOut])
def list_clauses(policy_id: int) -> list[PolicyClause]:
    with SessionLocal() as db:
        # The hackathon prototype has one active policy; policy_id names its uploaded source.
        return list(db.query(PolicyClause).order_by(PolicyClause.source_page).all())


@app.post("/clauses/{clause_id}/propose-rule", response_model=CandidateRuleOut)
async def create_candidate(clause_id: int) -> CandidateRule:
    with SessionLocal.begin() as db:
        clause = db.get(PolicyClause, clause_id)
        if not clause:
            raise HTTPException(404, "Clause not found")
        try:
            draft = await propose_rule(clause.raw_text)
        except LLMConfigurationError as exc:
            raise HTTPException(503, str(exc)) from exc
        except LLMUpstreamError as exc:
            raise HTTPException(502, str(exc)) from exc
        except Exception as exc:
            raise HTTPException(422, "Gemini output failed strict RuleDraft schema validation and was discarded") from exc
        candidate = CandidateRule(clause_id=clause_id, status="pending", **draft.model_dump())
        db.add(candidate); db.flush()
        return candidate


@app.post("/rules/{rule_id}/verify", response_model=VerifiedRuleOut)
def verify_rule(rule_id: int, verified_by: str = "demo-reviewer") -> VerifiedRule:
    with SessionLocal.begin() as db:
        candidate = db.get(CandidateRule, rule_id)
        if not candidate:
            raise HTTPException(404, "Candidate rule not found")
        if candidate.status != "pending":
            raise HTTPException(409, "Candidate is no longer pending")
        candidate.status = "verified"
        verified = VerifiedRule(candidate_rule_id=candidate.id, rule_id=f"VR-{candidate.id}", rule_version="1.0",
                                verified_at=datetime.now(timezone.utc).replace(tzinfo=None), verified_by=verified_by)
        db.add(verified); db.flush()
        return VerifiedRuleOut.model_validate({**verified.__dict__, "verified_at": verified.verified_at.isoformat()})


@app.post("/rules/{rule_id}/reject", response_model=CandidateRuleOut)
def reject_rule(rule_id: int) -> CandidateRule:
    with SessionLocal.begin() as db:
        candidate = db.get(CandidateRule, rule_id)
        if not candidate:
            raise HTTPException(404, "Candidate rule not found")
        candidate.status = "rejected"
        return candidate


@app.post("/claims/{claim_id}/documents", response_model=UploadResponse)
async def upload_claim_document(claim_id: str, kind: str, file: UploadFile = File(...)) -> UploadResponse:
    data = await file.read()
    with SessionLocal.begin() as db:
        document = SourceDocument(kind=kind, filename=file.filename or "claim.pdf",
                                  sha256=hashlib.sha256(data).hexdigest(), page_count=1)
        db.add(document); db.flush()
        CLAIM_STATE.setdefault(claim_id, fresh_nodes())
        return UploadResponse(id=document.id, filename=document.filename, sha256=document.sha256, page_count=1)


def graph_response(claim_id: str) -> GraphResponse:
    nodes = CLAIM_STATE.setdefault(claim_id, fresh_nodes())
    visible = []
    for node_id, node in nodes.items():
        if node.get("metadata", {}).get("visible") is False:
            continue
        visible.append(GraphNode(id=node_id, content=node["content"], state=node["state"], value=node.get("value"),
                                 changed=node.get("changed", False), metadata=node.get("metadata", {})))
    return GraphResponse(claim_id=claim_id, corrected=nodes["admission_date"]["value"] == "04-Mar",
                         nodes=visible, edges=[GraphEdge.model_validate(edge) for edge in EDGES])


@app.get("/claims/{claim_id}/graph", response_model=GraphResponse)
def get_graph(claim_id: str) -> GraphResponse:
    return graph_response(claim_id)


@app.post("/claims/{claim_id}/documents/{doc_id}/correct", response_model=GraphResponse)
def correct_document(claim_id: str, doc_id: str, correction: CorrectionRequest) -> GraphResponse:
    if correction.model_dump() != CorrectionRequest().model_dump():
        raise HTTPException(400, "This prototype accepts only the scripted corrected bill")
    CLAIM_STATE[claim_id] = corrected_scenario(CLAIM_STATE.setdefault(claim_id, fresh_nodes()))
    return graph_response(claim_id)


@app.get("/claims/{claim_id}/issues", response_model=list[IssueOut])
def get_issues(claim_id: str, include_non_correctable_demo: bool = False) -> list[IssueOut]:
    nodes = CLAIM_STATE.setdefault(claim_id, fresh_nodes())
    issues = []
    if nodes["E3"]["state"] == "MISSING":
        data = resolution_for("missing_document_that_exists")
        issues.append(IssueOut(id="I1", involved_nodes=["E3", "D1"], issue_class="missing_document_that_exists", state="OPEN", **data))
    if nodes["C1"]["state"] == "CONFLICTED":
        data = resolution_for("conflict_between_two_documents")
        issues.append(IssueOut(id="C1", involved_nodes=["admission_date", "summary_admission_date"], issue_class="conflict_between_two_documents", state="OPEN", **data))
    if include_non_correctable_demo:
        data = resolution_for("non_correctable_policy_condition")
        issues.append(IssueOut(id="NC1", involved_nodes=["R1"], issue_class="non_correctable_policy_condition", state="STOPPED", **data))
    return issues


@app.post("/claims/{claim_id}/export", response_model=PackageEnvelope)
def export_claim(claim_id: str) -> PackageEnvelope:
    CLAIM_STATE[claim_id] = corrected_scenario(CLAIM_STATE.setdefault(claim_id, fresh_nodes()))
    with SessionLocal() as db:
        docs = [{"document_id": d.id, "kind": d.kind, "sha256": d.sha256, "page_count": d.page_count}
                for d in db.query(SourceDocument).all()]
        rules = []
        for verified, candidate, clause in db.query(VerifiedRule, CandidateRule, PolicyClause).join(
                CandidateRule, VerifiedRule.candidate_rule_id == CandidateRule.id).join(
                PolicyClause, CandidateRule.clause_id == PolicyClause.id).all():
            rules.append({"rule_id": verified.rule_id, "rule_version": verified.rule_version,
                          "clause_anchor": clause.structural_anchor, "raw_clause_text": clause.raw_text,
                          "verified_at": verified.verified_at.isoformat()})
    return build_package(claim_id, docs, rules)
