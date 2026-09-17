# ClaimPilot

ClaimPilot is a deterministic Python prototype for resolving health-insurance claim evidence. It represents claim evidence as a directed acyclic graph, preserves uncertainty through downstream derivations, and exports signed, replayable Claim Evidence Packages (CEPs).

## Capabilities

- Strict Pydantic v2 schemas for policies, evidence, issues, rules, and CEPs.
- A non-probabilistic uncertainty lattice: `CONFLICTED` > `MISSING` > `NEEDS_HUMAN_CONFIRMATION` > `UNVERIFIED`.
- Topological graph recomputation and dependency invalidation.
- Verified Rule Registry with exact reuse, diff-confirmation, and safe re-verification states.
- Dynamic ownership resolution for missing-document, conflict, and non-correctable policy issues.
- Canonical JSON CEPs, SHA-256 state digests, Ed25519 detached signatures, and standalone replay validation.

## Requirements

- Python 3.11+
- `pydantic` 2.x
- `cryptography` 41+

## Run tests

```bash
python -m pytest -v
```

The suite covers lattice precedence, registry lookup/invalidation, Section 18 multi-branch propagation, and signed CEP replay validation.

## Layout

```text
claimpilot/
  models/     # Strict domain schemas and enums
  engine/     # Lattice, ownership resolver, and DAG engine
  registry/   # Verified Rule Registry
  package/    # CEP generator and replay validator
tests/        # Executable specification tests
```
