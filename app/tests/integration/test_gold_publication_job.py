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
    assert bundle.dashboard_summary.included_study_count == 2
    assert bundle.dashboard_summary.sample_source_counts == {"PBMC": 30, "blood": 24}
    assert bundle.filter_options.country_filter_enabled is False
    assert bundle.filter_options.country_metadata_status is CountryMetadataStatus.UNAVAILABLE
