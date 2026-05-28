import inspect

from app.domain.contracts import VolcanoPoint
from app.domain.enums import EffectDirection, EffectDirectionFilter
from app.ui.state import DashboardFilterState
from app.ui.views.volcano_plot import (
    build_volcano_figure,
    build_volcano_plot_model,
    render_volcano_plot,
)


def _point(
    gene_symbol: str,
    *,
    gene_id: str | None = None,
    x_log2_fold_change: float = 1.23456,
    y_neg_log10_adjusted_p_value: float = 2.5,
    adjusted_p_value: float = 0.003,
    effect_direction: EffectDirection = EffectDirection.UPREGULATED,
    study_accessions: list[str] | None = None,
) -> VolcanoPoint:
    return VolcanoPoint(
        gene_id=gene_id or f"{gene_symbol}_ID",
        gene_symbol=gene_symbol,
        x_log2_fold_change=x_log2_fold_change,
        y_neg_log10_adjusted_p_value=y_neg_log10_adjusted_p_value,
        adjusted_p_value=adjusted_p_value,
        effect_direction=effect_direction,
        study_accessions=study_accessions or ["GSE200002", "GSE100001"],
    )


def _filter_state(
    *,
    adjusted_p_value: float = 0.05,
    log2_fold_change: float = 1.0,
    selected_studies: list[str] | None = None,
    selected_sample_sources: list[str] | None = None,
    effect_direction: EffectDirectionFilter = EffectDirectionFilter.ALL,
    selected_countries: list[str] | None = None,
) -> DashboardFilterState:
    return DashboardFilterState(
        adjusted_p_value=adjusted_p_value,
        log2_fold_change=log2_fold_change,
        selected_studies=selected_studies or [],
        selected_sample_sources=selected_sample_sources or [],
        effect_direction=effect_direction,
        selected_countries=selected_countries or [],
        country_filter_available=False,
        country_filter_note="Country filtering is unavailable.",
    )


def test_volcano_plot_model_builds_stable_display_rows() -> None:
    model = build_volcano_plot_model(
        [
            _point(
                "IFITM3",
                gene_id="ENSG000001",
                x_log2_fold_change=1.23456,
                y_neg_log10_adjusted_p_value=4.321,
                adjusted_p_value=0.0000477,
                effect_direction=EffectDirection.UPREGULATED,
                study_accessions=["GSE200002", "GSE100001"],
            )
        ]
    )

    assert model.result_count == 1
    assert model.unsupported_filter_note is None
    assert model.rows == [
        {
            "Gene symbol": "IFITM3",
            "Gene ID": "ENSG000001",
            "Log2 fold change": 1.23456,
            "-log10 adjusted p-value": 4.321,
            "Adjusted p-value": 0.0000477,
            "Direction": "upregulated",
            "Studies": "GSE100001; GSE200002",
            "Hover": "IFITM3 (ENSG000001)<br>Studies: GSE100001; GSE200002",
        }
    ]


def test_volcano_plot_model_applies_supported_filters() -> None:
    points = [
        _point(
            "KEPT",
            adjusted_p_value=0.01,
            x_log2_fold_change=-1.5,
            effect_direction=EffectDirection.DOWNREGULATED,
            study_accessions=["GSE000001", "GSE000003"],
        ),
        _point(
            "HIGH_P",
            adjusted_p_value=0.06,
            x_log2_fold_change=-1.5,
            effect_direction=EffectDirection.DOWNREGULATED,
            study_accessions=["GSE000003"],
        ),
        _point(
            "LOW_EFFECT",
            adjusted_p_value=0.01,
            x_log2_fold_change=-0.9,
            effect_direction=EffectDirection.DOWNREGULATED,
            study_accessions=["GSE000003"],
        ),
        _point(
            "WRONG_STUDY",
            adjusted_p_value=0.01,
            x_log2_fold_change=-1.5,
            effect_direction=EffectDirection.DOWNREGULATED,
            study_accessions=["GSE999999"],
        ),
        _point(
            "WRONG_DIRECTION",
            adjusted_p_value=0.01,
            x_log2_fold_change=1.5,
            effect_direction=EffectDirection.UPREGULATED,
            study_accessions=["GSE000003"],
        ),
    ]

    model = build_volcano_plot_model(
        points,
        _filter_state(
            selected_studies=["GSE000003"],
            effect_direction=EffectDirectionFilter.DOWNREGULATED,
        ),
    )

    assert [row["Gene symbol"] for row in model.rows] == ["KEPT"]


def test_sample_source_selection_adds_note_without_filtering_points() -> None:
    model = build_volcano_plot_model(
        [_point("IFITM3"), _point("CXCL10")],
        _filter_state(selected_sample_sources=["PBMC"], selected_countries=["Japan"]),
    )

    assert model.result_count == 2
    assert [row["Gene symbol"] for row in model.rows] == ["IFITM3", "CXCL10"]
    assert model.unsupported_filter_note is not None
    assert "not represented in the volcano artifact" in model.unsupported_filter_note


def test_empty_supported_filter_results_return_empty_model() -> None:
    model = build_volcano_plot_model(
        [_point("IFITM3", adjusted_p_value=0.2, x_log2_fold_change=0.2)],
        _filter_state(),
    )

    assert model.result_count == 0
    assert model.rows == []


def test_volcano_figure_uses_stable_title_axes_and_marker_hovertext() -> None:
    model = build_volcano_plot_model([_point("IFITM3")])

    figure = build_volcano_figure(model)

    assert figure.layout.title.text == "Volcano Plot"
    assert figure.layout.xaxis.title.text == "Log2 fold change"
    assert figure.layout.yaxis.title.text == "-log10 adjusted p-value"
    assert list(figure.data[0].x) == [1.23456]
    assert list(figure.data[0].y) == [2.5]
    assert list(figure.data[0].hovertext) == [
        "IFITM3 (IFITM3_ID)<br>Studies: GSE100001; GSE200002"
    ]
    assert figure.data[0].mode == "markers"


def test_render_volcano_plot_uses_stable_streamlit_key() -> None:
    source = inspect.getsource(render_volcano_plot)

    assert 'st.subheader("Volcano Plot")' in source
    assert 'key="volcano_plot"' in source
