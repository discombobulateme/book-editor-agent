import os
import glob
import argparse
import difflib
from termcolor import colored

def get_edited_files():
    """Get a list of edited text files"""
    return glob.glob("edited-texts/*.txt")

def group_files_by_original():
    """Group edited files by their original source file"""
    edited_files = get_edited_files()
    groups = {}
    
    for file_path in edited_files:
        filename = os.path.basename(file_path)
        
        # Check if the filename contains a hyphen (model identifier)
        if '-' in filename:
            # Extract the original filename by removing model identifiers
            # This assumes the naming format: originalname-modelidentifier.txt
            parts = filename.split('-')
            original_name = parts[0]
        else:
            # For files without a hyphen, use the filename without extension
            original_name, _ = os.path.splitext(filename)
        
        if original_name not in groups:
            groups[original_name] = []
        
        groups[original_name].append(file_path)
    
    return groups

def read_file_content(filename):
    """Read the content of a file"""
    with open(filename, "r") as f:
        return f.read()

def get_model_name_from_file(filename):
    """Extract the model name from the filename"""
    base_name = os.path.basename(filename)
    
    # Check if the filename contains a hyphen (model identifier)
    if '-' in base_name:
        # Remove the original name and .txt extension
        name_without_original = '-'.join(base_name.split('-')[1:])
        return name_without_original.replace('.txt', '')
    else:
        # For files without a hyphen, assume it's from Claude
        return "claude"

def compare_outputs(file_groups):
    """Compare the edited outputs from different models"""
    for original_name, files in file_groups.items():
        if len(files) < 2:
            print(f"Skipping {original_name} - needs at least 2 edited versions for comparison")
            continue
        
        print(f"\n{'='*80}")
        print(f"Comparing outputs for original file: {original_name}.txt")
        print(f"{'='*80}")
        
        # First, print a summary of the files
        print("\nFiles being compared:")
        for i, file_path in enumerate(files):
            model_name = get_model_name_from_file(file_path)
            print(f"  {i+1}. {file_path} (Model: {model_name})")
        
        # Read file contents
        contents = [read_file_content(file_path) for file_path in files]
        
        # Compare files pairwise
        for i in range(len(files)):
            for j in range(i+1, len(files)):
                print(f"\n{'-'*80}")
                print(f"Comparing {get_model_name_from_file(files[i])} vs {get_model_name_from_file(files[j])}")
                print(f"{'-'*80}")
                
                # Calculate and print diff
                diff = list(difflib.unified_diff(
                    contents[i].splitlines(),
                    contents[j].splitlines(),
                    lineterm='',
                    n=3
                ))
                
                if diff:
                    for line in diff:
                        if line.startswith('+'):
                            print(colored(line, 'green'))
                        elif line.startswith('-'):
                            print(colored(line, 'red'))
                        elif line.startswith('@@'):
                            print(colored(line, 'cyan'))
                        else:
                            print(line)
                else:
                    print("No differences found.")
                    
        # Optional: Print statistics about the outputs
        print(f"\n{'-'*80}")
        print("Output Statistics:")
        for i, file_path in enumerate(files):
            model_name = get_model_name_from_file(file_path)
            word_count = len(contents[i].split())
            sentence_count = contents[i].count('.') + contents[i].count('!') + contents[i].count('?')
            avg_word_length = sum(len(word) for word in contents[i].split()) / word_count if word_count > 0 else 0
            
            print(f"  {model_name}:")
            print(f"    - Word count: {word_count}")
            print(f"    - Sentence count: {sentence_count}")
            print(f"    - Avg word length: {avg_word_length:.2f}")

def main():
    parser = argparse.ArgumentParser(description="Compare edited outputs from different models")
    parser.add_argument("--original", "-o", 
                        help="Compare only outputs for this original filename")
    
    args = parser.parse_args()
    
    file_groups = group_files_by_original()
    
    # Filter by original file if specified
    if args.original:
        original_name = os.path.splitext(args.original)[0]  # Remove extension if present
        if original_name in file_groups:
            file_groups = {original_name: file_groups[original_name]}
        else:
            print(f"No edited files found for original: {args.original}")
            return
    
    if not file_groups:
        print("No edited files found to compare.")
        return
    
    compare_outputs(file_groups)

if __name__ == "__main__":
    main() 