import json
from pathlib import Path

CONFIG_PATH = Path("app/config/curated_studies.json")


def _records() -> list[dict[str, object]]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_curated_studies_registry_has_required_records() -> None:
    records = _records()
    accessions = {record["study_accession"] for record in records}

    assert {"GSE224615", "GSE270045", "GSE267625"} <= accessions
    assert {"GSE226260", "GSE297499", "GSE235050", "GSE262861", "GSE265753"} <= (
        accessions
    )


def test_curated_studies_registry_active_records_match_first_metadata_milestone() -> None:
    records = _records()
    active_records = [record for record in records if record["pipeline_active"]]

    assert [record["study_accession"] for record in active_records] == [
        "GSE224615",
        "GSE270045",
        "GSE267625",
    ]
    assert {
        record["study_accession"]: record["curation_status"]
        for record in active_records
    } == {
        "GSE224615": "primary metadata candidate",
        "GSE270045": "primary metadata + first expression candidate",
        "GSE267625": "metadata-only, phenotype labels need verification",
    }


def test_curated_studies_registry_has_required_metadata_fields() -> None:
    required_fields = {
        "study_accession",
        "study_title",
        "organism",
        "platforms",
        "sample_count",
        "case_sample_count",
        "control_sample_count",
        "sample_sources",
        "countries",
        "source_urls",
        "publication_urls",
        "curation_status",
        "pipeline_active",
        "expression_candidate",
        "phenotype_label_status",
        "curation_notes",
        "metadata_quality_flags",
    }

    for record in _records():
        assert required_fields <= set(record)
        assert str(record["study_accession"]).startswith("GSE")
        assert record["organism"] == "Homo sapiens"
        assert record["platforms"]
        assert record["source_urls"]
        assert record["curation_notes"]


def test_secondary_candidates_are_review_only() -> None:
    secondary_accessions = {
        "GSE226260",
        "GSE297499",
        "GSE235050",
        "GSE262861",
        "GSE265753",
    }

    secondary_records = [
        record
        for record in _records()
        if record["study_accession"] in secondary_accessions
    ]

    assert len(secondary_records) == len(secondary_accessions)
    assert all(not record["pipeline_active"] for record in secondary_records)
    assert all(not record["expression_candidate"] for record in secondary_records)


def test_gse267625_is_metadata_only_until_phenotype_labels_are_verified() -> None:
    record = next(
        record for record in _records() if record["study_accession"] == "GSE267625"
    )

    assert record["pipeline_active"] is True
    assert record["expression_candidate"] is False
    assert record["phenotype_label_status"] == "needs verification"
    assert record["case_sample_count"] == 0
    assert record["control_sample_count"] == 0
    assert "metadata_only" in record["metadata_quality_flags"]
    assert "phenotype_labels_need_verification" in record["metadata_quality_flags"]
