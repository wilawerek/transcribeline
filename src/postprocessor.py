import glob
import json
import logging
from pathlib import Path

from src.utils import setup_logger

logger = setup_logger("postprocessing")


def collect_aligned_files(inputs: list[str]) -> list[Path]:
    files = []
    for pattern in inputs:
        for match in glob.glob(pattern):
            path = Path(match)
            if path.is_dir():
                files.extend(list(path.glob("*.aligned.json")))
            elif path.is_file() and path.suffix == ".json" and ".aligned" in path.stem:
                files.append(path)
    return files


def merge_aligned_chunks(input_patterns: list[str], output_file: Path):
    speaker_blocks = []

    aligned_files = collect_aligned_files(input_patterns)
    if not aligned_files:
        logger.warning(f"No aligned files found for patterns: {input_patterns}.")
        return

    # Sort files by name to preserve chunk order
    aligned_files.sort(key=lambda f: f.name)

    for file in aligned_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for seg in data.get("segments", []):
                speaker_blocks.append((seg["start"], seg["speaker"], seg["text"].strip()))
        except Exception as e:
            logger.error(f"Failed to load or parse {file.name}: {e}")

    # Sort all segments by start time
    speaker_blocks.sort(key=lambda x: x[0])

    formatted_lines = []
    last_speaker = None
    buffer = []

    for _, speaker, text in speaker_blocks:
        if speaker != last_speaker:
            if buffer:
                formatted_lines.append(f"[SPEAKER {last_speaker}]\n" + " ".join(buffer) + "\n")
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

    input_patterns = args.inputs  # list of file or directory patterns
    output_file = Path(args.output)

    merge_aligned_chunks(input_patterns, output_file)
