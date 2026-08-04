import pandas as pd
import streamlit as st

from services.permission_service import has_permission, require_permission

from application_loader import load_application
from application_service import (
    add_candidate_as_applied_if_available,
)
from schema import CandidateStatus


def get_candidate_application_status(
    candidate_id: str,
    job_id: str,
) -> str:
    application_data = load_application(
        candidate_id=candidate_id,
        job_id=job_id,
    )

    if not application_data:
        return CandidateStatus.NONE.value

    return (
        application_data.get("status")
        or CandidateStatus.NONE.value
    )


def render_candidate_application_selection(
    rows: list[dict],
    selected_job: dict,
    section_key: str,
) -> None:
    """
    Filter matching results and add multiple candidates
    to the selected job with Applied status.

    Candidates with an existing status other than NONE
    are skipped.
    """
    if not rows:
        return

    result_df = pd.DataFrame(rows)

    if result_df.empty or "score" not in result_df.columns:
        return

    job_id = selected_job.get("job_id")

    if not job_id:
        st.error("The selected job does not have a valid job ID.")
        return

    result_df["score"] = pd.to_numeric(
        result_df["score"],
        errors="coerce",
    ).fillna(0)

    result_df = result_df.sort_values(
        "score",
        ascending=False,
    )

    st.divider()
    st.markdown("### Add Candidates to Job")

    min_score = st.slider(
        "Minimum match score",
        min_value=0,
        max_value=100,
        value=70,
        step=5,
        key=f"{section_key}_application_min_score",
    )

    filtered_df = result_df[
        result_df["score"] >= min_score
    ].copy()

    if filtered_df.empty:
        st.info(
            "No candidates meet the selected score threshold."
        )
        return

    candidate_options: dict[str, dict] = {}

    for _, row in filtered_df.iterrows():
        candidate_id = row.get("candidate_id")

        if not candidate_id:
            continue

        candidate_name = (
            row.get("candidate_name")
            or "Unknown Candidate"
        )

        score = float(row.get("score", 0))

        current_status = get_candidate_application_status(
            candidate_id=candidate_id,
            job_id=job_id,
        )

        label = (
            f"{candidate_name} | "
            f"Score: {score:.1f} | "
            f"Status: {current_status.title()}"
        )

        candidate_options[label] = {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "score": score,
            "current_status": current_status,
        }

    if not candidate_options:
        st.info("No valid candidates are available.")
        return

    available_count = sum(
        1
        for candidate in candidate_options.values()
        if candidate["current_status"]
        == CandidateStatus.NONE.value
    )

    existing_count = (
        len(candidate_options) - available_count
    )

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric(
            "Above Threshold",
            len(candidate_options),
        )

    with metric_col2:
        st.metric(
            "Available to Add",
            available_count,
        )

    with metric_col3:
        st.metric(
            "Already in Process",
            existing_count,
        )

    st.caption(
        "Candidates with an existing application status "
        "will be skipped automatically."
    )

    selectable_labels = [
        label
        for label, candidate in candidate_options.items()
        if candidate["current_status"]
        == CandidateStatus.NONE.value
    ]

    selected_labels = st.multiselect(
        "Select candidates",
        options=list(candidate_options.keys()),
        default=selectable_labels,
        key=f"{section_key}_application_candidates",
    )

    selected_candidates = [
        candidate_options[label]
        for label in selected_labels
    ]

    candidates_available_to_add = [
        candidate
        for candidate in selected_candidates
        if candidate["current_status"]
        == CandidateStatus.NONE.value
    ]

    candidates_already_in_process = [
        candidate
        for candidate in selected_candidates
        if candidate["current_status"]
        != CandidateStatus.NONE.value
    ]

    if candidates_already_in_process:
        skipped_names = ", ".join(
            candidate["candidate_name"]
            for candidate in candidates_already_in_process
        )

        st.info(
            "These selected candidates already have a status "
            f"and will be skipped: {skipped_names}"
        )

    can_update_status = has_permission(
        "application.update_status"
    )
    add_disabled = (
        not candidates_available_to_add
        or not can_update_status
    )

    button_label = (
        "Add Selected Candidates as Applied"
        if candidates_available_to_add
        else "No Candidates Available to Add"
    )

    if st.button(
        button_label,
        type="primary",
        disabled=add_disabled,
        use_container_width=True,
        key=f"{section_key}_batch_add_as_applied",
    ):
        require_permission(
            "application.update_status"
        )
        added_candidates = []
        skipped_candidates = []
        failed_candidates = []

        progress = st.progress(0)
        status_box = st.empty()

        total_candidates = len(selected_candidates)

        for index, candidate in enumerate(
            selected_candidates
        ):
            candidate_name = candidate["candidate_name"]

            status_box.info(
                f"Processing {candidate_name}..."
            )

            try:
                _, was_added, message = (
                    add_candidate_as_applied_if_available(
                        candidate_id=candidate[
                            "candidate_id"
                        ],
                        job_id=job_id,
                        note=(
                            f"Added from "
                            f"{section_key.replace('_', ' ')} "
                            f"with match score "
                            f"{candidate['score']:.1f}"
                        ),
                    )
                )

                if was_added:
                    added_candidates.append(
                        candidate_name
                    )
                else:
                    skipped_candidates.append(
                        {
                            "name": candidate_name,
                            "reason": message,
                        }
                    )

            except Exception as exc:
                failed_candidates.append(
                    {
                        "name": candidate_name,
                        "reason": str(exc),
                    }
                )

            progress.progress(
                (index + 1) / total_candidates
            )

        status_box.empty()

        st.session_state[
            f"{section_key}_batch_application_result"
        ] = {
            "added": added_candidates,
            "skipped": skipped_candidates,
            "failed": failed_candidates,
        }

        st.rerun()

    result_key = (
        f"{section_key}_batch_application_result"
    )

    batch_result = st.session_state.get(result_key)

    if batch_result:
        added = batch_result.get("added", [])
        skipped = batch_result.get("skipped", [])
        failed = batch_result.get("failed", [])

        if added:
            st.success(
                f"{len(added)} candidate(s) added with "
                "Applied status: "
                + ", ".join(added)
            )

        if skipped:
            st.info(
                f"{len(skipped)} candidate(s) skipped."
            )

            with st.expander("View skipped candidates"):
                for item in skipped:
                    st.write(
                        f"- **{item['name']}**: "
                        f"{item['reason']}"
                    )

        if failed:
            st.error(
                f"{len(failed)} candidate(s) could not be added."
            )

            with st.expander("View failed candidates"):
                for item in failed:
                    st.write(
                        f"- **{item['name']}**: "
                        f"{item['reason']}"
                    )

        if st.button(
            "OK",
            key=f"{section_key}_close_batch_result",
        ):
            del st.session_state[result_key]
            st.rerun()