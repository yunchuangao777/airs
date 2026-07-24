import json
from pathlib import Path


CANDIDATE_DIR = Path("outputs/json")
JOB_DIR = Path("outputs/jobs")
MATCH_DIR = Path("outputs/matches")


def load_json_file(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_candidates() -> list[dict]:
    candidates = []

    for path in CANDIDATE_DIR.glob("*.json"):
        data = load_json_file(path)
        data["_source_path"] = str(path)
        candidates.append(data)

    return candidates


def load_all_jobs() -> list[dict]:
    jobs = []

    for path in JOB_DIR.glob("*.json"):
        data = load_json_file(path)
        data["_source_path"] = str(path)
        jobs.append(data)

    return jobs


def load_all_matches() -> list[dict]:
    matches = []

    for path in MATCH_DIR.glob("*.json"):
        data = load_json_file(path)
        data["_source_path"] = str(path)
        matches.append(data)

    return matches


def load_matches_by_job(job_id: str) -> list[dict]:
    matches = load_all_matches()

    return [
        m for m in matches
        if m.get("job_id") == job_id
    ]


def load_match_for_candidate_job(
    candidate_id: str,
    job_id: str
) -> dict | None:
    matches = load_all_matches()

    for m in matches:
        if (
            m.get("candidate_id") == candidate_id
            and m.get("job_id") == job_id
        ):
            return m

    return None


def get_ranked_matches_by_job(
    job_id: str,
    min_score: float = 0
) -> list[dict]:
    matches = load_matches_by_job(job_id)

    filtered = [
        m for m in matches
        if float(m.get("score", 0)) >= min_score
    ]

    return sorted(
        filtered,
        key=lambda x: float(x.get("score", 0)),
        reverse=True
    )

def load_candidate_by_id(candidate_id: str) -> dict | None:
    candidates = load_all_candidates()

    for c in candidates:
        if c.get("candidate_id") == candidate_id:
            return c

    return None

def load_matches_by_candidate(candidate_id: str) -> list[dict]:
    matches = load_all_matches()

    return [
        m for m in matches
        if m.get("candidate_id") == candidate_id
    ]