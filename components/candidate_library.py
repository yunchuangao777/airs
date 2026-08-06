import pandas as pd
import streamlit as st

from components.candidate_dialog import show_candidate_details
from match_loader import (
    load_all_candidates,
    load_all_jobs,
    load_matches_by_candidate,
)
from utils.file_helpers import candidates_to_pdf_bytes
from utils.formatters import format_education, format_skills


def get_candidate_match_summary(
    candidate_id: str,
    jobs_by_id: dict,
) -> dict:
    """
    Return match-related information for one candidate.
    """
    matches = load_matches_by_candidate(candidate_id)

    if not matches:
        return {
            "matched_jobs": [],
            "matched_job_ids": [],
            "best_match_score": None,
            "best_matched_job": "",
        }

    matched_jobs: list[str] = []
    matched_job_ids: list[str] = []

    for match in matches:
        job_id = match.get("job_id")
        job = jobs_by_id.get(job_id, {})

        job_title = (
            job.get("job_title")
            or match.get("job_title")
            or "Untitled Job"
        )

        if job_title not in matched_jobs:
            matched_jobs.append(job_title)

        if job_id and job_id not in matched_job_ids:
            matched_job_ids.append(job_id)

    best_match = max(
        matches,
        key=lambda item: float(
            item.get("score", 0) or 0
        ),
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


def build_candidate_dataframe(
    candidates: list[dict],
    jobs_by_id: dict,
) -> pd.DataFrame:
    """
    Convert candidate records into the table used by the UI.
    """
    table_rows: list[dict] = []

    for candidate in candidates:
        candidate_id = str(
            candidate.get("candidate_id") or ""
        ).strip()

        # Stable UI lookup key for older records created before
        # candidate IDs were assigned during CV extraction.
        candidate_lookup_key = (
            candidate_id
            or str(candidate.get("_source_path") or "").strip()
            or str(candidate.get("source_filepath") or "").strip()
            or str(candidate.get("source_filename") or "").strip()
        )

        candidate_skills = [
            str(skill).strip()
            for skill in candidate.get("skills", [])
            if str(skill).strip()
        ]

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

                "Record Status": (
                    "Archived"
                    if candidate.get(
                        "is_archived",
                        False,
                    )
                    else "Active"
                ),

                "Education": format_education(
                    candidate.get("education", [])
                ),
                "Skills": format_skills(
                    candidate_skills,
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
                "_Candidate Lookup Key": candidate_lookup_key,

                # Internal fields used only for filtering.
                "_All Skills": candidate_skills,
                "_Matched Job IDs": match_summary[
                    "matched_job_ids"
                ],
            }
        )

    return pd.DataFrame(table_rows)


def render_candidate_library() -> None:
    all_candidates = load_all_candidates()
    jobs = load_all_jobs()

    archived_message = st.session_state.pop(
        "candidate_archived_message",
        None,
    )

    if archived_message:
        st.success(archived_message)

    show_archived = st.checkbox(
        "Show archived candidates",
        value=False,
        key="candidate_show_archived",
        help=(
            "Archived candidates are hidden from the "
            "normal active-candidate list."
        ),
    )

    if show_archived:
        candidates = all_candidates
    else:
        candidates = [
            candidate
            for candidate in all_candidates
            if not bool(
                candidate.get(
                    "is_archived",
                    False,
                )
            )
        ]

    # st.markdown("## Candidate Library")

    if not candidates:
        if show_archived:
            st.info(
                "No candidate records are available."
            )
        else:
            st.info(
                "No active candidates are available."
            )
        return

    jobs_by_id = {
        job.get("job_id"): job
        for job in jobs
        if job.get("job_id")
    }

    candidate_df = build_candidate_dataframe(
        candidates=candidates,
        jobs_by_id=jobs_by_id,
    )

    # =========================================================
    # Global search
    # =========================================================
    st.markdown("### 🔍 Search")

    keyword = st.text_input(
        # "Search candidates",
        "",
        placeholder=(
            "Search name, email, skill, school, "
            "location, job, or source file..."
        ),
        key="candidate_global_search",
    )

    # =========================================================
    # Structured filters
    # =========================================================
    st.markdown("### 📊 Filters")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    # ---------------------------------------------------------
    # Skill filter
    # ---------------------------------------------------------
    with filter_col1:
        skill_options = sorted(
            {
                str(skill).strip()
                for candidate in candidates
                for skill in candidate.get("skills", [])
                if str(skill).strip()
            },
            key=str.lower,
        )

        selected_skill = st.selectbox(
            "Skill",
            options=[
                "Any skill",
                *skill_options,
                "Other...",
            ],
            key="candidate_skill_filter",
        )

        typed_skill = ""

        if selected_skill == "Other...":
            typed_skill = st.text_input(
                "Specify skill",
                placeholder="Example: Power BI",
                key="candidate_typed_skill",
            )

    # ---------------------------------------------------------
    # Location filter
    # ---------------------------------------------------------
    with filter_col2:
        location_options = sorted(
            {
                str(candidate.get("location")).strip()
                for candidate in candidates
                if candidate.get("location")
            },
            key=str.lower,
        )

        selected_location = st.selectbox(
            "Location",
            options=[
                "Any location",
                *location_options,
                "Other...",
            ],
            key="candidate_location_filter",
        )

        typed_location = ""

        if selected_location == "Other...":
            typed_location = st.text_input(
                "Specify location",
                placeholder="City, province, or country",
                key="candidate_typed_location",
            )

    # ---------------------------------------------------------
    # Education filter
    # ---------------------------------------------------------
    with filter_col3:
        selected_education = st.selectbox(
            "Education",
            options=[
                "Any education",
                "Bachelor",
                "Master",
                "MBA",
                "PhD",
                "Diploma",
                "Certificate",
                "Other...",
            ],
            key="candidate_education_filter",
        )

        typed_education = ""

        if selected_education == "Other...":
            typed_education = st.text_input(
                "Specify education",
                placeholder=(
                    "Degree, major, qualification, or school"
                ),
                key="candidate_typed_education",
            )

    filter_col4, filter_col5, filter_col6 = st.columns(3)

    # ---------------------------------------------------------
    # Experience filter
    # ---------------------------------------------------------
    with filter_col4:
        min_experience = st.number_input(
            "Minimum experience",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="candidate_min_experience",
        )

    # ---------------------------------------------------------
    # Matched-job filter
    # ---------------------------------------------------------
    with filter_col5:
        job_options = {
            (
                f"{job.get('job_title') or 'Untitled Job'}"
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
            options=[
                "Any job",
                *job_options.keys(),
            ],
            key="candidate_matched_job_filter",
        )

        selected_job_id = (
            None
            if selected_job_label == "Any job"
            else job_options[selected_job_label]
        )

    # ---------------------------------------------------------
    # Match-score filter
    # ---------------------------------------------------------
    with filter_col6:
        min_match_score = st.number_input(
            "Minimum match score",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=5.0,
            key="candidate_min_match_score",
        )

    # =========================================================
    # Clear filters
    # =========================================================
    clear_col, _ = st.columns([1, 5])

    with clear_col:
        if st.button(
            "Reset",
            use_container_width=True,
            key="candidate_clear_filters",
        ):
            keys_to_clear = [
                "candidate_global_search",
                "candidate_skill_filter",
                "candidate_typed_skill",
                "candidate_location_filter",
                "candidate_typed_location",
                "candidate_education_filter",
                "candidate_typed_education",
                "candidate_min_experience",
                "candidate_matched_job_filter",
                "candidate_min_match_score",
            ]

            for key in keys_to_clear:
                st.session_state.pop(key, None)

            st.rerun()

    # =========================================================
    # Prepare filter values
    # =========================================================
    skill_filter = ""

    if selected_skill not in {
        "Any skill",
        "Other...",
    }:
        skill_filter = selected_skill.strip().lower()

    elif selected_skill == "Other...":
        skill_filter = typed_skill.strip().lower()

    location_filter = ""

    if selected_location not in {
        "Any location",
        "Other...",
    }:
        location_filter = (
            selected_location.strip().lower()
        )

    elif selected_location == "Other...":
        location_filter = (
            typed_location.strip().lower()
        )

    education_filter = ""

    if selected_education not in {
        "Any education",
        "Other...",
    }:
        education_filter = (
            selected_education.strip().lower()
        )

    elif selected_education == "Other...":
        education_filter = (
            typed_education.strip().lower()
        )

    # =========================================================
    # Apply search and filters
    # =========================================================
    filtered_df = candidate_df.copy()

    # ---------------------------------------------------------
    # Global search
    # ---------------------------------------------------------
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

        mask = (
            filtered_df[searchable_columns]
            .fillna("")
            .apply(
                lambda row: (
                    row.astype(str)
                    .str.lower()
                    .str.contains(
                        search_text,
                        regex=False,
                    )
                    .any()
                ),
                axis=1,
            )
        )

        filtered_df = filtered_df[mask]

    # ---------------------------------------------------------
    # Skill
    # ---------------------------------------------------------
    if skill_filter:
        filtered_df = filtered_df[
            filtered_df["_All Skills"].apply(
                lambda skills: (
                    any(
                        skill_filter
                        in str(skill).strip().lower()
                        for skill in skills
                    )
                    if isinstance(skills, list)
                    else False
                )
            )
        ]

    # ---------------------------------------------------------
    # Location
    # ---------------------------------------------------------
    if location_filter:
        filtered_df = filtered_df[
            filtered_df["Location"]
            .fillna("")
            .apply(
                lambda value: (
                    location_filter
                    in str(value).lower()
                )
            )
        ]

    # ---------------------------------------------------------
    # Education
    # ---------------------------------------------------------
    if education_filter:
        filtered_df = filtered_df[
            filtered_df["Education"]
            .fillna("")
            .apply(
                lambda value: (
                    education_filter
                    in str(value).lower()
                )
            )
        ]

    # ---------------------------------------------------------
    # Experience
    # ---------------------------------------------------------
    if min_experience > 0:
        experience_values = pd.to_numeric(
            filtered_df["Experience (Years)"],
            errors="coerce",
        )

        filtered_df = filtered_df[
            experience_values >= min_experience
        ]

    # ---------------------------------------------------------
    # Matched job
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # Match score
    # ---------------------------------------------------------
    if min_match_score > 0:
        match_scores = pd.to_numeric(
            filtered_df["Best Match Score"],
            errors="coerce",
        )

        filtered_df = filtered_df[
            match_scores >= min_match_score
        ]

    # st.caption(
        # f"Showing {len(filtered_df)} of "
        # f"{len(candidate_df)} candidates."
    # )

    # =========================================================
    # Export
    # =========================================================
    st.markdown("### 📤 Export")

    internal_columns = [
        "Candidate ID",
        "_Candidate Lookup Key",
        "_All Skills",
        "_Matched Job IDs",
    ]

    export_df = filtered_df.drop(
        columns=internal_columns,
        errors="ignore",
    )

    export_col1, export_col2, _ = st.columns(
        [1, 1, 4]
    )

    # ---------------------------------------------------------
    # CSV export
    # ---------------------------------------------------------
    with export_col1:
        csv_data = export_df.to_csv(
            index=False,
            encoding="utf-8-sig",
        ).encode("utf-8-sig")

        st.download_button(
            label="Export CSV",
            data=csv_data,
            file_name="candidates_filtered.csv",
            mime="text/csv",
            use_container_width=True,
            key="candidate_export_csv",
        )

    # ---------------------------------------------------------
    # PDF export
    # ---------------------------------------------------------
    with export_col2:
        # Candidate ID is still available in filtered_df.
        filtered_candidate_ids = {
            str(candidate_id)
            for candidate_id in (
                filtered_df["Candidate ID"]
                .dropna()
                .tolist()
            )
            if str(candidate_id).strip()
        }

        filtered_candidates = [
            candidate
            for candidate in candidates
            if str(
                candidate.get("candidate_id") or ""
            )
            in filtered_candidate_ids
        ]

        # Preserve the match fields shown in the candidate table.
        candidate_rows = {
            str(row["Candidate ID"]): row.to_dict()
            for _, row in filtered_df.iterrows()
            if str(
                row.get("Candidate ID") or ""
            ).strip()
        }

        pdf_data = candidates_to_pdf_bytes(
            candidates=filtered_candidates,
            candidate_rows=candidate_rows,
        )

        st.download_button(
            label="Export PDF",
            data=pdf_data,
            file_name="candidate_report.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="candidate_export_pdf",
        )

    st.divider()

    # =========================================================
    # Candidate list
    # =========================================================
    # st.markdown("### Candidate List")

    st.caption(
        "Select a candidate row to open the full "
        "candidate profile."
    )

    display_df = filtered_df.drop(
        columns=[
            "_All Skills",
            "_Matched Job IDs",
        ],
        errors="ignore",
    ).reset_index(drop=True)

    table_version = st.session_state.get(
        "candidate_table_version",
        0,
    )

    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=(
            f"candidate_library_table_"
            f"{table_version}"
        ),
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
            "Best Matched Job": (
                st.column_config.TextColumn(
                    "Best Matched Job",
                    width="medium",
                )
            ),
            "Source File": st.column_config.TextColumn(
                "Source File",
                width="medium",
            ),
            "Candidate ID": None,
            "_Candidate Lookup Key": None,
            "Record Status": st.column_config.TextColumn(
                "Status",
                width="small",
            ),
        },
    )

    selected_rows = event.selection.rows

    if selected_rows:
        selected_row = display_df.iloc[
            selected_rows[0]
        ]

        selected_lookup_key = str(
            selected_row.get(
                "_Candidate Lookup Key",
                "",
            )
            or ""
        ).strip()

        selected_candidate = next(
            (
                candidate
                for candidate in candidates
                if (
                    str(
                        candidate.get("candidate_id")
                        or candidate.get("_source_path")
                        or candidate.get("source_filepath")
                        or candidate.get("source_filename")
                        or ""
                    ).strip()
                    == selected_lookup_key
                )
            ),
            None,
        )

        if selected_candidate:
            show_candidate_details(
                selected_candidate
            )