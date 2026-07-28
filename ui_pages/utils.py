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
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(f"**Job title:** {selected_job.get('job_title') or 'Not available'}")
        st.write(f"**Company:** {selected_job.get('company') or 'Not available'}")

    with col2:
        st.write(f"**Location:** {selected_job.get('location') or 'Not available'}")
        required_years = selected_job.get("required_experience_years")
        experience_text = f"{required_years} years" if required_years is not None else "Not specified"
        st.write(f"**Required experience:** {experience_text}")

    with col3:
        required_skills = selected_job.get("required_skills", [])
        preferred_skills = selected_job.get("preferred_skills", [])
        st.write(f"**Required skills:** {', '.join(required_skills) if required_skills else 'None'}")
        st.write(f"**Preferred skills:** {', '.join(preferred_skills) if preferred_skills else 'None'}")


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
