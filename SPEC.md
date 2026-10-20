# vidius specification

Version 0.2.1 (2026-10-20; code 0.2.1). Owner: Chuck Forsyth.
Repository: `charles-forsyth/vidius` (local checkout `~/Projects/vidius`). License: MIT.

## 1. Purpose and scope

`vidius` is the primary Veo 3.1 video generation CLI used both interactively and as the video leaf tool beneath **Mirage** (`~/Projects/mirage`). It supports:

1. **Text-to-Video** (`vidius "prompt"`)
2. **Image-to-Video (Start Frame)** (`-i start.png`)
3. **Start & End Frame Interpolation** (`-i start.png -li end.png`)
4. **Reference-Guided Generation** (`-ri ref1.png -ri ref2.png`, up to 3 asset references)
5. **Video Extension** (`-e prev.mp4`)

## 2. Design decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | Dedicated per-tool config `~/.config/vidius/.env` (`0600`) | Loaded via `pydantic-settings` (`Settings`). Never shares keys via `~/.env`. |
| D2 | Dual backend support (Gemini Developer API vs Vertex AI) with automatic parameter adaptation | When `API_KEY` is set in `~/.config/vidius/.env`, `VideoGenerator` uses `genai.Client(api_key=settings.api_key)`. Because the Gemini Developer API rejects `generate_audio` and `enhance_prompt` in `GenerateVideosConfig` (audio and prompt enhancement are always on), `api_client.py` omits those fields in API-key mode and calls `client.files.download(file=video_object)` before `video_object.save(output_file)`. |
| D3 | Automatic `person_generation` policy selection (`auto`) | Veo 3.1 allows `allow_all` for pure text-to-video but requires `allow_adult` whenever an input image, last frame, reference image, or input video is supplied. `--person-generation auto` (default) selects the right policy automatically. |
| D4 | Output directory routing (`~/Videos/Vidius`) | Bare filenames (`-o clip.mp4` or auto-slugged prompts) are placed inside `settings.output_dir` (`~/Videos/Vidius` by default); paths containing a directory separator (`-o ./clip.mp4` or `/abs/path/clip.mp4`) are written to the exact path specified (used by Mirage when rendering into a run folder). |

## 3. Architecture

```text
vidius CLI (src/vidius/main.py)
  |-- Settings (src/vidius/config.py)
  |     `-- ~/.config/vidius/.env (API_KEY, PROJECT_ID, LOCATION, MODEL_ID, OUTPUT_DIR)
  |-- History manager (src/vidius/history.py)
  |     |-- -H / --history -> list_history()
  |     `-- -r / --rerun ID -> get_entry_by_id()
  |-- Output path & model alias resolution (main.py -> resolve_model())
  |     |-- standard -> veo-3.1-generate-preview
  |     |-- fast     -> veo-3.1-fast-generate-preview
  |     `-- lite     -> veo-3.1-lite-generate-preview
  `-- VideoGenerator (src/vidius/api_client.py)
        |-- genai.Client(api_key=...) or genai.Client(vertexai=True, project=..., location=...)
        |-- _load_image() / _load_video()
        |-- generate_video() -> client.models.generate_videos(...)
        `-- _wait_and_save() -> 15s polling loop -> client.files.download() -> video_object.save()
```

### Module map

| File | Responsibility |
|---|---|
| `src/vidius/main.py` | CLI argument parser, `resolve_model()`, output path resolution, history recording, `main()`. |
| `src/vidius/config.py` | `MODELS` map (`standard`, `fast`, `lite`), `Settings` (`pydantic-settings`) loading `~/.config/vidius/.env`. |
| `src/vidius/api_client.py` | `VideoGenerator` (`_wait_and_save`, `_load_image`, `_load_video`, `generate_video`). |
| `src/vidius/history.py` | `HistoryManager` reading/writing prompt history JSON. |

## 4. Models and cost model

| Tier alias (`-m`) | Model ID | Resolution / Audio | List price (USD / second) | 4s clip | 6s clip | 8s clip |
|---|---|---|---|---|---|---|
| `lite` | `veo-3.1-lite-generate-preview` | 720p w/ audio | $0.05 / s | $0.20 | $0.30 | $0.40 |
| `fast` | `veo-3.1-fast-generate-preview` | 720p w/ audio | $0.10 / s | $0.40 | $0.60 | $0.80 |
| `standard` (default) | `veo-3.1-generate-preview` | 720p w/ audio | $0.40 / s | $1.60 | $2.40 | $3.20 |

## 5. Configuration (`~/.config/vidius/.env`)

| Variable | Field | Default | Description |
|---|---|---|---|
| `API_KEY` | `settings.api_key` | `None` | Gemini API key restricted to `generativelanguage.googleapis.com`. |
| `PROJECT_ID` | `settings.project_id` | `"ucr-research-computing"` | GCP project ID for Vertex AI fallback when `API_KEY` is unset. |
| `LOCATION` | `settings.location` | `"us-central1"` | GCP region for Vertex AI fallback. |
| `MODEL_ID` | `settings.model_id` | `"veo-3.1-generate-preview"` | Default Veo model ID or tier alias. |
| `OUTPUT_DIR` | `settings.output_dir` | `~/Videos/Vidius` | Default output directory for bare filenames. |
| `HISTORY_FILE` | `settings.history_file` | `.history.json` | Prompt history file path. |

## 6. CLI interface

```text
vidius [prompt]
       [-i IMAGE | --image IMAGE]
       [-li LAST_IMAGE | --last-image LAST_IMAGE]
       [-ri REF_IMAGE | --ref-image REF_IMAGE ...]   # max 3
       [-e EXTEND_VIDEO | --extend-video EXTEND_VIDEO]
       [-o OUTPUT_FILE | --output-file OUTPUT_FILE]
       [-d {4,6,8} | --duration {4,6,8}]             # default: 8
       [-ar {16:9,9:16} | --aspect-ratio {16:9,9:16}] # default: 16:9
       [-na | --no-audio]
       [-np TEXT | --negative-prompt TEXT]
       [-pg {auto,allow_all,allow_adult,dont_allow} | --person-generation ...]
       [-H | --history]
       [-r ID | --rerun ID]
       [-m MODEL | --model MODEL]                    # standard, fast, lite, or full ID
       [-v | --version]
```

## 7. Requirements traceability

| ID | Requirement | Verified by |
|---|---|---|
| REQ-CLI-1 | Basic prompt generation invokes `VideoGenerator.generate_video` with default 8s duration, 16:9 aspect ratio, and `audio=True`. | `tests/test_main.py::test_main_prompt_only` |
| REQ-CLI-2 | `--no-audio` passes `enable_audio=False` to `generate_video`. | `tests/test_main.py::test_main_no_audio` |
| REQ-CLI-3 | `--history` lists recorded runs and exits cleanly without calling the API. | `tests/test_main.py::test_main_history` |
| REQ-MODEL-1 | `-m lite|fast|standard` resolves to the corresponding `veo-3.1-*-generate-preview` model ID. | `tests/test_main.py::test_model_alias_resolves` |
| REQ-AUTH-1 | When `settings.api_key` is set, `VideoGenerator` initializes `genai.Client(api_key=...)` and omits Vertex-only `generate_audio` from `GenerateVideosConfig`. | `tests/test_main.py::test_client_uses_api_key`, `test_api_key_mode_omits_generate_audio` |

## 8. Known gaps and backlog

- **K1 (Confirmed):** `settings.history_file` defaults to `.history.json` in the current working directory rather than `~/.config/vidius/history.json`.
- **K2 (Confirmed):** `_wait_and_save()` polls until `operation.done` without an upper wall-clock timeout; adding a 15-minute ceiling and transient `503/429` retry backoff inside `api_client.py` (currently handled by Mirage's retry wrapper when called from Mirage) will harden standalone runs.
