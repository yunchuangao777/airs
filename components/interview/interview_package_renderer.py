from __future__ import annotations

import streamlit as st

def _render_interview_objectives(content) -> None:
    with st.container(border=True):
        st.subheader("Interview Objectives")

        if content.interview_objectives:
            for index, objective in enumerate(
                content.interview_objectives,
                start=1,
            ):
                st.markdown(
                    f"**{index}.** {objective}"
                )
        else:
            st.caption(
                "No interview objectives were generated."
            )


def _render_agenda(content) -> None:
    with st.container(border=True):
        st.subheader("Interview Agenda")

        if not content.agenda:
            st.caption(
                "No interview agenda was generated."
            )
            return

        total_minutes = sum(
            int(item.minutes or 0)
            for item in content.agenda
        )

        st.caption(
            f"Planned interview time: "
            f"{total_minutes} minutes"
        )

        for index, item in enumerate(
            content.agenda,
            start=1,
        ):
            section_col, time_col = st.columns(
                [4, 1]
            )

            with section_col:
                st.markdown(
                    f"**{index}. {item.section}**"
                )

                if item.objective:
                    st.caption(item.objective)

            with time_col:
                st.metric(
                    "Time",
                    f"{item.minutes} min",
                )

            if index < len(content.agenda):
                st.divider()


def render_interview_package(package) -> None:
    """
    Render a saved interview package in a
    recruiter-friendly format.
    """
    content = package.generated_content

    _render_header(package)

    st.divider()

    _render_summary(content)

    st.divider()

    _render_strengths_and_concerns(content)

    st.divider()

    _render_areas_to_verify(content)

    st.divider()

    _render_interview_objectives(content)

    st.divider()

    _render_agenda(content)


def _render_header(package) -> None:
    content = package.generated_content

    candidate_name = (
        package.candidate_name
        or "Unknown Candidate"
    )

    job_title = (
        package.job_title
        or "Untitled Job"
    )

    company = package.company or ""

    with st.container(border=True):
        header_col1, header_col2 = st.columns(
            [3, 2]
        )

        with header_col1:
            st.markdown("### Interview Brief")

            st.markdown(
                f"## {candidate_name}"
            )

            st.markdown(
                f"**Position:** {job_title}"
            )

            if company:
                st.markdown(
                    f"**Company:** {company}"
                )

            if package.focus_areas:
                st.caption(
                    "Focus areas: "
                    + ", ".join(
                        package.focus_areas
                    )
                )

        with header_col2:
            st.caption("Package Details")

            st.write(
                f"**Interview type:** "
                f"{package.interview_type_label}"
            )

            st.write(
                f"**Difficulty:** "
                f"{package.difficulty_label}"
            )

            st.write(
                f"**Duration:** "
                f"{package.duration_minutes} minutes"
            )

            st.write(
                f"**Questions generated:** "
                f"{len(content.questions)}"
            )

            st.write(
                f"**Model:** "
                f"{package.model_name}"
            )

    metric_col1, metric_col2, metric_col3, metric_col4 = (
        st.columns(4)
    )

    with metric_col1:
        st.metric(
            "Duration",
            f"{package.duration_minutes} min",
        )

    with metric_col2:
        st.metric(
            "Questions",
            len(content.questions),
        )

    with metric_col3:
        st.metric(
            "Focus Areas",
            len(package.focus_areas),
        )

    with metric_col4:
        st.metric(
            "Objectives",
            len(content.interview_objectives),
        )


def _render_summary(content) -> None:
    summary_col, role_fit_col = st.columns(2)

    with summary_col:
        with st.container(border=True):
            st.subheader("Candidate Summary")

            if content.candidate_summary:
                st.write(
                    content.candidate_summary
                )
            else:
                st.caption(
                    "No candidate summary was generated."
                )

    with role_fit_col:
        with st.container(border=True):
            st.subheader("Role-Fit Summary")

            if content.role_fit_summary:
                st.write(
                    content.role_fit_summary
                )
            else:
                st.caption(
                    "No role-fit summary was generated."
                )


def _render_strengths_and_concerns(
    content,
) -> None:
    strength_col, concern_col = st.columns(2)

    with strength_col:
        with st.container(border=True):
            st.subheader(
                f"Strengths ({len(content.strengths)})"
            )

            if content.strengths:
                for item in content.strengths:
                    st.markdown(
                        f"✅ {item}"
                    )
            else:
                st.caption(
                    "No strengths were identified."
                )

    with concern_col:
        with st.container(border=True):
            st.subheader(
                f"Concerns ({len(content.concerns)})"
            )

            if content.concerns:
                for item in content.concerns:
                    st.markdown(
                        f"⚠️ {item}"
                    )
            else:
                st.caption(
                    "No concerns were identified."
                )


def _render_areas_to_verify(content) -> None:
    with st.container(border=True):
        st.subheader(
            f"Areas to Verify "
            f"({len(content.areas_to_verify)})"
        )

        if content.areas_to_verify:
            st.caption(
                "These points should be confirmed during "
                "the interview rather than assumed."
            )

            for index, item in enumerate(
                content.areas_to_verify,
                start=1,
            ):
                st.markdown(
                    f"**{index}.** {item}"
                )
        else:
            st.caption(
                "No additional verification areas "
                "were identified."
            )