from __future__ import annotations

from datetime import datetime

import streamlit as st

from services.candidate_timeline_service import (
    build_candidate_timeline,
)


EVENT_ICONS = {
    "application_created": "📄",
    "job_match": "🎯",
    "status_change": "🔄",
    "interview_session_created": "🗂️",
    "interview_started": "▶️",
    "interview_completed": "✅",
    "evaluation_draft": "📝",
    "evaluation_completed": "⭐",
}


def format_timeline_time(
    timestamp: str | None,
) -> str:
    if not timestamp:
        return "Time not available"

    try:
        parsed = datetime.fromisoformat(
            str(timestamp).replace(
                "Z",
                "+00:00",
            )
        )

        return parsed.strftime(
            "%b %d, %Y · %H:%M"
        )

    except ValueError:
        return str(timestamp)


def render_timeline_summary(
    application_row: dict,
    events: list[dict],
) -> None:
    application = application_row.get(
        "application",
        {},
    )

    current_status = (
        application_row.get("status_label")
        or application_row.get("status")
        or "Not available"
    )

    interview_count = sum(
        1
        for event in events
        if event.get("event_type")
        == "interview_session_created"
    )

    completed_evaluations = sum(
        1
        for event in events
        if event.get("event_type")
        == "evaluation_completed"
    )

    metric_col1, metric_col2, metric_col3 = (
        st.columns(3)
    )

    with metric_col1:
        st.metric(
            "Current Status",
            str(current_status),
        )

    with metric_col2:
        st.metric(
            "Interview Sessions",
            interview_count,
        )

    with metric_col3:
        st.metric(
            "Finalized Evaluations",
            completed_evaluations,
        )

    created_time = application.get(
        "created_time"
    )

    if created_time:
        st.caption(
            "Application created "
            f"{format_timeline_time(created_time)}"
        )


def render_candidate_timeline(
    application_row: dict,
) -> None:
    """
    Render the chronological candidate timeline.
    """

    candidate_name = (
        application_row.get("candidate_name")
        or "Candidate"
    )

    job_title = (
        application_row.get("job_title")
        or "Untitled Job"
    )

    st.markdown(
        f"### {candidate_name}"
    )

    st.caption(
        f"Timeline for {job_title}"
    )


    events = build_candidate_timeline(
        application_row
    )

    render_timeline_summary(
        application_row=application_row,
        events=events,
    )

    st.divider()

    if not events:
        st.info(
            "No timeline activity is available."
        )
        return

    for index, event in enumerate(events):
        icon = EVENT_ICONS.get(
            event.get("event_type"),
            "•",
        )

        title = event.get(
            "title",
            "Activity",
        )

        timestamp = format_timeline_time(
            event.get("timestamp")
        )

        description = event.get(
            "description",
            "",
        )

        status = event.get(
            "status",
            "completed",
        )

        left_col, right_col = st.columns(
            [1, 12]
        )

        with left_col:
            st.markdown(
                f"<div style='font-size:1.45rem;"
                f"text-align:center;padding-top:0.15rem;'>"
                f"{icon}</div>",
                unsafe_allow_html=True,
            )

        with right_col:
            title_suffix = ""

            if status == "active":
                title_suffix = " · In progress"

            st.markdown(
                f"**{title}{title_suffix}**"
            )

            st.caption(timestamp)

            if description:
                st.write(description)

        if index < len(events) - 1:
            st.markdown(
                """
                <div style="
                    margin-left: 1.2rem;
                    height: 18px;
                    border-left: 2px solid
                    rgba(128, 128, 128, 0.30);
                "></div>
                """,
                unsafe_allow_html=True,
            )