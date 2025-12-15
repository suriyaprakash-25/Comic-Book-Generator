"""
Image Generator Service - Stage 2 & 3: Character Designer + Cinematographer
Generates character reference sheets and comic panels using Hugging Face Inference API
"""

import os
import io
import uuid
from pathlib import Path
from typing import Optional, List
from PIL import Image
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
HF_TOKEN = os.getenv("HF_TOKEN")
OUTPUT_DIR = Path(__file__).parent.parent / "static" / "generated"

# Available models (in order of preference)
MODELS = {
    "flux": "black-forest-labs/FLUX.1-dev",
    "sdxl": "stabilityai/stable-diffusion-xl-base-1.0",
    "sdxl_turbo": "stabilityai/sdxl-turbo",
}

# Default model
DEFAULT_MODEL = "flux"

# Style presets for different art styles
STYLE_PRESETS = {
    "comic": ", american comic book style, vibrant colors, bold outlines, dynamic paneling, superhero comic art",
    "manga": ", japanese manga style, black and white, detailed ink shading, action lines, anime style, detailed linework",
    "cinematic": ", cinematic movie scene, 8k resolution, realistic lighting, photorealistic, movie still, dramatic composition",
    "3d": ", 3d render, pixar style, disney animation style, cute characters, soft lighting, vibrant colors, animated movie",
}


def get_style_suffix(style_preset: str) -> str:
    """Get the style suffix for a given preset"""
    return STYLE_PRESETS.get(style_preset, STYLE_PRESETS["comic"])


def get_inference_client() -> InferenceClient:
    """Get configured Hugging Face Inference Client"""
    if not HF_TOKEN or HF_TOKEN == "your_huggingface_token_here":
        raise ValueError("HF_TOKEN not configured. Please set it in .env file.")
    return InferenceClient(token=HF_TOKEN)


def ensure_output_dir() -> Path:
    """Ensure the output directory exists"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def generate_character_reference(
    character_name: str,
    character_description: str,
    style_preset: str = "comic",
    model_key: str = DEFAULT_MODEL
) -> dict:
    """
    Stage 2: Character Designer
    Generate a character reference sheet for consistency anchoring.
    
    Args:
        character_name: Name of the character
        character_description: Physical description of the character
        style_preset: Style preset key (comic, manga, cinematic, 3d)
        model_key: Which model to use (flux, sdxl, sdxl_turbo)
    
    Returns:
        dict with status, image_path, and image_url
    """
    try:
        client = get_inference_client()
        model = MODELS.get(model_key, MODELS["flux"])
        style_suffix = get_style_suffix(style_preset)
        
        # Construct the reference sheet prompt
        prompt = (
            f"Character reference sheet of {character_name}: {character_description}. "
            f"Full body portrait, front view, detailed face, "
            f"high quality, professional illustration, white background, "
            f"character design sheet, multiple angles, {style_suffix}"
        )
        
        # Generate the image
        image = client.text_to_image(
            prompt=prompt,
            model=model,
        )
        
        # Save the image
        output_dir = ensure_output_dir()
        filename = f"ref_{character_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}.png"
        filepath = output_dir / filename
        
        # Convert to PIL Image if needed and save
        if isinstance(image, bytes):
            image = Image.open(io.BytesIO(image))
        
        image.save(filepath, "PNG")
        
        return {
            "status": "success",
            "character_name": character_name,
            "image_path": str(filepath),
            "image_url": f"/static/generated/{filename}",
            "prompt_used": prompt
        }
        
    except Exception as e:
        return {
            "status": "error",
            "character_name": character_name,
            "error": str(e),
            "message": f"Failed to generate reference for {character_name}"
        }


def generate_panel(
    panel_id: int,
    visual_prompt: str,
    character_desc: str = "",
    style_preset: str = "comic",
    model_key: str = DEFAULT_MODEL
) -> dict:
    """
    Stage 3: Cinematographer
    Generate a comic panel image using prompt anchoring for consistency.
    
    Args:
        panel_id: Panel identifier
        visual_prompt: The visual description from the script
        character_desc: Character description to anchor consistency
        style_preset: Style preset key (comic, manga, cinematic, 3d)
        model_key: Which model to use
    
    Returns:
        dict with status, image_path, and image_url
    """
    try:
        client = get_inference_client()
        model = MODELS.get(model_key, MODELS["flux"])
        
        # Get style suffix from preset
        style_suffix = get_style_suffix(style_preset)
        
        # PROMPT ANCHORING: Prepend character description for consistency
        if character_desc:
            full_prompt = f"{character_desc}. {visual_prompt}{style_suffix}, highly detailed"
        else:
            full_prompt = f"{visual_prompt}{style_suffix}, highly detailed"
        
        # Generate the image
        image = client.text_to_image(
            prompt=full_prompt,
            model=model,
        )
        
        # Save the image
        output_dir = ensure_output_dir()
        filename = f"panel_{panel_id}_{uuid.uuid4().hex[:8]}.png"
        filepath = output_dir / filename
        
        # Convert to PIL Image if needed and save
        if isinstance(image, bytes):
            image = Image.open(io.BytesIO(image))
        
        image.save(filepath, "PNG")
        
        return {
            "status": "success",
            "panel_id": panel_id,
            "image_path": str(filepath),
            "image_url": f"/static/generated/{filename}",
            "prompt_used": full_prompt
        }
        
    except Exception as e:
        return {
            "status": "error",
            "panel_id": panel_id,
            "error": str(e),
            "message": f"Failed to generate panel {panel_id}"
        }


def generate_all_panels(
    panels: List[dict],
    character_descriptions: dict = None,
    style_preset: str = "comic",
    model_key: str = DEFAULT_MODEL
) -> dict:
    """
    Generate all panels for a comic script.
    
    Args:
        panels: List of panel dictionaries from the script
        character_descriptions: Dict mapping character names to descriptions
        style_preset: Style preset key (comic, manga, cinematic, 3d)
        model_key: Which model to use
    
    Returns:
        dict with status and list of generated panel results
    """
    if character_descriptions is None:
        character_descriptions = {}
    
    results = []
    
    for panel in panels:
        panel_id = panel.get("id", 0)
        visual_prompt = panel.get("visual_prompt", "")
        character_name = panel.get("character_name", "")
        
        # Get character description for anchoring
        char_desc = character_descriptions.get(character_name, "")
        
        # Generate the panel
        result = generate_panel(
            panel_id=panel_id,
            visual_prompt=visual_prompt,
            character_desc=char_desc,
            style_preset=style_preset,
            model_key=model_key
        )
        
        results.append(result)
    
    # Check overall status
    failed = [r for r in results if r["status"] == "error"]
    
    return {
        "status": "success" if not failed else "partial",
        "total_panels": len(panels),
        "successful": len(panels) - len(failed),
        "failed": len(failed),
        "panels": results
    }


def extract_character_description(panels: List[dict], character_name: str) -> str:
    """
    Extract a consistent character description from the first panel
    featuring that character.
    
    Args:
        panels: List of panel dictionaries
        character_name: Name of the character to find
    
    Returns:
        Character description string
    """
    for panel in panels:
        if panel.get("character_name") == character_name:
            # Extract character-related parts from the visual prompt
            visual_prompt = panel.get("visual_prompt", "")
            # Return the first sentence or portion that describes the character
            # This is a simple heuristic - the LLM should have put description first
            return visual_prompt.split(".")[0] if visual_prompt else ""
    return ""


# For testing
if __name__ == "__main__":
    import json
    
    # Test character reference generation
    print("Testing character reference generation...")
    result = generate_character_reference(
        character_name="Sir Edward",
        character_description="A medieval knight with short brown hair, blue eyes, wearing silver and blue armor with a golden crest",
        style="comic book style"
    )
    print(json.dumps(result, indent=2))
    
    # Test panel generation
    print("\nTesting panel generation...")
    panel_result = generate_panel(
        panel_id=1,
        visual_prompt="A knight facing a dragon in a rocky landscape at sunset",
        character_desc="A medieval knight with short brown hair, blue eyes, wearing silver and blue armor",
        style="comic book style"
    )
    print(json.dumps(panel_result, indent=2))
