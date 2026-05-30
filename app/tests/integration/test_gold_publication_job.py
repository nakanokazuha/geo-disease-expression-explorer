import json
from pathlib import Path

from app.data_pipeline.jobs.run_bronze_ingestion import run_bronze_ingestion
from app.data_pipeline.jobs.run_gold_publication import run_gold_publication
from app.data_pipeline.jobs.run_silver_harmonization import run_silver_harmonization
from app.data_pipeline.orchestration import PipelineStage, PipelineStatus
from app.domain.contracts import GoldArtifactBundle
from app.domain.enums import CountryMetadataStatus


def test_gold_publication_writes_contract_valid_bundle(tmp_path: Path) -> None:
    run_bronze_ingestion(storage_root=tmp_path)
    run_silver_harmonization(storage_root=tmp_path)

    manifest = run_gold_publication(storage_root=tmp_path)

    gold_path = tmp_path / "gold" / "gold_artifact_bundle.json"
    payload = json.loads(gold_path.read_text(encoding="utf-8"))
    bundle = GoldArtifactBundle.model_validate(payload)

    assert manifest.stage is PipelineStage.GOLD_PUBLICATION
    assert manifest.status is PipelineStatus.SUCCESS
    assert manifest.record_count == 1
    assert bundle.dashboard_summary.included_study_count == 3
    assert bundle.dashboard_summary.included_sample_count == 183
    assert bundle.dashboard_summary.case_sample_count == 19
    assert bundle.dashboard_summary.control_sample_count == 17
    assert bundle.dashboard_summary.sample_source_counts == {
        "blood-derived immune cells": 36,
        "whole blood": 147,
    }
    assert bundle.dashboard_summary.study_sample_counts == {
        "GSE224615": 36,
        "GSE267625": 111,
        "GSE270045": 36,
    }
    assert bundle.dashboard_summary.provenance.included_studies == [
        "GSE224615",
        "GSE267625",
        "GSE270045",
    ]
    assert bundle.filter_options.studies == [
        "GSE224615",
        "GSE267625",
        "GSE270045",
    ]
    assert (
        "catalog-included metadata records"
        in bundle.dashboard_summary.provenance.curation_notes[0]
    )
    assert (
        "metadata-catalog sample counts"
        in bundle.dashboard_summary.provenance.metadata_quality_notes[0]
    )
    assert "curated metadata skeleton bundle" in bundle.export_context.provenance_statement
    assert "not expression-ready" in bundle.export_context.disclaimer
    assert bundle.filter_options.country_filter_enabled is False
    assert bundle.filter_options.country_metadata_status is CountryMetadataStatus.UNAVAILABLE
