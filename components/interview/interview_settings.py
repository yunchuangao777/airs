from __future__ import annotations

import streamlit as st


INTERVIEW_TYPES = {
    "Recruiter Screening": "recruiter_screening",
    "Hiring Manager Interview": "hiring_manager",
    "Technical Interview": "technical",
    "Behavioral Interview": "behavioral",
    "Final Interview": "final",
}


DIFFICULTY_LEVELS = {
    "Standard": "standard",
    "Advanced": "advanced",
}


DURATION_OPTIONS = [
    30,
    45,
    60,
    90,
]


QUESTION_COUNT_OPTIONS = [
    5,
    6,
    8,
    10,
    12,
    15,
]


DEFAULT_FOCUS_AREAS = [
    "Relevant Experience",
    "Technical Skills",
    "Problem Solving",
    "Communication",
    "Leadership",
    "Teamwork",
    "Motivation",
    "Culture and Work Style",
]


def parse_custom_focus_areas(
    value: str,
) -> list[str]:
    """
    Convert comma-separated or line-separated text
    into a clean list of focus areas.
    """
    if not value:
        return []

    normalized = value.replace(",", "\n")

    results: list[str] = []

    for line in normalized.splitlines():
        cleaned = line.strip().lstrip("-•").strip()

        if cleaned and cleaned not in results:
            results.append(cleaned)

    return results


def build_settings_key(
    context: dict,
) -> str:
    """
    Create a candidate-job-specific session-state key.
    """
    candidate_id = context.get("candidate_id") or "candidate"
    job_id = context.get("job_id") or "job"

    return f"{job_id}_{candidate_id}"


def render_interview_settings(
    context: dict,
    package_exists: bool = False,
) -> dict | None:
    """
    Render interview preparation settings.

    Returns the selected settings only when the recruiter
    clicks Generate or Regenerate Interview Package.
    Otherwise returns None.
    """
    settings_key = build_settings_key(context)

    candidate_name = (
        context.get("candidate_name")
        or "Unknown Candidate"
    )

    job_title = (
        context.get("job_title")
        or "Untitled Job"
    )

    company = context.get("company") or ""

    job_label = (
        f"{job_title} — {company}"
        if company
        else job_title
    )

    st.markdown("### Interview Preparation")

    st.caption(
        f"Prepare an interview package for "
        f"**{candidate_name}** and **{job_label}**."
    )

    with st.container(border=True):
        st.markdown("#### Interview Settings")

        row1_col1, row1_col2 = st.columns(2)

        with row1_col1:
            selected_type_label = st.selectbox(
                "Interview type",
                options=list(
                    INTERVIEW_TYPES.keys()
                ),
                index=1,
                key=(
                    f"interview_type_"
                    f"{settings_key}"
                ),
            )

        with row1_col2:
            selected_difficulty_label = st.selectbox(
                "Difficulty",
                options=list(
                    DIFFICULTY_LEVELS.keys()
                ),
                index=0,
                key=(
                    f"interview_difficulty_"
                    f"{settings_key}"
                ),
            )

        row2_col1, row2_col2 = st.columns(2)

        with row2_col1:
            duration_minutes = st.selectbox(
                "Interview duration",
                options=DURATION_OPTIONS,
                index=1,
                format_func=lambda value: (
                    f"{value} minutes"
                ),
                key=(
                    f"interview_duration_"
                    f"{settings_key}"
                ),
            )

        with row2_col2:
            question_count = st.selectbox(
                "Number of main questions",
                options=QUESTION_COUNT_OPTIONS,
                index=2,
                key=(
                    f"interview_question_count_"
                    f"{settings_key}"
                ),
            )

        selected_focus_areas = st.multiselect(
            "Focus areas",
            options=DEFAULT_FOCUS_AREAS,
            default=[
                "Relevant Experience",
                "Technical Skills",
                "Problem Solving",
                "Communication",
            ],
            key=(
                f"interview_focus_areas_"
                f"{settings_key}"
            ),
        )

        include_custom_focus = st.checkbox(
            "Add custom focus areas",
            value=False,
            key=(
                f"interview_add_custom_focus_"
                f"{settings_key}"
            ),
        )

        custom_focus_text = ""

        if include_custom_focus:
            custom_focus_text = st.text_area(
                "Custom focus areas",
                placeholder=(
                    "Enter one area per line or separate "
                    "areas with commas.\n"
                    "Example:\n"
                    "Month-end close ownership\n"
                    "Stakeholder management"
                ),
                height=110,
                key=(
                    f"interview_custom_focus_"
                    f"{settings_key}"
                ),
            )

        recruiter_instructions = st.text_area(
            "Additional recruiter instructions",
            placeholder=(
                "Optional guidance for the AI.\n"
                "Example: Focus on leadership experience "
                "and verify the candidate's direct ownership "
                "of financial reporting."
            ),
            height=120,
            key=(
                f"interview_recruiter_instructions_"
                f"{settings_key}"
            ),
        )

    custom_focus_areas = parse_custom_focus_areas(
        custom_focus_text
    )

    all_focus_areas = list(
        dict.fromkeys(
            [
                *selected_focus_areas,
                *custom_focus_areas,
            ]
        )
    )

    st.markdown("#### Package Preview")

    preview_col1, preview_col2, preview_col3 = (
        st.columns(3)
    )

    with preview_col1:
        st.metric(
            "Duration",
            f"{duration_minutes} min",
        )

    with preview_col2:
        st.metric(
            "Main Questions",
            question_count,
        )

    with preview_col3:
        st.metric(
            "Focus Areas",
            len(all_focus_areas),
        )

    if all_focus_areas:
        st.caption(
            "Focus: " + ", ".join(all_focus_areas)
        )
    else:
        st.warning(
            "Select at least one focus area before "
            "generating the package."
        )

    button_label = (
        "Regenerate Interview Package"
        if package_exists
        else "Generate Interview Package"
    )

    generate_clicked = st.button(
        button_label,
        type="primary",
        use_container_width=True,
        disabled=not all_focus_areas,
        key=(
            f"generate_interview_package_"
            f"{settings_key}"
        ),
    )

    if not generate_clicked:
        return None

    settings = {
        "candidate_id": context.get(
            "candidate_id"
        ),
        "job_id": context.get("job_id"),
        "application_id": context.get(
            "application_id"
        ),
        "interview_type": INTERVIEW_TYPES[
            selected_type_label
        ],
        "interview_type_label": (
            selected_type_label
        ),
        "difficulty": DIFFICULTY_LEVELS[
            selected_difficulty_label
        ],
        "difficulty_label": (
            selected_difficulty_label
        ),
        "duration_minutes": duration_minutes,
        "question_count": question_count,
        "focus_areas": all_focus_areas,
        "recruiter_instructions": (
            recruiter_instructions.strip()
        ),
    }

    st.session_state[
        f"interview_settings_{settings_key}"
    ] = settings

    return settings