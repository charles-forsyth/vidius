# Vidius

A professional CLI for generating videos using Vertex AI VEO models.

## Defaults

If run without flags, `vidius` uses:
*   **Duration**: 8 seconds
*   **Aspect Ratio**: 16:9 (Widescreen)
*   **Audio**: Enabled
*   **Enhance Prompt**: Enabled (Google's AI rewrites prompts for better quality)
*   **Person Generation**: `allow_adult`
*   **Output File**: Generated from prompt (e.g., `A_cat_eating_pizza.mp4`)

## Usage Examples

### 1. Quick Start
Just provide a prompt.
```bash
vidius "A cyberpunk city in the rain at night"
```

### 2. Image-to-Video (Start from Image)
Provide an input image to start the video generation.
```bash
vidius "The water begins to flow and birds fly" --image river_start.png
```

### 3. Vertical Video (Shorts/Reels)
Create a 6-second vertical video.
```bash
vidius "A dancer on stage" -ar 9:16 -d 6
```
*   **Supported Ratios**: `16:9`, `9:16`, `1:1`, `21:9`, `4:3`, `3:4`
*   **Supported Durations**: `4`, `6`, `8`

### 4. Custom Output Filename
Specify the output file name.
```bash
vidius "A quiet beach" -o my_beach_video.mp4
```

### 5. Raw Generation
Disable audio and prompt enhancement for exact control.
```bash
vidius "Abstract geometric shapes" --no-audio --no-enhance
```

### 6. Negative Prompting
Exclude specific elements (e.g., blurry or distorted features).
```bash
vidius "A sharp portrait of a man" -np "blurry, distorted, dark, low resolution"
```

### 7. History Management
List past prompts and rerun them.
```bash
# List history
vidius -H

# Rerun entry #3
vidius -r 3
```

### 8. Strict Person Policy
Ensure no people are generated.
```bash
vidius "A crowded market street" -pg dont_allow
```

## Installation

```bash
uv tool install git+https://github.com/charles-forsyth/vidius
```

## Configuration

Vidius reads configuration from `~/.config/vidius/.env`.
See `envfile.txt` for a template.
