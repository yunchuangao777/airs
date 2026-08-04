import streamlit as st

from services.permission_service import has_permission

from components.create_job_dialog import (
    show_create_job_dialog,
)
from components.job_library import render_job_library


def render_job_management():

    # st.header("Job Management")

    if st.session_state.get("job_created_message"):
        st.success(
            st.session_state.pop("job_created_message")
        )

    action_col, search_col = st.columns(
        [1, 4],
        vertical_alignment="bottom",
    )

    with action_col:
        can_create_job = has_permission("job.create")

        if st.button(
            "＋ Create Job",
            type="primary",
            use_container_width=True,
            key="open_create_job_dialog",
            disabled=not can_create_job,
        ):
            show_create_job_dialog()

    with search_col:
        search_text = st.text_input(
            "Search jobs",
            placeholder=(
                "Search title, company, location, skills, "
                "responsibilities..."
            ),
            key="job_global_search",
        )

    st.divider()

    render_job_library(search_text=search_text)