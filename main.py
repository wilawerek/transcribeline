import argparse

from config.config import DEFAULT_CONFIG_PATH
from src.chunker import cli_entry as chunk_cli_entry
from src.diarizer import cli_entry as diarizer_cli_entry
from src.transcriber import cli_entry as transcribe_cli_entry
from src.utils import load_config, setup_logger

# Initialize top-level logger
logger = setup_logger("main")


def run_chunking(args):
    logger.info("Running chunking module...")
    chunk_cli_entry(args)


def run_transcription(args):
    logger.info("Running transcription module...")
    transcribe_cli_entry(args)


def run_diarization(args):
    logger.info("Running diarization module...")
    diarizer_cli_entry(args)


def run_postprocessing(args):
    logger.info("Running postprocessing module...")
    # Stub for postproc.py entrypoint
    pass


def run_merging(args):
    logger.info("Running merging module...")
    # Stub for merger.py entrypoint
    pass


def main():
    parser = argparse.ArgumentParser(description="Transcription Pipeline CLI")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to the TOML config file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    chunk_parser = subparsers.add_parser("chunk", help="Run the chunking step")
    # chunk_parser.add_argument("input", help="Path to the input .wav file")
    chunk_parser.add_argument("--input", required=True, help="Path to the input .wav file")
    chunk_parser.add_argument("--output", required=True, help="Directory to save audio chunks")
    chunk_parser.set_defaults(func=run_chunking)

    transcribe_parser = subparsers.add_parser("transcribe", help="Run the transcription step")
    # transcribe_parser.add_argument("input", nargs="+", help="Path(s) to the input chunk .wav files")
    transcribe_parser.add_argument(
        "--input", required=True, nargs="+", help="Path(s) to the input .wav files or directories"
    )
    transcribe_parser.add_argument("--output", required=True, help="Directory to save transcription JSON files")
    transcribe_parser.set_defaults(func=run_transcription)

    diarizer_parser = subparsers.add_parser("diarize", help="Run the diarization step")
    diarizer_parser.add_argument("--input", required=True, nargs="+", help="Path(s) to .wav files or directories")
    diarizer_parser.add_argument("--output", required=True, help="Directory to save diarization RTTM files")
    diarizer_parser.add_argument(
        "--num-speakers", type=int, help="Optional: number of speakers to force in diarization"
    )
    diarizer_parser.set_defaults(func=run_diarization)

    subparsers.add_parser("postprocess", help="Run the postprocessing step").set_defaults(func=run_postprocessing)
    subparsers.add_parser("merge", help="Run the merging step").set_defaults(func=run_merging)

    args = parser.parse_args()
    config = load_config(args.config)
    args.func(args)


if __name__ == "__main__":
    main()
