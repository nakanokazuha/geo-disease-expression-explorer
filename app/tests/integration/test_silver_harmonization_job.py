import json
from pathlib import Path

from app.data_pipeline.jobs.run_bronze_ingestion import run_bronze_ingestion
from app.data_pipeline.jobs.run_silver_harmonization import run_silver_harmonization
from app.data_pipeline.orchestration import PipelineStage, PipelineStatus


def test_silver_harmonization_writes_standardized_records(tmp_path: Path) -> None:
    run_bronze_ingestion(storage_root=tmp_path)

    manifest = run_silver_harmonization(storage_root=tmp_path)

    silver_path = tmp_path / "silver" / "studies.json"
    records = json.loads(silver_path.read_text(encoding="utf-8"))

    assert manifest.stage is PipelineStage.SILVER_HARMONIZATION
    assert manifest.status is PipelineStatus.SUCCESS
    assert manifest.record_count == 2
    assert records[0]["study_accession"] == "GSE000001"
    assert records[0]["included"] is True
    assert records[0]["sample_sources"] == ["blood"]
