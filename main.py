import argparse
from src.utils import load_config, setup_logger

# Initialize top-level logger
logger = setup_logger("main")


def run_chunking(args):
    logger.info("Running chunking module...")
    # Here you'd import and call your actual chunking function from chunker.py
    pass


def run_transcription(args):
    logger.info("Running transcription module...")
    # Stub for transcriber.py entrypoint
    pass


def run_diarization(args):
    logger.info("Running diarization module...")
    # Stub for diarizer.py entrypoint
    pass


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
    parser.add_argument("--config", required=True, help="Path to the TOML config file")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("chunk", help="Run the chunking step").set_defaults(func=run_chunking)
    subparsers.add_parser("transcribe", help="Run the transcription step").set_defaults(func=run_transcription)
    subparsers.add_parser("diarize", help="Run the diarization step").set_defaults(func=run_diarization)
    subparsers.add_parser("postprocess", help="Run the postprocessing step").set_defaults(func=run_postprocessing)
    subparsers.add_parser("merge", help="Run the merging step").set_defaults(func=run_merging)

    args = parser.parse_args()
    config = load_config(args.config)
    args.func(args)


if __name__ == "__main__":
    main()
