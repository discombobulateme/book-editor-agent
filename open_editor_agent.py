#!/usr/bin/env python3
"""
Book Editor Agent - Open source LLMpowered text editor using Ollama models
"""

import os
import glob
import re
import argparse
import requests
import json
from dotenv import load_dotenv
import time
import traceback
import signal
import sys

# Import our terminal colors utility
from terminal_colors import Colors, print_header, print_subheader, print_stats, success, warning, error, info, debug

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
    """Save the edited text to the edited-texts directory with model name in filename"""
    # Extract just the filename from the path
    base_name = os.path.basename(filename)
    
    # Split the base name into name and extension
    name, ext = os.path.splitext(base_name)
    
    # Get the model identifier
    model_id = model_name
    
    # Create the directory if it doesn't exist
    os.makedirs("edited-texts", exist_ok=True)
    
    # Create output path
    output_path = os.path.join("edited-texts", f"{name}-{model_id}{ext}")
    
    # Check if the file already exists and add a version number if it does
    version = 1
    while os.path.exists(output_path):
        # Increment version number and create a new filename
        output_path = os.path.join("edited-texts", f"{name}-{model_id}-{version}{ext}")
        version += 1
    
    # Write the edited content to the file
    with open(output_path, "w") as f:
        f.write(edited_content)
    
    info(f"Saved edited text to {output_path}")
    return output_path

def get_model_type(model_name):
    """Determine the model type and display name based on the model name"""
    model_name = model_name.lower()
    if "mistral" in model_name:
        return "mistral", "MISTRAL"
    elif "llama3" in model_name:
        return "llama3", "LLAMA 3.1"
    elif "deepseek" in model_name:
        return "deepseek", "DEEPSEEK"
    else:
        return "", ""

def create_editing_prompt(original_text, review_notes, instructions_content, model_name=""):
    """Create a prompt for the AI to edit the text"""
    # Create our system message for the assistant
    system_message = (
        f"You are a professional editor skilled in enhancing text without losing content or nuance. "
        f"You will edit the provided text following the style guide and any specific instructions."
    )
    
    # Instructions section
    instructions = (
        f"## EDITING INSTRUCTIONS\n\n"
        f"1. Apply the style guide below to improve the text.\n"
        f"2. Preserve all important information, facts, and details from the original text.\n"
        f"3. Maintain the original text flow, organization, and paragraph structure.\n"
        f"4. If the review notes request shortening, make the text more concise while preserving key information.\n"
        f"5. Otherwise, maintain the original length and detail level.\n"
    )
    
    # Add instructions content (style guide)
    style_guide = f"## STYLE GUIDE\n\n{instructions_content}"
    
    # Examples section to illustrate good editing
    examples = (
        f"## EXAMPLES OF GOOD EDITING\n\n"
        f"Original: The car, which was red, drove down the street at a high rate of speed.\n"
        f"Good edit: The red car sped down the street.\n\n"
        
        f"Original: The CEO made an announcement that the company would be implementing new policies in the near future regarding remote work.\n"
        f"Good edit: The CEO announced the company would soon implement new remote work policies.\n"
    )
    
    # For Mistral specifically, add example of what not to do
    model_type, _ = get_model_type(model_name)
    if "mistral" in model_type:
        examples += (
            f"\n## WHAT NOT TO DO\n\n"
            f"DO NOT convert the text into a summary or abstract.\n"
            f"DO NOT merge paragraphs unless they are very short.\n"
            f"DO NOT remove important details or compress content excessively.\n"
        )
    
    # The document to edit
    content_to_edit = f"## TEXT TO EDIT\n\n{original_text}"
    
    # Review notes if provided
    notes_section = ""
    if review_notes:
        notes_section = f"## SPECIFIC EDITING REQUESTS\n\n{review_notes}"
    
    # Build final prompt
    prompt = f"{system_message}\n\n{instructions}\n\n{style_guide}\n\n{examples}\n\n{content_to_edit}"
    
    if notes_section:
        prompt += f"\n\n{notes_section}"
        
    prompt += "\n\n## YOUR EDITED TEXT\n\n"
    
    return prompt

def get_available_models():
    """Return a dictionary of available Ollama models with their descriptions"""
    return {
        "mistral": "Fast and efficient 7B Mistral model",
        "llama2": "Meta's LLama2 7B model",
        "llama3.1": "Meta's latest Llama 3.1, highly capable and efficient",
        "deepseek-r1": "DeepSeek R1 model with strong reasoning capabilities",
        "mistral-openorca": "Instruction-tuned Mistral, good for complex tasks",
        "zephyr": "Fast but high-quality 7B instruction model"
    }

def get_ollama_installed_models():
    """Get a list of models that are actually installed in Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            data = response.json()
            # Extract model names and creation dates
            models = []
            for model in data.get("models", []):
                model_name = model.get("name", "")
                size = model.get("size", 0) / (1024 * 1024 * 1024)  # Convert to GB
                models.append({
                    "name": model_name,
                    "size": f"{size:.1f} GB"
                })
            return models
        else:
            error(f"Failed to get installed models: HTTP {response.status_code}")
            return []
    except requests.exceptions.ConnectionError:
        error("Could not connect to Ollama server. Is Ollama running?")
        return []
    except Exception as e:
        error(f"Error fetching installed models: {str(e)}")
        return []

def call_ollama_api(model_name, prompt, base_url=None, temp_adjustment=0):
    """Call the Ollama API to get a response"""
    if base_url is None:
        base_url = "http://localhost:11434"  # Default Ollama URL
    
    api_url = f"{base_url}/api/generate"
    
    # Set up options with reasonable defaults
    options = {
        "temperature": 0.7 + temp_adjustment,  # Default temperature
        "top_k": 50,
        "top_p": 0.95,
        "repeat_penalty": 1.1,
        "num_predict": 8000,  # Generous token count for editing tasks
        "num_ctx": 16384      # Large context window
    }
    
    # Limit temperature to valid range
    options["temperature"] = min(0.95, max(0.1, options["temperature"]))
    
    # Print configuration
    info(f"🔄 API Configuration:")
    info(f"   • Model: {model_name}")
    info(f"   • Temperature: {options['temperature']:.2f}")
    
    # Prepare the request payload
    payload = {
        "model": model_name,
        "prompt": prompt,
        "options": options,
        "stream": False
    }
    
    start_time = time.time()
    info(f"⏳ Sending request to Ollama API...")
    
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        completion_time = time.time() - start_time
        success(f"Response received in {completion_time:.1f} seconds")
        
        result = response.json()
        
        # Handle error responses from Ollama
        if 'error' in result:
            error_msg = result.get('error', 'Unknown error')
            error(f"Ollama API error: {error_msg}")
            if "no models found" in error_msg.lower():
                info(f"💡 Tip: You might need to download the model first with 'ollama pull {model_name}'")
            raise Exception(f"Ollama API error: {error_msg}")
            
        return result.get('response', '')
        
    except requests.exceptions.ConnectionError:
        error(f"Connection error: Could not connect to Ollama at {base_url}")
        info(f"💡 Tip: Make sure Ollama is running with 'ollama serve'")
        raise Exception("Connection error: Could not connect to Ollama server")
        
    except requests.exceptions.RequestException as e:
        error(f"Request error: {str(e)}")
        raise Exception(f"Request error: {str(e)}")

def is_already_edited(filename, model):
    """Check if a file has already been edited by this model and has no review notes to incorporate"""
    base_name = os.path.basename(filename)
    name, ext = os.path.splitext(base_name)
    
    # Check if an edited version exists
    edited_glob = os.path.join("edited-texts", f"{name}-{model}*{ext}")
    edited_files = glob.glob(edited_glob)
    
    # If no edited version exists, the file needs editing
    if not edited_files:
        return False
    
    # If review notes exist, the file should be re-edited
    review_notes = get_review_notes(filename)
    if review_notes:
        return False
    
    # File has been edited and no review notes exist
    return True

def cleanup_response(text):
    """Clean up the response from the model by removing any metadata or notes at the end"""
    
    # Common endings that models might add
    ending_phrases = [
        "This text has been edited",
        "I have edited the text",
        "The edited text follows",
        "Here is the edited text",
        "I've maintained the full length",
        "I've preserved all content",
        "This edit maintains",
        "Edited according to",
        "Following the style guidelines",
        "As per the instructions",
    ]
    
    # Check for any of the ending phrases and remove them and anything that follows
    cleaned_text = text
    for phrase in ending_phrases:
        if phrase in cleaned_text:
            # Split on the phrase and take only what comes before it
            cleaned_text = cleaned_text.split(phrase)[0].strip()
    
    # Also remove anything after common markdown or comment delimiters if they appear near the end
    ending_delimiters = ["---", "***", "###", "```", "//"]
    for delimiter in ending_delimiters:
        # Only consider delimiters in the last 15% of the text to avoid removing content
        search_start = int(len(cleaned_text) * 0.85)
        last_part = cleaned_text[search_start:]
        if delimiter in last_part:
            # Find the position in the full text
            delimiter_pos = cleaned_text.rfind(delimiter, search_start)
            # Check if there's text after this delimiter that looks like metadata
            text_after = cleaned_text[delimiter_pos:].lower()
            if any(phrase.lower() in text_after for phrase in ["edit", "note", "comment", "text", "follow"]):
                cleaned_text = cleaned_text[:delimiter_pos].strip()
    
    return cleaned_text

def create_output_path(input_file, model_name="model"):
    """Create an output file path based on the input file path and model name"""
    # Extract the base name and extension
    file_name = os.path.basename(input_file)
    name, ext = os.path.splitext(file_name)
    
    # Create edited-texts directory at the root level if it doesn't exist
    output_dir = "edited-texts"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        info(f"📁 Created output directory: {output_dir}")
    
    # Create the output file path with model name included
    output_file = os.path.join(output_dir, f"{name}-{model_name}{ext}")
    
    # Check if the file already exists and add a version number if it does
    version = 1
    while os.path.exists(output_file):
        # Increment version number and create a new filename
        output_file = os.path.join(output_dir, f"{name}-{model_name}-{version}{ext}")
        version += 1
    
    return output_file

def edit_text(input_file, output_path=None, model_name="mistral", review_notes=None, instructions_file='INSTRUCTIONS.md', ollama_base_url=None):
    """Edit the text in the input file and save the result to the output file"""
    try:
        # Read the input file
        info(f"📄 Reading input file: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            original_text = f.read()
        
        # Read the style instructions
        info(f"📝 Reading style instructions from: {instructions_file}")
        with open(instructions_file, 'r', encoding='utf-8') as f:
            instructions_content = f.read()
            
        # Create output path if not provided
        if not output_path:
            output_path = create_output_path(input_file, model_name)
            
        # Handle cleanup on Ctrl+C
        def signal_handler(sig, frame):
            info(f"\n🛑 Editing process interrupted. Cleaning up...")
            if os.path.exists(output_path):
                info(f"Removing partial output file: {output_path}")
                os.remove(output_path)
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        
        # Create prompt
        info(f"🔍 Preparing editing prompt...")
        prompt = create_editing_prompt(original_text, review_notes, instructions_content, model_name)
        
        # Call the AI model
        info(f"🤖 Calling {model_name} to edit the text...")
        edited_text = call_ollama_api(model_name, prompt, ollama_base_url)
        
        # Check if we've lost too much content
        is_valid, message = validate_edited_text(original_text, edited_text, review_notes is not None, model_name)
        
        # If validation failed and review notes don't exist (so we shouldn't be shortening),
        # try the paragraph approach
        if not is_valid and not review_notes:
            warning(f"⚠️ {message}")
            info(f"🧩 Trying paragraph-by-paragraph approach...")
            edited_text = edit_by_paragraph(original_text, instructions_content, model_name, ollama_base_url)
        
        # Write the result to the output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(edited_text)
            
        # Get wordcounts for reporting
        original_wc = len(original_text.split())
        edited_wc = len(edited_text.split())
        diff_pct = ((edited_wc - original_wc) / original_wc) * 100 if original_wc > 0 else 0
            
        info(f"✅ Edited text saved to: {output_path}")
        info(f"📊 Word count: {original_wc} → {edited_wc} ({diff_pct:+.1f}%)")
        
        return output_path
        
    except Exception as e:
        error(f"\n❌ Error editing text: {str(e)}")
        traceback.print_exc()
        return None

def validate_edited_text(original_text, edited_text, review_notes_exist, model_name=""):
    """Validate the edited text against various criteria"""
    # Calculate basic statistics
    original_words = len(original_text.split())
    edited_words = len(edited_text.split())
    word_diff_percent = ((edited_words - original_words) / original_words) * 100
    
    # Count paragraphs by splitting on double newlines
    original_paragraphs = len([p for p in original_text.split("\n\n") if p.strip()])
    edited_paragraphs = len([p for p in edited_text.split("\n\n") if p.strip()])
    
    # Print statistics
    print_stats("Original text", f"{original_words} words, {original_paragraphs} paragraphs")
    print_stats("Edited text", f"{edited_words} words, {edited_paragraphs} paragraphs")
    print_stats("Word count change", f"{word_diff_percent:.1f}%")
    
    # Check for summary indicators
    summary_phrases = [
        "the text below", "this text", "this is a", "below is a", 
        "condensed version", "shorter version", "summary of"
    ]
    
    # Check the first 100 words for summary indicators
    first_100_words = " ".join(edited_text.split()[:100]).lower()
    has_summary_indicator = any(phrase in first_100_words for phrase in summary_phrases)
    
    if has_summary_indicator:
        warning(f"⚠️  WARNING: Edited text appears to be a summary rather than an edit.")
    
    # Determine validity based on the criteria
    is_valid = True
    validation_message = ""
    
    # If review notes don't exist (so we shouldn't be shortening),
    # check for significant length reduction
    if not review_notes_exist:
        # Allow up to 20% reduction by default
        threshold = -20
        
        # Check if the word count reduction exceeds the threshold
        if word_diff_percent < threshold:
            is_valid = False
            validation_message = (
                f"Text too short: {abs(word_diff_percent):.1f}% reduction when no shortening was requested."
            )
    
    # Check for paragraph structure issues only when we're not expecting shortening
    if not review_notes_exist and edited_paragraphs < original_paragraphs * 0.7 and original_paragraphs > 3:
        if not is_valid:  # If already invalid for another reason
            validation_message += f" Paragraphs have been merged or lost."
        else:
            is_valid = False
            validation_message = f"Paragraph structure changed significantly."
    
    # If we detected a summary indicator and no review notes, make it invalid
    if has_summary_indicator and not review_notes_exist:
        is_valid = False
        if validation_message:
            validation_message += " Text appears to be a summary."
        else:
            validation_message = "Text appears to be a summary rather than an edit."
    
    # Return validation result
    return is_valid, validation_message

def edit_by_paragraph(original_text, instructions_content, model_name, ollama_base_url=None):
    """Edit text one paragraph at a time as a fallback approach"""
    info(f"🧩 Using paragraph-by-paragraph approach for model: {model_name}")
    
    # Split the text into paragraphs
    paragraphs = [p for p in original_text.split("\n\n") if p.strip()]
    info(f"📋 Processing {len(paragraphs)} paragraphs...")
    
    edited_paragraphs = []
    
    # Process each paragraph
    for i, paragraph in enumerate(paragraphs):
        # Progress indicator
        progress = f"[{i+1}/{len(paragraphs)}]"
        info(f"{progress} Editing paragraph {i+1}...")
        
        # Create a simplified prompt for this paragraph
        paragraph_prompt = (
            f"Edit this paragraph following the style guide. Keep the full content and meaning.\n\n"
            f"STYLE GUIDE:\n{instructions_content}\n\n"
            f"PARAGRAPH:\n{paragraph}\n\n"
            f"EDITED PARAGRAPH:"
        )
        
        # Call the model and get the edited paragraph
        edited_paragraph = call_ollama_api(model_name, paragraph_prompt, ollama_base_url)
        edited_paragraphs.append(edited_paragraph.strip())
        
        # Show minimal progress feedback
        word_diff = len(edited_paragraph.split()) - len(paragraph.split())
        info(f"{progress} Complete: {word_diff:+} words change")
    
    # Join all paragraphs with double newlines
    edited_text = "\n\n".join(edited_paragraphs)
    
    # Validate the result
    validation_result = validate_edited_text(original_text, edited_text, False, model_name)
    
    return edited_text

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Edit text file based on style guidelines using Ollama API")
    parser.add_argument("files", nargs="*", help="Path to text file(s) to edit (optional if using --batch)")
    parser.add_argument("--model", default="mistral", help="Model name to use (default: mistral)")
    parser.add_argument("--instructions", default="INSTRUCTIONS.md", help="Path to style instructions file (default: INSTRUCTIONS.md)")
    parser.add_argument("--ollama-url", default=None, help="Ollama API base URL (default: http://localhost:11434)")
    parser.add_argument("--review", help="Path to review notes file")
    parser.add_argument("--batch", "-b", action="store_true", help="Process all files in original-texts directory")
    parser.add_argument("--list-models", "-l", action="store_true", help="List installed Ollama models")
    args = parser.parse_args()
    
    # List models if requested
    if args.list_models:
        print_header("INSTALLED OLLAMA MODELS")
        installed_models = get_ollama_installed_models()
        if not installed_models:
            warning("No models found or Ollama is not running")
            info("💡 Tip: Start Ollama with 'ollama serve' and make sure it's running")
            return
        
        # Print table of models
        print_subheader("Model Name | Size")
        print_subheader("----------|-----")
        for model in installed_models:
            info(f"{model['name']} | {model['size']}")
        
        # Print suggestion for recommended models
        print_subheader("\nRECOMMENDED MODELS")
        info("If you don't see the models you need, you can pull them with:")
        info("  ollama pull mistral      # good all-around model")
        info("  ollama pull llama3.1     # high quality")
        info("  ollama pull zephyr       # fast and efficient")
        return
    
    # Read the style instructions
    try:
        with open(args.instructions, 'r', encoding='utf-8') as f:
            instructions_content = f.read()
            info(f"\n✅ Loaded style instructions from {args.instructions}")
    except Exception as e:
        info(f"\n❌ Error reading style instructions: {str(e)}")
        info("Make sure the file exists and contains the style guidelines.")
        return
    
    # Read review notes if provided
    review_notes = None
    if args.review:
        try:
            with open(args.review, 'r', encoding='utf-8') as f:
                review_notes = f.read()
                info(f"\n✅ Loaded review notes from {args.review}")
                info(f"📝 Review notes:")
                info(f"{Colors.REVIEW_NOTES}{review_notes}")
        except Exception as e:
            info(f"\n❌ Error reading review notes: {str(e)}")
            info("Processing will continue without review notes.")
    
    # Determine which files to process
    files_to_process = []
    if args.batch:
        # Process all files in original-texts directory
        files_to_process = get_text_files()
        if not files_to_process:
            info("\n❌ No text files found in original-texts directory.")
            return
        info(f"\n✅ Batch mode: Found {len(files_to_process)} text files to process")
    elif args.files:
        # Process specific files provided as arguments
        files_to_process = args.files
    else:
        # No files specified and no batch mode
        info("\n❌ Error: No files specified. Please provide files or use --batch option.")
        parser.print_help()
        return
    
    # Process files individually
    for text_file in files_to_process:
        info(f"\n{Colors.SEPARATOR}{'='*80}")
        info(f"{Colors.HEADER}🔄 PROCESSING: {text_file} with model {args.model}")
        info(f"{Colors.SEPARATOR}{'='*80}")
        info("")
        
        # Skip if already edited (for batch mode)
        if args.batch and is_already_edited(text_file, args.model):
            info(f"⏭️  Skipping {text_file} - already edited by {args.model} and no review notes found.")
            continue
        
        output_file = create_output_path(text_file, args.model)
        result = edit_text(
            input_file=text_file,
            output_path=output_file,
            model_name=args.model,
            review_notes=review_notes,
            instructions_file=args.instructions,
            ollama_base_url=args.ollama_url
        )
        
        if result:
            info(f"✅ Successfully processed {text_file}")
        else:
            info(f"❌ Failed to process {text_file}")
            
    info(f"\n🎉 Editing process complete!")

if __name__ == "__main__":
    main() 