from pathlib import Path

import pandas as pd
import streamlit as st

from job_matcher import match_candidate_to_job
from match_loader import load_all_candidates, load_all_jobs
from match_saver import save_match_result


def render_job_matching():
    st.header("Job Matching")

    candidates = load_all_candidates()
    jobs = load_all_jobs()

    if not candidates:
        st.warning("No candidates found. Please extract CVs first.")
        return

    if not jobs:
        st.warning("No jobs found. Please create a job description first.")
        return

    job_options = {
        (
            f"{job.get('job_title', 'Untitled Job')} | "
            f"{job.get('company', '')} | "
            f"{job.get('job_id', '')}"
        ): job
        for job in jobs
    }

    selected_job_label = st.selectbox(
        "Select a job",
        list(job_options.keys()),
    )
    selected_job = job_options[selected_job_label]

    st.subheader("Selected Job")
    st.json(
        {
            "job_id": selected_job.get("job_id"),
            "job_title": selected_job.get("job_title"),
            "company": selected_job.get("company"),
            "required_skills": selected_job.get("required_skills"),
            "preferred_skills": selected_job.get("preferred_skills"),
            "required_experience_years": selected_job.get(
                "required_experience_years"
            ),
        }
    )

    if st.button("Run Matching"):
        rows: list[dict] = []
        progress = st.progress(0)
        status = st.empty()

        for index, candidate in enumerate(candidates):
            display_name = (
                candidate.get("name")
                or candidate.get("source_filename")
            )
            status.info(f"Matching {display_name}")

            try:
                result = match_candidate_to_job(
                    candidate,
                    selected_job,
                )
                save_match_result(result)

                rows.append(
                    {
                        "candidate_id": result.candidate_id,
                        "candidate_name": result.candidate_name,
                        "job_id": result.job_id,
                        "job_title": result.job_title,
                        "score": result.score,
                        "matched_skills": ", ".join(
                            result.matched_skills
                        ),
                        "missing_required_skills": ", ".join(
                            result.missing_required_skills
                        ),
                        "recommendation": result.recommendation,
                        "strengths": "; ".join(result.strengths),
                        "concerns": "; ".join(result.concerns),
                    }
                )
            except Exception as exc:
                rows.append(
                    {
                        "candidate_id": candidate.get("candidate_id"),
                        "candidate_name": candidate.get("name"),
                        "job_id": selected_job.get("job_id"),
                        "job_title": selected_job.get("job_title"),
                        "score": 0,
                        "matched_skills": "",
                        "missing_required_skills": "",
                        "recommendation": "",
                        "strengths": "",
                        "concerns": f"Failed: {exc}",
                    }
                )

            progress.progress((index + 1) / len(candidates))

        status.empty()

        result_df = pd.DataFrame(rows).sort_values(
            "score",
            ascending=False,
        )

        st.success("Matching completed")
        st.dataframe(result_df, use_container_width=True)

        output_path = Path("outputs/matching_results.xlsx")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_excel(output_path, index=False)

        with open(output_path, "rb") as file:
            st.download_button(
                label="Download Matching Results",
                data=file,
                file_name="matching_results.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            )
