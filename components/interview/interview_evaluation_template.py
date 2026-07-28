from __future__ import annotations

import streamlit as st

from services.interview_evaluation_service import (
    InterviewEvaluationTemplate,
    add_custom_criterion,
    get_or_create_evaluation_template,
    get_selected_criteria,
    save_evaluation_template,
    utc_now_iso,
)
from services.interview_package_service import (
    InterviewPackage,
)


def build_editor_key(
    package: InterviewPackage,
) -> str:
    return (
        f"{package.job_id}_"
        f"{package.candidate_id}"
    )


def render_template_summary(
    template: InterviewEvaluationTemplate,
) -> None:
    selected = get_selected_criteria(
        template
    )

    total_weight = sum(
        criterion.weight
        for criterion in selected
    )

    metric_col1, metric_col2, metric_col3 = (
        st.columns(3)
    )

    with metric_col1:
        st.metric(
            "Total Criteria",
            len(template.criteria),
        )

    with metric_col2:
        st.metric(
            "Selected Criteria",
            len(selected),
        )

    with metric_col3:
        st.metric(
            "Total Weight",
            f"{total_weight}%",
        )

    if total_weight != 100:
        st.warning(
            "Selected evaluation weights currently total "
            f"{total_weight}%. A total of 100% is recommended."
        )


def render_criterion_guidance(
    criterion,
) -> None:
    st.markdown("##### Strong evidence")

    if criterion.strong_evidence:
        for item in criterion.strong_evidence:
            st.markdown(f"✅ {item}")
    else:
        st.caption(
            "No strong-evidence examples recorded."
        )

    st.markdown("##### Weak evidence")

    if criterion.weak_evidence:
        for item in criterion.weak_evidence:
            st.markdown(f"⚠️ {item}")
    else:
        st.caption(
            "No weak-evidence examples recorded."
        )


def render_existing_criteria(
    template: InterviewEvaluationTemplate,
    editor_key: str,
) -> None:
    st.markdown("### Evaluation Criteria")

    st.caption(
        "Choose the competencies that should be assessed "
        "during the interview. The weights should normally "
        "total 100%."
    )

    with st.form(
        key=f"evaluation_template_form_{editor_key}",
        clear_on_submit=False,
    ):
        form_values: list[dict] = []

        for criterion in template.criteria:
            source_label = (
                "AI"
                if criterion.source == "ai"
                else "Recruiter"
            )

            title = (
                f"{criterion.criterion_id} · "
                f"{source_label} · "
                f"{criterion.competency}"
            )

            with st.expander(
                title,
                expanded=False,
            ):
                selected = st.checkbox(
                    "Include in evaluation",
                    value=criterion.selected,
                    key=(
                        f"evaluation_selected_"
                        f"{editor_key}_"
                        f"{criterion.criterion_id}"
                    ),
                )

                competency = st.text_input(
                    "Competency",
                    value=criterion.competency,
                    key=(
                        f"evaluation_competency_"
                        f"{editor_key}_"
                        f"{criterion.criterion_id}"
                    ),
                )

                description = st.text_area(
                    "Description",
                    value=criterion.description,
                    height=90,
                    key=(
                        f"evaluation_description_"
                        f"{editor_key}_"
                        f"{criterion.criterion_id}"
                    ),
                )

                weight = st.number_input(
                    "Weight (%)",
                    min_value=0,
                    max_value=100,
                    value=int(
                        criterion.weight
                    ),
                    step=5,
                    key=(
                        f"evaluation_weight_"
                        f"{editor_key}_"
                        f"{criterion.criterion_id}"
                    ),
                )

                with st.expander(
                    "View scoring guidance",
                    expanded=False,
                ):
                    render_criterion_guidance(
                        criterion
                    )

                form_values.append(
                    {
                        "criterion": criterion,
                        "selected": selected,
                        "competency": competency,
                        "description": description,
                        "weight": weight,
                    }
                )

        save_clicked = st.form_submit_button(
            "Save Evaluation Template",
            type="primary",
            use_container_width=True,
        )

    if not save_clicked:
        return

    validation_errors: list[str] = []

    for item in form_values:
        criterion = item["criterion"]

        competency = (
            item["competency"].strip()
        )

        if item["selected"] and not competency:
            validation_errors.append(
                criterion.criterion_id
            )
            continue

        criterion.selected = bool(
            item["selected"]
        )
        criterion.competency = competency
        criterion.description = (
            item["description"].strip()
        )
        criterion.weight = int(
            item["weight"]
        )
        criterion.updated_time = utc_now_iso()

    if validation_errors:
        st.error(
            "The following selected criteria have "
            "no competency name: "
            + ", ".join(validation_errors)
        )
        return

    total_weight = sum(
        criterion.weight
        for criterion in template.criteria
        if criterion.selected
    )

    save_evaluation_template(template)

    st.session_state[
        "interview_evaluation_message"
    ] = (
        "The evaluation template was saved. "
        f"Selected weights total {total_weight}%."
    )

    st.rerun()


def render_add_custom_criterion(
    template: InterviewEvaluationTemplate,
    editor_key: str,
) -> None:
    st.markdown("### Add Evaluation Criterion")

    with st.expander(
        "Create a recruiter criterion",
        expanded=False,
    ):
        with st.form(
            key=f"add_evaluation_criterion_{editor_key}",
            clear_on_submit=True,
        ):
            competency = st.text_input(
                "Competency *",
                placeholder=(
                    "Example: Stakeholder Management"
                ),
            )

            description = st.text_area(
                "Description",
                placeholder=(
                    "Describe what should be assessed."
                ),
                height=90,
            )

            weight = st.number_input(
                "Weight (%)",
                min_value=0,
                max_value=100,
                value=10,
                step=5,
            )

            add_clicked = st.form_submit_button(
                "Add Criterion",
                type="primary",
                use_container_width=True,
            )

    if not add_clicked:
        return

    try:
        criterion = add_custom_criterion(
            template=template,
            competency=competency,
            description=description,
            weight=int(weight),
        )

        st.session_state[
            "interview_evaluation_message"
        ] = (
            f"{criterion.criterion_id} was added "
            "successfully."
        )

        st.rerun()

    except Exception as exc:
        st.error(
            f"Unable to add criterion: {exc}"
        )


def render_scorecard_preview(
    template: InterviewEvaluationTemplate,
) -> None:
    selected = get_selected_criteria(
        template
    )

    st.markdown("### Scorecard Preview")

    if not selected:
        st.warning(
            "No evaluation criteria are selected."
        )
        return

    for criterion in selected:
        with st.container(border=True):
            header_col, weight_col = st.columns(
                [4, 1]
            )

            with header_col:
                st.markdown(
                    f"#### {criterion.competency}"
                )

                if criterion.description:
                    st.write(
                        criterion.description
                    )

            with weight_col:
                st.metric(
                    "Weight",
                    f"{criterion.weight}%",
                )

            st.caption(
                "Future interviewer rating: "
                f"{template.rating_scale_min}–"
                f"{template.rating_scale_max}"
            )


def render_interview_evaluation_template(
    package: InterviewPackage,
) -> None:
    message = st.session_state.pop(
        "interview_evaluation_message",
        None,
    )

    if message:
        st.success(message)

    template = (
        get_or_create_evaluation_template(
            package
        )
    )

    editor_key = build_editor_key(
        package
    )

    st.markdown("## Evaluation Template")

    st.caption(
        "Define the scorecard that will be used after "
        "the interview. Candidate ratings and comments "
        "will be recorded later in the Interview Session."
    )

    render_template_summary(template)

    st.divider()

    render_existing_criteria(
        template=template,
        editor_key=editor_key,
    )

    st.divider()

    render_add_custom_criterion(
        template=template,
        editor_key=editor_key,
    )

    st.divider()

    render_scorecard_preview(template)