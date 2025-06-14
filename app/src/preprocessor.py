from pathlib import Path

from pydub import AudioSegment, effects
from src.utils import setup_logger

logger = setup_logger("preprocessor")


def preprocess_audio(
    input_path: Path,
    output_path: Path,
    apply_high_pass: bool = True,
):
    """
    Preprocess an audio file by:
    - Normalizing volume
    - Optionally applying a high-pass filter
    - Saving a cleaned version of the file

    (Silence is NOT removed to preserve structure for chunking.)
    """
    logger.info(f"Loading audio file: {input_path}")
    audio = AudioSegment.from_wav(input_path)

    logger.info("Normalizing audio...")
    audio = effects.normalize(audio)

    if apply_high_pass:
        logger.info("Applying high-pass filter at 80Hz...")
        audio = audio.high_pass_filter(80)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio.export(output_path, format="wav")
    logger.info(f"Preprocessed audio saved to {output_path}")


def cli_entry(args):
    input_path = Path(args.input)
    output_path = Path(args.output)
    preprocess_audio(input_path, output_path)
