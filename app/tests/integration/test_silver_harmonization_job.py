import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.data_pipeline.jobs.run_bronze_ingestion import run_bronze_ingestion
from app.data_pipeline.jobs.run_silver_harmonization import run_silver_harmonization
from app.data_pipeline.orchestration import PipelineStage, PipelineStatus
from app.data_pipeline.silver.study_record import SilverStudyRecord


def test_silver_harmonization_writes_standardized_records(tmp_path: Path) -> None:
    run_bronze_ingestion(storage_root=tmp_path)

    manifest = run_silver_harmonization(storage_root=tmp_path)

    silver_path = tmp_path / "silver" / "studies.json"
    records = json.loads(silver_path.read_text(encoding="utf-8"))

    assert manifest.stage is PipelineStage.SILVER_HARMONIZATION
    assert manifest.status is PipelineStatus.SUCCESS
    assert manifest.record_count == 3
    assert len(records) == 3

    validated_records = [SilverStudyRecord.model_validate(record) for record in records]
    records_by_accession = {
        record.study_accession: record for record in validated_records
    }

    assert all(record.included for record in validated_records)
    assert records_by_accession["GSE224615"].sample_sources == [
        "blood-derived immune cells"
    ]


def test_silver_harmonization_keeps_metadata_only_active_records(
    tmp_path: Path,
) -> None:
    run_bronze_ingestion(storage_root=tmp_path)

    run_silver_harmonization(storage_root=tmp_path)

    silver_path = tmp_path / "silver" / "studies.json"
    records = json.loads(silver_path.read_text(encoding="utf-8"))
    records_by_accession = {
        record["study_accession"]: SilverStudyRecord.model_validate(record)
        for record in records
    }

    metadata_only_record = records_by_accession["GSE267625"]

    assert metadata_only_record.included is True
    assert metadata_only_record.sample_count == 111
    assert metadata_only_record.case_sample_count == 0
    assert metadata_only_record.control_sample_count == 0
    assert "metadata_only" in metadata_only_record.metadata_quality_flags
    assert (
        metadata_only_record.inclusion_notes
        == "Included for metadata cataloging; phenotype labels need verification "
        "before expression analysis."
    )


def test_silver_study_record_rejects_coerced_values() -> None:
    record = {
        "study_accession": "GSE000001",
        "study_title": "Long COVID expression pilot",
        "organism": "Homo sapiens",
        "platform": "RNA-seq",
        "included": "true",
        "inclusion_notes": "Has case and control samples",
        "sample_count": "1",
        "case_sample_count": 1,
        "control_sample_count": 0,
        "sample_sources": ["blood"],
        "countries": ["United States"],
        "metadata_quality_flags": [],
    }

    with pytest.raises(ValidationError):
        SilverStudyRecord.model_validate(record)
