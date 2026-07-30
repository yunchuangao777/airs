from __future__ import annotations

import streamlit as st

from services.ai_interview_service import (
    apply_ai_evaluation_draft,
    finish_ai_interview,
    generate_ai_evaluation_draft,
    review_candidate_answer,
    save_ai_answer_review,
    save_ai_follow_up_answer,
)
from services.interview_session_service import (
    accept_ai_interview_consent,
    load_all_interview_sessions,
    load_interview_session,
    set_current_question,
)


def _load_ai_sessions():
    return [
        session
        for session in load_all_interview_sessions()
        if session.interview_mode == "ai_chat"
    ]


def render_ai_interview_page() -> None:
    st.title("AI Interview")
    st.caption(
        "Candidate-facing text interview. During development, select an "
        "AI Chat session below. A secure link can replace this selector later."
    )

    sessions = _load_ai_sessions()
    if not sessions:
        st.info(
            "No AI Chat session exists. Create one from Interview Session "
            "by choosing Interview Mode: AI Chat."
        )
        return

    session_lookup = {session.session_id: session for session in sessions}
    selected_id = st.selectbox(
        "AI interview session",
        options=list(session_lookup),
        format_func=lambda session_id: (
            f"{session_lookup[session_id].candidate_name} · "
            f"{session_lookup[session_id].job_title} · "
            f"Round {session_lookup[session_id].interview_round} · "
            f"{session_lookup[session_id].status.title()}"
        ),
        key="ai_interview_session_id",
    )

    session = load_interview_session(selected_id)
    if session is None:
        st.error("The selected interview session could not be loaded.")
        return

    st.markdown(f"## {session.job_title}")
    st.caption(
        f"{session.company or 'Company'} · Round {session.interview_round} · "
        f"{session.interview_stage}"
    )

    if session.status == "completed":
        st.success("This interview has been completed.")
        if session.evaluation_status == "draft":
            st.info("An AI evaluation draft is ready for recruiter review.")
        return

    if session.consent_status != "accepted":
        st.markdown("### Before you begin")
        st.write(
            "You will interact with an AI interview assistant. Your typed "
            "responses will be stored and may be summarized and evaluated "
            "by AI. A recruiter should review the resulting draft before "
            "any hiring decision."
        )
        consent = st.checkbox(
            "I understand and consent to this AI-assisted interview.",
            key=f"ai_consent_{session.session_id}",
        )
        if st.button(
            "Accept and Begin",
            disabled=not consent,
            type="primary",
            use_container_width=True,
        ):
            accept_ai_interview_consent(session)
            st.rerun()
        return

    total = len(session.questions)
    if total == 0:
        st.warning("This session contains no interview questions.")
        return

    index = min(max(session.current_question_index, 0), total - 1)
    question = session.questions[index]

    answered_count = sum(1 for item in session.questions if item.answered)
    st.progress(answered_count / total)
    st.caption(f"Question {index + 1} of {total}")

    with st.container(border=True):
        st.markdown(f"### {question.question_text}")
        if question.competency:
            st.caption(question.competency)

    if question.ai_follow_up_question and not question.ai_follow_up_answer:
        st.markdown("#### Follow-up question")
        st.write(question.ai_follow_up_question)
        follow_up_answer = st.text_area(
            "Your follow-up answer",
            height=160,
            key=f"ai_follow_up_answer_{session.session_id}_{question.question_id}",
        )
        if st.button(
            "Submit Follow-up",
            disabled=not follow_up_answer.strip(),
            type="primary",
            use_container_width=True,
        ):
            save_ai_follow_up_answer(session, index, follow_up_answer)
            if index < total - 1:
                set_current_question(session, index + 1)
            st.rerun()
        return

    if not question.answered:
        answer = st.text_area(
            "Your answer",
            height=220,
            placeholder="Type your answer here...",
            key=f"ai_answer_{session.session_id}_{question.question_id}",
        )

        if st.button(
            "Submit Answer",
            disabled=not answer.strip(),
            type="primary",
            use_container_width=True,
        ):
            try:
                with st.spinner("Reviewing your answer..."):
                    review = review_candidate_answer(session, index, answer)
                    save_ai_answer_review(session, index, answer, review)

                refreshed = load_interview_session(session.session_id)
                if (
                    refreshed is not None
                    and not refreshed.questions[index].ai_follow_up_question
                    and index < total - 1
                ):
                    set_current_question(refreshed, index + 1)
                st.rerun()
            except Exception as exc:
                st.error(f"Unable to process the answer: {exc}")
        return

    if index < total - 1:
        if st.button("Continue", type="primary", use_container_width=True):
            set_current_question(session, index + 1)
            st.rerun()
        return

    st.success("All interview questions have been answered.")
    if st.button("Complete Interview", type="primary", use_container_width=True):
        try:
            with st.spinner("Preparing the recruiter evaluation draft..."):
                finish_ai_interview(session)
                completed = load_interview_session(session.session_id)
                if completed is None:
                    raise RuntimeError("Unable to reload the completed session.")
                draft = generate_ai_evaluation_draft(completed)
                apply_ai_evaluation_draft(completed, draft)
            st.rerun()
        except Exception as exc:
            st.error(f"Unable to complete the interview: {exc}")
