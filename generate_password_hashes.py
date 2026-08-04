from __future__ import annotations

import getpass

import streamlit_authenticator as stauth


def main() -> None:
    password = getpass.getpass(
        "Enter the password to hash: "
    )

    if not password:
        raise ValueError(
            "Password cannot be empty."
        )

    hashed_password = stauth.Hasher.hash(
        password
    )

    print("\nPassword hash:")
    print(hashed_password)


if __name__ == "__main__":
    main()