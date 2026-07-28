from __future__ import annotations

import pandas as pd
import streamlit as st

from components.hiring.candidate_status_dialog import (
    show_candidate_status_dialog,
)
from services.hiring_service import (
    STATUS_LABELS,
    get_candidates_for_job,
)


VISIBLE_STATUSES = [
    "applied",
    "review",
    "interview",
    "offer",
    "accepted",
    "rejected",
    "archived",
]


def create_job_label(summary: dict) -> str:
    """Create a readable label for the job selector."""
    job_title = (
        summary.get("job_title")
        or "Untitled Job"
    )

    company = summary.get("company") or ""

    if company:
        return f"{job_title} — {company}"

    return job_title


def create_status_options() -> dict[str, str | None]:
    """
    Map display labels to stored status values.
    """
    options: dict[str, str | None] = {
        "All statuses": None,
    }

    for status in VISIBLE_STATUSES:
        options[
            STATUS_LABELS.get(
                status,
                status.title(),
            )
        ] = status

    return options


def build_candidate_table(
    application_rows: list[dict],
) -> pd.DataFrame:
    """
    Convert hiring dataset rows into a candidate table.
    """
    rows: list[dict] = []

    for application in application_rows:
        candidate = application.get(
            "candidate",
            {},
        )

        status = (
            application.get("status")
            or "none"
        )

        updated_time = (
            application.get("updated_time")
            or application.get("created_time")
            or ""
        )

        rows.append(
            {
                "Candidate": (
                    application.get("candidate_name")
                    or "Unknown Candidate"
                ),
                "Status": STATUS_LABELS.get(
                    status,
                    status.title(),
                ),
                "Match Score": float(
                    application.get(
                        "match_score",
                        0,
                    )
                    or 0
                ),
                "Email": (
                    application.get(
                        "candidate_email"
                    )
                    or candidate.get("email")
                    or ""
                ),
                "Phone": (
                    candidate.get("phone")
                    or ""
                ),
                "Location": (
                    candidate.get("location")
                    or ""
                ),
                "Experience": candidate.get(
                    "total_years_experience"
                ),
                "Last Updated": updated_time,
                "Candidate ID": application.get(
                    "candidate_id"
                ),
                "Job ID": application.get(
                    "job_id"
                ),
                "_Application Row": application,
            }
        )

    return pd.DataFrame(rows)


def render_pipeline_metrics(
    application_rows: list[dict],
) -> None:
    """
    Show a compact count for each hiring status.
    """
    counts = {
        status: 0
        for status in VISIBLE_STATUSES
    }

    for application in application_rows:
        status = (
            application.get("status")
            or "none"
        )

        if status in counts:
            counts[status] += 1

    columns = st.columns(
        len(VISIBLE_STATUSES)
    )

    for column, status in zip(
        columns,
        VISIBLE_STATUSES,
    ):
        with column:
            st.metric(
                STATUS_LABELS.get(
                    status,
                    status.title(),
                ),
                counts[status],
            )


def render_candidate_management(
    dataset: list[dict],
    summaries: list[dict],
) -> None:
    """
    Render candidate pipeline management for one selected job.
    """
    st.markdown("### Candidate Management")

    st.caption(
        "Select a job, filter its candidate pipeline, "
        "and open a candidate to review details or "
        "change hiring status."
    )

    if not summaries:
        st.info("No jobs are available.")
        return

    job_options: dict[str, dict] = {}

    for summary in summaries:
        label = create_job_label(summary)

        # Protect against duplicate job titles.
        if label in job_options:
            label = (
                f"{label} "
                f"({summary.get('job_id')})"
            )

        job_options[label] = summary

    filter_col1, filter_col2 = st.columns(
        [2, 1]
    )

    with filter_col1:
        selected_job_label = st.selectbox(
            "Select job",
            options=list(job_options.keys()),
            key="hiring_candidate_job_filter",
        )

    selected_summary = job_options[
        selected_job_label
    ]

    selected_job_id = selected_summary.get(
        "job_id"
    )

    status_options = create_status_options()

    with filter_col2:
        selected_status_label = st.selectbox(
            "Status",
            options=list(
                status_options.keys()
            ),
            key="hiring_candidate_status_filter",
        )

    selected_status = status_options[
        selected_status_label
    ]

    search_col, score_col = st.columns(
        [2, 1]
    )

    with search_col:
        search_text = st.text_input(
            "Search candidate",
            placeholder=(
                "Search by name, email, phone, "
                "or location"
            ),
            key="hiring_candidate_search",
        )

    with score_col:
        minimum_score = st.number_input(
            "Minimum match score",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=5.0,
            key="hiring_candidate_min_score",
        )

    all_job_rows = get_candidates_for_job(
        job_id=selected_job_id,
        dataset=dataset,
    )

    render_pipeline_metrics(
        all_job_rows
    )

    application_rows = get_candidates_for_job(
        job_id=selected_job_id,
        status=selected_status,
        dataset=dataset,
    )

    if search_text.strip():
        search_value = (
            search_text.strip().lower()
        )

        application_rows = [
            application
            for application in application_rows
            if search_value
            in " ".join(
                [
                    str(
                        application.get(
                            "candidate_name"
                        )
                        or ""
                    ),
                    str(
                        application.get(
                            "candidate_email"
                        )
                        or ""
                    ),
                    str(
                        application.get(
                            "candidate",
                            {},
                        ).get("phone")
                        or ""
                    ),
                    str(
                        application.get(
                            "candidate",
                            {},
                        ).get("location")
                        or ""
                    ),
                ]
            ).lower()
        ]

    if minimum_score > 0:
        application_rows = [
            application
            for application in application_rows
            if float(
                application.get(
                    "match_score",
                    0,
                )
                or 0
            )
            >= minimum_score
        ]

    st.caption(
        f"Showing {len(application_rows)} of "
        f"{len(all_job_rows)} candidate(s) for "
        f"{selected_job_label}."
    )

    if not all_job_rows:
        st.info(
            "No candidates are currently in the hiring "
            "pipeline for this job."
        )
        return

    if not application_rows:
        st.info(
            "No candidates match the selected filters."
        )
        return

    candidate_df = build_candidate_table(
        application_rows
    )

    display_df = candidate_df.drop(
        columns=[
            "Candidate ID",
            "Job ID",
            "_Application Row",
        ],
        errors="ignore",
    ).reset_index(drop=True)

    table_version = st.session_state.get(
        "hiring_candidate_table_version",
        0,
    )

    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=(
            f"hiring_candidate_table_"
            f"{selected_job_id}_"
            f"{table_version}"
        ),
        column_config={
            "Candidate": (
                st.column_config.TextColumn(
                    "Candidate",
                    width="medium",
                )
            ),
            "Status": (
                st.column_config.TextColumn(
                    "Status",
                    width="small",
                )
            ),
            "Match Score": (
                st.column_config.NumberColumn(
                    "Match Score",
                    min_value=0,
                    max_value=100,
                    format="%.1f",
                )
            ),
            "Email": (
                st.column_config.TextColumn(
                    "Email",
                    width="medium",
                )
            ),
            "Phone": (
                st.column_config.TextColumn(
                    "Phone",
                    width="small",
                )
            ),
            "Location": (
                st.column_config.TextColumn(
                    "Location",
                    width="small",
                )
            ),
            "Experience": (
                st.column_config.NumberColumn(
                    "Experience",
                    format="%.1f years",
                )
            ),
            "Last Updated": (
                st.column_config.TextColumn(
                    "Last Updated",
                    width="medium",
                )
            ),
        },
    )

    st.caption(
        "Select a row to open candidate details "
        "and update status."
    )

    selected_rows = event.selection.rows

    if selected_rows:
        selected_index = selected_rows[0]

        application_row = candidate_df.iloc[
            selected_index
        ]["_Application Row"]

        show_candidate_status_dialog(
            application_row
        )