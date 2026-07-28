import streamlit as st

from components.hiring.candidate_management import (
    render_candidate_management,
)
from components.hiring.job_overview import (
    render_job_overview,
)
from services.hiring_service import (
    build_hiring_dataset,
    get_job_status_summaries,
)


def render_hiring_management() -> None:
    status_message = st.session_state.pop(
        "hiring_status_update_message",
        None,
    )

    if status_message:
        st.success(status_message)

    # Reading the current JSON data on each rerun ensures that
    # status changes immediately appear in both tabs.
    dataset = build_hiring_dataset()

    summaries = get_job_status_summaries(
        dataset
    )

    overview_tab, candidate_tab = st.tabs(
        [
            "Job Overview",
            "Candidate Management",
        ]
    )

    with overview_tab:
        render_job_overview(
            summaries=summaries,
        )

    with candidate_tab:
        render_candidate_management(
            dataset=dataset,
            summaries=summaries,
        )