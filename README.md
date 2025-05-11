# Book Editor Agent

An AI-powered text editor that applies style guidelines to text files using either Claude API or local open-source models via Ollama.

## Features

- Support for Claude (Anthropic) models and Ollama-based models (Mistral, Llama, DeepSeek)
- Smart handling to prevent models from summarizing content
- Paragraph-by-paragraph editing for challenging content
- Review note handling for specific editing requests

## Setup

1. Clone this repository
   ```bash
   git clone https://github.com/discombobulateme/book-editor-agent.git
   cd book-editor-agent
   ```

2. Set up Python environment
   ```bash
   # Create and activate virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Update pip and install dependencies
   pip install --upgrade pip
   pip install -r requirements.txt   # This installs anthropic==0.51.0 (latest)
   ```

3. Configure your environment
   - Create a `.env` file in the project root
   - For Claude: Add `ANTHROPIC_API_KEY=your_api_key_here`
   - For local models: [Install Ollama](https://ollama.com/download)
   
4. Download required models
   ```bash
   # For local Ollama models
   ollama pull mistral    # Fast 7B model, good general choice
   ollama pull llama3.1   # High quality but larger
   ollama pull deepseek-r1 # Strong reasoning capabilities
   
   # Claude models are available via API once key is configured
   ```

5. Prepare your content
   - Place text files in `original-texts/` directory
   - Optional: Create style guide as `INSTRUCTIONS.md`
   - Optional: Create review notes (explained below)

## Understanding Review Notes

Review notes are specific editing instructions for a particular text file:

1. You can provide them in two ways:
   - Same-named file in `review-notes/` directory (e.g., `review-notes/chapter1.txt` for `original-texts/chapter1.txt`)
   - Directly via command line with the `--review` flag

2. Review notes contain feedback such as:
   ```
   Please make the introduction more engaging.
   Simplify paragraph 3 - it's too technical.
   Use more academic language throughout.
   ```

3. The AI will follow these instructions while applying the style guide.

## Usage

### Using Claude API

```bash
# Basic usage with default model
python3 book_editor_agent.py

# List available Claude models
python3 book_editor_agent.py --list-models

# Use specific model
python3 book_editor_agent.py --model claude-3-sonnet-20240229

# Process all files in batch mode
python3 book_editor_agent.py --batch
```

### Using Ollama (Local Models)

```bash
# Edit a specific file with default model (mistral)
python3 open_editor_agent.py path/to/text.txt

# Use specific model and custom style guide
python3 open_editor_agent.py file.txt --model llama3.1 --instructions custom_style.md

# Process with review notes
python3 open_editor_agent.py file.txt --review path/to/review-notes.txt

# Process all files in original-texts directory with batch mode
python3 open_editor_agent.py --batch --model llama3.1
```

Example with review notes:
```bash
# This will edit essay.txt according to the feedback in review.txt
python3 open_editor_agent.py original-texts/essay.txt --review review.txt --model mistral
```

## Configuration Options

- `DEBUG_COLORS=1` (default) - Enable colorful terminal output
- `DEBUG_COLORS=0` - Disable colors for logging to files

## Troubleshooting

- **Claude API errors**: Check your API key and internet connection
- **Ollama errors**: Ensure Ollama is running with `ollama serve`
- **Summarization issues**: Try using the paragraph-by-paragraph approach
- **Missing dependencies**: Run `pip install --upgrade pip && pip install -r requirements.txt`

Edited files will be saved to the `edited-texts/` directory.