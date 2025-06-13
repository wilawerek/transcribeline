from pathlib import Path

from pydub import AudioSegment, silence
from src.utils import estimate_silence_threshold, load_config, setup_logger
from tqdm import tqdm

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
    base_name = input_file.stem

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
        output_dir.mkdir(parents=True, exist_ok=True)
        audio.export(output_dir / f"{base_name}_0.wav", format="wav")
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
    for idx, chunk in enumerate(chunks):
        chunk_path = output_dir / f"{base_name}_{idx:02d}.wav"
        chunk.export(chunk_path, format="wav")

    logger.info("Chunking complete.")


def cli_entry(args):
    config = load_config(args.config)
    input_file = Path(args.input)
    output_dir = Path(args.output)

    # Determine silence threshold
    if getattr(config.CHUNKING, "auto_threshold", False):
        silence_thresh_db = estimate_silence_threshold(
            str(input_file), offset_db=getattr(config.CHUNKING, "threshold_offset_db", -10.0)
        )
        logger.info(f"Auto-estimated silence threshold: {silence_thresh_db:.2f} dBFS")
    else:
        silence_thresh_db = config.CHUNKING.silence_noise_threshold_db
        logger.info(f"Using static silence threshold: {silence_thresh_db} dBFS")

    chunk_audio(
        input_file=input_file,
        output_dir=output_dir,
        max_duration_sec=config.CHUNKING.max_chunk_duration_sec,
        silence_thresh_db=silence_thresh_db,
        min_silence_len_sec=config.CHUNKING.min_silence_duration_sec,
        keep_silence_ms=config.CHUNKING.keep_silence_ms,
    )
