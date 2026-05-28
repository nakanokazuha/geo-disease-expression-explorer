import inspect

from app.domain.contracts import HeatmapMatrix
from app.ui.views.heatmap_view import (
    build_heatmap_figure,
    build_heatmap_view_model,
    render_heatmap_view,
)

CONTEXT_NOTE = (
    "Heatmap shows the published Gold matrix and is not dynamically filtered in "
    "this milestone."
)


def _matrix() -> HeatmapMatrix:
    return HeatmapMatrix(
        gene_symbols=["CXCL10", "IFITM3", "OAS1"],
        sample_or_group_labels=["Control", "Case", "Recovery"],
        values=[
            [0.1, 1.2, 0.4],
            [-0.3, 2.4, 0.8],
            [1.1, -1.4, 0.0],
        ],
        value_kind="z_score",
        study_accessions=["GSE200002", "GSE100001"],
        top_n=25,
    )


def test_heatmap_model_preserves_matrix_order_and_values() -> None:
    matrix = _matrix()

    model = build_heatmap_view_model(matrix)

    assert model.gene_symbols == ["CXCL10", "IFITM3", "OAS1"]
    assert model.sample_or_group_labels == ["Control", "Case", "Recovery"]
    assert model.values == [
        [0.1, 1.2, 0.4],
        [-0.3, 2.4, 0.8],
        [1.1, -1.4, 0.0],
    ]


def test_heatmap_model_exposes_metadata_and_stable_context_note() -> None:
    model = build_heatmap_view_model(_matrix())

    assert model.value_kind == "z_score"
    assert model.top_n == 25
    assert model.study_accessions == ["GSE100001", "GSE200002"]
    assert model.context_note == CONTEXT_NOTE


def test_heatmap_model_copies_mutable_matrix_lists() -> None:
    matrix = _matrix()

    model = build_heatmap_view_model(matrix)
    matrix.gene_symbols[0] = "MUTATED_GENE"
    matrix.sample_or_group_labels[0] = "Mutated sample"
    matrix.values[0][0] = 99.9

    assert model.gene_symbols == ["CXCL10", "IFITM3", "OAS1"]
    assert model.sample_or_group_labels == ["Control", "Case", "Recovery"]
    assert model.values[0][0] == 0.1


def test_heatmap_figure_uses_model_data_and_stable_layout() -> None:
    model = build_heatmap_view_model(_matrix())

    figure = build_heatmap_figure(model)

    assert figure.layout.title.text == "Expression Heatmap"
    assert figure.layout.xaxis.title.text == "Sample or group"
    assert figure.layout.yaxis.title.text == "Gene symbol"
    assert figure.layout.yaxis.autorange == "reversed"
    assert list(figure.data[0].x) == ["Control", "Case", "Recovery"]
    assert list(figure.data[0].y) == ["CXCL10", "IFITM3", "OAS1"]
    assert figure.data[0].z == (
        [0.1, 1.2, 0.4],
        [-0.3, 2.4, 0.8],
        [1.1, -1.4, 0.0],
    )


def test_render_heatmap_view_uses_stable_streamlit_key() -> None:
    source = inspect.getsource(render_heatmap_view)

    assert 'st.subheader("Expression Heatmap")' in source
    assert 'key="expression_heatmap"' in source
