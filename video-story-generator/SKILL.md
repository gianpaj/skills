---
name: video-story-generator
description:
  "Generates complete video stories from images or text. Supports flexible input
  (1-N images, pure text, or mixed), selectable duration (24/48/72s) and visual
  styles (Ghibli, Cyberpunk, Realistic, etc.). Handles script generation,
  subject reference images, frame generation, video segments, background music,
  and final video assembly with FFmpeg."
---

# Video Story Generator

## Overview

Automatically generates complete video stories from images or text descriptions.
The workflow covers story script generation, subject reference image creation,
sequential first-frame generation, video segment creation, background music
generation, and final video assembly with FFmpeg. Supports flexible input modes:
1-N images, pure text, or mixed.

## Interaction Rules

- **Language**: Detect user's conversation language; all outputs follow user's
  language. When displaying options, use only user's language (no bilingual
  display).
- **Conciseness**: Keep content concise, no rambling. Only ask what's necessary.
  Restrained politeness — forbidden: "Hello", "Okay", "Let me help you".
- **Options Display**: For any Q&A with options, use `genui-form-wizard` to
  display.
- **File Output**: Generated video/files must use this format to display in
  conversation:
  ```
  <deliver_assets>
  <item>
  <path>video or file path</path>
  </item>
  </deliver_assets>
  ```
  One `<item>` block per file, multiple files in the same `<deliver_assets>`.

## Input Modes

| Mode       | Input                    | Processing                                                          |
| ---------- | ------------------------ | ------------------------------------------------------------------- |
| Image Mode | 1-N images               | AI auto-identifies characters, generates script from image analysis |
| Text Mode  | Pure text description    | Generates script from text                                          |
| Mixed Mode | Images + text supplement | Images primary, text as supplement                                  |

- User can generate from just 1 image or just one sentence.
- User doesn't categorize images — AI auto-determines roles.

## Optional Parameters

### Duration Options

Display using `genui-form-wizard`:

- 24 seconds (4 segments × 6s) — Short film
- 48 seconds (8 segments × 6s) — Standard (default)
- 72 seconds (12 segments × 6s) — Long film

### Style Options (displayed for pure text mode)

Display using `genui-form-wizard`:

- Ghibli (warm and healing)
- Cyberpunk (sci-fi future)
- Realistic (natural and real)
- Watercolor (artistic hand-painted)
- Pixel (retro gaming)
- Anime (Japanese animation)
- Oil Painting (classical art)
- Minimalist (clean and modern)
- AI Recommended (auto-select based on content)

## Key Constraints

| Parameter            | Value                                                      |
| -------------------- | ---------------------------------------------------------- |
| Per segment duration | 6 seconds (fixed)                                          |
| Video resolution     | 768P (unified)                                             |
| Background music     | Instrumental without lyrics, duration = total video length |

## Environment Dependencies

FFmpeg is required. Check and install before execution:

```bash
if ! command -v ffmpeg &> /dev/null; then
  if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install ffmpeg
  elif [[ -f /etc/debian_version ]]; then
    sudo apt-get update && sudo apt-get install -y ffmpeg
  elif [[ -f /etc/redhat-release ]]; then
    sudo yum install -y ffmpeg
  fi
fi
```

## Directory Structure

```
output/
├── story_script.json       # Story script
├── subject_reference.png   # Subject reference image (consistency anchor)
├── frames/                 # First frame images
├── videos/                 # Video segments
├── bgm.mp3                 # Background music
├── merged/                 # Merge intermediate files
└── final_video.mp4         # Final video
```

## Workflow

### Step 0: Environment Check & Collect Input

1. Check if FFmpeg is available, install if not.
2. Receive user's images/text.
3. If user didn't specify duration, ask or use default 48 seconds.
4. If pure text mode and no style specified, display style options via
   `genui-form-wizard`.
5. Create output directories:
   ```bash
   mkdir -p output/frames output/videos output/merged
   ```

### Step 1: Generate Story Script

Delegate based on input mode:

- **Has images** → Follow
  [Image Analysis & Script Generation](#image-analysis--script-generation)
- **Pure text** → Follow [Text to Script Generation](#text-to-script-generation)
- **Output**: `output/story_script.json`

### Step 1.5: Subject Reference Image Generation

Follow [Subject Reference Generation](#subject-reference-generation).

- Generate subject reference image based on script's `analysis.subject`.
- Supports: characters/animals/objects/scenes and various subject types.
- Serves as visual consistency anchor for all subsequent frames.
- **Output**: `output/subject_reference.png`
- **[IMPORTANT] This step is key to visual consistency.**

### Step 2: First Frame Image Generation (Sequential)

Follow [First Frame Generation](#first-frame-generation).

- **Sequentially** generate first frame images based on script's `visual_desc`.
- Each frame uses: Subject reference image + Previous frame as dual reference.
- **Must generate frame by frame in order, cannot parallelize.**
- **Output**: `output/frames/frame_01.png` – `frame_N.png`

### Step 3: Video Segment Generation

Follow [Video Segment Generation](#video-segment-generation).

- Generate video segments from first frame images.
- Unified parameters: duration=6, resolution=768P.
- **Output**: `output/videos/segment_01.mp4` – `segment_N.mp4`

### Step 4: Background Music Generation _(Can execute in parallel with Step 3)_

Follow [Background Music Generation](#background-music-generation).

- Generate instrumental background music based on story mood.
- Music duration = Total video duration.
- **Output**: `output/bgm.mp3`

### Step 5: Video Concatenation & Music Overlay

Follow [Video Merge](#video-merge).

- Concatenate all video segments.
- Overlay background music.
- **Output**: `output/final_video.mp4`

### Step 6: Completion

Report to user:

- Final video path (display using `<deliver_assets>` format)
- Video duration
- Style used

## Execution Principles

1. **Flexible Input**: 1 image / N images / pure text / mixed — all can be
   processed.
2. **Fully Automatic**: After confirming input, automatically complete all
   steps.
3. **Parallel Processing**: Step 3 and Step 4 can be parallelized.
4. **Error Retry**: Auto-retry once if single resource generation fails.

---

## Image Analysis & Script Generation

### When to Use

When user provides images (with or without supplementary text).

### Tools Required

- `images_understand` — to analyze user-provided images
- `terminal` — to create directories

### Execution Steps

#### 1. Create Output Directory

```bash
mkdir -p output/frames output/videos output/merged
```

#### 2. Analyze Images and Generate Script

Use `images_understand` tool with the following prompt:

```
You are an experienced storyboard director. Please create a coherent video script consisting of {segment_count} shots based on the provided images.

[Key Task 0: Image Role Identification]
First analyze each image and determine its role:
- Subject image: Contains clear character/object/person
- Scene image: Mainly environment/background
- Style image: Reflects specific artistic style/tone
- Mixed image: Contains multiple elements simultaneously

If only 1 image, extract all elements from it (subject+scene+style).
If multiple images, comprehensively analyze their relationships.

[Key Task 1: Subject Feature Lock]
Extract no less than 3 core visual features of the protagonist from the images (e.g.: fur texture, eye color, accessories, body characteristics).
**Constraint**: In each generated `visual_desc`, these features must be forcibly repeated to prevent character appearance drift.
(Wrong example: "The cat ran...")
(Correct example: "The same brown tabby Maine Coon cat (yellow-green eyes, black ear tips) runs to the right...")

[Key Task 2: Visual Continuity Design]
- **Action Connection**: Segment N's ending action must set up Segment N+1's opening action.
- **Environment Gradient**: When switching scenes, must retain elements from previous scene as anchor.
- **Action Quantification**: Must specify action speed (slow/fast), direction (left/right/approaching camera), and magnitude.

[Output Requirements]
Generate strict JSON format:

{
  "analysis": {
    "subject": "Detailed subject features (must be very specific, for subsequent locking)",
    "scene": "Environment feature anchor",
    "style": "Lighting and art style definition",
    "image_roles": ["Image 1: subject+scene", "Image 2: style", ...]
  },
  "story_script": [
    {
      "segment_id": 1,
      "visual_desc": "[Shot type+style definition] + [Complete subject feature restatement] + [Specific environment location] + [Quantified action description]. [Lighting description]."
    },
    ... (total {segment_count} segments)
  ]
}

**Special Instructions**:
1. `visual_desc` is for AI painting models, must include English word prompts (e.g.: Cinematic shot, Ghibli style).
2. Ensure the last segment has a perfect ending feel.
3. Even with only 1 image, create a complete story arc.
```

#### 3. Save Script

Save generated JSON to `output/story_script.json`.

Add to the output JSON:

- `"input_mode": "image"`
- `"image_count": N`

### Processing Strategy for Different Image Counts

| Image Count | Processing Method                                                          |
| ----------- | -------------------------------------------------------------------------- |
| 1 image     | Extract all elements from single image, AI expands scene variations        |
| 2 images    | AI determines character relationships (e.g.: subject+scene, or two scenes) |
| 3 images    | Classic mode: Try to identify as subject/scene/style                       |
| 4+ images   | Comprehensive analysis, may serve as multiple scene nodes in story         |

### Notes

1. **Subject Feature Lock**: `visual_desc` must repeat subject's core features.
2. **Action Continuity**: Each segment's ending must set up next segment's
   opening.
3. **English Prompts**: `visual_desc` needs to include English style prompts.
4. **JSON Format**: Output must be valid JSON format.
5. **Flexible Adaptation**: Regardless of image count, generate complete usable
   script.

---

## Text to Script Generation

### When to Use

When user provides only text description (no images).

### Tools Required

- `terminal` — to create directories

### Execution Steps

#### 1. Create Output Directory

```bash
mkdir -p output/frames output/videos output/merged
```

#### 2. Determine Style

If user didn't specify style, recommend based on theme:

| Theme Type         | Recommended Style       |
| ------------------ | ----------------------- |
| Fairy tale/Fantasy | Ghibli, Watercolor      |
| Sci-fi/Future      | Cyberpunk, Minimalist   |
| Daily life/Warm    | Realistic, Anime        |
| Adventure/Action   | Anime, Realistic        |
| Nature/Scenery     | Oil Painting, Realistic |
| Retro/Nostalgic    | Pixel, Oil Painting     |

#### 3. Generate Script

Use LLM to generate script with this prompt:

```
You are an experienced storyboard director. Please create a coherent video script consisting of {segment_count} shots based on the user description.

[User Description]
{user_description}

[Visual Style]
{style_description}

[Key Task 1: Subject Design and Lock]
First, design the protagonist/subject's specific visual appearance based on user description, extract no less than 3 core visual features.
**Constraint**: In each generated `visual_desc`, these features must be forcibly repeated to prevent character appearance drift.

[Key Task 2: Visual Continuity Design]
- **Action Connection**: Segment N's ending action must set up Segment N+1's opening action.
- **Environment Gradient**: When switching scenes, must retain elements from previous scene as anchor.
- **Action Quantification**: Must specify action speed (slow/fast), direction (left/right/approaching camera), and magnitude.

[Output Requirements]
Generate strict JSON format:

{
  "analysis": {
    "subject": "Detailed subject features (must be very specific, for subsequent locking)",
    "scene": "Main environment features",
    "style": "{style_name} style: Lighting and art style definition"
  },
  "story_script": [
    {
      "segment_id": 1,
      "visual_desc": "[Shot type+style definition] + [Complete subject feature restatement] + [Specific environment location] + [Quantified action description]. [Lighting description]."
    },
    ... (total {segment_count} segments)
  ]
}

**Special Instructions**:
1. `visual_desc` is for AI painting models, must include English word prompts.
2. Style keywords must appear in each visual_desc.
3. Ensure the last segment has a perfect ending feel.
```

#### 4. Save Script

Save generated JSON to `output/story_script.json`.

Add to the output JSON:

- `"input_mode": "text"`
- `"style_used": "{style_name}"`

### Style Prompt Mapping

| Style        | Prompt Keywords                                              |
| ------------ | ------------------------------------------------------------ |
| Ghibli       | Ghibli style, soft lighting, hand-drawn animation, whimsical |
| Cyberpunk    | Cyberpunk, neon lights, futuristic city, dark atmosphere     |
| Realistic    | Photorealistic, natural lighting, detailed textures          |
| Watercolor   | Watercolor painting, soft edges, artistic, pastel colors     |
| Pixel        | Pixel art, 8-bit style, retro gaming aesthetic               |
| Anime        | Anime style, vibrant colors, expressive characters           |
| Oil Painting | Oil painting style, rich textures, classical art             |
| Minimalist   | Minimalist, clean lines, simple shapes, limited palette      |

### Notes

1. **Subject Consistency**: Even without images, design specific subject
   appearance in first segment, strictly restate in subsequent segments.
2. **Style Anchoring**: Each `visual_desc` must include style keywords.
3. **JSON Format**: Output must be valid JSON format.
4. **Compatible with Image Mode**: Output format completely consistent;
   subsequent steps connect seamlessly.

---

## Subject Reference Generation

### Purpose

Generate a high-quality "subject reference image" as the visual consistency
anchor throughout the entire video. All subsequent frames will use this
reference image.

### Supported Subject Types

- Human characters (humans, anime characters, etc.)
- Animal characters (cats, dogs, fantasy creatures, etc.)
- Objects/Products (cars, buildings, props, etc.)
- Scenes/Locations (cities, forests, interiors, etc.)

### Tools Required

- `gen_images` — to generate the reference image

### Input

- `output/story_script.json` → `analysis.subject` (subject feature description)
- Optional: User-provided subject reference images

### Execution Steps

#### 1. Read Character Features

Read `analysis.subject` from `output/story_script.json`, extract core visual
features.

#### 2. Determine Subject Type

| Type             | Judgment Basis                     | Reference Image Characteristics |
| ---------------- | ---------------------------------- | ------------------------------- |
| Character/Animal | Biological features in description | Front-facing, neutral pose      |
| Object/Product   | Item features in description       | 3/4 view, show details          |
| Scene/Location   | Environment-focused description    | Panorama or standard view       |

#### 3. Build Reference Image Prompt

**Prompt Structure:**

```
Character reference sheet, [detailed character feature description],
front-facing view, neutral pose, centered composition,
clean background, studio lighting, high detail,
consistent character design, reference image for animation,
same character as will appear throughout the video,
stable face, preserve features, detailed facial features,
high quality, 8k resolution
```

**Example:**

```
Character reference sheet, a brown tabby Maine Coon cat with yellow-green eyes,
black ear tips, fluffy fur, medium build,
front-facing view, neutral pose, centered composition,
clean background, studio lighting, high detail,
consistent character design, reference image for animation,
same character as will appear throughout the video,
stable face, preserve features, detailed facial features,
high quality, 8k resolution
```

#### 4. Generate Reference Image

**With User Reference Image Mode:**

```json
{
  "prompt": "[reference image prompt]",
  "output_file": "output/subject_reference.png",
  "reference_files": ["user-provided reference image"],
  "aspect_ratio": "1:1",
  "resolution": "2K"
}
```

**Pure Text Mode:**

```json
{
  "prompt": "[reference image prompt with style keywords]",
  "output_file": "output/subject_reference.png",
  "aspect_ratio": "1:1",
  "resolution": "2K"
}
```

### Reference Image Specifications

#### Character/Animal Type

| Element    | Requirement              |
| ---------- | ------------------------ |
| Angle      | Front-facing             |
| Pose       | Neutral standing/sitting |
| Background | Clean and simple         |
| Lighting   | Uniform studio lighting  |

#### Object/Product Type

| Element    | Requirement                  |
| ---------- | ---------------------------- |
| Angle      | 3/4 view, show details       |
| Background | Clean and simple             |
| Lighting   | Product photography lighting |

#### Scene/Location Type

| Element     | Requirement                            |
| ----------- | -------------------------------------- |
| Angle       | Panorama or standard establishing shot |
| Composition | Show environment characteristics       |
| Lighting    | Match scene atmosphere                 |

### Consistency Keywords

**Character/Animal:**

```
stable appearance, preserve features, consistent character design,
same character throughout, detailed features,
reference image for animation
```

**Object/Product:**

```
stable appearance, preserve details, consistent product design,
same object throughout, detailed features,
reference image for animation
```

**Scene/Location:**

```
stable atmosphere, preserve environment style, consistent location design,
same environment throughout, detailed features,
reference image for animation
```

### Notes

1. **Clean Background**: Reference image background should be clean to avoid
   interfering with subject feature extraction.
2. **Appropriate Angle**: Choose best display angle based on subject type.
3. **High Detail**: Subject details should be clear for subsequent reproduction.
4. **Single Subject**: One reference image contains only one main subject.
5. **Multi-Subject Scenes**: If story has multiple main subjects, generate
   independent reference images for each.

---

## First Frame Generation

### Purpose

Sequentially generate first frame images based on story script, using subject
reference + previous frame for visual consistency.

### Tools Required

- `gen_images` — to generate each frame

### Input

- Script data from `output/story_script.json`
- `output/subject_reference.png` (required)
- Optional: User-provided original reference images

### Character Consistency Strategy

```
Subject Reference Image ─────────────────────────────────────────────┐
     │                                                              │
     ▼                                                              ▼
  frame_01 ──→ frame_02 ──→ frame_03 ──→ ... ──→ frame_N
              (previous)    (previous)          (previous)
```

**Dual Reference Mechanism:**

1. **Subject Reference Image**: Ensure subject visual consistency
   (character/object/scene features)
2. **Previous Frame**: Ensure action/composition/lighting continuity

### Execution Steps

#### 1. Read Input

- Read `analysis` and `story_script` from `output/story_script.json`.
- Confirm `output/subject_reference.png` exists.

#### 2. Sequential Generation (Frame by Frame)

**Must generate frame by frame in order, cannot parallelize.**

##### Frame 1 (First Frame)

```json
{
  "prompt": "[visual_desc_1] + [consistency keywords]",
  "output_file": "output/frames/frame_01.png",
  "reference_files": ["output/subject_reference.png"],
  "aspect_ratio": "16:9",
  "resolution": "2K"
}
```

##### Frame 2–N (Subsequent Frames)

```json
{
  "prompt": "[visual_desc_N] + [consistency keywords]",
  "output_file": "output/frames/frame_0N.png",
  "reference_files": [
    "output/subject_reference.png",
    "output/frames/frame_0{N-1}.png"
  ],
  "aspect_ratio": "16:9",
  "resolution": "2K"
}
```

#### 3. Prompt Construction Rules

Each prompt must include:

```
[Style description: analysis.style].
[Scene description: analysis.scene].
[Subject description: analysis.subject].
[This segment's visual_desc].
same subject as reference image, stable appearance, preserve features,
consistent design, consistent lighting style,
high quality, cinematic shot, detailed texture, 8k resolution.
```

**Consistency Keywords (select based on subject type):**

Character/Animal:

```
same character as reference image,
stable appearance, preserve features,
consistent character design,
same outfit as reference,
consistent lighting style
```

Object/Product:

```
same object as reference image,
stable appearance, preserve details,
consistent product design,
consistent lighting style
```

Scene/Location:

```
same environment as reference image,
stable atmosphere, preserve style,
consistent location design,
consistent lighting style
```

### Generation Order (Strictly Execute)

```
1. Generate frame_01 (use subject reference image only)
2. Wait for frame_01 completion
3. Generate frame_02 (use subject reference image + frame_01)
4. Wait for frame_02 completion
5. Generate frame_03 (use subject reference image + frame_02)
...
N. Generate frame_N (use subject reference image + frame_{N-1})
```

**Parallel generation prohibited** — must wait for previous frame to complete
before generating next frame.

### Style Enhancement Keywords

| Style        | Enhancement Keywords                                         |
| ------------ | ------------------------------------------------------------ |
| Ghibli       | Ghibli style, soft lighting, hand-drawn animation, whimsical |
| Cyberpunk    | Cyberpunk, neon lights, futuristic city, dark atmosphere     |
| Realistic    | Photorealistic, natural lighting, detailed textures          |
| Watercolor   | Watercolor painting, soft edges, artistic, pastel colors     |
| Pixel        | Pixel art, 8-bit style, retro gaming aesthetic               |
| Anime        | Anime style, vibrant colors, expressive                      |
| Oil Painting | Oil painting style, rich textures, classical art             |
| Minimalist   | Minimalist, clean lines, simple shapes                       |

### Parameters

| Parameter          | Value                     | Description                        |
| ------------------ | ------------------------- | ---------------------------------- |
| reference_files[0] | subject_reference.png     | Subject reference image (required) |
| reference_files[1] | Previous frame (frame 2+) | Continuity reference               |
| aspect_ratio       | "16:9"                    | Video standard ratio               |
| resolution         | "2K"                      | Ensure quality                     |

### Performance Note

Due to sequential generation, total time = single frame time × frame count. This
is the necessary cost for ensuring character consistency and cannot be replaced
with parallelization.

---

## Video Segment Generation

### Purpose

Generate video segments from first frame images.

### Tools Required

- `gen_videos` — to generate video segments

### Input

- First frame images: `output/frames/frame_01.png` – `frame_N.png`
- Story script data from `output/story_script.json`

### Execution Steps

#### 1. Read Story Script

Read `story_script` data from `output/story_script.json`, get `segment_count`.

#### 2. Call gen_videos to Generate Videos

Since `gen_videos` allows max 5 requests per call, batch based on segment_count.

**Batching Strategy:**

- 4 segments → 1 batch
- 8 segments → 2 batches (5 + 3)
- 12 segments → 3 batches (5 + 5 + 2)

**Request Format:**

```json
{
  "video_requests": [
    {
      "prompt": "[This segment's visual_desc, add dynamic description]",
      "output_file": "output/videos/segment_01.mp4",
      "image_file": "output/frames/frame_01.png",
      "reference_type": "first_frame",
      "duration": 6,
      "resolution": "768P"
    }
  ]
}
```

### Parameter Requirements (Strictly Execute)

| Parameter      | Value         | Description                 |
| -------------- | ------------- | --------------------------- |
| duration       | 6             | Fixed 6 seconds per segment |
| resolution     | "768P"        | Unified resolution          |
| reference_type | "first_frame" | Use first frame as start    |

### Notes

1. **Unified Duration**: All videos must be 6 seconds.
2. **Unified Resolution**: All videos must be 768P to ensure seamless
   concatenation.
3. **Batch Generation**: `gen_videos` max 5 per call, need batching if exceeds.
4. **Dynamic Description**: Prompt should add action-related descriptions to
   enhance video dynamic effects.
5. **Flexible Quantity**: Generate corresponding quantity based on
   `segment_count`, not hardcoded.

---

## Background Music Generation

### Purpose

Generate instrumental background music matching the story mood.

### Tools Required

- `gen_music` — to generate background music

### Input

- Total video duration (seconds)
- Story script `output/story_script.json` (for analyzing mood tone)
- Optional: User-specified music style

### Execution Steps

#### 1. Analyze Story Mood

Extract overall mood tone from `story_script.json`'s `visual_desc`:

- Warm/Healing → Soft piano, acoustic
- Adventure/Action → Intense orchestral, epic orchestral
- Mysterious/Fantasy → Ethereal electronic, ambient
- Cheerful/Playful → Lively melody, playful
- Epic/Grand → Symphony, cinematic

#### 2. Build Music Generation Prompt

```
[Mood tone] + [Music type] + instrumental, no vocals, no lyrics + [Duration requirement]
```

Example:

```
Warm and heartfelt acoustic guitar melody, gentle piano accompaniment,
cinematic film score style, emotional and touching,
instrumental only, no vocals, no lyrics,
suitable for storytelling video, 48 seconds duration
```

#### 3. Call Music Generation Tool

Parameters:

- duration: Total video duration (e.g., 48 seconds)
- style: instrumental / no vocals
- prompt: Prompt built based on mood analysis

#### 4. Save Output

Save to `output/bgm.mp3`.

### Music Style Mapping

| Video Type         | Recommended Music Style                   |
| ------------------ | ----------------------------------------- |
| Warm Story         | soft piano, acoustic guitar, warm strings |
| Adventure Action   | epic orchestral, drums, brass             |
| Fairy Tale Fantasy | magical bells, harp, ethereal synth       |
| Daily Life Healing | lo-fi, jazz piano, ambient                |
| Epic Narrative     | cinematic orchestra, choir (humming)      |
| Natural Scenery    | ambient, nature sounds, peaceful          |

### Notes

1. **No Lyrics**: Prompt must emphasize instrumental, no vocals, no lyrics.
2. **Exact Duration**: BGM duration must equal total video duration.
3. **Mood Unity**: Music style needs to match overall video mood.
4. **Loop Friendly**: If duration is long, consider loopable style.

---

## Video Merge

### Purpose

Concatenate all video segments and overlay background music to produce the final
video.

### Tools Required

- `terminal` — to run FFmpeg commands

### Input

- Video segments: `output/videos/segment_01.mp4` – `segment_N.mp4`
- Background music: `output/bgm.mp3`
- Segment count from `output/story_script.json`

### Execution Steps

#### Step 1: Get Segment Count

Read `segment_count` from `output/story_script.json`, or scan `output/videos/`
directory to get actual segment count.

#### Step 2: Unify Video Resolution

Force scale each video segment to unified resolution 1280×720 (16:9):

```bash
segment_count=$(ls output/videos/segment_*.mp4 | wc -l)

for i in $(seq -w 1 $segment_count); do
  ffmpeg -y -i output/videos/segment_${i}.mp4 \
         -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" \
         -c:v libx264 -preset fast -crf 23 \
         -an \
         output/merged/scaled_${i}.mp4
done
```

#### Step 3: Create Concatenation List

```bash
rm -f output/merged/filelist.txt
for i in $(seq -w 1 $segment_count); do
  echo "file 'scaled_${i}.mp4'" >> output/merged/filelist.txt
done
```

#### Step 4: Concatenate Video (No Audio)

```bash
ffmpeg -y -f concat -safe 0 -i output/merged/filelist.txt \
       -c copy output/merged/video_only.mp4
```

#### Step 5: Overlay Background Music

```bash
ffmpeg -y -i output/merged/video_only.mp4 \
       -i output/bgm.mp3 \
       -c:v copy -c:a aac \
       -map 0:v:0 -map 1:a:0 \
       -shortest \
       output/final_video.mp4
```

#### Step 6: Verify Output

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 output/final_video.mp4
```

Expected output = segment_count × 6 seconds (minor variance allowed).

### FFmpeg Parameter Reference

| Parameter              | Description                       |
| ---------------------- | --------------------------------- |
| `-vf "scale=1280:720"` | Force scale to 720p               |
| `-c:v libx264`         | Use H.264 encoding                |
| `-an`                  | Remove audio track (Step 2)       |
| `-f concat`            | Use concat mode for concatenation |
| `-map 0:v:0`           | Use first input's video track     |
| `-map 1:a:0`           | Use second input's audio track    |
| `-shortest`            | Use shorter stream as reference   |

### Notes

1. **Unified Resolution**: Use scale filter to ensure all segments are 1280×720.
2. **Concat Then Overlay**: First concatenate video, then overlay complete BGM
   to avoid audio breaks.
3. **BGM Duration**: BGM should equal total video duration; use `-shortest` to
   ensure sync.
4. **Keep Intermediate Files**: `merged/` directory kept for debugging.
5. **Flexible Quantity**: Process based on actual segment count, not hardcoded.

---

## Tools Reference

| Tool                | Used In                                   | Purpose                          |
| ------------------- | ----------------------------------------- | -------------------------------- |
| `images_understand` | Image Analysis & Script Generation        | Analyze user-provided images     |
| `gen_images`        | Subject Reference, First Frame Generation | Generate images                  |
| `gen_videos`        | Video Segment Generation                  | Generate video clips from frames |
| `gen_music`         | Background Music Generation               | Generate instrumental BGM        |
| `terminal`          | Directory setup, Video Merge (FFmpeg)     | Run shell commands               |

## Common Mistakes to Avoid

1. **Parallel frame generation**: Frames MUST be generated sequentially — each
   frame depends on the previous one for continuity.
2. **Missing subject features in prompts**: Every `visual_desc` must repeat the
   subject's core visual features to prevent appearance drift.
3. **Wrong aspect ratios**: Reference images use 1:1; frames use 16:9. Do not
   mix these up.
4. **Forgetting consistency keywords**: Always append the appropriate
   consistency keywords based on subject type.
5. **Hardcoding segment counts**: Always derive segment count from the script or
   user's duration selection.
6. **Skipping resolution unification before merge**: All segments must be scaled
   to 1280×720 before concatenation.
7. **Music with vocals**: BGM must always be instrumental only — enforce "no
   vocals, no lyrics" in every music prompt.
8. **Directly calling generation tools as orchestrator**: All specific
   generation work must follow the detailed procedures in each section above.
