from __future__ import annotations

from services.candidate_source_config_service import (
    get_enabled_candidate_sources,
    load_candidate_source_config,
)
from services.candidate_discovery.internal_source import (
    search_internal_candidates,
)
from services.candidate_discovery.public_web_source import (
    search_public_web_candidates,
)
from services.candidate_discovery.models import (
    CandidateDiscoveryQuery,
    CandidateDiscoveryResponse,
    CandidateDiscoveryResult,
)


def discover_candidates(
    query: CandidateDiscoveryQuery,
    *,
    source_ids: list[str] | None = None,
) -> CandidateDiscoveryResponse:
    """
    Search all enabled candidate sources.

    At this stage only the Internal AIRS adapter is
    implemented. Public Web and GitHub are registered
    by configuration but skipped until their adapters
    are added.
    """
    config = load_candidate_source_config()

    enabled_sources = (
        get_enabled_candidate_sources()
    )

    enabled_source_ids = [
        source["source_id"]
        for source in enabled_sources
    ]

    requested_source_ids = (
        [
            str(source_id).strip().lower()
            for source_id in source_ids
            if str(source_id).strip()
        ]
        if source_ids
        else enabled_source_ids
    )

    settings_limit = int(
        config["settings"].get(
            "maximum_results_per_source",
            10,
        )
    )

    effective_query = (
        CandidateDiscoveryQuery(
            query_text=query.query_text,
            name=query.name,
            location=query.location,
            skills=list(query.skills),
            minimum_experience=(
                query.minimum_experience
            ),
            education=query.education,
            job_id=query.job_id,
            status=query.status,
            minimum_match_score=(
                query.minimum_match_score
            ),
            limit=min(
                query.normalized_limit(),
                settings_limit,
            ),
        )
    )

    results: list[
        CandidateDiscoveryResult
    ] = []

    source_errors: dict[str, str] = {}

    for source_id in requested_source_ids:
        if source_id not in enabled_source_ids:
            source_errors[source_id] = (
                "The source is disabled or not configured."
            )
            continue

        try:
            if source_id == "internal_airs":
                results.extend(
                    search_internal_candidates(
                        effective_query
                    )
                )

            elif source_id == "public_web":
                source_config = config[
                    "sources"
                ][source_id]

                results.extend(
                    search_public_web_candidates(
                        effective_query,
                        source_config=source_config,
                    )
                )

            elif source_id == "github":
                source_errors[source_id] = (
                    "This source is configured but its "
                    "search adapter has not been "
                    "implemented yet."
                )

            else:
                source_errors[source_id] = (
                    "No discovery adapter is registered "
                    "for this source."
                )

        except Exception as exc:
            source_errors[source_id] = str(exc)

    return CandidateDiscoveryResponse(
        query=effective_query,
        enabled_source_ids=enabled_source_ids,
        results=results,
        source_errors=source_errors,
    )