from __future__ import annotations

import pandas as pd
import streamlit as st

from services.permission_service import require_permission
from services.user_management_service import (
    add_user,
    list_users,
    reset_user_password,
    update_user,
)


ROLE_OPTIONS = [
    "admin",
    "recruiter",
    "interviewer",
    "viewer",
]


def _refresh_authentication_cache() -> None:
    st.session_state.pop("airs_auth_config", None)
    st.session_state.pop("airs_authenticator", None)


def _finish_user_change(message: str) -> None:
    _refresh_authentication_cache()
    st.session_state["user_management_message"] = message
    st.rerun()


@st.dialog("Add AIRS User", width="large")
def show_add_user_dialog() -> None:
    require_permission(
        "user.manage",
        message="Only an administrator can add users.",
    )

    st.caption(
        "Create an invite-only account. There is no public registration."
    )

    with st.form("add_airs_user_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input(
                "Username *",
                placeholder="example: jane_recruiter",
            )
            first_name = st.text_input("First name")
            email = st.text_input("Email")

        with col2:
            role = st.selectbox(
                "Role *",
                options=ROLE_OPTIONS,
                index=1,
                format_func=lambda value: value.title(),
            )
            last_name = st.text_input("Last name")
            is_active = st.checkbox("Active account", value=True)

        password = st.text_input(
            "Temporary password *",
            type="password",
            help=(
                "Use at least 8 characters. Send the password "
                "through a private channel."
            ),
        )
        confirm_password = st.text_input(
            "Confirm temporary password *",
            type="password",
        )

        submitted = st.form_submit_button(
            "Create User",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    if not username.strip():
        st.warning("Username is required.")
        return

    if password != confirm_password:
        st.warning("The password confirmation does not match.")
        return

    try:
        created = add_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            is_active=is_active,
        )
        _finish_user_change(
            f"User '{created['username']}' was created."
        )
    except Exception as exc:
        st.error(f"Unable to create user: {exc}")


@st.dialog("Edit AIRS User", width="large")
def show_edit_user_dialog(user: dict) -> None:
    require_permission(
        "user.manage",
        message="Only an administrator can edit users.",
    )

    username = str(user.get("username") or "")
    current_username = str(
        st.session_state.get("username", "") or ""
    ).strip().lower()
    editing_self = username.strip().lower() == current_username

    st.text_input("Username", value=username, disabled=True)

    with st.form(
        f"edit_airs_user_form_{username}",
        clear_on_submit=False,
    ):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input(
                "First name",
                value=str(user.get("first_name") or ""),
            )
            email = st.text_input(
                "Email",
                value=str(user.get("email") or ""),
            )

        with col2:
            last_name = st.text_input(
                "Last name",
                value=str(user.get("last_name") or ""),
            )

            current_role = str(
                user.get("role") or "viewer"
            ).lower()
            role_index = (
                ROLE_OPTIONS.index(current_role)
                if current_role in ROLE_OPTIONS
                else ROLE_OPTIONS.index("viewer")
            )

            role = st.selectbox(
                "Role",
                options=ROLE_OPTIONS,
                index=role_index,
                format_func=lambda value: value.title(),
                disabled=editing_self,
                help=(
                    "You cannot change your own role from this page."
                    if editing_self
                    else None
                ),
            )

        is_active = st.checkbox(
            "Active account",
            value=bool(user.get("is_active", True)),
            disabled=editing_self,
            help=(
                "You cannot disable your own account."
                if editing_self
                else None
            ),
        )

        submitted = st.form_submit_button(
            "Save User",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    try:
        updated = update_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=current_role if editing_self else role,
            is_active=(
                bool(user.get("is_active", True))
                if editing_self
                else is_active
            ),
        )
        _finish_user_change(
            f"User '{updated['username']}' was updated."
        )
    except Exception as exc:
        st.error(f"Unable to update user: {exc}")


@st.dialog("Reset User Password", width="small")
def show_reset_password_dialog(user: dict) -> None:
    require_permission(
        "user.manage",
        message="Only an administrator can reset passwords.",
    )

    username = str(user.get("username") or "")
    st.write(f"Reset the password for **{username}**.")

    with st.form(
        f"reset_user_password_form_{username}",
        clear_on_submit=False,
    ):
        new_password = st.text_input(
            "New temporary password",
            type="password",
        )
        confirm_password = st.text_input(
            "Confirm new password",
            type="password",
        )
        submitted = st.form_submit_button(
            "Reset Password",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    if new_password != confirm_password:
        st.warning("The password confirmation does not match.")
        return

    try:
        reset_user_password(
            username=username,
            new_password=new_password,
        )
        _finish_user_change(
            f"Password for '{username}' was reset."
        )
    except Exception as exc:
        st.error(f"Unable to reset password: {exc}")


def _render_user_summary(users: list[dict]) -> None:
    total_users = len(users)
    active_users = sum(
        bool(user.get("is_active")) for user in users
    )
    admin_users = sum(
        str(user.get("role")).lower() == "admin"
        for user in users
    )
    disabled_users = total_users - active_users

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Users", total_users)
    col2.metric("Active", active_users)
    col3.metric("Administrators", admin_users)
    col4.metric("Disabled", disabled_users)


def _render_user_table(users: list[dict]) -> dict | None:
    table_rows = [
        {
            "Username": user["username"],
            "Name": user.get("display_name") or "Not specified",
            "Email": user.get("email") or "Not specified",
            "Role": str(user.get("role") or "")
            .replace("_", " ")
            .title(),
            "Status": (
                "Active" if user.get("is_active") else "Disabled"
            ),
        }
        for user in users
    ]

    dataframe = pd.DataFrame(table_rows)

    event = st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="user_management_table",
    )

    selected_rows = event.selection.rows
    if not selected_rows:
        return None

    selected_index = selected_rows[0]
    if selected_index >= len(users):
        return None

    return users[selected_index]


def render_user_management() -> None:
    require_permission(
        "user.manage",
        message=(
            "Only an administrator can access User Management."
        ),
    )

    # st.title("User Management")

    st.caption(
        "Manage invite-only AIRS staff accounts, roles, "
        "access status, and passwords."
    )

    message = st.session_state.pop(
        "user_management_message",
        None,
    )
    if message:
        st.success(message)

    try:
        users = list_users()
    except Exception as exc:
        st.error(f"Unable to load AIRS users: {exc}")
        return

    _render_user_summary(users)
    st.divider()

    action_col, info_col = st.columns([1, 4])

    with action_col:
        if st.button(
            "＋ Add User",
            type="primary",
            use_container_width=True,
            key="open_add_user_dialog",
        ):
            show_add_user_dialog()

    # with info_col:
        # st.info(
            # "Accounts are created only by an administrator. "
            # "Public registration is not available."
        # )

    st.divider()
    st.markdown("### Users")

    selected_user = _render_user_table(users)

    if selected_user is None:
        st.caption(
            "Select a user row to edit the account or reset its password."
        )
        return

    st.markdown(
        f"#### Selected User: {selected_user['username']}"
    )

    edit_col, password_col, _ = st.columns([1, 1, 3])

    with edit_col:
        if st.button(
            "Edit User",
            use_container_width=True,
            key=f"edit_user_{selected_user['username']}",
        ):
            show_edit_user_dialog(selected_user)

    with password_col:
        if st.button(
            "Reset Password",
            use_container_width=True,
            key=f"reset_password_{selected_user['username']}",
        ):
            show_reset_password_dialog(selected_user)