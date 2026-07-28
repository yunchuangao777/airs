from services.hiring_service import (
    build_hiring_dataset,
)
from services.interview_package_service import (
    load_interview_package,
)
from services.interview_question_service import (
    add_custom_question,
    get_or_create_question_set,
    get_selected_questions,
    load_question_set,
)
from services.interview_service import (
    get_interview_candidates_for_job,
    get_interview_jobs,
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

candidate = candidate_rows[0]

package = load_interview_package(
    candidate_id=candidate["candidate_id"],
    job_id=job["job_id"],
)

if package is None:
    raise RuntimeError(
        "Generate an interview package first."
    )

question_set = get_or_create_question_set(
    package
)

print(
    "Question set:",
    question_set.question_set_id,
)

print(
    "AI questions:",
    len(question_set.questions),
)

custom_question = add_custom_question(
    question_set=question_set,
    question_text=(
        "What would your priorities be during "
        "your first 90 days in this role?"
    ),
    category="closing",
    competency="Role Planning",
    reason=(
        "Assess the candidate's understanding of "
        "the role and ability to prioritize."
    ),
)

print(
    "Added:",
    custom_question.question_id,
)

loaded = load_question_set(
    candidate_id=package.candidate_id,
    job_id=package.job_id,
)

print(
    "Reloaded questions:",
    len(loaded.questions)
    if loaded
    else 0,
)

selected = get_selected_questions(
    loaded
)

print(
    "Selected questions:",
    len(selected),
)

for question in selected:
    print(
        question.question_id,
        question.source,
        question.edited_question,
    )