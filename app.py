import streamlit as st

from components.sidebar import render_nav_button
from ui_pages.cv_management import render_cv_management
from ui_pages.job_management import render_job_management
from ui_pages.job_matching import render_job_matching
from ui_pages.interview_prep_page import render_interview_prep
from ui_pages.hiring_management import (
    render_hiring_management,
)
from ui_pages.interview_session_page import (
    render_interview_session_page,
)
# from ui_pages.ai_interview_page import render_ai_interview_page
from ui_pages.public_interview_page import (
    render_public_interview_page,
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

    render_nav_button(
        display_name="Interview Prep",
        page_name="Interview Prep",
    )

    render_nav_button(
        display_name="Interview Session",
        page_name="Interview Session",
    )

    # render_nav_button(
        # display_name="AI Interview",
        # page_name="AI Interview",
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

    elif page == "Interview Session":
        render_interview_session_page()

    # elif page == "AI Interview":
        # render_ai_interview_page()

    else:
        st.error(f"Unknown page: {page}")


def main() -> None:
    st.set_page_config(
        page_title="In-Recruit",
        page_icon="IR",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    interview_token = str(
        st.query_params.get(
            "interview_token",
            "",
        )
    ).strip()

    # Public candidate interview route.
    # This check must happen before rendering the recruiter sidebar.
    if interview_token:
        st.markdown(
            """
            <style>
            section[data-testid="stSidebar"] {
                display: none !important;
            }

            div[data-testid="stSidebarCollapsedControl"] {
                display: none !important;
            }

            .block-container {
                max-width: 900px;
                padding-top: 2rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        render_public_interview_page()
        return

    # Recruiter application styling and navigation.
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"]
        button[data-testid="stBaseButton-tertiary"],

        section[data-testid="stSidebar"]
        button[data-testid="baseButton-tertiary"] {
            justify-content: flex-start !important;
            text-align: left !important;
            padding-left: 0.75rem !important;
        }

        section[data-testid="stSidebar"]
        button[data-testid="stBaseButton-tertiary"] p,

        section[data-testid="stSidebar"]
        button[data-testid="baseButton-tertiary"] p {
            width: 100% !important;
            text-align: left !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    page = render_sidebar()

    st.title(page)

    render_page(page)


if __name__ == "__main__":
    main()