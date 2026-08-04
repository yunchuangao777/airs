from services.permission_service import (
    can_access_page,
    get_allowed_pages,
    has_permission,
)


def main() -> None:
    assert can_access_page(
        "Dashboard",
        role="viewer",
    )

    assert not can_access_page(
        "User Management",
        role="viewer",
    )

    assert has_permission(
        "candidate.create",
        role="recruiter",
    )

    assert not has_permission(
        "candidate.create",
        role="viewer",
    )

    assert has_permission(
        "user.manage",
        role="admin",
    )

    assert can_access_page(
        "Candidate Source Settings",
        role="admin",
    )

    assert not can_access_page(
        "Candidate Source Settings",
        role="recruiter",
    )

    assert not can_access_page(
        "Candidate Source Settings",
        role="interviewer",
    )

    assert not can_access_page(
        "Candidate Source Settings",
        role="viewer",
    )

    assert has_permission(
        "candidate_sources.manage",
        role="admin",
    )

    assert not has_permission(
        "candidate_sources.manage",
        role="recruiter",
    )

    assert not has_permission(
        "candidate_sources.manage",
        role="viewer",
    )

    print("Admin pages:")
    print(get_allowed_pages("admin"))

    print("\nRecruiter pages:")
    print(get_allowed_pages("recruiter"))

    print("\nInterviewer pages:")
    print(get_allowed_pages("interviewer"))

    print("\nViewer pages:")
    print(get_allowed_pages("viewer"))

    print(
        "\n[PASSED] Permission service tests passed."
    )


if __name__ == "__main__":
    main()