import streamlit as st


DEFAULT_PAGE = "CV Management"


def render_nav_button(
    display_name: str,
    page_name: str,
) -> None:
    current_page = st.session_state.get(
        "current_page",
        DEFAULT_PAGE,
    )

    is_selected = current_page == page_name

    icon = "🟩" if is_selected else "⬜"

    if st.sidebar.button(
        display_name,
        key=f"nav_{page_name}",
        use_container_width=True,
        type="tertiary",
        icon=icon,
    ):
        if not is_selected:
            st.session_state["current_page"] = page_name
            st.rerun()