from __future__ import annotations

from services.ai_recruiter_tools import (
    search_external_candidates,
)


def main() -> None:
    print("=" * 70)
    print("AI Recruiter External Search Tool Test")
    print("=" * 70)

    result = search_external_candidates(
        query_text=(
            "Python FastAPI backend developer"
        ),
        source_ids=["public_web"],
        location="Toronto",
        skills=[
            "Python",
            "FastAPI",
        ],
        minimum_experience=5,
        education=None,
        limit=5,
    )

    print("Searched sources:")
    print(result["searched_sources"])

    print("\nProspect count:")
    print(result["count"])

    print("\nSource errors:")
    print(result["source_errors"])

    for prospect in result["prospects"]:
        print("-" * 70)
        print("Name:", prospect["name"])
        print("Title:", prospect["title"])
        print("URL:", prospect["profile_url"])
        print("Skills:", prospect["skills"])
        print("Evidence:", prospect["evidence"])

        assert prospect["already_in_airs"] is False
        assert prospect["import_supported"] is True
        assert prospect["profile_url"]

    assert result["searched_sources"] == [
        "public_web"
    ]

    print("=" * 70)
    print(
        "[PASSED] AI Recruiter external-search "
        "tool is working."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()