from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from services.permission_service import (
    require_permission,
)


CANDIDATE_JSON_DIR = Path(
    "outputs/json"
)


def _load_json_file(
    path: Path,
) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Candidate JSON must contain an object: {path}"
        )

    return data


def _save_json_file(
    path: Path,
    data: dict,
) -> None:
    temporary_path = path.with_suffix(
        ".tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4,
        )

    temporary_path.replace(path)


def find_candidate_json_path(
    candidate_id: str,
    json_dir: Path = CANDIDATE_JSON_DIR,
) -> Path | None:
    clean_candidate_id = str(
        candidate_id or ""
    ).strip()

    if not clean_candidate_id:
        return None

    if not json_dir.exists():
        return None

    for path in json_dir.glob("*.json"):
        try:
            candidate = _load_json_file(
                path
            )
        except (
            OSError,
            json.JSONDecodeError,
            ValueError,
        ):
            continue

        stored_candidate_id = str(
            candidate.get(
                "candidate_id",
                "",
            )
        ).strip()

        if stored_candidate_id == clean_candidate_id:
            return path

    return None


def archive_candidate(
    *,
    candidate_id: str,
    archived_by: str,
    json_dir: Path = CANDIDATE_JSON_DIR,
    enforce_permission: bool = True,
) -> dict:
    if enforce_permission:
        require_permission(
            "candidate.archive",
            message=(
                "You do not have permission to "
                "archive candidates."
            ),
        )

    path = find_candidate_json_path(
        candidate_id,
        json_dir,
    )

    if path is None:
        raise ValueError(
            "Candidate record was not found."
        )

    candidate = _load_json_file(
        path
    )

    if candidate.get(
        "is_archived",
        False,
    ):
        return candidate

    candidate["is_archived"] = True
    candidate["archived_at"] = (
        datetime.now().isoformat(
            timespec="seconds"
        )
    )
    candidate["archived_by"] = str(
        archived_by or ""
    ).strip() or None

    _save_json_file(
        path,
        candidate,
    )

    return candidate