from __future__ import annotations

from pprint import pprint

from services.ai_recruiter_tools import (
    get_candidate_details,
    get_interview_summary,
    get_pipeline_summary,
    get_recruitment_overview,
    search_candidates,
    search_jobs,
)


def main() -> None:
    print("=" * 60)
    print("AIRS AI Recruiter Tool Test")
    print("=" * 60)

    overview = get_recruitment_overview()
    print("\nOverview")
    pprint(overview)

    assert "candidate_count" in overview
    assert "job_count" in overview

    jobs = search_jobs(limit=5)
    print("\nJobs")
    pprint(jobs)

    assert "jobs" in jobs

    candidates = search_candidates(
        minimum_experience=5,
        limit=5,
    )
    print("\nCandidates with at least 5 years experience")
    pprint(candidates)

    assert "candidates" in candidates

    pipeline = get_pipeline_summary()
    print("\nPipeline")
    pprint(pipeline)

    interviews = get_interview_summary()
    print("\nInterviews")
    pprint(interviews)

    if candidates["candidates"]:
        candidate_id = candidates["candidates"][0]["candidate_id"]

        if candidate_id:
            details = get_candidate_details(candidate_id)
            print("\nCandidate details")
            pprint(details)
            assert details["found"] is True

    print("\n[PASSED] AI Recruiter tools are working.")


if __name__ == "__main__":
    main()