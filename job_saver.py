import json
from pathlib import Path


JOB_OUTPUT_DIR = Path("outputs/jobs")
MATCH_OUTPUT_DIR = Path("outputs/matches")
INTERVIEW_OUTPUT_DIR = Path("outputs/interviews")

JOB_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_job_json(job):
    """
    Creates a new job or updates an existing job.

    Because the filename is based on job_id, saving the same
    job_id overwrites the existing JSON file.
    """
    output_path = JOB_OUTPUT_DIR / f"{job.job_id}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            job.model_dump(),
            f,
            ensure_ascii=False,
            indent=4,
        )

    return output_path


def delete_job_json(
    job_id: str,
    delete_related: bool = False,
) -> bool:
    """
    Delete a saved job.

    When delete_related=True, also delete matching results and
    interview-prep files associated with the job.
    """
    job_path = JOB_OUTPUT_DIR / f"{job_id}.json"

    deleted = False

    if job_path.exists():
        job_path.unlink()
        deleted = True

    if delete_related:
        if MATCH_OUTPUT_DIR.exists():
            for path in MATCH_OUTPUT_DIR.glob(f"{job_id}_*.json"):
                path.unlink()

        if INTERVIEW_OUTPUT_DIR.exists():
            for path in INTERVIEW_OUTPUT_DIR.glob(f"{job_id}_*.json"):
                path.unlink()

    return deleted