import pandas as pd
import streamlit as st

from components.candidate_dialog import show_candidate_details
from match_loader import (
    load_all_candidates,
    load_all_jobs,
    load_matches_by_candidate,
)
from utils.file_helpers import dataframe_to_excel_bytes
from utils.formatters import format_education, format_skills


def get_candidate_match_summary(
    candidate_id: str,
    jobs_by_id: dict,
) -> dict:
    """
    Return match-related information for one candidate.

    Example:
    {
        "matched_jobs": ["Senior Accountant", "Finance Manager"],
        "matched_job_ids": ["job-1", "job-2"],
        "best_match_score": 91,
        "best_matched_job": "Senior Accountant"
    }
    """
    matches = load_matches_by_candidate(candidate_id)

    if not matches:
        return {
            "matched_jobs": [],
            "matched_job_ids": [],
            "best_match_score": None,
            "best_matched_job": "",
        }

    matched_jobs = []
    matched_job_ids = []

    for match in matches:
        job_id = match.get("job_id")
        job = jobs_by_id.get(job_id, {})

        job_title = (
            job.get("job_title")
            or match.get("job_title")
            or "Untitled Job"
        )

        matched_jobs.append(job_title)

        if job_id:
            matched_job_ids.append(job_id)

    best_match = max(
        matches,
        key=lambda item: float(item.get("score", 0) or 0),
    )

    best_job_id = best_match.get("job_id")
    best_job = jobs_by_id.get(best_job_id, {})

    best_job_title = (
        best_job.get("job_title")
        or best_match.get("job_title")
        or "Untitled Job"
    )

    return {
        "matched_jobs": matched_jobs,
        "matched_job_ids": matched_job_ids,
        "best_match_score": float(
            best_match.get("score", 0) or 0
        ),
        "best_matched_job": best_job_title,
    }


def render_candidate_library():
    candidates = load_all_candidates()
    jobs = load_all_jobs()

    st.markdown("## Candidate Library")

    if not candidates:
        st.info("No CVs loaded yet.")
        return

    jobs_by_id = {
        job.get("job_id"): job
        for job in jobs
        if job.get("job_id")
    }

    table_rows = []

    for candidate in candidates:
        candidate_id = candidate.get("candidate_id") or ""

        match_summary = get_candidate_match_summary(
            candidate_id=candidate_id,
            jobs_by_id=jobs_by_id,
        )

        table_rows.append(
            {
                "Name": (
                    candidate.get("name")
                    or "Unknown Candidate"
                ),
                "Email": candidate.get("email") or "",
                "Phone": candidate.get("phone") or "",
                "Location": candidate.get("location") or "",
                "Education": format_education(
                    candidate.get("education", [])
                ),
                "Skills": format_skills(
                    candidate.get("skills", []),
                    max_items=8,
                ),
                "Experience (Years)": candidate.get(
                    "total_years_experience"
                ),
                "Matched Jobs": "; ".join(
                    match_summary["matched_jobs"]
                ),
                "Best Match Score": match_summary[
                    "best_match_score"
                ],
                "Best Matched Job": match_summary[
                    "best_matched_job"
                ],
                "Source File": (
                    candidate.get("source_filename") or ""
                ),
                "Candidate ID": candidate_id,

                # Internal filter field; hidden from the table.
                "_Matched Job IDs": match_summary[
                    "matched_job_ids"
                ],
            }
        )

    candidate_df = pd.DataFrame(table_rows)

    # =========================================================
    # Global search
    # =========================================================
    st.markdown("### 🔍 Search")

    keyword = st.text_input(
        "Search candidates",
        placeholder=(
            "Search name, email, skill, school, company, "
            "location, or source file..."
        ),
        key="candidate_global_search",
    )

    # =========================================================
    # Structured filters
    # =========================================================
    st.markdown("### 📊 Filters")

    filter_row1_col1, filter_row1_col2, filter_row1_col3 = (
        st.columns(3)
    )

    with filter_row1_col1:
        skill_options = sorted(
            {
                skill
                for candidate in candidates
                for skill in candidate.get("skills", [])
                if skill
            },
            key=str.lower,
        )

        selected_skills = st.multiselect(
            "Skills",
            options=skill_options,
            key="candidate_skill_filter",
        )

    with filter_row1_col2:
        location_options = sorted(
            {
                candidate.get("location")
                for candidate in candidates
                if candidate.get("location")
            },
            key=str.lower,
        )

        selected_locations = st.multiselect(
            "Locations",
            options=location_options,
            key="candidate_location_filter",
        )

    with filter_row1_col3:
        education_options = [
            "Bachelor",
            "Master",
            "MBA",
            "PhD",
            "Diploma",
            "Certificate",
        ]

        selected_education = st.multiselect(
            "Education level",
            options=education_options,
            key="candidate_education_filter",
        )

    filter_row2_col1, filter_row2_col2, filter_row2_col3 = (
        st.columns(3)
    )

    with filter_row2_col1:
        min_experience = st.number_input(
            "Minimum experience",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="candidate_min_experience",
        )

    with filter_row2_col2:
        job_options = {
            (
                f"{job.get('job_title', 'Untitled Job')}"
                + (
                    f" — {job.get('company')}"
                    if job.get("company")
                    else ""
                )
            ): job.get("job_id")
            for job in jobs
            if job.get("job_id")
        }

        selected_job_label = st.selectbox(
            "Matched job",
            options=["Any job"] + list(job_options.keys()),
            key="candidate_matched_job_filter",
        )

        selected_job_id = (
            None
            if selected_job_label == "Any job"
            else job_options[selected_job_label]
        )

    with filter_row2_col3:
        min_match_score = st.number_input(
            "Minimum match score",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=5.0,
            key="candidate_min_match_score",
        )

    clear_col, spacer_col = st.columns([1, 5])

    with clear_col:
        if st.button(
            "Clear Filters",
            use_container_width=True,
            key="candidate_clear_filters",
        ):
            keys_to_clear = [
                "candidate_global_search",
                "candidate_skill_filter",
                "candidate_location_filter",
                "candidate_education_filter",
                "candidate_min_experience",
                "candidate_matched_job_filter",
                "candidate_min_match_score",
            ]

            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]

            st.rerun()

    # =========================================================
    # Apply search and filters
    # =========================================================
    filtered_df = candidate_df.copy()

    if keyword.strip():
        search_text = keyword.strip().lower()

        searchable_columns = [
            "Name",
            "Email",
            "Phone",
            "Location",
            "Education",
            "Skills",
            "Matched Jobs",
            "Best Matched Job",
            "Source File",
        ]

        mask = filtered_df[searchable_columns].fillna("").apply(
            lambda row: row.astype(str)
            .str.lower()
            .str.contains(
                search_text,
                regex=False,
            )
            .any(),
            axis=1,
        )

        filtered_df = filtered_df[mask]

    if selected_skills:
        selected_skills_lower = {
            skill.lower()
            for skill in selected_skills
        }

        filtered_df = filtered_df[
            filtered_df["Skills"]
            .fillna("")
            .apply(
                lambda value: selected_skills_lower.issubset(
                    {
                        skill.strip().lower()
                        for skill in str(value).split(",")
                    }
                )
            )
        ]

    if selected_locations:
        selected_locations_lower = {
            location.lower()
            for location in selected_locations
        }

        filtered_df = filtered_df[
            filtered_df["Location"]
            .fillna("")
            .str.lower()
            .isin(selected_locations_lower)
        ]

    if selected_education:
        education_terms = [
            value.lower()
            for value in selected_education
        ]

        filtered_df = filtered_df[
            filtered_df["Education"]
            .fillna("")
            .str.lower()
            .apply(
                lambda value: any(
                    term in value
                    for term in education_terms
                )
            )
        ]

    if min_experience > 0:
        experience_values = pd.to_numeric(
            filtered_df["Experience (Years)"],
            errors="coerce",
        )

        filtered_df = filtered_df[
            experience_values >= min_experience
        ]

    if selected_job_id:
        filtered_df = filtered_df[
            filtered_df["_Matched Job IDs"].apply(
                lambda job_ids: (
                    selected_job_id in job_ids
                    if isinstance(job_ids, list)
                    else False
                )
            )
        ]

    if min_match_score > 0:
        match_scores = pd.to_numeric(
            filtered_df["Best Match Score"],
            errors="coerce",
        )

        filtered_df = filtered_df[
            match_scores >= min_match_score
        ]

    st.caption(
        f"Showing {len(filtered_df)} of "
        f"{len(candidate_df)} candidates."
    )

    # =========================================================
    # Export
    # =========================================================
    st.markdown("### 📤 Export")

    export_df = filtered_df.drop(
        columns=[
            "Candidate ID",
            "_Matched Job IDs",
        ],
        errors="ignore",
    )

    export_col1, export_col2, export_spacer = st.columns(
        [1, 1, 4]
    )

    with export_col1:
        csv_data = export_df.to_csv(
            index=False,
            encoding="utf-8-sig",
        ).encode("utf-8-sig")

        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="candidates_filtered.csv",
            mime="text/csv",
            use_container_width=True,
            key="candidate_export_csv",
        )

    with export_col2:
        excel_data = dataframe_to_excel_bytes(export_df)

        st.download_button(
            label="Download Excel",
            data=excel_data,
            file_name="candidates_filtered.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
            key="candidate_export_excel",
        )

    st.divider()

    # =========================================================
    # Candidate list
    # =========================================================
    st.markdown("### Candidate List")

    st.caption(
        "Select a candidate row to open the full candidate profile."
    )

    display_df = filtered_df.drop(
        columns=["_Matched Job IDs"],
        errors="ignore",
    ).reset_index(drop=True)

    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="candidate_library_table",
        column_config={
            "Name": st.column_config.TextColumn(
                "Name",
                width="medium",
            ),
            "Email": st.column_config.TextColumn(
                "Email",
                width="medium",
            ),
            "Phone": st.column_config.TextColumn(
                "Phone",
                width="small",
            ),
            "Location": st.column_config.TextColumn(
                "Location",
                width="small",
            ),
            "Education": st.column_config.TextColumn(
                "Education",
                width="large",
            ),
            "Skills": st.column_config.TextColumn(
                "Skills",
                width="large",
            ),
            "Experience (Years)": (
                st.column_config.NumberColumn(
                    "Experience",
                    format="%.1f years",
                )
            ),
            "Matched Jobs": st.column_config.TextColumn(
                "Matched Jobs",
                width="large",
            ),
            "Best Match Score": (
                st.column_config.NumberColumn(
                    "Best Score",
                    min_value=0,
                    max_value=100,
                    format="%.1f",
                )
            ),
            "Best Matched Job": st.column_config.TextColumn(
                "Best Matched Job",
                width="medium",
            ),
            "Source File": st.column_config.TextColumn(
                "Source File",
                width="medium",
            ),
            "Candidate ID": None,
        },
    )

    selected_rows = event.selection.rows

    if selected_rows:
        selected_row = display_df.iloc[selected_rows[0]]
        candidate_id = selected_row["Candidate ID"]

        selected_candidate = next(
            (
                candidate
                for candidate in candidates
                if candidate.get("candidate_id")
                == candidate_id
            ),
            None,
        )

        if selected_candidate:
            show_candidate_details(selected_candidate)