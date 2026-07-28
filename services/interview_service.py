from __future__ import annotations

from services.hiring_service import (
    build_hiring_dataset,
    get_candidates_for_job,
)


INTERVIEW_ELIGIBLE_STATUSES = [
    "review",
    "interview",
    "offer",
]


def get_interview_jobs(
    dataset: list[dict] | None = None,
) -> list[dict]:
    """
    Return jobs that have at least one candidate eligible
    for interview preparation.
    """
    if dataset is None:
        dataset = build_hiring_dataset()

    jobs_by_id: dict[str, dict] = {}

    for row in dataset:
        status = row.get("status") or "none"
        job_id = row.get("job_id")

        if (
            not job_id
            or status not in INTERVIEW_ELIGIBLE_STATUSES
        ):
            continue

        if job_id not in jobs_by_id:
            jobs_by_id[job_id] = {
                "job_id": job_id,
                "job_title": (
                    row.get("job_title")
                    or "Untitled Job"
                ),
                "company": row.get("company") or "",
                "job": row.get("job", {}),
            }

    return sorted(
        jobs_by_id.values(),
        key=lambda item: (
            str(item.get("job_title") or "").lower()
        ),
    )


def get_interview_candidates_for_job(
    job_id: str,
    dataset: list[dict] | None = None,
) -> list[dict]:
    """
    Return candidates in Review, Interview, or Offer status
    for the selected job.
    """
    if dataset is None:
        dataset = build_hiring_dataset()

    rows = get_candidates_for_job(
        job_id=job_id,
        dataset=dataset,
    )

    eligible_rows = [
        row
        for row in rows
        if (
            row.get("status")
            in INTERVIEW_ELIGIBLE_STATUSES
        )
    ]

    return sorted(
        eligible_rows,
        key=lambda row: float(
            row.get("match_score", 0) or 0
        ),
        reverse=True,
    )


def build_interview_context(
    candidate_id: str,
    job_id: str,
    dataset: list[dict] | None = None,
) -> dict | None:
    """
    Return all existing candidate, job, application,
    and match information needed for Interview Prep.
    """
    if dataset is None:
        dataset = build_hiring_dataset()

    application_row = next(
        (
            row
            for row in dataset
            if (
                row.get("candidate_id")
                == candidate_id
                and row.get("job_id") == job_id
            )
        ),
        None,
    )

    if not application_row:
        return None

    candidate = application_row.get(
        "candidate",
        {},
    )
    job = application_row.get(
        "job",
        {},
    )
    match = application_row.get(
        "match",
        {},
    )
    application = application_row.get(
        "application",
        {},
    )

    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "application_id": application_row.get(
            "application_id"
        ),
        "candidate_name": (
            application_row.get("candidate_name")
            or candidate.get("name")
            or "Unknown Candidate"
        ),
        "job_title": (
            application_row.get("job_title")
            or job.get("job_title")
            or "Untitled Job"
        ),
        "company": (
            application_row.get("company")
            or job.get("company")
            or ""
        ),
        "status": (
            application_row.get("status")
            or "none"
        ),
        "match_score": float(
            application_row.get(
                "match_score",
                0,
            )
            or 0
        ),
        "match_method": (
            application_row.get("match_method")
            or ""
        ),
        "candidate": candidate,
        "job": job,
        "match": match,
        "application": application,
        "strengths": match.get(
            "strengths",
            [],
        ),
        "concerns": match.get(
            "concerns",
            [],
        ),
        "matched_skills": match.get(
            "matched_skills",
            [],
        ),
        "missing_required_skills": match.get(
            "missing_required_skills",
            [],
        ),
        "recommendation": match.get(
            "recommendation"
        ),
    }