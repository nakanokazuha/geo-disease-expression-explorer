"""Gold publication skeleton job."""

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from app.data_pipeline.jobs.run_bronze_ingestion import DEFAULT_STORAGE_ROOT
from app.data_pipeline.orchestration import (
    PipelineManifest,
    PipelineStage,
    PipelineStatus,
    PipelineStoragePaths,
)
from app.data_pipeline.silver import SilverStudyRecord
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

DATASET_VERSION = "long-covid-skeleton-v1"
PIPELINE_VERSION = "pipeline-skeleton-0.1.0"


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _count_values(records: list[SilverStudyRecord], field_name: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for record in records:
        counter.update(getattr(record, field_name))
    return dict(sorted(counter.items()))


def _study_sample_counts(records: list[SilverStudyRecord]) -> dict[str, int]:
    return {
        record.study_accession: record.sample_count
        for record in sorted(records, key=lambda item: item.study_accession)
    }


def _sample_source_counts(records: list[SilverStudyRecord]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for record in records:
        for sample_source in record.sample_sources:
            counter[sample_source] += record.sample_count
    return dict(sorted(counter.items()))


def _study_summary(records: list[SilverStudyRecord]) -> list[StudySummaryRecord]:
    return [
        StudySummaryRecord.model_validate(record.model_dump(mode="json"))
        for record in records
    ]


def _build_gold_bundle(
    silver_records: list[SilverStudyRecord],
    generated_at: datetime,
) -> GoldArtifactBundle:
    included_records = [record for record in silver_records if record.included]
    included_studies = sorted(record.study_accession for record in included_records)
    sample_sources = sorted(_count_values(included_records, "sample_sources"))

    provenance = ProvenanceContext(
        dataset_version=DATASET_VERSION,
        pipeline_version=PIPELINE_VERSION,
        generated_at=generated_at,
        source_system=SourceSystem.GEO,
        included_studies=included_studies,
        curation_notes=[
            "Gold skeleton generated from catalog-included metadata records in Silver."
        ],
        metadata_quality_notes=[
            "Dashboard sample source totals are metadata-catalog sample counts; "
            "metadata-only records may not have verified expression-ready case/control "
            "counts.",
            "Country metadata is unavailable for skeleton filtering.",
        ],
    )
    threshold_context = ThresholdContext(
        adjusted_p_value=0.05,
        log2_fold_change=1.0,
        selected_studies=[],
        selected_sample_sources=[],
        effect_direction=EffectDirectionFilter.ALL,
        selected_countries=[],
    )

    return GoldArtifactBundle(
        dashboard_summary=DashboardSummary(
            artifact_version="gold-artifact-bundle-skeleton-v1",
            dataset_version=DATASET_VERSION,
            generated_at=generated_at,
            provenance=provenance,
            included_study_count=len(included_records),
            included_sample_count=sum(record.sample_count for record in included_records),
            case_sample_count=sum(
                record.case_sample_count for record in included_records
            ),
            control_sample_count=sum(
                record.control_sample_count for record in included_records
            ),
            sample_source_counts=_sample_source_counts(included_records),
            study_sample_counts=_study_sample_counts(included_records),
            country_counts={},
            country_metadata_status=CountryMetadataStatus.UNAVAILABLE,
        ),
        study_summary=_study_summary(silver_records),
        merged_deg_table=[
            MergedDegRecord(
                gene_id="SKELETON_GENE_001",
                gene_symbol="SKELETON1",
                log2_fold_change=0.0,
                adjusted_p_value=1.0,
                p_value=1.0,
                effect_direction=EffectDirection.UNCHANGED,
                study_accessions=included_studies,
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
                study_accessions=included_studies,
            )
        ],
        heatmap_matrix=HeatmapMatrix(
            gene_symbols=["SKELETON1"],
            sample_or_group_labels=["Long COVID", "Control"],
            values=[[0.0, 0.0]],
            value_kind="skeleton_placeholder",
            study_accessions=included_studies,
            top_n=1,
        ),
        filter_options=FilterOptions(
            studies=included_studies,
            sample_sources=sample_sources,
            effect_directions=[
                EffectDirectionFilter.ALL,
                EffectDirectionFilter.UPREGULATED,
                EffectDirectionFilter.DOWNREGULATED,
                EffectDirectionFilter.UNCHANGED,
            ],
            adjusted_p_value=FilterThresholdRange(
                default=0.05,
                minimum=0.0,
                maximum=1.0,
            ),
            log2_fold_change=FilterThresholdRange(
                default=1.0,
                minimum=0.0,
                maximum=10.0,
            ),
            countries=[],
            country_filter_enabled=False,
            country_filter_reason="Country metadata is unavailable for this skeleton bundle.",
            country_metadata_status=CountryMetadataStatus.UNAVAILABLE,
        ),
        export_context=ExportContext(
            dataset_version=DATASET_VERSION,
            pipeline_version=PIPELINE_VERSION,
            generated_at=generated_at,
            included_studies=included_studies,
            threshold_context=threshold_context,
            provenance_statement=(
                "curated metadata skeleton bundle generated from public study metadata "
                "catalog records."
            ),
            disclaimer=(
                "Skeleton artifact for pipeline validation only; catalog-included "
                "metadata records are not expression-ready real DEG findings and are "
                "not clinical or diagnostic."
            ),
            allowed_export_kinds=[
                ExportKind.FILTERED_DEG_CSV,
                ExportKind.SELECTED_GENE_LIST_CSV,
            ],
        ),
    )


def run_gold_publication(
    storage_root: Path = DEFAULT_STORAGE_ROOT,
) -> PipelineManifest:
    started_at = datetime.now(UTC)
    paths = PipelineStoragePaths(root=storage_root)
    paths.ensure_directories()

    silver_payload = json.loads(paths.silver_studies.read_text(encoding="utf-8"))
    silver_records = [
        SilverStudyRecord.model_validate(record) for record in silver_payload
    ]
    bundle = _build_gold_bundle(silver_records, generated_at=started_at)

    _write_json(paths.gold_bundle, bundle.model_dump(mode="json"))

    finished_at = datetime.now(UTC)
    manifest = PipelineManifest(
        stage=PipelineStage.GOLD_PUBLICATION,
        status=PipelineStatus.SUCCESS,
        started_at=started_at,
        finished_at=finished_at,
        input_paths=[paths.silver_studies],
        output_paths=[paths.gold_bundle],
        record_count=1,
        notes=[
            "Gold skeleton wrote a contract-valid curated metadata publication bundle."
        ],
    )
    _write_json(
        paths.manifest_path(PipelineStage.GOLD_PUBLICATION),
        manifest.model_dump(mode="json"),
    )
    return manifest


if __name__ == "__main__":
    run_gold_publication()
