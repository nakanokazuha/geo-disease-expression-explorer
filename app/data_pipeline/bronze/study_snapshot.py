"""Bronze study snapshot models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BronzeStudySnapshot(BaseModel):
    """Source-faithful curated study snapshot for the Bronze layer."""

    model_config = ConfigDict(extra="forbid")

    study_accession: str = Field(min_length=1)
    study_title: str = Field(min_length=1)
    organism: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    sample_count: int = Field(ge=0)
    case_sample_count: int = Field(ge=0)
    control_sample_count: int = Field(ge=0)
    sample_sources: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    curation_notes: list[str] = Field(default_factory=list)
    metadata_quality_flags: list[str] = Field(default_factory=list)
    ingested_at: datetime

    @model_validator(mode="after")
    def _sample_count_must_match_groups(self) -> "BronzeStudySnapshot":
        if self.sample_count != self.case_sample_count + self.control_sample_count:
            raise ValueError("sample_count must equal case_sample_count + control_sample_count")
        return self
