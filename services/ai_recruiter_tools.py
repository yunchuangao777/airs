from __future__ import annotations

from collections import Counter
from typing import Any

from application_loader import load_all_applications
from match_loader import (
    load_all_candidates,
    load_all_jobs,
    load_all_matches,
)
import json
from pathlib import Path

from services.candidate_discovery.discovery_service import (
    discover_candidates,
)
from services.candidate_discovery.models import (
    CandidateDiscoveryQuery,
)

INTERVIEW_SESSION_DIR = Path("outputs/interview_sessions")


def _load_all_interview_sessions() -> list[dict]:
    sessions: list[dict] = []
    if not INTERVIEW_SESSION_DIR.exists():
        return sessions
    for path in INTERVIEW_SESSION_DIR.glob("*.json"):
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict):
                sessions.append(data)
        except (OSError, json.JSONDecodeError):
            continue
    return sorted(
        sessions,
        key=lambda item: _text(item.get("updated_time")),
        reverse=True,
    )


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _text(value).lower()


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _candidate_key(candidate: dict) -> str:
    candidate_id = _text(candidate.get("candidate_id"))
    if candidate_id:
        return f"id:{candidate_id}"

    email = _lower(candidate.get("email"))
    if email:
        return f"email:{email}"

    return f"source:{_text(candidate.get('_source_path'))}"


def _unique_candidates() -> list[dict]:
    unique: dict[str, dict] = {}

    for candidate in load_all_candidates():
        unique[_candidate_key(candidate)] = candidate

    return list(unique.values())


def _applications_by_pair() -> dict[tuple[str, str], dict]:
    results: dict[tuple[str, str], dict] = {}

    for application in load_all_applications():
        candidate_id = _text(application.get("candidate_id"))
        job_id = _text(application.get("job_id"))

        if candidate_id and job_id:
            results[(candidate_id, job_id)] = application

    return results


def _best_matches() -> dict[tuple[str, str], dict]:
    results: dict[tuple[str, str], dict] = {}

    for match in load_all_matches():
        candidate_id = _text(match.get("candidate_id"))
        job_id = _text(match.get("job_id"))

        if not candidate_id or not job_id:
            continue

        key = (candidate_id, job_id)
        current = results.get(key)

        if current is None or (
            _float(match.get("score")) or 0
        ) > (_float(current.get("score")) or 0):
            results[key] = match

    return results


def _education_text(candidate: dict) -> str:
    parts: list[str] = []

    for item in candidate.get("education") or []:
        if not isinstance(item, dict):
            continue

        values = [
            _text(item.get("degree")),
            _text(item.get("major")),
            _text(item.get("school")),
        ]

        text = " | ".join(value for value in values if value)
        if text:
            parts.append(text)

    return "; ".join(parts)


def get_recruitment_overview() -> dict:
    candidates = _unique_candidates()
    jobs = load_all_jobs()
    applications = load_all_applications()
    sessions = _load_all_interview_sessions()

    application_status = Counter(
        _lower(application.get("status")) or "none"
        for application in applications
    )

    interview_status = Counter(
        _lower(session.get("status")) or "unknown"
        for session in sessions
    )

    return {
        "candidate_count": len(candidates),
        "job_count": len(jobs),
        "application_count": len(applications),
        "interview_session_count": len(sessions),
        "application_status": dict(application_status),
        "interview_status": dict(interview_status),
        "completed_interviews": sum(
            session.get("status") == "completed"
            for session in sessions
        ),
        "evaluations_waiting_review": sum(
            session.get("status") == "completed"
            and session.get("evaluation_status") != "completed"
            for session in sessions
        ),
    }


def search_candidates(
    *,
    name: str | None = None,
    skills: list[str] | None = None,
    minimum_experience: float | None = None,
    education: str | None = None,
    job_id: str | None = None,
    status: str | None = None,
    minimum_match_score: float | None = None,
    limit: int = 10,
) -> dict:
    candidates = _unique_candidates()
    applications = _applications_by_pair()
    matches = _best_matches()

    requested_name = _lower(name)
    requested_skills = [
        _lower(skill)
        for skill in (skills or [])
        if _lower(skill)
    ]
    requested_education = _lower(education)
    requested_status = _lower(status)
    selected_job_id = _text(job_id)

    rows: list[dict] = []

    for candidate in candidates:
        candidate_id = _text(candidate.get("candidate_id"))
        candidate_name = _text(candidate.get("name"))
        candidate_skills = [
            _text(skill)
            for skill in candidate.get("skills") or []
            if _text(skill)
        ]
        searchable_skills = " | ".join(
            skill.lower() for skill in candidate_skills
        )
        experience = _float(
            candidate.get("total_years_experience")
        )
        education_text = _education_text(candidate)

        if requested_name and requested_name not in candidate_name.lower():
            continue

        if requested_skills and not all(
            skill in searchable_skills
            for skill in requested_skills
        ):
            continue

        if (
            minimum_experience is not None
            and (experience is None or experience < minimum_experience)
        ):
            continue

        if (
            requested_education
            and requested_education not in education_text.lower()
        ):
            continue

        application_status = ""
        match_score = None
        matched_skills: list[str] = []
        missing_skills: list[str] = []

        if selected_job_id:
            application = applications.get(
                (candidate_id, selected_job_id)
            )
            match = matches.get(
                (candidate_id, selected_job_id)
            )

            application_status = _lower(
                (application or {}).get("status")
            )
            match_score = _float(
                (match or {}).get("score")
            )
            matched_skills = list(
                (match or {}).get("matched_skills") or []
            )
            missing_skills = list(
                (match or {}).get("missing_required_skills") or []
            )

            if requested_status and application_status != requested_status:
                continue

            if (
                minimum_match_score is not None
                and (
                    match_score is None
                    or match_score < minimum_match_score
                )
            ):
                continue

        elif requested_status or minimum_match_score is not None:
            related_applications = [
                application
                for (app_candidate_id, _), application
                in applications.items()
                if app_candidate_id == candidate_id
            ]
            related_matches = [
                match
                for (match_candidate_id, _), match
                in matches.items()
                if match_candidate_id == candidate_id
            ]

            if requested_status and not any(
                _lower(application.get("status")) == requested_status
                for application in related_applications
            ):
                continue

            best_score = max(
                (
                    _float(match.get("score")) or 0
                    for match in related_matches
                ),
                default=0,
            )

            if (
                minimum_match_score is not None
                and best_score < minimum_match_score
            ):
                continue

            match_score = best_score or None

        rows.append(
            {
                "candidate_id": candidate_id,
                "name": candidate_name or "Unknown Candidate",
                "location": _text(candidate.get("location")),
                "skills": candidate_skills,
                "experience_years": experience,
                "education": education_text,
                "application_status": application_status,
                "match_score": match_score,
                "matched_skills": matched_skills,
                "missing_required_skills": missing_skills,
            }
        )

    rows.sort(
        key=lambda item: (
            item.get("match_score") is not None,
            item.get("match_score") or 0,
            item.get("experience_years") or 0,
        ),
        reverse=True,
    )

    safe_limit = max(1, min(int(limit or 10), 50))

    return {
        "count": len(rows),
        "returned": min(len(rows), safe_limit),
        "candidates": rows[:safe_limit],
    }


def get_candidate_details(candidate_id: str) -> dict:
    selected_id = _text(candidate_id)

    candidate = next(
        (
            item
            for item in _unique_candidates()
            if _text(item.get("candidate_id")) == selected_id
        ),
        None,
    )

    if candidate is None:
        return {
            "found": False,
            "candidate_id": selected_id,
        }

    jobs_by_id = {
        _text(job.get("job_id")): job
        for job in load_all_jobs()
    }
    applications = load_all_applications()
    matches = _best_matches()
    sessions = _load_all_interview_sessions()

    related_applications = []

    for application in applications:
        if _text(application.get("candidate_id")) != selected_id:
            continue

        job_id = _text(application.get("job_id"))
        job = jobs_by_id.get(job_id, {})
        match = matches.get((selected_id, job_id), {})

        related_applications.append(
            {
                "job_id": job_id,
                "job_title": _text(job.get("job_title")),
                "status": _lower(application.get("status")),
                "match_score": _float(match.get("score")),
                "strengths": list(match.get("strengths") or []),
                "concerns": list(match.get("concerns") or []),
            }
        )

    related_sessions = [
        {
            "session_id": _text(session.get("session_id")),
            "job_id": _text(session.get("job_id")),
            "job_title": _text(session.get("job_title")),
            "stage": _text(session.get("interview_stage")),
            "mode": _text(session.get("interview_mode")),
            "status": _text(session.get("status")),
            "evaluation_status": _text(session.get("evaluation_status")),
            "recommendation": _text(session.get("recommendation")),
        }
        for session in sessions
        if _text(session.get("candidate_id")) == selected_id
    ]

    return {
        "found": True,
        "candidate": {
            "candidate_id": selected_id,
            "name": _text(candidate.get("name")),
            "location": _text(candidate.get("location")),
            "summary": _text(candidate.get("summary")),
            "skills": list(candidate.get("skills") or []),
            "experience_years": _float(
                candidate.get("total_years_experience")
            ),
            "education": list(candidate.get("education") or []),
            "work_experience": list(
                candidate.get("work_experience") or []
            )[:5],
        },
        "applications": related_applications,
        "interviews": related_sessions,
    }


def search_jobs(
    *,
    title: str | None = None,
    company: str | None = None,
    required_skill: str | None = None,
    limit: int = 20,
) -> dict:
    requested_title = _lower(title)
    requested_company = _lower(company)
    requested_skill = _lower(required_skill)

    rows = []

    for job in load_all_jobs():
        title_value = _text(job.get("job_title"))
        company_value = _text(job.get("company"))
        required_skills = list(job.get("required_skills") or [])
        preferred_skills = list(job.get("preferred_skills") or [])
        skills_text = " | ".join(
            _lower(skill)
            for skill in required_skills + preferred_skills
        )

        if requested_title and requested_title not in title_value.lower():
            continue

        if requested_company and requested_company not in company_value.lower():
            continue

        if requested_skill and requested_skill not in skills_text:
            continue

        rows.append(
            {
                "job_id": _text(job.get("job_id")),
                "job_title": title_value,
                "company": company_value,
                "location": _text(job.get("location")),
                "required_experience_years": _float(
                    job.get("required_experience_years")
                ),
                "required_skills": required_skills,
                "preferred_skills": preferred_skills,
            }
        )

    safe_limit = max(1, min(int(limit or 20), 50))

    return {
        "count": len(rows),
        "returned": min(len(rows), safe_limit),
        "jobs": rows[:safe_limit],
    }


def get_pipeline_summary(job_id: str | None = None) -> dict:
    selected_job_id = _text(job_id)
    jobs_by_id = {
        _text(job.get("job_id")): job
        for job in load_all_jobs()
    }

    applications = [
        application
        for application in load_all_applications()
        if (
            not selected_job_id
            or _text(application.get("job_id")) == selected_job_id
        )
    ]

    status_counts = Counter(
        _lower(application.get("status")) or "none"
        for application in applications
    )

    per_job: dict[str, Counter] = {}

    for application in applications:
        application_job_id = _text(application.get("job_id"))
        per_job.setdefault(
            application_job_id,
            Counter(),
        )[
            _lower(application.get("status")) or "none"
        ] += 1

    job_rows = []

    for application_job_id, counts in per_job.items():
        job = jobs_by_id.get(application_job_id, {})
        job_rows.append(
            {
                "job_id": application_job_id,
                "job_title": _text(job.get("job_title")),
                "status_counts": dict(counts),
                "total": sum(counts.values()),
            }
        )

    job_rows.sort(
        key=lambda item: item["total"],
        reverse=True,
    )

    return {
        "job_id": selected_job_id or None,
        "application_count": len(applications),
        "status_counts": dict(status_counts),
        "jobs": job_rows,
    }


def get_interview_summary(
    *,
    candidate_id: str | None = None,
    job_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    selected_candidate_id = _text(candidate_id)
    selected_job_id = _text(job_id)
    selected_session_id = _text(session_id)

    sessions = []

    for session in _load_all_interview_sessions():
        if selected_session_id and _text(session.get("session_id")) != selected_session_id:
            continue
        if selected_candidate_id and _text(session.get("candidate_id")) != selected_candidate_id:
            continue
        if selected_job_id and _text(session.get("job_id")) != selected_job_id:
            continue

        answered_questions = sum(
            bool(_text(question.get("answer")))
            for question in session.get("questions") or []
        )

        sessions.append(
            {
                "session_id": _text(session.get("session_id")),
                "candidate_id": _text(session.get("candidate_id")),
                "candidate_name": _text(session.get("candidate_name")),
                "job_id": _text(session.get("job_id")),
                "job_title": _text(session.get("job_title")),
                "stage": _text(session.get("interview_stage")),
                "mode": _text(session.get("interview_mode")),
                "status": _text(session.get("status")),
                "answered_questions": answered_questions,
                "question_count": len(session.get("questions") or []),
                "evaluation_status": _text(session.get("evaluation_status")),
                "evaluation_summary": _text(session.get("evaluation_summary")),
                "recommendation": _text(session.get("recommendation")),
                "completed_time": session.get("completed_time"),
            }
        )

    return {
        "count": len(sessions),
        "sessions": sessions,
    }


def search_external_candidates(
    *,
    query_text: str,
    source_ids: list[str] | None = None,
    location: str | None = None,
    skills: list[str] | None = None,
    minimum_experience: float | None = None,
    education: str | None = None,
    limit: int = 10,
) -> dict:
    """
    Search configured candidate-discovery sources.

    External prospects remain separate from AIRS
    candidates. This tool never imports or saves them.
    """
    clean_source_ids = [
        _lower(source_id)
        for source_id in (
            source_ids
            or ["public_web", "github"]
        )
        if _lower(source_id)
    ]

    # Internal AIRS records already have a dedicated
    # search_candidates tool. Keep this tool focused on
    # configured external discovery sources.
    clean_source_ids = [
        source_id
        for source_id in clean_source_ids
        if source_id != "internal_airs"
    ]

    if not clean_source_ids:
        clean_source_ids = [
            "public_web",
        ]

    query = CandidateDiscoveryQuery(
        query_text=_text(query_text),
        location=(
            _text(location)
            or None
        ),
        skills=[
            _text(skill)
            for skill in (skills or [])
            if _text(skill)
        ],
        minimum_experience=(
            minimum_experience
        ),
        education=(
            _text(education)
            or None
        ),
        limit=max(
            1,
            min(
                int(limit or 10),
                50,
            ),
        ),
    )

    response = discover_candidates(
        query,
        source_ids=clean_source_ids,
    )

    payload = response.to_dict()

    compact_results = []

    for result in payload.get(
        "results",
        [],
    ):
        compact_results.append(
            {
                "source_id": result.get(
                    "source_id"
                ),
                "source_type": result.get(
                    "source_type"
                ),
                "external_id": result.get(
                    "external_id"
                ),
                "name": result.get("name"),
                "title": result.get("title"),
                "location": result.get(
                    "location"
                ),
                "skills": result.get(
                    "skills",
                    [],
                ),
                "summary": result.get(
                    "summary"
                ),
                "profile_url": result.get(
                    "profile_url"
                ),
                "evidence": result.get(
                    "evidence",
                    [],
                ),
                "confidence": result.get(
                    "confidence"
                ),
                "import_supported": result.get(
                    "import_supported",
                    False,
                ),
                "already_in_airs": result.get(
                    "already_in_airs",
                    False,
                ),
            }
        )

    return {
        "query": payload.get("query"),
        "searched_sources": clean_source_ids,
        "enabled_source_ids": payload.get(
            "enabled_source_ids",
            [],
        ),
        "count": len(compact_results),
        "prospects": compact_results,
        "source_errors": payload.get(
            "source_errors",
            {},
        ),
        "important_note": (
            "These are unverified external prospects. "
            "A recruiter must review the source and "
            "confirm import before AIRS creates a "
            "candidate record."
        ),
    }
