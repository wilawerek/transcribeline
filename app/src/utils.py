import json
import logging
import tomllib
from pathlib import Path
from types import SimpleNamespace

from pydub import AudioSegment


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


def setup_logger(module_name: str = "pipeline", log_path: str = "transcribeline.log") -> logging.Logger:
    """
    Configure and return a logger that logs both to the console and a file.
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(f"[{module_name}] %(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    # Path(log_dir).mkdir(parents=True, exist_ok=True)
    # file_handler = logging.FileHandler(Path(log_dir) / f"{module_name}.log")
    file_handler = logging.FileHandler(log_path)
    file_formatter = logging.Formatter(f"%(asctime)s [{module_name}] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def estimate_silence_threshold(audio_path: str, offset_db: float = -10.0) -> float:
    """
    Estimate a dynamic silence threshold based on the average loudness of the audio file.

    Parameters:
        audio_path (str): Path to the audio file.
        offset_db (float): How many dB quieter than the average should count as silence.

    Returns:
        float: Estimated silence threshold in dBFS.
    """
    audio = AudioSegment.from_file(audio_path)
    average_loudness = audio.dBFS
    return average_loudness + offset_db  # offset_db is negative
