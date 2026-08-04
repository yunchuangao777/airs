from __future__ import annotations

import streamlit as st

from services.permission_service import has_permission, require_permission

from components.interview.interview_session_runner import (
    render_interview_session_runner,
)
from services.hiring_service import (
    build_hiring_dataset,
)
from services.interview_evaluation_service import (
    get_or_create_evaluation_template,
)
from services.interview_package_service import (
    load_interview_package,
)
from services.interview_question_service import (
    get_or_create_question_set,
)
from services.interview_service import (
    get_interview_candidates_for_job,
    get_interview_jobs,
)
from services.interview_session_service import (
    build_candidate_interview_link,
    create_interview_session,
    find_sessions_for_candidate_job,
    load_interview_session,
)
from components.interview.interview_session_evaluation import (
    render_interview_session_evaluation,
)

INTERVIEW_MODE_LABELS = {
    "recruiter_led": "Recruiter-led",
    "candidate_async": "Candidate Self-service",
    "ai_chat": "AI Chat",
    "ai_voice": "AI Voice",
}

AVAILABLE_INTERVIEW_MODES = [
    "recruiter_led",
    "ai_chat",
]


def render_candidate_interview_link(session) -> None:
    """Display the full public interview link for AI Chat sessions."""
    interview_mode = str(
        getattr(session, "interview_mode", "") or ""
    )
    if interview_mode != "ai_chat":
        return

    token = str(
        getattr(session, "candidate_access_token", "") or ""
    ).strip()
    access_enabled = bool(
        getattr(session, "candidate_access_enabled", False)
    )

    st.subheader("Candidate Interview Link")

    if not token:
        st.warning(
            "This AI Chat session does not have a candidate access token."
        )
        return

    candidate_link = build_candidate_interview_link(token)

    if not candidate_link:
        st.warning(
            "The candidate interview link could not be generated."
        )
        return

    if access_enabled:
        st.success(
            "The public interview link is ready for testing "
            "or sending to the candidate."
        )
    else:
        st.warning(
            "The public link exists, but candidate access is disabled."
        )

    st.text_input(
        "Full Public Interview Link",
        value=candidate_link,
        key=f"candidate_interview_link_{session.session_id}",
        help=(
            "Copy this URL or open it in another browser or "
            "incognito window for testing."
        ),
    )

    st.link_button(
        "Open Public Interview",
        candidate_link,
        use_container_width=True,
        disabled=not access_enabled,
    )


def render_interview_session_page() -> None:
    st.title("Interview Session")

    st.caption(
        "Create and manage recruiter-led or text-based AI interviews "
        "using the approved Interview Prep package."
    )

    dataset = build_hiring_dataset()

    jobs = get_interview_jobs(dataset)

    if not jobs:
        st.info(
            "No jobs currently have interview-eligible "
            "candidates."
        )
        return

    job_lookup = {
        job["job_id"]: job
        for job in jobs
    }

    selected_job_id = st.selectbox(
        "Job",
        options=list(job_lookup.keys()),
        format_func=lambda job_id: (
            job_lookup[job_id].get(
                "job_title",
                job_id,
            )
        ),
        key="interview_session_job",
    )

    candidates = get_interview_candidates_for_job(
        job_id=selected_job_id,
        dataset=dataset,
    )

    if not candidates:
        st.info(
            "No interview-eligible candidates were found "
            "for this job."
        )
        return

    candidate_lookup = {
        candidate["candidate_id"]: candidate
        for candidate in candidates
    }

    selected_candidate_id = st.selectbox(
        "Candidate",
        options=list(candidate_lookup.keys()),
        format_func=lambda candidate_id: (
            candidate_lookup[
                candidate_id
            ].get(
                "candidate_name",
                candidate_id,
            )
        ),
        key="interview_session_candidate",
    )

    package = load_interview_package(
        candidate_id=selected_candidate_id,
        job_id=selected_job_id,
    )

    if package is None:
        st.warning(
            "No interview package exists for this "
            "candidate and job. Complete Interview Prep "
            "first."
        )
        return

    question_set = get_or_create_question_set(
        package
    )

    evaluation_template = (
        get_or_create_evaluation_template(
            package
        )
    )

    sessions = find_sessions_for_candidate_job(
        candidate_id=selected_candidate_id,
        job_id=selected_job_id,
    )

    default_round = (
        max(
            (
                session.interview_round
                for session in sessions
            ),
            default=0,
        )
        + 1
    )

    with st.expander(
        "New Session Settings",
        expanded=not bool(sessions),
    ):
        setting_col1, setting_col2 = st.columns(
            [1, 2]
        )

        with setting_col1:
            interview_round = st.number_input(
                "Interview Round",
                min_value=1,
                step=1,
                value=default_round,
                key=(
                    f"new_session_round_"
                    f"{selected_job_id}_"
                    f"{selected_candidate_id}"
                ),
            )

        with setting_col2:
            interview_stage = st.text_input(
                "Interview Stage",
                value=(
                    "Recruiter Screening"
                    if default_round == 1
                    else f"Interview Round {default_round}"
                ),
                placeholder=(
                    "For example: Technical Interview"
                ),
                key=(
                    f"new_session_stage_"
                    f"{selected_job_id}_"
                    f"{selected_candidate_id}"
                ),
            )

        interview_mode = st.selectbox(
            "Interview Mode",
            options=AVAILABLE_INTERVIEW_MODES,
            format_func=lambda value: (
                INTERVIEW_MODE_LABELS.get(
                    value,
                    value.replace("_", " ").title(),
                )
            ),
            key=(
                f"new_session_mode_"
                f"{selected_job_id}_"
                f"{selected_candidate_id}"
            ),
        )

        st.caption(
            "These settings apply only when a new "
            "interview session is created."
        )

    st.divider()

    selected_session = None

    if sessions:

        session_options = {
            session.session_id: session
            for session in sessions
        }

        session_ids = list(session_options.keys())

        # A newly created session is selected on the next rerun,
        # before the selectbox is instantiated.
        pending_session_id = st.session_state.pop(
            "pending_selected_interview_session",
            None,
        )

        if (
            pending_session_id
            and pending_session_id in session_options
        ):
            st.session_state[
                "selected_interview_session"
            ] = pending_session_id

        # Protect against an old session ID remaining in state.
        current_selected_id = st.session_state.get(
            "selected_interview_session"
        )

        if current_selected_id not in session_options:
            st.session_state[
                "selected_interview_session"
            ] = session_ids[0]

        selected_session_id = st.selectbox(
            "Interview Session",
            options=session_ids,
            format_func=lambda session_id: (
                f"Round "
                f"{session_options[session_id].interview_round}"
                f" · "
                f"{session_options[session_id].interview_stage}"
                f" · "
                f"{session_options[session_id].status.replace('_', ' ').title()}"
            ),
            key="selected_interview_session",
        )

        selected_session = session_options[
            selected_session_id
        ]

        create_col, info_col = st.columns(
            [1, 2]
        )

        with create_col:
            can_create_session = has_permission(
                "interview.create"
            )
            create_new_clicked = st.button(
                "Create New Session",
                use_container_width=True,
                disabled=not can_create_session,
            )

        with info_col:
            st.caption(
                "Creating a new session takes a new "
                "snapshot of the currently approved "
                "questions and evaluation template."
            )

        if create_new_clicked:
            require_permission("interview.create")
            try:

                new_session = create_interview_session(
                    package=package,
                    question_set=question_set,
                    evaluation_template=evaluation_template,
                    interview_round=int(interview_round),
                    interview_stage=interview_stage,
                    interview_mode=interview_mode,
                )

                candidate_link = build_candidate_interview_link(
                    new_session.candidate_access_token
                )

                st.session_state[
                    "new_candidate_interview_link"
                ] = candidate_link
                

                st.session_state[
                    "pending_selected_interview_session"
                ] = new_session.session_id

                st.session_state[
                    "interview_session_message"
                ] = "A new interview session was created."

                st.rerun()

            except Exception as exc:
                st.error(
                    f"Unable to create session: {exc}"
                )

                return

    else:
        st.info(
            "No interview session has been created for "
            "this candidate and job."
        )

        can_create_session = has_permission(
            "interview.create"
        )

        if st.button(
            "Create Interview Session",
            type="primary",
            use_container_width=True,
            disabled=not can_create_session,
        ):
            require_permission("interview.create")
            try:

                new_session = create_interview_session(
                    package=package,
                    question_set=question_set,
                    evaluation_template=evaluation_template,
                    interview_round=int(interview_round),
                    interview_stage=interview_stage,
                    interview_mode=interview_mode,
                )

                candidate_link = build_candidate_interview_link(
                    new_session.candidate_access_token
                )

                st.session_state[
                    "new_candidate_interview_link"
                ] = candidate_link

                st.session_state[
                    "pending_selected_interview_session"
                ] = new_session.session_id

                st.session_state[
                    "interview_session_message"
                ] = "The interview session was created."

                st.rerun()

            except Exception as exc:
                st.error(
                    f"Unable to create session: {exc}"
                )

                return

    if selected_session is None:
        return

    current_session = load_interview_session(
        selected_session.session_id
    )

    if current_session is None:
        st.error(
            "The selected interview session could not "
            "be loaded."
        )
        return

    session_message = st.session_state.pop(
        "interview_session_message",
        "",
    )

    if session_message:
        st.success(session_message)

    st.divider()

    render_candidate_interview_link(
        current_session
    )

    st.divider()

    session_tab, evaluation_tab = st.tabs(
        [
            "Interview Record",
            "Evaluation",
        ]
    )

    with session_tab:
        render_interview_session_runner(
            current_session
        )

    with evaluation_tab:
        render_interview_session_evaluation(
            current_session
        )