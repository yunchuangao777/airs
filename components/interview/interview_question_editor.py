from __future__ import annotations

import streamlit as st

from services.permission_service import has_permission, require_permission

from services.interview_package_service import (
    InterviewPackage,
)
from services.interview_question_service import (
    InterviewQuestionSet,
    add_custom_question,
    get_or_create_question_set,
    get_selected_questions,
    save_question_set,
    utc_now_iso,
)


CATEGORY_OPTIONS = [
    "opening",
    "experience",
    "technical",
    "behavioral",
    "problem_solving",
    "leadership",
    "motivation",
    "concern_probe",
    "closing",
    "general",
]


def format_category(value: str) -> str:
    """
    Convert a stored category into a friendly label.
    """
    return (
        str(value)
        .replace("_", " ")
        .strip()
        .title()
    )


def build_editor_key(
    package: InterviewPackage,
) -> str:
    """
    Create a candidate-job-specific widget-key prefix.
    """
    return (
        f"{package.job_id}_"
        f"{package.candidate_id}"
    )


def render_question_set_summary(
    question_set: InterviewQuestionSet,
) -> None:
    """
    Show high-level counts for the editable question set.
    """
    selected_questions = get_selected_questions(
        question_set
    )

    ai_count = sum(
        1
        for question in question_set.questions
        if question.source == "ai"
    )

    custom_count = sum(
        1
        for question in question_set.questions
        if question.source == "recruiter"
    )

    metric_col1, metric_col2, metric_col3, metric_col4 = (
        st.columns(4)
    )

    with metric_col1:
        st.metric(
            "Total Questions",
            len(question_set.questions),
        )

    with metric_col2:
        st.metric(
            "Selected",
            len(selected_questions),
        )

    with metric_col3:
        st.metric(
            "AI Generated",
            ai_count,
        )

    with metric_col4:
        st.metric(
            "Recruiter Added",
            custom_count,
        )


def render_question_guidance(
    question,
) -> None:
    """
    Display the supporting AI guidance for one question.
    """
    detail_col1, detail_col2 = st.columns(2)

    with detail_col1:
        st.caption("Category")
        st.write(
            format_category(
                question.category
            )
        )

    with detail_col2:
        st.caption("Competency")
        st.write(
            question.competency
            or "Not specified"
        )

    if question.reason:
        st.markdown("##### Why ask this")
        st.write(question.reason)

    st.markdown(
        "##### Strong-answer indicators"
    )

    if question.strong_answer_indicators:
        for item in (
            question.strong_answer_indicators
        ):
            st.markdown(f"✅ {item}")
    else:
        st.caption(
            "No strong-answer indicators recorded."
        )

    st.markdown("##### Warning signs")

    if question.warning_signs:
        for item in question.warning_signs:
            st.markdown(f"⚠️ {item}")
    else:
        st.caption(
            "No warning signs recorded."
        )

    st.markdown("##### Suggested follow-ups")

    if question.suggested_follow_ups:
        for item in (
            question.suggested_follow_ups
        ):
            st.markdown(f"- {item}")
    else:
        st.caption(
            "No follow-up questions recorded."
        )


def render_existing_questions_form(
    question_set: InterviewQuestionSet,
    editor_key: str,
) -> None:
    """
    Render selection and editing controls for all questions.
    """
    can_edit_questions = has_permission(
        "interview.create"
    )
    if not question_set.questions:
        st.info(
            "No questions are available in this "
            "question set."
        )
        return

    st.markdown("### Select and Edit Questions")

    st.caption(
        "Selected questions will become the approved "
        "interview script. Editing does not overwrite "
        "the original AI question."
    )

    with st.form(
        key=f"question_editor_form_{editor_key}",
        clear_on_submit=False,
    ):
        form_values: list[dict] = []

        for index, question in enumerate(
            question_set.questions,
            start=1,
        ):
            source_label = (
                "AI"
                if question.source == "ai"
                else "Recruiter"
            )

            expander_title = (
                f"{question.question_id} · "
                f"{source_label} · "
                f"{format_category(question.category)}"
            )

            with st.expander(
                expander_title,
                expanded=False,
            ):
                selected = st.checkbox(
                    "Include in final interview",
                    value=question.selected,
                    disabled=not can_edit_questions,
                    key=(
                        f"question_selected_"
                        f"{editor_key}_"
                        f"{question.question_id}"
                    ),
                )

                edited_question = st.text_area(
                    "Question",
                    value=question.edited_question,
                    height=110,
                    disabled=not can_edit_questions,
                    key=(
                        f"question_text_"
                        f"{editor_key}_"
                        f"{question.question_id}"
                    ),
                )

                if (
                    question.source == "ai"
                    and question.original_question
                    and question.edited_question
                    != question.original_question
                ):
                    with st.expander(
                        "View original AI question",
                        expanded=False,
                    ):
                        st.write(
                            question.original_question
                        )

                with st.expander(
                    "View question guidance",
                    expanded=False,
                ):
                    render_question_guidance(
                        question
                    )

                form_values.append(
                    {
                        "question": question,
                        "selected": selected,
                        "edited_question": (
                            edited_question
                        ),
                    }
                )

        save_clicked = st.form_submit_button(
            "Save Approved Question Set",
            type="primary",
            use_container_width=True,
            disabled=not can_edit_questions,
        )

    if not save_clicked:
        return

    require_permission("interview.create")

    empty_selected_questions: list[str] = []

    for item in form_values:
        question = item["question"]
        edited_text = (
            item["edited_question"].strip()
        )
        selected = bool(item["selected"])

        if selected and not edited_text:
            empty_selected_questions.append(
                question.question_id
            )
            continue

        question.selected = selected
        question.edited_question = edited_text
        question.updated_time = utc_now_iso()

    if empty_selected_questions:
        st.error(
            "The following selected questions have "
            "empty text: "
            + ", ".join(
                empty_selected_questions
            )
        )
        return

    save_question_set(question_set)

    st.session_state[
        "interview_question_message"
    ] = (
        "The approved interview question set "
        "was saved successfully."
    )

    st.rerun()


def render_add_custom_question(
    question_set: InterviewQuestionSet,
    editor_key: str,
) -> None:
    """
    Render the recruiter-created question form.
    """
    can_edit_questions = has_permission(
        "interview.create"
    )
    st.markdown("### Add New Question")

    with st.expander(
        "Create a recruiter question",
        expanded=False,
    ):
        with st.form(
            key=f"add_custom_question_{editor_key}",
            clear_on_submit=True,
        ):
            question_text = st.text_area(
                "Question *",
                disabled=not can_edit_questions,
                placeholder=(
                    "Example: What would your priorities "
                    "be during your first 90 days?"
                ),
                height=110,
            )

            custom_col1, custom_col2 = (
                st.columns(2)
            )

            with custom_col1:
                category = st.selectbox(
                    "Category",
                    options=CATEGORY_OPTIONS,
                    disabled=not can_edit_questions,
                    index=9,
                    format_func=format_category,
                )

            with custom_col2:
                competency = st.text_input(
                    "Competency",
                    disabled=not can_edit_questions,
                    placeholder=(
                        "Example: Role Planning"
                    ),
                )

            reason = st.text_area(
                "Why ask this question?",
                disabled=not can_edit_questions,
                placeholder=(
                    "Optional explanation of what "
                    "the question should assess."
                ),
                height=90,
            )

            add_clicked = st.form_submit_button(
                "Add Question",
                type="primary",
                use_container_width=True,
                disabled=not can_edit_questions,
            )

    if not add_clicked:
        return

    require_permission(
        "interview.create"
    )

    if not question_text.strip():
        st.error(
            "Question text is required."
        )
        return

    try:
        new_question = add_custom_question(
            question_set=question_set,
            question_text=question_text,
            category=category,
            competency=competency,
            reason=reason,
        )

        st.session_state[
            "interview_question_message"
        ] = (
            f"{new_question.question_id} was "
            "added successfully."
        )

        st.rerun()

    except Exception as exc:
        st.error(
            f"Unable to add the question: {exc}"
        )


def render_final_script_preview(
    question_set: InterviewQuestionSet,
) -> None:
    """
    Display the currently approved interview script.
    """
    selected_questions = get_selected_questions(
        question_set
    )

    st.markdown("### Final Interview Script")

    if not selected_questions:
        st.warning(
            "No questions are currently selected."
        )
        return

    st.caption(
        f"{len(selected_questions)} question(s) "
        "are approved for the interview."
    )

    for index, question in enumerate(
        selected_questions,
        start=1,
    ):
        with st.container(border=True):
            st.markdown(
                f"**{index}. "
                f"{question.edited_question}**"
            )

            detail_parts = [
                format_category(
                    question.category
                )
            ]

            if question.competency:
                detail_parts.append(
                    question.competency
                )

            detail_parts.append(
                (
                    "AI generated"
                    if question.source == "ai"
                    else "Recruiter added"
                )
            )

            st.caption(
                " · ".join(detail_parts)
            )


def render_interview_question_editor(
    package: InterviewPackage,
) -> None:
    """
    Render the complete recruiter question workspace.
    """
    message = st.session_state.pop(
        "interview_question_message",
        None,
    )

    if message:
        st.success(message)

    question_set = get_or_create_question_set(
        package
    )

    editor_key = build_editor_key(
        package
    )

    st.markdown("## Interview Questions")

    st.caption(
        "Review the AI-generated question bank, "
        "select the final questions, edit wording, "
        "and add recruiter-created questions."
    )

    render_question_set_summary(
        question_set
    )

    st.divider()

    render_existing_questions_form(
        question_set=question_set,
        editor_key=editor_key,
    )

    st.divider()

    render_add_custom_question(
        question_set=question_set,
        editor_key=editor_key,
    )

    st.divider()

    render_final_script_preview(
        question_set
    )