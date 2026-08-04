import streamlit as st

from services.auth_service import (
    initialize_authentication,
    render_sidebar_user_panel,
    require_staff_authentication,
)

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
from ui_pages.dashboard import (
    render_dashboard,
)
from services.permission_service import (
    can_access_page,
    get_allowed_pages,
)
from ui_pages.user_management import (
    render_user_management,
)
from ui_pages.ai_recruiter import (
    render_ai_recruiter,
)

DEFAULT_PAGE = "Dashboard"


def render_sidebar(
    authenticator,
    user_record: dict,
) -> str:
    """Render the sidebar navigation and return the selected page."""

    allowed_pages = get_allowed_pages()

    if not allowed_pages:
        st.sidebar.error(
            "No application pages are assigned to your role."
        )
        st.stop()

    current_page = st.session_state.get(
        "current_page",
        DEFAULT_PAGE,
    )

    if current_page not in allowed_pages:
        st.session_state["current_page"] = (
            allowed_pages[0]
        )
        
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = DEFAULT_PAGE

    st.sidebar.markdown("## In-Recruit")
    st.sidebar.caption("AI Recruitment Management")

    st.sidebar.divider()
    st.sidebar.markdown("### Navigation")

    if can_access_page("Dashboard"):
        render_nav_button(
            display_name="Dashboard",
            page_name="Dashboard",
        )

    if can_access_page("CV Management"):
        render_nav_button(
            display_name="CV Management",
            page_name="CV Management",
        )

    if can_access_page("Job Management"):
        render_nav_button(
            display_name="Job Management",
            page_name="Job Management",
        )

    if can_access_page("Job Matching"):
        render_nav_button(
            display_name="Job Matching",
            page_name="Job Matching",
        )

    if can_access_page("Hiring Management"):
        render_nav_button(
            display_name="Hiring Management",
            page_name="Hiring Management",
        )

    if can_access_page("Interview Prep"):
        render_nav_button(
            display_name="Interview Prep",
            page_name="Interview Prep",
        )

    if can_access_page("Interview Session"):
        render_nav_button(
            display_name="Interview Session",
            page_name="Interview Session",
        )

    if can_access_page("AI Recruiter"):
        render_nav_button(
            display_name="🤖 AI Recruiter",
            page_name="AI Recruiter",
        )
        
    if can_access_page("User Management"):
        render_nav_button(
            display_name="User Management",
            page_name="User Management",
        )

    # render_nav_button(
        # display_name="AI Interview",
        # page_name="AI Interview",
    # )

    render_sidebar_user_panel(
        authenticator=authenticator,
        user_record=user_record,
    )

    return st.session_state["current_page"]


def render_page(page: str) -> None:
    """Render the selected application page."""

    if not can_access_page(page):
        st.error(
            "You do not have permission to access "
            "this page."
        )
        return

    if page == "Dashboard":
        render_dashboard()
        
    elif page == "CV Management":
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

    elif page == "User Management":
        render_user_management()

    elif page == "AI Recruiter":
        render_ai_recruiter()

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

            section[data-testid="stSidebar"]
            button[data-testid="stBaseButton-tertiary"],
            section[data-testid="stSidebar"]
            button[data-testid="baseButton-tertiary"] {
                justify-content: flex-start !important;
                text-align: left !important;
            }

            section[data-testid="stSidebar"]
            button[data-testid="stBaseButton-tertiary"] > div,
            section[data-testid="stSidebar"]
            button[data-testid="baseButton-tertiary"] > div {
                width: 100% !important;
                justify-content: flex-start !important;
                text-align: left !important;
            }

            section[data-testid="stSidebar"]
            button[data-testid="stBaseButton-tertiary"] p,
            section[data-testid="stSidebar"]
            button[data-testid="baseButton-tertiary"] p {
                width: 100% !important;
                margin: 0 !important;
                text-align: left !important;
            }
            
            </style>
            """,
            unsafe_allow_html=True,
        )

        render_public_interview_page()
        return

    # Staff authentication applies only to the recruiter application.
    # Public candidate interview links bypass this block.
    try:
        auth_config, authenticator = (
            initialize_authentication()
        )
    except Exception as exc:
        st.error(
            "AIRS authentication could not be initialized."
        )
        st.exception(exc)
        return

    user_record = require_staff_authentication(
        config=auth_config,
        authenticator=authenticator,
    )

    if user_record is None:
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

            border: 1.5px solid rgba(
                120,
                120,
                120,
                0.42
            ) !important;
            border-radius: 9px !important;
            background: transparent !important;
            margin-bottom: 0.35rem !important;

            transition:
                border-color 0.18s ease,
                background-color 0.18s ease,
                box-shadow 0.18s ease !important;
        }

        section[data-testid="stSidebar"]
        button[data-testid="stBaseButton-tertiary"]:hover,

        section[data-testid="stSidebar"]
        button[data-testid="baseButton-tertiary"]:hover {
            border-color: rgba(
                46,
                125,
                90,
                0.85
            ) !important;
            background-color: rgba(
                46,
                125,
                90,
                0.07
            ) !important;
            box-shadow: 0 2px 7px rgba(
                0,
                0,
                0,
                0.08
            ) !important;
        }

        /*
        Streamlit places the button label inside an internal
        Markdown container. The button itself may be left-aligned
        while that inner container remains centered, so all three
        levels need to be aligned.
        */
        section[data-testid="stSidebar"]
        button[data-testid="stBaseButton-tertiary"],

        section[data-testid="stSidebar"]
        button[data-testid="baseButton-tertiary"] {
            justify-content: flex-start !important;
        }

        section[data-testid="stSidebar"]
        button[data-testid="stBaseButton-tertiary"]
        div[data-testid="stMarkdownContainer"],

        section[data-testid="stSidebar"]
        button[data-testid="baseButton-tertiary"]
        div[data-testid="stMarkdownContainer"] {
            width: 100% !important;
            display: block !important;
            text-align: left !important;
        }

        section[data-testid="stSidebar"]
        button[data-testid="stBaseButton-tertiary"]
        div[data-testid="stMarkdownContainer"] p,

        section[data-testid="stSidebar"]
        button[data-testid="baseButton-tertiary"]
        div[data-testid="stMarkdownContainer"] p {
            width: 100% !important;
            margin: 0 !important;
            text-align: left !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    page = render_sidebar(
        authenticator=authenticator,
        user_record=user_record,
    )

    st.title(page)

    render_page(page)


if __name__ == "__main__":
    main()