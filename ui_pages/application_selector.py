import pandas as pd
import streamlit as st

from application_loader import load_application
from application_service import add_candidate_as_applied_if_available
from schema import CandidateStatus


def render_candidate_application_selection(rows: list[dict], selected_job: dict, section_key: str) -> None:
    if not rows:
        return

    result_df = pd.DataFrame(rows)
    if result_df.empty or "score" not in result_df.columns:
        return

    result_df["score"] = pd.to_numeric(result_df["score"], errors="coerce").fillna(0)

    st.divider()
    st.markdown("### Add Candidate to Job")

    min_score = st.slider(
        "Minimum match score",
        0, 100, 70, 5,
        key=f"{section_key}_application_min_score",
    )

    filtered_df = result_df[result_df["score"] >= min_score].copy()
    filtered_df = filtered_df.sort_values("score", ascending=False)

    if filtered_df.empty:
        st.info("No candidates meet the selected score threshold.")
        return

    st.caption(f"{len(filtered_df)} candidate(s) meet the minimum score of {min_score}.")

    candidate_options = {}
    for _, row in filtered_df.iterrows():
        candidate_id = row.get("candidate_id")
        candidate_name = row.get("candidate_name") or "Unknown Candidate"
        score = float(row.get("score", 0))

        application_data = load_application(
            candidate_id=candidate_id,
            job_id=selected_job.get("job_id"),
        )
        current_status = (application_data.get("status") or "none") if application_data else "none"

        label = f"{candidate_name} | Score: {score:.1f} | Status: {current_status}"
        candidate_options[label] = {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "score": score,
            "current_status": current_status,
        }

    selected_label = st.selectbox(
        "Select candidate",
        list(candidate_options.keys()),
        key=f"{section_key}_application_candidate",
    )
    selected_candidate = candidate_options[selected_label]
    current_status = selected_candidate["current_status"]
    add_disabled = current_status != CandidateStatus.NONE.value

    if add_disabled:
        st.info(
            f"This candidate already has status **{current_status.title()}** "
            "for this job. The existing status will not be changed."
        )

    if st.button(
        "Add Candidate as Applied",
        type="primary",
        disabled=add_disabled,
        key=f"{section_key}_add_as_applied",
    ):
        _, was_added, message = add_candidate_as_applied_if_available(
            candidate_id=selected_candidate["candidate_id"],
            job_id=selected_job.get("job_id"),
            note=(
                f"Added from {section_key.replace('_', ' ')} "
                f"with match score {selected_candidate['score']:.1f}"
            ),
        )

        st.session_state[f"{section_key}_application_message"] = {
            "type": "success" if was_added else "info",
            "message": (
                f"{selected_candidate['candidate_name']} was added with Applied status."
                if was_added else message
            ),
        }
        st.rerun()

    message_key = f"{section_key}_application_message"
    message_data = st.session_state.get(message_key)

    if message_data:
        (st.success if message_data["type"] == "success" else st.info)(
            message_data["message"]
        )
        if st.button("OK", key=f"{section_key}_close_application_message"):
            del st.session_state[message_key]
            st.rerun()
