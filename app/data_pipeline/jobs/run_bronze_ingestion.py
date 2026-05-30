"""Bronze ingestion skeleton job."""

import json
from datetime import UTC, datetime
from pathlib import Path

from app.data_pipeline.bronze import BronzeStudySnapshot, CuratedStudyRecord
from app.data_pipeline.orchestration import (
    PipelineManifest,
    PipelineStage,
    PipelineStatus,
    PipelineStoragePaths,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / "app" / "config" / "curated_studies.json"
DEFAULT_STORAGE_ROOT = PROJECT_ROOT / "app" / "storage"


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run_bronze_ingestion(
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    config_path: Path = CONFIG_PATH,
) -> PipelineManifest:
    started_at = datetime.now(UTC)
    paths = PipelineStoragePaths(root=storage_root)
    paths.ensure_directories()

    config_records = json.loads(config_path.read_text(encoding="utf-8"))
    curated_records = [
        CuratedStudyRecord.model_validate(record) for record in config_records
    ]
    active_records = [record for record in curated_records if record.pipeline_active]
    skipped_records = len(curated_records) - len(active_records)
    snapshots = [
        BronzeStudySnapshot.from_curated_record(record, ingested_at=started_at)
        for record in active_records
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
        notes=[
            "Bronze ingestion wrote active curated GEO study metadata snapshots.",
            f"Read {len(curated_records)} curated registry record(s).",
            f"Skipped {skipped_records} review-only record(s).",
        ],
    )
    _write_json(
        paths.manifest_path(PipelineStage.BRONZE_INGESTION),
        manifest.model_dump(mode="json"),
    )
    return manifest


if __name__ == "__main__":
    run_bronze_ingestion()
