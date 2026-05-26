import os
import re
import sys
import argparse
from datetime import datetime

def get_image_timestamp(file_path):
    filename = os.path.basename(file_path)
    # Check for IMG_YYYYMMDD_HHMMSS pattern
    match = re.match(r'^IMG_(\d{8})_(\d{6})\.(jpg|jpeg)$', filename, re.IGNORECASE)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        try:
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            return dt.timestamp(), filename
        except ValueError:
            pass
    
    # Fallback to filesystem modification time
    try:
        mtime = os.path.getmtime(file_path)
        return mtime, filename
    except OSError:
        return 0.0, filename

def main():
    parser = argparse.ArgumentParser(description="Rename images in a journal book folder chronologically by page number.")
    parser.add_argument(
        "-b", "--book", 
        default="book-1", 
        help="The book folder name under data/journal-images/ (e.g., book-1, book-2). Default is book-1."
    )
    parser.add_argument(
        "-e", "--execute", 
        action="store_true", 
        help="Perform the actual renaming (default is dry-run)."
    )
    
    args = parser.parse_args()
    
    # Resolve directory paths relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    directory = os.path.join(repo_root, "data", "journal-images", args.book)
    
    if not os.path.exists(directory):
        print(f"Error: Book directory '{directory}' does not exist.")
        sys.exit(1)
        
    dry_run = not args.execute
    
    if dry_run:
        print("Running in DRY-RUN mode. No files will be renamed.\n")

    # Find all jpg/jpeg files
    files = []
    for f in os.listdir(directory):
        if f.lower().endswith(('.jpg', '.jpeg')):
            files.append(os.path.join(directory, f))
            
    if not files:
        print(f"No JPG or JPEG images found in: {directory}")
        return

    # Parse timestamps and sort
    file_info = []
    for f in files:
        ts, name = get_image_timestamp(f)
        file_info.append((ts, f, name))
        
    # Sort by timestamp, break ties by original filename
    file_info.sort(key=lambda x: (x[0], x[2]))

    print(f"Found {len(file_info)} images in '{args.book}'")
    print("Proposed renaming:\n")
    
    # Track actions to perform
    renames = []
    # Using 3 digit zero-padding (fits up to 999 pages)
    for i, (ts, path, name) in enumerate(file_info, start=1):
        ext = os.path.splitext(name)[1].lower()
        new_name = f"page_{i:03d}{ext}"
        new_path = os.path.join(directory, new_name)
        renames.append((path, new_path, name, new_name))
        
    # Print the proposed actions
    for old_path, new_path, old_name, new_name in renames:
        status = "[DRY-RUN]" if dry_run else "[RENAMING]"
        print(f"{status} {old_name} -> {new_name}")

    if dry_run:
        print("\nThis was a dry run. No files were renamed.")
        print("To execute the rename, run with: python3 scripts/rename_pages.py --book <folder> --execute")
    else:
        # Before renaming, check if any destination already exists to prevent overwrites
        existing_destinations = [new_path for _, new_path, _, _ in renames if os.path.exists(new_path)]
        if existing_destinations:
            print("\nError: Some of the target filenames already exist in the folder!")
            for dest in existing_destinations:
                print(f"  Existing target: {os.path.basename(dest)}")
            print("Aborting to prevent overwriting.")
            sys.exit(1)
            
        print("\nRenaming files...")
        success_count = 0
        for old_path, new_path, old_name, new_name in renames:
            try:
                os.rename(old_path, new_path)
                success_count += 1
            except Exception as e:
                print(f"Failed to rename {old_name} to {new_name}: {e}")
                
        print(f"Successfully renamed {success_count} / {len(renames)} files.")

if __name__ == "__main__":
    main()
