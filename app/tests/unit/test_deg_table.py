from app.domain.contracts import MergedDegRecord
from app.domain.enums import EffectDirection
from app.ui.views.deg_table import build_deg_table_model


def _deg_record(
    *,
    gene_id: str = "ENSG000001",
    gene_symbol: str = "IFITM3",
    log2_fold_change: float = 1.23456,
    adjusted_p_value: float = 0.012345,
    p_value: float = 0.000456,
    effect_direction: EffectDirection = EffectDirection.UPREGULATED,
    study_accessions: list[str] | None = None,
    sample_source: str = "PBMC",
    provenance_note: str = "Merged from public GEO studies.",
) -> MergedDegRecord:
    return MergedDegRecord(
        gene_id=gene_id,
        gene_symbol=gene_symbol,
        log2_fold_change=log2_fold_change,
        adjusted_p_value=adjusted_p_value,
        p_value=p_value,
        effect_direction=effect_direction,
        study_accessions=study_accessions or ["GSE200002", "GSE100001"],
        sample_source=sample_source,
        provenance_note=provenance_note,
    )


def test_deg_table_model_builds_stable_display_rows() -> None:
    model = build_deg_table_model([_deg_record()])

    assert model.result_count == 1
    assert model.rows == [
        {
            "Gene symbol": "IFITM3",
            "Gene ID": "ENSG000001",
            "Log2 fold change": 1.235,
            "Adjusted p-value": 0.012345,
            "P-value": 0.000456,
            "Direction": "upregulated",
            "Sample source": "PBMC",
            "Studies": "GSE100001; GSE200002",
            "Provenance note": "Merged from public GEO studies.",
        }
    ]


def test_deg_table_model_returns_empty_rows_for_empty_results() -> None:
    model = build_deg_table_model([])

    assert model.result_count == 0
    assert model.rows == []
