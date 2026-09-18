from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class PolicyClause(Base):
    __tablename__ = "policy_clauses"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_page: Mapped[int]
    source_section: Mapped[str] = mapped_column(String(200))
    raw_text: Mapped[str] = mapped_column(Text)
    structural_anchor: Mapped[str] = mapped_column(String(300))


class CandidateRule(Base):
    __tablename__ = "candidate_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    clause_id: Mapped[int] = mapped_column(ForeignKey("policy_clauses.id"))
    conditions: Mapped[dict] = mapped_column(JSON)
    required_evidence: Mapped[str] = mapped_column(Text)
    affected_expense_type: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="pending")


class VerifiedRule(Base):
    __tablename__ = "verified_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_rule_id: Mapped[int] = mapped_column(ForeignKey("candidate_rules.id"))
    rule_id: Mapped[str] = mapped_column(String(50), unique=True)
    rule_version: Mapped[str] = mapped_column(String(20))
    verified_at: Mapped[datetime] = mapped_column(DateTime)
    verified_by: Mapped[str] = mapped_column(String(100))


class SourceDocument(Base):
    __tablename__ = "source_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(50))
    filename: Mapped[str] = mapped_column(String(300))
    sha256: Mapped[str] = mapped_column(String(64))
    page_count: Mapped[int]


class ExtractedField(Base):
    __tablename__ = "extracted_fields"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(Text)
    document_id: Mapped[int] = mapped_column(ForeignKey("source_documents.id"))
    page: Mapped[int]
    bbox: Mapped[list] = mapped_column(JSON)
    uncertainty_state: Mapped[str] = mapped_column(String(40))


class EvidenceNode(Base):
    __tablename__ = "evidence_nodes"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    kind: Mapped[str] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(40))


class EvidenceEdge(Base):
    __tablename__ = "evidence_edges"
    id: Mapped[int] = mapped_column(primary_key=True)
    from_node: Mapped[str] = mapped_column(String(80))
    to_node: Mapped[str] = mapped_column(String(80))
    edge_type: Mapped[str] = mapped_column(String(60))
    rule_id: Mapped[str | None] = mapped_column(String(50), nullable=True)


class Issue(Base):
    __tablename__ = "issues"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    involved_nodes: Mapped[list] = mapped_column(JSON)
    issue_class: Mapped[str] = mapped_column("class", String(100))
    state: Mapped[str] = mapped_column(String(40))


class ResolutionAction(Base):
    __tablename__ = "resolution_actions"
    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[str] = mapped_column(ForeignKey("issues.id"))
    action_type: Mapped[str] = mapped_column(String(120))
    resolution_owner: Mapped[str] = mapped_column(String(100))


class ClaimEvidencePackage(Base):
    __tablename__ = "claim_evidence_packages"
    id: Mapped[int] = mapped_column(primary_key=True)
    claim_ref: Mapped[str] = mapped_column(String(100))
    generated_at: Mapped[datetime] = mapped_column(DateTime)
    fingerprint_sha256: Mapped[str] = mapped_column(String(64))
    payload_json: Mapped[dict] = mapped_column(JSON)


engine = create_engine("sqlite:///./claimpilot.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)

