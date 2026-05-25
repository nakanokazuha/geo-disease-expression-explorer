import json
from pathlib import Path


def test_curated_studies_config_has_required_skeleton_records() -> None:
    config_path = Path("app/config/curated_studies.json")

    records = json.loads(config_path.read_text(encoding="utf-8"))

    assert len(records) == 2

    required_fields = {
        "study_accession",
        "study_title",
        "organism",
        "platform",
        "sample_count",
        "case_sample_count",
        "control_sample_count",
        "sample_sources",
        "countries",
        "source_urls",
        "curation_notes",
        "metadata_quality_flags",
    }

    for record in records:
        assert required_fields <= set(record)
        assert record["study_accession"].startswith("GSE")
        assert record["organism"] == "Homo sapiens"
        assert record["sample_count"] == record["case_sample_count"] + record["control_sample_count"]
        assert record["curation_notes"]
