"""Controlled vocabulary for app-facing data contracts."""

from enum import StrEnum


class CountryMetadataStatus(StrEnum):
    """Metadata quality status for country-level UI behavior."""

    RELIABLE = "reliable"
    PARTIAL = "partial"
    WEAK = "weak"
    UNAVAILABLE = "unavailable"


class EffectDirection(StrEnum):
    """Effect direction values in Gold expression artifacts."""

    UPREGULATED = "upregulated"
    DOWNREGULATED = "downregulated"
    UNCHANGED = "unchanged"


class EffectDirectionFilter(StrEnum):
    """Effect direction values accepted by UI filter state."""

    ALL = "all"
    UPREGULATED = "upregulated"
    DOWNREGULATED = "downregulated"
    UNCHANGED = "unchanged"


class ExportKind(StrEnum):
    """Approved v1 export kinds."""

    FILTERED_DEG_CSV = "filtered_deg_csv"
    SELECTED_GENE_LIST_CSV = "selected_gene_list_csv"


class SourceSystem(StrEnum):
    """Supported public source systems."""

    GEO = "GEO"
