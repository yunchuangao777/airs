import json
from pathlib import Path


INTERVIEW_DIR = Path("outputs/interviews")
INTERVIEW_DIR.mkdir(parents=True, exist_ok=True)


def save_interview_prep(prep):
    filename = f"{prep.job_id}_{prep.candidate_id}.json"
    path = INTERVIEW_DIR / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            prep.model_dump(),
            f,
            ensure_ascii=False,
            indent=4
        )

    return path