import json
from pathlib import Path


MATCH_DIR = Path("outputs/matches")
MATCH_DIR.mkdir(parents=True, exist_ok=True)


def save_match_result(match_result):

    filename = (
        f"{match_result.job_id}_"
        f"{match_result.candidate_id}.json"
    )

    path = MATCH_DIR / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            match_result.model_dump(),
            f,
            ensure_ascii=False,
            indent=4
        )

    return path