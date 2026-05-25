from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.contracts.export_contract import ExportContext, ThresholdContext
from app.domain.enums import EffectDirectionFilter, ExportKind


def test_export_context_accepts_allowed_export_kinds() -> None:
    context = ExportContext(
        dataset_version="long-covid-v1",
        pipeline_version="pipeline-0.1.0",
        generated_at=datetime(2026, 5, 25, tzinfo=UTC),
        included_studies=["GSE000001"],
        threshold_context=ThresholdContext(
            adjusted_p_value=0.05,
            log2_fold_change=1.0,
            selected_studies=["GSE000001"],
            selected_sample_sources=["blood"],
            effect_direction=EffectDirectionFilter.ALL,
            selected_countries=[],
        ),
        provenance_statement="Merged exploratory output from curated GEO studies.",
        disclaimer="Exploratory research use only; not clinical or diagnostic.",
        allowed_export_kinds=[
            ExportKind.FILTERED_DEG_CSV,
            ExportKind.SELECTED_GENE_LIST_CSV,
        ],
    )

    assert context.allowed_export_kinds == [
        ExportKind.FILTERED_DEG_CSV,
        ExportKind.SELECTED_GENE_LIST_CSV,
    ]


def test_export_context_rejects_unapproved_export_kind() -> None:
    with pytest.raises(ValidationError):
        ExportContext(
            dataset_version="long-covid-v1",
            pipeline_version="pipeline-0.1.0",
            generated_at=datetime(2026, 5, 25, tzinfo=UTC),
            included_studies=["GSE000001"],
            threshold_context=ThresholdContext(
                adjusted_p_value=0.05,
                log2_fold_change=1.0,
                selected_studies=[],
                selected_sample_sources=[],
                effect_direction=EffectDirectionFilter.ALL,
                selected_countries=[],
            ),
            provenance_statement="Merged exploratory output from curated GEO studies.",
            disclaimer="Exploratory research use only; not clinical or diagnostic.",
            allowed_export_kinds=["raw_source_dump"],
        )


def test_threshold_context_rejects_invalid_p_value_threshold() -> None:
    with pytest.raises(ValidationError):
        ThresholdContext(
            adjusted_p_value=1.5,
            log2_fold_change=1.0,
            selected_studies=[],
            selected_sample_sources=[],
            effect_direction=EffectDirectionFilter.ALL,
            selected_countries=[],
        )
