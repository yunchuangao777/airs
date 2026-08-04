import streamlit as st

from services.permission_service import has_permission, require_permission

from components.matching.application_selector import render_candidate_application_selection
from components.matching.results import display_matching_results
from components.matching.utils import build_result_row, result_state_key, text_to_list
from match_saver import save_match_result
from traditional_matcher import match_candidate_traditional


def render_traditional_matching(candidates: list[dict], selected_job: dict) -> None:
    st.markdown("### Rule Matching")
    st.caption(
        "Rule-basedl Matching uses fixed criteria and weights. "
    )

    job_id = selected_job.get("job_id")
    state_key = result_state_key("traditional", job_id)

    st.markdown("#### Matching Criteria")
    col1, col2 = st.columns(2)

    with col1:
        required_skills_text = st.text_area(
            "Required skills",
            value="\n".join(selected_job.get("required_skills", [])),
            height=180,
            key=f"traditional_required_skills_{job_id}",
        )
        preferred_skills_text = st.text_area(
            "Preferred skills",
            value="\n".join(selected_job.get("preferred_skills", [])),
            height=150,
            key=f"traditional_preferred_skills_{job_id}",
        )

    with col2:
        required_experience = st.number_input(
            "Minimum experience in years",
            min_value=0.0,
            value=float(selected_job.get("required_experience_years") or 0),
            step=1.0,
            key=f"traditional_experience_{job_id}",
        )
        education_keywords_text = st.text_area(
            "Education keywords",
            value="\n".join(selected_job.get("education_requirements", [])),
            height=150,
            key=f"traditional_education_{job_id}",
        )
        preferred_location = st.text_input(
            "Preferred location",
            value=selected_job.get("location") or "",
            key=f"traditional_location_{job_id}",
        )

    st.markdown("#### Matching Weights")
    w1, w2, w3, w4 = st.columns(4)

    with w1:
        skill_weight = st.number_input("Skills", 0, 100, 50, 5, key=f"traditional_skill_weight_{job_id}")
    with w2:
        experience_weight = st.number_input("Experience", 0, 100, 25, 5, key=f"traditional_experience_weight_{job_id}")
    with w3:
        education_weight = st.number_input("Education", 0, 100, 15, 5, key=f"traditional_education_weight_{job_id}")
    with w4:
        location_weight = st.number_input("Location", 0, 100, 10, 5, key=f"traditional_location_weight_{job_id}")

    total_weight = skill_weight + experience_weight + education_weight + location_weight

    if total_weight == 0:
        st.error("At least one matching weight must be greater than zero.")
    elif total_weight != 100:
        st.info(
            f"The weights currently total {total_weight}. "
            "They will be normalized automatically."
        )

    can_run_matching = has_permission("matching.run")

    if st.button(
        "Run Rule Matching",
        type="primary",
        disabled=(
            total_weight == 0
            or not can_run_matching
        ),
        key=f"run_traditional_matching_{job_id}",
    ):
        require_permission("matching.run")
        required_skills = text_to_list(required_skills_text)
        preferred_skills = text_to_list(preferred_skills_text)
        education_keywords = text_to_list(education_keywords_text)

        rows = []
        progress = st.progress(0)
        status = st.empty()

        for index, candidate in enumerate(candidates):
            candidate_name = (
                candidate.get("name")
                or candidate.get("source_filename")
                or "Unknown Candidate"
            )
            status.info(f"Traditional matching: {candidate_name}")

            try:
                result = match_candidate_traditional(
                    candidate=candidate,
                    job=selected_job,
                    required_skills=required_skills,
                    preferred_skills=preferred_skills,
                    required_experience_years=required_experience,
                    education_keywords=education_keywords,
                    preferred_location=preferred_location,
                    skill_weight=skill_weight,
                    experience_weight=experience_weight,
                    education_weight=education_weight,
                    location_weight=location_weight,
                )
                save_match_result(result)
                rows.append(build_result_row(result))
            except Exception as exc:
                rows.append({
                    "candidate_id": candidate.get("candidate_id"),
                    "candidate_name": candidate.get("name"),
                    "job_id": job_id,
                    "job_title": selected_job.get("job_title"),
                    "match_method": "traditional",
                    "score": 0,
                    "skill_score": None,
                    "experience_score": None,
                    "education_score": None,
                    "location_score": None,
                    "matched_skills": "",
                    "missing_required_skills": "",
                    "recommendation": "",
                    "strengths": "",
                    "concerns": f"Failed: {exc}",
                })

            progress.progress((index + 1) / len(candidates))

        status.empty()
        st.session_state[state_key] = rows

    saved_rows = st.session_state.get(state_key, [])
    if saved_rows:
        display_matching_results(
            saved_rows,
            f"traditional_matching_results_{job_id}.xlsx",
            f"download_traditional_results_{job_id}",
        )
        render_candidate_application_selection(
            saved_rows,
            selected_job,
            f"traditional_matching_{job_id}",
        )
