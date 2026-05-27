"""Dashboard filter state and DEG filtering semantics."""

from dataclasses import dataclass

from app.domain.contracts import FilterOptions, MergedDegRecord, ThresholdContext
from app.domain.enums import EffectDirectionFilter

COUNTRY_FILTER_DISABLED_NOTE = (
    "Country metadata is available, but country filtering is not supported "
    "for DEG records yet."
)


@dataclass(frozen=True)
class DashboardFilterState:
    """Current dashboard filter selections."""

    adjusted_p_value: float
    log2_fold_change: float
    selected_studies: list[str]
    selected_sample_sources: list[str]
    effect_direction: EffectDirectionFilter
    selected_countries: list[str]
    country_filter_available: bool
    country_filter_note: str


def build_default_filter_state(filter_options: FilterOptions) -> DashboardFilterState:
    """Build the default dashboard filter state from canonical filter options."""

    country_filter_note = filter_options.country_filter_reason
    if filter_options.country_filter_enabled and filter_options.countries:
        country_filter_note = COUNTRY_FILTER_DISABLED_NOTE

    return DashboardFilterState(
        adjusted_p_value=filter_options.adjusted_p_value.default,
        log2_fold_change=filter_options.log2_fold_change.default,
        selected_studies=[],
        selected_sample_sources=[],
        effect_direction=EffectDirectionFilter.ALL,
        selected_countries=[],
        country_filter_available=False,
        country_filter_note=country_filter_note,
    )


def apply_dashboard_filters(
    records: list[MergedDegRecord],
    state: DashboardFilterState,
) -> list[MergedDegRecord]:
    """Apply dashboard filters to merged DEG records."""

    selected_studies = set(state.selected_studies)
    selected_sample_sources = set(state.selected_sample_sources)

    return [
        record
        for record in records
        if record.adjusted_p_value <= state.adjusted_p_value
        and abs(record.log2_fold_change) >= state.log2_fold_change
        and (
            not selected_studies
            or bool(selected_studies.intersection(record.study_accessions))
        )
        and (
            not selected_sample_sources
            or record.sample_source in selected_sample_sources
        )
        and (
            state.effect_direction is EffectDirectionFilter.ALL
            or record.effect_direction.value == state.effect_direction.value
        )
    ]


def build_threshold_context(state: DashboardFilterState) -> ThresholdContext:
    """Convert dashboard filter state to export threshold context."""

    return ThresholdContext(
        adjusted_p_value=state.adjusted_p_value,
        log2_fold_change=state.log2_fold_change,
        selected_studies=list(state.selected_studies),
        selected_sample_sources=list(state.selected_sample_sources),
        effect_direction=state.effect_direction,
        selected_countries=[],
    )
