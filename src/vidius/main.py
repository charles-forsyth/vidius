import argparse
import re
import sys
import textwrap
from pathlib import Path

from vidius.api_client import VideoGenerator
from vidius.config import settings
from vidius.history import HistoryManager


def generate_filename(prompt: str) -> str:
    """Generate a sane filename from the prompt."""
    sane_prompt = re.sub(r"[^a-zA-Z0-9_]+", "_", prompt)
    filename = "_".join(sane_prompt.split("_")[:5]) + ".mp4"
    return filename


def resolve_output_path(filename_or_path: str) -> Path:
    """
    Resolve the final output path.
    If the user provided path is absolute or has a parent directory part
    (e.g. './vid.mp4' or '/tmp/vid.mp4'), use it as is.
    Otherwise, save it to the configured output directory.
    """
    path = Path(filename_or_path)

    # If the user explicitly gave a path with separators, respect it.
    if len(path.parts) > 1:
        return path

    # Otherwise, place it in the default output directory
    output_dir = settings.output_dir
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir / filename_or_path


def main() -> None:
    epilog_text = textwrap.dedent(f"""
    Defaults:
      - Duration: 8 seconds
      - Aspect Ratio: 16:9
      - Audio: Enabled
      - Enhance Prompt: Always Enabled (Veo 3 requirement)
      - Person Generation: allow_adult
      - Output Directory: {settings.output_dir}
      - Output File: Generated from prompt

    Examples:
      1. Quick Start (Saves to default dir):
         vidius "A cyberpunk city in the rain"

      2. Image-to-Video (Start from Image):
         vidius "The water flows" --image river_start.png

      3. Vertical Video (Shorts/Reels):
         vidius "A dancer on stage" -ar 9:16 -d 6

      4. Custom Output Filename (In default dir):
         vidius "A quiet beach" -o my_beach.mp4
         
      5. Custom Absolute Path (Overrides default dir):
         vidius "A quiet beach" -o ./local_beach.mp4

      6. Raw Generation (No Audio):
         vidius "Abstract shapes" --no-audio

      7. Negative Prompting:
         vidius "A portrait" -np "blurry, distorted, dark"

      8. History Management:
         vidius -H          # List history
         vidius -r 3        # Rerun entry #3
    """)

    parser = argparse.ArgumentParser(
        description="Vidius: Professional CLI for Vertex AI VEO Video Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog_text,
    )

    # Core arguments
    parser.add_argument("prompt", nargs="?", default=None, help="The text prompt for the video.")

    # Options
    parser.add_argument("-i", "--image", help="Path to an input image for Image-to-Video generation.")
    parser.add_argument("-o", "--output-file", help="Output filename. Defaults to generated from prompt.")
    parser.add_argument("-d", "--duration", type=int, choices=[4, 6, 8], default=8, help="Video duration in seconds.")
    parser.add_argument("-ar", "--aspect-ratio", default="16:9", choices=["16:9", "9:16"], help="Video aspect ratio.")
    parser.add_argument("-na", "--no-audio", action="store_true", help="Disable audio generation.")
    # Removed -ne / --no-enhance as it is not supported by Veo 3
    parser.add_argument("-np", "--negative-prompt", help="Negative prompt to suppress elements.")
    parser.add_argument(
        "-pg",
        "--person-generation",
        default="allow_adult",
        choices=["allow_adult", "dont_allow"],
        help="Person generation policy.",
    )

    # History
    parser.add_argument("-H", "--history", action="store_true", help="Display prompt history.")
    parser.add_argument("-r", "--rerun", type=int, help="Rerun history entry by ID.")

    # Config overrides
    parser.add_argument("-m", "--model", default=settings.model_id, help="Vertex AI Model ID.")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.1.4")

    args = parser.parse_args()
    history_manager = HistoryManager()

    # Handle History Display
    if args.history:
        history_manager.display()
        return

    # Handle Rerun
    if args.rerun is not None:
        entry = history_manager.get_entry(args.rerun)
        if not entry:
            print(f"Error: Invalid history ID {args.rerun}")
            sys.exit(1)

        print(f"Rerunning entry {args.rerun}: {entry['prompt']}")
        args.prompt = entry["prompt"]
        if not args.output_file:
            args.output_file = entry.get("output_file")

        args.duration = entry.get("duration", args.duration)
        args.no_audio = entry.get("no_audio", args.no_audio)
        # Removed no_enhance from rerun logic as well
        args.aspect_ratio = entry.get("aspect_ratio", args.aspect_ratio)
        args.person_generation = entry.get("person_generation", args.person_generation)
        args.negative_prompt = entry.get("negative_prompt", args.negative_prompt)

    if not args.prompt:
        parser.error("prompt is required unless --history or --rerun is used")

    # Determine Output File/Path
    raw_output = args.output_file
    if not raw_output:
        raw_output = generate_filename(args.prompt)

    final_output_path = resolve_output_path(raw_output)

    # Save to history (we save the full path now so we know where it went)
    new_entry = {
        "prompt": args.prompt,
        "output_file": str(final_output_path),
        "duration": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "no_audio": args.no_audio,
        "person_generation": args.person_generation,
        "negative_prompt": args.negative_prompt,
        "image": args.image,
    }
    history_manager.save(new_entry)

    # Initialize Generator
    if args.model != settings.model_id:
        settings.model_id = args.model

    generator = VideoGenerator()

    try:
        generator.generate(
            prompt=args.prompt,
            output_file=str(final_output_path),
            duration=args.duration,
            aspect_ratio=args.aspect_ratio,
            generate_audio=not args.no_audio,
            # enhance_prompt=not args.no_enhance, # Removed: Always True
            person_generation=args.person_generation,
            negative_prompt=args.negative_prompt,
            image_path=args.image,
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
