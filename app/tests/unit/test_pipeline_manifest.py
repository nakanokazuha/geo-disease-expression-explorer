from datetime import UTC, datetime
from pathlib import Path

from app.data_pipeline.orchestration import PipelineManifest, PipelineStage, PipelineStatus
from app.data_pipeline.orchestration.storage_paths import PipelineStoragePaths


def test_pipeline_manifest_serializes_stage_metadata() -> None:
    manifest = PipelineManifest(
        stage=PipelineStage.BRONZE_INGESTION,
        status=PipelineStatus.SUCCESS,
        started_at=datetime(2026, 5, 25, 1, 0, tzinfo=UTC),
        finished_at=datetime(2026, 5, 25, 1, 1, tzinfo=UTC),
        input_paths=[Path("app/config/curated_studies.json")],
        output_paths=[Path("app/storage/bronze/studies.json")],
        record_count=2,
        notes=["Skeleton run completed."],
    )

    dumped = manifest.model_dump(mode="json")

    assert dumped["stage"] == "bronze_ingestion"
    assert dumped["status"] == "success"
    assert dumped["input_paths"] == ["app/config/curated_studies.json"]
    assert dumped["record_count"] == 2


def test_pipeline_storage_paths_stay_under_storage_root(tmp_path: Path) -> None:
    paths = PipelineStoragePaths(root=tmp_path)

    assert paths.bronze_studies == tmp_path / "bronze" / "studies.json"
    assert paths.silver_studies == tmp_path / "silver" / "studies.json"
    assert paths.gold_bundle == tmp_path / "gold" / "gold_artifact_bundle.json"
    assert paths.manifest_path(PipelineStage.GOLD_PUBLICATION) == (
        tmp_path / "manifests" / "gold_publication_manifest.json"
    )
