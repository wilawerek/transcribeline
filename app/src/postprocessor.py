import glob
import json
import logging
import re
from pathlib import Path

from src.utils import setup_logger

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
    # Extract numeric index from filename like chunk_0001.aligned.json
    match = re.search(r".*_(\d+)\.aligned\.json", path.name)
    return int(match.group(1)) if match else 0


def merge_aligned_chunks(input_patterns: list[str], output_file: Path):
    speaker_blocks = []

    aligned_files = collect_aligned_files(input_patterns)
    if not aligned_files:
        logger.warning(f"No aligned files found for patterns: {input_patterns}.")
        return

    # Sort files by extracted chunk index
    aligned_files.sort(key=extract_chunk_index)

    chunk_start_offset = 0.0
    # print(aligned_files)
    for file in aligned_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Find max end time to offset next chunk
            max_chunk_duration = max((seg["end"] for seg in data.get("segments", [])), default=0.0)

            for seg in data.get("segments", []):
                start = seg["start"] + chunk_start_offset
                end = seg["end"] + chunk_start_offset
                speaker = seg["speaker"]
                text = seg["text"].strip()
                speaker_blocks.append((start, speaker, text))

            chunk_start_offset += max_chunk_duration

        except Exception as e:
            logger.error(f"Failed to load or parse {file.name}: {e}")

    # Sort all segments by adjusted start time
    speaker_blocks.sort(key=lambda x: x[0])

    formatted_lines = []
    last_speaker = None
    buffer = []

    for start, speaker, text in speaker_blocks:
        if speaker != last_speaker:
            if buffer:
                formatted_lines.append(f"[SPEAKER {last_speaker}] ({start:.2f})\n" + " ".join(buffer) + "\n")
                buffer = []
            last_speaker = speaker
        buffer.append(text)

    if buffer:
        formatted_lines.append(f"[SPEAKER {last_speaker}]\n" + " ".join(buffer) + "\n")

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

    input_patterns = args.input  # list of file or directory patterns
    output_file = Path(args.output)

    merge_aligned_chunks(input_patterns, output_file)
