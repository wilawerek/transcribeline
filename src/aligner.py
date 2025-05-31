import glob
import json
import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from pyannote.core import Annotation, Segment
from tqdm import tqdm

from src.utils import load_config, setup_logger

logger = setup_logger("aligner")


def load_transcription(transcription_path: Path) -> dict:
    with open(transcription_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_diarization(rttm_path: Path) -> Annotation:
    annotation = Annotation()
    with open(rttm_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 8:
                continue
            start = float(parts[3])
            duration = float(parts[4])
            speaker = parts[7]
            segment = Segment(start, start + duration)
            annotation[segment] = speaker
    return annotation


def align_segments(transcription: dict, diarization: Annotation) -> list:
    aligned = []
    for seg in transcription.get("segments", []):
        start = seg.get("start")
        end = seg.get("end")
        text = seg.get("text")
        segment = Segment(start, end)
        overlaps = diarization.crop(segment, mode="intersection")
        if not overlaps:
            speaker = "UNKNOWN"
        else:
            best = None
            best_overlap = 0.0
            for spk_segment, track_id, spk_label in overlaps.itertracks(yield_label=True):
                overlap = min(spk_segment.end, segment.end) - max(spk_segment.start, segment.start)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best = spk_label
            speaker = best if best is not None else "UNKNOWN"
        aligned.append({"start": start, "end": end, "speaker": speaker, "text": text})
    return aligned


def align_pair(transcription_path: Path, diarization_path: Path, output_path: Path):
    try:
        transcription = load_transcription(transcription_path)
        diarization = load_diarization(diarization_path)
        aligned_segments = align_segments(transcription, diarization)

        combined = {
            "metadata": {
                "audio_file": transcription_path.name,
                "model": transcription.get("model"),
                "language": transcription.get("language"),
                "duration": transcription.get("duration"),
            },
            "segments": aligned_segments,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
        logger.info(f"Aligned: {transcription_path.name}")
    except Exception as e:
        logger.error(f"Failed to align {transcription_path.name} and {diarization_path.name}: {e}")


def collect_files(paths: list[str], suffix: str) -> dict:
    collected = {}
    for p in paths:
        for match in glob.glob(p):
            path = Path(match)
            if path.is_dir():
                for file in path.glob(f"*{suffix}"):
                    collected[file.stem] = file
            elif path.is_file() and path.suffix == suffix:
                collected[path.stem] = path
    return collected


def cli_entry(args):
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    config = load_config(args.config)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    transcription_files = collect_files(args.transcriptions, ".json")
    diarization_files = collect_files(args.diarizations, ".rttm")

    common_keys = transcription_files.keys() & diarization_files.keys()
    if not common_keys:
        logger.warning("No matching transcription and diarization files found.")
        return

    logger.info(f"Found {len(common_keys)} matching files. Starting alignment...")

    with ProcessPoolExecutor(max_workers=config.PARALLEL.parallel_workers) as executor:
        futures = {
            executor.submit(
                align_pair,
                transcription_files[key],
                diarization_files[key],
                output_dir / f"{key}.aligned.json",
            ): key
            for key in common_keys
        }

        # for future in tqdm(as_completed(futures), total=len(futures), desc="Aligning"):
        for future in as_completed(futures):
            future.result()
