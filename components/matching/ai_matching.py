import streamlit as st

from components.matching.application_selector import render_candidate_application_selection
from components.matching.results import display_matching_results
from components.matching.utils import build_result_row, result_state_key
from job_matcher import match_candidate_to_job
from match_saver import save_match_result


def render_ai_matching(candidates: list[dict], selected_job: dict) -> None:
    st.markdown("### AI Matching")
    st.caption(
        "AI Matching evaluates the complete candidate profile "
        "against the selected job description."
    )

    job_id = selected_job.get("job_id")
    state_key = result_state_key("ai", job_id)

    if st.button("Run AI Matching", type="primary", key=f"run_ai_matching_{job_id}"):
        rows = []
        progress = st.progress(0)
        status = st.empty()

        for index, candidate in enumerate(candidates):
            candidate_name = (
                candidate.get("name")
                or candidate.get("source_filename")
                or "Unknown Candidate"
            )
            status.info(f"AI matching: {candidate_name}")

            try:
                result = match_candidate_to_job(candidate, selected_job)
                result.match_method = "ai"
                save_match_result(result)
                rows.append(build_result_row(result))
            except Exception as exc:
                rows.append({
                    "candidate_id": candidate.get("candidate_id"),
                    "candidate_name": candidate.get("name"),
                    "job_id": job_id,
                    "job_title": selected_job.get("job_title"),
                    "match_method": "ai",
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
            f"ai_matching_results_{job_id}.xlsx",
            f"download_ai_results_{job_id}",
        )
        render_candidate_application_selection(
            saved_rows,
            selected_job,
            f"ai_matching_{job_id}",
        )
