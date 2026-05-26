"""Silver harmonization skeleton job."""

import json
from datetime import UTC, datetime
from pathlib import Path

from app.data_pipeline.bronze import BronzeStudySnapshot
from app.data_pipeline.jobs.run_bronze_ingestion import DEFAULT_STORAGE_ROOT
from app.data_pipeline.orchestration import (
    PipelineManifest,
    PipelineStage,
    PipelineStatus,
    PipelineStoragePaths,
)
from app.data_pipeline.silver import SilverStudyRecord


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _is_included(snapshot: BronzeStudySnapshot) -> bool:
    return (
        snapshot.organism == "Homo sapiens"
        and snapshot.sample_count > 0
        and snapshot.case_sample_count > 0
        and snapshot.control_sample_count > 0
    )


def _harmonize_snapshot(snapshot: BronzeStudySnapshot) -> SilverStudyRecord:
    included = _is_included(snapshot)
    inclusion_notes = (
        "Passed skeleton inclusion gate."
        if included
        else "Failed skeleton inclusion gate."
    )
    return SilverStudyRecord(
        study_accession=snapshot.study_accession,
        study_title=snapshot.study_title,
        organism=snapshot.organism,
        platform=snapshot.platform,
        included=included,
        inclusion_notes=inclusion_notes,
        sample_count=snapshot.sample_count,
        case_sample_count=snapshot.case_sample_count,
        control_sample_count=snapshot.control_sample_count,
        sample_sources=snapshot.sample_sources,
        countries=snapshot.countries,
        metadata_quality_flags=snapshot.metadata_quality_flags,
    )


def run_silver_harmonization(
    storage_root: Path = DEFAULT_STORAGE_ROOT,
) -> PipelineManifest:
    started_at = datetime.now(UTC)
    paths = PipelineStoragePaths(root=storage_root)
    paths.ensure_directories()

    bronze_records = json.loads(paths.bronze_studies.read_text(encoding="utf-8"))
    snapshots = [BronzeStudySnapshot(**record) for record in bronze_records]
    silver_records = [_harmonize_snapshot(snapshot) for snapshot in snapshots]

    _write_json(
        paths.silver_studies,
        [record.model_dump(mode="json") for record in silver_records],
    )

    finished_at = datetime.now(UTC)
    manifest = PipelineManifest(
        stage=PipelineStage.SILVER_HARMONIZATION,
        status=PipelineStatus.SUCCESS,
        started_at=started_at,
        finished_at=finished_at,
        input_paths=[paths.bronze_studies],
        output_paths=[paths.silver_studies],
        record_count=len(silver_records),
        notes=["Silver skeleton wrote standardized study records."],
    )
    _write_json(
        paths.manifest_path(PipelineStage.SILVER_HARMONIZATION),
        manifest.model_dump(mode="json"),
    )
    return manifest


if __name__ == "__main__":
    run_silver_harmonization()
