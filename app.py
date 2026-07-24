import streamlit as st

from pages.cv_management import render_cv_management
from pages.job_management import render_job_management
from pages.job_matching import render_job_matching
from pages.interview_prep_page import render_interview_prep


def main():
    st.set_page_config(
        page_title="CV Management",
        layout="wide"
    )

    st.title("CV Management")

    page = st.sidebar.radio(
        "Navigation",
        [
            "CV Management",
            "Job Management",
            "Job Matching",
            "Interview Prep",
        ],
    )

    if page == "CV Management":
        render_cv_management()
    elif page == "Job Management":
        render_job_management()
    elif page == "Job Matching":
        render_job_matching()
    elif page == "Interview Prep":
        render_interview_prep()


if __name__ == "__main__":
    main()
