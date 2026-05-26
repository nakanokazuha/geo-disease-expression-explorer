"""Dashboard overview view model and Streamlit rendering helpers."""

from dataclasses import dataclass

import streamlit as st

from app.domain.contracts import GoldArtifactBundle
from app.domain.enums import CountryMetadataStatus

SKELETON_COUNTRY_NOTE = "Country metadata is unavailable for skeleton filtering."
SKELETON_NOTICE = (
    "Current Gold values are skeleton artifacts for pipeline validation; "
    "they are not biological findings."
)


@dataclass(frozen=True)
class DashboardOverviewModel:
    dataset_version: str
    pipeline_version: str
    metrics: list[tuple[str, str]]
    sample_source_rows: list[tuple[str, int]]
    study_rows: list[tuple[str, int]]
    country_coverage_enabled: bool
    country_note: str
    skeleton_notice: str


def _sorted_count_rows(counts: dict[str, int]) -> list[tuple[str, int]]:
    return sorted(counts.items(), key=lambda item: item[0].lower())


def build_dashboard_overview_model(bundle: GoldArtifactBundle) -> DashboardOverviewModel:
    summary = bundle.dashboard_summary
    country_coverage_enabled = (
        summary.country_metadata_status is CountryMetadataStatus.RELIABLE
        and bool(summary.country_counts)
        and bundle.filter_options.country_filter_enabled
    )
    country_note = (
        f"Country coverage available for {len(summary.country_counts)} countries."
        if country_coverage_enabled
        else SKELETON_COUNTRY_NOTE
    )

    return DashboardOverviewModel(
        dataset_version=summary.dataset_version,
        pipeline_version=summary.provenance.pipeline_version,
        metrics=[
            ("Included studies", str(summary.included_study_count)),
            ("Total samples", str(summary.included_sample_count)),
            ("Long COVID samples", str(summary.case_sample_count)),
            ("Control samples", str(summary.control_sample_count)),
        ],
        sample_source_rows=_sorted_count_rows(summary.sample_source_counts),
        study_rows=_sorted_count_rows(summary.study_sample_counts),
        country_coverage_enabled=country_coverage_enabled,
        country_note=country_note,
        skeleton_notice=SKELETON_NOTICE,
    )


def render_dashboard_overview(bundle: GoldArtifactBundle) -> None:
    model = build_dashboard_overview_model(bundle)

    st.title("Long COVID GEO Expression Explorer")
    st.caption("Study-aware public GEO expression explorer.")

    metric_columns = st.columns(len(model.metrics))
    for column, (label, value) in zip(metric_columns, model.metrics, strict=True):
        column.metric(label, value)

    st.subheader("Study And Sample Coverage")
    st.write(f"Dataset version: {model.dataset_version}")
    st.write(f"Pipeline version: {model.pipeline_version}")
    st.header("Sample Sources")
    st.dataframe(
        [
            {"Sample source": source, "Samples": count}
            for source, count in model.sample_source_rows
        ],
        hide_index=True,
        use_container_width=True,
    )
    st.header("Included Studies")
    st.dataframe(
        [{"Study": study, "Samples": count} for study, count in model.study_rows],
        hide_index=True,
        use_container_width=True,
    )
    st.info(model.country_note)
    st.warning(model.skeleton_notice)
