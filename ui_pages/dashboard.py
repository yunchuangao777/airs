from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from services.dashboard_service import (
    build_dashboard_data,
)


def _render_metric_cards(summary: dict) -> None:
    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)

    with row1_col1:
        st.metric(
            "Candidates",
            summary.get("total_candidates", 0),
        )

    with row1_col2:
        st.metric(
            "Jobs",
            summary.get("total_jobs", 0),
        )

    with row1_col3:
        st.metric(
            "Applications",
            summary.get("total_applications", 0),
        )

    with row1_col4:
        st.metric(
            "Interview Sessions",
            summary.get("total_interviews", 0),
        )

    row2_col1, row2_col2, row2_col3 = st.columns(3)

    with row2_col1:
        st.metric(
            "Completed Interviews",
            summary.get("completed_interviews", 0),
        )

    with row2_col2:
        st.metric(
            "Finalized Evaluations",
            summary.get("finalized_evaluations", 0),
        )

    with row2_col3:
        average_match_score = summary.get(
            "average_match_score"
        )

        st.metric(
            "Average Match Score",
            (
                f"{average_match_score:.1f}"
                if average_match_score is not None
                else "N/A"
            ),
        )


def _render_application_status_chart(
    rows: list[dict],
) -> None:
    st.markdown("### Application Status")

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        st.info(
            "No application status data is available."
        )
        return

    dataframe = dataframe[
        dataframe["count"] > 0
    ].copy()

    if dataframe.empty:
        st.info(
            "No applications have been recorded yet."
        )
        return

    chart = (
        alt.Chart(dataframe)
        .mark_bar(
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5,
        )
        .encode(
            x=alt.X(
                "status:N",
                title=None,
                sort=None,
                axis=alt.Axis(
                    labelAngle=0,
                ),
            ),
            y=alt.Y(
                "count:Q",
                title="Applications",
            ),
            tooltip=[
                alt.Tooltip(
                    "status:N",
                    title="Status",
                ),
                alt.Tooltip(
                    "count:Q",
                    title="Applications",
                    format=",",
                ),
            ],
        )
        .properties(
            height=320,
        )
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )


def _render_education_chart(
    rows: list[dict],
) -> None:
    st.markdown("### Highest Education Level")

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        st.info(
            "No education data is available."
        )
        return

    chart = (
        alt.Chart(dataframe)
        .mark_bar(
            cornerRadiusEnd=5,
        )
        .encode(
            y=alt.Y(
                "degree:N",
                title=None,
                sort="-x",
            ),
            x=alt.X(
                "count:Q",
                title="Candidates",
            ),
            tooltip=[
                alt.Tooltip(
                    "degree:N",
                    title="Education",
                ),
                alt.Tooltip(
                    "count:Q",
                    title="Candidates",
                    format=",",
                ),
            ],
        )
        .properties(
            height=max(
                260,
                len(dataframe) * 44,
            ),
        )
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )



def _render_candidate_skills_chart(
    rows: list[dict],
) -> None:
    st.markdown("### Top Candidate Skills")

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        st.info(
            "No candidate skill data is available."
        )
        return

    chart = (
        alt.Chart(dataframe)
        .mark_bar(
            cornerRadiusEnd=5,
        )
        .encode(
            y=alt.Y(
                "skill:N",
                title=None,
                sort="-x",
            ),
            x=alt.X(
                "count:Q",
                title="Candidates",
            ),
            tooltip=[
                alt.Tooltip(
                    "skill:N",
                    title="Skill",
                ),
                alt.Tooltip(
                    "count:Q",
                    title="Candidates",
                    format=",",
                ),
            ],
        )
        .properties(
            height=max(
                320,
                len(dataframe) * 32,
            ),
        )
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )

def _render_applications_by_job_chart(
    rows: list[dict],
) -> None:
    st.markdown("### Applications by Job")

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        st.info(
            "No job application data is available."
        )
        return

    chart = (
        alt.Chart(dataframe)
        .mark_bar(
            cornerRadiusEnd=5,
        )
        .encode(
            y=alt.Y(
                "job:N",
                title=None,
                sort="-x",
            ),
            x=alt.X(
                "count:Q",
                title="Applications",
            ),
            tooltip=[
                alt.Tooltip(
                    "job:N",
                    title="Job",
                ),
                alt.Tooltip(
                    "count:Q",
                    title="Applications",
                    format=",",
                ),
            ],
        )
        .properties(
            height=max(
                260,
                len(dataframe) * 44,
            ),
        )
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )


def _render_interview_status_chart(
    rows: list[dict],
) -> None:
    st.markdown("### Interview Status")

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        st.info(
            "No interview session data is available."
        )
        return

    chart = (
        alt.Chart(dataframe)
        .mark_arc(
            innerRadius=55,
        )
        .encode(
            theta=alt.Theta(
                "count:Q",
                stack=True,
            ),
            color=alt.Color(
                "status:N",
                title="Status",
            ),
            tooltip=[
                alt.Tooltip(
                    "status:N",
                    title="Status",
                ),
                alt.Tooltip(
                    "count:Q",
                    title="Sessions",
                    format=",",
                ),
            ],
        )
        .properties(
            height=320,
        )
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )


def _render_recommendation_chart(
    rows: list[dict],
) -> None:
    st.markdown("### Evaluation Recommendations")

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        st.info(
            "No evaluation recommendations are "
            "available yet."
        )
        return

    chart = (
        alt.Chart(dataframe)
        .mark_arc(
            innerRadius=55,
        )
        .encode(
            theta=alt.Theta(
                "count:Q",
                stack=True,
            ),
            color=alt.Color(
                "recommendation:N",
                title="Recommendation",
            ),
            tooltip=[
                alt.Tooltip(
                    "recommendation:N",
                    title="Recommendation",
                ),
                alt.Tooltip(
                    "count:Q",
                    title="Evaluations",
                    format=",",
                ),
            ],
        )
        .properties(
            height=320,
        )
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )


def render_dashboard() -> None:
    st.title("Dashboard")

    st.caption(
        "Overview of candidates, jobs, applications, "
        "interviews, and evaluations."
    )

    try:
        dashboard = build_dashboard_data()
    except Exception as exc:
        st.error(
            f"Unable to build dashboard data: {exc}"
        )
        return

    _render_metric_cards(
        dashboard.get("summary", {})
    )

    st.divider()

    first_row_col1, first_row_col2 = st.columns(2)

    with first_row_col1:
        _render_application_status_chart(
            dashboard.get(
                "application_status",
                [],
            )
        )

    with first_row_col2:
        _render_education_chart(
            dashboard.get(
                "education",
                [],
            )
        )

    st.divider()

    _render_candidate_skills_chart(
        dashboard.get(
            "candidate_skills",
            [],
        )
    )

    st.divider()

    second_row_col1, second_row_col2 = st.columns(2)

    with second_row_col1:
        _render_applications_by_job_chart(
            dashboard.get(
                "applications_by_job",
                [],
            )
        )

    with second_row_col2:
        _render_interview_status_chart(
            dashboard.get(
                "interview_status",
                [],
            )
        )

    st.divider()

    _render_recommendation_chart(
        dashboard.get(
            "recommendations",
            [],
        )
    )