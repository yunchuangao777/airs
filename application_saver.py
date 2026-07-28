import json
from pathlib import Path

from schema import ApplicationRecord


APPLICATION_DIR = Path("outputs/applications")
APPLICATION_DIR.mkdir(parents=True, exist_ok=True)


def save_application(
    application: ApplicationRecord
) -> Path:
    output_path = (
        APPLICATION_DIR
        / f"{application.job_id}_{application.candidate_id}.json"
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            application.model_dump(mode="json"),
            file,
            ensure_ascii=False,
            indent=4,
        )

    return output_path