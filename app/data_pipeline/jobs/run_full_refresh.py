"""Full refresh pipeline orchestration job."""

import json
from datetime import UTC, datetime
from pathlib import Path

from app.data_pipeline.jobs.run_bronze_ingestion import (
    DEFAULT_STORAGE_ROOT,
    run_bronze_ingestion,
)
from app.data_pipeline.jobs.run_gold_publication import run_gold_publication
from app.data_pipeline.jobs.run_silver_harmonization import run_silver_harmonization
from app.data_pipeline.orchestration import (
    PipelineManifest,
    PipelineStage,
    PipelineStatus,
    PipelineStoragePaths,
)


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run_full_refresh(
    storage_root: Path = DEFAULT_STORAGE_ROOT,
) -> PipelineManifest:
    started_at = datetime.now(UTC)
    paths = PipelineStoragePaths(root=storage_root)
    paths.ensure_directories()

    bronze_manifest = run_bronze_ingestion(storage_root=storage_root)
    silver_manifest = run_silver_harmonization(storage_root=storage_root)
    gold_manifest = run_gold_publication(storage_root=storage_root)

    finished_at = datetime.now(UTC)
    manifest = PipelineManifest(
        stage=PipelineStage.FULL_REFRESH,
        status=PipelineStatus.SUCCESS,
        started_at=started_at,
        finished_at=finished_at,
        input_paths=[
            paths.manifest_path(PipelineStage.BRONZE_INGESTION),
            paths.manifest_path(PipelineStage.SILVER_HARMONIZATION),
            paths.manifest_path(PipelineStage.GOLD_PUBLICATION),
        ],
        output_paths=[
            paths.bronze_studies,
            paths.silver_studies,
            paths.gold_bundle,
        ],
        record_count=3,
        notes=[
            f"Bronze status: {bronze_manifest.status.value}.",
            f"Silver status: {silver_manifest.status.value}.",
            f"Gold status: {gold_manifest.status.value}.",
        ],
    )
    _write_json(
        paths.manifest_path(PipelineStage.FULL_REFRESH),
        manifest.model_dump(mode="json"),
    )
    return manifest


if __name__ == "__main__":
    run_full_refresh()
