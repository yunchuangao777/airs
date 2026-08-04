from services.candidate_discovery.discovery_service import (
    discover_candidates,
)
from services.candidate_discovery.models import (
    CandidateDiscoveryQuery,
)


def main() -> None:
    query = CandidateDiscoveryQuery(
        query_text=(
            "Python FastAPI backend developer"
        ),
        location="Toronto",
        skills=[
            "Python",
            "FastAPI",
        ],
        minimum_experience=5,
        limit=5,
    )

    response = discover_candidates(
        query,
        source_ids=["public_web"],
    )

    payload = response.to_dict()

    print("Count:", payload["count"])
    print("Errors:", payload["source_errors"])

    for result in payload["results"]:
        print("-" * 70)
        print("Name:", result["name"])
        print("Title:", result["title"])
        print("URL:", result["profile_url"])
        print("Skills:", result["skills"])
        print("Evidence:", result["evidence"])


if __name__ == "__main__":
    main()