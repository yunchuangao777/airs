import pandas as pd
import streamlit as st

from cv_loader import load_single_cv
from cv_saver import save_candidate_json
from llm_extractor import extract_cv_info
from utils.file_helpers import save_uploaded_files


def render_cv_upload():
    st.subheader("Upload New CVs")

    uploaded_files = st.file_uploader(
        "",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="cv_uploader",
    )

    if uploaded_files:
        st.write(f"{len(uploaded_files)} file(s) selected")

    if uploaded_files and st.button(
        "Start CV Extraction",
        type="primary",
        key="start_cv_extraction",
    ):
        saved_paths = save_uploaded_files(uploaded_files)

        rows: list[dict] = []
        progress_bar = st.progress(0)
        status_box = st.empty()

        for index, path in enumerate(saved_paths):
            status_box.info(f"Processing: {path.name}")

            try:
                cv = load_single_cv(path)
                candidate = extract_cv_info(cv["text"])

                candidate.raw_text = cv["text"]
                candidate.source_filename = cv["filename"]
                candidate.source_filepath = cv.get("filepath")

                save_candidate_json(candidate, cv["filename"])

                rows.append(
                    {
                        "Filename": cv["filename"],
                        "Candidate ID": candidate.candidate_id,
                        "Name": candidate.name,
                        "Email": candidate.email,
                        "Status": "Success",
                    }
                )

            except Exception as exc:
                rows.append(
                    {
                        "Filename": path.name,
                        "Candidate ID": None,
                        "Name": None,
                        "Email": None,
                        "Status": f"Failed: {exc}",
                    }
                )

            progress_bar.progress((index + 1) / len(saved_paths))

        status_box.empty()
        st.session_state["cv_upload_results"] = rows
        st.session_state["cv_upload_complete"] = True

    if st.session_state.get("cv_upload_complete"):
        st.success("CV extraction completed.")

        result_df = pd.DataFrame(
            st.session_state.get("cv_upload_results", [])
        )
        st.dataframe(
            result_df,
            use_container_width=True,
            hide_index=True,
        )
