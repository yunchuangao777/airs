import html

import streamlit as st


def text_to_list(value: str) -> list[str]:
    if not value:
        return []
    results = []
    for line in value.splitlines():
        cleaned = line.strip().lstrip("-•").strip()
        if cleaned:
            results.append(cleaned)
    return results


def create_job_label(job: dict) -> str:
    job_title = job.get("job_title") or "Untitled Job"
    company = job.get("company") or ""
    return f"{job_title} — {company}" if company else job_title


def display_selected_job(selected_job: dict) -> None:
    st.markdown("### Selected Job")

    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.write(
            f"**Job title:** "
            f"{selected_job.get('job_title') or 'Not available'}"
        )
        st.write(
            f"**Company:** "
            f"{selected_job.get('company') or 'Not available'}"
        )

    with info_col2:
        st.write(
            f"**Location:** "
            f"{selected_job.get('location') or 'Not available'}"
        )

        required_years = selected_job.get(
            "required_experience_years"
        )
        experience_text = (
            f"{required_years} years"
            if required_years is not None
            else "Not specified"
        )

        st.write(
            f"**Required experience:** {experience_text}"
        )

    required_skills = selected_job.get(
        "required_skills",
        [],
    )
    preferred_skills = selected_job.get(
        "preferred_skills",
        [],
    )

    def render_skill_box(
        title: str,
        skills: list[str],
    ) -> None:
        if skills:
            items_html = "".join(
                (
                    "<li style='margin-bottom:0.35rem;'>"
                    f"{html.escape(str(skill))}"
                    "</li>"
                )
                for skill in skills
            )
        else:
            items_html = (
                "<div style='opacity:0.75;'>None</div>"
            )

        st.markdown(
            f"""
            <div style="
                margin-top: 0.25rem;
                margin-bottom: 0.5rem;
            ">
                <div style="
                    font-weight: 600;
                    margin-bottom: 0.4rem;
                ">
                    {html.escape(title)}
                </div>
                <div style="
                    height: 130px;
                    overflow-y: auto;
                    padding: 0.75rem 0.9rem;
                    border: 1px solid rgba(128, 128, 128, 0.35);
                    border-radius: 0.5rem;
                    background: rgba(128, 128, 128, 0.06);
                    color: inherit;
                ">
                    <ul style="
                        margin: 0;
                        padding-left: 1.2rem;
                    ">
                        {items_html}
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    skill_col1, skill_col2 = st.columns(2)

    with skill_col1:
        render_skill_box(
            "Required skills",
            required_skills,
        )

    with skill_col2:
        render_skill_box(
            "Preferred skills",
            preferred_skills,
        )


def build_result_row(result) -> dict:
    return {
        "candidate_id": result.candidate_id,
        "candidate_name": result.candidate_name,
        "job_id": result.job_id,
        "job_title": result.job_title,
        "match_method": result.match_method,
        "score": result.score,
        "skill_score": result.skill_score,
        "experience_score": result.experience_score,
        "education_score": result.education_score,
        "location_score": result.location_score,
        "matched_skills": ", ".join(result.matched_skills),
        "missing_required_skills": ", ".join(result.missing_required_skills),
        "recommendation": result.recommendation,
        "strengths": "; ".join(result.strengths),
        "concerns": "; ".join(result.concerns),
    }


def result_state_key(method: str, job_id: str) -> str:
    return f"latest_{method}_match_rows_{job_id}"