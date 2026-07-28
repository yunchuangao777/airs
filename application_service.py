import uuid
from datetime import datetime

from application_loader import load_application
from application_saver import save_application
from schema import (
    ApplicationRecord,
    CandidateStatus,
    StatusHistoryItem,
)


def current_time() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_or_create_application(
    candidate_id: str,
    job_id: str,
) -> ApplicationRecord:
    existing = load_application(
        candidate_id=candidate_id,
        job_id=job_id,
    )

    if existing:
        existing.pop("_source_path", None)
        return ApplicationRecord.model_validate(existing)

    now = current_time()

    application = ApplicationRecord(
        application_id=str(uuid.uuid4()),
        candidate_id=candidate_id,
        job_id=job_id,
        status=CandidateStatus.NONE,
        created_time=now,
        updated_time=now,
        status_history=[
            StatusHistoryItem(
                status=CandidateStatus.NONE,
                changed_time=now,
                note="Application record created",
            )
        ],
    )

    save_application(application)

    return application

def update_application_status(
    candidate_id: str,
    job_id: str,
    new_status: CandidateStatus,
    note: str | None = None,
) -> ApplicationRecord:
    application = get_or_create_application(
        candidate_id=candidate_id,
        job_id=job_id,
    )

    now = current_time()

    if application.status != new_status:
        application.status = new_status
        application.updated_time = now

        application.status_history.append(
            StatusHistoryItem(
                status=new_status,
                changed_time=now,
                note=note.strip() if note else None,
            )
        )

        save_application(application)

    return application

def add_candidate_as_applied_if_available(
    candidate_id: str,
    job_id: str,
    note: str | None = None,
) -> tuple[ApplicationRecord | None, bool, str]:
    """
    Add a candidate to a job with status APPLIED only when:

    - no application exists; or
    - the existing application status is NONE.

    Existing non-NONE statuses are preserved.

    Returns:
        application
        was_added
        message
    """

    existing_data = load_application(
        candidate_id=candidate_id,
        job_id=job_id,
    )

    now = current_time()

    if existing_data:
        existing_data.pop("_source_path", None)

        application = ApplicationRecord.model_validate(
            existing_data
        )

        if application.status != CandidateStatus.NONE:
            return (
                application,
                False,
                (
                    "Candidate was not added because the existing "
                    f"status is '{application.status.value}'."
                ),
            )

        application.status = CandidateStatus.APPLIED
        application.updated_time = now

        application.status_history.append(
            StatusHistoryItem(
                status=CandidateStatus.APPLIED,
                changed_time=now,
                note=note or "Added from Job Matching",
            )
        )

        save_application(application)

        return (
            application,
            True,
            "Candidate status was changed from none to applied.",
        )

    application = ApplicationRecord(
        application_id=str(uuid.uuid4()),
        candidate_id=candidate_id,
        job_id=job_id,
        status=CandidateStatus.APPLIED,
        created_time=now,
        updated_time=now,
        notes=note,
        status_history=[
            StatusHistoryItem(
                status=CandidateStatus.APPLIED,
                changed_time=now,
                note=note or "Added from Job Matching",
            )
        ],
    )

    save_application(application)

    return (
        application,
        True,
        "Candidate was added with applied status.",
    )
