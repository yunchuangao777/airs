from __future__ import annotations

import uuid
from datetime import datetime

import streamlit as st

from cv_saver import save_candidate_json
from llm_extractor import extract_cv_info
from schema import CVInfo
from services.external_candidate_import_service import (
    extract_candidate_source_from_url,
)
from services.permission_service import (
    has_permission,
    require_permission,
)


PENDING_URL_CANDIDATE_KEY = (
    "pending_external_candidate_import"
)


def _text_to_list(value: str) -> list[str]:
    if not value:
        return []

    normalized = value.replace(",", "\n")

    return [
        line.strip().lstrip("-•").strip()
        for line in normalized.splitlines()
        if line.strip().lstrip("-•").strip()
    ]


def _optional_float(
    value: float,
) -> float | None:
    return value if value > 0 else None


def _model_dump(
    candidate: CVInfo,
) -> dict:
    if hasattr(candidate, "model_dump"):
        return candidate.model_dump()

    return candidate.dict()


def _format_size(
    downloaded_bytes: int,
) -> str:
    if downloaded_bytes >= 1024 * 1024:
        return (
            f"{downloaded_bytes / (1024 * 1024):.2f} MB"
        )

    if downloaded_bytes >= 1024:
        return f"{downloaded_bytes / 1024:.1f} KB"

    return f"{downloaded_bytes} bytes"


def _finish_candidate_creation(
    message: str,
) -> None:
    st.session_state["candidate_table_version"] = (
        st.session_state.get(
            "candidate_table_version",
            0,
        )
        + 1
    )

    st.session_state["candidate_created_message"] = (
        message
    )

    st.rerun()


def _clear_pending_import() -> None:
    st.session_state.pop(
        PENDING_URL_CANDIDATE_KEY,
        None,
    )


def _render_pending_candidate(
    pending: dict,
) -> None:
    candidate_data = dict(
        pending.get("candidate") or {}
    )
    source_data = dict(
        pending.get("source") or {}
    )

    st.success(
        "The source was loaded and candidate "
        "information was extracted. Review the fields "
        "before creating the AIRS candidate."
    )

    source_col1, source_col2 = st.columns(2)

    with source_col1:
        st.text_input(
            "Source title",
            value=str(
                source_data.get("title") or ""
            ),
            disabled=True,
            key="url_import_source_title",
        )

        st.text_input(
            "Source type",
            value=str(
                source_data.get("source_type") or ""
            ).upper(),
            disabled=True,
            key="url_import_source_type",
        )

    with source_col2:
        st.text_input(
            "Downloaded size",
            value=_format_size(
                int(
                    source_data.get(
                        "downloaded_bytes",
                        0,
                    )
                    or 0
                )
            ),
            disabled=True,
            key="url_import_source_size",
        )

        st.text_input(
            "Final URL",
            value=str(
                source_data.get("final_url") or ""
            ),
            disabled=True,
            key="url_import_final_url",
        )

    source_text = str(
        source_data.get("text") or ""
    )

    with st.expander(
        "Preview extracted source text",
        expanded=False,
    ):
        st.text_area(
            "Extracted text",
            value=source_text[:20_000],
            height=250,
            disabled=True,
            key="url_import_text_preview",
        )

        if len(source_text) > 20_000:
            st.caption(
                "The preview shows the first 20,000 "
                "characters. The full extracted text "
                "will be stored."
            )

    initial_skills = "\n".join(
        str(skill)
        for skill in (
            candidate_data.get("skills")
            or []
        )
        if str(skill).strip()
    )

    st.markdown("#### Review Candidate Information")

    with st.form(
        "external_candidate_review_form",
        clear_on_submit=False,
    ):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Candidate name *",
                value=str(
                    candidate_data.get("name") or ""
                ),
            )

            email = st.text_input(
                "Email",
                value=str(
                    candidate_data.get("email") or ""
                ),
            )

            phone = st.text_input(
                "Phone",
                value=str(
                    candidate_data.get("phone") or ""
                ),
            )

        with col2:
            location = st.text_input(
                "Location",
                value=str(
                    candidate_data.get("location") or ""
                ),
            )

            total_years_experience = st.number_input(
                "Total years of experience",
                min_value=0.0,
                value=float(
                    candidate_data.get(
                        "total_years_experience"
                    )
                    or 0.0
                ),
                step=0.5,
            )

        summary = st.text_area(
            "Professional summary",
            value=str(
                candidate_data.get("summary") or ""
            ),
            height=130,
        )

        skills_text = st.text_area(
            "Skills",
            value=initial_skills,
            height=150,
            help=(
                "Enter one skill per line or separate "
                "skills with commas."
            ),
        )

        with st.expander(
            "Extracted education and work history",
            expanded=False,
        ):
            st.markdown("**Education**")
            st.json(
                candidate_data.get("education")
                or []
            )

            st.markdown("**Work experience**")
            st.json(
                candidate_data.get(
                    "work_experience"
                )
                or []
            )

        save_col, cancel_col = st.columns(2)

        with save_col:
            save_clicked = st.form_submit_button(
                "Create Candidate",
                type="primary",
                use_container_width=True,
            )

        with cancel_col:
            cancel_clicked = st.form_submit_button(
                "Cancel Import",
                use_container_width=True,
            )

    if cancel_clicked:
        _clear_pending_import()
        st.rerun()

    if not save_clicked:
        return

    require_permission(
        "candidate.create",
        message=(
            "You do not have permission to create "
            "candidate records."
        ),
    )

    if not name.strip():
        st.warning(
            "Candidate name is required."
        )
        return

    try:
        candidate_data.update(
            {
                "candidate_id": (
                    candidate_data.get("candidate_id")
                    or str(uuid.uuid4())
                ),
                "name": name.strip(),
                "email": email.strip() or None,
                "phone": phone.strip() or None,
                "location": location.strip() or None,
                "summary": summary.strip() or None,
                "skills": _text_to_list(
                    skills_text
                ),
                "total_years_experience": (
                    _optional_float(
                        total_years_experience
                    )
                ),
                "raw_text": source_text,
                "source_filename": (
                    str(
                        source_data.get("title")
                        or "External candidate source"
                    )
                ),
                "source_filepath": (
                    str(
                        source_data.get("final_url")
                        or source_data.get(
                            "source_url"
                        )
                        or ""
                    )
                    or None
                ),
                "upload_time": datetime.now().isoformat(
                    timespec="seconds"
                ),
            }
        )

        candidate = CVInfo(
            **candidate_data
        )

        output_filename = (
            f"external_{candidate.candidate_id}.txt"
        )

        save_candidate_json(
            candidate,
            output_filename,
        )

        _clear_pending_import()

        _finish_candidate_creation(
            f"{candidate.name} was imported "
            "successfully from the external URL."
        )

    except Exception as exc:
        st.error(
            f"Unable to create candidate: {exc}"
        )


def render_url_candidate_import() -> None:
    """
    Import a candidate from a public HTML page,
    direct PDF URL, or direct text-file URL.
    """
    st.caption(
        "Import candidate information from a public "
        "portfolio, personal profile, CV page, direct "
        "PDF link, or direct text-file link."
    )

    st.warning(
        "Do not enter LinkedIn profile URLs or pages "
        "that require login. Use only information you "
        "are authorized to collect and process."
    )

    pending = st.session_state.get(
        PENDING_URL_CANDIDATE_KEY
    )

    if pending:
        _render_pending_candidate(
            pending
        )
        return

    source_url = st.text_input(
        "Public candidate URL",
        placeholder=(
            "https://example.com/jane-smith-resume.pdf"
        ),
        key="external_candidate_url",
    )

    authorized = st.checkbox(
        "I confirm that I am authorized to collect "
        "and use this candidate information.",
        key="external_candidate_authorized",
    )

    load_clicked = st.button(
        "Load and Extract",
        type="primary",
        use_container_width=True,
        key="external_candidate_load",
        disabled=(
            not source_url.strip()
            or not authorized
            or not has_permission(
                "candidate.create"
            )
        ),
    )

    if not load_clicked:
        return

    require_permission(
        "candidate.create",
        message=(
            "You do not have permission to import "
            "candidate records."
        ),
    )

    with st.spinner(
        "Downloading the source and extracting "
        "candidate information..."
    ):
        try:
            source = (
                extract_candidate_source_from_url(
                    source_url
                )
            )

            candidate = extract_cv_info(
                source.text
            )

            if not candidate.candidate_id:
                candidate.candidate_id = str(
                    uuid.uuid4()
                )

            candidate.raw_text = source.text
            candidate.source_filename = (
                source.title
                or "External candidate source"
            )
            candidate.source_filepath = (
                source.final_url
            )
            candidate.upload_time = (
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )

            st.session_state[
                PENDING_URL_CANDIDATE_KEY
            ] = {
                "candidate": _model_dump(
                    candidate
                ),
                "source": {
                    "source_url": source.source_url,
                    "final_url": source.final_url,
                    "source_type": source.source_type,
                    "title": source.title,
                    "content_type": (
                        source.content_type
                    ),
                    "text": source.text,
                    "downloaded_bytes": (
                        source.downloaded_bytes
                    ),
                },
            }

            st.rerun()

        except Exception as exc:
            st.error(
                "Unable to import this URL. "
                f"Details: {exc}"
            )