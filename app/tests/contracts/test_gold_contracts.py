from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.contracts import (
    DashboardSummary,
    FilterOptions,
    FilterThresholdRange,
    GoldArtifactBundle,
    HeatmapMatrix,
    MergedDegRecord,
    ProvenanceContext,
    StudySummaryRecord,
    VolcanoPoint,
)
from app.domain.contracts.export_contract import ExportContext, ThresholdContext
from app.domain.enums import (
    CountryMetadataStatus,
    EffectDirection,
    EffectDirectionFilter,
    ExportKind,
    SourceSystem,
)

GENERATED_AT = datetime(2026, 5, 25, tzinfo=UTC)


def test_contract_enums_expose_stable_values() -> None:
    assert CountryMetadataStatus.RELIABLE == "reliable"
    assert CountryMetadataStatus.PARTIAL == "partial"
    assert CountryMetadataStatus.WEAK == "weak"
    assert CountryMetadataStatus.UNAVAILABLE == "unavailable"
    assert EffectDirection.UPREGULATED == "upregulated"
    assert EffectDirection.DOWNREGULATED == "downregulated"
    assert EffectDirection.UNCHANGED == "unchanged"
    assert EffectDirectionFilter.ALL == "all"
    assert ExportKind.FILTERED_DEG_CSV == "filtered_deg_csv"
    assert ExportKind.SELECTED_GENE_LIST_CSV == "selected_gene_list_csv"
    assert SourceSystem.GEO == "GEO"


def _provenance() -> ProvenanceContext:
    return ProvenanceContext(
        dataset_version="long-covid-v1",
        pipeline_version="pipeline-0.1.0",
        generated_at=GENERATED_AT,
        source_system=SourceSystem.GEO,
        included_studies=["GSE000001"],
        curation_notes=["Initial curated snapshot."],
        metadata_quality_notes=["Country metadata not exposed as a filter."],
    )


def _export_context() -> ExportContext:
    return ExportContext(
        dataset_version="long-covid-v1",
        pipeline_version="pipeline-0.1.0",
        generated_at=GENERATED_AT,
        included_studies=["GSE000001"],
        threshold_context=ThresholdContext(
            adjusted_p_value=0.05,
            log2_fold_change=1.0,
            selected_studies=[],
            selected_sample_sources=[],
            effect_direction=EffectDirectionFilter.ALL,
            selected_countries=[],
        ),
        provenance_statement="Merged exploratory output from curated GEO studies.",
        disclaimer="Exploratory research use only; not clinical or diagnostic.",
        allowed_export_kinds=[ExportKind.FILTERED_DEG_CSV, ExportKind.SELECTED_GENE_LIST_CSV],
    )


def test_gold_artifact_bundle_accepts_required_artifacts() -> None:
    bundle = GoldArtifactBundle(
        dashboard_summary=DashboardSummary(
            artifact_version="dashboard-summary-v1",
            dataset_version="long-covid-v1",
            generated_at=GENERATED_AT,
            provenance=_provenance(),
            included_study_count=1,
            included_sample_count=24,
            case_sample_count=12,
            control_sample_count=12,
            sample_source_counts={"blood": 24},
            study_sample_counts={"GSE000001": 24},
            country_counts={},
            country_metadata_status=CountryMetadataStatus.UNAVAILABLE,
        ),
        study_summary=[
            StudySummaryRecord(
                study_accession="GSE000001",
                study_title="Example Long COVID study",
                organism="Homo sapiens",
                platform="GPL000",
                included=True,
                inclusion_notes="Usable case/control metadata.",
                sample_count=24,
                case_sample_count=12,
                control_sample_count=12,
                sample_sources=["blood"],
                countries=[],
                metadata_quality_flags=["country_unavailable"],
            )
        ],
        merged_deg_table=[
            MergedDegRecord(
                gene_id="ENSG000001",
                gene_symbol="IFIT1",
                log2_fold_change=1.4,
                adjusted_p_value=0.01,
                p_value=0.001,
                effect_direction=EffectDirection.UPREGULATED,
                study_accessions=["GSE000001"],
                sample_source="blood",
                provenance_note="Merged exploratory result.",
            )
        ],
        volcano_points=[
            VolcanoPoint(
                gene_id="ENSG000001",
                gene_symbol="IFIT1",
                x_log2_fold_change=1.4,
                y_neg_log10_adjusted_p_value=2.0,
                adjusted_p_value=0.01,
                effect_direction=EffectDirection.UPREGULATED,
                study_accessions=["GSE000001"],
            )
        ],
        heatmap_matrix=HeatmapMatrix(
            gene_symbols=["IFIT1", "ISG15"],
            sample_or_group_labels=["Long COVID", "Control"],
            values=[[1.2, -0.4], [0.9, -0.2]],
            value_kind="z_score",
            study_accessions=["GSE000001"],
            top_n=2,
        ),
        filter_options=FilterOptions(
            studies=["GSE000001"],
            sample_sources=["blood"],
            effect_directions=[
                EffectDirectionFilter.ALL,
                EffectDirectionFilter.UPREGULATED,
                EffectDirectionFilter.DOWNREGULATED,
                EffectDirectionFilter.UNCHANGED,
            ],
            adjusted_p_value=FilterThresholdRange(default=0.05, minimum=0.0, maximum=1.0),
            log2_fold_change=FilterThresholdRange(default=1.0, minimum=0.0, maximum=10.0),
            countries=[],
            country_filter_enabled=False,
            country_filter_reason="Country metadata is unavailable for this curated snapshot.",
            country_metadata_status=CountryMetadataStatus.UNAVAILABLE,
        ),
        export_context=_export_context(),
    )

    assert bundle.dashboard_summary.included_study_count == 1
    assert bundle.merged_deg_table[0].effect_direction is EffectDirection.UPREGULATED


def test_deg_record_rejects_invalid_adjusted_p_value() -> None:
    with pytest.raises(ValidationError):
        MergedDegRecord(
            gene_id="ENSG000001",
            gene_symbol="IFIT1",
            log2_fold_change=1.4,
            adjusted_p_value=1.5,
            p_value=0.001,
            effect_direction=EffectDirection.UPREGULATED,
            study_accessions=["GSE000001"],
            sample_source="blood",
            provenance_note="Merged exploratory result.",
        )


def test_heatmap_matrix_requires_rectangular_values() -> None:
    with pytest.raises(ValidationError, match="rectangular"):
        HeatmapMatrix(
            gene_symbols=["IFIT1", "ISG15"],
            sample_or_group_labels=["Long COVID", "Control"],
            values=[[1.2, -0.4], [0.9]],
            value_kind="z_score",
            study_accessions=["GSE000001"],
            top_n=2,
        )


def test_country_filter_requires_reliable_metadata_and_options() -> None:
    with pytest.raises(ValidationError, match="reliable"):
        FilterOptions(
            studies=["GSE000001"],
            sample_sources=["blood"],
            effect_directions=[EffectDirectionFilter.ALL],
            adjusted_p_value=FilterThresholdRange(default=0.05, minimum=0.0, maximum=1.0),
            log2_fold_change=FilterThresholdRange(default=1.0, minimum=0.0, maximum=10.0),
            countries=["Japan"],
            country_filter_enabled=True,
            country_filter_reason="Country metadata is partial.",
            country_metadata_status=CountryMetadataStatus.PARTIAL,
        )
