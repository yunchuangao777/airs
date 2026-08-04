from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CandidateDiscoveryQuery:
    query_text: str = ""
    name: str | None = None
    location: str | None = None
    skills: list[str] = field(default_factory=list)
    minimum_experience: float | None = None
    education: str | None = None
    job_id: str | None = None
    status: str | None = None
    minimum_match_score: float | None = None
    limit: int = 10

    def normalized_limit(self) -> int:
        return max(1, min(int(self.limit or 10), 50))


@dataclass
class CandidateDiscoveryResult:
    source_id: str
    source_type: str
    external_id: str | None
    candidate_id: str | None
    name: str | None
    title: str | None
    location: str | None
    skills: list[str]
    summary: str | None
    profile_url: str | None
    evidence: list[str]
    confidence: float | None
    import_supported: bool
    already_in_airs: bool
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CandidateDiscoveryResponse:
    query: CandidateDiscoveryQuery
    enabled_source_ids: list[str]
    results: list[CandidateDiscoveryResult]
    source_errors: dict[str, str] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict:
        return {
            "query": asdict(self.query),
            "enabled_source_ids": list(
                self.enabled_source_ids
            ),
            "results": [
                result.to_dict()
                for result in self.results
            ],
            "source_errors": dict(
                self.source_errors
            ),
            "count": len(self.results),
        }