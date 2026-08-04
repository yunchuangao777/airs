from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import bcrypt
import yaml
from yaml.loader import SafeLoader

from services.permission_service import require_permission


AUTH_CONFIG_PATH = Path("config/auth_config.yaml")

VALID_ROLES = {
    "admin",
    "recruiter",
    "interviewer",
    "viewer",
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_username(username: str) -> str:
    return _clean_text(username).lower()


def _normalize_role(role: str) -> str:
    return _clean_text(role).lower()


def load_user_config(
    config_path: Path = AUTH_CONFIG_PATH,
) -> dict:
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
        raise ValueError("Missing credentials section.")

    usernames = credentials.get("usernames")

    if not isinstance(usernames, dict):
        raise ValueError(
            "credentials.usernames must be a mapping."
        )

    if not isinstance(cookie, dict):
        raise ValueError("Missing cookie configuration.")

    return config


def save_user_config(
    config: dict,
    config_path: Path = AUTH_CONFIG_PATH,
) -> None:
    config_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=config_path.parent,
        prefix=f"{config_path.stem}_",
        suffix=".tmp",
        delete=False,
    ) as temporary_file:
        yaml.safe_dump(
            config,
            temporary_file,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

        temporary_path = Path(temporary_file.name)

    temporary_path.replace(config_path)


def list_users(
    config_path: Path = AUTH_CONFIG_PATH,
) -> list[dict]:
    config = load_user_config(config_path)
    usernames = config["credentials"]["usernames"]

    users = []

    for username, record in usernames.items():
        first_name = _clean_text(record.get("first_name"))
        last_name = _clean_text(record.get("last_name"))

        role_value = record.get("role")

        if not role_value:
            roles = record.get("roles")
            if isinstance(roles, list) and roles:
                role_value = roles[0]

        users.append(
            {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "display_name": " ".join(
                    part
                    for part in [first_name, last_name]
                    if part
                ),
                "email": _clean_text(record.get("email")),
                "role": _normalize_role(role_value),
                "is_active": bool(
                    record.get("is_active", True)
                ),
            }
        )

    return sorted(
        users,
        key=lambda user: user["username"].lower(),
    )


def hash_password(plain_password: str) -> str:
    password = str(plain_password or "")

    if len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def add_user(
    *,
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    email: str,
    role: str,
    is_active: bool = True,
    config_path: Path = AUTH_CONFIG_PATH,
    enforce_permission: bool = True,
) -> dict:
    if enforce_permission:
        require_permission(
            "user.manage",
            message="Only an administrator can add AIRS users.",
        )

    normalized_username = _normalize_username(username)
    normalized_role = _normalize_role(role)

    if not normalized_username:
        raise ValueError("Username is required.")

    if any(
        character.isspace()
        for character in normalized_username
    ):
        raise ValueError("Username cannot contain spaces.")

    if normalized_role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}")

    config = load_user_config(config_path)
    usernames = config["credentials"]["usernames"]

    if normalized_username in usernames:
        raise ValueError("That username already exists.")

    usernames[normalized_username] = {
        "email": _clean_text(email),
        "first_name": _clean_text(first_name),
        "last_name": _clean_text(last_name),
        "password": hash_password(password),
        "role": normalized_role,
        "is_active": bool(is_active),
    }

    save_user_config(config, config_path)

    return {
        "username": normalized_username,
        "role": normalized_role,
        "is_active": bool(is_active),
    }


def update_user(
    *,
    username: str,
    first_name: str,
    last_name: str,
    email: str,
    role: str,
    is_active: bool,
    config_path: Path = AUTH_CONFIG_PATH,
    enforce_permission: bool = True,
) -> dict:
    if enforce_permission:
        require_permission(
            "user.manage",
            message="Only an administrator can update AIRS users.",
        )

    normalized_username = _normalize_username(username)
    normalized_role = _normalize_role(role)

    if normalized_role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}")

    config = load_user_config(config_path)
    usernames = config["credentials"]["usernames"]

    if normalized_username not in usernames:
        raise ValueError("User was not found.")

    record = usernames[normalized_username]
    record["first_name"] = _clean_text(first_name)
    record["last_name"] = _clean_text(last_name)
    record["email"] = _clean_text(email)
    record["role"] = normalized_role
    record["is_active"] = bool(is_active)
    record.pop("roles", None)

    save_user_config(config, config_path)

    return {
        "username": normalized_username,
        "role": normalized_role,
        "is_active": bool(is_active),
    }


def reset_user_password(
    *,
    username: str,
    new_password: str,
    config_path: Path = AUTH_CONFIG_PATH,
    enforce_permission: bool = True,
) -> None:
    if enforce_permission:
        require_permission(
            "user.manage",
            message="Only an administrator can reset AIRS passwords.",
        )

    normalized_username = _normalize_username(username)

    config = load_user_config(config_path)
    usernames = config["credentials"]["usernames"]

    if normalized_username not in usernames:
        raise ValueError("User was not found.")

    usernames[normalized_username]["password"] = (
        hash_password(new_password)
    )

    save_user_config(config, config_path)