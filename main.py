import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {
        "true", "1", "yes", "on"
    }


def coerce(key, value):
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


def load_config():
    config = DEFAULTS.copy()

    env_name = os.getenv("APP_ENV", "development")
    yaml_file = Path(f"config.{env_name}.yaml")

    if yaml_file.exists():
        with yaml_file.open(encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
        config.update(yaml_config)

    dotenv_config = dotenv_values(".env")

    env_mapping = {
        "APP_PORT": "port",
        "NUM_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, config_key in env_mapping.items():
        if dotenv_config.get(env_key) is not None:
            config[config_key] = dotenv_config[env_key]

    os_mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, config_key in os_mapping.items():
        if env_key in os.environ:
            config[config_key] = os.environ[env_key]

    for key in config:
        config[key] = coerce(key, config[key])

    return config


@app.get("/effective-config")
def effective_config(
    set: list[str] = Query(default=[])
):
    config = load_config()

    for override in set:
        if "=" not in override:
            continue

        key, value = override.split("=", 1)

        if key in config:
            config[key] = coerce(key, value)

    config["api_key"] = "****"
    return config