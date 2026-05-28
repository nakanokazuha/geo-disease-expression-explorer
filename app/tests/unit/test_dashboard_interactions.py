from datetime import UTC, datetime
from types import SimpleNamespace

import app.ui.views as views
import app.ui.views.dashboard_interactions as dashboard_interactions
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
from app.ui.state import DashboardFilterState
from app.ui.views.dashboard_interactions import (
    build_country_filter_notice,
    build_dashboard_interaction_model,
)

GENERATED_AT = datetime(2026, 5, 26, tzinfo=UTC)


def _filter_options(
    *,
    countries: list[str] | None = None,
    country_filter_enabled: bool = False,
    country_filter_reason: str = "Country metadata is unavailable.",
    country_metadata_status: CountryMetadataStatus = CountryMetadataStatus.UNAVAILABLE,
) -> FilterOptions:
    return FilterOptions(
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
        countries=countries or [],
        country_filter_enabled=country_filter_enabled,
        country_filter_reason=country_filter_reason,
        country_metadata_status=country_metadata_status,
    )


def _deg_record(
    gene_symbol: str,
    *,
    adjusted_p_value: float = 0.01,
    log2_fold_change: float = 1.5,
    effect_direction: EffectDirection = EffectDirection.UPREGULATED,
    study_accessions: list[str] | None = None,
    sample_source: str = "PBMC",
) -> MergedDegRecord:
    return MergedDegRecord(
        gene_id=f"{gene_symbol}_ID",
        gene_symbol=gene_symbol,
        log2_fold_change=log2_fold_change,
        adjusted_p_value=adjusted_p_value,
        p_value=adjusted_p_value,
        effect_direction=effect_direction,
        study_accessions=study_accessions or ["GSE000001"],
        sample_source=sample_source,
        provenance_note="Unit test record.",
    )


def _bundle(
    *,
    filter_options: FilterOptions | None = None,
    merged_deg_table: list[MergedDegRecord] | None = None,
    allowed_export_kinds: list[ExportKind] | None = None,
) -> GoldArtifactBundle:
    provenance = ProvenanceContext(
        dataset_version="dataset-v1",
        pipeline_version="pipeline-v1",
        generated_at=GENERATED_AT,
        source_system=SourceSystem.GEO,
        included_studies=["GSE000001", "GSE000002"],
    )
    return GoldArtifactBundle(
        dashboard_summary=DashboardSummary(
            artifact_version="artifact-v1",
            dataset_version="dataset-v1",
            generated_at=GENERATED_AT,
            provenance=provenance,
            included_study_count=2,
            included_sample_count=20,
            case_sample_count=10,
            control_sample_count=10,
            sample_source_counts={"PBMC": 12, "blood": 8},
            study_sample_counts={"GSE000001": 10, "GSE000002": 10},
            country_counts={},
            country_metadata_status=CountryMetadataStatus.UNAVAILABLE,
        ),
        study_summary=[
            StudySummaryRecord(
                study_accession="GSE000001",
                study_title="Unit test study",
                organism="Homo sapiens",
                platform="GPL000",
                included=True,
                inclusion_notes="Included for unit testing.",
                sample_count=10,
                case_sample_count=5,
                control_sample_count=5,
                sample_sources=["PBMC"],
            )
        ],
        merged_deg_table=merged_deg_table
        if merged_deg_table is not None
        else [_deg_record("IFITM3")],
        volcano_points=[
            VolcanoPoint(
                gene_id="IFITM3_ID",
                gene_symbol="IFITM3",
                x_log2_fold_change=1.5,
                y_neg_log10_adjusted_p_value=2.0,
                adjusted_p_value=0.01,
                effect_direction=EffectDirection.UPREGULATED,
                study_accessions=["GSE000001"],
            )
        ],
        heatmap_matrix=HeatmapMatrix(
            gene_symbols=["IFITM3"],
            sample_or_group_labels=["Long COVID", "Control"],
            values=[[1.0, 0.0]],
            value_kind="expression",
            study_accessions=["GSE000001"],
            top_n=1,
        ),
        filter_options=filter_options if filter_options is not None else _filter_options(),
        export_context=ExportContext(
            dataset_version="dataset-v1",
            pipeline_version="pipeline-v1",
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
            provenance_statement="Unit test provenance.",
            disclaimer="For exploratory research use only.",
            allowed_export_kinds=allowed_export_kinds
            if allowed_export_kinds is not None
            else [ExportKind.FILTERED_DEG_CSV],
        ),
    )


def test_country_filter_notice_uses_reason_when_country_filtering_unavailable() -> None:
    notice = build_country_filter_notice(
        _filter_options(country_filter_reason="Country metadata failed reliability checks."),
    )

    assert notice == "Country metadata failed reliability checks."


def test_country_filter_notice_disables_reliable_country_metadata_for_deg() -> None:
    notice = build_country_filter_notice(
        _filter_options(
            countries=["Japan", "United States"],
            country_filter_enabled=True,
            country_filter_reason="Country metadata is reliable.",
            country_metadata_status=CountryMetadataStatus.RELIABLE,
        ),
    )

    assert "Country metadata is available" in notice
    assert "country filtering is not supported for DEG records" in notice


def test_interaction_model_filters_records_and_reports_export_allowed() -> None:
    bundle = _bundle(
        merged_deg_table=[
            _deg_record("KEPT", study_accessions=["GSE000002"], sample_source="blood"),
            _deg_record("HIGH_P", adjusted_p_value=0.02, sample_source="blood"),
            _deg_record("WRONG_SOURCE", sample_source="PBMC"),
        ],
    )
    state = DashboardFilterState(
        adjusted_p_value=0.01,
        log2_fold_change=1.0,
        selected_studies=["GSE000002"],
        selected_sample_sources=["blood"],
        effect_direction=EffectDirectionFilter.UPREGULATED,
        selected_countries=[],
        country_filter_available=False,
        country_filter_note="Country filtering is unavailable.",
    )

    model = build_dashboard_interaction_model(bundle, state)

    assert [record.gene_symbol for record in model.filtered_records] == ["KEPT"]
    assert model.filtered_result_count == 1
    assert model.filtered_deg_export_allowed is True
    assert model.export_disclaimer == "For exploratory research use only."


def test_interaction_model_reports_export_not_allowed_when_kind_absent() -> None:
    model = build_dashboard_interaction_model(
        _bundle(allowed_export_kinds=[ExportKind.SELECTED_GENE_LIST_CSV]),
    )

    assert model.filtered_deg_export_allowed is False


def test_filtered_deg_download_button_uses_stable_key_without_rerun(
    monkeypatch,
) -> None:
    bundle = _bundle()
    state = DashboardFilterState(
        adjusted_p_value=0.05,
        log2_fold_change=1.0,
        selected_studies=[],
        selected_sample_sources=[],
        effect_direction=EffectDirectionFilter.ALL,
        selected_countries=[],
        country_filter_available=False,
        country_filter_note="Country filtering is unavailable.",
    )
    model = dashboard_interactions.DashboardInteractionModel(
        filter_state=state,
        filtered_records=bundle.merged_deg_table,
        filtered_result_count=len(bundle.merged_deg_table),
        filtered_deg_export_allowed=True,
        country_filter_notice="Country filtering is unavailable.",
        export_disclaimer="For exploratory research use only.",
    )
    captured_download_button: dict[str, object] = {}

    monkeypatch.setattr(dashboard_interactions.st, "subheader", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard_interactions.st, "caption", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        dashboard_interactions,
        "build_filtered_deg_csv_export",
        lambda **_kwargs: SimpleNamespace(
            csv_text="gene_symbol\nIFITM3\n",
            filename="filtered.csv",
            mime_type="text/csv",
        ),
    )

    def capture_download_button(*_args, **kwargs) -> None:
        captured_download_button.update(kwargs)

    monkeypatch.setattr(
        dashboard_interactions.st,
        "download_button",
        capture_download_button,
    )

    dashboard_interactions._render_filtered_deg_export_control(bundle, model)

    assert captured_download_button["key"] == "filtered_deg_csv_download"
    assert captured_download_button["on_click"] == "ignore"


def test_dashboard_interactions_render_visualizations_before_deg_table(
    monkeypatch,
) -> None:
    bundle = _bundle()
    state = DashboardFilterState(
        adjusted_p_value=0.05,
        log2_fold_change=1.0,
        selected_studies=[],
        selected_sample_sources=[],
        effect_direction=EffectDirectionFilter.ALL,
        selected_countries=[],
        country_filter_available=False,
        country_filter_note="Country filtering is unavailable.",
    )
    model = dashboard_interactions.DashboardInteractionModel(
        filter_state=state,
        filtered_records=bundle.merged_deg_table,
        filtered_result_count=len(bundle.merged_deg_table),
        filtered_deg_export_allowed=True,
        country_filter_notice="Country filtering is unavailable.",
        export_disclaimer="For exploratory research use only.",
    )
    order: list[str] = []

    monkeypatch.setattr(
        dashboard_interactions,
        "_render_sidebar_filters",
        lambda _filter_options: state,
    )
    monkeypatch.setattr(
        dashboard_interactions,
        "build_dashboard_interaction_model",
        lambda _bundle, _state: model,
    )
    monkeypatch.setattr(
        dashboard_interactions,
        "_render_visualizations",
        lambda _bundle, _state: order.append("visualizations"),
    )
    monkeypatch.setattr(
        dashboard_interactions,
        "render_deg_table",
        lambda _records: order.append("deg_table"),
    )
    monkeypatch.setattr(
        dashboard_interactions,
        "_render_filtered_deg_export_control",
        lambda _bundle, _model: order.append("export"),
    )

    dashboard_interactions.render_dashboard_interactions(bundle)

    assert order == ["visualizations", "deg_table", "export"]


def test_dashboard_visualizations_call_volcano_plot_and_heatmap_view(
    monkeypatch,
) -> None:
    bundle = _bundle()
    state = DashboardFilterState(
        adjusted_p_value=0.05,
        log2_fold_change=1.0,
        selected_studies=[],
        selected_sample_sources=[],
        effect_direction=EffectDirectionFilter.ALL,
        selected_countries=[],
        country_filter_available=False,
        country_filter_note="Country filtering is unavailable.",
    )
    calls: list[str] = []

    def capture_volcano_plot(points, received_state) -> None:
        assert points is bundle.volcano_points
        assert received_state is state
        calls.append("volcano")

    def capture_heatmap_view(matrix) -> None:
        assert matrix is bundle.heatmap_matrix
        calls.append("heatmap")

    monkeypatch.setattr(dashboard_interactions.st, "subheader", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        dashboard_interactions,
        "render_volcano_plot",
        capture_volcano_plot,
    )
    monkeypatch.setattr(
        dashboard_interactions,
        "render_heatmap_view",
        capture_heatmap_view,
    )

    dashboard_interactions._render_visualizations(bundle, state)

    assert calls == ["volcano", "heatmap"]


def test_views_package_exports_visualization_helpers() -> None:
    expected_exports = {
        "VolcanoPlotModel",
        "build_volcano_plot_model",
        "build_volcano_figure",
        "render_volcano_plot",
        "HeatmapViewModel",
        "build_heatmap_view_model",
        "build_heatmap_figure",
        "render_heatmap_view",
    }

    assert expected_exports.issubset(set(views.__all__))
    for export_name in expected_exports:
        assert hasattr(views, export_name)
