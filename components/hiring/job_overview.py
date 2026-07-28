from __future__ import annotations

import streamlit as st

from services.hiring_service import (
    STATUS_LABELS,
    STATUS_ORDER,
)
from components.hiring.candidate_status_dialog import (
    show_candidate_status_dialog,
)

# Statuses that should appear in Hiring Management.
# "none" is excluded because these candidates have not entered
# the hiring process for the selected job.
VISIBLE_STATUSES = [
    status
    for status in STATUS_ORDER
    if status != "none"
]


STATUS_COLORS = {
    "applied": "#3B82F6",
    "review": "#F59E0B",
    "interview": "#8B5CF6",
    "offer": "#06B6D4",
    "accepted": "#10B981",
    "rejected": "#EF4444",
    "archived": "#6B7280",
}


def format_job_title(summary: dict) -> str:
    """
    Return a readable job heading.
    """
    job_title = (
        summary.get("job_title")
        or "Untitled Job"
    )

    company = summary.get("company") or ""

    if company:
        return f"{job_title} — {company}"

    return job_title


def get_active_candidate_count(
    summary: dict,
) -> int:
    """
    Count candidates who are still in the active hiring process.
    """
    status_counts = summary.get(
        "status_counts",
        {},
    )

    active_statuses = [
        "applied",
        "review",
        "interview",
        "offer",
    ]

    return sum(
        int(status_counts.get(status, 0) or 0)
        for status in active_statuses
    )


def get_completed_candidate_count(
    summary: dict,
) -> int:
    """
    Count candidates who reached Accepted status.
    """
    status_counts = summary.get(
        "status_counts",
        {},
    )

    return int(
        status_counts.get("accepted", 0) or 0
    )


def render_status_metrics(
    summary: dict,
) -> None:
    """
    Render one count for every hiring status.
    """
    status_counts = summary.get(
        "status_counts",
        {},
    )

    metric_columns = st.columns(
        len(VISIBLE_STATUSES)
    )

    for column, status in zip(
        metric_columns,
        VISIBLE_STATUSES,
    ):
        with column:
            st.metric(
                label=STATUS_LABELS.get(
                    status,
                    status.title(),
                ),
                value=int(
                    status_counts.get(status, 0)
                    or 0
                ),
            )


def render_status_progress(
    summary: dict,
) -> None:
    """
    Render a simple hiring-progress indicator.

    The current version treats Accepted candidates as completed.
    """
    total_candidates = int(
        summary.get("total_candidates", 0)
        or 0
    )

    accepted_count = get_completed_candidate_count(
        summary
    )

    if total_candidates <= 0:
        progress_value = 0.0
    else:
        progress_value = min(
            accepted_count / total_candidates,
            1.0,
        )

    st.progress(progress_value)

    st.caption(
        f"Hiring completion: "
        f"{accepted_count} accepted out of "
        f"{total_candidates} candidate(s)"
    )


def group_applications_by_status(
    applications: list[dict],
) -> dict[str, list[dict]]:
    """
    Group application rows by hiring status.
    """
    grouped = {
        status: []
        for status in VISIBLE_STATUSES
    }

    for application in applications:
        status = (
            application.get("status")
            or "none"
        )

        if status in grouped:
            grouped[status].append(
                application
            )

    for status in grouped:
        grouped[status] = sorted(
            grouped[status],
            key=lambda row: float(
                row.get("match_score", 0)
                or 0
            ),
            reverse=True,
        )

    return grouped


def render_candidate_row(
    application: dict,
    status: str,
    row_key: str,
) -> None:
    """
    Render one candidate row with a details/status button.
    """
    candidate_name = (
        application.get("candidate_name")
        or "Unknown Candidate"
    )

    candidate_email = (
        application.get("candidate_email")
        or ""
    )

    match_score = float(
        application.get("match_score", 0)
        or 0
    )

    updated_time = (
        application.get("updated_time")
        or application.get("created_time")
        or ""
    )

    candidate_col, score_col, date_col, action_col = (
        st.columns([3, 1, 2, 1])
    )

    with candidate_col:
        st.markdown(
            f"**{candidate_name}**"
        )

        if candidate_email:
            st.caption(candidate_email)

    with score_col:
        st.write(f"{match_score:.1f}")

    with date_col:
        st.caption(
            str(updated_time)
            if updated_time
            else "No update time"
        )

    with action_col:
        if st.button(
            "View / Update",
            key=f"view_update_{row_key}",
            use_container_width=True,
        ):
            show_candidate_status_dialog(
                application
            )


def render_candidates_by_status(
    summary: dict,
) -> None:
    """
    Display candidate names grouped by hiring status.
    """
    applications = summary.get(
        "applications",
        [],
    )

    if not applications:
        st.info(
            "No candidates are currently associated "
            "with this job."
        )
        return

    grouped = group_applications_by_status(
        applications
    )

    for status in VISIBLE_STATUSES:
        candidates = grouped.get(
            status,
            [],
        )

        if not candidates:
            continue

        label = STATUS_LABELS.get(
            status,
            status.title(),
        )

        color = STATUS_COLORS.get(
            status,
            "#6B7280",
        )

        st.markdown(
            (
                f"<div style='"
                f"display:flex;"
                f"align-items:center;"
                f"gap:8px;"
                f"margin-top:12px;"
                f"margin-bottom:6px;'>"
                f"<span style='"
                f"display:inline-block;"
                f"width:10px;"
                f"height:10px;"
                f"border-radius:50%;"
                f"background:{color};'>"
                f"</span>"
                f"<strong>{label}</strong>"
                f"<span style='color:#6B7280;'>"
                f"({len(candidates)})"
                f"</span>"
                f"</div>"
            ),
            unsafe_allow_html=True,
        )

        header_col1, header_col2, header_col3, header_col4 = (
            st.columns([3, 1, 2, 1])
        )

        with header_col1:
            st.caption("Candidate")

        with header_col2:
            st.caption("Match Score")

        with header_col3:
            st.caption("Last Updated")

        with header_col4:
            st.caption("Action")

        for index, application in enumerate(
            candidates
        ):
            render_candidate_row(
                application=application,
                status=status,
                row_key=(
                    f"{summary.get('job_id')}_"
                    f"{status}_{index}"
                ),
            )


def render_job_card(
    summary: dict,
    index: int,
) -> None:
    """
    Render one job overview card.
    """
    job_title = format_job_title(summary)

    location = (
        summary.get("location")
        or "Location not specified"
    )

    total_candidates = int(
        summary.get("total_candidates", 0)
        or 0
    )

    active_candidates = (
        get_active_candidate_count(summary)
    )

    accepted_candidates = (
        get_completed_candidate_count(summary)
    )

    with st.container(border=True):
        heading_col, summary_col = st.columns(
            [3, 2]
        )

        with heading_col:
            st.markdown(f"### {job_title}")
            st.caption(location)

        with summary_col:
            metric_col1, metric_col2, metric_col3 = (
                st.columns(3)
            )

            with metric_col1:
                st.metric(
                    "Total",
                    total_candidates,
                )

            with metric_col2:
                st.metric(
                    "Active",
                    active_candidates,
                )

            with metric_col3:
                st.metric(
                    "Accepted",
                    accepted_candidates,
                )

        render_status_progress(summary)

        st.markdown("#### Status Summary")
        render_status_metrics(summary)

        expander_label = (
            f"View candidates ({total_candidates})"
        )

        with st.expander(
            expander_label,
            expanded=False,
        ):
            render_candidates_by_status(
                summary
            )


def render_job_overview(
    summaries: list[dict],
) -> None:
    """
    Render the Hiring Management Job Overview tab.
    """
    st.markdown("### Job Overview")

    # st.caption(
        # "Review candidate counts and hiring progress "
        # "for each job."
    # )

    if not summaries:
        st.info(
            "No jobs are available."
        )
        return

    search_col, status_col = st.columns(
        [2, 1]
    )

    with search_col:
        search_text = st.text_input(
            "Search jobs",
            placeholder=(
                "Search by job title, company, "
                "or location"
            ),
            key="hiring_overview_job_search",
        )

    with status_col:
        job_filter = st.selectbox(
            "Job activity",
            options=[
                "All jobs",
                "With candidates",
                "Without candidates",
                "With active candidates",
                "With accepted candidates",
            ],
            key="hiring_overview_activity_filter",
        )

    filtered_summaries = summaries

    if search_text.strip():
        search_value = (
            search_text.strip().lower()
        )

        filtered_summaries = [
            summary
            for summary in filtered_summaries
            if search_value
            in " ".join(
                [
                    str(
                        summary.get("job_title")
                        or ""
                    ),
                    str(
                        summary.get("company")
                        or ""
                    ),
                    str(
                        summary.get("location")
                        or ""
                    ),
                ]
            ).lower()
        ]

    if job_filter == "With candidates":
        filtered_summaries = [
            summary
            for summary in filtered_summaries
            if int(
                summary.get(
                    "total_candidates",
                    0,
                )
                or 0
            )
            > 0
        ]

    elif job_filter == "Without candidates":
        filtered_summaries = [
            summary
            for summary in filtered_summaries
            if int(
                summary.get(
                    "total_candidates",
                    0,
                )
                or 0
            )
            == 0
        ]

    elif job_filter == "With active candidates":
        filtered_summaries = [
            summary
            for summary in filtered_summaries
            if get_active_candidate_count(
                summary
            )
            > 0
        ]

    elif job_filter == "With accepted candidates":
        filtered_summaries = [
            summary
            for summary in filtered_summaries
            if get_completed_candidate_count(
                summary
            )
            > 0
        ]

    # st.caption(
        # f"Showing {len(filtered_summaries)} "
        # f"of {len(summaries)} job(s)."
    # )

    if not filtered_summaries:
        st.info(
            "No jobs match the selected filters."
        )
        return

    sorted_summaries = sorted(
        filtered_summaries,
        key=lambda summary: (
            -int(
                summary.get(
                    "total_candidates",
                    0,
                )
                or 0
            ),
            str(
                summary.get("job_title")
                or ""
            ).lower(),
        ),
    )

    for index, summary in enumerate(
        sorted_summaries
    ):
        render_job_card(
            summary=summary,
            index=index,
        )