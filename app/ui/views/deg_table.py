"""Filtered DEG table view model and Streamlit rendering helpers."""

from dataclasses import dataclass

import streamlit as st

from app.domain.contracts import MergedDegRecord


@dataclass(frozen=True)
class DegTableModel:
    result_count: int
    rows: list[dict[str, object]]


def _display_row(record: MergedDegRecord) -> dict[str, object]:
    return {
        "Gene symbol": record.gene_symbol,
        "Gene ID": record.gene_id,
        "Log2 fold change": round(record.log2_fold_change, 3),
        "Adjusted p-value": record.adjusted_p_value,
        "P-value": record.p_value,
        "Direction": record.effect_direction.value,
        "Sample source": record.sample_source,
        "Studies": "; ".join(sorted(record.study_accessions)),
        "Provenance note": record.provenance_note,
    }


def build_deg_table_model(records: list[MergedDegRecord]) -> DegTableModel:
    rows = [_display_row(record) for record in records]
    return DegTableModel(result_count=len(rows), rows=rows)


def render_deg_table(records: list[MergedDegRecord]) -> None:
    model = build_deg_table_model(records)

    st.subheader("Filtered DEG Table")
    st.caption(f"{model.result_count} result(s)")
    if not model.rows:
        st.info("No differential expression records match the current filters.")
        return

    st.dataframe(
        model.rows,
        hide_index=True,
        use_container_width=True,
    )
