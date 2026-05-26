from datetime import UTC, datetime

import pytest

from app.domain.contracts import (
    DashboardSummary,
    ExportContext,
    FilterOptions,
    FilterThresholdRange,
    GoldArtifactBundle,
    HeatmapMatrix,
    MergedDegRecord,
    ProvenanceContext,
    StudySummaryRecord,
    ThresholdContext,
    VolcanoPoint,
)
from app.domain.enums import (
    CountryMetadataStatus,
    EffectDirection,
    EffectDirectionFilter,
    ExportKind,
    SourceSystem,
)
from app.ui.views.dashboard_overview import build_dashboard_overview_model

GENERATED_AT = datetime(2026, 5, 26, tzinfo=UTC)


def _bundle() -> GoldArtifactBundle:
    provenance = ProvenanceContext(
        dataset_version="long-covid-skeleton-v1",
        pipeline_version="pipeline-skeleton-0.1.0",
        generated_at=GENERATED_AT,
        source_system=SourceSystem.GEO,
        included_studies=["GSE000001", "GSE000002"],
        curation_notes=["Skeleton bundle."],
        metadata_quality_notes=["Country metadata unavailable."],
    )
    return GoldArtifactBundle(
        dashboard_summary=DashboardSummary(
            artifact_version="dashboard-shell-test-v1",
            dataset_version="long-covid-skeleton-v1",
            generated_at=GENERATED_AT,
            provenance=provenance,
            included_study_count=2,
            included_sample_count=54,
            case_sample_count=27,
            control_sample_count=27,
            sample_source_counts={"PBMC": 30, "blood": 24},
            study_sample_counts={"GSE000001": 24, "GSE000002": 30},
            country_counts={},
            country_metadata_status=CountryMetadataStatus.UNAVAILABLE,
        ),
        study_summary=[
            StudySummaryRecord(
                study_accession="GSE000001",
                study_title="Skeleton Long COVID blood study",
                organism="Homo sapiens",
                platform="GPL000",
                included=True,
                inclusion_notes="Skeleton inclusion gate passed.",
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
                gene_id="SKELETON_GENE_001",
                gene_symbol="SKELETON1",
                log2_fold_change=0.0,
                adjusted_p_value=1.0,
                p_value=1.0,
                effect_direction=EffectDirection.UNCHANGED,
                study_accessions=["GSE000001", "GSE000002"],
                sample_source="skeleton",
                provenance_note="Skeleton placeholder; no differential expression claim.",
            )
        ],
        volcano_points=[
            VolcanoPoint(
                gene_id="SKELETON_GENE_001",
                gene_symbol="SKELETON1",
                x_log2_fold_change=0.0,
                y_neg_log10_adjusted_p_value=0.0,
                adjusted_p_value=1.0,
                effect_direction=EffectDirection.UNCHANGED,
                study_accessions=["GSE000001", "GSE000002"],
            )
        ],
        heatmap_matrix=HeatmapMatrix(
            gene_symbols=["SKELETON1"],
            sample_or_group_labels=["Long COVID", "Control"],
            values=[[0.0, 0.0]],
            value_kind="skeleton_placeholder",
            study_accessions=["GSE000001", "GSE000002"],
            top_n=1,
        ),
        filter_options=FilterOptions(
            studies=["GSE000001", "GSE000002"],
            sample_sources=["PBMC", "blood"],
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
            country_filter_reason="Country metadata is unavailable.",
            country_metadata_status=CountryMetadataStatus.UNAVAILABLE,
        ),
        export_context=ExportContext(
            dataset_version="long-covid-skeleton-v1",
            pipeline_version="pipeline-skeleton-0.1.0",
            generated_at=GENERATED_AT,
            included_studies=["GSE000001", "GSE000002"],
            threshold_context=ThresholdContext(
                adjusted_p_value=0.05,
                log2_fold_change=1.0,
                selected_studies=[],
                selected_sample_sources=[],
                effect_direction=EffectDirectionFilter.ALL,
                selected_countries=[],
            ),
            provenance_statement="Skeleton export context.",
            disclaimer="Skeleton artifact for pipeline validation only.",
            allowed_export_kinds=[
                ExportKind.FILTERED_DEG_CSV,
                ExportKind.SELECTED_GENE_LIST_CSV,
            ],
        ),
    )


@pytest.fixture
def gold_bundle() -> GoldArtifactBundle:
    return _bundle()


def test_dashboard_overview_model_contains_summary_metrics(
    gold_bundle: GoldArtifactBundle,
) -> None:
    model = build_dashboard_overview_model(gold_bundle)

    assert model.metrics == [
        ("Included studies", "2"),
        ("Total samples", "54"),
        ("Long COVID samples", "27"),
        ("Control samples", "27"),
    ]
    assert model.sample_source_rows == [("blood", 24), ("PBMC", 30)]
    assert model.study_rows == [("GSE000001", 24), ("GSE000002", 30)]


def test_dashboard_overview_model_disables_country_coverage_when_unavailable(
    gold_bundle: GoldArtifactBundle,
) -> None:
    model = build_dashboard_overview_model(gold_bundle)

    assert model.country_coverage_enabled is False
    assert model.country_note == "Country metadata is unavailable for skeleton filtering."
    assert "pipeline validation" in model.skeleton_notice
