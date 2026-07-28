import json
from pathlib import Path


MATCH_DIR = Path("outputs/matches")
MATCH_DIR.mkdir(parents=True, exist_ok=True)


def save_match_result(match_result):
    match_method = (
        getattr(
            match_result,
            "match_method",
            None,
        )
        or "ai"
    )

    filename = (
        f"{match_result.job_id}_"
        f"{match_result.candidate_id}_"
        f"{match_method}.json"
    )

    output_path = MATCH_DIR / filename

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            match_result.model_dump(),
            file,
            ensure_ascii=False,
            indent=4,
        )

    return output_path