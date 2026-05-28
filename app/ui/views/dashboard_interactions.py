"""Dashboard filter controls, DEG table, and export interactions."""

from dataclasses import dataclass
from datetime import UTC, datetime

import streamlit as st

from app.domain.contracts import FilterOptions, GoldArtifactBundle, MergedDegRecord
from app.domain.enums import EffectDirectionFilter, ExportKind
from app.ui.exports import build_filtered_deg_csv_export
from app.ui.state import (
    DashboardFilterState,
    apply_dashboard_filters,
    build_default_filter_state,
)
from app.ui.views.deg_table import render_deg_table
from app.ui.views.heatmap_view import render_heatmap_view
from app.ui.views.volcano_plot import render_volcano_plot

COUNTRY_FILTER_DISABLED_NOTICE = (
    "Country metadata is available, but country filtering is not supported "
    "for DEG records in this milestone."
)


@dataclass(frozen=True)
class DashboardInteractionModel:
    filter_state: DashboardFilterState
    filtered_records: list[MergedDegRecord]
    filtered_result_count: int
    filtered_deg_export_allowed: bool
    country_filter_notice: str
    export_disclaimer: str


def build_country_filter_notice(filter_options: FilterOptions) -> str:
    """Build the explanatory country-filter notice for DEG interactions."""

    if not filter_options.country_filter_enabled:
        return filter_options.country_filter_reason
    return COUNTRY_FILTER_DISABLED_NOTICE


def build_dashboard_interaction_model(
    bundle: GoldArtifactBundle,
    state: DashboardFilterState | None = None,
) -> DashboardInteractionModel:
    """Apply dashboard filters and expose interaction/export state."""

    filter_state = state
    if filter_state is None:
        filter_state = build_default_filter_state(bundle.filter_options)

    filtered_records = apply_dashboard_filters(bundle.merged_deg_table, filter_state)
    export_allowed = (
        ExportKind.FILTERED_DEG_CSV in bundle.export_context.allowed_export_kinds
    )

    return DashboardInteractionModel(
        filter_state=filter_state,
        filtered_records=filtered_records,
        filtered_result_count=len(filtered_records),
        filtered_deg_export_allowed=export_allowed,
        country_filter_notice=build_country_filter_notice(bundle.filter_options),
        export_disclaimer=bundle.export_context.disclaimer,
    )


def _render_sidebar_filters(filter_options: FilterOptions) -> DashboardFilterState:
    st.sidebar.header("Filters")

    adjusted_p_value = st.sidebar.slider(
        "Adjusted p-value",
        min_value=float(filter_options.adjusted_p_value.minimum),
        max_value=float(filter_options.adjusted_p_value.maximum),
        value=float(filter_options.adjusted_p_value.default),
        step=0.001,
    )
    log2_fold_change = st.sidebar.slider(
        "Absolute log2 fold-change",
        min_value=float(filter_options.log2_fold_change.minimum),
        max_value=float(filter_options.log2_fold_change.maximum),
        value=float(filter_options.log2_fold_change.default),
        step=0.1,
    )
    selected_studies = st.sidebar.multiselect(
        "Studies",
        options=filter_options.studies,
        default=[],
    )
    selected_sample_sources = st.sidebar.multiselect(
        "Sample sources",
        options=filter_options.sample_sources,
        default=[],
    )
    effect_direction = st.sidebar.selectbox(
        "Effect direction",
        options=filter_options.effect_directions,
        index=_default_effect_direction_index(filter_options.effect_directions),
        format_func=lambda option: option.value.replace("_", " ").title(),
    )

    country_filter_note = build_country_filter_notice(filter_options)
    st.sidebar.caption(country_filter_note)

    return DashboardFilterState(
        adjusted_p_value=adjusted_p_value,
        log2_fold_change=log2_fold_change,
        selected_studies=list(selected_studies),
        selected_sample_sources=list(selected_sample_sources),
        effect_direction=effect_direction,
        selected_countries=[],
        country_filter_available=False,
        country_filter_note=country_filter_note,
    )


def _render_filtered_deg_export_control(
    bundle: GoldArtifactBundle,
    model: DashboardInteractionModel,
) -> None:
    st.subheader("Export")
    st.caption(model.export_disclaimer)

    if not model.filtered_deg_export_allowed:
        st.info("The current Gold bundle does not permit filtered DEG CSV export.")
        return

    payload = build_filtered_deg_csv_export(
        records=model.filtered_records,
        export_context=bundle.export_context,
        state=model.filter_state,
        exported_at=datetime.now(UTC),
    )
    st.download_button(
        "Download filtered DEG CSV",
        data=payload.csv_text,
        file_name=payload.filename,
        mime=payload.mime_type,
        key="filtered_deg_csv_download",
        on_click="ignore",
    )


def _render_visualizations(
    bundle: GoldArtifactBundle,
    state: DashboardFilterState,
) -> None:
    st.subheader("Visualizations")
    render_volcano_plot(bundle.volcano_points, state)
    render_heatmap_view(bundle.heatmap_matrix)


def render_dashboard_interactions(bundle: GoldArtifactBundle) -> None:
    """Render sidebar filters, filtered DEG table, and filtered CSV export."""

    state = _render_sidebar_filters(bundle.filter_options)
    model = build_dashboard_interaction_model(bundle, state)

    _render_visualizations(bundle, state)
    render_deg_table(model.filtered_records)
    _render_filtered_deg_export_control(bundle, model)


def _default_effect_direction_index(
    effect_directions: list[EffectDirectionFilter],
) -> int:
    try:
        return effect_directions.index(EffectDirectionFilter.ALL)
    except ValueError:
        return 0
