
from pathlib import Path
import re

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="StoryVideo")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class StoryRequest(BaseModel):
    story: str = Field(min_length=1, max_length=20000)
    length_minutes: int = Field(default=1, ge=1, le=10)
    image_style: str = Field(default="cartoon")


def split_into_scenes(story: str, scene_count: int):
    # Split the story into sentences.
    sentences = re.split(r'(?<=[.!?])\s+', story.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return []

    # Combine sentences into a manageable number of scenes.
    scene_count = min(scene_count, len(sentences))
    scenes = []
    group_size = max(1, len(sentences) // scene_count)

    for i in range(0, len(sentences), group_size):
        scenes.append(" ".join(sentences[i:i + group_size]))

    return scenes[:20]


@app.get("/")
async def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/plan")
async def create_story_plan(request: StoryRequest):
    story = request.story.strip()

    if not story:
        raise HTTPException(status_code=400, detail="Please enter a story.")

    scene_count = request.length_minutes * 6
    scene_count = min(scene_count, 20)

    scene_texts = split_into_scenes(story, scene_count)

    if not scene_texts:
        raise HTTPException(status_code=400, detail="Could not read your story.")

    style = request.image_style.lower()

    if style not in ["cartoon", "realistic", "storybook"]:
        style = "cartoon"

    scenes = []

    for number, scene_text in enumerate(scene_texts, start=1):
        scenes.append({
            "scene_number": number,
            "story_text": scene_text,
            "image_style": style,
            "image_prompt": (
                f"Create a vertical 9:16 {style} story illustration. "
                f"Show this scene: {scene_text}. "
                "Use the same character appearances throughout the story. "
                "One still image, no text, no subtitles, no animation."
            )
        })

    return {
        "status": "planned",
        "message": f"Your story has been divided into {len(scenes)} scenes. Image and voice generation are the next step.",
        "scene_count": len(scenes),
        "scenes": scenes
    }

