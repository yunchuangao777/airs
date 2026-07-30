from __future__ import annotations

import streamlit as st
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from services.interview_session_service import (
    find_session_by_candidate_token,
)
from services.ai_interview_service import (
    review_candidate_answer,
    save_ai_answer_review,
    save_ai_follow_up_answer,
    finish_ai_interview,
    generate_ai_evaluation_draft,
    apply_ai_evaluation_draft,
)

def get_candidate_token() -> str:
    """
    Read the candidate interview token from the URL.

    Expected URL:
    http://localhost:8501/?interview_token=...
    """
    token = st.query_params.get(
        "interview_token",
        "",
    )

    return str(token or "").strip()


def show_invalid_link_message() -> None:
    """
    Display a neutral error without revealing whether
    a specific interview exists.
    """
    st.error(
        "This interview link is invalid, disabled, "
        "or no longer available."
    )

    st.info(
        "Please contact the recruiter who sent you "
        "the interview invitation."
    )

def get_question_text(question: Any) -> str:
    """
    Return question text from a session question object.

    Different versions of the question model may use
    slightly different field names.
    """
    possible_fields = [
        "question_text",
        "text",
        "question",
        "content",
    ]

    for field_name in possible_fields:
        value = getattr(
            question,
            field_name,
            None,
        )

        if value:
            return str(value).strip()

    if isinstance(question, dict):
        for field_name in possible_fields:
            value = question.get(field_name)

            if value:
                return str(value).strip()

    return "Question text is unavailable."

def initialize_public_interview_state(
    interview_session,
    token: str,
) -> None:
    """
    Initialize browser session state for the candidate.
    """
    session_id = interview_session.session_id

    existing_session_id = st.session_state.get(
        "public_interview_session_id"
    )

    if existing_session_id != session_id:
        st.session_state[
            "public_interview_token"
        ] = token

        st.session_state[
            "public_interview_session_id"
        ] = session_id

        st.session_state[
            "public_interview_started"
        ] = False

        st.session_state[
            "public_question_index"
        ] = 0

        st.session_state[
            "public_current_answer"
        ] = ""

        st.session_state[
            "public_follow_up_active"
        ] = False

        st.session_state[
            "public_follow_up_answer"
        ] = ""

        st.session_state[
            "public_last_saved_question"
        ] = None

        st.session_state[
            "public_finalization_attempted"
        ] = False

        st.session_state[
            "public_finalization_error"
        ] = ""


def render_interview_landing(
    interview_session,
    token: str,
) -> None:
    """
    Render candidate welcome, interview details,
    consent, and the Start Interview button.
    """
    st.success("Your interview link is valid.")

    st.subheader(
        f"Welcome, "
        f"{interview_session.candidate_name}"
    )

    st.write(
        "You have been invited to complete an "
        "AI-assisted interview."
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Position**")
        st.write(
            interview_session.job_title
            or "Not specified"
        )

        st.markdown("**Company**")
        st.write(
            interview_session.company
            or "Not specified"
        )

    with col2:
        st.markdown("**Interview type**")
        st.write(
            interview_session.interview_type_label
            or interview_session.interview_type
            or "AI interview"
        )

        st.markdown("**Estimated duration**")

        duration = (
            interview_session.duration_minutes
            or 30
        )

        st.write(
            f"Approximately {duration} minutes"
        )

    st.divider()

    st.markdown("### Before you begin")

    st.write(
        """
        Please complete the interview in a quiet place.
        Read each question carefully and provide your
        answer in your own words.

        Your responses will be saved and reviewed by
        the hiring team.
        """
    )

    consent_checked = st.checkbox(
        "I understand that this interview is conducted "
        "with the assistance of AI and that my responses "
        "will be recorded and evaluated.",
        key="public_interview_consent",
    )

    if st.button(
        "Start Interview",
        type="primary",
        use_container_width=True,
        disabled=not consent_checked,
    ):
        st.session_state[
            "public_interview_started"
        ] = True

        st.session_state[
            "public_question_index"
        ] = 0

        st.session_state[
            "public_current_answer"
        ] = ""

        st.rerun()

def move_to_next_public_question(
    interview_session,
) -> None:
    """
    Move the candidate to the next interview question.
    """
    current_index = int(
        st.session_state.get(
            "public_question_index",
            0,
        )
    )

    next_index = current_index + 1

    st.session_state[
        "public_question_index"
    ] = next_index

    st.session_state[
        "public_current_answer"
    ] = ""

    st.session_state[
        "public_follow_up_active"
    ] = False

    st.session_state[
        "public_follow_up_answer"
    ] = ""

    st.session_state[
        "public_last_saved_question"
    ] = None


def render_public_interview_complete(
    interview_session,
) -> None:
    """
    Render the candidate-facing completion page.

    Do not display the AI evaluation or recommendation
    to the candidate.
    """
    st.success("Interview completed")

    st.subheader(
        "Thank you for completing your interview."
    )

    st.write(
        f"Your responses for the "
        f"**{interview_session.job_title}** position "
        "have been saved successfully."
    )

    st.info(
        "The hiring team will review your responses. "
        "You may now close this browser window."
    )

    st.divider()

    st.caption(
        "For security, please do not share your "
        "interview link with anyone."
    )


def render_public_follow_up(
    interview_session,
    current_index: int,
    follow_up_question: str,
) -> None:
    """
    Render and save the optional AI follow-up answer.
    """
    st.info(
        "The interviewer has one follow-up question."
    )

    st.markdown("### Follow-up question")

    st.write(follow_up_question)

    follow_up_key = (
        f"public_follow_up_"
        f"{interview_session.session_id}_"
        f"{current_index}"
    )

    current_question = (
        interview_session.questions[
            current_index
        ]
    )

    existing_follow_up_answer = str(
        getattr(
            current_question,
            "ai_follow_up_answer",
            "",
        )
        or ""
    )

    if follow_up_key not in st.session_state:
        st.session_state[follow_up_key] = (
            existing_follow_up_answer
        )

    follow_up_answer = st.text_area(
        "Your follow-up answer",
        key=follow_up_key,
        height=180,
        placeholder=(
            "Type your follow-up answer here..."
        ),
    )

    cleaned_follow_up = str(
        follow_up_answer or ""
    ).strip()

    st.divider()

    button_col1, button_col2 = st.columns(
        [3, 1]
    )

    with button_col1:
        continue_clicked = st.button(
            "Save and Continue",
            type="primary",
            use_container_width=True,
            disabled=not bool(cleaned_follow_up),
        )

    with button_col2:
        exit_clicked = st.button(
            "Exit",
            key="public_follow_up_exit",
            use_container_width=True,
        )

    if exit_clicked:
        st.session_state[
            "public_interview_started"
        ] = False

        st.rerun()

    if continue_clicked:
        if not cleaned_follow_up:
            st.warning(
                "Please enter your follow-up answer."
            )
            return

        try:
            with st.spinner(
                "Saving your follow-up answer..."
            ):
                updated_session = (
                    save_ai_follow_up_answer(
                        session=interview_session,
                        question_index=current_index,
                        follow_up_answer=(
                            cleaned_follow_up
                        ),
                    )
                )

            move_to_next_public_question(
                updated_session
            )

            st.rerun()

        except Exception as exc:
            st.error(
                "The follow-up answer could not "
                "be saved."
            )

            st.info(
                "Please wait a moment and try again."
            )

            st.exception(exc)


def finalize_public_ai_interview(
    interview_session,
):
    """
    Complete the interview and generate an AI evaluation
    draft for later recruiter review.

    Interview completion is saved first so that an AI
    evaluation failure does not lose candidate answers.
    """
    updated_session = interview_session

    # First, mark the interview itself as completed.
    if updated_session.status != "completed":
        updated_session = finish_ai_interview(
            updated_session
        )

    # Avoid generating the evaluation again after a
    # Streamlit rerun or page refresh.
    if updated_session.evaluation_status != "draft":
        draft = generate_ai_evaluation_draft(
            updated_session
        )

        updated_session = apply_ai_evaluation_draft(
            session=updated_session,
            draft=draft,
        )

    return updated_session


def render_candidate_interview(
    interview_session,
) -> None:
    """
    Render the current interview question, save the
    candidate's answer, handle an optional AI follow-up,
    and advance to the next question.
    """
    questions = interview_session.questions or []

    if not questions:
        st.warning(
            "No interview questions are available "
            "for this session."
        )
        return

    current_index = int(
        st.session_state.get(
            "public_question_index",
            0,
        )
    )

    total_questions = len(questions)

    if current_index < 0:
        current_index = 0
        st.session_state[
            "public_question_index"
        ] = 0

    # All questions have been completed.
    if current_index >= total_questions:
        finalization_attempted = (
            st.session_state.get(
                "public_finalization_attempted",
                False,
            )
        )

        if not finalization_attempted:
            st.session_state[
                "public_finalization_attempted"
            ] = True

            try:
                with st.spinner(
                    "Saving your completed interview..."
                ):
                    interview_session = (
                        finalize_public_ai_interview(
                            interview_session
                        )
                    )

                st.session_state[
                    "public_finalization_error"
                ] = ""

            except Exception as exc:
                # The answers may already be saved and the
                # interview may already be completed. Do not
                # expose internal AI errors to the candidate.
                st.session_state[
                    "public_finalization_error"
                ] = str(exc)

        render_public_interview_complete(
            interview_session
        )
        return

    current_question = questions[current_index]

    question_text = get_question_text(
        current_question
    )

    st.caption(
        f"Question {current_index + 1} "
        f"of {total_questions}"
    )

    progress_value = (
        current_index / total_questions
    )

    st.progress(progress_value)

    st.subheader(question_text)

    # Determine whether the question already contains
    # an unanswered AI follow-up.
    follow_up_question = str(
        getattr(
            current_question,
            "ai_follow_up_question",
            "",
        )
        or ""
    ).strip()

    follow_up_answer = str(
        getattr(
            current_question,
            "ai_follow_up_answer",
            "",
        )
        or ""
    ).strip()

    show_follow_up = (
        bool(follow_up_question)
        and not bool(follow_up_answer)
    )

    if show_follow_up:
        render_public_follow_up(
            interview_session=interview_session,
            current_index=current_index,
            follow_up_question=follow_up_question,
        )
        return

    answer_key = (
        f"public_answer_"
        f"{interview_session.session_id}_"
        f"{current_index}"
    )

    existing_answer = str(
        getattr(
            current_question,
            "answer_text",
            "",
        )
        or ""
    )

    if answer_key not in st.session_state:
        st.session_state[answer_key] = (
            existing_answer
        )

    answer_text = st.text_area(
        "Your answer",
        key=answer_key,
        height=220,
        placeholder=(
            "Type your answer here. Include specific "
            "examples where possible."
        ),
    )

    character_count = len(
        str(answer_text or "").strip()
    )

    st.caption(
        f"{character_count} characters"
    )

    st.divider()

    button_col1, button_col2 = st.columns(
        [3, 1]
    )

    with button_col1:
        submit_clicked = st.button(
            "Submit Answer",
            type="primary",
            use_container_width=True,
            disabled=character_count == 0,
        )

    with button_col2:
        exit_clicked = st.button(
            "Exit",
            use_container_width=True,
        )

    if exit_clicked:
        st.session_state[
            "public_interview_started"
        ] = False

        st.rerun()

    if submit_clicked:
        cleaned_answer = str(
            answer_text or ""
        ).strip()

        if not cleaned_answer:
            st.warning(
                "Please enter an answer before "
                "continuing."
            )
            return

        try:
            with st.spinner(
                "Reviewing your answer..."
            ):
                review = review_candidate_answer(
                    session=interview_session,
                    question_index=current_index,
                    answer_text=cleaned_answer,
                )

                updated_session = (
                    save_ai_answer_review(
                        session=interview_session,
                        question_index=current_index,
                        answer_text=cleaned_answer,
                        review=review,
                    )
                )

            updated_question = (
                updated_session.questions[
                    current_index
                ]
            )

            new_follow_up = str(
                getattr(
                    updated_question,
                    "ai_follow_up_question",
                    "",
                )
                or ""
            ).strip()

            if new_follow_up:
                st.session_state[
                    "public_follow_up_active"
                ] = True

                st.rerun()

            move_to_next_public_question(
                updated_session
            )

            st.rerun()

        except Exception as exc:
            st.error(
                "We could not process your answer. "
                "Your interview has not advanced."
            )

            st.info(
                "Please wait a moment and submit "
                "the answer again."
            )

            st.exception(exc)

                
def render_public_interview_page() -> None:
    """
    Public candidate-facing interview page.
    """
    st.set_page_config(
        page_title="Candidate Interview",
        page_icon="🎤",
        layout="centered",
    )

    st.title("AI Interview")

    token = get_candidate_token()

    if not token:
        show_invalid_link_message()
        return

    interview_session = (
        find_session_by_candidate_token(token)
    )

    if interview_session is None:
        show_invalid_link_message()
        return

    if not interview_session.candidate_access_enabled:
        show_invalid_link_message()
        return

    if interview_session.interview_mode != "ai_chat":
        show_invalid_link_message()
        return

    initialize_public_interview_state(
        interview_session=interview_session,
        token=token,
    )

    interview_started = (
        st.session_state.get(
            "public_interview_started",
            False,
        )
    )

    if not interview_started:
        render_interview_landing(
            interview_session=interview_session,
            token=token,
        )
        return

    render_candidate_interview(
        interview_session=interview_session,
    )


if __name__ == "__main__":
    render_public_interview_page()