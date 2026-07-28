from pathlib import Path
import pandas as pd
import streamlit as st


def display_matching_results(rows: list[dict], filename: str, download_key: str) -> None:
    if not rows:
        st.warning("No matching results were generated.")
        return

    result_df = pd.DataFrame(rows)
    if "score" in result_df.columns:
        result_df["score"] = pd.to_numeric(result_df["score"], errors="coerce").fillna(0)
        result_df = result_df.sort_values("score", ascending=False)

    st.success("Matching completed.")
    st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "candidate_id": None,
            "job_id": None,
            "candidate_name": st.column_config.TextColumn("Candidate", width="medium"),
            "job_title": st.column_config.TextColumn("Job", width="medium"),
            "match_method": st.column_config.TextColumn("Method", width="small"),
            "score": st.column_config.NumberColumn("Overall Score", min_value=0, max_value=100, format="%.1f"),
            "skill_score": st.column_config.NumberColumn("Skill Score", min_value=0, max_value=100, format="%.1f"),
            "experience_score": st.column_config.NumberColumn("Experience Score", min_value=0, max_value=100, format="%.1f"),
            "education_score": st.column_config.NumberColumn("Education Score", min_value=0, max_value=100, format="%.1f"),
            "location_score": st.column_config.NumberColumn("Location Score", min_value=0, max_value=100, format="%.1f"),
            "matched_skills": st.column_config.TextColumn("Matched Skills", width="large"),
            "missing_required_skills": st.column_config.TextColumn("Missing Required Skills", width="large"),
            "recommendation": st.column_config.TextColumn("Recommendation", width="medium"),
            "strengths": st.column_config.TextColumn("Strengths", width="large"),
            "concerns": st.column_config.TextColumn("Concerns", width="large"),
        },
    )

    output_path = Path("outputs") / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_excel(output_path, index=False)

    with open(output_path, "rb") as file:
        st.download_button(
            "Download Matching Results",
            data=file,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=download_key,
        )
