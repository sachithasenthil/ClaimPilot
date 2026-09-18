from __future__ import annotations

import json
import sys
from pathlib import Path

from .export import canonical, state_digest
from .graph_engine import corrected_scenario
from .schemas import PackageEnvelope
from .seed_data import fresh_nodes


def validate_package(path: str) -> bool:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    package = PackageEnvelope.model_validate(raw)
    unsigned = package.model_dump(mode="json", by_alias=True)
    fingerprint = unsigned.pop("fingerprint_sha256")
    if fingerprint != __import__("hashlib").sha256(canonical(unsigned)).hexdigest():
        return False
    recomputed = corrected_scenario(fresh_nodes())
    return state_digest(recomputed) == package.replay["expected_state_digest"]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m app.replay_validator <package.json>")
    ok = validate_package(sys.argv[1])
    print("MATCH" if ok else "MISMATCH")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()

