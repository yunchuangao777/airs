from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from services.interview_package_service import (
    InterviewPackage,
)


EVALUATION_TEMPLATE_DIR = Path(
    "outputs/interview_evaluation_templates"
)

EVALUATION_TEMPLATE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


class EditableEvaluationCriterion(BaseModel):
    criterion_id: str

    source: str = "ai"

    competency: str

    description: str = ""

    weight: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    strong_evidence: list[str] = Field(
        default_factory=list
    )

    weak_evidence: list[str] = Field(
        default_factory=list
    )

    selected: bool = True

    created_time: str

    updated_time: str


class InterviewEvaluationTemplate(BaseModel):
    template_id: str

    package_id: str

    candidate_id: str

    job_id: str

    application_id: str | None = None

    candidate_name: str

    job_title: str

    criteria: list[
        EditableEvaluationCriterion
    ] = Field(default_factory=list)

    rating_scale_min: int = 1

    rating_scale_max: int = 5

    recommendation_options: list[str] = Field(
        default_factory=lambda: [
            "Strongly Proceed",
            "Proceed",
            "Proceed with Reservations",
            "Hold",
            "Do Not Proceed",
        ]
    )

    created_time: str

    updated_time: str


def utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")


def get_template_path(
    candidate_id: str,
    job_id: str,
) -> Path:
    return (
        EVALUATION_TEMPLATE_DIR
        / f"{job_id}__{candidate_id}.json"
    )


def create_template_from_package(
    package: InterviewPackage,
) -> InterviewEvaluationTemplate:
    now = utc_now_iso()

    criteria: list[
        EditableEvaluationCriterion
    ] = []

    for index, criterion in enumerate(
        package.generated_content.evaluation_criteria,
        start=1,
    ):
        criteria.append(
            EditableEvaluationCriterion(
                criterion_id=(
                    criterion.criterion_id
                    or f"C{index}"
                ),
                source="ai",
                competency=criterion.competency,
                description=criterion.description,
                weight=int(
                    criterion.weight or 0
                ),
                strong_evidence=list(
                    criterion.strong_evidence
                ),
                weak_evidence=list(
                    criterion.weak_evidence
                ),
                selected=True,
                created_time=now,
                updated_time=now,
            )
        )

    return InterviewEvaluationTemplate(
        template_id=str(uuid4()),
        package_id=package.package_id,
        candidate_id=package.candidate_id,
        job_id=package.job_id,
        application_id=package.application_id,
        candidate_name=package.candidate_name,
        job_title=package.job_title,
        criteria=criteria,
        created_time=now,
        updated_time=now,
    )


def save_evaluation_template(
    template: InterviewEvaluationTemplate,
) -> Path:
    template.updated_time = utc_now_iso()

    output_path = get_template_path(
        candidate_id=template.candidate_id,
        job_id=template.job_id,
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
            template.model_dump(mode="json"),
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporary_path.replace(output_path)

    return output_path


def load_evaluation_template(
    candidate_id: str,
    job_id: str,
) -> InterviewEvaluationTemplate | None:
    path = get_template_path(
        candidate_id=candidate_id,
        job_id=job_id,
    )

    if not path.exists():
        return None

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return InterviewEvaluationTemplate.model_validate(
            data
        )

    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            f"Unable to load evaluation template "
            f"{path}: {exc}"
        ) from exc


def get_or_create_evaluation_template(
    package: InterviewPackage,
) -> InterviewEvaluationTemplate:
    existing = load_evaluation_template(
        candidate_id=package.candidate_id,
        job_id=package.job_id,
    )

    if existing is not None:
        return existing

    template = create_template_from_package(
        package
    )

    save_evaluation_template(template)

    return template


def add_custom_criterion(
    template: InterviewEvaluationTemplate,
    competency: str,
    description: str = "",
    weight: int = 0,
) -> EditableEvaluationCriterion:
    cleaned_competency = competency.strip()

    if not cleaned_competency:
        raise ValueError(
            "Competency is required."
        )

    now = utc_now_iso()

    custom_count = sum(
        1
        for criterion in template.criteria
        if criterion.source == "recruiter"
    )

    criterion = EditableEvaluationCriterion(
        criterion_id=(
            f"CUSTOM-{custom_count + 1}"
        ),
        source="recruiter",
        competency=cleaned_competency,
        description=description.strip(),
        weight=int(weight),
        selected=True,
        created_time=now,
        updated_time=now,
    )

    template.criteria.append(criterion)

    save_evaluation_template(template)

    return criterion


def get_selected_criteria(
    template: InterviewEvaluationTemplate,
) -> list[EditableEvaluationCriterion]:
    return [
        criterion
        for criterion in template.criteria
        if criterion.selected
    ]