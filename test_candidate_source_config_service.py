from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from services.candidate_source_config_service import (
    get_candidate_source,
    get_enabled_candidate_sources,
    is_candidate_source_enabled,
    load_candidate_source_config,
    update_candidate_source,
    update_candidate_source_settings,
)


def build_test_config() -> dict:
    return {
        "sources": {
            "internal_airs": {
                "enabled": True,
                "display_name": "AIRS Candidate Database",
                "source_type": "internal",
            },
            "public_web": {
                "enabled": True,
                "display_name": "Public Web",
                "source_type": "tavily",
                "excluded_domains": [
                    "linkedin.com",
                ],
            },
            "github": {
                "enabled": False,
                "display_name": "GitHub",
                "source_type": "github",
                "search_users": True,
                "search_repositories": True,
            },
        },
        "settings": {
            "maximum_results_per_source": 8,
            "require_import_confirmation": True,
            "require_authorization_confirmation": True,
            "save_search_history": False,
        },
    }


def main() -> None:
    with TemporaryDirectory() as directory:
        config_path = (
            Path(directory)
            / "candidate_sources.yaml"
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

        config = load_candidate_source_config(
            config_path
        )

        assert (
            config["settings"]
            ["maximum_results_per_source"]
            == 8
        )

        enabled = get_enabled_candidate_sources(
            config_path
        )

        assert {
            source["source_id"]
            for source in enabled
        } == {
            "internal_airs",
            "public_web",
        }

        assert is_candidate_source_enabled(
            "internal_airs",
            config_path,
        )

        assert not is_candidate_source_enabled(
            "github",
            config_path,
        )

        github = update_candidate_source(
            source_id="github",
            enabled=True,
            config_path=config_path,
        )

        assert github["enabled"]

        assert is_candidate_source_enabled(
            "github",
            config_path,
        )

        settings = (
            update_candidate_source_settings(
                maximum_results_per_source=12,
                save_search_history=True,
                config_path=config_path,
            )
        )

        assert (
            settings[
                "maximum_results_per_source"
            ]
            == 12
        )
        assert settings[
            "save_search_history"
        ]

        public_web = get_candidate_source(
            "public_web",
            config_path,
        )

        assert (
            public_web["source_type"]
            == "tavily"
        )

        print(
            "[PASSED] Candidate source configuration "
            "service tests passed."
        )


if __name__ == "__main__":
    main()