from __future__ import annotations

import pandas as pd
import streamlit as st


def render_interview_questions(package) -> None:
    """
    Render objectives, agenda, and detailed interview questions.
    """
    content = package.generated_content

    st.markdown("### Interview Objectives")

    if content.interview_objectives:
        for index, objective in enumerate(
            content.interview_objectives,
            start=1,
        ):
            st.markdown(
                f"{index}. {objective}"
            )
    else:
        st.caption(
            "No interview objectives were generated."
        )

    st.divider()

    _render_agenda(content.agenda)

    st.divider()

    _render_question_bank(
        content.questions
    )


def _render_agenda(
    agenda: list,
) -> None:
    st.markdown("### Interview Agenda")

    if not agenda:
        st.caption(
            "No interview agenda was generated."
        )
        return

    agenda_rows = []

    for item in agenda:
        agenda_rows.append(
            {
                "Section": item.section,
                "Minutes": item.minutes,
                "Objective": item.objective,
            }
        )

    agenda_df = pd.DataFrame(
        agenda_rows
    )

    st.dataframe(
        agenda_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Section": (
                st.column_config.TextColumn(
                    "Section",
                    width="medium",
                )
            ),
            "Minutes": (
                st.column_config.NumberColumn(
                    "Minutes",
                    format="%d min",
                )
            ),
            "Objective": (
                st.column_config.TextColumn(
                    "Objective",
                    width="large",
                )
            ),
        },
    )


def _render_question_bank(
    questions: list,
) -> None:
    st.markdown("### Question Bank")

    if not questions:
        st.caption(
            "No interview questions were generated."
        )
        return

    for index, question in enumerate(
        questions,
        start=1,
    ):
        title = (
            f"{question.question_id or f'Q{index}'} — "
            f"{question.question}"
        )

        with st.expander(
            title,
            expanded=False,
        ):
            info_col1, info_col2 = st.columns(2)

            with info_col1:
                st.caption("Category")
                st.write(
                    question.category
                    .replace("_", " ")
                    .title()
                )

            with info_col2:
                st.caption("Competency")
                st.write(
                    question.competency
                )

            st.markdown("#### Why ask this")
            st.write(question.reason)

            st.markdown(
                "#### Strong-answer indicators"
            )

            if question.strong_answer_indicators:
                for item in (
                    question.strong_answer_indicators
                ):
                    st.markdown(
                        f"✅ {item}"
                    )
            else:
                st.caption(
                    "No strong-answer indicators."
                )

            st.markdown("#### Warning signs")

            if question.warning_signs:
                for item in question.warning_signs:
                    st.markdown(
                        f"⚠️ {item}"
                    )
            else:
                st.caption(
                    "No warning signs identified."
                )

            st.markdown(
                "#### Suggested follow-ups"
            )

            if question.suggested_follow_ups:
                for follow_up in (
                    question.suggested_follow_ups
                ):
                    st.markdown(
                        f"- {follow_up}"
                    )
            else:
                st.caption(
                    "No follow-up questions generated."
                )