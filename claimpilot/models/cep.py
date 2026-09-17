from typing import Any
from pydantic import Field, model_validator
from .policy import FrozenModel

FORBIDDEN_PREDICTION_FIELDS = {"approval_probability", "rejection_probability", "guaranteed_coverage"}
class ClaimEvidencePackage(FrozenModel):
    schema_version: str = "3.0"
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    verified_rules: list[dict[str, Any]] = Field(default_factory=list)
    documents: dict[str, str] = Field(default_factory=dict)
    replay: dict[str, str]
    signature: str | None = None
    public_key: str | None = None
    @model_validator(mode="before")
    @classmethod
    def reject_predictions(cls, value: Any) -> Any:
        def scan(obj: Any) -> None:
            if isinstance(obj, dict):
                bad = FORBIDDEN_PREDICTION_FIELDS & set(obj)
                if bad: raise ValueError(f"prediction fields forbidden: {sorted(bad)}")
                for x in obj.values(): scan(x)
            elif isinstance(obj, list):
                for x in obj: scan(x)
        scan(value); return value
