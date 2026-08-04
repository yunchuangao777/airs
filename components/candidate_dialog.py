import pandas as pd
import streamlit as st

from services.permission_service import has_permission, require_permission

from match_loader import load_matches_by_candidate
from utils.formatters import format_experience_years

from application_loader import (
    load_applications_by_candidate,
)
from application_service import (
    get_or_create_application,
    update_application_status,
)
from match_loader import load_all_jobs
from schema import CandidateStatus


@st.dialog("Candidate Details", width="large")
def show_candidate_details(candidate: dict):
    candidate_name = candidate.get("name") or "Unknown Candidate"
    st.subheader(candidate_name)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Contact")
        st.write(f"**Email:** {candidate.get('email') or 'Not available'}")
        st.write(f"**Phone:** {candidate.get('phone') or 'Not available'}")
        st.write(f"**Location:** {candidate.get('location') or 'Not available'}")
        st.write(
            f"**Candidate ID:** "
            f"{candidate.get('candidate_id') or 'Not available'}"
        )

    with col2:
        st.markdown("#### Source")
        st.write(
            f"**Filename:** "
            f"{candidate.get('source_filename') or 'Not available'}"
        )
        st.write(
            f"**Upload time:** "
            f"{candidate.get('upload_time') or 'Not available'}"
        )

        experience = format_experience_years(
            candidate.get("total_years_experience")
        )
        experience_text = f"{experience} years" if experience else "Not available"
        st.write(f"**Total experience:** {experience_text}")

    summary = candidate.get("summary")
    if summary:
        st.markdown("#### Professional Summary")
        st.write(summary)

    st.markdown("#### Skills")
    skills = candidate.get("skills", [])
    if skills:
        st.write(", ".join(skills))
    else:
        st.info("No skills extracted.")

    st.markdown("#### Education")
    education = candidate.get("education", [])

    if education:
        for item in education:
            school = item.get("school") or "Unknown school"
            degree = item.get("degree") or ""
            major = item.get("major") or ""
            graduation_year = item.get("graduation_year") or ""

            heading = " — ".join(
                value for value in [school, degree] if value
            )
            st.markdown(f"**{heading}**")

            details: list[str] = []
            if major:
                details.append(f"Major: {major}")
            if graduation_year:
                details.append(f"Graduation year: {graduation_year}")

            if details:
                st.write(" | ".join(details))
    else:
        st.info("No education information extracted.")

    st.markdown("#### Work Experience")
    work_experience = candidate.get("work_experience", [])

    if work_experience:
        for experience_item in work_experience:
            company = experience_item.get("company") or "Unknown company"
            title = experience_item.get("title") or "Unknown position"
            start_date = experience_item.get("start_date") or ""
            end_date = experience_item.get("end_date") or ""

            st.markdown(f"**{title} — {company}**")

            date_range = " to ".join(
                value for value in [start_date, end_date] if value
            )
            if date_range:
                st.caption(date_range)

            description = experience_item.get("description")
            if description:
                st.write(description)

            st.divider()
    else:
        st.info("No work experience extracted.")

    st.markdown("#### Match History")
    matches = load_matches_by_candidate(candidate.get("candidate_id"))

    if matches:
        matches = sorted(
            matches,
            key=lambda item: float(item.get("score", 0)),
            reverse=True,
        )

        match_rows = [
            {
                "Job": match.get("job_title") or "Untitled Job",
                "Score": match.get("score"),
                "Recommendation": match.get("recommendation") or "",
            }
            for match in matches
        ]

        st.dataframe(
            pd.DataFrame(match_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("This candidate has not been matched to a job yet.")

    raw_text = candidate.get("raw_text")
    if raw_text:
        with st.expander("View extracted CV text"):
            st.text_area(
                "CV text",
                value=raw_text,
                height=400,
                disabled=True,
                key=f"dialog_raw_text_{candidate.get('candidate_id')}",
            )

    st.markdown("#### Application Status")

    jobs = load_all_jobs()

    job_options = {
        (
            f"{job.get('job_title') or 'Untitled Job'}"
            + (
                f" — {job.get('company')}"
                if job.get("company")
                else ""
            )
        ): job
        for job in jobs
    }

    if not job_options:
        st.info("No jobs are available.")
    else:
        selected_job_label = st.selectbox(
            "Select job",
            list(job_options.keys()),
            key=f"status_job_{candidate.get('candidate_id')}",
        )

        selected_job = job_options[selected_job_label]

        application = get_or_create_application(
            candidate_id=candidate.get("candidate_id"),
            job_id=selected_job.get("job_id"),
        )

        status_values = [
            status.value
            for status in CandidateStatus
        ]

        current_index = status_values.index(
            application.status.value
        )

        can_update_status = has_permission(
            "application.update_status"
        )

        selected_status = st.selectbox(
            "Candidate status",
            options=status_values,
            index=current_index,
            key=(
                f"status_value_"
                f"{candidate.get('candidate_id')}_"
                f"{selected_job.get('job_id')}"
            ),
            disabled=not can_update_status,
        )

        status_note = st.text_input(
            "Status note",
            key=(
                f"status_note_"
                f"{candidate.get('candidate_id')}_"
                f"{selected_job.get('job_id')}"
            ),
            disabled=not can_update_status,
        )

        if st.button(
            "Update Status",
            key=(
                f"update_status_"
                f"{candidate.get('candidate_id')}_"
                f"{selected_job.get('job_id')}"
            ),
            disabled=not can_update_status,
        ):
            require_permission(
                "application.update_status"
            )
            update_application_status(
                candidate_id=candidate.get("candidate_id"),
                job_id=selected_job.get("job_id"),
                new_status=CandidateStatus(selected_status),
                note=status_note,
            )

            st.session_state["status_update_success"] = {
                "candidate_id": candidate.get("candidate_id"),
                "job_id": selected_job.get("job_id"),
                "status": selected_status,
            }

            st.rerun()

        # -----------------------------------------------------------
        success_info = st.session_state.get("status_update_success")

        if (
            success_info
            and success_info.get("candidate_id")
            == candidate.get("candidate_id")
            and success_info.get("job_id")
            == selected_job.get("job_id")
        ):
            st.success(
                f"The candidate status was updated to "
                f"**{success_info.get('status').title()}**."
            )

            if st.button(
                "OK",
                key=(
                    f"close_status_message_"
                    f"{candidate.get('candidate_id')}_"
                    f"{selected_job.get('job_id')}"
                ),
            ):
                del st.session_state["status_update_success"]
                st.rerun()