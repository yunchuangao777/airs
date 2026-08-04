from __future__ import annotations

from services.candidate_discovery.models import (
    CandidateDiscoveryQuery,
)
from services.candidate_discovery.public_web_source import (
    search_public_web_candidates,
)


class FakeTavilyClient:
    def search(self, **kwargs):
        assert kwargs["topic"] == "general"
        assert kwargs["max_results"] == 5
        assert "linkedin.com" in (
            kwargs["exclude_domains"]
        )

        return {
            "results": [
                {
                    "title": (
                        "Jane Smith - Data Engineering Portfolio"
                    ),
                    "url": (
                        "https://example.com/jane-smith"
                    ),
                    "content": (
                        "Toronto-based data engineer with "
                        "Python, FastAPI, SQL, and 7 years "
                        "of professional experience."
                    ),
                    "score": 0.91,
                },
                {
                    "title": "Invalid result",
                    "url": "javascript:alert(1)",
                    "content": "Should be ignored.",
                    "score": 0.5,
                },
            ]
        }


def main() -> None:
    query = CandidateDiscoveryQuery(
        query_text=(
            "Find backend candidates"
        ),
        location="Toronto",
        skills=[
            "Python",
            "FastAPI",
        ],
        minimum_experience=5,
        limit=5,
    )

    source_config = {
        "excluded_domains": [
            "linkedin.com",
            "indeed.com",
        ]
    }

    results = (
        search_public_web_candidates(
            query,
            source_config=source_config,
            client=FakeTavilyClient(),
        )
    )

    assert len(results) == 1

    result = results[0]

    assert result.source_id == (
        "public_web"
    )
    assert result.source_type == "tavily"
    assert result.already_in_airs is False
    assert result.import_supported is True
    assert result.candidate_id is None
    assert result.name == "Jane Smith"
    assert result.location == "Toronto"
    assert result.skills == [
        "Python",
        "FastAPI",
    ]
    assert result.profile_url == (
        "https://example.com/jane-smith"
    )

    print("Candidate:", result.name)
    print("Title:", result.title)
    print("Skills:", result.skills)
    print("Evidence:", result.evidence)
    print(
        "[PASSED] Public web discovery adapter "
        "unit test passed."
    )


if __name__ == "__main__":
    main()