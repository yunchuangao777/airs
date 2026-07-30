from collections import Counter

from application_loader import load_all_applications
from match_loader import (
    load_all_candidates,
    load_all_jobs,
    load_all_matches,
)
from services.interview_session_service import (
    calculate_weighted_evaluation_score,
    load_all_interview_sessions,
)

STATUS_ORDER = [
    "none",
    "applied",
    "review",
    "interview",
    "offer",
    "accepted",
    "rejected",
    "archived",
]


STATUS_LABELS = {
    "none": "Not Applied",
    "applied": "Applied",
    "review": "Review",
    "interview": "Interview",
    "offer": "Offer",
    "accepted": "Accepted",
    "rejected": "Rejected",
    "archived": "Archived",
}


def _get_best_matches(
    matches: list[dict],
) -> dict[tuple[str, str], dict]:
    """
    Return the best match record for each candidate/job pair.

    Your current outputs may contain:
        old match file
        AI match file
        traditional match file

    This selects the highest score for the pair.
    """
    best_matches: dict[tuple[str, str], dict] = {}

    for match in matches:
        candidate_id = match.get("candidate_id")
        job_id = match.get("job_id")

        if not candidate_id or not job_id:
            continue

        key = (candidate_id, job_id)

        try:
            score = float(match.get("score", 0) or 0)
        except (TypeError, ValueError):
            score = 0.0

        existing = best_matches.get(key)

        if existing is None:
            best_matches[key] = match
            continue

        try:
            existing_score = float(
                existing.get("score", 0) or 0
            )
        except (TypeError, ValueError):
            existing_score = 0.0

        if score > existing_score:
            best_matches[key] = match

    return best_matches

def _get_latest_interview_sessions() -> dict:
    """
    Return the newest interview session for each
    candidate/job pair.
    """
    sessions = load_all_interview_sessions()

    latest: dict[tuple[str, str], object] = {}

    for session in sessions:
        key = (
            session.candidate_id,
            session.job_id,
        )

        existing = latest.get(key)

        if existing is None:
            latest[key] = session
            continue

        if session.updated_time > existing.updated_time:
            latest[key] = session

    return latest

def build_hiring_dataset() -> list[dict]:
    """
    Build one joined record per application.
    """
    candidates = load_all_candidates()
    jobs = load_all_jobs()
    applications = load_all_applications()
    matches = load_all_matches()

    candidates_by_id = {
        candidate.get("candidate_id"): candidate
        for candidate in candidates
        if candidate.get("candidate_id")
    }

    jobs_by_id = {
        job.get("job_id"): job
        for job in jobs
        if job.get("job_id")
    }

    best_matches = _get_best_matches(matches)

    # Build this once before the loop.
    latest_sessions = _get_latest_interview_sessions()

    rows: list[dict] = []

    for application in applications:
        candidate_id = application.get("candidate_id")
        job_id = application.get("job_id")

        # This must come after candidate_id and job_id
        # have been assigned.
        session = latest_sessions.get(
            (candidate_id, job_id)
        )

        if session is not None:
            weighted_score = (
                calculate_weighted_evaluation_score(
                    session
                )
            )
        else:
            weighted_score = None

        candidate = candidates_by_id.get(
            candidate_id,
            {},
        )

        job = jobs_by_id.get(
            job_id,
            {},
        )

        match = best_matches.get(
            (candidate_id, job_id),
            {},
        )

        try:
            match_score = float(
                match.get("score", 0) or 0
            )
        except (TypeError, ValueError):
            match_score = 0.0

        status = application.get("status") or "none"

        rows.append(
            {
                "application_id": application.get(
                    "application_id"
                ),
                "candidate_id": candidate_id,
                "candidate_name": (
                    candidate.get("name")
                    or match.get("candidate_name")
                    or "Unknown Candidate"
                ),
                "candidate_email": (
                    candidate.get("email") or ""
                ),
                "job_id": job_id,
                "job_title": (
                    job.get("job_title")
                    or match.get("job_title")
                    or "Untitled Job"
                ),
                "company": job.get("company") or "",
                "status": status,
                "status_label": STATUS_LABELS.get(
                    status,
                    status.title(),
                ),
                "match_score": match_score,
                "match_method": (
                    match.get("match_method") or ""
                ),
                "created_time": application.get(
                    "created_time"
                ),
                "updated_time": application.get(
                    "updated_time"
                ),
                "notes": application.get("notes") or "",

                # Interview information
                "interview_round": (
                    session.interview_round
                    if session is not None
                    else None
                ),
                "interview_stage": (
                    session.interview_stage
                    if session is not None
                    else ""
                ),
                "interview_mode": (
                    session.interview_mode
                    if session is not None
                    else ""
                ),
                "interview_status": (
                    session.status
                    if session is not None
                    else ""
                ),
                "evaluation_status": (
                    session.evaluation_status
                    if session is not None
                    else ""
                ),
                "evaluation_score": weighted_score,
                "evaluation_recommendation": (
                    session.recommendation
                    if session is not None
                    else ""
                ),

                "candidate": candidate,
                "job": job,
                "match": match,
                "application": application,
                "interview_session": session,
            }
        )

    return rows


def get_job_status_summaries(
    dataset: list[dict] | None = None,
) -> list[dict]:
    """
    Return candidate-status totals for every job,
    including jobs with zero applications.
    """
    if dataset is None:
        dataset = build_hiring_dataset()

    jobs = load_all_jobs()

    rows_by_job: dict[str, list[dict]] = {}

    for row in dataset:
        job_id = row.get("job_id")

        if job_id:
            rows_by_job.setdefault(
                job_id,
                [],
            ).append(row)

    summaries: list[dict] = []

    for job in jobs:
        job_id = job.get("job_id")

        if not job_id:
            continue

        job_rows = [
            row
            for row in rows_by_job.get(job_id, [])
            if (row.get("status") or "none") != "none"
        ]

        counts = Counter(
            row.get("status") or "none"
            for row in job_rows
        )

        status_counts = {
            status: counts.get(status, 0)
            for status in STATUS_ORDER
        }

        summaries.append(
            {
                "job_id": job_id,
                "job_title": (
                    job.get("job_title")
                    or "Untitled Job"
                ),
                "company": job.get("company") or "",
                "location": job.get("location") or "",
                "total_candidates": len(job_rows),
                "status_counts": status_counts,
                "applications": job_rows,
                "job": job,
            }
        )

    return summaries


def get_candidates_for_job(
    job_id: str,
    status: str | None = None,
    dataset: list[dict] | None = None,
) -> list[dict]:
    if dataset is None:
        dataset = build_hiring_dataset()

    rows = [
        row
        for row in dataset
        if (
            row.get("job_id") == job_id
            and (row.get("status") or "none") != "none"
        )
    ]

    if status and status != "all":
        rows = [
            row
            for row in rows
            if row.get("status") == status
        ]

    return sorted(
        rows,
        key=lambda row: float(
            row.get("match_score", 0) or 0
        ),
        reverse=True,
    )