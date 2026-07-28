from services.hiring_service import (
    build_hiring_dataset,
)
from services.interview_service import (
    build_interview_context,
    get_interview_candidates_for_job,
    get_interview_jobs,
)


dataset = build_hiring_dataset()

jobs = get_interview_jobs(dataset)

print("Interview jobs:", len(jobs))

for job in jobs:
    print(
        job["job_title"],
        job["job_id"],
    )

    candidates = get_interview_candidates_for_job(
        job_id=job["job_id"],
        dataset=dataset,
    )

    print("Candidates:", len(candidates))

    for candidate in candidates:
        print(
            " -",
            candidate["candidate_name"],
            candidate["status"],
            candidate["match_score"],
        )


if jobs:
    first_job = jobs[0]

    candidates = get_interview_candidates_for_job(
        job_id=first_job["job_id"],
        dataset=dataset,
    )

    if candidates:
        context = build_interview_context(
            candidate_id=candidates[0][
                "candidate_id"
            ],
            job_id=first_job["job_id"],
            dataset=dataset,
        )

        print("\nInterview context:")
        print(context)