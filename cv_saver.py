from pathlib import Path
import json

UPLOAD_DIR = Path("cvs")
OUTPUT_DIR = Path("outputs")
JSON_DIR = OUTPUT_DIR / "json"

UPLOAD_DIR.mkdir(exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)

def save_candidate_json(candidate, filename):
    output_path = JSON_DIR / f"{Path(filename).stem}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            candidate.model_dump(),
            f,
            ensure_ascii=False,
            indent=4
        )

    return output_path