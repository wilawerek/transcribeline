#!/usr/bin/env python3

import argparse
import shutil
import sys
from pathlib import Path

# from config.config import DEFAULT_CONFIG_PATH
from src.aligner import cli_entry as aligner_cli_entry
from src.chunker import cli_entry as chunk_cli_entry
from src.diarizer import cli_entry as diarizer_cli_entry
from src.postprocessor import cli_entry as postprocess_cli_entry
from src.preprocessor import cli_entry as preprocess_cli_entry
from src.transcriber import cli_entry as transcribe_cli_entry
from src.utils import load_config, setup_logger

# Initialize top-level logger
logger = setup_logger("main")

# Get the absolute path to the directory containing the current script (main.py).
# Assuming main.py is at your project root, SCRIPT_DIR will be the project root.
SCRIPT_DIR = Path(__file__).resolve().parent

# Construct the absolute path to your default config template.
# This ensures it's found regardless of the current working directory.
SOURCE_CONFIG_TEMPLATE_PATH = SCRIPT_DIR / "config" / "settings.toml"

# --- CLI Entrypoint Functions for Subcommands ---


def run_generate_config(args):
    """Handles the 'generate-config' command to copy the default config file."""
    destination = Path(args.output).resolve()  # Resolve to an absolute path

    # If the provided path is a directory (or ends with a path separator),
    # append the default config filename to it.
    if destination.is_dir() or str(destination).endswith(("/", "\\")):
        destination = destination / SOURCE_CONFIG_TEMPLATE_PATH.name

    if destination.exists():
        if not args.overwrite:
            logger.error(f"Config file already exists at '{destination}'.")
            logger.info("Use --overwrite to replace it.")
            sys.exit(1)  # Exit if file exists and overwrite not specified
        else:
            logger.warning(f"Overwriting existing config file at '{destination}'.")

    # Ensure the parent directory for the destination file exists
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Check if the source template exists before attempting to copy
    if not SOURCE_CONFIG_TEMPLATE_PATH.is_file():
        logger.error(f"Error: Source config template not found at '{SOURCE_CONFIG_TEMPLATE_PATH}'")
        logger.error("Please ensure your 'settings.toml' template exists in 'config/' relative to main.py.")
        sys.exit(1)

    try:
        shutil.copy(SOURCE_CONFIG_TEMPLATE_PATH, destination)
        logger.info(f"Default config copied to: {destination}")
    except Exception as e:
        logger.error(f"Failed to copy config file to '{destination}': {e}")
        sys.exit(1)

    sys.exit(0)  # Exit successfully after generating config


def run_preprocessing(args):
    """Executes the preprocessing module."""
    logger.info("Running preprocessing module...")
    preprocess_cli_entry(args)


def run_chunking(args):
    """Executes the chunking module."""
    logger.info("Running chunking module...")
    chunk_cli_entry(args)


def run_transcribing(args):
    """Executes the transcription module."""
    logger.info("Running transcription module...")
    transcribe_cli_entry(args)


def run_diarization(args):
    """Executes the diarization module."""
    logger.info("Running diarization module...")
    diarizer_cli_entry(args)


def run_aligning(args):
    """Executes the aligning module."""
    logger.info("Running aligning module...")
    aligner_cli_entry(args)


def run_postprocessing(args):
    """Executes the postprocessing module."""
    logger.info("Running postprocessing module...")
    postprocess_cli_entry(args)


def run_merging(args):
    """Placeholder for the merging module."""
    logger.info("Running merging module...")
    # Stub for merger.py entrypoint
    pass


def main():
    parser = argparse.ArgumentParser(description="Transcription Pipeline CLI")

    # Global --config argument, accessible by all subparsers
    parser.add_argument(
        "--config",
        default="config/settings.toml",
        help="Path to the TOML config file (default: config/settings.toml)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # --- GENERATE-CONFIG Subparser ---
    gen_config_parser = subparsers.add_parser(
        "generate-config", help="Copy a default settings.toml configuration file to a specified location."
    )
    gen_config_parser.add_argument(
        "output",
        nargs="?",  # Makes this argument optional (0 or 1 occurrence)
        default=".",  # Default value if no argument is provided (current directory)
        help="Destination path (directory or full file path) for the config file. Default: current directory.",
    )
    gen_config_parser.add_argument(  # NEW: Overwrite flag
        "--overwrite",
        action="store_true",  # This makes it a boolean flag (True if present, False otherwise)
        help="Overwrite the destination file if it already exists.",
    )
    gen_config_parser.set_defaults(func=run_generate_config)

    # --- PREPROCESS Subparser ---
    preprocess_parser = subparsers.add_parser("preprocess", help="Run the audio preprocessing step.")
    preprocess_parser.add_argument(
        "--input", required=True, help="Path to the raw audio file to preprocess (e.g., WAV format)."
    )
    preprocess_parser.add_argument("--output", required=True, help="Path to save the preprocessed audio file.")
    preprocess_parser.set_defaults(func=run_preprocessing)

    # --- CHUNK Subparser ---
    chunk_parser = subparsers.add_parser("chunk", help="Run the audio chunking step.")
    chunk_parser.add_argument("--input", required=True, help="Path to the input .wav file.")
    chunk_parser.add_argument("--output", required=True, help="Directory to save audio chunks.")
    chunk_parser.set_defaults(func=run_chunking)

    # --- TRANSCRIBE Subparser ---
    transcribe_parser = subparsers.add_parser("transcribe", help="Run the transcription step.")
    transcribe_parser.add_argument(
        "--input", required=True, nargs="+", help="Path(s) to input .wav files or directories."
    )
    transcribe_parser.add_argument("--output", required=True, help="Directory to save transcription JSON files.")
    transcribe_parser.set_defaults(func=run_transcribing)

    # --- DIARIZE Subparser ---
    diarizer_parser = subparsers.add_parser("diarize", help="Run the speaker diarization step.")
    diarizer_parser.add_argument("--input", required=True, nargs="+", help="Path(s) to .wav files or directories.")
    diarizer_parser.add_argument("--output", required=True, help="Directory to save diarization RTTM files.")
    diarizer_parser.set_defaults(func=run_diarization)

    # --- ALIGN Subparser ---
    align_parser = subparsers.add_parser("align", help="Align transcription and diarization outputs.")
    align_parser.add_argument(
        "--transcriptions", required=True, nargs="+", help="Path(s) to transcription .json files or directories."
    )
    align_parser.add_argument(
        "--diarizations", required=True, nargs="+", help="Path(s) to diarization .rttm files or directories."
    )
    align_parser.add_argument("--output", required=True, help="Directory to save aligned .json files.")
    # Removed specific --config here, as it's handled globally by the main parser.
    align_parser.set_defaults(func=run_aligning)

    # --- POSTPROCESS Subparser ---
    postprocess_parser = subparsers.add_parser("postprocess", help="Run the postprocessing step.")
    postprocess_parser.add_argument(
        "--input", required=True, nargs="+", help="Path(s) to aligned JSON files or directories."
    )
    postprocess_parser.add_argument("--output", required=True, help="Path to the final merged/formatted text file.")
    postprocess_parser.set_defaults(func=run_postprocessing)

    # --- Parse Arguments ---
    args = parser.parse_args()
    # config = load_config(args.config)
    args.func(args)


if __name__ == "__main__":
    main()
