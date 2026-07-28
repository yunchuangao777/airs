import json
from pathlib import Path
from typing import Optional


APPLICATION_DIR = Path("outputs/applications")


def load_all_applications() -> list[dict]:
    applications = []

    if not APPLICATION_DIR.exists():
        return applications

    for path in APPLICATION_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)

            data["_source_path"] = str(path)
            applications.append(data)

        except (OSError, json.JSONDecodeError) as exc:
            print(f"Unable to load {path}: {exc}")

    return applications


def load_application(
    candidate_id: str,
    job_id: str,
) -> Optional[dict]:
    path = (
        APPLICATION_DIR
        / f"{job_id}_{candidate_id}.json"
    )

    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_applications_by_candidate(
    candidate_id: str
) -> list[dict]:
    return [
        application
        for application in load_all_applications()
        if application.get("candidate_id") == candidate_id
    ]


def load_applications_by_job(
    job_id: str
) -> list[dict]:
    return [
        application
        for application in load_all_applications()
        if application.get("job_id") == job_id
    ]