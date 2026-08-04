from __future__ import annotations

from services.ai_recruiter_service import (
    ask_ai_recruiter,
)


TEST_QUESTIONS = [
    "Give me a brief overview of the current recruitment activity.",
    (
        "Find up to five candidates with at least "
        "five years of experience."
    ),
    (
        "Which interview sessions are completed but "
        "still waiting for evaluation?"
    ),
]


def main() -> None:
    print("=" * 70)
    print("AIRS AI Recruiter Service Test")
    print("=" * 70)

    for index, question in enumerate(
        TEST_QUESTIONS,
        start=1,
    ):
        print(f"\nQuestion {index}:")
        print(question)

        result = ask_ai_recruiter(
            question,
            conversation_history=[],
        )

        print("\nAnswer:")
        print(result["answer"])

        print("\nTools used:")
        print(result["tool_trace"])

        assert result["answer"].strip()

    print("\n" + "=" * 70)
    print(
        "[PASSED] AI Recruiter model service is working."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()