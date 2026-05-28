"""Volcano plot view model and Streamlit rendering helpers."""

from dataclasses import dataclass

import plotly.graph_objects as go
import streamlit as st

from app.domain.contracts import VolcanoPoint
from app.domain.enums import EffectDirectionFilter
from app.ui.state import DashboardFilterState

UNSUPPORTED_FILTER_NOTE = (
    "Sample source and country filters are not represented in the volcano artifact."
)

DIRECTION_COLORS = {
    "upregulated": "#d62728",
    "downregulated": "#1f77b4",
    "unchanged": "#7f7f7f",
}


@dataclass(frozen=True)
class VolcanoPlotModel:
    result_count: int
    rows: list[dict[str, object]]
    unsupported_filter_note: str | None


def _passes_supported_filters(point: VolcanoPoint, state: DashboardFilterState) -> bool:
    selected_studies = set(state.selected_studies)

    return (
        point.adjusted_p_value <= state.adjusted_p_value
        and abs(point.x_log2_fold_change) >= state.log2_fold_change
        and (
            not selected_studies
            or bool(selected_studies.intersection(point.study_accessions))
        )
        and (
            state.effect_direction is EffectDirectionFilter.ALL
            or point.effect_direction.value == state.effect_direction.value
        )
    )


def _display_row(point: VolcanoPoint) -> dict[str, object]:
    studies = "; ".join(sorted(point.study_accessions))

    return {
        "Gene symbol": point.gene_symbol,
        "Gene ID": point.gene_id,
        "Log2 fold change": point.x_log2_fold_change,
        "-log10 adjusted p-value": point.y_neg_log10_adjusted_p_value,
        "Adjusted p-value": point.adjusted_p_value,
        "Direction": point.effect_direction.value,
        "Studies": studies,
        "Hover": f"{point.gene_symbol} ({point.gene_id})<br>Studies: {studies}",
    }


def build_volcano_plot_model(
    points: list[VolcanoPoint],
    state: DashboardFilterState | None = None,
) -> VolcanoPlotModel:
    unsupported_filter_note = None
    filtered_points = points

    if state is not None:
        filtered_points = [
            point for point in points if _passes_supported_filters(point, state)
        ]
        if state.selected_sample_sources or state.selected_countries:
            unsupported_filter_note = UNSUPPORTED_FILTER_NOTE

    rows = [_display_row(point) for point in filtered_points]
    return VolcanoPlotModel(
        result_count=len(rows),
        rows=rows,
        unsupported_filter_note=unsupported_filter_note,
    )


def build_volcano_figure(model: VolcanoPlotModel) -> go.Figure:
    marker_colors = [
        DIRECTION_COLORS.get(str(row["Direction"]), "#444444") for row in model.rows
    ]

    figure = go.Figure(
        data=[
            go.Scatter(
                x=[row["Log2 fold change"] for row in model.rows],
                y=[row["-log10 adjusted p-value"] for row in model.rows],
                hovertext=[row["Hover"] for row in model.rows],
                mode="markers",
                marker={"color": marker_colors},
            )
        ]
    )
    figure.update_layout(
        title="Volcano Plot",
        xaxis_title="Log2 fold change",
        yaxis_title="-log10 adjusted p-value",
    )
    return figure


def render_volcano_plot(
    points: list[VolcanoPoint],
    state: DashboardFilterState | None = None,
) -> None:
    model = build_volcano_plot_model(points, state)

    st.subheader("Volcano Plot")
    if model.unsupported_filter_note:
        st.caption(model.unsupported_filter_note)
    if not model.rows:
        st.info("No volcano points match the supported visualization filters.")
        return

    figure = build_volcano_figure(model)
    st.plotly_chart(figure, use_container_width=True, key="volcano_plot")
