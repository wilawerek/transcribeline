import argparse
import glob
import logging
import subprocess
from pathlib import Path

from src.utils import load_config, setup_logger

logger = setup_logger("pipeline")


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
    # Deduplicate and sort
    unique = sorted(set(files))
    return unique


def run_subprocess(command: list[str]):
    """
    Run a subprocess command and let each module's own logging print live.
    """
    logger.info(f"Running: {' '.join(command)}")
    result = subprocess.run(command)  # NO capture_output

    if result.returncode != 0:
        logger.error(f"Command failed: {' '.join(command)}")
        raise RuntimeError(f"Step failed: {' '.join(command)}")
    else:
        logger.info("Step completed successfully")


def run_pipeline_for_file(audio_path: Path, output_root: Path, config_path: str):
    """
    For a single audio file, create a working directory structure and run all pipeline steps in sequence.
    """
    stem = audio_path.stem
    audio_dir = output_root / stem
    # Create subdirectories
    chunks_dir = audio_dir / "chunks"
    transcripts_dir = audio_dir / "transcripts"
    diarz_dir = audio_dir / "diarizations"
    aligns_dir = audio_dir / "aligns"
    formatted_file = audio_dir / "formatted" / "merged.txt"

    for d in (chunks_dir, transcripts_dir, diarz_dir, aligns_dir, formatted_file.parent):
        d.mkdir(parents=True, exist_ok=True)

    # 1) Chunk
    run_subprocess(["python", "main.py", "chunk", "--input", str(audio_path), "--output", str(chunks_dir)])

    # 2) Transcribe
    run_subprocess(["python", "main.py", "transcribe", "--input", str(chunks_dir), "--output", str(transcripts_dir)])

    # 3) Diarize
    run_subprocess(["python", "main.py", "diarize", "--input", str(chunks_dir), "--output", str(diarz_dir)])

    # 4) Align
    run_subprocess(
        [
            "python",
            "main.py",
            "align",
            "--transcriptions",
            str(transcripts_dir),
            "--diarizations",
            str(diarz_dir),
            "--output",
            str(aligns_dir),
        ]
    )

    # 5) Postprocess (merge+format)
    run_subprocess(
        [
            "python",
            "main.py",
            "postprocess",
            "--inputs",
            str(aligns_dir),
            "--output",
            str(formatted_file),
        ]
    )

    logger.info(f"Pipeline complete for {audio_path.name}. Final file: {formatted_file}")


def main():
    parser = argparse.ArgumentParser(description="Full audio processing pipeline")
    parser.add_argument("inputs", nargs="+", help="Path(s) or glob patterns to audio files (e.g. *.wav)")
    parser.add_argument(
        "--output-root",
        default="data/processed/pipeline_outputs",
        help="Root directory under which each audio file gets its own subfolder",
    )
    parser.add_argument("--config", default="config/settings.toml", help="Path to the TOML config file")
    args = parser.parse_args()

    # Expand input patterns into actual file paths
    audio_files = expand_audio_inputs(args.inputs)
    if not audio_files:
        logger.error(f"No valid audio files found for patterns: {args.inputs}")
        return

    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    for audio_path in audio_files:
        try:
            logger.info(f"Starting pipeline for {audio_path.name}")
            run_pipeline_for_file(audio_path, output_root, args.config)
        except Exception as e:
            logger.error(f"Pipeline failed for {audio_path.name}: {e}")


if __name__ == "__main__":
    main()
