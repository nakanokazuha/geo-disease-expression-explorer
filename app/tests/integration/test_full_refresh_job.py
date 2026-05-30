import json
from pathlib import Path

from app.data_pipeline.jobs.run_full_refresh import run_full_refresh
from app.data_pipeline.orchestration import PipelineStage, PipelineStatus


def test_full_refresh_runs_all_pipeline_stages(tmp_path: Path) -> None:
    manifest = run_full_refresh(storage_root=tmp_path)

    assert manifest.stage is PipelineStage.FULL_REFRESH
    assert manifest.status is PipelineStatus.SUCCESS
    assert manifest.record_count == 3

    assert (tmp_path / "bronze" / "studies.json").exists()
    assert (tmp_path / "silver" / "studies.json").exists()
    assert (tmp_path / "gold" / "gold_artifact_bundle.json").exists()

    bronze_records = json.loads(
        (tmp_path / "bronze" / "studies.json").read_text(encoding="utf-8")
    )
    silver_records = json.loads(
        (tmp_path / "silver" / "studies.json").read_text(encoding="utf-8")
    )
    gold_bundle = json.loads(
        (tmp_path / "gold" / "gold_artifact_bundle.json").read_text(encoding="utf-8")
    )

    assert [record["study_accession"] for record in bronze_records] == [
        "GSE224615",
        "GSE270045",
        "GSE267625",
    ]
    assert len(silver_records) == 3
    assert gold_bundle["dashboard_summary"]["included_study_count"] == 3

    saved_manifest = json.loads(
        (tmp_path / "manifests" / "full_refresh_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert saved_manifest["stage"] == "full_refresh"
    assert saved_manifest["record_count"] == 3
