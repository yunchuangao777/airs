from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import bcrypt
import yaml

from services.user_management_service import (
    VALID_ROLES,
    add_user,
    list_users,
    load_user_config,
    reset_user_password,
    update_user,
)


def build_test_config() -> dict:
    return {
        "credentials": {
            "usernames": {
                "admin": {
                    "email": "admin@example.com",
                    "first_name": "AIRS",
                    "last_name": "Administrator",
                    "password": bcrypt.hashpw(
                        b"AdminTest123!",
                        bcrypt.gensalt(),
                    ).decode("utf-8"),
                    "role": "admin",
                    "is_active": True,
                }
            }
        },
        "cookie": {
            "name": "airs_test_cookie",
            "key": "test-cookie-key",
            "expiry_days": 1,
        },
    }


def main() -> None:
    with TemporaryDirectory() as directory:
        config_path = (
            Path(directory) / "auth_config.yaml"
        )

        with config_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            yaml.safe_dump(
                build_test_config(),
                file,
                allow_unicode=True,
                sort_keys=False,
            )

        config = load_user_config(config_path)

        assert "admin" in (
            config["credentials"]["usernames"]
        )

        added = add_user(
            username="Recruiter_One",
            password="Recruiter123!",
            first_name="Test",
            last_name="Recruiter",
            email="recruiter@example.com",
            role="recruiter",
            config_path=config_path,
            enforce_permission=False,
        )

        assert added["username"] == "recruiter_one"
        assert len(list_users(config_path)) == 2

        updated = update_user(
            username="recruiter_one",
            first_name="Updated",
            last_name="Recruiter",
            email="updated@example.com",
            role="interviewer",
            is_active=False,
            config_path=config_path,
            enforce_permission=False,
        )

        assert updated["role"] == "interviewer"
        assert not updated["is_active"]

        reset_user_password(
            username="recruiter_one",
            new_password="NewPassword123!",
            config_path=config_path,
            enforce_permission=False,
        )

        updated_config = load_user_config(config_path)

        password_hash = (
            updated_config["credentials"]
            ["usernames"]
            ["recruiter_one"]
            ["password"]
            .encode("utf-8")
        )

        assert bcrypt.checkpw(
            b"NewPassword123!",
            password_hash,
        )

        try:
            add_user(
                username="recruiter_one",
                password="AnotherPassword123!",
                first_name="Duplicate",
                last_name="User",
                email="duplicate@example.com",
                role="viewer",
                config_path=config_path,
                enforce_permission=False,
            )
        except ValueError as exc:
            assert "already exists" in str(exc)
        else:
            raise AssertionError(
                "Duplicate username was accepted."
            )

        assert VALID_ROLES == {
            "admin",
            "recruiter",
            "interviewer",
            "viewer",
        }

        print(
            "[PASSED] User management service tests passed."
        )


if __name__ == "__main__":
    main()