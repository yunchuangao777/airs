import pandas as pd
import streamlit as st

from match_loader import load_matches_by_candidate
from utils.formatters import format_experience_years


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
