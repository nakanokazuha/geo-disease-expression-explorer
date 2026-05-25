"""Executable contract models for app-facing Gold artifacts."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.contracts.export_contract import ExportContext
from app.domain.enums import CountryMetadataStatus, EffectDirection, EffectDirectionFilter, SourceSystem


class ContractBaseModel(BaseModel):
    """Base model for strict app-facing contract validation."""

    model_config = ConfigDict(extra="forbid")


class ProvenanceContext(ContractBaseModel):
    """Shared provenance context attached to Gold artifacts."""

    dataset_version: str = Field(min_length=1)
    pipeline_version: str = Field(min_length=1)
    generated_at: datetime
    source_system: SourceSystem = SourceSystem.GEO
    included_studies: list[str] = Field(min_length=1)
    curation_notes: list[str] = Field(default_factory=list)
    metadata_quality_notes: list[str] = Field(default_factory=list)


class DashboardSummary(ContractBaseModel):
    """First-screen dataset summary consumed by the dashboard overview."""

    artifact_version: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    generated_at: datetime
    provenance: ProvenanceContext
    included_study_count: int = Field(ge=0)
    included_sample_count: int = Field(ge=0)
    case_sample_count: int = Field(ge=0)
    control_sample_count: int = Field(ge=0)
    sample_source_counts: dict[str, int] = Field(default_factory=dict)
    study_sample_counts: dict[str, int] = Field(default_factory=dict)
    country_counts: dict[str, int] = Field(default_factory=dict)
    country_metadata_status: CountryMetadataStatus

    @field_validator("sample_source_counts", "study_sample_counts", "country_counts")
    @classmethod
    def _counts_must_be_non_negative(cls, counts: dict[str, int]) -> dict[str, int]:
        if any(value < 0 for value in counts.values()):
            raise ValueError("summary counts must be non-negative")
        return counts


class StudySummaryRecord(ContractBaseModel):
    """Study-level metadata used for provenance and study-aware views."""

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


class MergedDegRecord(ContractBaseModel):
    """App-safe differential expression table record."""

    gene_id: str = Field(min_length=1)
    gene_symbol: str = Field(min_length=1)
    log2_fold_change: float
    adjusted_p_value: float = Field(ge=0.0, le=1.0)
    p_value: float = Field(ge=0.0, le=1.0)
    effect_direction: EffectDirection
    study_accessions: list[str] = Field(min_length=1)
    sample_source: str = Field(min_length=1)
    provenance_note: str = Field(min_length=1)
    gene_name: str | None = None
    chromosome: str | None = None
    mean_expression_case: float | None = None
    mean_expression_control: float | None = None


class VolcanoPoint(ContractBaseModel):
    """Chart-ready volcano point."""

    gene_id: str = Field(min_length=1)
    gene_symbol: str = Field(min_length=1)
    x_log2_fold_change: float
    y_neg_log10_adjusted_p_value: float = Field(ge=0.0)
    adjusted_p_value: float = Field(ge=0.0, le=1.0)
    effect_direction: EffectDirection
    study_accessions: list[str] = Field(min_length=1)


class HeatmapMatrix(ContractBaseModel):
    """Chart-ready heatmap matrix."""

    gene_symbols: list[str] = Field(min_length=1)
    sample_or_group_labels: list[str] = Field(min_length=1)
    values: list[list[float]] = Field(min_length=1)
    value_kind: str = Field(min_length=1)
    study_accessions: list[str] = Field(min_length=1)
    top_n: int = Field(gt=0)

    @model_validator(mode="after")
    def _values_must_be_rectangular(self) -> "HeatmapMatrix":
        expected_width = len(self.sample_or_group_labels)
        if len(self.values) != len(self.gene_symbols):
            raise ValueError("heatmap values must include one row per gene")
        if any(len(row) != expected_width for row in self.values):
            raise ValueError("heatmap values must be rectangular")
        return self


class FilterThresholdRange(ContractBaseModel):
    """Numeric threshold range exposed to the UI."""

    default: float
    minimum: float
    maximum: float

    @model_validator(mode="after")
    def _default_must_be_inside_range(self) -> "FilterThresholdRange":
        if self.minimum > self.maximum:
            raise ValueError("threshold minimum cannot exceed maximum")
        if not self.minimum <= self.default <= self.maximum:
            raise ValueError("threshold default must be inside range")
        return self


class FilterOptions(ContractBaseModel):
    """Canonical filter options available to the UI."""

    studies: list[str] = Field(default_factory=list)
    sample_sources: list[str] = Field(default_factory=list)
    effect_directions: list[EffectDirectionFilter] = Field(min_length=1)
    adjusted_p_value: FilterThresholdRange
    log2_fold_change: FilterThresholdRange
    countries: list[str] = Field(default_factory=list)
    country_filter_enabled: bool
    country_filter_reason: str = Field(min_length=1)
    country_metadata_status: CountryMetadataStatus

    @model_validator(mode="after")
    def _country_filter_requires_reliable_metadata(self) -> "FilterOptions":
        if self.country_filter_enabled and self.country_metadata_status is not CountryMetadataStatus.RELIABLE:
            raise ValueError("country filter requires reliable country metadata")
        if self.country_filter_enabled and not self.countries:
            raise ValueError("country filter requires at least one country option")
        return self


class GoldArtifactBundle(ContractBaseModel):
    """Complete set of required app-facing Gold artifact families."""

    dashboard_summary: DashboardSummary
    study_summary: list[StudySummaryRecord] = Field(min_length=1)
    merged_deg_table: list[MergedDegRecord] = Field(min_length=1)
    volcano_points: list[VolcanoPoint] = Field(min_length=1)
    heatmap_matrix: HeatmapMatrix
    filter_options: FilterOptions
    export_context: ExportContext
