"""
Services module for AI Comic Generator
"""

from .story_generator import generate_script
from .image_generator import (
    generate_character_reference,
    generate_panel,
    generate_all_panels,
    extract_character_description
)
from .comic_assembler import (
    assemble_comic_page,
    assemble_from_script,
    COMIC_SETTINGS
)

__all__ = [
    "generate_script",
    "generate_character_reference",
    "generate_panel",
    "generate_all_panels",
    "extract_character_description",
    "assemble_comic_page",
    "assemble_from_script",
    "COMIC_SETTINGS"
]
