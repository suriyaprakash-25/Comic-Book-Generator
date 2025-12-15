"""Quick test script for the API endpoints"""
import requests
import json
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_script():
    """Test Stage 1: Script Generation"""
    print("=" * 50)
    print("Testing Stage 1: Script Generation")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/generate-script"
    payload = {
        "story": "A knight fights a dragon",
        "num_panels": 2
    }
    
    response = requests.post(url, json=payload, timeout=120)
    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    return response.json()


def test_panel_generation():
    """Test Stage 3: Panel Generation"""
    print("\n" + "=" * 50)
    print("Testing Stage 3: Panel Generation")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/generate-panel"
    payload = {
        "panel_id": 1,
        "visual_prompt": "A knight in silver armor facing a dragon at sunset",
        "character_desc": "A medieval knight with short brown hair, blue eyes, wearing silver and blue armor",
        "style": "comic book style"
    }
    
    print("Generating panel image (this may take 30-60 seconds)...")
    response = requests.post(url, json=payload, timeout=180)
    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    return response.json()


def test_character_reference():
    """Test Stage 2: Character Reference Generation"""
    print("\n" + "=" * 50)
    print("Testing Stage 2: Character Reference Generation")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/generate-character-ref"
    payload = {
        "character_name": "Sir Edward",
        "character_description": "A medieval knight with short brown hair, blue eyes, wearing silver and blue armor with a golden crest",
        "style": "comic book style"
    }
    
    print("Generating character reference (this may take 30-60 seconds)...")
    response = requests.post(url, json=payload, timeout=180)
    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    return response.json()


def test_assembly():
    """Test Stage 4: Comic Assembly"""
    print("\n" + "=" * 50)
    print("Testing Stage 4: Comic Assembly")
    print("=" * 50)
    
    # Find existing panel images
    generated_dir = Path(__file__).parent / "static" / "generated"
    panel_files = list(generated_dir.glob("panel_*.png")) if generated_dir.exists() else []
    
    if not panel_files:
        print("No panel images found. Generate some panels first!")
        print("Run: python test_api.py panel")
        return None
    
    print(f"Found {len(panel_files)} panel images")
    
    url = f"{BASE_URL}/api/assemble-comic"
    payload = {
        "panel_images": [str(f) for f in panel_files[:4]],
        "dialogues": ["The battle begins!", "Face my wrath!", "You cannot defeat me!", "Victory is mine!"],
        "title": "Epic Battle"
    }
    
    print("Assembling comic page...")
    response = requests.post(url, json=payload, timeout=60)
    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    return response.json()


def test_full_pipeline():
    """Test Full Pipeline: All 4 Stages"""
    print("\n" + "=" * 50)
    print("Testing FULL PIPELINE (All 4 Stages)")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/generate-comic-full"
    payload = {
        "story": "A brave knight named Arthur discovers a baby dragon in the enchanted forest. Instead of fighting it, he decides to protect it from evil hunters.",
        "num_panels": 4,
        "style": "comic book style"
    }
    
    print("Running full pipeline (this may take 2-5 minutes)...")
    print("Stage 1: Generating script...")
    print("Stage 2: Extracting character descriptions...")
    print("Stage 3: Generating panel images...")
    print("Stage 4: Assembling comic page...")
    
    response = requests.post(url, json=payload, timeout=600)
    print(f"\nStatus Code: {response.status_code}")
    result = response.json()
    
    # Print summary
    print(f"\n{'='*50}")
    print("PIPELINE RESULT SUMMARY")
    print(f"{'='*50}")
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")
    print(f"\nPipeline Stages:")
    for stage, status in result.get('pipeline_stages', {}).items():
        emoji = "✅" if status == "completed" else "❌" if status == "failed" else "⏳"
        print(f"  {emoji} {stage}: {status}")
    
    if result.get('comic_page'):
        print(f"\n📖 Comic Page Generated!")
        print(f"   URL: {result['comic_page'].get('image_url')}")
        print(f"   Path: {result['comic_page'].get('image_path')}")
    
    return result


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            test_type = sys.argv[1]
            if test_type == "script":
                test_script()
            elif test_type == "panel":
                test_panel_generation()
            elif test_type == "character":
                test_character_reference()
            elif test_type == "assembly":
                test_assembly()
            elif test_type == "full":
                test_full_pipeline()
            else:
                print(f"Unknown test: {test_type}")
                print("Usage: python test_api.py [script|panel|character|assembly|full]")
        else:
            # Default: test script generation
            test_script()
    except Exception as e:
        print(f"Error: {e}")
