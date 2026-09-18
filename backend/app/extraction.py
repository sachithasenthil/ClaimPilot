from __future__ import annotations

import io
from typing import Any

import pdfplumber
from pydantic import BaseModel

from .llm_client import llm_client
from .schemas import CandidateRuleOut


def extract_clauses(pdf_bytes: bytes) -> tuple[int, list[dict[str, Any]]]:
    clauses = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            words = page.extract_words() or []
            text = page.extract_text() or ""
            if text.strip():
                bbox = [0, 0, float(page.width), float(page.height)]
                if words:
                    bbox = [min(w["x0"] for w in words), min(w["top"] for w in words),
                            max(w["x1"] for w in words), max(w["bottom"] for w in words)]
                clauses.append({"source_page": page_number, "source_section": f"Page {page_number}",
                                "raw_text": text.strip(), "structural_anchor": f"page:{page_number}:bbox:{bbox}"})
        return len(pdf.pages), clauses


class RuleDraft(BaseModel):
    conditions: dict[str, Any]
    required_evidence: str
    affected_expense_type: str


async def propose_rule(clause_text: str) -> RuleDraft:
    prompt = "Convert this policy clause into a candidate reimbursement evidence rule. Return JSON only. Clause:\n" + clause_text
    return await llm_client.generate_json(prompt, RuleDraft)

