import streamlit as st

from components.matching.ai_matching import render_ai_matching
from components.matching.traditional_matching import render_traditional_matching
from components.matching.utils import create_job_label, display_selected_job
from match_loader import load_all_candidates, load_all_jobs


def render_job_matching() -> None:
    candidates = load_all_candidates()
    jobs = load_all_jobs()

    if not candidates:
        st.warning("No candidates found. Please upload and extract CVs first.")
        return

    if not jobs:
        st.warning("No jobs found. Please create a job first.")
        return

    job_options = {create_job_label(job): job for job in jobs}

    selected_job_label = st.selectbox(
        "Select a job",
        list(job_options.keys()),
        key="matching_job_select",
    )
    selected_job = job_options[selected_job_label]

    display_selected_job(selected_job)
    st.divider()

    ai_tab, traditional_tab = st.tabs(["AI Matching", "Rule Matching"])

    with ai_tab:
        render_ai_matching(candidates, selected_job)

    with traditional_tab:
        render_traditional_matching(candidates, selected_job)
