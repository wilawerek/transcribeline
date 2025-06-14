from pathlib import Path

from pydub import AudioSegment, silence
from src.utils import (
    estimate_silence_threshold,
    load_config,
    seconds_to_hhmmss,
    setup_logger,
)

logger = setup_logger("chunker")


def chunk_audio(
    input_file: Path,
    output_dir: Path,
    max_duration_sec: int,
    silence_thresh_db: float,
    min_silence_len_sec: float,
    silence_cut_ratio: float = 0.5,  # NEW: 0.0=start, 1.0=end, 0.5=middle
):
    audio = AudioSegment.from_wav(input_file)
    base_name = input_file.stem
    max_duration_ms = int(max_duration_sec * 1000)
    min_silence_len_ms = int(min_silence_len_sec * 1000)

    logger.info("Detecting silent chunks...")
    silent_ranges = silence.detect_silence(
        audio,
        min_silence_len=min_silence_len_ms,
        silence_thresh=silence_thresh_db,
        seek_step=100,
    )

    if not silent_ranges:
        logger.warning("No silence found. Exporting original as single chunk.")
        output_dir.mkdir(parents=True, exist_ok=True)
        audio.export(output_dir / f"{base_name}_0.wav", format="wav")
        return

    chunks = []
    last_chunk_start = 0
    last_valid_silence = None  # tuple: (start, end)

    for i, (start, end) in enumerate(silent_ranges):
        duration_since_last = end - last_chunk_start

        if duration_since_last > max_duration_ms:
            if last_valid_silence is not None:
                sil_start, sil_end = last_valid_silence
                cut_point = int(sil_start + (sil_end - sil_start) * silence_cut_ratio)
                # logger.debug(
                #     f"Cutting chunk at silence: {sil_start}-{sil_end}ms → cut at {cut_point}ms "
                #     f"[chunk: {(cut_point - last_chunk_start)/1000:.2f}s]"
                # )
                chunks.append(audio[last_chunk_start:cut_point])
                last_chunk_start = cut_point
                last_valid_silence = (start, end)
            else:
                logger.error(f"No silence found within {max_duration_sec}s from {last_chunk_start}ms. Aborting.")
                raise RuntimeError("No valid silence to cut at. Adjust chunking settings.")
        else:
            last_valid_silence = (start, end)
            # logger.debug(f"Silence {i+1} accepted for chunk {len(chunks) + 1}")

    # Add final chunk
    if last_chunk_start < len(audio):
        # logger.info(f"Exporting final chunk from {last_chunk_start}ms to end")
        chunks.append(audio[last_chunk_start:])

    logger.info(f"Exporting {len(chunks)} chunks...")
    output_dir.mkdir(parents=True, exist_ok=True)
    for idx, chunk in enumerate(chunks):
        chunk.export(output_dir / f"{base_name}_{idx:02d}.wav", format="wav")
        # logger.debug(f"Exported chunk {idx} ({len(chunk) / 1000:.2f} sec)")

    logger.info("Chunking complete.")


def cli_entry(args):
    config = load_config(args.config)
    input_file = Path(args.input)
    output_dir = Path(args.output)

    # Always auto-estimate threshold
    logger.info(f"Loading audio file: {input_file}")
    silence_thresh_db = estimate_silence_threshold(str(input_file), offset_db=-15.0)
    logger.info(f"Auto-estimated silence threshold: {silence_thresh_db:.2f} dBFS")

    chunk_audio(
        input_file=input_file,
        output_dir=output_dir,
        max_duration_sec=config.CHUNKING.max_chunk_duration_sec,
        silence_thresh_db=silence_thresh_db,
        min_silence_len_sec=config.CHUNKING.min_silence_duration_sec,
    )
