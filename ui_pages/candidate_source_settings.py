from __future__ import annotations

import streamlit as st

from services.candidate_source_config_service import (
    get_candidate_source,
    load_candidate_source_config,
    update_candidate_source,
    update_candidate_source_settings,
)
from services.permission_service import (
    require_permission,
)


SOURCE_ORDER = [
    "internal_airs",
    "public_web",
    "github",
]


def _show_saved_message() -> None:
    message = st.session_state.pop(
        "candidate_source_settings_message",
        None,
    )

    if message:
        st.success(message)


def _finish_update(
    message: str,
) -> None:
    st.session_state[
        "candidate_source_settings_message"
    ] = message

    st.rerun()


def _render_source_card(
    source_id: str,
    source: dict,
) -> None:
    display_name = str(
        source.get("display_name")
        or source_id
    )

    description = str(
        source.get("description")
        or ""
    )

    source_type = str(
        source.get("source_type")
        or ""
    ).replace(
        "_",
        " ",
    ).title()

    enabled = bool(
        source.get("enabled")
    )

    with st.container(
        border=True,
    ):
        title_col, status_col = st.columns(
            [4, 1]
        )

        with title_col:
            st.markdown(
                f"### {display_name}"
            )

            if description:
                st.caption(description)

            st.caption(
                f"Source type: {source_type}"
            )

        with status_col:
            st.markdown(
                "**Enabled**"
                if enabled
                else "**Disabled**"
            )

        new_enabled = st.toggle(
            "Enable this source",
            value=enabled,
            key=(
                "candidate_source_enabled_"
                f"{source_id}"
            ),
        )

        if source_id == "public_web":
            allowed_content = source.get(
                "allowed_content",
                [],
            )

            excluded_domains = source.get(
                "excluded_domains",
                [],
            )

            with st.expander(
                "Public Web Scope",
                expanded=False,
            ):
                st.markdown(
                    "**Allowed content types**"
                )

                for item in allowed_content:
                    st.write(
                        f"• {str(item).replace('_', ' ').title()}"
                    )

                st.markdown(
                    "**Excluded domains**"
                )

                for domain in excluded_domains:
                    st.write(
                        f"• {domain}"
                    )

                st.caption(
                    "Domain editing is not enabled in "
                    "this first UI version. Update the "
                    "YAML file directly when necessary."
                )

        if source_id == "github":
            with st.expander(
                "GitHub Scope",
                expanded=False,
            ):
                st.write(
                    "Search public users: "
                    f"{'Yes' if source.get('search_users') else 'No'}"
                )

                st.write(
                    "Search public repositories: "
                    f"{'Yes' if source.get('search_repositories') else 'No'}"
                )

        save_clicked = st.button(
            "Save Source",
            type="primary",
            use_container_width=True,
            key=(
                "save_candidate_source_"
                f"{source_id}"
            ),
        )

        if save_clicked:
            try:
                updated = update_candidate_source(
                    source_id=source_id,
                    enabled=new_enabled,
                )

                status_text = (
                    "enabled"
                    if updated.get("enabled")
                    else "disabled"
                )

                _finish_update(
                    f"{display_name} was {status_text}."
                )

            except Exception as exc:
                st.error(
                    f"Unable to update source: {exc}"
                )


def _render_global_settings(
    settings: dict,
) -> None:
    st.markdown("## Discovery Settings")

    with st.form(
        "candidate_source_global_settings_form",
        clear_on_submit=False,
    ):
        maximum_results = st.number_input(
            "Maximum results per source",
            min_value=1,
            max_value=50,
            value=int(
                settings.get(
                    "maximum_results_per_source",
                    10,
                )
            ),
            step=1,
            help=(
                "This limit applies separately to "
                "AIRS, Public Web, and GitHub."
            ),
        )

        require_import_confirmation = st.checkbox(
            "Require recruiter confirmation before import",
            value=bool(
                settings.get(
                    "require_import_confirmation",
                    True,
                )
            ),
        )

        require_authorization_confirmation = (
            st.checkbox(
                "Require authorization confirmation",
                value=bool(
                    settings.get(
                        "require_authorization_confirmation",
                        True,
                    )
                ),
            )
        )

        save_search_history = st.checkbox(
            "Save candidate discovery search history",
            value=bool(
                settings.get(
                    "save_search_history",
                    False,
                )
            ),
            help=(
                "Leave disabled until an audit-log or "
                "database-backed history is implemented."
            ),
        )

        save_clicked = st.form_submit_button(
            "Save Discovery Settings",
            type="primary",
            use_container_width=True,
        )

    if not save_clicked:
        return

    try:
        update_candidate_source_settings(
            maximum_results_per_source=int(
                maximum_results
            ),
            require_import_confirmation=(
                require_import_confirmation
            ),
            require_authorization_confirmation=(
                require_authorization_confirmation
            ),
            save_search_history=(
                save_search_history
            ),
        )

        _finish_update(
            "Candidate discovery settings were updated."
        )

    except Exception as exc:
        st.error(
            f"Unable to update settings: {exc}"
        )


def render_candidate_source_settings() -> None:
    require_permission(
        "candidate_sources.manage",
        message=(
            "Only an administrator can manage "
            "candidate discovery sources."
        ),
    )

    # st.title("Candidate Source Settings")

    st.caption(
        "Choose which sources the AI Recruiter may "
        "search when discovering candidates."
    )

    # st.warning(
        # "External prospects remain separate from AIRS "
        # "candidates until a recruiter reviews and "
        # "confirms an import."
    # )

    _show_saved_message()

    try:
        config = load_candidate_source_config()
    except Exception as exc:
        st.error(
            "Unable to load candidate source "
            f"configuration: {exc}"
        )
        return

    sources = config["sources"]
    settings = config["settings"]

    enabled_count = sum(
        bool(source.get("enabled"))
        for source in sources.values()
    )

    metric_col1, metric_col2, metric_col3 = (
        st.columns(3)
    )

    metric_col1.metric(
        "Configured Sources",
        len(sources),
    )

    metric_col2.metric(
        "Enabled Sources",
        enabled_count,
    )

    metric_col3.metric(
        "Results Per Source",
        settings.get(
            "maximum_results_per_source",
            10,
        ),
    )

    st.divider()
    st.markdown("## Candidate Sources")

    for source_id in SOURCE_ORDER:
        source = sources.get(source_id)

        if source is None:
            continue

        _render_source_card(
            source_id,
            source,
        )

    other_source_ids = [
        source_id
        for source_id in sources
        if source_id not in SOURCE_ORDER
    ]

    for source_id in other_source_ids:
        _render_source_card(
            source_id,
            sources[source_id],
        )

    st.divider()

    _render_global_settings(
        settings
    )