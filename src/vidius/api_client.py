import mimetypes
import time
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from vidius.config import settings


class VideoGenerator:
    def __init__(self) -> None:
        self.client = genai.Client(vertexai=True, project=settings.project_id, location=settings.location)

    def generate(
        self,
        prompt: str,
        output_file: str,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        generate_audio: bool = True,
        enhance_prompt: bool = True,
        person_generation: str = "allow_adult",
        negative_prompt: Optional[str] = None,
        number_of_videos: int = 1,
        image_path: Optional[str] = None,
    ) -> None:
        """Generates a video using the Vertex AI VEO model."""

        print(f"Sending video generation request for prompt: '{prompt}'")
        print(
            f"Config: duration={duration}, aspect_ratio={aspect_ratio}, "
            f"audio={generate_audio}, model={settings.model_id}"
        )

        input_image = None
        if image_path:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Read image as bytes
            image_bytes = path.read_bytes()
            mime_type, _ = mimetypes.guess_type(path)
            if not mime_type:
                mime_type = "image/png"  # Default fallback

            print(f"Using input image: {image_path} ({mime_type})")
            input_image = types.Image(image_bytes=image_bytes, mime_type=mime_type)

        config = types.GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
            number_of_videos=number_of_videos,
            duration_seconds=duration,
            person_generation=person_generation,
            enhance_prompt=enhance_prompt,
            generate_audio=generate_audio,
            negative_prompt=negative_prompt,
        )

        operation = self.client.models.generate_videos(
            model=settings.model_id,
            prompt=prompt,
            config=config,
            image=input_image,
        )

        print(f"Operation started: {operation.name}")

        while not operation.done:
            print("Video generation in progress. Checking status in 15 seconds...")
            time.sleep(15)
            operation = self.client.operations.get(operation)

        if operation.response:
            print("Operation succeeded!")
            # Save the first video (since we default to 1, but handle list if needed)
            # Use 'Any' cast or check to satisfy mypy if structure is dynamic
            result = operation.result
            if result and hasattr(result, "generated_videos") and result.generated_videos:
                video_object = result.generated_videos[0].video
                if video_object:
                    video_object.save(output_file)
                    print(f"Video saved as {output_file}")
                else:
                    print("Video object is empty.")
            else:
                print("No videos returned in result.")
        else:
            print("Operation failed.")
            if operation.error:
                print(f"Error details: {operation.error}")
            raise Exception(f"Video generation failed: {operation.error}")
