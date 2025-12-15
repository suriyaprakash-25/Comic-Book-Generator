"""
Comic Assembler Service - Stage 4: The Editor
Assembles generated panels into a comic page with speech bubbles
"""

import os
import uuid
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "static" / "generated"
FONTS_DIR = Path(__file__).parent.parent / "static" / "fonts"

# Comic layout settings
COMIC_SETTINGS = {
    "page_width": 1200,
    "page_height": 1600,
    "panel_gap": 20,
    "border_width": 3,
    "border_color": (0, 0, 0),  # Black
    "background_color": (255, 255, 255),  # White
    "bubble_color": (255, 255, 255),  # White
    "bubble_border_color": (0, 0, 0),  # Black
    "bubble_border_width": 2,
    "text_color": (0, 0, 0),  # Black
    "font_size": 18,
    "bubble_padding": 15,
    "bubble_radius": 20,
}


def ensure_output_dir() -> Path:
    """Ensure the output directory exists"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def get_font(size: int = 18) -> ImageFont.FreeTypeFont:
    """Get a font for text rendering"""
    # Try to load a comic-style font, fall back to default
    font_paths = [
        FONTS_DIR / "comic.ttf",
        FONTS_DIR / "ComicSans.ttf",
        "arial.ttf",
        "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    
    for font_path in font_paths:
        try:
            if isinstance(font_path, Path):
                if font_path.exists():
                    return ImageFont.truetype(str(font_path), size)
            else:
                return ImageFont.truetype(font_path, size)
        except (IOError, OSError):
            continue
    
    # Fall back to default font
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """Wrap text to fit within a maximum width"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        # Get text width
        try:
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = len(test_line) * (font.size * 0.6)
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def draw_speech_bubble(
    draw: ImageDraw.ImageDraw,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    settings: dict = None
) -> Tuple[int, int]:
    """
    Draw a speech bubble with text at the given position.
    Returns the size of the bubble (width, height).
    """
    if settings is None:
        settings = COMIC_SETTINGS
    
    padding = settings["bubble_padding"]
    max_bubble_width = 250
    
    # Wrap text
    lines = wrap_text(text, font, max_bubble_width - (padding * 2))
    
    if not lines:
        return (0, 0)
    
    # Calculate bubble size
    line_height = font.size + 5
    text_height = len(lines) * line_height
    
    max_line_width = 0
    for line in lines:
        try:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
        except:
            line_width = len(line) * (font.size * 0.6)
        max_line_width = max(max_line_width, line_width)
    
    bubble_width = max_line_width + (padding * 2)
    bubble_height = text_height + (padding * 2)
    
    x, y = position
    
    # Draw bubble background (rounded rectangle)
    bubble_rect = [x, y, x + bubble_width, y + bubble_height]
    radius = settings["bubble_radius"]
    
    # Draw rounded rectangle
    draw.rounded_rectangle(
        bubble_rect,
        radius=radius,
        fill=settings["bubble_color"],
        outline=settings["bubble_border_color"],
        width=settings["bubble_border_width"]
    )
    
    # Draw the tail (triangle pointing down)
    tail_points = [
        (x + bubble_width // 3, y + bubble_height),
        (x + bubble_width // 3 + 10, y + bubble_height),
        (x + bubble_width // 3 - 5, y + bubble_height + 20)
    ]
    draw.polygon(tail_points, fill=settings["bubble_color"], outline=settings["bubble_border_color"])
    
    # Draw text
    text_y = y + padding
    for line in lines:
        draw.text(
            (x + padding, text_y),
            line,
            font=font,
            fill=settings["text_color"]
        )
        text_y += line_height
    
    return (bubble_width, bubble_height + 20)  # Include tail height


def calculate_grid_layout(num_panels: int, page_width: int, page_height: int, gap: int) -> List[Tuple[int, int, int, int]]:
    """
    Calculate panel positions for a grid layout.
    Returns list of (x, y, width, height) for each panel.
    """
    if num_panels <= 0:
        return []
    
    # Determine grid dimensions
    if num_panels == 1:
        cols, rows = 1, 1
    elif num_panels == 2:
        cols, rows = 2, 1
    elif num_panels <= 4:
        cols, rows = 2, 2
    elif num_panels <= 6:
        cols, rows = 3, 2
    elif num_panels <= 9:
        cols, rows = 3, 3
    else:
        cols = 3
        rows = (num_panels + 2) // 3
    
    # Calculate panel dimensions
    panel_width = (page_width - (gap * (cols + 1))) // cols
    panel_height = (page_height - (gap * (rows + 1))) // rows
    
    positions = []
    for i in range(num_panels):
        row = i // cols
        col = i % cols
        x = gap + col * (panel_width + gap)
        y = gap + row * (panel_height + gap)
        positions.append((x, y, panel_width, panel_height))
    
    return positions


def assemble_comic_page(
    panel_images: List[str],
    dialogues: List[str] = None,
    title: str = "Comic",
    settings: dict = None
) -> dict:
    """
    Assemble multiple panel images into a single comic page.
    
    Args:
        panel_images: List of paths to panel images
        dialogues: List of dialogue text for each panel
        title: Title of the comic
        settings: Custom settings (optional)
    
    Returns:
        dict with status and output path
    """
    if settings is None:
        settings = COMIC_SETTINGS.copy()
    
    if dialogues is None:
        dialogues = [""] * len(panel_images)
    
    # Ensure dialogues list matches panels
    while len(dialogues) < len(panel_images):
        dialogues.append("")
    
    try:
        # Create the comic page canvas
        page = Image.new(
            "RGB",
            (settings["page_width"], settings["page_height"]),
            settings["background_color"]
        )
        draw = ImageDraw.Draw(page)
        
        # Calculate grid layout
        positions = calculate_grid_layout(
            len(panel_images),
            settings["page_width"],
            settings["page_height"],
            settings["panel_gap"]
        )
        
        # Get font
        font = get_font(settings["font_size"])
        
        # Place each panel
        for i, (image_path, dialogue) in enumerate(zip(panel_images, dialogues)):
            if i >= len(positions):
                break
            
            x, y, panel_width, panel_height = positions[i]
            
            # Load and resize panel image
            try:
                panel_img = Image.open(image_path)
                panel_img = panel_img.resize((panel_width, panel_height), Image.Resampling.LANCZOS)
                
                # Paste panel onto page
                page.paste(panel_img, (x, y))
                
                # Draw border
                draw.rectangle(
                    [x, y, x + panel_width, y + panel_height],
                    outline=settings["border_color"],
                    width=settings["border_width"]
                )
                
                # Add speech bubble if there's dialogue
                if dialogue and dialogue.strip():
                    bubble_x = x + 10
                    bubble_y = y + 10
                    draw_speech_bubble(draw, (bubble_x, bubble_y), dialogue, font, settings)
                    
            except Exception as e:
                # Draw placeholder for failed panel
                draw.rectangle(
                    [x, y, x + panel_width, y + panel_height],
                    fill=(200, 200, 200),
                    outline=settings["border_color"],
                    width=settings["border_width"]
                )
                draw.text(
                    (x + panel_width // 2 - 50, y + panel_height // 2),
                    f"Panel {i + 1} Error",
                    fill=(100, 100, 100),
                    font=font
                )
        
        # Save the assembled comic
        output_dir = ensure_output_dir()
        filename = f"comic_{title.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}.png"
        filepath = output_dir / filename
        
        page.save(filepath, "PNG", quality=95)
        
        return {
            "status": "success",
            "title": title,
            "image_path": str(filepath),
            "image_url": f"/static/generated/{filename}",
            "num_panels": len(panel_images),
            "page_size": (settings["page_width"], settings["page_height"])
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to assemble comic page"
        }


def assemble_from_script(script: dict, panel_results: List[dict]) -> dict:
    """
    Assemble a comic page from a script and generated panel results.
    
    Args:
        script: The comic script with panels and dialogues
        panel_results: Results from generate_all_panels
    
    Returns:
        dict with assembled comic info
    """
    title = script.get("title", "Untitled Comic")
    script_panels = script.get("panels", [])
    
    # Extract image paths and dialogues
    panel_images = []
    dialogues = []
    
    for i, panel_result in enumerate(panel_results):
        if panel_result.get("status") == "success":
            panel_images.append(panel_result["image_path"])
            
            # Get dialogue from script
            if i < len(script_panels):
                dialogues.append(script_panels[i].get("dialogue", ""))
            else:
                dialogues.append("")
        else:
            # Skip failed panels or use placeholder
            pass
    
    if not panel_images:
        return {
            "status": "error",
            "error": "No valid panel images to assemble",
            "message": "All panel generations failed"
        }
    
    return assemble_comic_page(
        panel_images=panel_images,
        dialogues=dialogues,
        title=title
    )


# For testing
if __name__ == "__main__":
    import json
    
    # Test with sample images
    print("Testing comic assembly...")
    
    # Check if there are any generated panels
    generated_dir = OUTPUT_DIR
    if generated_dir.exists():
        panel_files = list(generated_dir.glob("panel_*.png"))
        if panel_files:
            print(f"Found {len(panel_files)} panel images")
            
            result = assemble_comic_page(
                panel_images=[str(f) for f in panel_files[:4]],
                dialogues=["First dialogue!", "Second panel text.", "Action scene!", "The end."],
                title="Test Comic"
            )
            print(json.dumps(result, indent=2))
        else:
            print("No panel images found. Generate some panels first!")
    else:
        print(f"Output directory not found: {generated_dir}")
