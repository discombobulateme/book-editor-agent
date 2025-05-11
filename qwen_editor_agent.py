import os
import glob
import re
import argparse
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_text_files():
    """Get a list of text files from the original-texts directory"""
    return glob.glob("original-texts/*.txt")

def get_review_notes(filename):
    """Get review notes for a text file if they exist"""
    base_name = os.path.basename(filename)
    review_file = os.path.join("review-notes", base_name)
    
    if os.path.exists(review_file):
        with open(review_file, "r") as f:
            return f.read()
    return None

def read_file_content(filename):
    """Read the content of a file"""
    with open(filename, "r") as f:
        return f.read()

def save_edited_text(filename, edited_content, model_name):
    """Save the edited text to the qwen-edited-texts directory with model name in filename"""
    # Extract just the filename from the path
    base_name = os.path.basename(filename)
    
    # Create the directory if it doesn't exist
    os.makedirs("qwen-edited-texts", exist_ok=True)
    
    # Split the base name into name and extension
    name, ext = os.path.splitext(base_name)
    
    # Get a shortened model identifier
    model_id = model_name
    
    # Create output path
    output_path = os.path.join("qwen-edited-texts", f"{name}-{model_id}{ext}")
    
    # Check if the file already exists and add a version number if it does
    version = 1
    while os.path.exists(output_path):
        # Increment version number and create a new filename
        output_path = os.path.join("qwen-edited-texts", f"{name}-{model_id}-{version}{ext}")
        version += 1
    
    # Write the edited content to the file
    with open(output_path, "w") as f:
        f.write(edited_content)
    
    print(f"Saved edited text to {output_path}")
    
    # Also save a copy to the edited-texts directory for comparison
    shared_output_path = os.path.join("edited-texts", f"{name}-{model_id}{ext}")
    
    # Check if the file already exists and add a version number if it does
    version = 1
    while os.path.exists(shared_output_path):
        # Increment version number and create a new filename
        shared_output_path = os.path.join("edited-texts", f"{name}-{model_id}-{version}{ext}")
        version += 1
    
    # Create the directory if it doesn't exist
    os.makedirs("edited-texts", exist_ok=True)
    
    # Write the edited content to the file
    with open(shared_output_path, "w") as f:
        f.write(edited_content)

def create_editing_prompt(original_text, review_notes, instructions_content):
    """Create a prompt for the AI to edit the text"""
    prompt = (
        "Edit the following text according to the style and structure guidelines below. "
        "The text should be academically sophisticated while remaining accessible. "
        "Use a mix of sentence structures and follow the Structured Experiential Theory approach.\n\n"
        
        "STYLE GUIDELINES:\n"
        f"{instructions_content}\n\n"
        
        "ORIGINAL TEXT:\n"
        f"{original_text}\n\n"
    )
    
    if review_notes:
        prompt += (
            "REVIEW NOTES TO ADDRESS:\n"
            f"{review_notes}\n\n"
        )
    
    prompt += (
        "INSTRUCTIONS:\n"
        "1. Edit the text to follow the style guidelines\n"
        "2. Incorporate any feedback from the review notes\n"
        "3. Return ONLY the edited text without any explanations, comments, or formatting\n"
    )
    
    return prompt

def get_available_models():
    """Return a dictionary of available Ollama models with their descriptions"""
    return {
        "mistral": "Fast and efficient 7B Mistral model",
        "llama2": "Fast Meta's LLama2 7B model",
        "mistral-openorca": "Instruction-tuned Mistral, good for complex tasks",
        "zephyr": "Fast but high-quality 7B instruction model"
    }

def call_ollama_api(model_name, prompt, max_tokens=4096):
    """Call the Ollama API to generate text"""
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": max_tokens
        }
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        result = response.json()
        return result.get('response', '')
    except requests.exceptions.RequestException as e:
        if "Connection refused" in str(e):
            raise ConnectionError(
                "Could not connect to Ollama. "
                "Please make sure Ollama is installed and running on your system. "
                "You can install it from https://ollama.com/ and run 'ollama serve' in a terminal."
            )
        else:
            raise e

def edit_text_with_ollama(text_file, model_name, instructions_content):
    """Edit a text file using Ollama API"""
    print(f"Processing {text_file} with {model_name}...")
    
    # Read the text file
    original_text = read_file_content(text_file)
    
    # Get review notes if they exist
    review_notes = get_review_notes(text_file)
    
    # Create prompt
    prompt = create_editing_prompt(original_text, review_notes, instructions_content)
    
    try:
        # Call Ollama API
        print(f"Sending request to Ollama for model {model_name}...")
        response = call_ollama_api(model_name, prompt)
        
        # Clean up the response if needed
        content = response.strip()
        
        print("Editing complete.")
        
        # Save the edited text
        save_edited_text(text_file, content, model_name)
        
        return content
        
    except Exception as e:
        print(f"Error processing {text_file}: {e}")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Book Editor Agent using Ollama")
    parser.add_argument("--model", "-m", 
                        default="mistral",
                        help="Ollama model to use for editing (e.g., mistral, llama2)")
    parser.add_argument("--list-models", "-l", action="store_true",
                        help="List available Ollama models with descriptions")
    
    args = parser.parse_args()
    
    # List models if requested
    if args.list_models:
        models = get_available_models()
        print("Available Ollama models:")
        for model, description in models.items():
            print(f"  {model}: {description}")
        return
    
    # Get text files
    text_files = get_text_files()
    
    if not text_files:
        print("No text files found in original-texts directory.")
        return
    
    # Read instructions for style guidelines
    try:
        instructions_content = read_file_content("INSTRUCTIONS.md")
    except FileNotFoundError:
        print("INSTRUCTIONS.md not found. Using default style guidelines.")
        instructions_content = "Default style guidelines: Academic yet accessible writing with clear explanations."
    
    # Process files individually
    for text_file in text_files:
        edit_text_with_ollama(text_file, args.model, instructions_content)

if __name__ == "__main__":
    main() 