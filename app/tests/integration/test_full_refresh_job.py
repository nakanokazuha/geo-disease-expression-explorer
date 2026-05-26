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

    saved_manifest = json.loads(
        (tmp_path / "manifests" / "full_refresh_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert saved_manifest["stage"] == "full_refresh"
    assert saved_manifest["record_count"] == 3
