import os
import subprocess
from pathlib import Path

from pydub import AudioSegment, silence
from tqdm import tqdm

from src.utils import load_config, setup_logger

logger = setup_logger("chunker")


def chunk_audio(
    input_file: Path,
    output_dir: Path,
    max_duration_sec: int,
    silence_thresh_db: int,
    min_silence_len_sec: float,
    keep_silence_ms: int,
):
    logger.info(f"Loading audio file: {input_file}")
    audio = AudioSegment.from_wav(input_file)

    logger.info("Detecting silent chunks...")
    silent_ranges = silence.detect_silence(
        audio,
        min_silence_len=int(min_silence_len_sec * 1000),
        silence_thresh=silence_thresh_db,
        seek_step=1,
    )

    silent_ranges = [(start, end) for start, end in silent_ranges if end - start > 200]
    if not silent_ranges:
        logger.warning("No silent ranges found. Exporting original file as a single chunk.")
        audio.export(output_dir / f"chunk_0.wav", format="wav")
        print("[chunker] Exported chunk_0.wav")
        return

    chunks = []
    last_start = 0
    for i, (start, end) in enumerate(silent_ranges):
        if (start - last_start) > max_duration_sec * 1000:
            chunk = audio[last_start : start + keep_silence_ms]
            chunks.append(chunk)
            last_start = start

    # Add final chunk
    if last_start < len(audio):
        chunks.append(audio[last_start:])

    logger.info(f"Exporting {len(chunks)} chunks...")
    output_dir.mkdir(parents=True, exist_ok=True)
    for idx, chunk in tqdm(list(enumerate(chunks)), total=len(chunks), desc="[chunker] Exporting"):
        chunk_path = output_dir / f"chunk_{idx}.wav"
        chunk.export(chunk_path, format="wav")
        print(f"[chunker] Exported: {chunk_path.name}")

    logger.info("Chunking complete.")
    print("[chunker] Done.")


def cli_entry(args):
    config = load_config(args.config)
    input_file = Path(args.input)
    output_dir = Path(args.output)
    # output_dir = Path(config.GENERAL.processed_output_dir) / "chunks"

    chunk_audio(
        input_file=input_file,
        output_dir=output_dir,
        max_duration_sec=config.CHUNKING.max_chunk_duration_sec,
        silence_thresh_db=config.CHUNKING.silence_noise_threshold_db,
        min_silence_len_sec=config.CHUNKING.min_silence_duration_sec,
        keep_silence_ms=config.CHUNKING.keep_silence_ms,
    )
