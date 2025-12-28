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
         
      3. Start & End Frames (Interpolation):
         vidius "A flower blooming" --image bud.png --last-image flower.png
         
      4. Reference Images (Style/Character):
         vidius "A knight fighting a dragon" --ref-image character_sheet.png --ref-image style_guide.png

      5. Extend Video:
         vidius "The character walks into the portal" --extend-video part1.mp4

      6. Vertical Video (Shorts/Reels):
         vidius "A dancer on stage" -ar 9:16 -d 6

      7. Custom Output Filename:
         vidius "A quiet beach" -o my_beach.mp4
         
      8. Raw Generation (No Audio):
         vidius "Abstract shapes" --no-audio

      9. Negative Prompting:
         vidius "A portrait" -np "blurry, distorted, dark"
    """)

    parser = argparse.ArgumentParser(
        description="Vidius: Professional CLI for Vertex AI VEO Video Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog_text,
    )

    # Core arguments
    parser.add_argument("prompt", nargs="?", default=None, help="The text prompt for the video.")

    # Options
    parser.add_argument("-i", "--image", help="Path to the START frame image.")
    parser.add_argument("-li", "--last-image", help="Path to the END frame image (for interpolation).")
    parser.add_argument(
        "-ri", "--ref-image", action="append", help="Path to a REFERENCE image (can be used multiple times, max 3)."
    )
    parser.add_argument("-e", "--extend-video", help="Path to an input video to extend.")
    parser.add_argument("-o", "--output-file", help="Output filename. Defaults to generated from prompt.")
    parser.add_argument("-d", "--duration", type=int, choices=[4, 6, 8], default=8, help="Video duration in seconds.")
    parser.add_argument("-ar", "--aspect-ratio", default="16:9", choices=["16:9", "9:16"], help="Video aspect ratio.")
    parser.add_argument("-na", "--no-audio", action="store_true", help="Disable audio generation.")
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
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.1.6")

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
        args.aspect_ratio = entry.get("aspect_ratio", args.aspect_ratio)
        args.person_generation = entry.get("person_generation", args.person_generation)
        args.negative_prompt = entry.get("negative_prompt", args.negative_prompt)

    if not args.prompt:
        parser.error("prompt is required unless --history or --rerun is used")

    if args.image and args.extend_video:
        parser.error("Cannot specify both --image and --extend-video")

    # Determine Output File/Path
    raw_output = args.output_file
    if not raw_output:
        raw_output = generate_filename(args.prompt)

    final_output_path = resolve_output_path(raw_output)

    # Save to history
    new_entry = {
        "prompt": args.prompt,
        "output_file": str(final_output_path),
        "duration": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "no_audio": args.no_audio,
        "person_generation": args.person_generation,
        "negative_prompt": args.negative_prompt,
        "image": args.image,
        "last_image": args.last_image,
        "ref_images": args.ref_image,
        "extend_video": args.extend_video,
    }
    history_manager.save(new_entry)

    # Initialize Generator
    if args.model != settings.model_id:
        settings.model_id = args.model

    generator = VideoGenerator()

    try:
        if args.extend_video:
            generator.extend_video(
                prompt=args.prompt,
                input_video_path=args.extend_video,
                output_file=str(final_output_path),
                negative_prompt=args.negative_prompt,
            )
        else:
            generator.generate(
                prompt=args.prompt,
                output_file=str(final_output_path),
                duration=args.duration,
                aspect_ratio=args.aspect_ratio,
                generate_audio=not args.no_audio,
                person_generation=args.person_generation,
                negative_prompt=args.negative_prompt,
                image_path=args.image,
                last_frame_path=args.last_image,
                reference_image_paths=args.ref_image,
            )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
