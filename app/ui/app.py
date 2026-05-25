"""Streamlit entrypoint for the Long COVID GEO Expression Explorer."""

import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="Long COVID GEO Expression Explorer",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Long COVID GEO Expression Explorer")
    st.caption("Study-aware public GEO expression explorer.")
    st.info(
        "Repository foundation is ready. Gold data contracts will be defined before "
        "real dashboard views are implemented."
    )


if __name__ == "__main__":
    main()
