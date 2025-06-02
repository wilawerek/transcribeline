import json
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from src.utils import load_config, setup_logger
from tqdm import tqdm

logger = setup_logger("transcriber")


def transcribe_audio(audio_path: Path, output_path: Path, model: str, language: str, logger: logging.Logger):
    # import warnings
    # warnings.filterwarnings("ignore", category=UserWarning)

    import whisper

    model = whisper.load_model(model)

    try:
        logger.info(f"Starting transcription: {audio_path.name}")
        result = model.transcribe(str(audio_path), language=language)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"Transcribed: {audio_path.name}")
    except Exception as e:
        logger.error(f"Failed to transcribe {audio_path.name}: {e}")


def cli_entry(args):
    config = load_config(args.config)
    # chunk_dir = Path(config.GENERAL.processed_output_dir) / "chunks"
    # output_dir = Path(config.GENERAL.processed_output_dir) / "transcripts"
    # input_paths = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_paths = [Path(p) for p in args.input]
    audio_files = []
    for path in input_paths:
        if path.is_dir():
            audio_files.extend(path.glob("*.wav"))
        elif path.is_file() and path.suffix == ".wav":
            audio_files.append(path)

    # audio_files = list(input_path.glob("*.wav"))
    if not audio_files:
        logger.warning("No audio chunks found for transcription.")
        return

    logger.info(f"Found {len(audio_files)} chunks. Starting transcription...")

    model = config.WHISPER.model
    language = config.WHISPER.language

    with ProcessPoolExecutor(max_workers=config.PARALLEL.parallel_workers) as executor:
        futures = {
            executor.submit(
                transcribe_audio, audio_file, output_dir / f"{audio_file.stem}.json", model, language, logger
            ): audio_file
            for audio_file in audio_files
        }

        # for future in tqdm(as_completed(futures), total=len(futures), desc="Transcribing"):
        for future in as_completed(futures):
            future.result()
