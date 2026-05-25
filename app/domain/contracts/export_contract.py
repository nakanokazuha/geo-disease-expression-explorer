"""Export-safe contract models for app-facing Gold artifacts."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EffectDirectionFilter, ExportKind


class ThresholdContext(BaseModel):
    """Threshold and filter state attached to an export."""

    model_config = ConfigDict(extra="forbid")

    adjusted_p_value: float = Field(ge=0.0, le=1.0)
    log2_fold_change: float = Field(ge=0.0, le=10.0)
    selected_studies: list[str] = Field(default_factory=list)
    selected_sample_sources: list[str] = Field(default_factory=list)
    effect_direction: EffectDirectionFilter = EffectDirectionFilter.ALL
    selected_countries: list[str] = Field(default_factory=list)


class ExportContext(BaseModel):
    """Context that must accompany approved v1 exports."""

    model_config = ConfigDict(extra="forbid")

    dataset_version: str = Field(min_length=1)
    pipeline_version: str = Field(min_length=1)
    generated_at: datetime
    included_studies: list[str] = Field(min_length=1)
    threshold_context: ThresholdContext
    provenance_statement: str = Field(min_length=1)
    disclaimer: str = Field(min_length=1)
    allowed_export_kinds: list[ExportKind] = Field(min_length=1)
