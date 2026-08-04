from __future__ import annotations

import hashlib
import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient

from services.candidate_discovery.models import (
    CandidateDiscoveryQuery,
    CandidateDiscoveryResult,
)


load_dotenv()

SOURCE_ID = "public_web"
SOURCE_TYPE = "tavily"


def _clean_text(value: object) -> str:
    return " ".join(
        str(value or "").split()
    ).strip()


def _build_search_query(
    query: CandidateDiscoveryQuery,
) -> str:
    parts: list[str] = []

    if query.query_text.strip():
        parts.append(
            query.query_text.strip()
        )

    if query.name:
        parts.append(
            f'"{query.name.strip()}"'
        )

    if query.skills:
        skill_text = " ".join(
            f'"{skill.strip()}"'
            for skill in query.skills
            if skill.strip()
        )

        if skill_text:
            parts.append(skill_text)

    if query.location:
        parts.append(
            f'"{query.location.strip()}"'
        )

    if query.minimum_experience is not None:
        parts.append(
            f'"{query.minimum_experience:g}+ years experience"'
        )

    if query.education:
        parts.append(
            f'"{query.education.strip()}"'
        )

    parts.append(
        "(resume OR CV OR portfolio OR "
        "\"personal website\" OR "
        "\"professional profile\")"
    )

    # Tavily recommends concise queries. Keep enough room
    # below its documented 400-character best-practice limit.
    return " ".join(parts)[:380]


def _extract_matching_skills(
    text: str,
    requested_skills: list[str],
) -> list[str]:
    normalized_text = text.lower()

    return [
        skill
        for skill in requested_skills
        if skill.strip()
        and skill.strip().lower()
        in normalized_text
    ]


def _guess_name_from_title(
    title: str,
) -> str | None:
    cleaned = _clean_text(title)

    if not cleaned:
        return None

    separators = [
        " | ",
        " - ",
        " — ",
        " – ",
        " :: ",
    ]

    first_part = cleaned

    for separator in separators:
        if separator in first_part:
            first_part = first_part.split(
                separator,
                1,
            )[0].strip()

    generic_titles = {
        "resume",
        "cv",
        "portfolio",
        "home",
        "about",
        "professional profile",
    }

    if first_part.lower() in generic_titles:
        return None

    # Avoid pretending an entire sentence is a person's name.
    if len(first_part.split()) > 6:
        return None

    return first_part or None


def _stable_external_id(
    url: str,
) -> str:
    return hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:20]


def _is_http_url(
    url: str,
) -> bool:
    parsed = urlparse(url)

    return parsed.scheme in {
        "http",
        "https",
    } and bool(parsed.netloc)


def search_public_web_candidates(
    query: CandidateDiscoveryQuery,
    *,
    source_config: dict,
    api_key: str | None = None,
    client: TavilyClient | None = None,
) -> list[CandidateDiscoveryResult]:
    """
    Search public web results for candidate-like pages.

    This function returns prospects only. It does not
    download, import, or create AIRS candidates.
    """
    resolved_api_key = (
        api_key
        or os.getenv("TAVILY_API_KEY")
    )

    if client is None and not resolved_api_key:
        raise ValueError(
            "TAVILY_API_KEY is not configured."
        )

    tavily_client = (
        client
        or TavilyClient(
            api_key=resolved_api_key
        )
    )

    maximum_results = (
        query.normalized_limit()
    )

    excluded_domains = [
        str(domain).strip()
        for domain in (
            source_config.get(
                "excluded_domains"
            )
            or []
        )
        if str(domain).strip()
    ]

    search_query = _build_search_query(
        query
    )

    response = tavily_client.search(
        query=search_query,
        topic="general",
        search_depth="basic",
        max_results=maximum_results,
        include_answer=False,
        include_raw_content=False,
        exclude_domains=excluded_domains,
    )

    raw_results = response.get(
        "results",
        [],
    )

    results: list[
        CandidateDiscoveryResult
    ] = []

    for item in raw_results:
        url = _clean_text(
            item.get("url")
        )

        if not _is_http_url(url):
            continue

        title = _clean_text(
            item.get("title")
        )
        content = _clean_text(
            item.get("content")
        )

        combined_text = (
            f"{title}\n{content}"
        ).strip()

        matched_skills = (
            _extract_matching_skills(
                combined_text,
                query.skills,
            )
        )

        evidence: list[str] = []

        if content:
            evidence.append(
                content[:500]
            )

        if matched_skills:
            evidence.append(
                "Requested skills mentioned: "
                + ", ".join(
                    matched_skills
                )
            )

        score_value = item.get(
            "score"
        )

        try:
            confidence = float(
                score_value
            )
        except (
            TypeError,
            ValueError,
        ):
            confidence = None

        results.append(
            CandidateDiscoveryResult(
                source_id=SOURCE_ID,
                source_type=SOURCE_TYPE,
                external_id=(
                    _stable_external_id(
                        url
                    )
                ),
                candidate_id=None,
                name=_guess_name_from_title(
                    title
                ),
                title=title or None,
                location=(
                    query.location.strip()
                    if query.location
                    else None
                ),
                skills=matched_skills,
                summary=content or None,
                profile_url=url,
                evidence=evidence,
                confidence=confidence,
                import_supported=True,
                already_in_airs=False,
                metadata={
                    "search_query": (
                        search_query
                    ),
                    "domain": (
                        urlparse(
                            url
                        ).netloc.lower()
                    ),
                    "tavily_score": (
                        confidence
                    ),
                    "result_title": title,
                    "result_snippet": content,
                },
            )
        )

    return results