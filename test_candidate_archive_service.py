from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from services.candidate_archive_service import (
    archive_candidate,
    find_candidate_json_path,
)


def main() -> None:
    with TemporaryDirectory() as directory:
        json_dir = Path(directory)

        candidate_path = (
            json_dir / "sample_cv.json"
        )

        candidate_path.write_text(
            json.dumps(
                {
                    "candidate_id": "candidate-test-001",
                    "name": "Test Candidate",
                    "is_archived": False,
                },
                ensure_ascii=False,
                indent=4,
            ),
            encoding="utf-8",
        )

        found_path = find_candidate_json_path(
            "candidate-test-001",
            json_dir,
        )

        assert found_path == candidate_path

        archived = archive_candidate(
            candidate_id="candidate-test-001",
            archived_by="admin",
            json_dir=json_dir,
            enforce_permission=False,
        )

        assert archived["is_archived"] is True
        assert archived["archived_by"] == "admin"
        assert archived["archived_at"]

        saved = json.loads(
            candidate_path.read_text(
                encoding="utf-8"
            )
        )

        assert saved["is_archived"] is True

        print(
            "[PASSED] Candidate archive service "
            "tests passed."
        )


if __name__ == "__main__":
    main()