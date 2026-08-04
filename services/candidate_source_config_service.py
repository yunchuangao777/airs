from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import yaml


CANDIDATE_SOURCE_CONFIG_PATH = Path(
    "config/candidate_sources.yaml"
)

SUPPORTED_SOURCE_TYPES = {
    "internal",
    "tavily",
    "github",
}

DEFAULT_SETTINGS = {
    "maximum_results_per_source": 10,
    "require_import_confirmation": True,
    "require_authorization_confirmation": True,
    "save_search_history": False,
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_source_id(source_id: str) -> str:
    return _clean_text(source_id).lower()


def load_candidate_source_config(
    config_path: Path = CANDIDATE_SOURCE_CONFIG_PATH,
) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(
            "Candidate source configuration was not found: "
            f"{config_path}"
        )

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError(
            "Candidate source configuration must be a YAML mapping."
        )

    sources = config.get("sources")

    if not isinstance(sources, dict) or not sources:
        raise ValueError(
            "The configuration must contain at least one candidate source."
        )

    normalized_sources: dict[str, dict] = {}

    for raw_source_id, raw_source in sources.items():
        source_id = _normalize_source_id(
            raw_source_id
        )

        if not source_id:
            raise ValueError(
                "Candidate source IDs cannot be empty."
            )

        if not isinstance(raw_source, dict):
            raise ValueError(
                f"Candidate source '{source_id}' must be a mapping."
            )

        source_type = _clean_text(
            raw_source.get("source_type")
        ).lower()

        if source_type not in SUPPORTED_SOURCE_TYPES:
            raise ValueError(
                f"Unsupported source type '{source_type}' "
                f"for source '{source_id}'."
            )

        display_name = _clean_text(
            raw_source.get("display_name")
        )

        if not display_name:
            raise ValueError(
                f"Candidate source '{source_id}' needs a display_name."
            )

        normalized_source = deepcopy(
            raw_source
        )
        normalized_source["enabled"] = bool(
            raw_source.get("enabled", False)
        )
        normalized_source["source_type"] = source_type
        normalized_source["display_name"] = display_name

        normalized_sources[
            source_id
        ] = normalized_source

    settings = dict(DEFAULT_SETTINGS)
    raw_settings = config.get("settings")

    if isinstance(raw_settings, dict):
        settings.update(raw_settings)

    maximum_results = int(
        settings.get(
            "maximum_results_per_source",
            10,
        )
    )

    if not 1 <= maximum_results <= 50:
        raise ValueError(
            "maximum_results_per_source must be between 1 and 50."
        )

    settings[
        "maximum_results_per_source"
    ] = maximum_results

    for field_name in [
        "require_import_confirmation",
        "require_authorization_confirmation",
        "save_search_history",
    ]:
        settings[field_name] = bool(
            settings.get(
                field_name,
                DEFAULT_SETTINGS[field_name],
            )
        )

    return {
        "sources": normalized_sources,
        "settings": settings,
    }


def save_candidate_source_config(
    config: dict,
    config_path: Path = CANDIDATE_SOURCE_CONFIG_PATH,
) -> None:
    validated = _validate_config_for_save(
        config
    )

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
            validated,
            temporary_file,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

        temporary_path = Path(
            temporary_file.name
        )

    temporary_path.replace(
        config_path
    )


def _validate_config_for_save(
    config: dict,
) -> dict:
    if not isinstance(config, dict):
        raise ValueError(
            "Candidate source configuration must be a mapping."
        )

    # Validate by writing to an in-memory-like temporary structure.
    sources = config.get("sources")
    settings = config.get("settings", {})

    if not isinstance(sources, dict):
        raise ValueError(
            "Candidate source configuration requires a sources mapping."
        )

    normalized = {
        "sources": deepcopy(sources),
        "settings": deepcopy(settings),
    }

    for source_id, source in normalized["sources"].items():
        if not isinstance(source, dict):
            raise ValueError(
                f"Candidate source '{source_id}' must be a mapping."
            )

        source_type = _clean_text(
            source.get("source_type")
        ).lower()

        if source_type not in SUPPORTED_SOURCE_TYPES:
            raise ValueError(
                f"Unsupported source type: {source_type}"
            )

        source["enabled"] = bool(
            source.get("enabled", False)
        )

    maximum_results = int(
        normalized["settings"].get(
            "maximum_results_per_source",
            DEFAULT_SETTINGS[
                "maximum_results_per_source"
            ],
        )
    )

    if not 1 <= maximum_results <= 50:
        raise ValueError(
            "maximum_results_per_source must be between 1 and 50."
        )

    normalized["settings"][
        "maximum_results_per_source"
    ] = maximum_results

    for field_name in [
        "require_import_confirmation",
        "require_authorization_confirmation",
        "save_search_history",
    ]:
        normalized["settings"][field_name] = bool(
            normalized["settings"].get(
                field_name,
                DEFAULT_SETTINGS[field_name],
            )
        )

    return normalized


def get_enabled_candidate_sources(
    config_path: Path = CANDIDATE_SOURCE_CONFIG_PATH,
) -> list[dict]:
    config = load_candidate_source_config(
        config_path
    )

    return [
        {
            "source_id": source_id,
            **deepcopy(source),
        }
        for source_id, source in config[
            "sources"
        ].items()
        if source.get("enabled")
    ]


def get_candidate_source(
    source_id: str,
    config_path: Path = CANDIDATE_SOURCE_CONFIG_PATH,
) -> dict | None:
    config = load_candidate_source_config(
        config_path
    )

    normalized_source_id = (
        _normalize_source_id(
            source_id
        )
    )

    source = config["sources"].get(
        normalized_source_id
    )

    if source is None:
        return None

    return {
        "source_id": normalized_source_id,
        **deepcopy(source),
    }


def is_candidate_source_enabled(
    source_id: str,
    config_path: Path = CANDIDATE_SOURCE_CONFIG_PATH,
) -> bool:
    source = get_candidate_source(
        source_id,
        config_path,
    )

    return bool(
        source
        and source.get("enabled")
    )


def update_candidate_source(
    *,
    source_id: str,
    enabled: bool | None = None,
    display_name: str | None = None,
    config_path: Path = CANDIDATE_SOURCE_CONFIG_PATH,
) -> dict:
    config = load_candidate_source_config(
        config_path
    )

    normalized_source_id = (
        _normalize_source_id(
            source_id
        )
    )

    if normalized_source_id not in config[
        "sources"
    ]:
        raise ValueError(
            f"Candidate source was not found: {source_id}"
        )

    source = config["sources"][
        normalized_source_id
    ]

    if enabled is not None:
        source["enabled"] = bool(
            enabled
        )

    if display_name is not None:
        cleaned_name = _clean_text(
            display_name
        )

        if not cleaned_name:
            raise ValueError(
                "display_name cannot be empty."
            )

        source["display_name"] = (
            cleaned_name
        )

    save_candidate_source_config(
        config,
        config_path,
    )

    return {
        "source_id": normalized_source_id,
        **deepcopy(source),
    }


def update_candidate_source_settings(
    *,
    maximum_results_per_source: int | None = None,
    require_import_confirmation: bool | None = None,
    require_authorization_confirmation: bool | None = None,
    save_search_history: bool | None = None,
    config_path: Path = CANDIDATE_SOURCE_CONFIG_PATH,
) -> dict:
    config = load_candidate_source_config(
        config_path
    )

    settings = config["settings"]

    if maximum_results_per_source is not None:
        maximum_results = int(
            maximum_results_per_source
        )

        if not 1 <= maximum_results <= 50:
            raise ValueError(
                "maximum_results_per_source must be "
                "between 1 and 50."
            )

        settings[
            "maximum_results_per_source"
        ] = maximum_results

    optional_boolean_updates = {
        "require_import_confirmation": (
            require_import_confirmation
        ),
        "require_authorization_confirmation": (
            require_authorization_confirmation
        ),
        "save_search_history": (
            save_search_history
        ),
    }

    for field_name, value in (
        optional_boolean_updates.items()
    ):
        if value is not None:
            settings[field_name] = bool(
                value
            )

    save_candidate_source_config(
        config,
        config_path,
    )

    return deepcopy(settings)