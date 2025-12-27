#!/usr/bin/env python3
import time
import os
import argparse
import re
import json
from google import genai
from google.genai import types
import base64

# Your project and location details
PROJECT_ID = "ucr-research-computing"
LOCATION = "us-central1"
MODEL_ID = "veo-3.0-generate-preview"
HISTORY_FILE = ".history.json"

def load_history():
    """Loads the prompt history from the history file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def save_history(history):
    """Saves the prompt history to the history file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def display_history(history):
    """Displays the prompt history."""
    if not history:
        print("No history found.")
        return
    for i, entry in enumerate(history):
        print(f"{i+1}: {entry['prompt']}")

def generate_video(prompt, output_file, duration, no_audio, no_enhance, aspect_ratio):
    """Generates a video using the Vertex AI VEO model."""

    # Create the client
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    # Configure the video generation
    config = types.GenerateVideosConfig(
        aspect_ratio=aspect_ratio,
        number_of_videos=1,
        duration_seconds=duration,
        person_generation="allow_adult",
        enhance_prompt=not no_enhance,
        generate_audio=not no_audio,
    )

    print(f"Sending video generation request for prompt: '{prompt}'")
    # Start the video generation
    operation = client.models.generate_videos(
        model=MODEL_ID,
        prompt=prompt,
        config=config,
    )

    print(f"Operation started: {operation.name}")

    # Poll the operation status
    while not operation.done:
        print("Video generation in progress. This may take a few minutes. Checking status in 15 seconds...")
        time.sleep(15)
        operation = client.operations.get(operation)


    if operation.response:
        print("Operation succeeded!")
        # The .video attribute is an object with a .save() method.
        video_object = operation.result.generated_videos[0].video
        video_object.save(output_file)
        print(f"Video saved as {output_file}")
    else:
        print("Operation failed.")
        if operation.error:
            print(f"Error details: {operation.error}")

def main():
    """Main function to parse arguments and generate video."""
    parser = argparse.ArgumentParser(description="Generate a video using the Vertex AI VEO model.")
    parser.add_argument("prompt", type=str, nargs='?', default=None, help="The text prompt for the video.")
    parser.add_argument("--output-file", type=str, default=None, help="The name of the output video file. If not specified, a filename will be generated from the prompt.")
    parser.add_argument("--duration", type=int, default=8, help="The duration of the video in seconds. Currently, only 8 seconds is supported.")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio generation.")
    parser.add_argument("--no-enhance", action="store_true", help="Disable prompt enhancement.")
    parser.add_argument("--aspect-ratio", type=str, default="16:9", help="The aspect ratio of the video.")
    parser.add_argument("--history", action="store_true", help="Display prompt history.")
    parser.add_argument("--rerun", type=int, default=None, help="Rerun a prompt from history by its number.")
    args = parser.parse_args()

    history = load_history()

    if args.history:
        display_history(history)
        return

    if args.rerun is not None:
        if not history or args.rerun < 1 or args.rerun > len(history):
            print("Invalid history number.")
            return
        entry = history[args.rerun - 1]
        args.prompt = entry["prompt"]
        args.output_file = entry["output_file"]
        args.duration = entry["duration"]
        args.no_audio = entry["no_audio"]
        args.no_enhance = entry["no_enhance"]
        args.aspect_ratio = entry["aspect_ratio"]
    elif args.prompt is None:
        parser.error("the following arguments are required: prompt")


    output_filename = args.output_file
    if not output_filename:
        # Generate a descriptive filename from the prompt
        sane_prompt = re.sub(r'[^a-zA-Z0-9_]+', '_', args.prompt)
        output_filename = "_".join(sane_prompt.split('_')[:5]) + ".mp4"

    # Save the current prompt and arguments to history
    new_entry = {
        "prompt": args.prompt,
        "output_file": output_filename,
        "duration": args.duration,
        "no_audio": args.no_audio,
        "no_enhance": args.no_enhance,
        "aspect_ratio": args.aspect_ratio,
    }
    history.append(new_entry)
    save_history(history)

    generate_video(args.prompt, output_filename, args.duration, args.no_audio, args.no_enhance, args.aspect_ratio)

if __name__ == "__main__":
    main()