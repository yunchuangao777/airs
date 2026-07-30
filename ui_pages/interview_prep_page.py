from __future__ import annotations

import streamlit as st

from components.interview.interview_settings import (
    render_interview_settings,
)
from services.hiring_service import (
    build_hiring_dataset,
)
from services.interview_service import (
    build_interview_context,
    get_interview_candidates_for_job,
    get_interview_jobs,
)
from components.interview.interview_package_renderer import (
    render_interview_package,
)
from services.interview_package_service import (
    generate_interview_package,
    load_interview_package,
)
from components.interview.interview_questions import (
    render_interview_questions,
)
from components.interview.interview_question_editor import (
    render_interview_question_editor,
)
from components.interview.interview_evaluation_template import (
    render_interview_evaluation_template,
)

def create_job_label(job: dict) -> str:
    """
    Create a readable job label for the selector.
    """
    job_title = (
        job.get("job_title")
        or "Untitled Job"
    )

    company = job.get("company") or ""

    if company:
        return f"{job_title} — {company}"

    return job_title


def create_candidate_label(
    candidate_row: dict,
) -> str:
    """
    Create a readable candidate label for the selector.
    """
    candidate_name = (
        candidate_row.get("candidate_name")
        or "Unknown Candidate"
    )

    status = (
        candidate_row.get("status")
        or "none"
    ).title()

    score = float(
        candidate_row.get("match_score", 0)
        or 0
    )

    return (
        f"{candidate_name} | "
        f"{status} | Score: {score:.1f}"
    )


def render_interview_prep() -> None:
    """
    Render the Interview Prep page.
    """
    package_message = st.session_state.pop(
    "interview_package_message",
    None,
    )

    if package_message:
        st.success(package_message)
        
    dataset = build_hiring_dataset()

    interview_jobs = get_interview_jobs(
        dataset
    )

    if not interview_jobs:
        st.info(
            "No candidates are currently eligible "
            "for interview preparation."
        )
        return

    # =========================================================
    # Job selection
    # =========================================================
    job_options: dict[str, dict] = {}

    for job in interview_jobs:
        label = create_job_label(job)

        # Protect against duplicate labels.
        if label in job_options:
            label = (
                f"{label} "
                f"({job.get('job_id')})"
            )

        job_options[label] = job

    selected_job_label = st.selectbox(
        "Select job",
        options=list(job_options.keys()),
        key="interview_prep_job",
    )

    selected_job = job_options[
        selected_job_label
    ]

    selected_job_id = selected_job.get(
        "job_id"
    )

    if not selected_job_id:
        st.error(
            "The selected job does not have a valid job ID."
        )
        return

    # =========================================================
    # Candidate selection
    # =========================================================
    candidate_rows = (
        get_interview_candidates_for_job(
            job_id=selected_job_id,
            dataset=dataset,
        )
    )

    if not candidate_rows:
        st.info(
            "No eligible candidates are available "
            "for this job."
        )
        return

    candidate_options: dict[str, dict] = {}

    for candidate_row in candidate_rows:
        label = create_candidate_label(
            candidate_row
        )

        # Protect against duplicate names and scores.
        if label in candidate_options:
            label = (
                f"{label} "
                f"({candidate_row.get('candidate_id')})"
            )

        candidate_options[label] = candidate_row

    selected_candidate_label = st.selectbox(
        "Select candidate",
        options=list(candidate_options.keys()),
        key="interview_prep_candidate",
    )

    selected_candidate = candidate_options[
        selected_candidate_label
    ]

    selected_candidate_id = (
        selected_candidate.get("candidate_id")
    )

    if not selected_candidate_id:
        st.error(
            "The selected candidate does not have "
            "a valid candidate ID."
        )
        return

    # =========================================================
    # Build interview context
    # =========================================================
    context = build_interview_context(
        candidate_id=selected_candidate_id,
        job_id=selected_job_id,
        dataset=dataset,
    )

    if not context:
        st.error(
            "Unable to build the interview context."
        )
        return

    # =========================================================
    # Interview Prep workspace
    # =========================================================
    (
        overview_tab,
        preparation_tab,
        questions_tab,
        scorecard_tab,
    ) = st.tabs(
        [
            "Overview",
            "Preparation",
            "Questions",
            "Scorecard",
        ]
    )

    # ---------------------------------------------------------
    # Overview
    # ---------------------------------------------------------
    with overview_tab:

        package = load_interview_package(
            candidate_id=context["candidate_id"],
            job_id=context["job_id"],
        )

        if package is None:

            st.info(
                "Generate an interview package first."
            )

        else:

            render_interview_package(package)

        # st.caption(
            # "This temporary JSON view confirms that "
            # "candidate, job, application, and matching "
            # "information are loaded correctly."
        # )

        # st.json(context)

    # ---------------------------------------------------------
    # Preparation
    # ---------------------------------------------------------
    package = load_interview_package(
    candidate_id=context["candidate_id"],
    job_id=context["job_id"],
    )
    
    with preparation_tab:
        if package is not None:
            with st.container(border=True):
                st.markdown("### Existing Interview Package")

                info_col1, info_col2, info_col3 = st.columns(3)

                with info_col1:
                    st.caption("Created")
                    st.write(package.created_time)

                with info_col2:
                    st.caption("Last Updated")
                    st.write(package.updated_time)

                with info_col3:
                    st.caption("Model")
                    st.write(package.model_name)

                st.caption(
                    "Change the settings below and generate again "
                    "to replace the current package."
                )

        generated_settings = render_interview_settings(
            context=context,
            package_exists=package is not None,
        )

        if generated_settings:
            with st.spinner(
                "Generating the interview package..."
            ):
                try:
                    package = generate_interview_package(
                        context=context,
                        settings=generated_settings,
                        overwrite=True,
                    )

                    st.session_state[
                        "interview_package_message"
                    ] = (
                        f"Interview package for "
                        f"{package.candidate_name} was generated "
                        f"successfully."
                    )

                    st.rerun()

                except Exception as exc:
                    st.error(
                        f"Unable to generate interview package: {exc}"
                    )

    # ---------------------------------------------------------
    # Questions
    # ---------------------------------------------------------
    with questions_tab:
        if package is None:
            st.info(
                "Generate an interview package in the "
                "Preparation tab first."
            )
        else:
            render_interview_question_editor(
                package
            )

    # ---------------------------------------------------------
    # Evaluation
    # ---------------------------------------------------------
    with scorecard_tab:
        if package is None:
            st.info(
                "Generate an interview package in the "
                "Preparation tab first."
            )
        else:
            render_interview_evaluation_template(
                package
            )