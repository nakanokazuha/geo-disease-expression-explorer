"""Streamlit entrypoint for the Long COVID GEO Expression Explorer."""

import streamlit as st

from app.ui.data_access import GoldArtifactNotFoundError, load_gold_bundle
from app.ui.views import render_dashboard_overview


def _render_missing_gold_artifact(error: GoldArtifactNotFoundError) -> None:
    st.title("Long COVID GEO Expression Explorer")
    st.caption("Study-aware public GEO expression explorer.")
    st.warning("No published Gold artifact bundle is available yet.")
    st.info(
        "Run the local full refresh pipeline to publish "
        "`app/storage/gold/gold_artifact_bundle.json`."
    )
    st.code(str(error), language="text")


def main() -> None:
    st.set_page_config(
        page_title="Long COVID GEO Expression Explorer",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    try:
        bundle = load_gold_bundle()
    except GoldArtifactNotFoundError as error:
        _render_missing_gold_artifact(error)
        return

    render_dashboard_overview(bundle)


if __name__ == "__main__":
    main()
