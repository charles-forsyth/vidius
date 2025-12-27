import argparse
import re
import sys
import textwrap

from vidius.api_client import VideoGenerator
from vidius.config import settings
from vidius.history import HistoryManager


def generate_filename(prompt: str) -> str:
    """Generate a sane filename from the prompt."""
    sane_prompt = re.sub(r"[^a-zA-Z0-9_]+", "_", prompt)
    return "_".join(sane_prompt.split("_")[:5]) + ".mp4"


def main() -> None:
    epilog_text = textwrap.dedent("""
    Defaults:
      - Duration: 8 seconds
      - Aspect Ratio: 16:9
      - Audio: Enabled
      - Enhance Prompt: Enabled
      - Person Generation: allow_adult
      - Output File: Generated from prompt

    Examples:
      1. Quick Start:
         vidius "A cyberpunk city in the rain"

      2. Vertical Video (Shorts/Reels):
         vidius "A dancer on stage" -ar 9:16 -d 6

      3. Custom Output Filename:
         vidius "A quiet beach" -o my_beach.mp4

      4. Raw Generation (No Audio, No AI Rewrite):
         vidius "Abstract shapes" --no-audio --no-enhance

      5. Negative Prompting:
         vidius "A portrait" -np "blurry, distorted, dark"

      6. History Management:
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
    parser.add_argument("-o", "--output-file", help="Output filename. Defaults to generated from prompt.")
    parser.add_argument("-d", "--duration", type=int, choices=[4, 6, 8], default=8, help="Video duration in seconds.")
    parser.add_argument(
        "-ar",
        "--aspect-ratio",
        default="16:9",
        choices=["16:9", "9:16", "1:1", "21:9", "4:3", "3:4"],
        help="Video aspect ratio.",
    )
    parser.add_argument("-na", "--no-audio", action="store_true", help="Disable audio generation.")
    parser.add_argument("-ne", "--no-enhance", action="store_true", help="Disable prompt enhancement.")
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
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.1.1")

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
        args.no_enhance = entry.get("no_enhance", args.no_enhance)
        args.aspect_ratio = entry.get("aspect_ratio", args.aspect_ratio)
        args.person_generation = entry.get("person_generation", args.person_generation)
        args.negative_prompt = entry.get("negative_prompt", args.negative_prompt)

    if not args.prompt:
        parser.error("prompt is required unless --history or --rerun is used")

    # Determine Output File
    if not args.output_file:
        args.output_file = generate_filename(args.prompt)

    # Save to history
    new_entry = {
        "prompt": args.prompt,
        "output_file": args.output_file,
        "duration": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "no_audio": args.no_audio,
        "no_enhance": args.no_enhance,
        "person_generation": args.person_generation,
        "negative_prompt": args.negative_prompt,
    }
    history_manager.save(new_entry)

    # Initialize Generator
    if args.model != settings.model_id:
        settings.model_id = args.model

    generator = VideoGenerator()

    try:
        generator.generate(
            prompt=args.prompt,
            output_file=args.output_file,
            duration=args.duration,
            aspect_ratio=args.aspect_ratio,
            generate_audio=not args.no_audio,
            enhance_prompt=not args.no_enhance,
            person_generation=args.person_generation,
            negative_prompt=args.negative_prompt,
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
