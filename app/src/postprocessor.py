import glob
import json
import logging
import re
from pathlib import Path

from src.utils import seconds_to_hhmmss, setup_logger

logger = setup_logger("postprocessing")


def collect_aligned_files(inputs: list[str]) -> list[Path]:
    files = []
    for pattern in sorted(inputs):
        for match in glob.glob(pattern):
            path = Path(match)
            if path.is_dir():
                files.extend(list(path.glob("*.aligned.json")))
            elif path.is_file() and path.suffix == ".json" and ".aligned" in path.stem:
                files.append(path)
    return files


def extract_chunk_index(path: Path) -> int:
    match = re.search(r".*_(\d+)\.aligned\.json", path.name)
    return int(match.group(1)) if match else 0


def merge_aligned_chunks(input_patterns: list[str], output_file: Path):
    speaker_blocks = []

    aligned_files = collect_aligned_files(input_patterns)
    if not aligned_files:
        logger.warning(f"No aligned files found for patterns: {input_patterns}.")
        return

    aligned_files.sort(key=extract_chunk_index)

    chunk_start_offset = 0.0

    for idx, file in enumerate(aligned_files):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            segments = data.get("segments", [])
            max_chunk_duration = max((seg["end"] for seg in segments), default=0.0)

            for seg in segments:
                start = seg["start"] + chunk_start_offset
                speaker = seg["speaker"]
                text = seg["text"].strip()
                speaker_blocks.append((start, speaker, text))

            chunk_start_offset += max_chunk_duration - idx * 0.5

        except Exception as e:
            logger.error(f"Failed to load or parse {file.name}: {e}")

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
        formatted_lines.append(f"[{last_speaker}] ({seconds_to_hhmmss(block_start_time)})\n" + " ".join(buffer) + "\n")

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
