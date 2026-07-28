import streamlit as st

from components.sidebar import render_nav_button
from ui_pages.cv_management import render_cv_management
from ui_pages.job_management import render_job_management
from ui_pages.job_matching import render_job_matching
from ui_pages.interview_prep_page import render_interview_prep
from ui_pages.hiring_management import (
    render_hiring_management,
)

DEFAULT_PAGE = "CV Management"


def render_sidebar() -> str:
    """Render the sidebar navigation and return the selected page."""

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = DEFAULT_PAGE

    st.sidebar.markdown("## In-Recruit")
    st.sidebar.caption("AI Recruitment Management")

    st.sidebar.divider()
    st.sidebar.markdown("### Navigation")

    render_nav_button(
        display_name="CV Management",
        page_name="CV Management",
    )

    render_nav_button(
        display_name="Job Management",
        page_name="Job Management",
    )

    
    render_nav_button(
        display_name="Job Matching",
        page_name="Job Matching",
    )

    render_nav_button(
        display_name="Hiring Management",
        page_name="Hiring Management",
    )

    # render_nav_button(
        # display_name="Interview Prep",
        # page_name="Interview Prep",
    # )
    

    return st.session_state["current_page"]


def render_page(page: str) -> None:
    """Render the selected application page."""

    if page == "CV Management":
        render_cv_management()

    elif page == "Job Management":
        render_job_management()

    elif page == "Job Matching":
        render_job_matching()

    elif page == "Hiring Management":
        render_hiring_management()

    elif page == "Interview Prep":
        render_interview_prep()

    else:
        st.error(f"Unknown page: {page}")


def main() -> None:
    st.set_page_config(
        page_title="In-Recruit",
        page_icon="IR",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    page = render_sidebar()

    st.title(page)

    render_page(page)


if __name__ == "__main__":
    main()