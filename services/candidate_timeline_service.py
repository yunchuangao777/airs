from __future__ import annotations

from datetime import datetime
from typing import Any

from services.interview_session_service import (
    calculate_weighted_evaluation_score,
    find_sessions_for_candidate_job,
)
from services.hiring_service import STATUS_LABELS

EVENT_ORDER = {
    "application_created": 10,
    "job_match": 20,
    "status_change": 30,
    "interview_session_created": 40,
    "interview_started": 50,
    "interview_completed": 60,
    "evaluation_draft": 70,
    "evaluation_completed": 80,
}

def _normalize_value(value: Any) -> Any:
    """
    Convert Pydantic models and enum values into
    ordinary Python values.
    """
    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "value"):
        return value.value

    return value


def _parse_time(value: str | None) -> datetime:
    """
    Parse ISO timestamps for chronological sorting.

    Invalid or missing timestamps sort first.
    """
    if not value:
        return datetime.min

    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        ).replace(tzinfo=None)
    except ValueError:
        return datetime.min


def _add_event(
    events: list[dict],
    *,
    event_type: str,
    title: str,
    timestamp: str | None,
    description: str = "",
    status: str = "completed",
    metadata: dict | None = None,
) -> None:
    events.append(
        {
            "event_type": event_type,
            "title": title,
            "timestamp": timestamp or "",
            "description": description,
            "status": status,
            "metadata": metadata or {},
        }
    )


def build_candidate_timeline(
    application_row: dict,
) -> list[dict]:
    """
    Build a chronological timeline for one candidate-job
    application.
    """
    candidate_id = application_row.get(
        "candidate_id"
    )

    job_id = application_row.get("job_id")

    application = application_row.get(
        "application",
        {},
    )

    match = application_row.get(
        "match",
        {},
    )

    events: list[dict] = []

    created_time = (
        application.get("created_time")
        or application_row.get("created_time")
    )

    _add_event(
        events,
        event_type="application_created",
        title="Application Created",
        timestamp=created_time,
        description=(
            "The candidate was added to this job's "
            "hiring pipeline."
        ),
    )

    match_score = application_row.get(
        "match_score"
    )

    if match_score is not None:
        try:
            score = float(match_score)
        except (TypeError, ValueError):
            score = 0.0

        match_method = (
            application_row.get("match_method")
            or match.get("match_method")
            or ""
        )

        method_label = (
            str(match_method)
            .replace("_", " ")
            .title()
        )

        description = (
            f"Match score: {score:.1f}"
        )

        if method_label:
            description += (
                f" · Method: {method_label}"
            )

        match_time = (
            match.get("created_time")
            or match.get("updated_time")
            or created_time
        )

        _add_event(
            events,
            event_type="job_match",
            title="Job Match Available",
            timestamp=match_time,
            description=description,
            metadata={
                "score": score,
                "method": match_method,
            },
        )

    status_history = application.get(
        "status_history",
        [],
    )

    for history_item in status_history:
        history_item = _normalize_value(
            history_item
        )

        if not isinstance(history_item, dict):
            continue

        raw_status = _normalize_value(
            history_item.get("status", "none")
        )

        status_value = str(raw_status)

        note = (
            history_item.get("note")
            or ""
        )

        is_initial_creation_record = (
            status_value == "none"
            and "application record created"
            in note.lower()
        )

        if is_initial_creation_record:
            continue

        status_label = STATUS_LABELS.get(
            status_value,
            status_value.replace(
                "_",
                " ",
            ).title(),
        )

        _add_event(
            events,
            event_type="status_change",
            title=f"Status Changed to {status_label}",
            timestamp=history_item.get(
                "changed_time"
            ),
            description=note,
            metadata={
                "application_status": status_value,
            },
        )

    if candidate_id and job_id:
        sessions = find_sessions_for_candidate_job(
            candidate_id=candidate_id,
            job_id=job_id,
        )
    else:
        sessions = []

    for session in sessions:
        session_label = (
            f"Round {session.interview_round}"
            f" · {session.interview_stage}"
        )

        mode_label = (
            session.interview_mode
            .replace("_", " ")
            .title()
        )

        _add_event(
            events,
            event_type="interview_session_created",
            title="Interview Session Created",
            timestamp=session.created_time,
            description=(
                f"{session_label} · {mode_label}"
            ),
            metadata={
                "session_id": session.session_id,
                "round": session.interview_round,
                "stage": session.interview_stage,
                "mode": session.interview_mode,
            },
        )

        if session.started_time:
            _add_event(
                events,
                event_type="interview_started",
                title="Interview Started",
                timestamp=session.started_time,
                description=session_label,
                status=(
                    "active"
                    if session.status == "in_progress"
                    else "completed"
                ),
                metadata={
                    "session_id": session.session_id,
                },
            )

        if session.completed_time:
            answered_count = sum(
                1
                for question in session.questions
                if question.answered
            )

            _add_event(
                events,
                event_type="interview_completed",
                title="Interview Completed",
                timestamp=session.completed_time,
                description=(
                    f"{session_label} · "
                    f"{answered_count} of "
                    f"{len(session.questions)} "
                    "questions answered"
                ),
                metadata={
                    "session_id": session.session_id,
                    "answered_count": answered_count,
                    "question_count": len(
                        session.questions
                    ),
                },
            )

        if session.evaluation_status == "draft":
            score = (
                calculate_weighted_evaluation_score(
                    session
                )
            )

            description = (
                f"{session_label} · Evaluation draft"
            )

            if score is not None:
                description += (
                    f" · Score: {score:.2f} / 5"
                )

            _add_event(
                events,
                event_type="evaluation_draft",
                title="Evaluation In Progress",
                timestamp=session.updated_time,
                description=description,
                status="active",
                metadata={
                    "session_id": session.session_id,
                    "score": score,
                },
            )

        if session.evaluation_status == "completed":
            score = (
                calculate_weighted_evaluation_score(
                    session
                )
            )

            description_parts = [
                session_label,
            ]

            if score is not None:
                description_parts.append(
                    f"Score: {score:.2f} / 5"
                )

            if session.recommendation:
                description_parts.append(
                    "Recommendation: "
                    f"{session.recommendation}"
                )

            _add_event(
                events,
                event_type="evaluation_completed",
                title="Evaluation Finalized",
                timestamp=(
                    session.evaluation_completed_time
                    or session.updated_time
                ),
                description=" · ".join(
                    description_parts
                ),
                metadata={
                    "session_id": session.session_id,
                    "score": score,
                    "recommendation": (
                        session.recommendation
                    ),
                },
            )

    # Remove duplicate initial status records when they
    # describe the same application creation event.
    deduplicated_events: list[dict] = []
    seen: set[tuple] = set()

    for event in events:
        key = (
            event["event_type"],
            event["title"],
            event["timestamp"],
            event["description"],
        )

        if key in seen:
            continue

        seen.add(key)
        deduplicated_events.append(event)

    return sorted(
        deduplicated_events,
        key=lambda event: (
            _parse_time(
                event.get("timestamp")
            ),
            EVENT_ORDER.get(
                event.get("event_type"),
                999,
            ),
        ),
    )