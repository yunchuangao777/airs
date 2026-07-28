from schema import MatchResult


def normalize_text(value: str | None) -> str:
    return str(value or "").strip().lower()


def normalize_skills(skills: list[str]) -> set[str]:
    return {
        normalize_text(skill)
        for skill in skills
        if normalize_text(skill)
    }


def contains_any_keyword(
    text: str,
    keywords: list[str],
) -> bool:
    normalized_text = normalize_text(text)

    return any(
        normalize_text(keyword) in normalized_text
        for keyword in keywords
        if normalize_text(keyword)
    )


def get_candidate_education_text(candidate: dict) -> str:
    parts = []

    for education in candidate.get("education", []):
        parts.extend(
            [
                education.get("school"),
                education.get("degree"),
                education.get("major"),
                education.get("graduation_year"),
            ]
        )

    return " ".join(
        str(part)
        for part in parts
        if part
    )


def calculate_skill_score(
    candidate_skills: set[str],
    required_skills: set[str],
    preferred_skills: set[str],
) -> tuple[float, list[str], list[str]]:
    matched_required = sorted(
        candidate_skills.intersection(required_skills)
    )

    missing_required = sorted(
        required_skills.difference(candidate_skills)
    )

    matched_preferred = sorted(
        candidate_skills.intersection(preferred_skills)
    )

    if required_skills:
        required_ratio = (
            len(matched_required) / len(required_skills)
        )
    else:
        required_ratio = 1.0

    if preferred_skills:
        preferred_ratio = (
            len(matched_preferred) / len(preferred_skills)
        )
    else:
        preferred_ratio = 1.0

    # Required skills count more than preferred skills.
    score = (
        required_ratio * 80
        + preferred_ratio * 20
    )

    matched_skills = sorted(
        set(matched_required + matched_preferred)
    )

    return score, matched_skills, missing_required


def calculate_experience_score(
    candidate_years,
    required_years: float,
) -> float:
    if required_years <= 0:
        return 100.0

    try:
        candidate_value = float(candidate_years or 0)
    except (TypeError, ValueError):
        candidate_value = 0.0

    return min(
        candidate_value / required_years,
        1.0,
    ) * 100


def calculate_education_score(
    candidate: dict,
    education_keywords: list[str],
) -> float:
    if not education_keywords:
        return 100.0

    education_text = get_candidate_education_text(
        candidate
    )

    matched_count = sum(
        1
        for keyword in education_keywords
        if normalize_text(keyword)
        in normalize_text(education_text)
    )

    return (
        matched_count
        / len(education_keywords)
        * 100
    )


def calculate_location_score(
    candidate_location: str | None,
    preferred_location: str,
) -> float:
    if not preferred_location.strip():
        return 100.0

    candidate_text = normalize_text(
        candidate_location
    )
    preferred_text = normalize_text(
        preferred_location
    )

    return (
        100.0
        if preferred_text in candidate_text
        else 0.0
    )


def score_to_recommendation(score: float) -> str:
    if score >= 90:
        return "Excellent match"
    if score >= 75:
        return "Strong match"
    if score >= 60:
        return "Possible match"
    if score >= 40:
        return "Weak match"

    return "Poor match"


def match_candidate_traditional(
    candidate: dict,
    job: dict,
    required_skills: list[str],
    preferred_skills: list[str],
    required_experience_years: float,
    education_keywords: list[str],
    preferred_location: str,
    skill_weight: float,
    experience_weight: float,
    education_weight: float,
    location_weight: float,
) -> MatchResult:
    candidate_skills = normalize_skills(
        candidate.get("skills", [])
    )

    required_skill_set = normalize_skills(
        required_skills
    )

    preferred_skill_set = normalize_skills(
        preferred_skills
    )

    (
        skill_score,
        matched_skills,
        missing_required_skills,
    ) = calculate_skill_score(
        candidate_skills=candidate_skills,
        required_skills=required_skill_set,
        preferred_skills=preferred_skill_set,
    )

    experience_score = calculate_experience_score(
        candidate_years=candidate.get(
            "total_years_experience"
        ),
        required_years=required_experience_years,
    )

    education_score = calculate_education_score(
        candidate=candidate,
        education_keywords=education_keywords,
    )

    location_score = calculate_location_score(
        candidate_location=candidate.get("location"),
        preferred_location=preferred_location,
    )

    total_weight = (
        skill_weight
        + experience_weight
        + education_weight
        + location_weight
    )

    if total_weight <= 0:
        raise ValueError(
            "At least one matching weight must be greater than zero."
        )

    final_score = (
        skill_score * skill_weight
        + experience_score * experience_weight
        + education_score * education_weight
        + location_score * location_weight
    ) / total_weight

    strengths = []
    concerns = []

    if skill_score >= 75:
        strengths.append(
            "Strong overlap with the selected skills."
        )
    elif missing_required_skills:
        concerns.append(
            "Missing required skills: "
            + ", ".join(missing_required_skills)
        )

    if experience_score >= 100:
        strengths.append(
            "Meets or exceeds the experience requirement."
        )
    else:
        concerns.append(
            "Does not fully meet the experience requirement."
        )

    if education_keywords:
        if education_score > 0:
            strengths.append(
                "Education partially or fully matches the criteria."
            )
        else:
            concerns.append(
                "Education criteria were not identified."
            )

    if preferred_location.strip():
        if location_score == 100:
            strengths.append(
                "Candidate location matches the preferred location."
            )
        else:
            concerns.append(
                "Candidate location does not match the preferred location."
            )

    return MatchResult(
        candidate_id=candidate.get("candidate_id"),
        job_id=job.get("job_id"),
        candidate_name=candidate.get("name"),
        job_title=job.get("job_title"),
        match_method="traditional",
        score=round(final_score, 1),
        skill_score=round(skill_score, 1),
        experience_score=round(
            experience_score,
            1,
        ),
        education_score=round(
            education_score,
            1,
        ),
        location_score=round(
            location_score,
            1,
        ),
        matched_skills=matched_skills,
        missing_required_skills=(
            missing_required_skills
        ),
        strengths=strengths,
        concerns=concerns,
        recommendation=score_to_recommendation(
            final_score
        ),
    )