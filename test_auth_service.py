from __future__ import annotations

from services.auth_service import (
    create_authenticator,
    get_user_role,
    is_user_active,
    load_auth_config,
)


def main() -> None:
    config = load_auth_config()

    usernames = config["credentials"]["usernames"]

    print("=" * 60)
    print("AIRS Authentication Configuration Test")
    print("=" * 60)

    print(f"Configured users: {len(usernames)}")

    for username, record in usernames.items():
        print("-" * 60)
        print("Username:", username)
        print("Role:", get_user_role(record))
        print("Active:", is_user_active(record))
        print(
            "Has password hash:",
            bool(record.get("password")),
        )

    create_authenticator(config)

    print("-" * 60)
    print(
        "[PASSED] Authentication configuration and "
        "authenticator are valid."
    )


if __name__ == "__main__":
    main()