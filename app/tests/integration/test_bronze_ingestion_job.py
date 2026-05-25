import json
from pathlib import Path

from app.data_pipeline.jobs.run_bronze_ingestion import run_bronze_ingestion
from app.data_pipeline.orchestration import PipelineStage, PipelineStatus


def test_bronze_ingestion_writes_snapshots_and_manifest(tmp_path: Path) -> None:
    manifest = run_bronze_ingestion(storage_root=tmp_path)

    studies_path = tmp_path / "bronze" / "studies.json"
    manifest_path = tmp_path / "manifests" / "bronze_ingestion_manifest.json"

    studies = json.loads(studies_path.read_text(encoding="utf-8"))
    saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest.stage is PipelineStage.BRONZE_INGESTION
    assert manifest.status is PipelineStatus.SUCCESS
    assert manifest.record_count == 2
    assert len(studies) == 2
    assert studies[0]["study_accession"] == "GSE000001"
    assert "ingested_at" in studies[0]
    assert saved_manifest["stage"] == "bronze_ingestion"
