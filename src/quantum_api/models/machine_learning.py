from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from quantum_api.models.qiskit_common import QiskitDomainProvider


class FeatureMapConfig(BaseModel):
    type: Literal["zz_feature_map"] = "zz_feature_map"
    reps: int = Field(default=1, ge=1, le=4)
    entanglement: Literal["linear", "full", "circular"] = "full"

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"type": "zz_feature_map", "reps": 1, "entanglement": "full"}},
    )


class KernelClassifierRequest(BaseModel):
    training_features: list[list[float]] = Field(min_length=2, max_length=32)
    training_labels: list[int | str] = Field(min_length=2, max_length=32)
    prediction_features: list[list[float]] = Field(min_length=1, max_length=32)
    feature_map: FeatureMapConfig = Field(default_factory=FeatureMapConfig)
    seed: int | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "training_features": [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]],
                "training_labels": [0, 1, 1, 0],
                "prediction_features": [[0.1, 0.2], [0.9, 0.8]],
                "feature_map": {"type": "zz_feature_map", "reps": 1, "entanglement": "full"},
                "seed": 7,
            }
        },
    )

    @model_validator(mode="after")
    def validate_shapes(self) -> KernelClassifierRequest:
        if len(self.training_features) != len(self.training_labels):
            raise ValueError("training_features and training_labels must have the same length")
        feature_dimension = len(self.training_features[0])
        if feature_dimension == 0:
            raise ValueError("feature vectors must not be empty")
        for row in [*self.training_features, *self.prediction_features]:
            if len(row) != feature_dimension:
                raise ValueError("all feature vectors must share the same dimension")
        return self


class KernelClassifierResponse(BaseModel):
    predictions: list[int | str]
    training_score: float
    support_vector_count: int
    training_metadata: dict[str, Any]
    provider: QiskitDomainProvider = "qiskit-machine-learning"
    backend_mode: str = "fidelity_quantum_kernel"

    model_config = ConfigDict(extra="forbid")
