import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from cv_loader import load_single_cv
from cv_saver import save_candidate_json
from llm_extractor import extract_cv_info
from schema import CVInfo
from utils.file_helpers import save_uploaded_files


def text_to_list(value: str) -> list[str]:
    """
    Convert one-item-per-line or comma-separated text
    into a clean list.
    """
    if not value:
        return []

    normalized = value.replace(",", "\n")

    return [
        line.strip().lstrip("-•").strip()
        for line in normalized.splitlines()
        if line.strip().lstrip("-•").strip()
    ]


def optional_float(value: float) -> float | None:
    """
    Treat zero as an unspecified value.
    """
    return value if value > 0 else None


def refresh_candidate_library() -> None:
    """
    Change the candidate-table key so new candidates
    appear with a fresh table state.
    """
    st.session_state["candidate_table_version"] = (
        st.session_state.get(
            "candidate_table_version",
            0,
        )
        + 1
    )


def finish_candidate_creation(message: str) -> None:
    """
    Store a success message and refresh the application.
    """
    refresh_candidate_library()

    st.session_state["candidate_created_message"] = (
        message
    )

    st.rerun()


def render_upload_candidate() -> None:
    """
    Existing CV upload and AI extraction workflow.
    """
    uploaded_files = st.file_uploader(
        "Select CV files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="create_candidate_uploader",
    )

    if not uploaded_files:
        st.caption(
            "Upload one or more PDF, DOCX, or TXT files."
        )
        return

    st.write(
        f"{len(uploaded_files)} file(s) selected."
    )

    if not st.button(
        "Upload and Extract",
        type="primary",
        use_container_width=True,
        key="create_candidate_upload_submit",
    ):
        return

    saved_paths = save_uploaded_files(
        uploaded_files
    )

    rows: list[dict] = []

    progress_bar = st.progress(0)
    status_box = st.empty()

    for index, path in enumerate(saved_paths):
        status_box.info(
            f"Processing: {path.name}"
        )

        try:
            cv = load_single_cv(path)

            candidate = extract_cv_info(
                cv["text"]
            )

            candidate.raw_text = cv["text"]
            candidate.source_filename = cv["filename"]
            candidate.source_filepath = cv.get(
                "filepath"
            )

            save_candidate_json(
                candidate,
                cv["filename"],
            )

            rows.append(
                {
                    "Filename": cv["filename"],
                    "Candidate ID": (
                        candidate.candidate_id
                    ),
                    "Name": candidate.name,
                    "Email": candidate.email,
                    "Status": "Success",
                }
            )

        except Exception as exc:
            rows.append(
                {
                    "Filename": path.name,
                    "Candidate ID": "",
                    "Name": "",
                    "Email": "",
                    "Status": f"Failed: {exc}",
                }
            )

        progress_bar.progress(
            (index + 1) / len(saved_paths)
        )

    status_box.empty()

    result_df = pd.DataFrame(rows)

    st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True,
    )

    success_count = sum(
        row["Status"] == "Success"
        for row in rows
    )

    if success_count:
        finish_candidate_creation(
            f"{success_count} candidate(s) "
            "created successfully."
        )


def render_manual_candidate() -> None:
    """
    Traditional candidate-entry workflow.

    This does not call the OpenAI API.
    """
    st.caption(
        "Enter candidate information manually. "
        "Skills should be separated by commas "
        "or entered one per line."
    )

    with st.form(
        "manual_candidate_form",
        clear_on_submit=False,
    ):
        st.markdown("#### Basic Information")

        basic_col1, basic_col2 = st.columns(2)

        with basic_col1:
            name = st.text_input(
                "Candidate name *",
            )

            email = st.text_input(
                "Email",
            )

            phone = st.text_input(
                "Phone",
            )

        with basic_col2:
            location = st.text_input(
                "Location",
            )

            total_years_experience = (
                st.number_input(
                    "Total years of experience",
                    min_value=0.0,
                    value=0.0,
                    step=0.5,
                )
            )

        summary = st.text_area(
            "Professional summary",
            height=120,
        )

        skills_text = st.text_area(
            "Skills",
            placeholder=(
                "Python\n"
                "SQL\n"
                "Power BI"
            ),
            height=130,
        )

        st.markdown("#### Education")

        education_col1, education_col2 = (
            st.columns(2)
        )

        with education_col1:
            school = st.text_input(
                "School or institution",
            )

            degree = st.text_input(
                "Degree",
                placeholder="Bachelor, Master, MBA...",
            )

        with education_col2:
            major = st.text_input(
                "Major",
            )

            graduation_year = st.text_input(
                "Graduation year",
            )

        st.markdown("#### Most Recent Work Experience")

        work_col1, work_col2 = st.columns(2)

        with work_col1:
            company = st.text_input(
                "Company",
            )

            job_title = st.text_input(
                "Position title",
            )

        with work_col2:
            start_date = st.text_input(
                "Start date",
                placeholder="2020-01",
            )

            end_date = st.text_input(
                "End date",
                placeholder="2024-06 or Present",
            )

        work_description = st.text_area(
            "Work description",
            height=120,
        )

        submitted = st.form_submit_button(
            "Create Candidate",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    if not name.strip():
        st.warning("Candidate name is required.")
        return

    education = []

    if any(
        [
            school.strip(),
            degree.strip(),
            major.strip(),
            graduation_year.strip(),
        ]
    ):
        education.append(
            {
                "school": school.strip() or None,
                "degree": degree.strip() or None,
                "major": major.strip() or None,
                "graduation_year": (
                    graduation_year.strip()
                    or None
                ),
            }
        )

    work_experience = []

    if any(
        [
            company.strip(),
            job_title.strip(),
            start_date.strip(),
            end_date.strip(),
            work_description.strip(),
        ]
    ):
        work_experience.append(
            {
                "company": company.strip() or None,
                "title": job_title.strip() or None,
                "start_date": (
                    start_date.strip() or None
                ),
                "end_date": (
                    end_date.strip() or None
                ),
                "description": (
                    work_description.strip()
                    or None
                ),
            }
        )

    try:
        candidate = CVInfo(
            candidate_id=str(uuid.uuid4()),
            name=name.strip(),
            email=email.strip() or None,
            phone=phone.strip() or None,
            location=location.strip() or None,
            summary=summary.strip() or None,
            skills=text_to_list(skills_text),
            education=education,
            work_experience=work_experience,
            total_years_experience=optional_float(
                total_years_experience
            ),
            raw_text=None,
            source_filename=None,
            source_filepath=None,
            upload_time=datetime.now().isoformat(
                timespec="seconds"
            ),
        )

        # The second argument is retained because your current
        # save_candidate_json() function expects a source name.
        manual_source_name = (
            f"manual_{candidate.candidate_id}.txt"
        )

        save_candidate_json(
            candidate,
            manual_source_name,
        )

        finish_candidate_creation(
            f"{candidate.name} was created successfully."
        )

    except Exception as exc:
        st.error(
            f"Unable to create candidate: {exc}"
        )


@st.dialog(
    "Create New Candidate",
    width="large",
)
def show_create_candidate_dialog() -> None:
    upload_tab, manual_tab = st.tabs(
        [
            "Upload CV",
            "Fill in Fields",
        ]
    )

    with upload_tab:
        render_upload_candidate()

    with manual_tab:
        render_manual_candidate()