from __future__ import annotations

import os
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field

from services.interview_session_service import (
    InterviewSession,
    SessionAuditEvent,
    complete_interview_session,
    save_interview_session,
    utc_now_iso,
)

AI_INTERVIEW_MODEL = os.getenv(
    "OPENAI_AI_INTERVIEW_MODEL",
    os.getenv("OPENAI_INTERVIEW_MODEL", "gpt-4o-mini"),
)


class AnswerReview(BaseModel):
    answer_summary: str
    interviewer_notes: str
    ask_follow_up: bool
    follow_up_question: str = ""


class CriterionDraft(BaseModel):
    criterion_id: str
    rating: int = Field(ge=1, le=5)
    comments: str


class EvaluationDraft(BaseModel):
    criteria: list[CriterionDraft]
    evaluation_summary: str
    recommendation: Literal[
        "Proceed",
        "Proceed with Reservations",
        "Hold",
        "Do Not Proceed",
    ]


def _client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def review_candidate_answer(
    session: InterviewSession,
    question_index: int,
    answer_text: str,
) -> AnswerReview:
    question = session.questions[question_index]

    prompt = f"""
You are conducting a structured text-based employment interview.
Review the candidate's answer only against the approved question and guidance.
Do not infer protected characteristics. Do not make a hiring decision.
Ask at most one concise follow-up only when the answer lacks a concrete example,
important clarification, or evidence relevant to the competency.

Job: {session.job_title}
Interview stage: {session.interview_stage}
Competency: {question.competency}
Question: {question.question_text}
Reason: {question.reason}
Strong-answer indicators: {question.strong_answer_indicators}
Warning signs: {question.warning_signs}
Approved suggested follow-ups: {question.suggested_follow_ups}
Candidate answer: {answer_text}
"""

    response = _client().responses.parse(
        model=AI_INTERVIEW_MODEL,
        input=prompt,
        text_format=AnswerReview,
    )

    result = response.output_parsed
    if result is None:
        raise RuntimeError("The AI answer review returned no structured result.")

    return result


def save_ai_answer_review(
    session: InterviewSession,
    question_index: int,
    answer_text: str,
    review: AnswerReview,
) -> InterviewSession:
    now = utc_now_iso()
    question = session.questions[question_index]

    question.answer_text = answer_text.strip()
    question.transcript_text = answer_text.strip()
    question.ai_summary = review.answer_summary.strip()
    question.ai_interviewer_notes = review.interviewer_notes.strip()
    question.answered = bool(question.answer_text)
    question.answered_time = now if question.answered else None

    should_follow_up = (
        review.ask_follow_up
        and question.follow_ups_used < question.max_follow_ups
        and bool(review.follow_up_question.strip())
    )

    if should_follow_up:
        question.ai_follow_up_question = review.follow_up_question.strip()
    else:
        question.ai_follow_up_question = ""

    session.status = "in_progress"
    session.started_time = session.started_time or now
    session.ai_state = (
        "awaiting_answer" if should_follow_up else "ready"
    )
    session.last_activity_time = now
    session.audit_events.append(
        SessionAuditEvent(
            action="answer_submitted",
            timestamp=now,
            actor_type="candidate",
            details=f"Question {question_index + 1} answered.",
        )
    )

    if should_follow_up:
        session.audit_events.append(
            SessionAuditEvent(
                action="follow_up_presented",
                timestamp=now,
                actor_type="ai",
                details=question.ai_follow_up_question,
            )
        )

    save_interview_session(session)
    return session


def save_ai_follow_up_answer(
    session: InterviewSession,
    question_index: int,
    follow_up_answer: str,
) -> InterviewSession:
    now = utc_now_iso()
    question = session.questions[question_index]
    question.ai_follow_up_answer = follow_up_answer.strip()
    question.follow_ups_used += 1
    session.ai_state = "ready"
    session.last_activity_time = now
    session.audit_events.append(
        SessionAuditEvent(
            action="follow_up_answer_submitted",
            timestamp=now,
            actor_type="candidate",
            details=f"Follow-up for question {question_index + 1} answered.",
        )
    )
    save_interview_session(session)
    return session


def generate_ai_evaluation_draft(
    session: InterviewSession,
) -> EvaluationDraft:
    transcript_sections: list[str] = []

    for index, question in enumerate(session.questions, start=1):
        section = [
            f"Question {index}: {question.question_text}",
            f"Answer: {question.answer_text}",
        ]
        if question.ai_follow_up_question:
            section.append(f"Follow-up: {question.ai_follow_up_question}")
            section.append(f"Follow-up answer: {question.ai_follow_up_answer}")
        transcript_sections.append("\n".join(section))

    criteria_text = "\n".join(
        (
            f"- {criterion.criterion_id}: {criterion.competency}; "
            f"weight {criterion.weight}; {criterion.description}; "
            f"strong evidence {criterion.strong_evidence}; "
            f"weak evidence {criterion.weak_evidence}"
        )
        for criterion in session.evaluation_criteria
    )

    prompt = f"""
Create a recruiter-reviewable DRAFT interview evaluation.
Use only evidence in the interview transcript. Do not infer protected
characteristics. Rate every listed criterion from 1 to 5. Explain each rating
with specific evidence or explicitly state that evidence was limited.
This is not a final hiring decision and must remain editable by a recruiter.

Job: {session.job_title}
Interview stage: {session.interview_stage}
Evaluation criteria:
{criteria_text}

Transcript:
{chr(10).join(transcript_sections)}
"""

    response = _client().responses.parse(
        model=AI_INTERVIEW_MODEL,
        input=prompt,
        text_format=EvaluationDraft,
    )

    result = response.output_parsed
    if result is None:
        raise RuntimeError("The AI evaluation returned no structured result.")

    return result


def apply_ai_evaluation_draft(
    session: InterviewSession,
    draft: EvaluationDraft,
) -> InterviewSession:
    criteria_by_id = {
        criterion.criterion_id: criterion
        for criterion in session.evaluation_criteria
    }

    for item in draft.criteria:
        criterion = criteria_by_id.get(item.criterion_id)
        if criterion is None:
            continue
        criterion.rating = item.rating
        criterion.comments = item.comments.strip()

    session.evaluation_summary = draft.evaluation_summary.strip()
    session.recommendation = draft.recommendation
    session.evaluation_status = "draft"
    session.ai_state = "completed"
    now = utc_now_iso()
    session.last_activity_time = now
    session.audit_events.append(
        SessionAuditEvent(
            action="ai_evaluation_draft_created",
            timestamp=now,
            actor_type="ai",
            details="AI-generated draft saved for recruiter review.",
        )
    )
    save_interview_session(session)
    return session


def finish_ai_interview(session: InterviewSession) -> InterviewSession:
    complete_interview_session(session)
    session.ai_state = "completed"
    now = utc_now_iso()
    session.last_activity_time = now
    session.audit_events.append(
        SessionAuditEvent(
            action="interview_completed",
            timestamp=now,
            actor_type="candidate",
            details="AI chat interview completed.",
        )
    )
    save_interview_session(session)
    return session
