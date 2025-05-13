# Book Editor Agent

Text editor that applies style guidelines to text files using either Claude API or local open-source models via Ollama.

Terminal feedback lets you follow the process and anticipate costs when using Claude API. Simplified cli flags lets you: control the output format, control chunk size and if you want your API call to be sent as batch when dealing with multiple files. 

## How does it work?

You have 3 folders: 
- original-texts: where you add the texts you want to be edited
- review-notes: this is your prompt, what you want your editor to do
- edited-texts: the output of your LLM with the same name as your original filename + model + version number

When you run your script, it will search for review-notes. If there's a review note, with the same name as an original text, it will edit. If there's already an edited file with that name, it will add a version number at the end of the file's name. 

Your style instructions should be added to a separated file in the root directory called INSTRUCTIONS.md

## Processing Options

Two main options help you handle both multiple files and large documents:

- **--batch**: Processes multiple files in sequence. It will find all files with matching review notes and process them one after another automatically.

- **--chunk-size**: For handling large individual documents. Setting a chunk size (like 5000 words) will split large texts into smaller pieces for better processing, then recombine them.

For multiple large files, use both together:
```bash
python book_editor_agent.py --model claude-3-7-sonnet-20250219 --output-format docx --batch --chunk-size 5000
```

## Features

- Support for Claude (Anthropic) models and Ollama-based models (Mistral, Llama, DeepSeek)
- Prevent models from summarizing content unless explicit in instructions
- Smart chunking for large documents to avoid context limits
- Batch processing for multiple files with review notes
- Support for both .txt and .docx file formats
- Format conversion (txt to docx and vice versa)
- List installed Ollama models for local editing
- Connection monitoring with real-time status updates

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
   pip install -r requirements.txt 
   ```

3. Configure your environment
   - Create a `.env` file in the project root
   - For Claude: Add `ANTHROPIC_API_KEY=your_api_key_here`
   - For local models: [Install Ollama](https://ollama.com/download)
   
4. Download your preferred open source model. This will allow you to use free open source models locally

   ```bash
   ollama pull mistral    # Fast 7B model, good general choice
   ollama pull llama3.1   # High quality but larger
   ollama pull deepseek-r1 # Strong reasoning capabilities
   ```

5. Prepare your content
   - Place text files (.txt or .docx) in `original-texts/` directory
   - Create style guide as `INSTRUCTIONS.md`
   - Create review notes in the `review-notes/` directory with the same filename as your text

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
python3 book_editor_agent.py --model claude-3-sonnet

# Process all files in batch mode
python3 book_editor_agent.py --batch

# Specify output format (txt, docx, or same as input)
python3 book_editor_agent.py --output-format docx
```

### Using Ollama (Local Models)

```bash
# List local installed Ollama models
python3 open_editor_agent.py --list-models

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

## Working with Document Formats

The book editor agent now supports both .txt and .docx file formats:

- **Input formats**: Place either .txt or .docx files in the `original-texts/` directory
- **Output formats**: Control output format with the `--output-format` flag:
  - `--output-format txt` - Save as plain text
  - `--output-format docx` - Save as Word document
  - `--output-format same` - Keep the same format as the input (default)
- **Review notes**: Can be in either .txt or .docx format in the `review-notes/` directory

Example converting formats:
```bash
# Convert a .txt file to .docx during editing
python3 book_editor_agent.py original-texts/chapter.txt --output-format docx

# Convert a .docx file to .txt during editing
python3 book_editor_agent.py original-texts/manuscript.docx --output-format txt
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