from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

AUTH_CONFIG_PATH = Path(
    os.getenv(
        "AIRS_AUTH_CONFIG_PATH",
        (
            "/etc/secrets/auth_config.yaml"
            if Path(
                "/etc/secrets/auth_config.yaml"
            ).exists()
            else "config/auth_config.yaml"
        ),
    )
)


def load_auth_config(
    config_path: Path = AUTH_CONFIG_PATH,
) -> dict:
    """Load the invite-only AIRS authentication config."""
    if not config_path.exists():
        raise FileNotFoundError(
            f"Authentication configuration was not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.load(file, Loader=SafeLoader)

    if not isinstance(config, dict):
        raise ValueError(
            "Authentication configuration must be a YAML mapping."
        )

    credentials = config.get("credentials")
    cookie = config.get("cookie")

    if not isinstance(credentials, dict):
        raise ValueError(
            "Missing credentials section in authentication configuration."
        )

    if not isinstance(cookie, dict):
        raise ValueError(
            "Missing cookie section in authentication configuration."
        )

    required_cookie_fields = {"name", "key", "expiry_days"}
    missing_cookie_fields = required_cookie_fields - set(cookie.keys())

    if missing_cookie_fields:
        raise ValueError(
            "Missing cookie configuration fields: "
            f"{sorted(missing_cookie_fields)}"
        )

    usernames = credentials.get("usernames")

    if not isinstance(usernames, dict):
        raise ValueError(
            "credentials.usernames must be a mapping."
        )

    return config


def create_authenticator(
    config: dict,
) -> stauth.Authenticate:
    """Create the Streamlit-Authenticator instance."""
    cookie = config["cookie"]

    return stauth.Authenticate(
        config["credentials"],
        cookie["name"],
        cookie["key"],
        float(cookie["expiry_days"]),
        auto_hash=False,
    )


def initialize_authentication() -> tuple[
    dict,
    stauth.Authenticate,
]:
    """
    Load configuration and create one authenticator per
    Streamlit browser session.
    """
    if "airs_auth_config" not in st.session_state:
        st.session_state["airs_auth_config"] = load_auth_config()

    config = st.session_state["airs_auth_config"]

    if "airs_authenticator" not in st.session_state:
        st.session_state["airs_authenticator"] = (
            create_authenticator(config)
        )

    return (
        config,
        st.session_state["airs_authenticator"],
    )


def get_current_user_record(
    config: dict,
) -> dict | None:
    """Return the authenticated user's YAML record."""
    username = str(
        st.session_state.get("username", "") or ""
    ).strip()

    if not username:
        return None

    return (
        config.get("credentials", {})
        .get("usernames", {})
        .get(username)
    )


def get_user_role(
    user_record: dict | None,
) -> str:
    """
    Support either `role: recruiter` or
    `roles: [recruiter]`.
    """
    if not user_record:
        return ""

    direct_role = str(
        user_record.get("role", "") or ""
    ).strip().lower()

    if direct_role:
        return direct_role

    roles = user_record.get("roles")

    if isinstance(roles, list) and roles:
        return str(roles[0]).strip().lower()

    return ""


def is_user_active(
    user_record: dict | None,
) -> bool:
    """Users are active unless explicitly disabled."""
    if not user_record:
        return False

    return bool(user_record.get("is_active", True))


def render_login_page(
    authenticator: stauth.Authenticate,
) -> None:
    """Render only the staff login form."""
    st.markdown(
        """
        <style>
        /* Login username and password fields */
        div[data-testid="stTextInput"]
        div[data-baseweb="input"] {
            border: 2px solid rgba(120, 120, 120, 0.55) !important;
            border-radius: 10px !important;
            background-color: var(--background-color, #ffffff) !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06) !important;
        }

        div[data-testid="stTextInput"]
        div[data-baseweb="input"]:focus-within {
            border-color: #2e7d5a !important;
            box-shadow: 0 0 0 2px rgba(46, 125, 90, 0.18) !important;
        }

        div[data-testid="stTextInput"]
        div[data-baseweb="input"] > div {
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }

        div[data-testid="stTextInput"] input {
            padding-top: 0.65rem !important;
            padding-bottom: 0.65rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("AIRS Staff Login")

    st.caption(
        "This application is restricted to invited HR "
        "team members and approved testers."
    )

    try:
        authenticator.login(
            location="main",
            max_login_attempts=5,
            single_session=False,
            clear_on_submit=False,
            key="airs_staff_login",
        )
    except Exception as exc:
        st.error(f"Unable to load login form: {exc}")
        return

    authentication_status = st.session_state.get(
        "authentication_status"
    )

    if authentication_status is False:
        st.error("The username or password is incorrect.")

    elif authentication_status is None:
        st.info(
            "Enter the username and password supplied by "
            "the AIRS administrator."
        )


def require_staff_authentication(
    config: dict,
    authenticator: stauth.Authenticate,
) -> dict | None:
    """
    Render login when necessary and return the active
    approved user record after successful login.
    """
    if not st.session_state.get("authentication_status"):
        render_login_page(authenticator)
        return None

    user_record = get_current_user_record(config)

    if user_record is None:
        st.error(
            "Your account is not present in the AIRS "
            "approved-user list."
        )

        authenticator.logout(
            button_name="Sign out",
            location="main",
            key="unknown_user_logout",
        )
        return None

    if not is_user_active(user_record):
        st.error(
            "This AIRS account has been disabled. Please "
            "contact the administrator."
        )

        authenticator.logout(
            button_name="Sign out",
            location="main",
            key="disabled_user_logout",
        )
        return None

    role = get_user_role(user_record)

    if not role:
        st.error(
            "No AIRS role has been assigned to this account."
        )
        return None

    st.session_state["current_user_role"] = role
    st.session_state["current_user_record"] = user_record

    return user_record


def render_sidebar_user_panel(
    authenticator: stauth.Authenticate,
    user_record: dict,
) -> None:
    """Show the signed-in user and logout control."""
    first_name = str(
        user_record.get("first_name", "") or ""
    ).strip()

    last_name = str(
        user_record.get("last_name", "") or ""
    ).strip()

    display_name = " ".join(
        part for part in [first_name, last_name] if part
    )

    if not display_name:
        display_name = str(
            st.session_state.get("name", "")
            or st.session_state.get("username", "User")
        )

    role = get_user_role(user_record)

    st.sidebar.divider()
    st.sidebar.caption(f"Signed in as {display_name}")
    st.sidebar.caption(
        f"Role: {role.replace('_', ' ').title()}"
    )

    authenticator.logout(
        button_name="Logout",
        location="sidebar",
        key="airs_sidebar_logout",
        use_container_width=True,
    )