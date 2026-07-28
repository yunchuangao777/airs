import streamlit as st

from components.candidate_library import (
    render_candidate_library,
)
from components.create_candidate_dialog import (
    show_create_candidate_dialog,
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
        if st.button(
            "＋ Create New Candidate",
            type="primary",
            use_container_width=True,
            key="open_create_candidate_dialog",
        ):
            show_create_candidate_dialog()

    st.divider()

    render_candidate_library()