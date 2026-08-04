from __future__ import annotations

from pprint import pprint

from services.dashboard_service import (
    build_dashboard_data,
)


def main() -> None:
    dashboard = build_dashboard_data()

    print("=" * 60)
    print("AIRS Dashboard Service Test")
    print("=" * 60)

    print("\nSummary")
    pprint(dashboard["summary"])

    print("\nApplication Status")
    pprint(dashboard["application_status"])

    print("\nEducation")
    pprint(dashboard["education"])

    print("\nApplications by Job")
    pprint(dashboard["applications_by_job"])

    print("\nInterview Status")
    pprint(dashboard["interview_status"])

    print("\nRecommendations")
    pprint(dashboard["recommendations"])

    required_sections = {
        "summary",
        "application_status",
        "education",
        "applications_by_job",
        "interview_status",
        "recommendations",
    }

    missing_sections = (
        required_sections
        - set(dashboard.keys())
    )

    if missing_sections:
        raise AssertionError(
            "Missing dashboard sections: "
            f"{sorted(missing_sections)}"
        )

    print("\n[PASSED] Dashboard data was built.")


if __name__ == "__main__":
    main()