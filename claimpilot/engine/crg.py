from __future__ import annotations
import hashlib, json
from collections import defaultdict, deque
from typing import Callable
from claimpilot.models.enums import UncertaintyState
from claimpilot.models.graph import EvidenceEdge, EvidenceNode
from .lattice import evaluate_required

Compute = Callable[[dict[str, EvidenceNode], EvidenceNode], EvidenceNode]
class ClaimResolutionGraph:
    """A DAG whose derived node state is recomputed from required upstream evidence."""
    def __init__(self) -> None:
        self.nodes: dict[str, EvidenceNode] = {}
        self.edges: list[EvidenceEdge] = []
        self._computations: dict[str, Compute] = {}

    def add_node(self, node: EvidenceNode, compute: Compute | None = None) -> None:
        if node.id in self.nodes: raise ValueError(f"duplicate node {node.id}")
        self.nodes[node.id] = node
        if compute: self._computations[node.id] = compute

    def add_edge(self, edge: EvidenceEdge) -> None:
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes: raise KeyError("edge endpoint absent")
        self.edges.append(edge)

    def replace_node(self, node: EvidenceNode) -> None:
        if node.id not in self.nodes: raise KeyError(node.id)
        self.nodes[node.id] = node

    def _order(self) -> list[str]:
        degree = {key: 0 for key in self.nodes}; children: dict[str, list[str]] = defaultdict(list)
        for edge in self.edges:
            degree[edge.target_id] += 1; children[edge.source_id].append(edge.target_id)
        queue = deque(sorted(key for key, val in degree.items() if val == 0)); order = []
        while queue:
            current = queue.popleft(); order.append(current)
            for child in children[current]:
                degree[child] -= 1
                if degree[child] == 0: queue.append(child)
        if len(order) != len(self.nodes): raise ValueError("ClaimResolutionGraph must be acyclic")
        return order

    def recompute(self) -> None:
        for target in self._order():
            node = self.nodes[target]
            inputs = [self.nodes[e.source_id] for e in self.edges if e.target_id == target and e.required]
            if not inputs: continue
            lattice_state = evaluate_required([n.state for n in inputs])
            if lattice_state != UncertaintyState.VERIFIED:
                self.nodes[target] = node.model_copy(update={"state": lattice_state})
            elif target in self._computations:
                computed = self._computations[target](self.nodes, node)
                # Compute callbacks cannot collapse a verified required input into uncertainty without stating it.
                self.nodes[target] = computed
            else:
                self.nodes[target] = node.model_copy(update={"state": UncertaintyState.VERIFIED})

    def state_digest(self) -> str:
        payload = [{"id": key, "state": self.nodes[key].state.value} for key in sorted(self.nodes)]
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def mark_downstream_stale(self, source_ids: set[str]) -> None:
        """Mark every reachable dependency edge stale after a rule is invalidated."""
        frontier = set(source_ids)
        while frontier:
            next_frontier: set[str] = set()
            for index, edge in enumerate(self.edges):
                if edge.source_id in frontier:
                    self.edges[index] = edge.model_copy(update={"stale": True})
                    next_frontier.add(edge.target_id)
            frontier = next_frontier
