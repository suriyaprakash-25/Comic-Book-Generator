"""
Pydantic models for the AI Comic Generator
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Panel(BaseModel):
    """Represents a single comic panel"""
    id: int = Field(..., description="Panel number/identifier")
    visual_prompt: str = Field(
        ..., 
        description="Detailed visual description of the scene and characters for image generation"
    )
    dialogue: str = Field(
        default="", 
        description="Text spoken by characters in this panel"
    )
    character_name: str = Field(
        default="", 
        description="Name of the main character in this panel"
    )


class ComicScript(BaseModel):
    """Complete comic script with all panels"""
    title: str = Field(default="Untitled Comic", description="Title of the comic")
    panels: List[Panel] = Field(..., description="List of comic panels")
    characters: List[str] = Field(
        default_factory=list, 
        description="List of unique character names in the comic"
    )


class StoryInput(BaseModel):
    """Input model for story text"""
    story: str = Field(..., description="The story text to convert into a comic")
    num_panels: int = Field(default=4, ge=1, le=8, description="Number of panels to generate")
    style_preset: str = Field(default="comic", description="Style preset: comic, manga, cinematic, 3d")


class GenerationResponse(BaseModel):
    """Response model for comic generation"""
    status: str
    message: str
    script: Optional[ComicScript] = None
    error: Optional[str] = None
