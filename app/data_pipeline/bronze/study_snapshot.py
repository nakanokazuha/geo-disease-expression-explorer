"""Bronze study snapshot models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StudyPlatform(BaseModel):
    """GEO platform metadata captured during curation."""

    model_config = ConfigDict(extra="forbid")

    accession: str = Field(min_length=1)
    name: str = Field(min_length=1)


class CuratedStudyRecord(BaseModel):
    """Reviewed GEO study registry record."""

    model_config = ConfigDict(extra="forbid")

    study_accession: str = Field(min_length=1)
    study_title: str = Field(min_length=1)
    organism: str = Field(min_length=1)
    platforms: list[StudyPlatform] = Field(min_length=1)
    sample_count: int = Field(ge=0)
    case_sample_count: int = Field(ge=0)
    control_sample_count: int = Field(ge=0)
    sample_sources: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    publication_urls: list[str] = Field(default_factory=list)
    curation_status: str = Field(min_length=1)
    pipeline_active: bool
    expression_candidate: bool
    phenotype_label_status: str = Field(min_length=1)
    curation_notes: list[str] = Field(default_factory=list)
    metadata_quality_flags: list[str] = Field(default_factory=list)

    @property
    def platform_summary(self) -> str:
        return "; ".join(
            f"{platform.accession} {platform.name}" for platform in self.platforms
        )

    @model_validator(mode="after")
    def _verified_sample_count_must_match_groups(self) -> "CuratedStudyRecord":
        if self.phenotype_label_status.lower().startswith("verified"):
            if self.sample_count != self.case_sample_count + self.control_sample_count:
                raise ValueError(
                    "sample_count must equal case_sample_count + control_sample_count"
                )
        return self


class BronzeStudySnapshot(BaseModel):
    """Source-faithful curated study snapshot for the Bronze layer."""

    model_config = ConfigDict(extra="forbid")

    study_accession: str = Field(min_length=1)
    study_title: str = Field(min_length=1)
    organism: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    platforms: list[StudyPlatform] = Field(min_length=1)
    sample_count: int = Field(ge=0)
    case_sample_count: int = Field(ge=0)
    control_sample_count: int = Field(ge=0)
    sample_sources: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    publication_urls: list[str] = Field(default_factory=list)
    curation_status: str = Field(min_length=1)
    pipeline_active: bool
    expression_candidate: bool
    phenotype_label_status: str = Field(min_length=1)
    curation_notes: list[str] = Field(default_factory=list)
    metadata_quality_flags: list[str] = Field(default_factory=list)
    ingested_at: datetime

    @classmethod
    def from_curated_record(
        cls,
        record: CuratedStudyRecord,
        ingested_at: datetime,
    ) -> "BronzeStudySnapshot":
        return cls(
            **record.model_dump(mode="python"),
            platform=record.platform_summary,
            ingested_at=ingested_at,
        )

    @model_validator(mode="after")
    def _verified_sample_count_must_match_groups(self) -> "BronzeStudySnapshot":
        if self.phenotype_label_status.lower().startswith("verified"):
            if self.sample_count != self.case_sample_count + self.control_sample_count:
                raise ValueError(
                    "sample_count must equal case_sample_count + control_sample_count"
                )
        return self
