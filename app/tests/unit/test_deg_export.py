import csv
from datetime import UTC, datetime, timedelta, timezone
from io import StringIO

import pytest

from app.domain.contracts import ExportContext, MergedDegRecord, ThresholdContext
from app.domain.enums import EffectDirection, EffectDirectionFilter, ExportKind
from app.ui.exports import (
    ExportNotAllowedError,
    build_filtered_deg_csv_export,
)
from app.ui.state import DashboardFilterState


def _export_context(
    *,
    allowed_export_kinds: list[ExportKind] | None = None,
    generated_at: datetime | None = None,
) -> ExportContext:
    return ExportContext(
        dataset_version="dataset-v1",
        pipeline_version="pipeline-v2",
        generated_at=generated_at
        if generated_at is not None
        else datetime(2026, 5, 20, 8, 30, 0, tzinfo=UTC),
        included_studies=["GSE100001", "GSE200002"],
        threshold_context=ThresholdContext(
            adjusted_p_value=0.05,
            log2_fold_change=1.0,
            selected_studies=[],
            selected_sample_sources=[],
            effect_direction=EffectDirectionFilter.ALL,
            selected_countries=[],
        ),
        provenance_statement="Public GEO studies curated into Gold artifacts.",
        disclaimer="For exploratory research use only.",
        allowed_export_kinds=allowed_export_kinds
        if allowed_export_kinds is not None
        else [ExportKind.FILTERED_DEG_CSV],
    )


def _filter_state() -> DashboardFilterState:
    return DashboardFilterState(
        adjusted_p_value=0.01,
        log2_fold_change=1.5,
        selected_studies=["GSE200002", "GSE100001"],
        selected_sample_sources=["PBMC", "Whole blood"],
        effect_direction=EffectDirectionFilter.UPREGULATED,
        selected_countries=["Japan"],
        country_filter_available=False,
        country_filter_note="Country filtering is unavailable for DEG records.",
    )


def _deg_record(
    *,
    gene_id: str = "ENSG000001",
    gene_symbol: str = "IFITM3",
    log2_fold_change: float = 1.23456,
    adjusted_p_value: float = 0.005,
    p_value: float = 0.0004,
    effect_direction: EffectDirection = EffectDirection.UPREGULATED,
    study_accessions: list[str] | None = None,
    sample_source: str = "PBMC",
    provenance_note: str = "Merged from public GEO studies.",
) -> MergedDegRecord:
    return MergedDegRecord(
        gene_id=gene_id,
        gene_symbol=gene_symbol,
        log2_fold_change=log2_fold_change,
        adjusted_p_value=adjusted_p_value,
        p_value=p_value,
        effect_direction=effect_direction,
        study_accessions=study_accessions or ["GSE200002", "GSE100001"],
        sample_source=sample_source,
        provenance_note=provenance_note,
    )


def _csv_rows(csv_text: str) -> list[list[str]]:
    return list(csv.reader(StringIO(csv_text)))


def test_allowed_filtered_deg_export_returns_timestamped_csv_payload() -> None:
    payload = build_filtered_deg_csv_export(
        records=[],
        export_context=_export_context(),
        state=_filter_state(),
        exported_at=datetime(2026, 5, 27, 3, 4, 5, tzinfo=UTC),
    )

    assert payload.filename == "long-covid-filtered-deg-20260527T030405Z.csv"
    assert payload.mime_type == "text/csv"


def test_csv_includes_metadata_context_and_filtered_deg_rows() -> None:
    records = [
        _deg_record(),
        _deg_record(
            gene_id="ENSG000002",
            gene_symbol="OAS1",
            log2_fold_change=-2.0,
            adjusted_p_value=0.007,
            p_value=0.0008,
            effect_direction=EffectDirection.DOWNREGULATED,
            study_accessions=["GSE300003"],
            sample_source="Whole blood",
            provenance_note="Single-study public GEO signal.",
        ),
    ]

    payload = build_filtered_deg_csv_export(
        records=records,
        export_context=_export_context(),
        state=_filter_state(),
        exported_at=datetime(2026, 5, 27, 3, 4, 5, tzinfo=UTC),
    )

    assert _csv_rows(payload.csv_text) == [
        ["export kind", "filtered_deg_csv"],
        ["exported timestamp", "2026-05-27T03:04:05Z"],
        ["dataset version", "dataset-v1"],
        ["pipeline version", "pipeline-v2"],
        ["Gold generated timestamp", "2026-05-20T08:30:00Z"],
        ["included studies", "GSE100001; GSE200002"],
        ["adjusted p-value threshold", "0.01"],
        ["log2 fold-change threshold", "1.5"],
        ["selected studies", "GSE200002; GSE100001"],
        ["selected sample sources", "PBMC; Whole blood"],
        ["selected effect direction", "upregulated"],
        ["selected countries", ""],
        ["provenance statement", "Public GEO studies curated into Gold artifacts."],
        ["disclaimer", "For exploratory research use only."],
        [],
        [
            "Gene symbol",
            "Gene ID",
            "Log2 fold change",
            "Adjusted p-value",
            "P-value",
            "Direction",
            "Sample source",
            "Studies",
            "Provenance note",
        ],
        [
            "IFITM3",
            "ENSG000001",
            "1.23456",
            "0.005",
            "0.0004",
            "upregulated",
            "PBMC",
            "GSE100001; GSE200002",
            "Merged from public GEO studies.",
        ],
        [
            "OAS1",
            "ENSG000002",
            "-2.0",
            "0.007",
            "0.0008",
            "downregulated",
            "Whole blood",
            "GSE300003",
            "Single-study public GEO signal.",
        ],
    ]


def test_timezone_aware_export_timestamp_is_normalized_to_utc() -> None:
    exported_at = datetime(
        2026,
        5,
        27,
        12,
        4,
        5,
        tzinfo=timezone(timedelta(hours=9)),
    )

    payload = build_filtered_deg_csv_export(
        records=[],
        export_context=_export_context(),
        state=_filter_state(),
        exported_at=exported_at,
    )

    assert payload.filename == "long-covid-filtered-deg-20260527T030405Z.csv"
    assert _csv_rows(payload.csv_text)[1] == [
        "exported timestamp",
        "2026-05-27T03:04:05Z",
    ]


def test_naive_export_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        build_filtered_deg_csv_export(
            records=[],
            export_context=_export_context(),
            state=_filter_state(),
            exported_at=datetime(2026, 5, 27, 3, 4, 5),
        )


def test_naive_gold_generated_timestamp_raises_value_error() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        build_filtered_deg_csv_export(
            records=[],
            export_context=_export_context(
                generated_at=datetime(2026, 5, 20, 8, 30, 0),
            ),
            state=_filter_state(),
            exported_at=datetime(2026, 5, 27, 3, 4, 5, tzinfo=UTC),
        )


def test_export_not_allowed_when_filtered_deg_csv_is_absent() -> None:
    with pytest.raises(ExportNotAllowedError):
        build_filtered_deg_csv_export(
            records=[],
            export_context=_export_context(
                allowed_export_kinds=[ExportKind.SELECTED_GENE_LIST_CSV],
            ),
            state=_filter_state(),
            exported_at=datetime(2026, 5, 27, 3, 4, 5, tzinfo=UTC),
        )
