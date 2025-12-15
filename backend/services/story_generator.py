"""
Story Generator Service - Stage 1: The Director
Converts raw story text into structured comic panel scripts using Hugging Face LLM
"""

import os
import json
import re
from typing import Optional
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Hugging Face Inference Client
HF_TOKEN = os.getenv("HF_TOKEN")

# Model to use - Meta Llama 3 8B Instruct (free tier compatible)
DEFAULT_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"


def get_inference_client() -> InferenceClient:
    """Get configured Hugging Face Inference Client"""
    if not HF_TOKEN or HF_TOKEN == "your_huggingface_token_here":
        raise ValueError("HF_TOKEN not configured. Please set it in .env file.")
    return InferenceClient(token=HF_TOKEN)


def create_system_prompt(num_panels: int) -> str:
    """Create the system prompt for the comic scriptwriter"""
    return f"""You are a professional comic book scriptwriter. Your task is to convert a story into exactly {num_panels} comic panels.

OUTPUT FORMAT: You must output ONLY valid JSON, no other text. Use this exact structure:
{{
    "title": "Comic Title",
    "panels": [
        {{
            "id": 1,
            "visual_prompt": "Detailed visual description of the scene. Include: character appearance (hair color, clothing, body type, facial features), setting details, lighting, mood, action/pose, camera angle.",
            "dialogue": "What the character says (or empty string if no dialogue)",
            "character_name": "Name of the main character in this panel"
        }}
    ],
    "characters": ["List", "of", "unique", "character", "names"]
}}

RULES:
1. visual_prompt must be HIGHLY detailed - describe character appearance consistently across panels
2. Include physical traits: hair color, eye color, clothing, accessories
3. Describe the scene: location, time of day, weather, background elements
4. Specify the action/pose and emotional expression
5. Keep dialogue concise and impactful
6. Maintain character consistency - same character should have same physical description
7. Output ONLY the JSON object, no markdown, no explanation"""


def create_user_prompt(story: str, num_panels: int) -> str:
    """Create the user prompt with the story"""
    return f"""Convert this story into exactly {num_panels} comic panels:

STORY:
{story}

Remember: Output ONLY valid JSON with detailed visual_prompt for each panel."""


def extract_json_from_response(response_text: str) -> dict:
    """Extract and parse JSON from LLM response, handling common issues"""
    # Try direct parsing first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in markdown code blocks
    json_patterns = [
        r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
        r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
        r'\{[\s\S]*\}',                   # Raw JSON object
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response_text)
        for match in matches:
            try:
                # Clean up the match
                clean_match = match.strip()
                if not clean_match.startswith('{'):
                    # Find the JSON object
                    start = clean_match.find('{')
                    if start != -1:
                        clean_match = clean_match[start:]
                
                return json.loads(clean_match)
            except json.JSONDecodeError:
                continue
    
    # Last resort: try to find and extract JSON object
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(response_text[start_idx:end_idx + 1])
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"Could not extract valid JSON from response: {response_text[:500]}...")


def generate_script(story_text: str, num_panels: int = 4) -> dict:
    """
    Generate a comic script from story text using Hugging Face LLM.
    
    Args:
        story_text: The story to convert into a comic script
        num_panels: Number of panels to generate (default: 4)
    
    Returns:
        dict: Parsed comic script with panels, or error information
    """
    try:
        # Get the inference client
        client = get_inference_client()
        
        # Create prompts
        system_prompt = create_system_prompt(num_panels)
        user_prompt = create_user_prompt(story_text, num_panels)
        
        # Call the LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = client.chat_completion(
            model=DEFAULT_MODEL,
            messages=messages,
            max_tokens=2000,
            temperature=0.7,
        )
        
        # Extract the response content
        response_text = response.choices[0].message.content
        
        # Parse JSON from response
        script_data = extract_json_from_response(response_text)
        
        # Validate required fields
        if "panels" not in script_data:
            raise ValueError("Response missing 'panels' field")
        
        # Ensure all panels have required fields
        for i, panel in enumerate(script_data["panels"]):
            if "id" not in panel:
                panel["id"] = i + 1
            if "visual_prompt" not in panel:
                raise ValueError(f"Panel {i+1} missing 'visual_prompt'")
            if "dialogue" not in panel:
                panel["dialogue"] = ""
            if "character_name" not in panel:
                panel["character_name"] = ""
        
        # Add title if missing
        if "title" not in script_data:
            script_data["title"] = "Untitled Comic"
        
        # Extract unique characters if not provided
        if "characters" not in script_data:
            characters = set()
            for panel in script_data["panels"]:
                if panel.get("character_name"):
                    characters.add(panel["character_name"])
            script_data["characters"] = list(characters)
        
        return {
            "status": "success",
            "script": script_data,
            "raw_response": response_text
        }
        
    except ValueError as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Configuration or parsing error"
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "message": "Failed to generate script"
        }


# For testing
if __name__ == "__main__":
    test_story = """
    A brave knight named Arthur discovers a baby dragon in the enchanted forest. 
    Instead of slaying it, he decides to protect it from evil hunters. 
    Together, they become unlikely friends and defenders of the realm.
    """
    
    result = generate_script(test_story, num_panels=4)
    print(json.dumps(result, indent=2))
