from __future__ import annotations

import streamlit as st

from services.permission_service import has_permission, require_permission

from services.interview_session_service import (
    InterviewSession,
    calculate_weighted_evaluation_score,
    complete_session_evaluation,
    get_evaluation_completion_counts,
    update_session_evaluation,
)


RECOMMENDATION_OPTIONS = [
    "",
    "Strongly Proceed",
    "Proceed",
    "Proceed with Reservations",
    "Hold",
    "Do Not Proceed",
]


RATING_LABELS = {
    1: "1 — Poor",
    2: "2 — Below Expectations",
    3: "3 — Meets Expectations",
    4: "4 — Strong",
    5: "5 — Exceptional",
}


def get_rating_display(
    rating: int,
) -> str:
    return RATING_LABELS.get(
        rating,
        str(rating),
    )


def render_evaluation_header(
    session: InterviewSession,
) -> None:
    rated_count, total_count = (
        get_evaluation_completion_counts(
            session
        )
    )

    weighted_score = (
        calculate_weighted_evaluation_score(
            session
        )
    )

    metric_col1, metric_col2, metric_col3 = (
        st.columns(3)
    )

    with metric_col1:
        st.metric(
            "Criteria Rated",
            f"{rated_count} / {total_count}",
        )

    with metric_col2:
        st.metric(
            "Weighted Score",
            (
                f"{weighted_score:.2f} / 5"
                if weighted_score is not None
                else "Not available"
            ),
        )

    with metric_col3:
        st.metric(
            "Evaluation Status",
            session.evaluation_status
            .replace("_", " ")
            .title(),
        )

    if total_count:
        st.progress(
            rated_count / total_count,
            text=(
                f"{rated_count} of "
                f"{total_count} criteria rated"
            ),
        )


def render_evidence_guidance(
    criterion,
) -> None:
    with st.expander(
        "View scoring guidance",
        expanded=False,
    ):
        st.markdown("#### Strong evidence")

        if criterion.strong_evidence:
            for item in criterion.strong_evidence:
                st.markdown(f"✅ {item}")
        else:
            st.caption(
                "No strong-evidence guidance was saved."
            )

        st.markdown("#### Weak evidence")

        if criterion.weak_evidence:
            for item in criterion.weak_evidence:
                st.markdown(f"⚠️ {item}")
        else:
            st.caption(
                "No weak-evidence guidance was saved."
            )


def render_interview_evidence(
    session: InterviewSession,
) -> None:
    with st.expander(
        "Review interview answers",
        expanded=False,
    ):
        for index, question in enumerate(
            session.questions,
            start=1,
        ):
            st.markdown(
                f"#### {index}. "
                f"{question.question_text}"
            )

            if question.answer_text:
                st.markdown(
                    "**Candidate answer**"
                )
                st.write(
                    question.answer_text
                )
            else:
                st.caption(
                    "No candidate answer was recorded."
                )

            if question.interviewer_notes:
                st.markdown(
                    "**Interviewer notes**"
                )
                st.write(
                    question.interviewer_notes
                )

            if index < len(session.questions):
                st.divider()


def render_evaluation_form(
    session: InterviewSession,
) -> None:
    can_evaluate = has_permission(
        "interview.evaluate"
    )

    evaluation_locked = (
        session.evaluation_status
        == "completed"
    )

    with st.form(
        key=(
            f"session_evaluation_form_"
            f"{session.session_id}"
        ),
        clear_on_submit=False,
    ):
        criterion_values: list[dict] = []

        for index, criterion in enumerate(
            session.evaluation_criteria,
            start=1,
        ):
            title = (
                f"{index}. {criterion.competency} "
                f"({criterion.weight}%)"
            )

            with st.container(border=True):
                st.markdown(f"### {title}")

                if criterion.description:
                    st.write(
                        criterion.description
                    )

                render_evidence_guidance(
                    criterion
                )

                rating_options = [
                    None,
                    1,
                    2,
                    3,
                    4,
                    5,
                ]

                current_rating_index = (
                    rating_options.index(
                        criterion.rating
                    )
                    if criterion.rating
                    in rating_options
                    else 0
                )

                rating = st.selectbox(
                    "Rating",
                    options=rating_options,
                    index=current_rating_index,
                    format_func=lambda value: (
                        "Select rating"
                        if value is None
                        else get_rating_display(value)
                    ),
                    key=(
                        f"evaluation_rating_"
                        f"{session.session_id}_"
                        f"{criterion.criterion_id}"
                    ),
                    disabled=(
                        evaluation_locked
                        or not can_evaluate
                    ),
                )

                comments = st.text_area(
                    "Evidence and Comments",
                    value=criterion.comments,
                    height=130,
                    placeholder=(
                        "Record examples from the "
                        "candidate's answers that support "
                        "this rating..."
                    ),
                    key=(
                        f"evaluation_comments_"
                        f"{session.session_id}_"
                        f"{criterion.criterion_id}"
                    ),
                    disabled=(
                        evaluation_locked
                        or not can_evaluate
                    ),
                )

                criterion_values.append(
                    {
                        "criterion_id": (
                            criterion.criterion_id
                        ),
                        "rating": rating,
                        "comments": comments,
                    }
                )

        st.markdown("### Overall Evaluation")

        evaluation_summary = st.text_area(
            "Evaluation Summary",
            value=session.evaluation_summary,
            height=180,
            placeholder=(
                "Summarize the candidate's overall "
                "performance, strengths, risks, and "
                "suitability for the role..."
            ),
            key=(
                f"evaluation_summary_"
                f"{session.session_id}"
            ),
            disabled=(
                evaluation_locked
                or not can_evaluate
            ),
        )

        current_recommendation_index = (
            RECOMMENDATION_OPTIONS.index(
                session.recommendation
            )
            if session.recommendation
            in RECOMMENDATION_OPTIONS
            else 0
        )

        recommendation = st.selectbox(
            "Overall Recommendation",
            options=RECOMMENDATION_OPTIONS,
            index=current_recommendation_index,
            format_func=lambda value: (
                "Select recommendation"
                if not value
                else value
            ),
            key=(
                f"evaluation_recommendation_"
                f"{session.session_id}"
            ),
            disabled=(
                evaluation_locked
                or not can_evaluate
            ),
        )

        if evaluation_locked:
            save_clicked = st.form_submit_button(
                "Evaluation Finalized",
                disabled=True,
                use_container_width=True,
            )
        else:
            save_clicked = st.form_submit_button(
                "Save Evaluation Draft",
                type="primary",
                use_container_width=True,
                disabled=not can_evaluate,
            )

    if not save_clicked:
        return

    require_permission("interview.evaluate")

    try:
        update_session_evaluation(
            session=session,
            criterion_updates=criterion_values,
            evaluation_summary=(
                evaluation_summary
            ),
            recommendation=recommendation,
        )

        st.session_state[
            "interview_evaluation_workspace_message"
        ] = "The evaluation draft was saved."

        st.rerun()

    except Exception as exc:
        st.error(
            f"Unable to save evaluation: {exc}"
        )


def render_finalize_evaluation(
    session: InterviewSession,
) -> None:
    can_finalize = has_permission(
        "interview.finalize"
    )
    st.markdown("### Finalize Evaluation")

    if session.evaluation_status == "completed":
        st.success(
            "This evaluation has been finalized."
        )

        if session.evaluation_completed_time:
            st.caption(
                "Finalized: "
                f"{session.evaluation_completed_time}"
            )

        return

    if session.status != "completed":
        st.info(
            "Complete the interview session before "
            "finalizing its evaluation."
        )
        return

    rated_count, total_count = (
        get_evaluation_completion_counts(
            session
        )
    )

    missing_items: list[str] = []

    if rated_count != total_count:
        missing_items.append(
            f"{total_count - rated_count} "
            "criterion rating(s)"
        )

    if not session.evaluation_summary.strip():
        missing_items.append(
            "overall evaluation summary"
        )

    if not session.recommendation.strip():
        missing_items.append(
            "overall recommendation"
        )

    if missing_items:
        st.warning(
            "Before finalization, complete: "
            + ", ".join(missing_items)
            + "."
        )
    else:
        st.success(
            "The evaluation contains all required "
            "information."
        )

    confirm_finalize = st.checkbox(
        "I confirm that this evaluation is complete.",
        key=(
            f"confirm_evaluation_finalize_"
            f"{session.session_id}"
        ),
    )

    finalize_clicked = st.button(
        "Finalize Evaluation",
        type="primary",
        use_container_width=True,
        disabled=(
            not confirm_finalize
            or bool(missing_items)
            or not can_finalize
        ),
        key=(
            f"finalize_evaluation_"
            f"{session.session_id}"
        ),
    )

    if not finalize_clicked:
        return

    require_permission("interview.finalize")

    try:
        complete_session_evaluation(
            session
        )

        st.session_state[
            "interview_evaluation_workspace_message"
        ] = (
            "The interview evaluation was finalized."
        )

        st.rerun()

    except Exception as exc:
        st.error(
            f"Unable to finalize evaluation: {exc}"
        )


def render_interview_session_evaluation(
    session: InterviewSession,
) -> None:
    message = st.session_state.pop(
        "interview_evaluation_workspace_message",
        None,
    )

    if message:
        st.success(message)

    st.markdown("## Interview Evaluation")

    mode_label = {
        "recruiter_led": "Recruiter-led",
        "candidate_async": "Candidate Self-service",
        "ai_chat": "AI Chat",
        "ai_voice": "AI Voice",
    }.get(
        session.interview_mode,
        session.interview_mode
        .replace("_", " ")
        .title(),
    )

    st.caption(
        f"Round {session.interview_round}"
        f" · {session.interview_stage}"
        f" · {mode_label}"
    )
    
    st.caption(
        "Rate each approved competency using evidence "
        "from the completed interview."
    )

    if session.status != "completed":
        st.warning(
            "The interview session is still in progress. "
            "You may review the scorecard, but the "
            "evaluation should normally be completed "
            "after the interview."
        )

    render_evaluation_header(session)

    st.divider()

    render_interview_evidence(session)

    st.divider()

    render_evaluation_form(session)

    st.divider()

    render_finalize_evaluation(session)