from services.hiring_service import (
    build_hiring_dataset,
    get_job_status_summaries,
)

dataset = build_hiring_dataset()
summaries = get_job_status_summaries(dataset)

print("Application rows:", len(dataset))

for summary in summaries:
    print(
        summary["job_title"],
        summary["total_candidates"],
        summary["status_counts"],
    )