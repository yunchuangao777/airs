from __future__ import annotations
import secrets
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from services.interview_evaluation_service import (
    InterviewEvaluationTemplate,
    get_selected_criteria,
)
from services.interview_package_service import (
    InterviewPackage,
)
from services.interview_question_service import (
    InterviewQuestionSet,
    get_selected_questions,
)
from application_service import (
    get_or_create_application,
    update_application_status,
)
from schema import CandidateStatus

INTERVIEW_SESSION_DIR = Path(
    "outputs/interview_sessions"
)

INTERVIEW_SESSION_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

PUBLIC_INTERVIEW_BASE_URL = os.getenv(
    "PUBLIC_INTERVIEW_BASE_URL",
    "https://airs-2mdr.onrender.com",
)

SessionStatus = Literal[
    "draft",
    "in_progress",
    "completed",
    "cancelled",
]

InterviewMode = Literal[
    "recruiter_led",
    "candidate_async",
    "ai_chat",
    "ai_voice",
]

class SessionAuditEvent(BaseModel):
    """One auditable action performed during a session."""

    action: str
    timestamp: str
    actor_type: str
    details: str = ""


class SessionQuestion(BaseModel):
    """
    Frozen copy of one approved interview question.
    """

    question_id: str

    source: str

    category: str

    competency: str

    question_text: str

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

    answer_text: str = ""

    interviewer_notes: str = ""

    answered: bool = False

    answered_time: str | None = None

    transcript_text: str = ""

    ai_summary: str = ""

    ai_interviewer_notes: str = ""

    ai_follow_up_question: str = ""

    ai_follow_up_answer: str = ""

    max_follow_ups: int = 1

    follow_ups_used: int = 0


class SessionEvaluationCriterion(BaseModel):
    """
    Frozen copy of one approved evaluation criterion.

    Ratings are filled after or during the interview.
    """

    criterion_id: str

    competency: str

    description: str = ""

    weight: int = 0

    strong_evidence: list[str] = Field(
        default_factory=list
    )

    weak_evidence: list[str] = Field(
        default_factory=list
    )

    rating: int | None = None

    comments: str = ""


class InterviewSession(BaseModel):
    """
    One interview execution record.
    """

    session_id: str

    package_id: str

    question_set_id: str

    evaluation_template_id: str

    candidate_id: str

    job_id: str

    application_id: str | None = None

    candidate_name: str

    job_title: str

    company: str = ""

    interview_type: str

    interview_type_label: str

    duration_minutes: int

    interview_round: int = 1

    interview_stage: str = "Recruiter Screening"

    interview_mode: InterviewMode = "recruiter_led"

    status: SessionStatus = "draft"

    current_question_index: int = 0

    questions: list[SessionQuestion] = Field(
        default_factory=list
    )

    evaluation_criteria: list[
        SessionEvaluationCriterion
    ] = Field(default_factory=list)

    overall_notes: str = ""

    recommendation: str = ""

    evaluation_summary: str = ""

    evaluation_status: Literal[
        "not_started",
        "draft",
        "completed",
    ] = "not_started"

    evaluation_completed_time: str | None = None

    interviewer_type: Literal["recruiter", "ai"] = "recruiter"

    interviewer_name: str = ""

    consent_status: Literal[
        "not_requested",
        "accepted",
        "declined",
    ] = "not_requested"

    consent_time: str | None = None

    consent_version: str = ""

    ai_state: Literal[
        "not_started",
        "awaiting_consent",
        "ready",
        "asking_question",
        "awaiting_answer",
        "processing_answer",
        "completed",
        "failed",
    ] = "not_started"

    ai_error_message: str = ""

    last_activity_time: str | None = None

    audit_events: list[SessionAuditEvent] = Field(
        default_factory=list
    )

    created_time: str

    started_time: str | None = None

    completed_time: str | None = None

    updated_time: str

    candidate_access_token: str = ""
    candidate_access_enabled: bool = False

    candidate_link_created_time: str | None = None
    candidate_link_expires_time: str | None = None

def build_candidate_interview_link(
    token: str,
) -> str:
    """
    Build the public interview URL.
    """
    base = PUBLIC_INTERVIEW_BASE_URL.rstrip("/")

    return (
        f"{base}/"
        f"?interview_token={token}"
    )

def utc_now_iso() -> str:
    """
    Return a timezone-aware UTC timestamp.
    """
    return datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")


def get_session_path(
    session_id: str,
) -> Path:
    """
    Return the JSON path for a session.
    """
    return (
        INTERVIEW_SESSION_DIR
        / f"{session_id}.json"
    )

def generate_candidate_access_token() -> str:
    """
    Generate a cryptographically secure token for
    candidate access to one AI interview session.
    """
    return secrets.token_urlsafe(32)


def create_interview_session(
    package: InterviewPackage,
    question_set: InterviewQuestionSet,
    evaluation_template: InterviewEvaluationTemplate,
    interview_round: int = 1,
    interview_stage: str = "Recruiter Screening",
    interview_mode: InterviewMode = "recruiter_led",
) -> InterviewSession:
    """
    Create a frozen session snapshot from the approved
    interview package, questions, and evaluation template.
    """

    interview_round = int(interview_round)

    if interview_round < 1:
        raise ValueError(
            "Interview round must be at least 1."
        )

    interview_stage = interview_stage.strip()

    if not interview_stage:
        raise ValueError(
            "Interview stage is required."
        )
    
    selected_questions = get_selected_questions(
        question_set
    )

    if not selected_questions:
        raise ValueError(
            "At least one approved interview question "
            "is required."
        )

    selected_criteria = get_selected_criteria(
        evaluation_template
    )

    now = utc_now_iso()

    session_questions = [
        SessionQuestion(
            question_id=question.question_id,
            source=question.source,
            category=question.category,
            competency=question.competency,
            question_text=question.edited_question,
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
        )
        for question in selected_questions
    ]

    session_criteria = [
        SessionEvaluationCriterion(
            criterion_id=criterion.criterion_id,
            competency=criterion.competency,
            description=criterion.description,
            weight=criterion.weight,
            strong_evidence=list(
                criterion.strong_evidence
            ),
            weak_evidence=list(
                criterion.weak_evidence
            ),
        )
        for criterion in selected_criteria
    ]

    is_ai_chat = (
        interview_mode == "ai_chat"
    )

    candidate_access_token = (
        generate_candidate_access_token()
        if is_ai_chat
        else ""
    )

    candidate_link_created_time = (
        now
        if is_ai_chat
        else None
    )
            
    session = InterviewSession(
        session_id=str(uuid4()),
        package_id=package.package_id,
        question_set_id=(
            question_set.question_set_id
        ),
        evaluation_template_id=(
            evaluation_template.template_id
        ),
        candidate_id=package.candidate_id,
        job_id=package.job_id,
        application_id=package.application_id,
        candidate_name=package.candidate_name,
        job_title=package.job_title,
        company=package.company,
        interview_type=package.interview_type,
        interview_type_label=(
            package.interview_type_label
        ),
        duration_minutes=(
            package.duration_minutes
        ),

        interview_round=interview_round,
        interview_stage=interview_stage,
        interview_mode=interview_mode,
        interviewer_type=(
            "ai" if interview_mode == "ai_chat" else "recruiter"
        ),
        interviewer_name=(
            "AIRS Interview Assistant"
            if interview_mode == "ai_chat"
            else ""
        ),
        consent_status=(
            "not_requested"
            if interview_mode == "recruiter_led"
            else "not_requested"
        ),
        ai_state=(
            "awaiting_consent"
            if interview_mode == "ai_chat"
            else "not_started"
        ),

        # Candidate access information
        candidate_access_token=(
            candidate_access_token
        ),
        candidate_access_enabled=is_ai_chat,
        candidate_link_created_time=(
            candidate_link_created_time
        ),
        candidate_link_expires_time=None,
        
        status="draft",
        current_question_index=0,
        questions=session_questions,
        evaluation_criteria=session_criteria,
        created_time=now,
        updated_time=now,
    )

    save_interview_session(session)

    return session


def save_interview_session(
    session: InterviewSession,
) -> Path:
    """
    Save a session atomically.
    """
    session.updated_time = utc_now_iso()

    output_path = get_session_path(
        session.session_id
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
            session.model_dump(mode="json"),
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporary_path.replace(output_path)

    return output_path


def load_interview_session(
    session_id: str,
) -> InterviewSession | None:
    """
    Load and validate one interview session.
    """
    path = get_session_path(session_id)

    if not path.exists():
        return None

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return InterviewSession.model_validate(
            data
        )

    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            f"Unable to load interview session "
            f"{path}: {exc}"
        ) from exc


def load_all_interview_sessions() -> list[
    InterviewSession
]:
    """
    Load all saved interview sessions.
    """
    sessions: list[InterviewSession] = []

    for path in INTERVIEW_SESSION_DIR.glob(
        "*.json"
    ):
        try:
            with open(
                path,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            sessions.append(
                InterviewSession.model_validate(
                    data
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
            ValueError,
        ):
            continue

    return sorted(
        sessions,
        key=lambda item: item.updated_time,
        reverse=True,
    )

def find_session_by_candidate_token(
    token: str,
) -> InterviewSession | None:
    """
    Find an AI interview session using the public
    candidate access token.
    """
    token = str(token).strip()

    if not token:
        return None

    for session in load_all_interview_sessions():

        stored_token = (
            session.candidate_access_token or ""
        )

        if (
            stored_token
            and secrets.compare_digest(
                stored_token,
                token,
            )
        ):
            return session

    return None

def find_sessions_for_candidate_job(
    candidate_id: str,
    job_id: str,
) -> list[InterviewSession]:
    """
    Return all sessions for one candidate-job pair.
    """
    return [
        session
        for session in load_all_interview_sessions()
        if (
            session.candidate_id == candidate_id
            and session.job_id == job_id
        )
    ]

def mark_application_as_interview(
    session: InterviewSession,
) -> None:
    """
    Move an application from an earlier pipeline stage
    into Interview without overwriting a later decision.
    """
    application = get_or_create_application(
        candidate_id=session.candidate_id,
        job_id=session.job_id,
    )

    allowed_current_statuses = {
        CandidateStatus.NONE,
        CandidateStatus.APPLIED,
        CandidateStatus.REVIEW,
    }

    if application.status not in allowed_current_statuses:
        return

    update_application_status(
        candidate_id=session.candidate_id,
        job_id=session.job_id,
        new_status=CandidateStatus.INTERVIEW,
        note=(
            "Interview session started: "
            f"{session.session_id}"
        ),
    )

def add_session_audit_event(
    session: InterviewSession,
    action: str,
    actor_type: str,
    details: str = "",
) -> InterviewSession:
    """Append an audit event and save the session."""
    now = utc_now_iso()
    session.audit_events.append(
        SessionAuditEvent(
            action=action,
            timestamp=now,
            actor_type=actor_type,
            details=details.strip(),
        )
    )
    session.last_activity_time = now
    save_interview_session(session)
    return session


def accept_ai_interview_consent(
    session: InterviewSession,
    consent_version: str = "ai-interview-v1",
) -> InterviewSession:
    """Record candidate consent for an AI interview."""
    if session.interview_mode != "ai_chat":
        raise ValueError("Consent is only used for AI chat interviews.")

    now = utc_now_iso()
    session.consent_status = "accepted"
    session.consent_time = now
    session.consent_version = consent_version
    session.ai_state = "ready"
    session.last_activity_time = now
    session.audit_events.append(
        SessionAuditEvent(
            action="consent_accepted",
            timestamp=now,
            actor_type="candidate",
            details=f"Consent version: {consent_version}",
        )
    )
    save_interview_session(session)
    return session


def set_ai_session_state(
    session: InterviewSession,
    ai_state: str,
    error_message: str = "",
) -> InterviewSession:
    """Update AI execution state and persist it."""
    session.ai_state = ai_state
    session.ai_error_message = error_message.strip()
    session.last_activity_time = utc_now_iso()
    save_interview_session(session)
    return session


def start_interview_session(
    session: InterviewSession,
) -> InterviewSession:
    """
    Start the interview and move the related application
    into the Interview pipeline stage.
    """
    if session.status == "draft":
        session.status = "in_progress"
        session.started_time = utc_now_iso()

        mark_application_as_interview(
            session
        )

    save_interview_session(session)

    return session


def update_session_question(
    session: InterviewSession,
    question_index: int,
    answer_text: str,
    interviewer_notes: str = "",
) -> InterviewSession:
    """
    Save the response and notes for one question.
    """
    if not (
        0 <= question_index < len(session.questions)
    ):
        raise IndexError(
            "Question index is out of range."
        )

    question = session.questions[
        question_index
    ]

    question.answer_text = answer_text.strip()
    question.interviewer_notes = (
        interviewer_notes.strip()
    )
    question.answered = bool(
        question.answer_text
    )

    question.answered_time = (
        utc_now_iso()
        if question.answered
        else None
    )

    session.current_question_index = (
        question_index
    )

    if session.status == "draft":
        session.status = "in_progress"
        session.started_time = utc_now_iso()

        mark_application_as_interview(
            session
        )

    save_interview_session(session)

    return session


def set_current_question(
    session: InterviewSession,
    question_index: int,
) -> InterviewSession:
    """
    Save the current question position.
    """
    if not session.questions:
        session.current_question_index = 0

    else:
        session.current_question_index = max(
            0,
            min(
                question_index,
                len(session.questions) - 1,
            ),
        )

    save_interview_session(session)

    return session


def complete_interview_session(
    session: InterviewSession,
) -> InterviewSession:
    """
    Mark the interview session complete.
    """
    session.status = "completed"
    session.completed_time = utc_now_iso()

    save_interview_session(session)

    return session

def get_latest_session_for_candidate_job(
    candidate_id: str,
    job_id: str,
) -> InterviewSession | None:
    """
    Return the most recently updated session for one
    candidate-job pair.
    """
    sessions = find_sessions_for_candidate_job(
        candidate_id=candidate_id,
        job_id=job_id,
    )

    if not sessions:
        return None

    return sessions[0]

def update_session_evaluation(
    session: InterviewSession,
    criterion_updates: list[dict],
    evaluation_summary: str,
    recommendation: str,
) -> InterviewSession:
    """
    Save ratings and comments as an evaluation draft.
    """
    criteria_by_id = {
        criterion.criterion_id: criterion
        for criterion in session.evaluation_criteria
    }

    for update in criterion_updates:
        criterion_id = update.get("criterion_id")

        criterion = criteria_by_id.get(
            criterion_id
        )

        if criterion is None:
            continue

        rating = update.get("rating")

        if rating is None:
            criterion.rating = None
        else:
            rating = int(rating)

            if rating < 1 or rating > 5:
                raise ValueError(
                    "Evaluation ratings must be "
                    "between 1 and 5."
                )

            criterion.rating = rating

        criterion.comments = str(
            update.get("comments", "")
        ).strip()

    session.evaluation_summary = (
        evaluation_summary.strip()
    )

    session.recommendation = (
        recommendation.strip()
    )

    session.evaluation_status = "draft"

    save_interview_session(session)

    return session


def calculate_weighted_evaluation_score(
    session: InterviewSession,
) -> float | None:
    """
    Return the weighted average rating on a 1–5 scale.

    Only rated criteria with a positive weight are used.
    """
    rated_criteria = [
        criterion
        for criterion in session.evaluation_criteria
        if (
            criterion.rating is not None
            and criterion.weight > 0
        )
    ]

    if not rated_criteria:
        return None

    total_weight = sum(
        criterion.weight
        for criterion in rated_criteria
    )

    if total_weight <= 0:
        return None

    weighted_total = sum(
        criterion.rating * criterion.weight
        for criterion in rated_criteria
    )

    return round(
        weighted_total / total_weight,
        2,
    )


def get_evaluation_completion_counts(
    session: InterviewSession,
) -> tuple[int, int]:
    """
    Return rated criteria count and total criteria count.
    """
    total_count = len(
        session.evaluation_criteria
    )

    rated_count = sum(
        1
        for criterion in session.evaluation_criteria
        if criterion.rating is not None
    )

    return rated_count, total_count


def complete_session_evaluation(
    session: InterviewSession,
) -> InterviewSession:
    """
    Finalize the evaluation after validating required data.
    """
    if session.status != "completed":
        raise ValueError(
            "The interview must be completed before "
            "the evaluation can be finalized."
        )

    rated_count, total_count = (
        get_evaluation_completion_counts(
            session
        )
    )

    if total_count == 0:
        raise ValueError(
            "This session has no evaluation criteria."
        )

    if rated_count != total_count:
        raise ValueError(
            "Every evaluation criterion must have "
            "a rating before finalization."
        )

    if not session.recommendation.strip():
        raise ValueError(
            "An overall recommendation is required."
        )

    if not session.evaluation_summary.strip():
        raise ValueError(
            "An overall evaluation summary is required."
        )

    session.evaluation_status = "completed"
    session.evaluation_completed_time = (
        utc_now_iso()
    )

    save_interview_session(session)

    return session
