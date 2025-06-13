from pathlib import Path

from pydub import AudioSegment, silence
from src.utils import estimate_silence_threshold, load_config, setup_logger

logger = setup_logger("chunker")


def chunk_audio(
    input_file: Path,
    output_dir: Path,
    max_duration_sec: int,
    silence_thresh_db: float,
    min_silence_len_sec: float,
):
    # logger.info(f"Loading audio file: {input_file}")
    audio = AudioSegment.from_wav(input_file)
    base_name = input_file.stem

    logger.info("Detecting silent chunks...")
    min_silence_len_ms = int(min_silence_len_sec * 1000)
    silent_ranges = silence.detect_silence(
        audio,
        min_silence_len=min_silence_len_ms,
        silence_thresh=silence_thresh_db,
        seek_step=1,
    )

    if not silent_ranges:
        logger.warning("No silent ranges found. Exporting original file as a single chunk.")
        output_dir.mkdir(parents=True, exist_ok=True)
        audio.export(output_dir / f"{base_name}_0.wav", format="wav")
        return

    chunks = []
    last_start = 0
    last_silence = None

    for start, end in silent_ranges:
        chunk_duration = start - last_start

        if chunk_duration > max_duration_sec * 1000:
            # If we passed max duration, split at last known silence
            if last_silence:
                chunk_end = last_silence[0]
            else:
                chunk_end = start  # fallback to current silence

            chunk = audio[last_start:chunk_end]
            chunks.append(chunk)
            last_start = last_silence[1] if last_silence else end
            last_silence = None  # reset

        else:
            last_silence = (start, end)

    # Final chunk
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

    # Always auto-estimate threshold
    logger.info(f"Loading audio file: {input_file}")
    silence_thresh_db = estimate_silence_threshold(str(input_file))
    logger.info(f"Auto-estimated silence threshold: {silence_thresh_db:.2f} dBFS")

    chunk_audio(
        input_file=input_file,
        output_dir=output_dir,
        max_duration_sec=config.CHUNKING.max_chunk_duration_sec,
        silence_thresh_db=silence_thresh_db,
        min_silence_len_sec=config.CHUNKING.min_silence_duration_sec,
    )
