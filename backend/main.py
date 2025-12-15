"""
AI Comic Generator - Backend Server
FastAPI server with Hugging Face integration
"""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional

# Import schemas and services
from schemas import StoryInput, ComicScript, GenerationResponse
from services.story_generator import generate_script
from services.image_generator import (
    generate_character_reference,
    generate_panel,
    generate_all_panels,
    extract_character_description
)
from services.comic_assembler import assemble_comic_page, assemble_from_script

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Comic Generator",
    description="Transform text stories into visually consistent comic pages",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static files directory for generated images
STATIC_DIR = Path(__file__).parent / "static" / "generated"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Validate HF_TOKEN
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN or HF_TOKEN == "your_huggingface_token_here":
    print("⚠️  Warning: HF_TOKEN not configured. Set it in .env file.")
else:
    print("✅ Hugging Face token loaded successfully")


# Pydantic model for health response
class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    hf_configured: bool


class CharacterRefInput(BaseModel):
    """Input for character reference generation"""
    character_name: str
    character_description: str
    style_preset: str = "comic"


class PanelInput(BaseModel):
    """Input for single panel generation"""
    panel_id: int
    visual_prompt: str
    character_desc: str = ""
    style_preset: str = "comic"


# Routes
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    hf_configured = HF_TOKEN and HF_TOKEN != "your_huggingface_token_here"
    return HealthResponse(
        status="online",
        message="AI Comic Generator API is running!",
        hf_configured=hf_configured
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    hf_configured = HF_TOKEN and HF_TOKEN != "your_huggingface_token_here"
    return HealthResponse(
        status="healthy",
        message="Server is operational",
        hf_configured=hf_configured
    )


@app.post("/api/test-story")
async def test_story(input_data: StoryInput):
    """Test endpoint to verify story input"""
    return {
        "received_story": input_data.story,
        "num_panels": input_data.num_panels,
        "message": "Story received successfully! Pipeline stages coming soon."
    }


@app.post("/api/generate-script")
async def generate_script_endpoint(input_data: StoryInput):
    """
    Stage 1: The Director
    Generate a comic script from story text using LLM.
    """
    result = generate_script(input_data.story, input_data.num_panels)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Failed to generate script")
        )
    
    return result


@app.post("/api/generate-comic")
async def generate_comic(input_data: StoryInput):
    """
    Main endpoint to generate a comic from a story.
    Orchestrates all 4 stages of the pipeline.
    """
    # Stage 1: Generate script
    script_result = generate_script(input_data.story, input_data.num_panels)
    
    if script_result["status"] == "error":
        return {
            "status": "error",
            "message": script_result.get("error", "Failed at Stage 1"),
            "pipeline_stages": {
                "stage_1_director": "failed",
                "stage_2_character_designer": "pending",
                "stage_3_cinematographer": "pending",
                "stage_4_editor": "pending"
            }
        }
    
    return {
        "status": "success",
        "message": "Stage 1 (Director) completed!",
        "script": script_result.get("script"),
        "pipeline_stages": {
            "stage_1_director": "completed",
            "stage_2_character_designer": "pending",
            "stage_3_cinematographer": "pending",
            "stage_4_editor": "pending"
        }
    }


# ============== Stage 2: Character Designer ==============

@app.post("/api/generate-character-ref")
async def generate_character_ref_endpoint(input_data: CharacterRefInput):
    """
    Stage 2: Character Designer
    Generate a character reference sheet for consistency anchoring.
    """
    result = generate_character_reference(
        character_name=input_data.character_name,
        character_description=input_data.character_description,
        style_preset=input_data.style_preset
    )
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Failed to generate character reference")
        )
    
    return result


# ============== Stage 3: Cinematographer ==============

@app.post("/api/generate-panel")
async def generate_panel_endpoint(input_data: PanelInput):
    """
    Stage 3: Cinematographer
    Generate a single comic panel with prompt anchoring.
    """
    result = generate_panel(
        panel_id=input_data.panel_id,
        visual_prompt=input_data.visual_prompt,
        character_desc=input_data.character_desc,
        style_preset=input_data.style_preset
    )
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Failed to generate panel")
        )
    
    return result


@app.post("/api/generate-all-panels")
async def generate_all_panels_endpoint(
    panels: List[dict],
    character_descriptions: dict = None,
    style_preset: str = "comic"
):
    """
    Generate all panels for a comic script.
    """
    result = generate_all_panels(
        panels=panels,
        character_descriptions=character_descriptions or {},
        style_preset=style_preset
    )
    
    return result


# ============== Full Pipeline ==============

@app.post("/api/generate-comic-full")
async def generate_comic_full(input_data: StoryInput):
    """
    Full pipeline: Generate complete comic from story.
    Stages 1-4: Script → Character Refs → Panels → Assembly
    """
    pipeline_status = {
        "stage_1_director": "pending",
        "stage_2_character_designer": "pending",
        "stage_3_cinematographer": "pending",
        "stage_4_editor": "pending"
    }
    
    # Stage 1: Generate script
    script_result = generate_script(input_data.story, input_data.num_panels)
    
    if script_result["status"] == "error":
        pipeline_status["stage_1_director"] = "failed"
        return {
            "status": "error",
            "message": script_result.get("error", "Failed at Stage 1"),
            "pipeline_stages": pipeline_status
        }
    
    pipeline_status["stage_1_director"] = "completed"
    script = script_result.get("script", {})
    panels = script.get("panels", [])
    characters = script.get("characters", [])
    
    # Stage 2: Generate character descriptions from first appearances
    character_descriptions = {}
    for char_name in characters:
        desc = extract_character_description(panels, char_name)
        if desc:
            character_descriptions[char_name] = desc
    
    pipeline_status["stage_2_character_designer"] = "completed"
    
    # Stage 3: Generate all panels with character anchoring
    panels_result = generate_all_panels(
        panels=panels,
        character_descriptions=character_descriptions,
        style_preset=input_data.style_preset
    )
    
    if panels_result["status"] == "error":
        pipeline_status["stage_3_cinematographer"] = "failed"
        return {
            "status": "partial",
            "message": "Failed at Stage 3 (Panel Generation)",
            "script": script,
            "pipeline_stages": pipeline_status
        }
    
    pipeline_status["stage_3_cinematographer"] = "completed"
    
    # Stage 4: Assemble comic page with speech bubbles
    assembly_result = assemble_from_script(
        script=script,
        panel_results=panels_result.get("panels", [])
    )
    
    if assembly_result["status"] == "error":
        pipeline_status["stage_4_editor"] = "failed"
        return {
            "status": "partial",
            "message": "Failed at Stage 4 (Assembly)",
            "script": script,
            "panels": panels_result.get("panels", []),
            "pipeline_stages": pipeline_status
        }
    
    pipeline_status["stage_4_editor"] = "completed"
    
    return {
        "status": "success",
        "message": "Comic generation completed!",
        "script": script,
        "character_descriptions": character_descriptions,
        "panels": panels_result.get("panels", []),
        "comic_page": assembly_result,
        "pipeline_stages": pipeline_status
    }


# ============== Stage 4: Editor (Assembly) ==============

class AssembleInput(BaseModel):
    """Input for comic assembly"""
    panel_images: List[str]
    dialogues: List[str] = []
    title: str = "Comic"


@app.post("/api/assemble-comic")
async def assemble_comic_endpoint(input_data: AssembleInput):
    """
    Stage 4: The Editor
    Assemble panel images into a comic page with speech bubbles.
    """
    result = assemble_comic_page(
        panel_images=input_data.panel_images,
        dialogues=input_data.dialogues,
        title=input_data.title
    )
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Failed to assemble comic")
        )
    
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
