from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from openai import OpenAI
from pydantic import BaseModel, Field


# =========================================================
# Configuration
# =========================================================

INTERVIEW_PACKAGE_DIR = Path(
    "outputs/interview_packages"
)

INTERVIEW_PACKAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OPENAI_MODEL = os.getenv(
    "OPENAI_INTERVIEW_MODEL",
    # "gpt-5.6",
    "gpt-4o-mini",
)


# =========================================================
# Structured package models
# =========================================================

QuestionCategory = Literal[
    "opening",
    "experience",
    "technical",
    "behavioral",
    "problem_solving",
    "leadership",
    "motivation",
    "concern_probe",
    "closing",
]


class InterviewQuestion(BaseModel):
    """
    One structured interview question.
    """

    question_id: str = Field(
        description=(
            "A short stable identifier such as Q1, Q2, Q3."
        )
    )

    category: QuestionCategory

    competency: str = Field(
        description=(
            "The primary competency assessed by this question."
        )
    )

    question: str

    reason: str = Field(
        description=(
            "Why this question is relevant to the candidate "
            "and selected job."
        )
    )

    strong_answer_indicators: list[str]

    warning_signs: list[str]

    suggested_follow_ups: list[str]


class EvaluationCriterion(BaseModel):
    """
    One interview scorecard criterion.
    """

    criterion_id: str = Field(
        description=(
            "A short stable identifier such as C1, C2, C3."
        )
    )

    competency: str

    description: str

    weight: int = Field(
        ge=0,
        le=100,
        description=(
            "Relative percentage weight. All criteria should "
            "total approximately 100."
        ),
    )

    strong_evidence: list[str]

    weak_evidence: list[str]


class InterviewAgendaItem(BaseModel):
    """
    One section of the interview plan.
    """

    section: str

    minutes: int = Field(
        ge=1,
        le=120,
    )

    objective: str


class InterviewPackageContent(BaseModel):
    """
    AI-generated content returned by OpenAI.
    """

    candidate_summary: str

    role_fit_summary: str

    strengths: list[str]

    concerns: list[str]

    areas_to_verify: list[str]

    interview_objectives: list[str]

    agenda: list[InterviewAgendaItem]

    questions: list[InterviewQuestion]

    evaluation_criteria: list[EvaluationCriterion]

    interviewer_guidance: list[str]


class InterviewPackage(BaseModel):
    """
    Complete saved interview package.
    """

    package_id: str

    candidate_id: str

    job_id: str

    application_id: str | None = None

    candidate_name: str

    job_title: str

    company: str = ""

    interview_type: str

    interview_type_label: str

    difficulty: str

    difficulty_label: str

    duration_minutes: int

    requested_question_count: int

    focus_areas: list[str]

    recruiter_instructions: str = ""

    generated_content: InterviewPackageContent

    model_name: str

    created_time: str

    updated_time: str


# =========================================================
# General helpers
# =========================================================

def utc_now_iso() -> str:
    """
    Return a timezone-aware UTC timestamp.
    """
    return datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")


def get_package_path(
    candidate_id: str,
    job_id: str,
) -> Path:
    """
    Return the JSON file path for one candidate-job pair.

    There is initially one current preparation package
    for each candidate and job.
    """
    filename = (
        f"{job_id}__{candidate_id}.json"
    )

    return INTERVIEW_PACKAGE_DIR / filename


def normalize_list(
    value,
) -> list[str]:
    """
    Convert common stored values into a clean string list.

    Match records may contain a list, a string, or no value.
    """
    if not value:
        return []

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, str):
        normalized = value.replace(
            ";",
            "\n",
        ).replace(
            ",",
            "\n",
        )

        return [
            item.strip().lstrip("-•").strip()
            for item in normalized.splitlines()
            if item.strip().lstrip("-•").strip()
        ]

    return [str(value).strip()]


def compact_json(
    value,
) -> str:
    """
    Serialize context data for inclusion in the prompt.
    """
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


# =========================================================
# Prompt preparation
# =========================================================

def build_candidate_prompt_data(
    context: dict,
) -> dict:
    """
    Keep only relevant candidate information for generation.
    """
    candidate = context.get(
        "candidate",
        {},
    )

    return {
        "candidate_id": context.get(
            "candidate_id"
        ),
        "name": context.get(
            "candidate_name"
        ),
        "email": candidate.get("email"),
        "location": candidate.get(
            "location"
        ),
        "professional_summary": candidate.get(
            "summary"
        ),
        "total_years_experience": (
            candidate.get(
                "total_years_experience"
            )
        ),
        "skills": candidate.get(
            "skills",
            [],
        ),
        "education": candidate.get(
            "education",
            [],
        ),
        "work_experience": candidate.get(
            "work_experience",
            [],
        ),
        "certifications": candidate.get(
            "certifications",
            [],
        ),
        "projects": candidate.get(
            "projects",
            [],
        ),
        "raw_cv_text": candidate.get(
            "raw_text"
        ),
    }


def build_job_prompt_data(
    context: dict,
) -> dict:
    """
    Keep only relevant job information for generation.
    """
    job = context.get(
        "job",
        {},
    )

    return {
        "job_id": context.get("job_id"),
        "job_title": context.get(
            "job_title"
        ),
        "company": context.get(
            "company"
        ),
        "location": job.get("location"),
        "department": job.get(
            "department"
        ),
        "employment_type": job.get(
            "employment_type"
        ),
        "description": (
            job.get("description")
            or job.get("job_description")
            or job.get("raw_text")
        ),
        "responsibilities": job.get(
            "responsibilities",
            [],
        ),
        "required_skills": job.get(
            "required_skills",
            [],
        ),
        "preferred_skills": job.get(
            "preferred_skills",
            [],
        ),
        "required_experience_years": (
            job.get(
                "required_experience_years"
            )
        ),
        "education_requirements": job.get(
            "education_requirements",
            [],
        ),
    }


def build_match_prompt_data(
    context: dict,
) -> dict:
    """
    Prepare existing job-match information.
    """
    match = context.get(
        "match",
        {},
    )

    return {
        "match_score": context.get(
            "match_score"
        ),
        "match_method": context.get(
            "match_method"
        ),
        "recommendation": (
            context.get("recommendation")
            or match.get("recommendation")
        ),
        "strengths": normalize_list(
            context.get("strengths")
            or match.get("strengths")
        ),
        "concerns": normalize_list(
            context.get("concerns")
            or match.get("concerns")
        ),
        "matched_skills": normalize_list(
            context.get("matched_skills")
            or match.get("matched_skills")
        ),
        "missing_required_skills": (
            normalize_list(
                context.get(
                    "missing_required_skills"
                )
                or match.get(
                    "missing_required_skills"
                )
            )
        ),
    }


def build_generation_prompt(
    context: dict,
    settings: dict,
) -> str:
    """
    Build the user prompt used for package generation.
    """
    candidate_data = (
        build_candidate_prompt_data(
            context
        )
    )

    job_data = build_job_prompt_data(
        context
    )

    match_data = build_match_prompt_data(
        context
    )

    return f"""
Create a structured interview preparation package.

CANDIDATE:
{compact_json(candidate_data)}

JOB:
{compact_json(job_data)}

CURRENT APPLICATION STATUS:
{context.get("status") or "unknown"}

EXISTING MATCH ANALYSIS:
{compact_json(match_data)}

INTERVIEW SETTINGS:
{compact_json(settings)}

REQUIREMENTS:

1. Generate exactly approximately
   {settings.get("question_count", 8)}
   main interview questions.

2. Tailor the package specifically to this candidate and job.

3. Use evidence from the CV, job information, and match analysis.
   Do not invent experience, credentials, employers, achievements,
   technologies, or qualifications.

4. Clearly distinguish:
   - confirmed candidate strengths;
   - possible concerns;
   - information that must be verified during the interview.

5. Include questions covering the requested focus areas:
   {", ".join(settings.get("focus_areas", []))}

6. Match the requested interview type:
   {settings.get("interview_type_label")}

7. Match the requested difficulty:
   {settings.get("difficulty_label")}

8. Design an agenda totaling approximately
   {settings.get("duration_minutes")} minutes.

9. For every question include:
   - why it is being asked;
   - strong-answer indicators;
   - warning signs;
   - useful follow-up questions;
   - the competency evaluated.

10. Create a practical evaluation scorecard.
    Evaluation weights should total approximately 100.

11. Do not evaluate protected personal characteristics.
    Do not infer personality, honesty, emotion, health,
    ethnicity, religion, age, family status, disability,
    or other sensitive characteristics.

12. Recruiter instructions:
    {settings.get("recruiter_instructions") or "None provided."}
""".strip()


SYSTEM_INSTRUCTIONS = """
You are an expert structured-interview designer supporting
professional recruiters and hiring managers.

Create job-related, evidence-based interview preparation.
Focus only on qualifications, experience, skills, work examples,
role motivation, and job-relevant competencies.

Do not make the hiring decision. Do not infer protected or sensitive
personal characteristics. Do not use appearance, accent, emotion,
facial expression, or other non-job-related signals.

When evidence is incomplete, identify an area to verify instead of
making an assumption.
""".strip()


# =========================================================
# OpenAI generation
# =========================================================

def generate_interview_package(
    context: dict,
    settings: dict,
    overwrite: bool = True,
) -> InterviewPackage:
    """
    Generate, validate, and save one interview package.
    """
    candidate_id = str(
        context.get("candidate_id") or ""
    ).strip()

    job_id = str(
        context.get("job_id") or ""
    ).strip()

    if not candidate_id:
        raise ValueError(
            "Candidate ID is required."
        )

    if not job_id:
        raise ValueError(
            "Job ID is required."
        )

    existing_package = load_interview_package(
        candidate_id=candidate_id,
        job_id=job_id,
    )

    if existing_package and not overwrite:
        return existing_package

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured."
        )

    client = OpenAI(
        api_key=api_key
    )

    prompt = build_generation_prompt(
        context=context,
        settings=settings,
    )

    response = client.responses.parse(
        model=OPENAI_MODEL,
        input=[
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTIONS,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=InterviewPackageContent,
    )

    generated_content = (
        response.output_parsed
    )

    if generated_content is None:
        raise RuntimeError(
            "OpenAI did not return a valid "
            "interview package."
        )

    now = utc_now_iso()

    package = InterviewPackage(
        package_id=(
            existing_package.package_id
            if existing_package
            else str(uuid4())
        ),
        candidate_id=candidate_id,
        job_id=job_id,
        application_id=context.get(
            "application_id"
        ),
        candidate_name=(
            context.get("candidate_name")
            or "Unknown Candidate"
        ),
        job_title=(
            context.get("job_title")
            or "Untitled Job"
        ),
        company=(
            context.get("company")
            or ""
        ),
        interview_type=(
            settings.get("interview_type")
            or "hiring_manager"
        ),
        interview_type_label=(
            settings.get(
                "interview_type_label"
            )
            or "Hiring Manager Interview"
        ),
        difficulty=(
            settings.get("difficulty")
            or "standard"
        ),
        difficulty_label=(
            settings.get(
                "difficulty_label"
            )
            or "Standard"
        ),
        duration_minutes=int(
            settings.get(
                "duration_minutes",
                45,
            )
        ),
        requested_question_count=int(
            settings.get(
                "question_count",
                8,
            )
        ),
        focus_areas=[
            str(value)
            for value in settings.get(
                "focus_areas",
                [],
            )
        ],
        recruiter_instructions=(
            settings.get(
                "recruiter_instructions"
            )
            or ""
        ),
        generated_content=generated_content,
        model_name=OPENAI_MODEL,
        created_time=(
            existing_package.created_time
            if existing_package
            else now
        ),
        updated_time=now,
    )

    save_interview_package(package)

    return package


# =========================================================
# Storage
# =========================================================

def save_interview_package(
    package: InterviewPackage,
) -> Path:
    """
    Save a validated package to JSON.
    """
    output_path = get_package_path(
        candidate_id=package.candidate_id,
        job_id=package.job_id,
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
            package.model_dump(
                mode="json"
            ),
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporary_path.replace(
        output_path
    )

    return output_path


def load_interview_package(
    candidate_id: str,
    job_id: str,
) -> InterviewPackage | None:
    """
    Load and validate a saved package.
    """
    package_path = get_package_path(
        candidate_id=candidate_id,
        job_id=job_id,
    )

    if not package_path.exists():
        return None

    try:
        with open(
            package_path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return InterviewPackage.model_validate(
            data
        )

    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            f"Unable to load interview package "
            f"{package_path}: {exc}"
        ) from exc


def delete_interview_package(
    candidate_id: str,
    job_id: str,
) -> bool:
    """
    Delete the current package for a candidate and job.
    """
    package_path = get_package_path(
        candidate_id=candidate_id,
        job_id=job_id,
    )

    if not package_path.exists():
        return False

    package_path.unlink()
    return True


def interview_package_exists(
    candidate_id: str,
    job_id: str,
) -> bool:
    """
    Check whether a saved package exists.
    """
    return get_package_path(
        candidate_id=candidate_id,
        job_id=job_id,
    ).exists()