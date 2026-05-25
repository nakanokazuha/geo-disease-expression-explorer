"""Pipeline run manifest contracts."""

from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class PipelineStage(StrEnum):
    """Supported local pipeline stages."""

    BRONZE_INGESTION = "bronze_ingestion"
    SILVER_HARMONIZATION = "silver_harmonization"
    GOLD_PUBLICATION = "gold_publication"
    FULL_REFRESH = "full_refresh"


class PipelineStatus(StrEnum):
    """Supported pipeline stage statuses."""

    SUCCESS = "success"
    FAILED = "failed"


class PipelineManifest(BaseModel):
    """Serializable manifest emitted by each pipeline stage."""

    model_config = ConfigDict(extra="forbid")

    stage: PipelineStage
    status: PipelineStatus
    started_at: datetime
    finished_at: datetime
    input_paths: list[Path] = Field(default_factory=list)
    output_paths: list[Path] = Field(default_factory=list)
    record_count: int = Field(ge=0)
    notes: list[str] = Field(default_factory=list)

    @field_serializer("input_paths", "output_paths", when_used="json")
    def _serialize_paths(self, paths: list[Path]) -> list[str]:
        return [path.as_posix() for path in paths]
