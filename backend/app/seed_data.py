from copy import deepcopy

from .schemas import UncertaintyState as S


BEFORE_NODES = {
    "R1": {"content": "Room-rent sub-limit: Rs 5,000/day", "state": S.VERIFIED, "value": 5000},
    "R2": {"content": "Pre-hospitalisation expenses: 30-day window", "state": S.VERIFIED, "value": 30},
    "R3": {"content": "Diagnostic expense requires itemised report", "state": S.VERIFIED, "value": True},
    "admission_date": {"content": "Admission date from hospital final bill", "state": S.VERIFIED, "value": "03-Mar"},
    "summary_admission_date": {"content": "Admission date from discharge summary", "state": S.VERIFIED, "value": "03-Mar"},
    "discharge_date": {"content": "Discharge date", "state": S.VERIFIED, "value": "07-Mar"},
    "length_of_stay": {"content": "Derived length of stay", "state": S.VERIFIED, "value": 4},
    "E1": {"content": "Room rent Rs 24,000; eligible room rent", "state": S.VERIFIED, "value": 20000},
    "E2": {"content": "Pharmacy bill 02-Feb; within pre-window", "state": S.VERIFIED, "value": True, "metadata": {"boundary_sensitive": False}},
    "E3": {"content": "MRI Rs 18,400; required report", "state": S.MISSING, "value": None},
    "D1": {"content": "MRI report dated 04-Mar, unmatched/orphan", "state": S.UNVERIFIED, "value": {"date": "04-Mar", "procedure_code": "MRI-BRAIN"}},
    "C1": {"content": "Corrected bill vs discharge summary", "state": S.UNVERIFIED, "value": None, "metadata": {"visible": False}},
}

EDGES = [
    {"from": "admission_date", "to": "length_of_stay", "edge_type": "derives", "rule_id": None},
    {"from": "discharge_date", "to": "length_of_stay", "edge_type": "derives", "rule_id": None},
    {"from": "length_of_stay", "to": "E1", "edge_type": "limits", "rule_id": "R1"},
    {"from": "R1", "to": "E1", "edge_type": "policy_rule", "rule_id": "R1"},
    {"from": "admission_date", "to": "E2", "edge_type": "window_check", "rule_id": "R2"},
    {"from": "R2", "to": "E2", "edge_type": "policy_rule", "rule_id": "R2"},
    {"from": "admission_date", "to": "E3", "edge_type": "date_match", "rule_id": "R3"},
    {"from": "D1", "to": "E3", "edge_type": "evidence_match", "rule_id": "R3"},
    {"from": "admission_date", "to": "C1", "edge_type": "conflict_check", "rule_id": None},
    {"from": "summary_admission_date", "to": "C1", "edge_type": "conflict_check", "rule_id": None},
]


def fresh_nodes() -> dict:
    return deepcopy(BEFORE_NODES)

