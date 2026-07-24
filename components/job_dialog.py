import streamlit as st

from job_saver import delete_job_json, save_job_json
from schema import JobInfo


def list_to_text(values: list[str]) -> str:
    """Convert a list into editable one-item-per-line text."""
    if not values:
        return ""

    return "\n".join(str(value) for value in values)


def text_to_list(value: str) -> list[str]:
    """Convert one-item-per-line text back into a clean list."""
    if not value:
        return []

    results = []

    for line in value.splitlines():
        cleaned = line.strip().lstrip("-•").strip()

        if cleaned:
            results.append(cleaned)

    return results


def parse_optional_float(value: str) -> float | None:
    value = value.strip()

    if not value:
        return None

    return float(value)


def refresh_job_table():
    """
    Change the dataframe key so old row selection is cleared
    after editing or deleting a job.
    """
    st.session_state["job_table_version"] = (
        st.session_state.get("job_table_version", 0) + 1
    )


@st.dialog("Job Details", width="large")
def show_job_details(job: dict):
    job_title = job.get("job_title") or "Untitled Job"

    st.subheader(job_title)

    details_tab, edit_tab, delete_tab = st.tabs(
        [
            "Details",
            "Edit Job",
            "Delete Job",
        ]
    )

    # =========================================================
    # Details
    # =========================================================
    with details_tab:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Basic Information")

            st.write(
                f"**Company:** "
                f"{job.get('company') or 'Not available'}"
            )
            st.write(
                f"**Location:** "
                f"{job.get('location') or 'Not available'}"
            )
            st.write(
                f"**Job ID:** "
                f"{job.get('job_id') or 'Not available'}"
            )

        with col2:
            st.markdown("#### Source")

            st.write(
                f"**Source file:** "
                f"{job.get('source_filename') or 'Pasted text'}"
            )
            st.write(
                f"**Created time:** "
                f"{job.get('created_time') or 'Not available'}"
            )

            required_years = job.get(
                "required_experience_years"
            )

            experience_text = (
                f"{required_years} years"
                if required_years is not None
                else "Not available"
            )

            st.write(
                f"**Required experience:** {experience_text}"
            )

        summary = job.get("summary")

        if summary:
            st.markdown("#### Job Summary")
            st.write(summary)

        st.markdown("#### Required Skills")

        required_skills = job.get("required_skills", [])

        if required_skills:
            st.write(", ".join(required_skills))
        else:
            st.info("No required skills extracted.")

        st.markdown("#### Preferred Skills")

        preferred_skills = job.get("preferred_skills", [])

        if preferred_skills:
            st.write(", ".join(preferred_skills))
        else:
            st.info("No preferred skills extracted.")

        st.markdown("#### Education Requirements")

        education_requirements = job.get(
            "education_requirements",
            [],
        )

        if education_requirements:
            for item in education_requirements:
                st.write(f"- {item}")
        else:
            st.info("No education requirements extracted.")

        st.markdown("#### Responsibilities")

        responsibilities = job.get("responsibilities", [])

        if responsibilities:
            for item in responsibilities:
                st.write(f"- {item}")
        else:
            st.info("No responsibilities extracted.")

        st.markdown("#### Requirements")

        requirements = job.get("requirements", [])

        if requirements:
            for item in requirements:
                st.write(f"- {item}")
        else:
            st.info("No additional requirements extracted.")

    # =========================================================
    # Edit
    # =========================================================
    with edit_tab:
        st.caption(
            "For list fields, enter one item per line."
        )

        with st.form(
            key=f"edit_job_form_{job.get('job_id')}"
        ):
            col1, col2 = st.columns(2)

            with col1:
                edited_title = st.text_input(
                    "Job title",
                    value=job.get("job_title") or "",
                )

                edited_company = st.text_input(
                    "Company",
                    value=job.get("company") or "",
                )

            with col2:
                edited_location = st.text_input(
                    "Location",
                    value=job.get("location") or "",
                )

                current_experience = job.get(
                    "required_experience_years"
                )

                edited_experience = st.text_input(
                    "Required experience in years",
                    value=(
                        str(current_experience)
                        if current_experience is not None
                        else ""
                    ),
                    placeholder="Example: 5",
                )

            edited_summary = st.text_area(
                "Job summary",
                value=job.get("summary") or "",
                height=140,
            )

            edited_required_skills = st.text_area(
                "Required skills",
                value=list_to_text(
                    job.get("required_skills", [])
                ),
                height=140,
            )

            edited_preferred_skills = st.text_area(
                "Preferred skills",
                value=list_to_text(
                    job.get("preferred_skills", [])
                ),
                height=120,
            )

            edited_education = st.text_area(
                "Education requirements",
                value=list_to_text(
                    job.get("education_requirements", [])
                ),
                height=120,
            )

            edited_responsibilities = st.text_area(
                "Responsibilities",
                value=list_to_text(
                    job.get("responsibilities", [])
                ),
                height=180,
            )

            edited_requirements = st.text_area(
                "Additional requirements",
                value=list_to_text(
                    job.get("requirements", [])
                ),
                height=180,
            )

            save_changes = st.form_submit_button(
                "Save Changes",
                type="primary",
                use_container_width=True,
            )

        if save_changes:
            try:
                updated_data = job.copy()

                updated_data.update(
                    {
                        "job_title": (
                            edited_title.strip() or None
                        ),
                        "company": (
                            edited_company.strip() or None
                        ),
                        "location": (
                            edited_location.strip() or None
                        ),
                        "summary": (
                            edited_summary.strip() or None
                        ),
                        "required_experience_years": (
                            parse_optional_float(
                                edited_experience
                            )
                        ),
                        "required_skills": text_to_list(
                            edited_required_skills
                        ),
                        "preferred_skills": text_to_list(
                            edited_preferred_skills
                        ),
                        "education_requirements": text_to_list(
                            edited_education
                        ),
                        "responsibilities": text_to_list(
                            edited_responsibilities
                        ),
                        "requirements": text_to_list(
                            edited_requirements
                        ),
                    }
                )

                # Validate the edited data against your schema.
                updated_job = JobInfo.model_validate(
                    updated_data
                )

                save_job_json(updated_job)

                refresh_job_table()

                st.success("Job updated successfully.")
                st.rerun()

            except ValueError:
                st.error(
                    "Required experience must be a valid number "
                    "or left blank."
                )

            except Exception as exc:
                st.error(f"Unable to update job: {exc}")

    # =========================================================
    # Delete
    # =========================================================
    with delete_tab:
        st.warning(
            "Deleting a job cannot be undone."
        )

        delete_related = st.checkbox(
            (
                "Also delete matching results and interview "
                "preparation files for this job"
            ),
            value=False,
            key=f"delete_related_{job.get('job_id')}",
        )

        confirmation = st.text_input(
            'Type "DELETE" to confirm',
            key=f"delete_confirmation_{job.get('job_id')}",
        )

        delete_clicked = st.button(
            "Delete Job",
            type="primary",
            use_container_width=True,
            disabled=confirmation.strip() != "DELETE",
            key=f"delete_job_{job.get('job_id')}",
        )

        if delete_clicked:
            job_id = job.get("job_id")

            if not job_id:
                st.error("This job does not have a valid job ID.")
                return

            deleted = delete_job_json(
                job_id=job_id,
                delete_related=delete_related,
            )

            if deleted:
                refresh_job_table()
                st.success("Job deleted successfully.")
                st.rerun()
            else:
                st.error("The job JSON file was not found.")