"""Silver study metadata records."""

from pydantic import BaseModel, ConfigDict, Field


class SilverStudyRecord(BaseModel):
    """Standardized study metadata record for downstream Gold publication."""

    model_config = ConfigDict(extra="forbid", strict=True)

    study_accession: str = Field(min_length=1)
    study_title: str = Field(min_length=1)
    organism: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    included: bool
    inclusion_notes: str = Field(min_length=1)
    sample_count: int = Field(ge=0)
    case_sample_count: int = Field(ge=0)
    control_sample_count: int = Field(ge=0)
    sample_sources: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    metadata_quality_flags: list[str] = Field(default_factory=list)
