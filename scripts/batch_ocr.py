import os
import subprocess
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Perform batch OCR on journal page images using native macOS Vision API.")
    parser.add_argument(
        "-b", "--book", 
        default="book-1", 
        help="The book folder name under data/journal-images/ (e.g., book-1, book-2). Default is book-1."
    )
    args = parser.parse_args()

    # Resolve paths relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    
    directory = os.path.join(repo_root, "data", "journal-images", args.book)
    output_file = os.path.join(repo_root, "data", f"{args.book}_raw_ocr.md")
    jxa_script = os.path.join(script_dir, "ocr.js")

    if not os.path.exists(directory):
        print(f"Error: Book directory '{directory}' does not exist.")
        sys.exit(1)

    if not os.path.exists(jxa_script):
        print(f"Error: JXA OCR helper script not found at '{jxa_script}'.")
        sys.exit(1)

    # Find and sort all page files (case-insensitive for JPG/JPEG)
    files = sorted([f for f in os.listdir(directory) if f.lower().endswith(('.jpg', '.jpeg'))])
    
    if not files:
        print(f"No JPG or JPEG images found in: {directory}")
        return

    print(f"Starting batch OCR for '{args.book}' ({len(files)} files)...")
    
    with open(output_file, "w", encoding="utf-8") as out:
        for idx, filename in enumerate(files, 1):
            file_path = os.path.join(directory, filename)
            print(f"[{idx}/{len(files)}] Running OCR on {filename}...")
            
            # Write page header
            out.write(f"## Page {idx:03d} ({filename})\n\n")
            
            try:
                # Call JXA script via osascript
                result = subprocess.run(
                    ["osascript", "-l", "JavaScript", jxa_script, file_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                text = result.stdout.strip()
                out.write(text + "\n\n")
            except subprocess.CalledProcessError as e:
                print(f"Failed to OCR {filename}: {e.stderr}")
                out.write(f"*[Error performing OCR on {filename}: {e.stderr.strip()}]*\n\n")
                
    print(f"Batch OCR complete! Raw text saved to '{output_file}'")

if __name__ == "__main__":
    main()
