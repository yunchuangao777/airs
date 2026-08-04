from __future__ import annotations

from services.candidate_discovery.discovery_service import (
    discover_candidates,
)
from services.candidate_discovery.models import (
    CandidateDiscoveryQuery,
)


def main() -> None:
    print("=" * 70)
    print("AIRS Internal Candidate Discovery Test")
    print("=" * 70)

    query = CandidateDiscoveryQuery(
        query_text=(
            "ALl candidates"
        ),
        minimum_experience=None,
        limit=20,
    )

    response = discover_candidates(
        query,
        source_ids=["internal_airs"],
    )

    payload = response.to_dict()

    print(
        "Enabled sources:",
        payload["enabled_source_ids"],
    )
    print(
        "Internal result count:",
        payload["count"],
    )

    for result in payload["results"]:
        print("-" * 70)
        print("Candidate:", result["name"])
        print(
            "Candidate ID:",
            result["candidate_id"],
        )
        print(
            "Experience:",
            result["metadata"].get(
                "experience_years"
            ),
        )
        print("Skills:", result["skills"])
        print("Evidence:", result["evidence"])

        assert result["source_id"] == (
            "internal_airs"
        )
        assert result["already_in_airs"] is True
        assert result["import_supported"] is False
        assert result["candidate_id"]

    assert "internal_airs" in (
        payload["enabled_source_ids"]
    )

    print("=" * 70)
    print(
        "[PASSED] Internal candidate discovery "
        "adapter is working."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()