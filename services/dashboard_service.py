from __future__ import annotations

from collections import Counter
from typing import Any

from application_loader import load_all_applications
from match_loader import (
    load_all_candidates,
    load_all_jobs,
    load_all_matches,
)
from services.interview_session_service import (
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
    "none": "Not applied",
    "applied": "Applied",
    "review": "Review",
    "interview": "Interview",
    "offer": "Offer",
    "accepted": "Accepted",
    "rejected": "Rejected",
    "archived": "Archived",
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _candidate_identity(candidate: dict) -> str:
    """
    Build a stable identity key for dashboard counting.

    Priority:
    1. Candidate ID
    2. Normalized email
    3. Source path or filename
    """
    candidate_id = _clean_text(
        candidate.get("candidate_id")
    )

    if candidate_id:
        return f"id:{candidate_id}"

    email = _clean_text(
        candidate.get("email")
    ).lower()

    if email:
        return f"email:{email}"

    source = _clean_text(
        candidate.get("_source_path")
        or candidate.get("source_filepath")
        or candidate.get("source_filename")
    )

    return f"source:{source}"


def _job_identity(job: dict) -> str:
    job_id = _clean_text(job.get("job_id"))

    if job_id:
        return f"id:{job_id}"

    title = _clean_text(
        job.get("job_title")
    ).lower()

    company = _clean_text(
        job.get("company")
    ).lower()

    return f"title:{title}|company:{company}"


def _application_identity(
    application: dict,
) -> str:
    application_id = _clean_text(
        application.get("application_id")
    )

    if application_id:
        return f"id:{application_id}"

    return (
        f"candidate:{_clean_text(application.get('candidate_id'))}"
        f"|job:{_clean_text(application.get('job_id'))}"
    )


def _deduplicate_records(
    records: list[dict],
    identity_builder,
) -> list[dict]:
    unique: dict[str, dict] = {}

    for record in records:
        key = identity_builder(record)

        if not key:
            continue

        unique[key] = record

    return list(unique.values())


def normalize_degree_label(
    degree_value: Any,
) -> str:
    """
    Convert free-text degree names into broad dashboard
    categories.
    """
    degree = _clean_text(
        degree_value
    ).lower()

    if not degree:
        return "Not specified"

    if any(
        keyword in degree
        for keyword in [
            "phd",
            "ph.d",
            "doctor",
            "博士",
        ]
    ):
        return "PhD / Doctorate"

    if any(
        keyword in degree
        for keyword in [
            "mba",
            "m.b.a",
        ]
    ):
        return "MBA"

    if any(
        keyword in degree
        for keyword in [
            "master",
            "msc",
            "m.sc",
            "ma ",
            "m.a",
            "硕士",
        ]
    ):
        return "Master"

    if any(
        keyword in degree
        for keyword in [
            "bachelor",
            "bsc",
            "b.sc",
            "ba ",
            "b.a",
            "undergraduate",
            "本科",
            "学士",
        ]
    ):
        return "Bachelor"

    if any(
        keyword in degree
        for keyword in [
            "diploma",
            "associate",
            "college",
            "大专",
            "专科",
        ]
    ):
        return "Diploma / Associate"

    if any(
        keyword in degree
        for keyword in [
            "certificate",
            "certification",
            "证书",
        ]
    ):
        return "Certificate"

    return "Other"


DEGREE_RANK = {
    "Not specified": 0,
    "Certificate": 1,
    "Diploma / Associate": 2,
    "Bachelor": 3,
    "Master": 4,
    "MBA": 5,
    "PhD / Doctorate": 6,
    "Other": 2,
}


def get_highest_degree(
    candidate: dict,
) -> str:
    education_items = (
        candidate.get("education")
        or []
    )

    degree_labels = [
        normalize_degree_label(
            education.get("degree")
            if isinstance(education, dict)
            else getattr(
                education,
                "degree",
                None,
            )
        )
        for education in education_items
    ]

    if not degree_labels:
        return "Not specified"

    return max(
        degree_labels,
        key=lambda label: DEGREE_RANK.get(
            label,
            0,
        ),
    )



SKILL_ALIASES = {
    "ms excel": "Excel",
    "microsoft excel": "Excel",
    "excel": "Excel",
    "ms word": "Word",
    "microsoft word": "Word",
    "word": "Word",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "python": "Python",
    "sql": "SQL",
    "tableau": "Tableau",
    "r": "R",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "c++": "C++",
    "c#": "C#",
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "google cloud platform": "GCP",
}


def normalize_skill_label(
    skill_value: Any,
) -> str:
    """
    Normalize common skill spellings while preserving
    readable labels for skills not in the alias map.
    """
    skill = _clean_text(skill_value)

    if not skill:
        return ""

    normalized_key = " ".join(
        skill.lower().split()
    )

    if normalized_key in SKILL_ALIASES:
        return SKILL_ALIASES[normalized_key]

    # Preserve acronyms and technical punctuation.
    if skill.isupper() or any(
        character in skill
        for character in ["+", "#", ".", "/"]
    ):
        return skill

    return skill.title()


def build_candidate_skill_rows(
    candidates: list[dict],
    top_n: int = 10,
) -> list[dict]:
    """
    Count how many unique candidates have each skill.

    A repeated skill inside one candidate profile counts
    only once for that candidate.
    """
    skill_counts: Counter[str] = Counter()

    for candidate in candidates:
        candidate_skills: set[str] = set()

        for raw_skill in (
            candidate.get("skills")
            or []
        ):
            skill = normalize_skill_label(
                raw_skill
            )

            if skill:
                candidate_skills.add(skill)

        for skill in candidate_skills:
            skill_counts[skill] += 1

    return [
        {
            "skill": skill,
            "count": count,
        }
        for skill, count in skill_counts.most_common(
            max(int(top_n), 1)
        )
    ]

def build_dashboard_data() -> dict:
    """
    Load current AIRS data and return dashboard-ready
    metrics and chart rows.
    """
    candidates = _deduplicate_records(
        load_all_candidates(),
        _candidate_identity,
    )

    jobs = _deduplicate_records(
        load_all_jobs(),
        _job_identity,
    )

    applications = _deduplicate_records(
        load_all_applications(),
        _application_identity,
    )

    matches = load_all_matches()
    sessions = load_all_interview_sessions()

    completed_sessions = [
        session
        for session in sessions
        if session.status == "completed"
    ]

    finalized_evaluations = [
        session
        for session in sessions
        if session.evaluation_status
        == "completed"
    ]

    status_counts = Counter(
        _clean_text(
            application.get("status")
        ).lower()
        or "none"
        for application in applications
    )

    application_status_rows = [
        {
            "status": STATUS_LABELS[
                status
            ],
            "count": status_counts.get(
                status,
                0,
            ),
        }
        for status in STATUS_ORDER
    ]

    degree_counts = Counter(
        get_highest_degree(candidate)
        for candidate in candidates
    )

    education_rows = [
        {
            "degree": degree,
            "count": count,
        }
        for degree, count in sorted(
            degree_counts.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )
    ]

    candidate_skill_rows = (
        build_candidate_skill_rows(
            candidates,
            top_n=10,
        )
    )

    jobs_by_id = {
        _clean_text(job.get("job_id")): job
        for job in jobs
        if _clean_text(job.get("job_id"))
    }

    application_job_counts = Counter(
        _clean_text(
            application.get("job_id")
        )
        for application in applications
        if _clean_text(
            application.get("job_id")
        )
    )

    applications_by_job_rows = []

    for job_id, count in (
        application_job_counts.most_common()
    ):
        job = jobs_by_id.get(
            job_id,
            {},
        )

        job_title = (
            _clean_text(
                job.get("job_title")
            )
            or job_id
        )

        applications_by_job_rows.append(
            {
                "job": job_title,
                "count": count,
            }
        )

    interview_status_counts = Counter(
        session.status
        for session in sessions
    )

    interview_status_rows = [
        {
            "status": status
            .replace("_", " ")
            .title(),
            "count": count,
        }
        for status, count in sorted(
            interview_status_counts.items()
        )
    ]

    recommendation_counts = Counter(
        _clean_text(
            session.recommendation
        )
        for session in sessions
        if _clean_text(
            session.recommendation
        )
    )

    recommendation_rows = [
        {
            "recommendation": recommendation,
            "count": count,
        }
        for recommendation, count
        in recommendation_counts.most_common()
    ]

    match_scores = []

    for match in matches:
        try:
            match_scores.append(
                float(
                    match.get("score", 0)
                    or 0
                )
            )
        except (TypeError, ValueError):
            continue

    average_match_score = (
        round(
            sum(match_scores)
            / len(match_scores),
            1,
        )
        if match_scores
        else None
    )

    return {
        "summary": {
            "total_candidates": len(
                candidates
            ),
            "total_jobs": len(jobs),
            "total_applications": len(
                applications
            ),
            "total_interviews": len(
                sessions
            ),
            "completed_interviews": len(
                completed_sessions
            ),
            "finalized_evaluations": len(
                finalized_evaluations
            ),
            "average_match_score": (
                average_match_score
            ),
        },
        "application_status": (
            application_status_rows
        ),
        "education": education_rows,
        "candidate_skills": candidate_skill_rows,
        "applications_by_job": (
            applications_by_job_rows
        ),
        "interview_status": (
            interview_status_rows
        ),
        "recommendations": (
            recommendation_rows
        ),
    }