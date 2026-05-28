"""Heatmap view model and Streamlit rendering helpers."""

from dataclasses import dataclass

import plotly.graph_objects as go
import streamlit as st

from app.domain.contracts import HeatmapMatrix

CONTEXT_NOTE = (
    "Heatmap shows the published Gold matrix and is not dynamically filtered in "
    "this milestone."
)


@dataclass(frozen=True)
class HeatmapViewModel:
    gene_symbols: list[str]
    sample_or_group_labels: list[str]
    values: list[list[float]]
    value_kind: str
    top_n: int
    study_accessions: list[str]
    context_note: str


def build_heatmap_view_model(matrix: HeatmapMatrix) -> HeatmapViewModel:
    return HeatmapViewModel(
        gene_symbols=list(matrix.gene_symbols),
        sample_or_group_labels=list(matrix.sample_or_group_labels),
        values=[list(row) for row in matrix.values],
        value_kind=matrix.value_kind,
        top_n=matrix.top_n,
        study_accessions=sorted(matrix.study_accessions),
        context_note=CONTEXT_NOTE,
    )


def build_heatmap_figure(model: HeatmapViewModel) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Heatmap(
                x=model.sample_or_group_labels,
                y=model.gene_symbols,
                z=model.values,
            )
        ]
    )
    figure.update_layout(
        title="Expression Heatmap",
        xaxis_title="Sample or group",
        yaxis_title="Gene symbol",
        yaxis={"autorange": "reversed"},
    )
    return figure


def render_heatmap_view(matrix: HeatmapMatrix) -> None:
    model = build_heatmap_view_model(matrix)
    studies = "; ".join(model.study_accessions)

    st.subheader("Expression Heatmap")
    st.caption(model.context_note)
    st.caption(
        f"Value kind: {model.value_kind}; top N: {model.top_n}; studies: {studies}"
    )
    figure = build_heatmap_figure(model)
    st.plotly_chart(figure, use_container_width=True, key="expression_heatmap")
