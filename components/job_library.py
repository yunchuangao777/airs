import pandas as pd
import streamlit as st

from components.job_dialog import show_job_details
from match_loader import load_all_jobs


def format_list(
    values: list[str],
    max_items: int = 6,
) -> str:
    if not values:
        return ""

    visible_values = values[:max_items]
    result = ", ".join(visible_values)

    remaining = len(values) - max_items

    if remaining > 0:
        result += f" (+{remaining} more)"

    return result


def render_job_library(search_text: str = ""):
    jobs = load_all_jobs()

    st.markdown("## Created Jobs")

    if not jobs:
        st.info("No jobs have been created yet.")
        return

    table_rows = []

    for job in jobs:
        table_rows.append(
            {
                "Job Title": (
                    job.get("job_title")
                    or "Untitled Job"
                ),
                "Company": job.get("company") or "",
                "Location": job.get("location") or "",
                "Required Skills": format_list(
                    job.get("required_skills", [])
                ),
                "Preferred Skills": format_list(
                    job.get("preferred_skills", [])
                ),
                "Required Experience": job.get(
                    "required_experience_years"
                ),
                "Created Time": job.get("created_time") or "",
                "Source File": job.get("source_filename") or "",
                "Job ID": job.get("job_id") or "",

                # Internal fields used for searching.
                "_Summary": job.get("summary") or "",
                "_Responsibilities": " ".join(
                    job.get("responsibilities", [])
                ),
                "_Requirements": " ".join(
                    job.get("requirements", [])
                ),
                "_Education": " ".join(
                    job.get("education_requirements", [])
                ),
            }
        )

    job_df = pd.DataFrame(table_rows)

    filtered_df = job_df.copy()

    if search_text.strip():
        query = search_text.strip().lower()

        searchable_columns = [
            "Job Title",
            "Company",
            "Location",
            "Required Skills",
            "Preferred Skills",
            "_Summary",
            "_Responsibilities",
            "_Requirements",
            "_Education",
            "Source File",
        ]

        mask = filtered_df[searchable_columns].fillna("").apply(
            lambda row: row.astype(str)
            .str.lower()
            .str.contains(
                query,
                regex=False,
            )
            .any(),
            axis=1,
        )

        filtered_df = filtered_df[mask]

    st.caption(
        f"Showing {len(filtered_df)} of "
        f"{len(job_df)} jobs."
    )

    display_df = filtered_df.drop(
        columns=[
            "_Summary",
            "_Responsibilities",
            "_Requirements",
            "_Education",
        ],
        errors="ignore",
    ).reset_index(drop=True)

    st.caption(
        "Select a job row to view, edit, or delete it."
    )

    table_version = st.session_state.get(
        "job_table_version",
        0,
    )

    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"job_library_table_{table_version}",
        column_config={
            "Job Title": st.column_config.TextColumn(
                "Job Title",
                width="medium",
            ),
            "Company": st.column_config.TextColumn(
                "Company",
                width="medium",
            ),
            "Location": st.column_config.TextColumn(
                "Location",
                width="small",
            ),
            "Required Skills": st.column_config.TextColumn(
                "Required Skills",
                width="large",
            ),
            "Preferred Skills": st.column_config.TextColumn(
                "Preferred Skills",
                width="large",
            ),
            "Required Experience": (
                st.column_config.NumberColumn(
                    "Experience",
                    format="%.1f years",
                )
            ),
            "Created Time": st.column_config.TextColumn(
                "Created Time",
                width="medium",
            ),
            "Source File": st.column_config.TextColumn(
                "Source File",
                width="medium",
            ),
            "Job ID": None,
        },
    )

    selected_rows = event.selection.rows

    if selected_rows:
        selected_row = display_df.iloc[selected_rows[0]]
        selected_job_id = selected_row["Job ID"]

        selected_job = next(
            (
                job
                for job in jobs
                if job.get("job_id") == selected_job_id
            ),
            None,
        )

        if selected_job:
            show_job_details(selected_job)