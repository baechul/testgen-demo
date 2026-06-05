from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "environments.yaml"

# Note that Environment is the immutable read-only dataclass once created.
@dataclass(frozen=True)
class Environment:
    name: str
    base_url: str
    max_response_time: float
    min_results_count: int
    headers: dict[str, str] = field(default_factory=dict)


def _expand_env_vars(headers: dict[str, str]) -> dict[str, str]:
    return {
        k: re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), m.group(0)), v)
        for k, v in headers.items()
    }


def load_environments() -> dict[str, dict[str, Any]]:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        msg = f"Expected a mapping at the root of {CONFIG_PATH}"
        raise ValueError(msg)

    return data


def resolve_environment(name: str) -> Environment:
    """ The central way of getting the Environment configuration 
        It provides the central way of properly loading the given environment 
        from the config/environments.yaml 
    """
    config = load_environments()

    if name not in config:
        available = ", ".join(sorted(config))
        msg = f"Unknown environment {name!r}. Choose from: {available}"
        raise KeyError(msg)

    entry = config[name]
    if not isinstance(entry, dict):
        msg = f"Environment {name!r} must be a mapping in {CONFIG_PATH}"
        raise ValueError(msg)

    required = ("base_url", "max_response_time", "min_results_count")
    missing = [key for key in required if key not in entry]
    if missing:
        msg = f"Environment {name!r} is missing keys: {', '.join(missing)}"
        raise ValueError(msg)

    raw_headers = entry.get("headers") or {}
    return Environment(
        name=name,
        base_url=str(entry["base_url"]),
        max_response_time=float(entry["max_response_time"]),
        min_results_count=int(entry["min_results_count"]),
        headers=_expand_env_vars(raw_headers),
    )
