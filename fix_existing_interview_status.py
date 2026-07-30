from application_service import (
    update_application_status,
)
from schema import CandidateStatus


update_application_status(
    candidate_id="13996438",
    job_id="8fe7c852-fc41-4ab1-a45d-db522f9a9b41",
    new_status=CandidateStatus.INTERVIEW,
    note=(
        "Status synchronized from completed "
        "interview session."
    ),
)

print("Application status updated to interview.")