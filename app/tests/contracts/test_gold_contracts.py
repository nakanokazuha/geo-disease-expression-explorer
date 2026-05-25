from app.domain.enums.contract_enums import (
    CountryMetadataStatus,
    EffectDirection,
    EffectDirectionFilter,
    ExportKind,
    SourceSystem,
)


def test_contract_enums_expose_stable_values() -> None:
    assert CountryMetadataStatus.RELIABLE == "reliable"
    assert CountryMetadataStatus.PARTIAL == "partial"
    assert CountryMetadataStatus.WEAK == "weak"
    assert CountryMetadataStatus.UNAVAILABLE == "unavailable"
    assert EffectDirection.UPREGULATED == "upregulated"
    assert EffectDirection.DOWNREGULATED == "downregulated"
    assert EffectDirection.UNCHANGED == "unchanged"
    assert EffectDirectionFilter.ALL == "all"
    assert ExportKind.FILTERED_DEG_CSV == "filtered_deg_csv"
    assert ExportKind.SELECTED_GENE_LIST_CSV == "selected_gene_list_csv"
    assert SourceSystem.GEO == "GEO"
