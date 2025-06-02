import argparse

from config.config import DEFAULT_CONFIG_PATH
from src.aligner import cli_entry as aligner_cli_entry
from src.chunker import cli_entry as chunk_cli_entry
from src.diarizer import cli_entry as diarizer_cli_entry
from src.postprocessor import cli_entry as postprocess_cli_entry
from src.transcriber import cli_entry as transcribe_cli_entry
from src.utils import load_config, setup_logger

# Initialize top-level logger
logger = setup_logger("main")


def run_chunking(args):
    logger.info("Running chunking module...")
    chunk_cli_entry(args)


def run_transcribing(args):
    logger.info("Running transcription module...")
    transcribe_cli_entry(args)


def run_diarization(args):
    logger.info("Running diarization module...")
    diarizer_cli_entry(args)


def run_aligning(args):
    logger.info("Running aligning module...")
    aligner_cli_entry(args)


def run_postprocessing(args):
    logger.info("Running postprocessing module...")
    postprocess_cli_entry(args)


def run_merging(args):
    logger.info("Running merging module...")
    # Stub for merger.py entrypoint
    pass


def main():
    parser = argparse.ArgumentParser(description="Transcription Pipeline CLI")
    parser.add_argument(
        "--config",
        default="config/settings.toml",
        help="Path to the TOML config file",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # CHUNK subparser
    chunk_parser = subparsers.add_parser("chunk", help="Run the chunking step")
    chunk_parser.add_argument("--input", required=True, help="Path to the input .wav file")
    chunk_parser.add_argument("--output", required=True, help="Directory to save audio chunks")
    chunk_parser.set_defaults(func=run_chunking)

    # TRANSCRIBE subparser
    transcribe_parser = subparsers.add_parser("transcribe", help="Run the transcription step")
    transcribe_parser.add_argument(
        "--input", required=True, nargs="+", help="Path(s) to input .wav files or directories"
    )
    transcribe_parser.add_argument("--output", required=True, help="Directory to save transcription JSON files")
    transcribe_parser.set_defaults(func=run_transcribing)

    # DIARIZE subparser
    diarizer_parser = subparsers.add_parser("diarize", help="Run the diarization step")
    diarizer_parser.add_argument("--input", required=True, nargs="+", help="Path(s) to .wav files or directories")
    diarizer_parser.add_argument("--output", required=True, help="Directory to save diarization RTTM files")
    diarizer_parser.set_defaults(func=run_diarization)

    # ALIGN subparser
    align_parser = subparsers.add_parser("align", help="Align transcription and diarization outputs")
    align_parser.add_argument(
        "--transcriptions", required=True, nargs="+", help="Path(s) to transcription .json files or directories"
    )
    align_parser.add_argument(
        "--diarizations", required=True, nargs="+", help="Path(s) to diarization .rttm files or directories"
    )
    align_parser.add_argument("--output", required=True, help="Directory to save aligned .json files")
    align_parser.add_argument("--config", default="config/settings.toml", help="Path to the TOML config file")
    align_parser.set_defaults(func=run_aligning)

    # POSTPROCESS subparser
    postprocess_parser = subparsers.add_parser("postprocess", help="Run the postprocessing step")
    postprocess_parser.add_argument(
        "--input", required=True, nargs="+", help="Path(s) to aligned JSON files or directories"
    )
    postprocess_parser.add_argument("--output", required=True, help="Path to the final merged/ formatted text file")
    postprocess_parser.set_defaults(func=run_postprocessing)

    args = parser.parse_args()
    config = load_config(args.config)
    args.func(args)


if __name__ == "__main__":
    main()
