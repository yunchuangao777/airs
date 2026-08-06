from __future__ import annotations

import streamlit as st


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "page.ai_recruiter",
        "ai_recruiter.ask",
        "ai_recruiter.propose",
        "ai_recruiter.execute",
        # Pages
        "page.dashboard",
        "page.cv_management",
        "page.job_management",
        "page.job_matching",
        "page.hiring_management",
        "page.interview_prep",
        "page.interview_session",
        "page.user_management",

        # Candidate actions
        "candidate.view",
        "candidate.create",
        "candidate.edit",
        "candidate.delete",
        "candidate.export",
        "candidate.archive",

        # Job actions
        "job.view",
        "job.create",
        "job.edit",
        "job.delete",

        # Matching and hiring actions
        "matching.run",
        "matching.save",
        "application.update_status",

        # Interview actions
        "interview.view",
        "interview.create",
        "interview.conduct",
        "interview.evaluate",
        "interview.finalize",

        # Administration
        "user.manage",

        # Ecternal source
        "page.candidate_source_settings",
        "candidate_sources.manage",
    },

    "recruiter": {
        "page.ai_recruiter",
        "ai_recruiter.ask",
        "ai_recruiter.propose",
        "ai_recruiter.execute",
        # Pages
        "page.dashboard",
        "page.cv_management",
        "page.job_management",
        "page.job_matching",
        "page.hiring_management",
        "page.interview_prep",
        "page.interview_session",

        # Candidate actions
        "candidate.view",
        "candidate.create",
        "candidate.edit",
        "candidate.export",
        "candidate.archive",

        # Job actions
        "job.view",
        "job.create",
        "job.edit",

        # Matching and hiring actions
        "matching.run",
        "matching.save",
        "application.update_status",

        # Interview actions
        "interview.view",
        "interview.create",
        "interview.conduct",
        "interview.evaluate",
        "interview.finalize",
    },

    "interviewer": {
        "page.ai_recruiter",
        "ai_recruiter.ask",
        # Pages
        "page.dashboard",
        "page.cv_management",
        "page.job_management",
        "page.job_matching",
        "page.hiring_management",
        "page.interview_prep",
        "page.interview_session",

        # Read access
        "candidate.view",
        "job.view",
        "interview.view",

        # Interview work
        "interview.conduct",
        "interview.evaluate",
    },

    "viewer": {
        "page.ai_recruiter",
        "ai_recruiter.ask",
        # Pages
        "page.dashboard",
        "page.cv_management",
        "page.job_management",
        "page.job_matching",
        "page.hiring_management",
        "page.interview_prep",
        "page.interview_session",

        # Read-only access
        "candidate.view",
        "job.view",
        "interview.view",
    },
}


PAGE_PERMISSION_MAP: dict[str, str] = {
    "Dashboard": "page.dashboard",
    "CV Management": "page.cv_management",
    "Job Management": "page.job_management",
    "Job Matching": "page.job_matching",
    "Hiring Management": "page.hiring_management",
    "Interview Prep": "page.interview_prep",
    "Interview Session": "page.interview_session",
    "User Management": "page.user_management",
    "AI Recruiter": "page.ai_recruiter",
    "Candidate Source Settings": "page.candidate_source_settings",
}


def normalize_role(role: str | None) -> str:
    return str(role or "").strip().lower()


def get_current_role() -> str:
    return normalize_role(
        st.session_state.get(
            "current_user_role",
            "",
        )
    )


def has_permission(
    permission: str,
    role: str | None = None,
) -> bool:
    selected_role = normalize_role(
        role if role is not None else get_current_role()
    )

    return permission in ROLE_PERMISSIONS.get(
        selected_role,
        set(),
    )


def can_access_page(
    page_name: str,
    role: str | None = None,
) -> bool:
    required_permission = PAGE_PERMISSION_MAP.get(
        page_name
    )

    if required_permission is None:
        return False

    return has_permission(
        required_permission,
        role=role,
    )


def get_allowed_pages(
    role: str | None = None,
) -> list[str]:
    return [
        page_name
        for page_name in PAGE_PERMISSION_MAP
        if can_access_page(
            page_name,
            role=role,
        )
    ]


def require_permission(
    permission: str,
    *,
    message: str = (
        "You do not have permission to perform "
        "this action."
    ),
    stop: bool = True,
) -> bool:
    if has_permission(permission):
        return True

    st.error(message)

    if stop:
        st.stop()

    return False