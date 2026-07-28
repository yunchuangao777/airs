import uuid
from datetime import datetime

import streamlit as st

from job_extractor import extract_job_info
from job_loader import load_job_file
from job_saver import save_job_json
from schema import JobInfo
from utils.paths import UPLOAD_DIR


def refresh_job_table():
    st.session_state["job_table_version"] = (
        st.session_state.get("job_table_version", 0) + 1
    )


def text_to_list(value: str) -> list[str]:
    if not value:
        return []

    results = []

    for line in value.splitlines():
        cleaned = line.strip().lstrip("-•").strip()

        if cleaned:
            results.append(cleaned)

    return results


@st.dialog("Create New Job", width="large")
def show_create_job_dialog():
    input_method = st.radio(
        "Input method",
        [
            "AI Generate",
            "Upload file",
            "Manual Fill",
        ],
        horizontal=True,
        key="create_job_input_method",
    )

    # =========================================================
    # Method 1: AI Generate
    # =========================================================
    if input_method == "AI Generate":
        job_text = st.text_area(
            "AI generates job using the description",
            height=350,
            placeholder="Paste the complete job description here...",
            key="create_job_text",
        )

        if st.button(
            "Create Job",
            type="primary",
            use_container_width=True,
            key="create_job_from_text",
        ):
            if not job_text.strip():
                st.warning(
                    "Please paste a job description."
                )
                return

            try:
                with st.spinner(
                    "Extracting and saving job information..."
                ):
                    job = extract_job_info(
                        job_text=job_text,
                        source_filename=None,
                    )

                    save_job_json(job)

                refresh_job_table()

                st.session_state["job_created_message"] = (
                    f"Job created successfully: "
                    f"{job.job_title or 'Untitled Job'}"
                )

                st.rerun()

            except Exception as exc:
                st.error(f"Unable to create job: {exc}")

    # =========================================================
    # Method 2: Upload file
    # =========================================================
    elif input_method == "Upload file":
        job_file = st.file_uploader(
            "Upload job description",
            type=["pdf", "docx", "txt"],
            key="create_job_uploader",
        )

        if not job_file:
            return

        file_path = UPLOAD_DIR / job_file.name

        with open(file_path, "wb") as file:
            file.write(job_file.getbuffer())

        try:
            job_data = load_job_file(str(file_path))

            job_text = job_data["text"]
            source_filename = job_data["filename"]

            st.text_area(
                "Loaded job description",
                value=job_text[:5000],
                height=300,
                disabled=True,
                key="create_job_preview",
            )

        except Exception as exc:
            st.error(
                f"Unable to load job description: {exc}"
            )
            return

        if st.button(
            "Create Job",
            type="primary",
            use_container_width=True,
            key="create_job_from_file",
        ):
            try:
                with st.spinner(
                    "Extracting and saving job information..."
                ):
                    job = extract_job_info(
                        job_text=job_text,
                        source_filename=source_filename,
                    )

                    save_job_json(job)

                refresh_job_table()

                st.session_state["job_created_message"] = (
                    f"Job created successfully: "
                    f"{job.job_title or 'Untitled Job'}"
                )

                st.rerun()

            except Exception as exc:
                st.error(f"Unable to create job: {exc}")

    # =========================================================
    # Method 3: Manual Fill
    # =========================================================
    else:
        st.caption(
            "For list fields, enter one item per line."
        )

        with st.form("manual_job_form"):
            col1, col2 = st.columns(2)

            with col1:
                job_title = st.text_input(
                    "Job title *"
                )

                company = st.text_input(
                    "Company"
                )

                location = st.text_input(
                    "Location"
                )

            with col2:
                required_experience_years = st.number_input(
                    "Required experience in years",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                )

            summary = st.text_area(
                "Job summary",
                height=120,
            )

            required_skills = st.text_area(
                "Required skills",
                placeholder=(
                    "Python\nSQL\nMachine Learning"
                ),
                height=120,
            )

            preferred_skills = st.text_area(
                "Preferred skills",
                placeholder=(
                    "AWS\nDocker\nFastAPI"
                ),
                height=100,
            )

            education_requirements = st.text_area(
                "Education requirements",
                placeholder=(
                    "Bachelor's degree in Computer Science\n"
                    "Master's degree preferred"
                ),
                height=100,
            )

            responsibilities = st.text_area(
                "Responsibilities",
                placeholder=(
                    "Build data pipelines\n"
                    "Develop machine-learning models\n"
                    "Work with business stakeholders"
                ),
                height=150,
            )

            requirements = st.text_area(
                "Additional requirements",
                placeholder=(
                    "Strong communication skills\n"
                    "Experience working in cross-functional teams"
                ),
                height=130,
            )

            submitted = st.form_submit_button(
                "Create Job",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not job_title.strip():
                st.warning("Job title is required.")
                return

            try:
                job = JobInfo(
                    job_id=str(uuid.uuid4()),
                    job_title=job_title.strip(),
                    company=company.strip() or None,
                    location=location.strip() or None,
                    summary=summary.strip() or None,
                    required_skills=text_to_list(
                        required_skills
                    ),
                    preferred_skills=text_to_list(
                        preferred_skills
                    ),
                    required_experience_years=(
                        required_experience_years
                        if required_experience_years > 0
                        else None
                    ),
                    education_requirements=text_to_list(
                        education_requirements
                    ),
                    responsibilities=text_to_list(
                        responsibilities
                    ),
                    requirements=text_to_list(
                        requirements
                    ),
                    source_filename=None,
                    created_time=datetime.now().isoformat(
                        timespec="seconds"
                    ),
                )

                save_job_json(job)
                refresh_job_table()

                st.session_state["job_created_message"] = (
                    f"Job created successfully: "
                    f"{job.job_title}"
                )

                st.rerun()

            except Exception as exc:
                st.error(f"Unable to create job: {exc}")