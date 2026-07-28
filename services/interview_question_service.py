from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from services.interview_package_service import (
    InterviewPackage,
)


QUESTION_SET_DIR = Path(
    "outputs/interview_question_sets"
)

QUESTION_SET_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


QuestionSource = Literal[
    "ai",
    "recruiter",
]


class EditableInterviewQuestion(BaseModel):
    """
    One recruiter-editable interview question.

    The original AI question is preserved separately from
    the recruiter-edited version.
    """

    question_id: str

    source: QuestionSource = "ai"

    original_question: str = ""

    edited_question: str

    selected: bool = True

    category: str = "general"

    competency: str = ""

    reason: str = ""

    strong_answer_indicators: list[str] = Field(
        default_factory=list
    )

    warning_signs: list[str] = Field(
        default_factory=list
    )

    suggested_follow_ups: list[str] = Field(
        default_factory=list
    )

    created_time: str

    updated_time: str


class InterviewQuestionSet(BaseModel):
    """
    Recruiter-approved interview script for one
    candidate-job pair.
    """

    question_set_id: str

    package_id: str

    candidate_id: str

    job_id: str

    application_id: str | None = None

    candidate_name: str

    job_title: str

    questions: list[EditableInterviewQuestion] = Field(
        default_factory=list
    )

    created_time: str

    updated_time: str


def utc_now_iso() -> str:
    """
    Return the current time as a timezone-aware UTC string.
    """
    return datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")


def get_question_set_path(
    candidate_id: str,
    job_id: str,
) -> Path:
    """
    Return the question-set path for a candidate-job pair.
    """
    return (
        QUESTION_SET_DIR
        / f"{job_id}__{candidate_id}.json"
    )


def create_question_set_from_package(
    package: InterviewPackage,
) -> InterviewQuestionSet:
    """
    Convert AI-generated package questions into a
    recruiter-editable question set.
    """
    now = utc_now_iso()

    editable_questions: list[
        EditableInterviewQuestion
    ] = []

    for index, question in enumerate(
        package.generated_content.questions,
        start=1,
    ):
        question_id = (
            question.question_id
            or f"Q{index}"
        )

        editable_questions.append(
            EditableInterviewQuestion(
                question_id=question_id,
                source="ai",
                original_question=question.question,
                edited_question=question.question,
                selected=True,
                category=str(
                    question.category
                ),
                competency=question.competency,
                reason=question.reason,
                strong_answer_indicators=list(
                    question.strong_answer_indicators
                ),
                warning_signs=list(
                    question.warning_signs
                ),
                suggested_follow_ups=list(
                    question.suggested_follow_ups
                ),
                created_time=now,
                updated_time=now,
            )
        )

    return InterviewQuestionSet(
        question_set_id=str(uuid4()),
        package_id=package.package_id,
        candidate_id=package.candidate_id,
        job_id=package.job_id,
        application_id=package.application_id,
        candidate_name=package.candidate_name,
        job_title=package.job_title,
        questions=editable_questions,
        created_time=now,
        updated_time=now,
    )


def save_question_set(
    question_set: InterviewQuestionSet,
) -> Path:
    """
    Save the recruiter-approved question set atomically.
    """
    question_set.updated_time = utc_now_iso()

    output_path = get_question_set_path(
        candidate_id=question_set.candidate_id,
        job_id=question_set.job_id,
    )

    temporary_path = output_path.with_suffix(
        ".json.tmp"
    )

    with open(
        temporary_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            question_set.model_dump(
                mode="json"
            ),
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporary_path.replace(output_path)

    return output_path


def load_question_set(
    candidate_id: str,
    job_id: str,
) -> InterviewQuestionSet | None:
    """
    Load and validate a saved question set.
    """
    path = get_question_set_path(
        candidate_id=candidate_id,
        job_id=job_id,
    )

    if not path.exists():
        return None

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return InterviewQuestionSet.model_validate(
            data
        )

    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            f"Unable to load question set "
            f"{path}: {exc}"
        ) from exc


def get_or_create_question_set(
    package: InterviewPackage,
) -> InterviewQuestionSet:
    """
    Load an existing question set or initialize one
    from the current interview package.
    """
    existing = load_question_set(
        candidate_id=package.candidate_id,
        job_id=package.job_id,
    )

    if existing is not None:
        return existing

    question_set = create_question_set_from_package(
        package
    )

    save_question_set(question_set)

    return question_set


def add_custom_question(
    question_set: InterviewQuestionSet,
    question_text: str,
    category: str = "general",
    competency: str = "",
    reason: str = "",
) -> EditableInterviewQuestion:
    """
    Add a recruiter-created question to the question set.
    """
    cleaned_question = question_text.strip()

    if not cleaned_question:
        raise ValueError(
            "Question text cannot be empty."
        )

    now = utc_now_iso()

    existing_custom_count = sum(
        1
        for question in question_set.questions
        if question.source == "recruiter"
    )

    custom_question = EditableInterviewQuestion(
        question_id=(
            f"CUSTOM-{existing_custom_count + 1}"
        ),
        source="recruiter",
        original_question="",
        edited_question=cleaned_question,
        selected=True,
        category=category.strip() or "general",
        competency=competency.strip(),
        reason=reason.strip(),
        strong_answer_indicators=[],
        warning_signs=[],
        suggested_follow_ups=[],
        created_time=now,
        updated_time=now,
    )

    question_set.questions.append(
        custom_question
    )

    save_question_set(question_set)

    return custom_question


def delete_custom_question(
    question_set: InterviewQuestionSet,
    question_id: str,
) -> bool:
    """
    Delete a recruiter-created question.

    AI-generated questions are preserved for traceability
    and should be deselected instead of deleted.
    """
    original_count = len(
        question_set.questions
    )

    question_set.questions = [
        question
        for question in question_set.questions
        if not (
            question.question_id == question_id
            and question.source == "recruiter"
        )
    ]

    changed = (
        len(question_set.questions)
        < original_count
    )

    if changed:
        save_question_set(question_set)

    return changed


def get_selected_questions(
    question_set: InterviewQuestionSet,
) -> list[EditableInterviewQuestion]:
    """
    Return only the recruiter-approved questions.
    """
    return [
        question
        for question in question_set.questions
        if (
            question.selected
            and question.edited_question.strip()
        )
    ]