from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Callable

from .schemas import UncertaintyState as S
from .seed_data import EDGES, fresh_nodes


def propagate_state(states: list[S]) -> S:
    if states and all(state == S.VERIFIED for state in states):
        return S.VERIFIED
    for state in (S.CONFLICTED, S.MISSING, S.NEEDS_HUMAN_CONFIRMATION, S.UNVERIFIED):
        if state in states:
            return state
    return S.UNVERIFIED


def _stay(nodes: dict) -> dict:
    return {"value": 3 if nodes["admission_date"]["value"] == "04-Mar" else 4, "state": S.VERIFIED}


def _room(nodes: dict) -> dict:
    days = nodes["length_of_stay"]["value"]
    return {"value": min(24000, days * nodes["R1"]["value"]), "state": S.VERIFIED}


def _prewindow(nodes: dict) -> dict:
    corrected = nodes["admission_date"]["value"] == "04-Mar"
    return {"value": True, "state": S.VERIFIED, "metadata": {"boundary_sensitive": corrected}}


def _report(nodes: dict) -> dict:
    item = nodes["admission_date"].get("metadata", {}).get("mri_item")
    report = nodes["D1"]["value"]
    matched = bool(item and item["date"] == report["date"] and item["procedure_code"] == report["procedure_code"])
    return {"value": {"matched_report": "D1"} if matched else None, "state": S.VERIFIED if matched else S.MISSING}


def _conflict(nodes: dict) -> dict:
    conflict = nodes["admission_date"]["value"] != nodes["summary_admission_date"]["value"]
    return {"value": "Final bill says 04-Mar; discharge summary says 03-Mar" if conflict else None,
            "state": S.CONFLICTED if conflict else S.VERIFIED, "metadata": {"visible": conflict}}


# Fixed scenario computations only. This is not a registry or general graph solver.
COMPUTE: dict[str, Callable[[dict], dict]] = {
    "length_of_stay": _stay, "E1": _room, "E2": _prewindow, "E3": _report, "C1": _conflict,
}


def recompute_from(nodes: dict, changed_id: str) -> dict:
    nodes = deepcopy(nodes)
    children: dict[str, list[str]] = {}
    for edge in EDGES:
        children.setdefault(edge["from"], []).append(edge["to"])
    queue = deque(children.get(changed_id, []))
    queued = set(queue)
    while queue:
        target = queue.popleft()
        queued.discard(target)
        if target in COMPUTE:
            old = deepcopy(nodes[target])
            nodes[target].update(COMPUTE[target](nodes))
            nodes[target]["changed"] = any(old.get(k) != nodes[target].get(k) for k in ("value", "state", "metadata"))
            if nodes[target] != old:
                for child in children.get(target, []):
                    if child not in queued:
                        queue.append(child); queued.add(child)
    return nodes


def corrected_scenario(before: dict | None = None) -> dict:
    nodes = deepcopy(before or fresh_nodes())
    nodes["admission_date"].update({
        "value": "04-Mar", "changed": True,
        "metadata": {"mri_item": {"date": "04-Mar", "procedure_code": "MRI-BRAIN"}},
    })
    return recompute_from(nodes, "admission_date")

