#!/usr/bin/env python3

import argparse
import glob
import logging
import subprocess
from pathlib import Path

from src.utils import load_config, setup_logger

# LOG_DIR = "logs"
logger = setup_logger("pipeline")

# Resolve absolute path to main.py regardless of working dir
SCRIPT_DIR = Path(__file__).resolve().parent
MAIN_PATH = SCRIPT_DIR / "main.py"


def expand_audio_inputs(patterns: list[str]) -> list[Path]:
    """
    Take a list of glob patterns (or file paths) and return a deduplicated list of existing audio files.
    """
    files = []
    for pattern in patterns:
        for match in glob.glob(pattern):
            p = Path(match)
            if p.is_file() and p.suffix.lower() in {".wav", ".mp3", ".flac"}:
                files.append(p.resolve())
    return sorted(set(files))


def run_subprocess(command: list[str]):
    logger.info(f"Running: {' '.join(command)}")
    result = subprocess.run(command)
    if result.returncode != 0:
        logger.error(f"Command failed: {' '.join(command)}")
        raise RuntimeError(f"Step failed: {' '.join(command)}")
    else:
        logger.info("Step completed successfully")


def run_pipeline_for_file(audio_path: Path, output_dir: Path, config_path: Path):
    """
    For a single audio file, create a working directory structure and run all pipeline steps in sequence.
    """
    stem = audio_path.stem
    audio_dir = output_dir / stem

    # Prepare all subdirectories
    chunks_dir = audio_dir / "chunks"
    transcripts_dir = audio_dir / "transcripts"
    diarizations_dir = audio_dir / "diarizations"
    aligns_dir = audio_dir / "aligns"
    formatted_file = audio_dir / "formatted" / f"{stem}.txt"
    log_dir = audio_dir / "log"

    for d in (chunks_dir, transcripts_dir, diarizations_dir, aligns_dir, formatted_file.parent, log_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Setup per-file logger
    # logger = setup_logger("pipeline", log_dir=log_dir)
    # logger.info(f"Processing file: {audio_path.name}")

    # 1) Chunk
    run_subprocess(
        [
            "python",
            str(MAIN_PATH),
            "--config",
            str(config_path),
            "chunk",
            "--input",
            str(audio_path),
            "--output",
            str(chunks_dir),
        ],
    )

    # 2) Transcribe
    run_subprocess(
        [
            "python",
            str(MAIN_PATH),
            "--config",
            str(config_path),
            "transcribe",
            "--input",
            str(chunks_dir),
            "--output",
            str(transcripts_dir),
        ],
    )

    # 3) Diarize
    run_subprocess(
        [
            "python",
            str(MAIN_PATH),
            "--config",
            str(config_path),
            "diarize",
            "--input",
            str(chunks_dir),
            "--output",
            str(diarizations_dir),
        ],
    )

    # 4) Align
    run_subprocess(
        [
            "python",
            str(MAIN_PATH),
            "--config",
            str(config_path),
            "align",
            "--transcriptions",
            str(transcripts_dir),
            "--diarizations",
            str(diarizations_dir),
            "--output",
            str(aligns_dir),
        ],
    )

    # 5) Postprocess (merge + format)
    run_subprocess(
        [
            "python",
            str(MAIN_PATH),
            "--config",
            str(config_path),
            "postprocess",
            "--input",
            str(aligns_dir),
            "--output",
            str(formatted_file),
        ],
    )

    logger.info(f"Pipeline complete for {audio_path.name}. Final file: {formatted_file}")


def main():
    parser = argparse.ArgumentParser(description="Full audio processing pipeline")
    parser.add_argument("input", nargs="+", help="Path(s) or glob patterns to audio files (e.g. *.wav)")
    parser.add_argument(
        "--output",
        default=".",
        help="Root directory under which each audio file gets its own subfolder",
    )
    parser.add_argument("--config", default="config/settings.toml", help="Path to the TOML config file")
    args = parser.parse_args()

    # Expand input patterns into actual file paths
    audio_files = expand_audio_inputs(args.input)
    if not audio_files:
        logger.error(f"No valid audio files found for: {args.input}")
        # print(f"No valid audio files found for: {args.input}")
        return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    config_path = Path(args.config)

    for audio_path in audio_files:
        try:
            logger.info(f"Starting pipeline for {audio_path.name}")
            run_pipeline_for_file(audio_path, output_dir, config_path)
        except Exception as e:
            logger.error(f"Pipeline failed for {audio_path.name}: {e}")
            # print(f"Pipeline failed for {audio_path.name}: {e}")


if __name__ == "__main__":
    main()
