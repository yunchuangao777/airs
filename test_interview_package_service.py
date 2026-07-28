from services.hiring_service import (
    build_hiring_dataset,
)
from services.interview_service import (
    build_interview_context,
    get_interview_candidates_for_job,
    get_interview_jobs,
)
from services.interview_package_service import (
    generate_interview_package,
    load_interview_package,
)


dataset = build_hiring_dataset()

jobs = get_interview_jobs(dataset)

if not jobs:
    raise RuntimeError(
        "No interview-eligible jobs found."
    )

job = jobs[0]

candidate_rows = (
    get_interview_candidates_for_job(
        job_id=job["job_id"],
        dataset=dataset,
    )
)

if not candidate_rows:
    raise RuntimeError(
        "No interview-eligible candidates found."
    )

candidate_row = candidate_rows[0]

context = build_interview_context(
    candidate_id=candidate_row[
        "candidate_id"
    ],
    job_id=job["job_id"],
    dataset=dataset,
)

settings = {
    "candidate_id": context[
        "candidate_id"
    ],
    "job_id": context["job_id"],
    "application_id": context.get(
        "application_id"
    ),
    "interview_type": "hiring_manager",
    "interview_type_label": (
        "Hiring Manager Interview"
    ),
    "difficulty": "standard",
    "difficulty_label": "Standard",
    "duration_minutes": 45,
    "question_count": 8,
    "focus_areas": [
        "Relevant Experience",
        "Technical Skills",
        "Problem Solving",
        "Communication",
    ],
    "recruiter_instructions": (
        "Verify the candidate's direct ownership "
        "of the most important job responsibilities."
    ),
}

print(
    "Generating package for:",
    context["candidate_name"],
    context["job_title"],
)

package = generate_interview_package(
    context=context,
    settings=settings,
    overwrite=True,
)

print(
    "Generated package:",
    package.package_id,
)

print(
    "Questions:",
    len(
        package.generated_content.questions
    ),
)

print(
    "Evaluation criteria:",
    len(
        package.generated_content
        .evaluation_criteria
    ),
)

loaded_package = load_interview_package(
    candidate_id=context[
        "candidate_id"
    ],
    job_id=context["job_id"],
)

print(
    "Reloaded package:",
    loaded_package.package_id
    if loaded_package
    else None,
)

print(
    loaded_package.model_dump_json(
        indent=2
    )
)