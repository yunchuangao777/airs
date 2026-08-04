from __future__ import annotations

from services.candidate_discovery.models import (
    CandidateDiscoveryQuery,
    CandidateDiscoveryResult,
)


SOURCE_ID = "internal_airs"
SOURCE_TYPE = "internal"


def _build_evidence(
    candidate: dict,
) -> list[str]:
    evidence: list[str] = []

    experience = candidate.get(
        "experience_years"
    )

    if experience is not None:
        evidence.append(
            f"{experience} years of experience"
        )

    match_score = candidate.get(
        "match_score"
    )

    if match_score is not None:
        evidence.append(
            f"Saved match score: {match_score}"
        )

    status = candidate.get(
        "status"
    )

    if status:
        evidence.append(
            f"Application status: {status}"
        )

    matched_skills = candidate.get(
        "matched_skills"
    ) or []

    if matched_skills:
        evidence.append(
            "Matched skills: "
            + ", ".join(
                str(skill)
                for skill in matched_skills[:8]
            )
        )

    return evidence


def search_internal_candidates(
    query: CandidateDiscoveryQuery,
) -> list[CandidateDiscoveryResult]:
    """
    Adapt the existing AIRS candidate search tool into
    the common candidate-discovery result format.

    Import search_candidates lazily to avoid a circular
    import between ai_recruiter_tools and the candidate
    discovery package.
    """
    from services.ai_recruiter_tools import (
        search_candidates,
    )

    response = search_candidates(
        name=query.name,
        skills=(
            query.skills
            if query.skills
            else None
        ),
        minimum_experience=(
            query.minimum_experience
        ),
        education=query.education,
        job_id=query.job_id,
        status=query.status,
        minimum_match_score=(
            query.minimum_match_score
        ),
        limit=query.normalized_limit(),
    )

    candidates = response.get(
        "candidates",
        [],
    )

    results: list[
        CandidateDiscoveryResult
    ] = []

    for candidate in candidates:
        candidate_id = str(
            candidate.get("candidate_id")
            or ""
        ).strip() or None

        skills = [
            str(skill).strip()
            for skill in (
                candidate.get("skills")
                or []
            )
            if str(skill).strip()
        ]

        title = (
            candidate.get("current_title")
            or candidate.get("job_title")
            or candidate.get("title")
        )

        summary = (
            candidate.get("summary")
            or candidate.get(
                "professional_summary"
            )
        )

        results.append(
            CandidateDiscoveryResult(
                source_id=SOURCE_ID,
                source_type=SOURCE_TYPE,
                external_id=None,
                candidate_id=candidate_id,
                name=(
                    str(
                        candidate.get("name")
                        or ""
                    ).strip()
                    or None
                ),
                title=(
                    str(title).strip()
                    if title
                    else None
                ),
                location=(
                    str(
                        candidate.get("location")
                        or ""
                    ).strip()
                    or None
                ),
                skills=skills,
                summary=(
                    str(summary).strip()
                    if summary
                    else None
                ),
                profile_url=None,
                evidence=_build_evidence(
                    candidate
                ),
                confidence=1.0,
                import_supported=False,
                already_in_airs=True,
                metadata={
                    "status": candidate.get(
                        "status"
                    ),
                    "match_score": (
                        candidate.get(
                            "match_score"
                        )
                    ),
                    "experience_years": (
                        candidate.get(
                            "experience_years"
                        )
                    ),
                    "matched_skills": (
                        candidate.get(
                            "matched_skills"
                        )
                        or []
                    ),
                    "missing_required_skills": (
                        candidate.get(
                            "missing_required_skills"
                        )
                        or []
                    ),
                },
            )
        )

    return results