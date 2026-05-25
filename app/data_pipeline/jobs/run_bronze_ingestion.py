"""Bronze ingestion skeleton job."""

import json
from datetime import UTC, datetime
from pathlib import Path

from app.data_pipeline.bronze import BronzeStudySnapshot
from app.data_pipeline.orchestration import (
    PipelineManifest,
    PipelineStage,
    PipelineStatus,
    PipelineStoragePaths,
)

CONFIG_PATH = Path("app/config/curated_studies.json")


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run_bronze_ingestion(
    storage_root: Path = Path("app/storage"),
    config_path: Path = CONFIG_PATH,
) -> PipelineManifest:
    started_at = datetime.now(UTC)
    paths = PipelineStoragePaths(root=storage_root)
    paths.ensure_directories()

    config_records = json.loads(config_path.read_text(encoding="utf-8"))
    snapshots = [
        BronzeStudySnapshot(**record, ingested_at=started_at) for record in config_records
    ]

    _write_json(
        paths.bronze_studies,
        [snapshot.model_dump(mode="json") for snapshot in snapshots],
    )

    finished_at = datetime.now(UTC)
    manifest = PipelineManifest(
        stage=PipelineStage.BRONZE_INGESTION,
        status=PipelineStatus.SUCCESS,
        started_at=started_at,
        finished_at=finished_at,
        input_paths=[config_path],
        output_paths=[paths.bronze_studies],
        record_count=len(snapshots),
        notes=["Bronze skeleton wrote curated study snapshots."],
    )
    _write_json(
        paths.manifest_path(PipelineStage.BRONZE_INGESTION),
        manifest.model_dump(mode="json"),
    )
    return manifest


if __name__ == "__main__":
    run_bronze_ingestion()
