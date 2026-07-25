import streamlit as st

from interview_prep import generate_interview_prep
from interview_saver import save_interview_prep
from match_loader import (
    get_ranked_matches_by_job,
    load_all_jobs,
    load_candidate_by_id,
)


def render_interview_prep():

    # st.header("Interview Prep")

    jobs = load_all_jobs()

    if not jobs:
        st.warning(
            "No jobs found. Please create a job description first."
        )
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
        "Select job",
        list(job_options.keys()),
        key="interview_job_select",
    )

    selected_job = job_options[selected_job_label]
    job_id = selected_job.get("job_id")

    min_score = st.slider(
        "Minimum match score",
        min_value=0,
        max_value=100,
        value=70,
        step=5,
    )

    matches = get_ranked_matches_by_job(
        job_id=job_id,
        min_score=min_score,
    )

    if not matches:
        st.warning(
            "No matching results found for this job. "
            "Please run Job Matching first."
        )
        return

    st.subheader("Matched Candidates")

    match_rows = [
        {
            "candidate_name": match.get("candidate_name"),
            "score": match.get("score"),
            "recommendation": match.get("recommendation"),
            "matched_skills": ", ".join(
                match.get("matched_skills", [])
            ),
            "missing_required_skills": ", ".join(
                match.get("missing_required_skills", [])
            ),
            "candidate_id": match.get("candidate_id"),
        }
        for match in matches
    ]

    st.dataframe(match_rows, use_container_width=True)

    match_options = {
        (
            f"{match.get('candidate_name', 'Unknown')} | "
            f"Score: {match.get('score')} | "
            f"{match.get('candidate_id')}"
        ): match
        for match in matches
    }

    selected_match_label = st.selectbox(
        "Select candidate for interview prep",
        list(match_options.keys()),
        key="interview_match_select",
    )

    selected_match = match_options[selected_match_label]
    candidate = load_candidate_by_id(
        selected_match.get("candidate_id")
    )

    if candidate is None:
        st.error("Candidate JSON not found for the selected match.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Candidate")
        st.json(
            {
                "candidate_id": candidate.get("candidate_id"),
                "name": candidate.get("name"),
                "email": candidate.get("email"),
                "skills": candidate.get("skills"),
                "total_years_experience": candidate.get(
                    "total_years_experience"
                ),
            }
        )

    with col2:
        st.subheader("Job")
        st.json(
            {
                "job_id": selected_job.get("job_id"),
                "job_title": selected_job.get("job_title"),
                "company": selected_job.get("company"),
                "required_skills": selected_job.get(
                    "required_skills"
                ),
                "preferred_skills": selected_job.get(
                    "preferred_skills"
                ),
            }
        )

    with col3:
        st.subheader("Match Result")
        st.json(
            {
                "score": selected_match.get("score"),
                "matched_skills": selected_match.get(
                    "matched_skills"
                ),
                "missing_required_skills": selected_match.get(
                    "missing_required_skills"
                ),
                "strengths": selected_match.get("strengths"),
                "concerns": selected_match.get("concerns"),
                "recommendation": selected_match.get(
                    "recommendation"
                ),
            }
        )

    if st.button("Generate Interview Prep"):
        with st.spinner("Generating interview prep..."):
            prep = generate_interview_prep(
                candidate=candidate,
                job=selected_job,
                match_result=selected_match,
            )
            path = save_interview_prep(prep)

        st.success(f"Interview prep saved: {path}")

        st.subheader("Candidate Summary")
        st.write(prep.candidate_summary)

        st.subheader("Role-Fit Summary")
        st.write(prep.role_fit_summary)

        st.subheader("Key Strengths")
        for item in prep.key_strengths:
            st.write(f"- {item}")

        st.subheader("Key Concerns")
        for item in prep.key_concerns:
            st.write(f"- {item}")

        st.subheader("Interview Focus Areas")
        for item in prep.interview_focus_areas:
            st.write(f"- {item}")
