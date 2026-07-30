from __future__ import annotations

import sys

from services.interview_session_service import (
    find_session_by_candidate_token,
    load_all_interview_sessions,
)
from pathlib import Path

def mask_token(token: str) -> str:
    """
    Hide most of the token when printing it.
    """
    if len(token) <= 12:
        return "*" * len(token)

    return f"{token[:6]}...{token[-6:]}"


def find_available_ai_session():
    """
    Return the first enabled AI Chat session that has
    a candidate access token.
    """
    sessions = load_all_interview_sessions()

    for session in sessions:
        if (
            session.interview_mode == "ai_chat"
            and session.candidate_access_enabled
            and session.candidate_access_token
        ):
            return session

    return None


def test_valid_token() -> bool:
    """
    Confirm that a valid stored token returns the
    expected interview session.
    """
    source_session = find_available_ai_session()

    if source_session is None:
        print(
            "\n[SKIPPED] No AI Chat session with an "
            "access token was found."
        )
        print(
            "Create a new AI Chat session first, then "
            "run this test again."
        )
        return False

    token = source_session.candidate_access_token

    found_session = find_session_by_candidate_token(
        token
    )

    print("\n--- Valid token test ---")
    print(f"Token: {mask_token(token)}")

    if found_session is None:
        print("[FAILED] The valid token returned None.")
        return False

    if (
        found_session.session_id
        != source_session.session_id
    ):
        print(
            "[FAILED] The token returned the wrong "
            "interview session."
        )
        print(
            "Expected session:",
            source_session.session_id,
        )
        print(
            "Returned session:",
            found_session.session_id,
        )
        return False

    print("[PASSED] Valid token found the session.")
    print(
        "Session ID:",
        found_session.session_id,
    )
    print(
        "Candidate:",
        found_session.candidate_name,
    )
    print(
        "Job:",
        found_session.job_title,
    )
    print(
        "Mode:",
        found_session.interview_mode,
    )

    return True


def test_invalid_token() -> bool:
    """
    Confirm that an invalid token returns None.
    """
    invalid_token = (
        "this-is-not-a-valid-candidate-token"
    )

    found_session = find_session_by_candidate_token(
        invalid_token
    )

    print("\n--- Invalid token test ---")

    if found_session is not None:
        print(
            "[FAILED] An invalid token returned a "
            "session."
        )
        print(
            "Returned session:",
            found_session.session_id,
        )
        return False

    print("[PASSED] Invalid token returned None.")
    return True


def test_empty_token() -> bool:
    """
    Confirm that empty token values return None.
    """
    print("\n--- Empty token test ---")

    empty_values = [
        "",
        "   ",
    ]

    for token in empty_values:
        found_session = (
            find_session_by_candidate_token(
                token
            )
        )

        if found_session is not None:
            print(
                "[FAILED] An empty token returned a "
                "session."
            )
            return False

    print("[PASSED] Empty tokens returned None.")
    return True

def show_loaded_sessions() -> None:
    sessions = load_all_interview_sessions()

    print(f"\nLoaded sessions: {len(sessions)}")

    for session in sessions:
        print("-" * 50)
        print("Session ID:", session.session_id)
        print("Mode:", session.interview_mode)
        print(
            "Access enabled:",
            session.candidate_access_enabled,
        )
        print(
            "Has token:",
            bool(session.candidate_access_token),
        )
        print(
            "Token length:",
            len(session.candidate_access_token),
        )

        
def main() -> None:
    print("=" * 60)
    print("Candidate access token lookup test")
    print("=" * 60)

    show_loaded_sessions()

    results = [
        test_valid_token(),
        test_invalid_token(),
        test_empty_token(),
    ]

    passed_count = sum(results)
    total_count = len(results)

    print("\n" + "=" * 60)
    print(
        f"Result: {passed_count}/{total_count} "
        "tests passed"
    )
    print("=" * 60)

    if passed_count != total_count:
        sys.exit(1)

if __name__ == "__main__":

    main()