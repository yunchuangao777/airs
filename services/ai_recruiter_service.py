from __future__ import annotations

import json
import os
from typing import Any, Callable

from openai import OpenAI

from services.ai_recruiter_tools import (
    get_candidate_details,
    get_interview_summary,
    get_pipeline_summary,
    get_recruitment_overview,
    search_candidates,
    search_external_candidates,
    search_jobs,
)


DEFAULT_MODEL = os.getenv(
    "AI_RECRUITER_MODEL",
    "gpt-4o-mini",
)

MAX_TOOL_ROUNDS = 6


SYSTEM_INSTRUCTIONS = """
You are AIRS AI Recruiter, a read-only recruiting assistant.

Your job is to answer staff questions using only the AIRS tool data
provided to you. You may summarize, compare, and explain the retrieved
records, but you must not invent candidates, jobs, scores, statuses,
interviews, or evaluations.

Important rules:
1. Use tools whenever the answer depends on AIRS data.
2. Use search_candidates for existing AIRS records. Use
   search_external_candidates only when the recruiter explicitly asks
   to search public or external sources or discover new prospects.
3. Never claim that you changed AIRS data. This version is read-only.
4. Do not expose password hashes, authentication configuration,
   candidate access tokens, public interview links, raw CV text,
   full phone numbers, or private street addresses.
5. When the data is missing or ambiguous, say so clearly.
6. Clearly label web-search results as unverified external prospects,
   not AIRS candidates. Include source URLs when useful and never
   imply that AIRS verified a person's identity, experience, or skills.
7. When referring to an AIRS candidate, include the candidate name and,
   when useful, the candidate ID so the recruiter can identify the
   correct record.
8. Treat match scores and interview evaluations as decision support,
   not as the sole basis for employment decisions.
9. Keep answers readable. Use short headings and compact bullets when
   several records are returned.
10. Do not infer protected personal characteristics.
11. If a user asks you to perform an action, explain that this version
   can only analyze data and may propose a next step for confirmation.
""".strip()


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "get_recruitment_overview",
        "description": (
            "Return organization-wide counts for candidates, jobs, "
            "applications, pipeline statuses, interview sessions, "
            "completed interviews, and evaluations waiting for review."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "search_candidates",
        "description": (
            "Search AIRS candidate records by name, skills, minimum "
            "experience, education, job, application status, and "
            "minimum match score. Use this to find or shortlist "
            "candidates."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": ["string", "null"],
                    "description": (
                        "Partial candidate name. Use null when not needed."
                    ),
                },
                "skills": {
                    "type": ["array", "null"],
                    "items": {"type": "string"},
                    "description": (
                        "Skills that every returned candidate should have."
                    ),
                },
                "minimum_experience": {
                    "type": ["number", "null"],
                    "description": (
                        "Minimum total years of experience."
                    ),
                },
                "education": {
                    "type": ["string", "null"],
                    "description": (
                        "Education keyword such as MBA, Master, CPA, "
                        "Bachelor, or a major."
                    ),
                },
                "job_id": {
                    "type": ["string", "null"],
                    "description": (
                        "AIRS job ID when filtering by a specific job."
                    ),
                },
                "status": {
                    "type": ["string", "null"],
                    "description": (
                        "Application status such as applied, review, "
                        "interview, offer, accepted, rejected, or archived."
                    ),
                },
                "minimum_match_score": {
                    "type": ["number", "null"],
                    "description": (
                        "Minimum saved match score from 0 to 100."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "description": "Maximum number of candidates to return.",
                },
            },
            "required": [
                "name",
                "skills",
                "minimum_experience",
                "education",
                "job_id",
                "status",
                "minimum_match_score",
                "limit",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "search_external_candidates",
        "description": (
            "Search enabled external candidate sources such as Public "
            "Web and, when implemented, GitHub. Use this only when the "
            "recruiter explicitly asks to search externally, search "
            "public sources, discover new prospects, or look beyond "
            "the AIRS candidate database. Results are unverified "
            "external prospects and are never imported automatically."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query_text": {
                    "type": "string",
                    "description": (
                        "Concise external candidate-search query, "
                        "including role or professional focus."
                    ),
                },
                "source_ids": {
                    "type": ["array", "null"],
                    "items": {
                        "type": "string",
                        "enum": [
                            "public_web",
                            "github",
                        ],
                    },
                    "description": (
                        "External source IDs to search, or null to "
                        "use the default configured external sources."
                    ),
                },
                "location": {
                    "type": ["string", "null"],
                    "description": (
                        "Location keyword such as Toronto or Canada."
                    ),
                },
                "skills": {
                    "type": ["array", "null"],
                    "items": {"type": "string"},
                    "description": (
                        "Requested skills such as Python, FastAPI, "
                        "CPA, SAP, or Power BI."
                    ),
                },
                "minimum_experience": {
                    "type": ["number", "null"],
                    "description": (
                        "Requested minimum years of experience."
                    ),
                },
                "education": {
                    "type": ["string", "null"],
                    "description": (
                        "Optional education, certification, or major."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "description": (
                        "Maximum prospects to return per configured "
                        "source."
                    ),
                },
            },
            "required": [
                "query_text",
                "source_ids",
                "location",
                "skills",
                "minimum_experience",
                "education",
                "limit",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_candidate_details",
        "description": (
            "Return a compact candidate profile with applications, "
            "match results, strengths, concerns, and interview records. "
            "Use only after obtaining a candidate ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "candidate_id": {
                    "type": "string",
                    "description": "Exact AIRS candidate ID.",
                },
            },
            "required": ["candidate_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "search_jobs",
        "description": (
            "Search AIRS jobs by title, company, or required/preferred "
            "skill. Use this to resolve a job name into a job ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": ["string", "null"],
                    "description": "Partial job title.",
                },
                "company": {
                    "type": ["string", "null"],
                    "description": "Partial company name.",
                },
                "required_skill": {
                    "type": ["string", "null"],
                    "description": (
                        "Skill that appears in required or preferred skills."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "description": "Maximum number of jobs to return.",
                },
            },
            "required": [
                "title",
                "company",
                "required_skill",
                "limit",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_pipeline_summary",
        "description": (
            "Return application status counts for all jobs or one exact "
            "job ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": ["string", "null"],
                    "description": (
                        "Exact AIRS job ID, or null for all jobs."
                    ),
                },
            },
            "required": ["job_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_interview_summary",
        "description": (
            "Return interview session progress and evaluation summaries. "
            "Filter by candidate ID, job ID, or session ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "candidate_id": {
                    "type": ["string", "null"],
                    "description": "Exact AIRS candidate ID.",
                },
                "job_id": {
                    "type": ["string", "null"],
                    "description": "Exact AIRS job ID.",
                },
                "session_id": {
                    "type": ["string", "null"],
                    "description": "Exact AIRS interview session ID.",
                },
            },
            "required": [
                "candidate_id",
                "job_id",
                "session_id",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


TOOL_FUNCTIONS: dict[str, Callable[..., dict]] = {
    "get_recruitment_overview": get_recruitment_overview,
    "search_candidates": search_candidates,
    "search_external_candidates": (
        search_external_candidates
    ),
    "get_candidate_details": get_candidate_details,
    "search_jobs": search_jobs,
    "get_pipeline_summary": get_pipeline_summary,
    "get_interview_summary": get_interview_summary,
}


def _safe_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        default=str,
    )


def _parse_tool_arguments(
    arguments: str,
) -> dict[str, Any]:
    if not arguments:
        return {}

    parsed = json.loads(arguments)

    if not isinstance(parsed, dict):
        raise ValueError(
            "Tool arguments must be a JSON object."
        )

    return parsed


def execute_ai_recruiter_tool(
    tool_name: str,
    arguments: dict[str, Any],
) -> dict:
    """
    Execute one approved read-only AIRS tool.
    """
    tool_function = TOOL_FUNCTIONS.get(tool_name)

    if tool_function is None:
        return {
            "ok": False,
            "error": f"Unknown AI Recruiter tool: {tool_name}",
        }

    try:
        result = tool_function(**arguments)

        return {
            "ok": True,
            "tool": tool_name,
            "result": result,
        }

    except Exception as exc:
        return {
            "ok": False,
            "tool": tool_name,
            "error": str(exc),
        }


def ask_ai_recruiter(
    user_message: str,
    *,
    conversation_history: list[dict[str, str]] | None = None,
    model: str = DEFAULT_MODEL,
    client: OpenAI | None = None,
) -> dict:
    """
    Answer one recruiter question through the Responses API.

    conversation_history should contain compact dictionaries such as:
        {"role": "user", "content": "..."}
        {"role": "assistant", "content": "..."}
    """
    message = str(user_message or "").strip()

    if not message:
        raise ValueError(
            "The recruiter question cannot be empty."
        )

    openai_client = client or OpenAI()

    input_items: list[Any] = []

    for item in conversation_history or []:
        role = str(item.get("role") or "").strip()

        if role not in {"user", "assistant"}:
            continue

        content = str(item.get("content") or "").strip()

        if content:
            input_items.append(
                {
                    "role": role,
                    "content": content,
                }
            )

    input_items.append(
        {
            "role": "user",
            "content": message,
        }
    )

    tool_trace: list[dict[str, Any]] = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = openai_client.responses.create(
            model=model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=input_items,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        function_calls = [
            item
            for item in response.output
            if getattr(item, "type", "") == "function_call"
        ]

        if not function_calls:
            answer = str(
                response.output_text or ""
            ).strip()

            if not answer:
                answer = (
                    "I could not produce an answer from the "
                    "available AIRS data."
                )

            return {
                "answer": answer,
                "model": model,
                "tool_trace": tool_trace,
                "response_id": response.id,
            }

        # Preserve every model output item before appending tool results.
        input_items.extend(response.output)

        for function_call in function_calls:
            tool_name = str(
                getattr(function_call, "name", "")
                or ""
            )

            call_id = str(
                getattr(function_call, "call_id", "")
                or ""
            )

            raw_arguments = str(
                getattr(function_call, "arguments", "")
                or "{}"
            )

            try:
                arguments = _parse_tool_arguments(
                    raw_arguments
                )

                tool_result = execute_ai_recruiter_tool(
                    tool_name,
                    arguments,
                )

            except Exception as exc:
                arguments = {}
                tool_result = {
                    "ok": False,
                    "tool": tool_name,
                    "error": (
                        "Invalid tool arguments: "
                        f"{exc}"
                    ),
                }

            tool_trace.append(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "ok": bool(tool_result.get("ok")),
                }
            )

            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": _safe_json(tool_result),
                }
            )

    raise RuntimeError(
        "AI Recruiter exceeded the maximum number "
        "of tool-calling rounds."
    )