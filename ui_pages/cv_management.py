import streamlit as st

from components.candidate_library import (
    render_candidate_library,
)
from components.create_candidate_dialog import (
    show_create_candidate_dialog,
)
from services.permission_service import (
    has_permission,
    require_permission,
)

def render_cv_management() -> None:
    message = st.session_state.pop(
        "candidate_created_message",
        None,
    )

    if message:
        st.success(message)

    action_col, spacer_col = st.columns(
        [1, 4]
    )

    with action_col:
        can_create_candidate = has_permission(
            "candidate.create"
        )

        add_clicked = st.button(
            "＋ Add",
            type="primary",
            use_container_width=True,
            key="open_create_candidate_dialog",
            disabled=not can_create_candidate,
            help=(
                None
                if can_create_candidate
                else (
                    "Your role has read-only access "
                    "to candidate records."
                )
            ),
        )

        if add_clicked:
            require_permission(
                "candidate.create",
                message=(
                    "You do not have permission to "
                    "create candidate records."
                ),
            )

            show_create_candidate_dialog()

    # st.divider()

    render_candidate_library()