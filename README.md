# Vidius

A CLI (`v0.2.1`) for generating and extending videos with Google's **Veo 3.1** models (`standard`, `fast`, `lite`). Serves as both a standalone video generator and the video leaf tool for **Mirage**.

See [SPEC.md](SPEC.md) for the full system specification, architecture, cost model, and requirement traceability.

## Installation

```bash
uv tool install --python 3.12 git+https://github.com/charles-forsyth/vidius.git
```

## Setup

Put a Gemini API key (restricted to `generativelanguage.googleapis.com`) in `~/.config/vidius/.env` (`chmod 600`):

```env
API_KEY=your_gemini_api_key_here
OUTPUT_DIR=/Users/yourname/Videos/Vidius
PERSON_GENERATION=allow_all
```

Without `API_KEY`, `vidius` falls back to Vertex AI with Application Default Credentials (`PROJECT_ID`, `LOCATION`).

Pick a tier with `-m standard|fast|lite` (default `standard`, Veo 3.1). Veo 3.0 and 2.0 were retired on 2026-06-30.

## Defaults

If run without flags, `vidius` uses:
* **Model**: `veo-3.1-generate-preview` (`standard`; pass `-m lite` for $0.05/s or `-m fast` for $0.10/s)
* **Duration**: `8` seconds (`4`, `6`, `8` supported)
* **Aspect Ratio**: `16:9` (`16:9`, `9:16` supported)
* **Audio**: Enabled
* **Person Generation**: `auto` (`allow_all` for text-to-video, `allow_adult` when images/videos are attached)
* **Output Directory**: `~/Videos/Vidius` (configurable in `.env`)
* **Output File**: Auto-slugged from prompt (or specify `-o path/to/file.mp4`)

## Usage Examples

### 1. Quick Start (Cheapest 4s Lite Tier)
```bash
vidius "A mountain stream flowing over mossy stones in morning light" -m lite -d 4
```

### 2. Image-to-Video (Start Frame)
```bash
vidius "The water begins to flow and birds fly" --image river_start.png -m lite
```

### 3. Start & End Frames (Interpolation)
```bash
vidius "A flower blooming in fast motion" --image bud.png --last-image flower.png
```

### 4. Reference Images (Up to 3)
```bash
vidius "A knight walking through a stone courtyard" \
  --ref-image character_sheet.png \
  --ref-image style_guide.png
```

### 5. Extend an Existing Veo Video
```bash
vidius "The character walks through the door into a bustling market" --extend-video part1.mp4
```

### 6. Vertical Video (Shorts / Reels)
```bash
vidius "A violinist performing on a lit stage" -ar 9:16 -d 6 -m lite
```

### 7. Custom Output Path
```bash
vidius "A quiet beach at dusk" -o ./local_beach.mp4 -m lite -d 4
```

## Development

```bash
uv sync --python 3.12
uv run --python 3.12 pytest
```
