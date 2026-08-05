from __future__ import annotations

import uuid
from datetime import datetime

import streamlit as st

from cv_loader import load_single_cv
from cv_saver import save_candidate_json
from llm_extractor import extract_cv_info
from schema import CVInfo
from services.permission_service import (
    has_permission,
    require_permission,
)
from utils.file_helpers import save_uploaded_files


PENDING_LINKEDIN_CANDIDATE_KEY = (
    "pending_linkedin_pdf_candidate"
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


def _finish_candidate_creation(
    message: str,
) -> None:

    st.session_state[
        "show_create_candidate_dialog"
    ] = False
    
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
        PENDING_LINKEDIN_CANDIDATE_KEY,
        None,
    )


def _render_pending_linkedin_candidate(
    pending: dict,
) -> None:
    candidate_data = dict(
        pending.get("candidate") or {}
    )
    source_data = dict(
        pending.get("source") or {}
    )

    st.success(
        "The LinkedIn PDF was extracted. Review the "
        "candidate information before creating the "
        "AIRS candidate."
    )

    source_col1, source_col2 = st.columns(2)

    with source_col1:
        st.text_input(
            "Source file",
            value=str(
                source_data.get("filename") or ""
            ),
            disabled=True,
            key="linkedin_source_filename",
        )

    with source_col2:
        st.text_input(
            "Source type",
            value="LinkedIn PDF Export",
            disabled=True,
            key="linkedin_source_type",
        )

    source_text = str(
        source_data.get("text") or ""
    )

    with st.expander(
        "Preview extracted LinkedIn text",
        expanded=False,
    ):
        st.text_area(
            "Extracted text",
            value=source_text[:20_000],
            height=250,
            disabled=True,
            key="linkedin_text_preview",
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
        "linkedin_candidate_review_form",
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

        st.session_state[
            "show_create_candidate_dialog"
        ] = False

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
        source_filename = str(
            source_data.get("filename")
            or "linkedin_profile.pdf"
        )

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
                    f"LinkedIn PDF - {source_filename}"
                ),
                "source_filepath": (
                    str(
                        source_data.get("filepath")
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
            f"linkedin_{candidate.candidate_id}.pdf"
        )

        save_candidate_json(
            candidate,
            output_filename,
        )

        _clear_pending_import()

        _finish_candidate_creation(
            f"{candidate.name} was imported "
            "successfully from a LinkedIn PDF."
        )

    except Exception as exc:
        st.error(
            f"Unable to create candidate: {exc}"
        )


def render_linkedin_pdf_import() -> None:
    """
    Import a candidate from a PDF exported by the
    recruiter or candidate from LinkedIn.
    """
    st.caption(
        "Upload a LinkedIn profile PDF that the "
        "recruiter or candidate is authorized to use."
    )

    st.info(
        "This workflow does not scrape LinkedIn. "
        "It processes a PDF file that you upload."
    )

    pending = st.session_state.get(
        PENDING_LINKEDIN_CANDIDATE_KEY
    )

    if pending:
        _render_pending_linkedin_candidate(
            pending
        )
        return

    uploaded_file = st.file_uploader(
        "Upload LinkedIn profile PDF",
        type=["pdf"],
        accept_multiple_files=False,
        key="linkedin_profile_pdf_uploader",
    )

    authorized = st.checkbox(
        "I confirm that I am authorized to collect "
        "and use this candidate information.",
        key="linkedin_pdf_authorized",
    )

    extract_clicked = st.button(
        "Upload and Extract LinkedIn PDF",
        type="primary",
        use_container_width=True,
        key="linkedin_pdf_extract",
        disabled=(
            uploaded_file is None
            or not authorized
            or not has_permission(
                "candidate.create"
            )
        ),
    )

    if not extract_clicked:
        return

    require_permission(
        "candidate.create",
        message=(
            "You do not have permission to import "
            "candidate records."
        ),
    )

    with st.spinner(
        "Extracting candidate information from "
        "the LinkedIn PDF..."
    ):
        try:
            saved_paths = save_uploaded_files(
                [uploaded_file]
            )

            if not saved_paths:
                raise ValueError(
                    "The LinkedIn PDF could not be saved."
                )

            path = saved_paths[0]
            cv = load_single_cv(path)

            candidate = extract_cv_info(
                cv["text"]
            )

            if not candidate.candidate_id:
                candidate.candidate_id = str(
                    uuid.uuid4()
                )

            candidate.raw_text = cv["text"]
            candidate.source_filename = (
                f"LinkedIn PDF - {cv['filename']}"
            )
            candidate.source_filepath = cv.get(
                "filepath"
            )
            candidate.upload_time = (
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )

            st.session_state[
                PENDING_LINKEDIN_CANDIDATE_KEY
            ] = {
                "candidate": _model_dump(
                    candidate
                ),
                "source": {
                    "filename": cv["filename"],
                    "filepath": cv.get(
                        "filepath"
                    ),
                    "text": cv["text"],
                },
            }

            st.rerun()

        except Exception as exc:
            st.error(
                "Unable to import the LinkedIn PDF. "
                f"Details: {exc}"
            )