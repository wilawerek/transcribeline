import glob
import json
import logging
import re
from pathlib import Path

from pydub import AudioSegment
from src.utils import seconds_to_hhmmss, setup_logger

logger = setup_logger("postprocessing")


def collect_aligned_files(inputs: list[str]) -> list[Path]:
    files = []
    for pattern in sorted(inputs):
        for match in glob.glob(pattern):
            path = Path(match)
            if path.is_dir():
                files.extend(path.glob("*.aligned.json"))
            elif path.is_file() and path.suffix == ".json" and ".aligned" in path.stem:
                files.append(path)
    return sorted(files, key=extract_chunk_index)


def extract_chunk_index(path: Path) -> int:
    match = re.search(r"_(\d+)\.aligned\.json$", path.name)
    return int(match.group(1)) if match else 0


def match_wav_chunk(json_path: Path) -> Path:
    """Try to locate the corresponding .wav file for the aligned chunk."""
    chunk_number = extract_chunk_index(json_path)
    parent = json_path.parent.parent  # aligned -> transcripts -> CHUNK_DIR
    audio_name = "_".join(json_path.stem.split("_")[:-1])
    return parent / "chunks" / f"{audio_name}_{chunk_number:02d}.wav"


def get_chunk_durations(json_files: list[Path]) -> list[float]:
    """Return list of durations for each chunk in order, to compute offsets."""
    durations = []
    for json_file in json_files:
        wav_path = match_wav_chunk(json_file)
        if not wav_path.exists():
            logger.warning(f"Missing chunk audio for {json_file.name}: {wav_path}")
            durations.append(0.0)
        else:
            audio = AudioSegment.from_wav(wav_path)
            durations.append(len(audio) / 1000.0)
    return durations


def merge_aligned_chunks(input_patterns: list[str], output_file: Path):
    aligned_files = collect_aligned_files(input_patterns)
    if not aligned_files:
        logger.warning(f"No aligned files found for patterns: {input_patterns}.")
        return

    logger.info(f"Found {len(aligned_files)} aligned files.")
    chunk_durations = get_chunk_durations(aligned_files)

    speaker_blocks = []
    offset = 0.0

    for file, duration in zip(aligned_files, chunk_durations):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for seg in data.get("segments", []):
                speaker = seg["speaker"]
                start = seg["start"] + offset
                text = seg["text"].strip()
                speaker_blocks.append((start, speaker, text))
        except Exception as e:
            logger.error(f"Failed to load or parse {file.name}: {e}")
        offset += duration

    speaker_blocks.sort(key=lambda x: x[0])

    formatted_lines = []
    last_speaker = None
    buffer = []
    block_start_time = None

    for start, speaker, text in speaker_blocks:
        if speaker != last_speaker:
            if buffer:
                formatted_lines.append(
                    f"[{last_speaker}] ({seconds_to_hhmmss(block_start_time)})\n" + " ".join(buffer) + "\n"
                )
                buffer = []
            last_speaker = speaker
            block_start_time = start
        buffer.append(text)

    if buffer:
        formatted_lines.append(
            f"[{last_speaker}] ({seconds_to_hhmmss(block_start_time)})\n" + " ".join(buffer) + "\n"
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(formatted_lines))

    logger.info(f"Merged and formatted file saved to {output_file}")


def cli_entry(args):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    input_patterns = args.input
    output_file = Path(args.output)

    merge_aligned_chunks(input_patterns, output_file)
