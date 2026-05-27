"""Provenance-aware CSV export for filtered DEG records."""

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from io import StringIO

from app.domain.contracts import ExportContext, MergedDegRecord
from app.domain.enums import ExportKind
from app.ui.state import DashboardFilterState, build_threshold_context


class ExportNotAllowedError(ValueError):
    """Raised when a requested export kind is not allowed by the artifact."""


@dataclass(frozen=True)
class FilteredDegCsvPayload:
    filename: str
    mime_type: str
    csv_text: str


def build_filtered_deg_csv_export(
    records: list[MergedDegRecord],
    export_context: ExportContext,
    state: DashboardFilterState,
    exported_at: datetime,
) -> FilteredDegCsvPayload:
    """Build a CSV payload for currently filtered DEG records."""

    if ExportKind.FILTERED_DEG_CSV not in export_context.allowed_export_kinds:
        raise ExportNotAllowedError("filtered DEG CSV export is not allowed")

    exported_at_utc = _normalize_aware_utc(exported_at)
    timestamp_for_filename = exported_at_utc.strftime("%Y%m%dT%H%M%SZ")
    filename = f"long-covid-filtered-deg-{timestamp_for_filename}.csv"

    return FilteredDegCsvPayload(
        filename=filename,
        mime_type="text/csv",
        csv_text=_build_csv_text(records, export_context, state, exported_at_utc),
    )


def _build_csv_text(
    records: list[MergedDegRecord],
    export_context: ExportContext,
    state: DashboardFilterState,
    exported_at_utc: datetime,
) -> str:
    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")

    threshold_context = build_threshold_context(state)
    generated_at_utc = _normalize_aware_utc(export_context.generated_at)
    writer.writerows(
        [
            ["export kind", ExportKind.FILTERED_DEG_CSV.value],
            ["exported timestamp", _format_utc_timestamp(exported_at_utc)],
            ["dataset version", export_context.dataset_version],
            ["pipeline version", export_context.pipeline_version],
            [
                "Gold generated timestamp",
                _format_utc_timestamp(generated_at_utc),
            ],
            ["included studies", _join_metadata_list(export_context.included_studies)],
            [
                "adjusted p-value threshold",
                str(threshold_context.adjusted_p_value),
            ],
            [
                "log2 fold-change threshold",
                str(threshold_context.log2_fold_change),
            ],
            ["selected studies", _join_metadata_list(threshold_context.selected_studies)],
            [
                "selected sample sources",
                _join_metadata_list(threshold_context.selected_sample_sources),
            ],
            ["selected effect direction", threshold_context.effect_direction.value],
            ["selected countries", _join_metadata_list(threshold_context.selected_countries)],
            ["provenance statement", export_context.provenance_statement],
            ["disclaimer", export_context.disclaimer],
            [],
        ]
    )

    writer.writerow(
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
        ]
    )
    for record in records:
        writer.writerow(_record_to_csv_row(record))

    return output.getvalue()


def _normalize_aware_utc(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("exported_at must be timezone-aware")
    return timestamp.astimezone(UTC)


def _format_utc_timestamp(timestamp: datetime) -> str:
    return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _join_metadata_list(values: list[str]) -> str:
    return "; ".join(values)


def _record_to_csv_row(record: MergedDegRecord) -> list[object]:
    return [
        record.gene_symbol,
        record.gene_id,
        record.log2_fold_change,
        record.adjusted_p_value,
        record.p_value,
        record.effect_direction.value,
        record.sample_source,
        "; ".join(sorted(record.study_accessions)),
        record.provenance_note,
    ]
