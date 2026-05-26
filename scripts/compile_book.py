import os
import re
import sys
import argparse
from datetime import datetime

def parse_simple_yaml(yaml_str):
    """
    A pure-Python, zero-dependency parser for simple YAML front matter.
    Handles key: value, integers, and lists like [A, B, C].
    """
    metadata = {}
    for line in yaml_str.splitlines():
        line = line.strip()
        if not line or ':' not in line:
            continue
        key, val = line.split(':', 1)
        key = key.strip()
        val = val.strip()
        
        # Parse arrays like [A, B, C]
        if val.startswith('[') and val.endswith(']'):
            items = []
            for item in val[1:-1].split(','):
                item = item.strip().strip("'\"")
                if item:
                    items.append(item)
            metadata[key] = items
        # Parse integers
        elif val.isdigit():
            metadata[key] = int(val)
        else:
            val = val.strip("'\"")
            metadata[key] = val
    return metadata

def parse_yaml_front_matter(file_path):
    """
    Parses a single Markdown file containing multiple pages,
    each starting with a YAML front matter block:
    ---
    yaml content
    ---
    page content
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find all blocks of the form:
    # ---
    # yaml metadata
    # ---
    # page content (up to the next front matter block or end of file)
    pattern = re.compile(r'---\s*\n(.*?)\n---\s*\n(.*?)(?=\n---\s*\n|\Z)', re.DOTALL)
    matches = pattern.findall(content)
    
    parsed_pages = []
    for metadata_str, page_content in matches:
        try:
            metadata = parse_simple_yaml(metadata_str)
            if not isinstance(metadata, dict):
                continue
            parsed_pages.append({
                'metadata': metadata,
                'content': page_content.strip()
            })
        except Exception as e:
            print(f"Warning: Failed to parse metadata block in {file_path}: {e}")
            
    return parsed_pages

def filter_pages(pages, args):
    filtered = []
    for page in pages:
        meta = page['metadata']
        
        # Filter by Topic
        if args.topic:
            topics = [t.lower() for t in meta.get('topics', [])]
            if args.topic.lower() not in topics:
                continue
                
        # Filter by Person
        if args.person:
            people = [p.lower() for p in meta.get('people', [])]
            if args.person.lower() not in people:
                continue
                
        # Filter by Source Type (original, sourced, mixed)
        if args.source:
            source_type = meta.get('source', '')
            if isinstance(source_type, str):
                if args.source.lower() != source_type.lower():
                    continue
            else:
                continue

        # Filter by Date Range
        if args.start_date or args.end_date:
            date_str = meta.get('date')
            if not date_str:
                continue
            try:
                # Convert string date (YYYY-MM-DD or YYYY-MM) to datetime
                if isinstance(date_str, datetime):
                    page_date = date_str
                elif isinstance(date_str, str):
                    # Handle YYYY-MM-DD or YYYY-MM
                    if len(date_str) == 7:
                        page_date = datetime.strptime(date_str, "%Y-%m")
                    else:
                        page_date = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    continue

                if args.start_date:
                    start = datetime.strptime(args.start_date, "%Y-%m-%d")
                    if page_date < start:
                        continue
                if args.end_date:
                    end = datetime.strptime(args.end_date, "%Y-%m-%d")
                    if page_date > end:
                        continue
            except ValueError as e:
                print(f"Warning: Date parsing failed for '{date_str}': {e}")
                continue

        filtered.append(page)
    return filtered

def main():
    parser = argparse.ArgumentParser(
        description="Compile journal entries from cleaned Markdown files using YAML metadata filters."
    )
    parser.add_argument(
        "-t", "--topic", 
        help="Filter entries by a specific topic/tag (e.g. Stoicism, Perception)."
    )
    parser.add_argument(
        "-p", "--person", 
        help="Filter entries by a key person (e.g. Emily, Nadia, Pam)."
    )
    parser.add_argument(
        "--source", 
        help="Filter entries by originality/source type (original, sourced, mixed)."
    )
    parser.add_argument(
        "-s", "--start-date", 
        help="Filter entries starting from this date (YYYY-MM-DD)."
    )
    parser.add_argument(
        "-e", "--end-date", 
        help="Filter entries up to this date (YYYY-MM-DD)."
    )
    parser.add_argument(
        "-o", "--output", 
        help="Output path for the compiled Markdown file (default is output/compiled_book.md)."
    )
    parser.add_argument(
        "--sort", 
        choices=["date", "page"], 
        default="date", 
        help="Sort entries by date or by page order. Default is date."
    )
    
    args = parser.parse_args()

    # Resolve paths relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    data_dir = os.path.join(repo_root, "data")
    
    # Locate all cleaned_ocr.md files in the data directory
    cleaned_files = [
        os.path.join(data_dir, f) for f in os.listdir(data_dir) 
        if f.endswith("_cleaned_ocr.md")
    ]
    
    if not cleaned_files:
        print("No cleaned journal files (*_cleaned_ocr.md) found in data/.")
        sys.exit(1)
        
    # Parse all pages from all files
    all_pages = []
    for file_path in cleaned_files:
        pages = parse_yaml_front_matter(file_path)
        all_pages.extend(pages)
        
    print(f"Parsed {len(all_pages)} total pages from {len(cleaned_files)} files.")
    
    # Apply filters
    filtered_pages = filter_pages(all_pages, args)
    print(f"Filtered down to {len(filtered_pages)} matching pages.")
    
    if not filtered_pages:
        print("No entries matched the specified criteria.")
        return
        
    # Sort pages
    if args.sort == "date":
        # Helper to convert metadata date to comparable format
        def get_sort_key(page):
            d = page['metadata'].get('date', '')
            if isinstance(d, datetime):
                return d.strftime("%Y-%m-%d")
            return str(d)
        filtered_pages.sort(key=get_sort_key)
    else:
        filtered_pages.sort(key=lambda x: (x['metadata'].get('book', 0), x['metadata'].get('page', 0)))

    # Set default output file if not specified
    if not args.output:
        output_dir = os.path.join(repo_root, "output")
        os.makedirs(output_dir, exist_ok=True)
        args.output = os.path.join(output_dir, "compiled_book.md")
    else:
        # Ensure parent directory of custom output exists
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    # Write compiled file
    with open(args.output, 'w', encoding='utf-8') as out:
        out.write("# Compiled Journal Almanac\n\n")
        
        # Write compile criteria
        out.write("## Compilation Criteria\n")
        criteria = []
        if args.topic: criteria.append(f"**Topic**: {args.topic}")
        if args.person: criteria.append(f"**Person**: {args.person}")
        if args.source: criteria.append(f"**Source**: {args.source}")
        if args.start_date or args.end_date:
            dates = f"{args.start_date or 'Beginning'} to {args.end_date or 'End'}"
            criteria.append(f"**Date Range**: {dates}")
            
        if criteria:
            out.write("- " + "\n- ".join(criteria) + "\n\n")
        else:
            out.write("- All Entries\n\n")
            
        # Write Table of Contents
        out.write("## Table of Contents\n")
        for idx, page in enumerate(filtered_pages, 1):
            meta = page['metadata']
            date_str = meta.get('date', 'Undated')
            if isinstance(date_str, datetime):
                date_str = date_str.strftime("%Y-%m-%d")
            title = f"Book {meta.get('book', '?')} - Page {meta.get('page', '?'):03d} ({date_str})"
            anchor = title.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("-", "-")
            # In markdown headers, colons or commas are omitted in anchors
            anchor = re.sub(r'[^\w\-]', '', anchor)
            out.write(f"{idx}. [{title}](#{anchor})\n")
        out.write("\n---\n\n")
        
        # Write actual page contents
        for page in filtered_pages:
            meta = page['metadata']
            date_str = meta.get('date', 'Undated')
            if isinstance(date_str, datetime):
                date_str = date_str.strftime("%Y-%m-%d")
            
            # Print page header
            out.write(f"### Book {meta.get('book', '?')} - Page {meta.get('page', '?'):03d} ({date_str})\n\n")
            
            # Print page tags / metadata
            metadata_lines = []
            if meta.get('topics'): metadata_lines.append(f"**Topics**: {', '.join(meta['topics'])}")
            if meta.get('people'): metadata_lines.append(f"**People**: {', '.join(meta['people'])}")
            if meta.get('source'): metadata_lines.append(f"**Source**: {meta['source']}")
            if meta.get('location'): metadata_lines.append(f"**Location**: {meta['location']}")
            
            if metadata_lines:
                out.write("> " + "\n> ".join(metadata_lines) + "\n\n")
                
            # Write page contents
            out.write(page['content'] + "\n\n")
            out.write("---\n\n")
            
    print(f"Successfully generated compiled book at: {args.output}")

if __name__ == "__main__":
    main()
