import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from src.utils import load_config, setup_logger

logger = setup_logger("diarizer")


def diarize_audio(audio_path: Path, output_path: Path, pipeline_name: str, auth_token: str, logger: logging.Logger):
    from pyannote.audio import Pipeline

    # Load the diarization pipeline inside each process
    pipeline = Pipeline.from_pretrained(pipeline_name, use_auth_token=auth_token)
    try:
        logger.info(f"Starting diarization: {audio_path.name}")
        diarization = pipeline(str(audio_path))
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(diarization.to_rttm())
        logger.info(f"Diarized: {audio_path.name}")
    except Exception as e:
        logger.error(f"Failed to diarize {audio_path.name}: {e}")


def cli_entry(args):
    load_dotenv()
    config = load_config(args.config)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect input .wav files from files or directories
    input_paths = [Path(p) for p in args.input]
    audio_files = []
    for path in input_paths:
        if path.is_dir():
            audio_files.extend(path.glob("*.wav"))
        elif path.is_file() and path.suffix == ".wav":
            audio_files.append(path)

    if not audio_files:
        logger.warning("No audio files found for diarization.")
        return

    logger.info(f"Found {len(audio_files)} files. Starting diarization...")

    # Configuration parameters for the diarization pipeline
    pipeline_name = config.DIARIZATION.model
    auth_token = os.getenv("HF_TOKEN")
    if not auth_token:
        logger.error(
            "HF_TOKEN environment variable not set. Please create a .env file in the project root with your Hugging Face token."
        )
        return

    # Run diarization in parallel
    with ProcessPoolExecutor(max_workers=config.PARALLEL.parallel_workers) as executor:
        futures = {
            executor.submit(
                diarize_audio, audio_file, output_dir / f"{audio_file.stem}.rttm", pipeline_name, auth_token, logger
            ): audio_file
            for audio_file in audio_files
        }
        for future in tqdm(as_completed(futures), total=len(futures), desc="Diarizing"):
            future.result()
