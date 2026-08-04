from __future__ import annotations

import streamlit as st

from services.permission_service import has_permission, require_permission

from application_service import (
    update_application_status,
)
from schema import CandidateStatus
from services.hiring_service import STATUS_LABELS
from components.hiring.candidate_timeline import (
    render_candidate_timeline,
)

EDITABLE_STATUSES = [
    CandidateStatus.APPLIED,
    CandidateStatus.REVIEW,
    CandidateStatus.INTERVIEW,
    CandidateStatus.OFFER,
    CandidateStatus.ACCEPTED,
    CandidateStatus.REJECTED,
    CandidateStatus.ARCHIVED,
]


def format_status(status: CandidateStatus) -> str:
    """
    Convert a stored status into a friendly UI label.
    """
    return STATUS_LABELS.get(
        status.value,
        status.value.title(),
    )


def render_candidate_basic_details(
    application_row: dict,
) -> None:
    """
    Display the candidate and application details.
    """
    candidate = application_row.get(
        "candidate",
        {},
    )

    candidate_name = (
        application_row.get("candidate_name")
        or candidate.get("name")
        or "Unknown Candidate"
    )

    st.markdown(f"### {candidate_name}")

    info_col1, info_col2, info_col3 = st.columns(3)

    with info_col1:
        st.caption("Email")
        st.write(
            application_row.get("candidate_email")
            or candidate.get("email")
            or "Not available"
        )

    with info_col2:
        st.caption("Phone")
        st.write(
            candidate.get("phone")
            or "Not available"
        )

    with info_col3:
        st.caption("Location")
        st.write(
            candidate.get("location")
            or "Not available"
        )

    info_col4, info_col5, info_col6 = st.columns(3)

    with info_col4:
        st.caption("Experience")
        experience = candidate.get(
            "total_years_experience"
        )

        st.write(
            f"{experience} years"
            if experience is not None
            else "Not available"
        )

    with info_col5:
        st.caption("Match Score")
        score = float(
            application_row.get(
                "match_score",
                0,
            )
            or 0
        )

        st.write(f"{score:.1f}")

    with info_col6:
        st.caption("Match Method")
        st.write(
            application_row.get("match_method")
            or "Not available"
        )

    summary = candidate.get("summary")

    if summary:
        st.markdown("#### Professional Summary")
        st.write(summary)

    skills = candidate.get("skills", [])

    if skills:
        st.markdown("#### Skills")
        st.write(
            ", ".join(
                str(skill)
                for skill in skills
            )
        )

    education = candidate.get(
        "education",
        [],
    )

    if education:
        st.markdown("#### Education")

        for item in education:
            if hasattr(item, "model_dump"):
                item = item.model_dump()

            if not isinstance(item, dict):
                continue

            education_parts = [
                item.get("degree"),
                item.get("major"),
                item.get("school"),
                item.get("graduation_year"),
            ]

            education_text = " | ".join(
                str(value)
                for value in education_parts
                if value
            )

            if education_text:
                st.write(f"- {education_text}")

    work_experience = candidate.get(
        "work_experience",
        [],
    )

    if work_experience:
        st.markdown("#### Work Experience")

        for item in work_experience:
            if hasattr(item, "model_dump"):
                item = item.model_dump()

            if not isinstance(item, dict):
                continue

            title = (
                item.get("title")
                or "Unknown position"
            )

            company = (
                item.get("company")
                or "Unknown company"
            )

            st.markdown(
                f"**{title} — {company}**"
            )

            dates = " to ".join(
                str(value)
                for value in [
                    item.get("start_date"),
                    item.get("end_date"),
                ]
                if value
            )

            if dates:
                st.caption(dates)

            description = item.get(
                "description"
            )

            if description:
                st.write(description)


def render_status_history(
    application_row: dict,
) -> None:
    """
    Display the existing application status history.
    """
    application = application_row.get(
        "application",
        {},
    )

    status_history = application.get(
        "status_history",
        [],
    )

    if not status_history:
        st.info("No status history is available.")
        return

    for history_item in reversed(status_history):
        if hasattr(history_item, "model_dump"):
            history_item = history_item.model_dump()

        if not isinstance(history_item, dict):
            continue

        status = history_item.get(
            "status",
            "none",
        )

        changed_time = history_item.get(
            "changed_time",
            "",
        )

        note = history_item.get("note")

        status_label = STATUS_LABELS.get(
            status,
            str(status).title(),
        )

        st.markdown(
            f"**{status_label}**"
        )

        if changed_time:
            st.caption(str(changed_time))

        if note:
            st.write(note)

        st.divider()


@st.dialog(
    "Candidate Application",
    width="large",
)
def show_candidate_status_dialog(
    application_row: dict,
) -> None:
    """
    Display candidate details and allow status updates.
    """
    candidate_id = application_row.get(
        "candidate_id"
    )

    job_id = application_row.get("job_id")

    if not candidate_id or not job_id:
        st.error(
            "The candidate or job ID is missing."
        )
        return

    job_title = (
        application_row.get("job_title")
        or "Untitled Job"
    )

    company = (
        application_row.get("company")
        or ""
    )

    job_label = (
        f"{job_title} — {company}"
        if company
        else job_title
    )

    st.caption(f"Application for: {job_label}")

    details_tab, status_tab, timeline_tab = st.tabs(
        [
            "Candidate Details",
            "Update Status",
            "Timeline",
        ]
    )

    with details_tab:
        render_candidate_basic_details(
            application_row
        )

    with status_tab:
        current_status_value = (
            application_row.get("status")
            or CandidateStatus.NONE.value
        )

        try:
            current_status = CandidateStatus(
                current_status_value
            )
        except ValueError:
            current_status = CandidateStatus.NONE

        st.markdown("#### Current Status")

        st.info(
            STATUS_LABELS.get(
                current_status.value,
                current_status.value.title(),
            )
        )

        can_update_status = has_permission(
            "application.update_status"
        )

        status_options = EDITABLE_STATUSES

        default_index = 0

        if current_status in status_options:
            default_index = status_options.index(
                current_status
            )

        selected_status = st.selectbox(
            "New status",
            options=status_options,
            index=default_index,
            format_func=format_status,
            key=(
                f"hiring_status_"
                f"{job_id}_{candidate_id}"
            ),
            disabled=not can_update_status,
        )

        status_note = st.text_area(
            "Status note",
            placeholder=(
                "Optional reason, interview result, "
                "offer note, or recruiter comment"
            ),
            height=110,
            key=(
                f"hiring_status_note_"
                f"{job_id}_{candidate_id}"
            ),
            disabled=not can_update_status,
        )

        status_changed = (
            selected_status != current_status
        )

        if not status_changed:
            st.caption(
                "Select a different status to enable "
                "the update button."
            )

        if st.button(
            "Update Status",
            type="primary",
            use_container_width=True,
            disabled=(
                not status_changed
                or not can_update_status
            ),
            key=(
                f"hiring_update_status_"
                f"{job_id}_{candidate_id}"
            ),
        ):
            require_permission(
                "application.update_status"
            )
            try:
                updated_application = (
                    update_application_status(
                        candidate_id=candidate_id,
                        job_id=job_id,
                        new_status=selected_status,
                        note=(
                            status_note.strip()
                            or "Updated from Hiring Management"
                        ),
                    )
                )

                candidate_name = (
                    application_row.get("candidate_name")
                    or "Candidate"
                )

                st.session_state[
                    "hiring_status_update_message"
                ] = (
                    f"{candidate_name} was updated to "
                    f"{format_status(selected_status)}."
                )

                # Incrementing this value makes the page reload
                # application data after the dialog closes.
                st.session_state[
                    "hiring_data_version"
                ] = (
                    st.session_state.get(
                        "hiring_data_version",
                        0,
                    )
                    + 1
                )

                st.rerun()

            except Exception as exc:
                st.error(
                    f"Unable to update status: {exc}"
                )

    with timeline_tab:
        render_candidate_timeline(
            application_row
        )