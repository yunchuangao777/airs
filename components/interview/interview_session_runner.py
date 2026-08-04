from __future__ import annotations

import streamlit as st

from services.permission_service import has_permission, require_permission

from services.interview_session_service import (
    InterviewSession,
    complete_interview_session,
    save_interview_session,
    set_current_question,
    start_interview_session,
    update_session_question,
)


STATUS_LABELS = {
    "draft": "Draft",
    "in_progress": "In Progress",
    "completed": "Completed",
    "cancelled": "Cancelled",
}

INTERVIEW_MODE_LABELS = {
    "recruiter_led": "Recruiter-led",
    "candidate_async": "Candidate Self-service",
    "ai_chat": "AI Chat",
    "ai_voice": "AI Voice",
}


def get_status_label(status: str) -> str:
    return STATUS_LABELS.get(
        status,
        status.replace("_", " ").title(),
    )


def get_answered_count(
    session: InterviewSession,
) -> int:
    return sum(
        1
        for question in session.questions
        if question.answered
    )


def render_session_header(
    session: InterviewSession,
) -> None:
    answered_count = get_answered_count(session)
    total_questions = len(session.questions)

    with st.container(border=True):
        left_col, right_col = st.columns([3, 2])

        with left_col:
            st.markdown("### Interview Session")
            st.markdown(
                f"## {session.candidate_name}"
            )

            st.write(
                f"**Position:** {session.job_title}"
            )

            if session.company:
                st.write(
                    f"**Company:** {session.company}"
                )

        with right_col:
            mode_label = INTERVIEW_MODE_LABELS.get(
                session.interview_mode,
                session.interview_mode
                .replace("_", " ")
                .title(),
            )

            st.write(
                f"**Status:** "
                f"{get_status_label(session.status)}"
            )

            st.write(
                f"**Round:** "
                f"{session.interview_round}"
            )

            st.write(
                f"**Stage:** "
                f"{session.interview_stage}"
            )

            st.write(
                f"**Mode:** {mode_label}"
            )

            st.write(
                f"**Interview type:** "
                f"{session.interview_type_label}"
            )

            st.write(
                f"**Planned duration:** "
                f"{session.duration_minutes} minutes"
            )

            st.write(
                f"**Session ID:** "
                f"`{session.session_id[:8]}`"
            )

    metric_col1, metric_col2, metric_col3 = (
        st.columns(3)
    )

    with metric_col1:
        st.metric(
            "Questions",
            total_questions,
        )

    with metric_col2:
        st.metric(
            "Answered",
            answered_count,
        )

    with metric_col3:
        completion_rate = (
            round(
                answered_count
                / total_questions
                * 100
            )
            if total_questions
            else 0
        )

        st.metric(
            "Completion",
            f"{completion_rate}%",
        )

    if total_questions:
        st.progress(
            answered_count / total_questions,
            text=(
                f"{answered_count} of "
                f"{total_questions} questions answered"
            ),
        )


def render_question_navigation(
    session: InterviewSession,
) -> None:
    """
    Let the interviewer jump directly to another question.
    """
    if not session.questions:
        return

    selector_key = (
        f"session_question_selector_"
        f"{session.session_id}"
    )

    pending_key = (
        f"pending_question_index_"
        f"{session.session_id}"
    )

    question_options = list(
        range(len(session.questions))
    )

    # Apply navigation requested during the previous run
    # before the selectbox widget is instantiated.
    pending_index = st.session_state.pop(
        pending_key,
        None,
    )

    if pending_index is not None:
        pending_index = max(
            0,
            min(
                int(pending_index),
                len(session.questions) - 1,
            ),
        )

        st.session_state[
            selector_key
        ] = pending_index

    # Protect against stale widget state.
    current_widget_value = st.session_state.get(
        selector_key
    )

    if current_widget_value not in question_options:
        st.session_state[
            selector_key
        ] = session.current_question_index

    selected_index = st.selectbox(
        "Go to question",
        options=question_options,
        format_func=lambda index: (
            f"{index + 1}. "
            f"{session.questions[index].competency}"
            + (
                " ✓"
                if session.questions[index].answered
                else ""
            )
        ),
        key=selector_key,
    )

    if selected_index != session.current_question_index:
        set_current_question(
            session=session,
            question_index=selected_index,
        )

        st.rerun()


def render_question_guidance(
    question,
) -> None:
    with st.expander(
        "Interviewer guidance",
        expanded=False,
    ):
        if question.reason:
            st.markdown("#### Why this question is included")
            st.write(question.reason)

        if question.strong_answer_indicators:
            st.markdown("#### Strong-answer indicators")

            for item in question.strong_answer_indicators:
                st.markdown(f"✅ {item}")

        if question.warning_signs:
            st.markdown("#### Warning signs")

            for item in question.warning_signs:
                st.markdown(f"⚠️ {item}")

        if question.suggested_follow_ups:
            st.markdown("#### Suggested follow-ups")

            for index, item in enumerate(
                question.suggested_follow_ups,
                start=1,
            ):
                st.markdown(
                    f"**{index}.** {item}"
                )


def save_current_question(
    session: InterviewSession,
    question_index: int,
    answer_text: str,
    interviewer_notes: str,
) -> None:
    update_session_question(
        session=session,
        question_index=question_index,
        answer_text=answer_text,
        interviewer_notes=interviewer_notes,
    )

def queue_question_navigation(
    session: InterviewSession,
    question_index: int,
) -> None:
    """
    Select a question on the next Streamlit rerun.
    """
    st.session_state[
        f"pending_question_index_{session.session_id}"
    ] = question_index

def render_current_question(
    session: InterviewSession,
) -> None:
    if not session.questions:
        st.warning(
            "This interview session contains no questions."
        )
        return

    question_index = max(
        0,
        min(
            session.current_question_index,
            len(session.questions) - 1,
        ),
    )

    question = session.questions[
        question_index
    ]

    question_number = question_index + 1
    total_questions = len(session.questions)

    with st.container(border=True):
        label_col, status_col = st.columns(
            [4, 1]
        )

        with label_col:
            st.caption(
                f"Question {question_number} "
                f"of {total_questions}"
            )

            st.markdown(
                f"### {question.question_text}"
            )

            detail_parts = [
                value
                for value in [
                    question.category,
                    question.competency,
                ]
                if value
            ]

            if detail_parts:
                st.caption(
                    " · ".join(detail_parts)
                )

        with status_col:
            if question.answered:
                st.success("Answered")
            else:
                st.info("Not answered")

        render_question_guidance(question)

    answer_key = (
        f"session_answer_"
        f"{session.session_id}_"
        f"{question.question_id}"
    )

    notes_key = (
        f"session_notes_"
        f"{session.session_id}_"
        f"{question.question_id}"
    )

    can_conduct = has_permission(
        "interview.conduct"
    )

    answer_text = st.text_area(
        "Candidate Answer",
        value=question.answer_text,
        height=220,
        placeholder=(
            "Record the candidate's response here..."
        ),
        key=answer_key,
        disabled=(
            session.status == "completed"
            or not can_conduct
        ),
    )

    interviewer_notes = st.text_area(
        "Interviewer Notes",
        value=question.interviewer_notes,
        height=120,
        placeholder=(
            "Record observations, evidence, concerns, "
            "or follow-up points..."
        ),
        key=notes_key,
        disabled=(
            session.status == "completed"
            or not can_conduct
        ),
    )

    if session.status == "completed":
        return

    previous_col, save_col, next_col = st.columns(
        [1, 2, 2]
    )

    with previous_col:
        previous_clicked = st.button(
            "Previous",
            key=(
                f"session_previous_"
                f"{session.session_id}_"
                f"{question.question_id}"
            ),
            disabled=(
                question_index == 0
                or not can_conduct
            ),
            use_container_width=True,
        )

    with save_col:
        save_clicked = st.button(
            "Save Answer",
            key=(
                f"session_save_"
                f"{session.session_id}_"
                f"{question.question_id}"
            ),
            use_container_width=True,
            disabled=not can_conduct,
        )

    with next_col:
        is_last_question = (
            question_index
            == total_questions - 1
        )

        next_label = (
            "Save Answer"
            if is_last_question
            else "Save & Next"
        )

        next_clicked = st.button(
            next_label,
            type="primary",
            key=(
                f"session_next_"
                f"{session.session_id}_"
                f"{question.question_id}"
            ),
            use_container_width=True,
            disabled=not can_conduct,
        )

    if previous_clicked:
        require_permission("interview.conduct")
        save_current_question(
            session=session,
            question_index=question_index,
            answer_text=answer_text,
            interviewer_notes=interviewer_notes,
        )

        next_index = question_index - 1

        set_current_question(
            session=session,
            question_index=next_index,
        )

        queue_question_navigation(
            session=session,
            question_index=next_index,
        )

        st.rerun()

    if save_clicked:
        require_permission("interview.conduct")
        save_current_question(
            session=session,
            question_index=question_index,
            answer_text=answer_text,
            interviewer_notes=interviewer_notes,
        )

        st.session_state[
            "interview_session_message"
        ] = (
            f"Question {question_number} was saved."
        )

        st.rerun()

    if next_clicked:
        require_permission("interview.conduct")
        save_current_question(
            session=session,
            question_index=question_index,
            answer_text=answer_text,
            interviewer_notes=interviewer_notes,
        )

        if not is_last_question:
            next_index = question_index + 1

            set_current_question(
                session=session,
                question_index=next_index,
            )

            queue_question_navigation(
                session=session,
                question_index=next_index,
            )

        st.rerun()


def render_overall_notes(
    session: InterviewSession,
) -> None:
    can_conduct = has_permission("interview.conduct")
    st.markdown("### Overall Interview Notes")

    notes_key = (
        f"session_overall_notes_"
        f"{session.session_id}"
    )

    overall_notes = st.text_area(
        "Notes",
        value=session.overall_notes,
        height=160,
        placeholder=(
            "Record overall observations that are not "
            "specific to one question..."
        ),
        label_visibility="collapsed",
        key=notes_key,
        disabled=(
            session.status == "completed"
            or not can_conduct
        ),
    )

    if session.status == "completed":
        return

    if st.button(
        "Save Overall Notes",
        key=(
            f"save_overall_notes_"
            f"{session.session_id}"
        ),
        disabled=not can_conduct,
    ):
        require_permission("interview.conduct")
        session.overall_notes = (
            overall_notes.strip()
        )

        save_interview_session(session)

        st.session_state[
            "interview_session_message"
        ] = "Overall interview notes were saved."

        st.rerun()


def render_completion_section(
    session: InterviewSession,
) -> None:
    can_conduct = has_permission("interview.conduct")
    st.markdown("### Complete Interview")

    answered_count = get_answered_count(session)
    total_questions = len(session.questions)
    unanswered_count = (
        total_questions - answered_count
    )

    if session.status == "completed":
        st.success(
            "This interview has been completed."
        )

        if session.completed_time:
            st.caption(
                f"Completed: {session.completed_time}"
            )

        return

    if unanswered_count:
        st.warning(
            f"{unanswered_count} question(s) do not yet "
            "have a candidate answer."
        )
    else:
        st.success(
            "All interview questions have answers."
        )

    confirm_complete = st.checkbox(
        "I confirm that the interview is finished.",
        key=(
            f"confirm_complete_"
            f"{session.session_id}"
        ),
    )

    complete_clicked = st.button(
        "Complete Interview",
        type="primary",
        disabled=(
            not confirm_complete
            or not can_conduct
        ),
        key=(
            f"complete_session_"
            f"{session.session_id}"
        ),
        use_container_width=True,
    )

    if complete_clicked:
        require_permission("interview.conduct")
        complete_interview_session(session)

        st.session_state[
            "interview_session_message"
        ] = (
            "The interview session was completed."
        )

        st.rerun()


def render_interview_session_runner(
    session: InterviewSession,
) -> None:
    message = st.session_state.pop(
        "interview_session_message",
        None,
    )

    if message:
        st.success(message)

    if session.status == "draft":
        render_session_header(session)

        st.info(
            "This session contains frozen copies of the "
            "approved questions and evaluation criteria."
        )

        can_conduct = has_permission(
            "interview.conduct"
        )

        start_clicked = st.button(
            "Start Interview",
            type="primary",
            key=(
                f"start_session_"
                f"{session.session_id}"
            ),
            use_container_width=True,
            disabled=not can_conduct,
            help=(
                None
                if can_conduct
                else (
                    "Your role has read-only access "
                    "to interview sessions."
                )
            ),
        )

        if start_clicked:
            require_permission(
                "interview.conduct",
                message=(
                    "You do not have permission to "
                    "start or conduct interviews."
                ),
            )

            start_interview_session(session)

            st.session_state[
                "interview_session_message"
            ] = "The interview session has started."

            st.rerun()

        return

    render_session_header(session)

    st.divider()

    render_question_navigation(session)

    render_current_question(session)

    st.divider()

    render_overall_notes(session)

    st.divider()

    render_completion_section(session)