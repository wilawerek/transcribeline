import os
import json
import tomllib
import logging
from pathlib import Path
from types import SimpleNamespace

def load_config(config_path: str) -> SimpleNamespace:
    """
    Load and parse the TOML configuration file into a SimpleNamespace for dot-notation access.
    """
    with open(config_path, "rb") as f:
        config_dict = tomllib.load(f)
    return dict_to_namespace(config_dict)

def dict_to_namespace(d: dict) -> SimpleNamespace:
    """
    Recursively convert a dictionary to a SimpleNamespace.
    """
    ns = SimpleNamespace()
    for key, value in d.items():
        if isinstance(value, dict):
            setattr(ns, key, dict_to_namespace(value))
        else:
            setattr(ns, key, value)
    return ns

def load_substitutions(path: str) -> dict:
    """
    Load substitution rules from a JSON file.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def setup_logger(name: str = "pipeline") -> logging.Logger:
    """
    Configure and return a logger with ASCII-only formatting.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
