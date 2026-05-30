import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.data_pipeline.bronze import BronzeStudySnapshot
from app.data_pipeline.jobs.run_bronze_ingestion import run_bronze_ingestion
from app.data_pipeline.orchestration import PipelineStage, PipelineStatus


def _curated_study_record() -> dict[str, object]:
    return {
        "study_accession": "GSE999999",
        "study_title": "Temporary Long COVID blood study",
        "organism": "Homo sapiens",
        "platform": "GPL999",
        "sample_count": 4,
        "case_sample_count": 2,
        "control_sample_count": 2,
        "sample_sources": ["blood"],
        "countries": [],
        "source_urls": ["https://example.test/study/GSE999999"],
        "curation_notes": ["Temporary config record for validation."],
        "metadata_quality_flags": [],
    }


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


def test_bronze_ingestion_uses_project_config_when_cwd_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage_root = tmp_path / "storage"

    monkeypatch.chdir(tmp_path)
    manifest = run_bronze_ingestion(storage_root=storage_root)

    studies = json.loads(
        (storage_root / "bronze" / "studies.json").read_text(encoding="utf-8")
    )
    assert manifest.record_count == 2
    assert studies[0]["study_accession"] == "GSE000001"


def test_bronze_study_snapshot_rejects_inconsistent_sample_counts() -> None:
    record = _curated_study_record()
    record["sample_count"] = 5

    with pytest.raises(ValidationError, match="sample_count must equal"):
        BronzeStudySnapshot(**record, ingested_at=datetime.now(UTC))


def test_bronze_ingestion_rejects_config_with_inconsistent_sample_counts(
    tmp_path: Path,
) -> None:
    record = _curated_study_record()
    record["control_sample_count"] = 1
    config_path = tmp_path / "curated_studies.json"
    config_path.write_text(json.dumps([record]), encoding="utf-8")

    with pytest.raises(ValidationError, match="sample_count must equal"):
        run_bronze_ingestion(
            storage_root=tmp_path / "storage",
            config_path=config_path,
        )


def test_bronze_snapshot_preserves_curated_registry_metadata() -> None:
    snapshot = BronzeStudySnapshot(
        study_accession="GSE270045",
        study_title="Example Long COVID whole blood study",
        organism="Homo sapiens",
        platform="GPL34284 Illumina NovaSeq X Plus",
        platforms=[{"accession": "GPL34284", "name": "Illumina NovaSeq X Plus"}],
        sample_count=36,
        case_sample_count=19,
        control_sample_count=17,
        sample_sources=["whole blood"],
        countries=[],
        source_urls=["https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE270045"],
        publication_urls=["https://pubmed.ncbi.nlm.nih.gov/41205594/"],
        curation_status="primary metadata + first expression candidate",
        pipeline_active=True,
        expression_candidate=True,
        phenotype_label_status="verified from GEO summary",
        curation_notes=["Counts are visible in GEO summary."],
        metadata_quality_flags=["participant_country_unverified"],
        ingested_at=datetime.now(UTC),
    )

    assert snapshot.platforms[0].accession == "GPL34284"
    assert snapshot.publication_urls == ["https://pubmed.ncbi.nlm.nih.gov/41205594/"]
    assert snapshot.expression_candidate is True
    assert snapshot.phenotype_label_status == "verified from GEO summary"


def test_bronze_snapshot_allows_metadata_only_unverified_group_counts() -> None:
    snapshot = BronzeStudySnapshot(
        study_accession="GSE267625",
        study_title="Metadata-only Long COVID study",
        organism="Homo sapiens",
        platform="GPL24676 Illumina NovaSeq 6000",
        platforms=[{"accession": "GPL24676", "name": "Illumina NovaSeq 6000"}],
        sample_count=111,
        case_sample_count=0,
        control_sample_count=0,
        sample_sources=["whole blood"],
        countries=[],
        source_urls=["https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE267625"],
        publication_urls=[],
        curation_status="metadata-only, phenotype labels need verification",
        pipeline_active=True,
        expression_candidate=False,
        phenotype_label_status="needs verification",
        curation_notes=["Phenotype labels need verification."],
        metadata_quality_flags=["metadata_only", "phenotype_labels_need_verification"],
        ingested_at=datetime.now(UTC),
    )

    assert snapshot.case_sample_count == 0
    assert snapshot.control_sample_count == 0
    assert "metadata_only" in snapshot.metadata_quality_flags


def test_bronze_snapshot_rejects_verified_inconsistent_group_counts() -> None:
    with pytest.raises(ValidationError, match="sample_count must equal"):
        BronzeStudySnapshot(
            study_accession="GSE270045",
            study_title="Example Long COVID whole blood study",
            organism="Homo sapiens",
            platform="GPL34284 Illumina NovaSeq X Plus",
            platforms=[{"accession": "GPL34284", "name": "Illumina NovaSeq X Plus"}],
            sample_count=36,
            case_sample_count=18,
            control_sample_count=17,
            sample_sources=["whole blood"],
            countries=[],
            source_urls=["https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE270045"],
            publication_urls=[],
            curation_status="primary metadata + first expression candidate",
            pipeline_active=True,
            expression_candidate=True,
            phenotype_label_status="verified from GEO summary",
            curation_notes=["Counts are visible in GEO summary."],
            metadata_quality_flags=[],
            ingested_at=datetime.now(UTC),
        )
