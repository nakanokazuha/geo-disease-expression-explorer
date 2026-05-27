from app.domain.contracts import FilterOptions, FilterThresholdRange, MergedDegRecord
from app.domain.enums import (
    CountryMetadataStatus,
    EffectDirection,
    EffectDirectionFilter,
)
from app.ui.state.dashboard_filters import (
    DashboardFilterState,
    apply_dashboard_filters,
    build_default_filter_state,
    build_threshold_context,
)


def _filter_options(
    *,
    adjusted_p_value: float = 0.05,
    log2_fold_change: float = 1.0,
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
        adjusted_p_value=FilterThresholdRange(
            default=adjusted_p_value,
            minimum=0.0,
            maximum=1.0,
        ),
        log2_fold_change=FilterThresholdRange(
            default=log2_fold_change,
            minimum=0.0,
            maximum=10.0,
        ),
        countries=countries or [],
        country_filter_enabled=country_filter_enabled,
        country_filter_reason=country_filter_reason,
        country_metadata_status=country_metadata_status,
    )


def _record(
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


def test_default_state_uses_threshold_defaults_and_all_empty_selections() -> None:
    state = build_default_filter_state(
        _filter_options(adjusted_p_value=0.1, log2_fold_change=2.0),
    )

    assert state.adjusted_p_value == 0.1
    assert state.log2_fold_change == 2.0
    assert state.selected_studies == []
    assert state.selected_sample_sources == []
    assert state.effect_direction is EffectDirectionFilter.ALL
    assert state.selected_countries == []
    assert state.country_filter_available is False
    assert state.country_filter_note == "Country metadata is unavailable."


def test_country_filter_stays_unavailable_for_reliable_metadata() -> None:
    state = build_default_filter_state(
        _filter_options(
            countries=["Japan", "United States"],
            country_filter_enabled=True,
            country_filter_reason="Country metadata is reliable.",
            country_metadata_status=CountryMetadataStatus.RELIABLE,
        ),
    )

    assert state.country_filter_available is False
    assert state.selected_countries == []
    assert "not supported for DEG records yet" in state.country_filter_note


def test_filters_by_adjusted_p_value_and_absolute_log2_fold_change() -> None:
    records = [
        _record("KEPT_UP", adjusted_p_value=0.05, log2_fold_change=1.0),
        _record("KEPT_DOWN", adjusted_p_value=0.01, log2_fold_change=-1.2),
        _record("HIGH_P", adjusted_p_value=0.06, log2_fold_change=2.0),
        _record("LOW_EFFECT", adjusted_p_value=0.01, log2_fold_change=0.9),
    ]
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

    filtered = apply_dashboard_filters(records, state)

    assert [record.gene_symbol for record in filtered] == ["KEPT_UP", "KEPT_DOWN"]


def test_filters_by_study_sample_source_and_effect_direction() -> None:
    records = [
        _record(
            "KEPT",
            effect_direction=EffectDirection.DOWNREGULATED,
            log2_fold_change=-1.4,
            study_accessions=["GSE000001", "GSE000003"],
            sample_source="blood",
        ),
        _record(
            "WRONG_STUDY",
            effect_direction=EffectDirection.DOWNREGULATED,
            log2_fold_change=-1.4,
            study_accessions=["GSE999999"],
            sample_source="blood",
        ),
        _record(
            "WRONG_SOURCE",
            effect_direction=EffectDirection.DOWNREGULATED,
            log2_fold_change=-1.4,
            study_accessions=["GSE000003"],
            sample_source="PBMC",
        ),
        _record(
            "WRONG_DIRECTION",
            effect_direction=EffectDirection.UPREGULATED,
            log2_fold_change=1.4,
            study_accessions=["GSE000003"],
            sample_source="blood",
        ),
    ]
    state = DashboardFilterState(
        adjusted_p_value=0.05,
        log2_fold_change=1.0,
        selected_studies=["GSE000003"],
        selected_sample_sources=["blood"],
        effect_direction=EffectDirectionFilter.DOWNREGULATED,
        selected_countries=[],
        country_filter_available=False,
        country_filter_note="Country filtering is unavailable.",
    )

    filtered = apply_dashboard_filters(records, state)

    assert [record.gene_symbol for record in filtered] == ["KEPT"]


def test_build_threshold_context_copies_filter_state_without_countries() -> None:
    state = DashboardFilterState(
        adjusted_p_value=0.01,
        log2_fold_change=1.5,
        selected_studies=["GSE000001"],
        selected_sample_sources=["PBMC"],
        effect_direction=EffectDirectionFilter.UPREGULATED,
        selected_countries=["Japan"],
        country_filter_available=False,
        country_filter_note="Country filtering is unavailable.",
    )

    context = build_threshold_context(state)

    assert context.adjusted_p_value == 0.01
    assert context.log2_fold_change == 1.5
    assert context.selected_studies == ["GSE000001"]
    assert context.selected_sample_sources == ["PBMC"]
    assert context.effect_direction is EffectDirectionFilter.UPREGULATED
    assert context.selected_countries == []
