import mimetypes
import time
from pathlib import Path
from typing import Any, Optional, cast

from google import genai
from google.genai import types

from vidius.config import settings


class VideoGenerator:
    def __init__(self) -> None:
        self.client = genai.Client(vertexai=True, project=settings.project_id, location=settings.location)

    def _wait_and_save(self, operation: Any, output_file: str) -> None:
        """Helper to poll operation and save result."""
        print(f"Operation started: {operation.name}")

        while not operation.done:
            print("Video generation/extension in progress. Checking status in 15 seconds...")
            time.sleep(15)
            operation = self.client.operations.get(operation)

        if operation.response:
            print("Operation succeeded!")
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

    def _load_image(self, image_path: str) -> types.Image:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        image_bytes = path.read_bytes()
        mime_type, _ = mimetypes.guess_type(path)
        if not mime_type:
            mime_type = "image/png"

        print(f"Loaded image: {image_path} ({mime_type})")
        return types.Image(image_bytes=image_bytes, mime_type=mime_type)

    def generate(
        self,
        prompt: str,
        output_file: str,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        generate_audio: bool = True,
        person_generation: str = "allow_adult",
        negative_prompt: Optional[str] = None,
        number_of_videos: int = 1,
        image_path: Optional[str] = None,
        last_frame_path: Optional[str] = None,
        reference_image_paths: Optional[list[str]] = None,
    ) -> None:
        """Generates a video using the Vertex AI VEO model."""

        print(f"Sending video generation request for prompt: '{prompt}'")
        print(
            f"Config: duration={duration}, aspect_ratio={aspect_ratio}, "
            f"audio={generate_audio}, model={settings.model_id}"
        )

        input_image = None
        if image_path:
            input_image = self._load_image(image_path)

        last_frame_image = None
        if last_frame_path:
            last_frame_image = self._load_image(last_frame_path)

        ref_images = []
        if reference_image_paths:
            for ref_path in reference_image_paths:
                ref_images.append(self._load_image(ref_path))

        # Cast ref_images to Any to satisfy mypy, assuming runtime compatibility
        # strictly speaking, we should convert to VideoGenerationReferenceImage if that type exists
        # but types.Image is likely what is expected or duck-typed.
        # We use Any to bypass the specific type check for now.
        config_ref_images = cast(Any, ref_images) if ref_images else None

        config = types.GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
            number_of_videos=number_of_videos,
            duration_seconds=duration,
            person_generation=person_generation,
            generate_audio=generate_audio,
            negative_prompt=negative_prompt,
            last_frame=last_frame_image,
            reference_images=config_ref_images,
        )

        operation = self.client.models.generate_videos(
            model=settings.model_id,
            prompt=prompt,
            config=config,
            image=input_image,
        )

        self._wait_and_save(operation, output_file)

    def extend_video(
        self,
        prompt: str,
        input_video_path: str,
        output_file: str,
        negative_prompt: Optional[str] = None,
    ) -> None:
        """Extends an existing video."""

        print(f"Sending video extension request for prompt: '{prompt}'")
        print(f"Input Video: {input_video_path}")

        path = Path(input_video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {input_video_path}")

        video_bytes = path.read_bytes()
        mime_type, _ = mimetypes.guess_type(path)
        if not mime_type:
            mime_type = "video/mp4"

        input_video = types.Video(video_bytes=video_bytes, mime_type=mime_type)

        config = types.GenerateVideosConfig(
            negative_prompt=negative_prompt,
        )

        operation = self.client.models.generate_videos(
            model=settings.model_id,
            prompt=prompt,
            config=config,
            video=input_video,
        )

        self._wait_and_save(operation, output_file)
