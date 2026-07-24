import streamlit as st

from job_extractor import extract_job_info
from job_loader import load_job_file
from job_saver import save_job_json
from utils.paths import UPLOAD_DIR


def refresh_job_table():
    st.session_state["job_table_version"] = (
        st.session_state.get("job_table_version", 0) + 1
    )


@st.dialog("Create New Job", width="large")
def show_create_job_dialog():
    input_method = st.radio(
        "Input method",
        ["Paste text", "Upload file"],
        horizontal=True,
        key="create_job_input_method",
    )

    job_text = ""
    source_filename = None

    if input_method == "Paste text":
        job_text = st.text_area(
            "Paste job description",
            height=350,
            placeholder="Paste the complete job description here...",
            key="create_job_text",
        )

    else:
        job_file = st.file_uploader(
            "Upload job description",
            type=["pdf", "docx", "txt"],
            key="create_job_uploader",
        )

        if job_file:
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
        key="create_job_submit",
    ):
        if not job_text.strip():
            st.warning(
                "Please paste or upload a job description."
            )
            return

        try:
            with st.spinner(
                "Extracting and saving job information..."
            ):
                job = extract_job_info(
                    job_text=job_text,
                    source_filename=source_filename,
                )

                path = save_job_json(job)

            refresh_job_table()

            st.session_state["job_created_message"] = (
                f"Job created successfully: "
                f"{job.job_title or 'Untitled Job'}"
            )

            st.rerun()

        except Exception as exc:
            st.error(f"Unable to create job: {exc}")