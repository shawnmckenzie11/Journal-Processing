# Journal Processing Pipeline

A lightweight, high-accuracy processing pipeline designed to organize handwritten journal page images and extract/clean their text contents.

This project leverages macOS's native **Vision Framework** via JavaScript for Automation (JXA) to perform OCR directly from the command line without requiring external software (like Tesseract) or complex dependencies.

---

## Directory Structure

```text
Journal-Processing/
├── .gitignore               # Excludes raw images (.jpg, .jpeg) and OS artifacts
├── README.md                # Project documentation
├── data/
│   ├── book-1_raw_ocr.md    # Raw OCR text from Book 1
│   ├── book-1_cleaned_ocr.md# Corrected journal text for Book 1
│   └── journal-images/      # [Git Ignored] Place raw image folders here
│       └── book-1/
│           ├── page_001.jpg
│           └── ...
└── scripts/
    ├── rename_pages.py      # Chronologically renames pages by camera timestamp
    ├── ocr.js               # JXA helper that executes Apple's Vision OCR
    └── batch_ocr.py         # Runs OCR in batch over a specific book
```

---

## Pipeline Workflow (For New Books)

When you receive a new batch of journal images (e.g., **Book 2**), follow these steps to process them:

### Step 1: Add Raw Images
1. Create a new folder inside the ignored `data/journal-images/` directory named after your book:
   ```bash
   mkdir -p data/journal-images/book-2
   ```
2. Move your raw images (e.g., `IMG_20260526_100531.jpg`) into that directory.

### Step 2: Chronologically Rename the Images
The images need to be sorted chronologically by their capture timestamp (parsed from `IMG_YYYYMMDD_HHMMSS` or file metadata) and renamed to `page_NNN.jpg`.

1. **Perform a Dry Run** to preview the renaming:
   ```bash
   python3 scripts/rename_pages.py --book book-2
   ```
2. **Execute the Renaming** once you verify the preview:
   ```bash
   python3 scripts/rename_pages.py --book book-2 --execute
   ```

### Step 3: Extract the Text (Batch OCR)
Run the batch OCR script to generate the raw transcript. This utilizes Apple's native Vision framework on your Mac and runs very fast:

```bash
python3 scripts/batch_ocr.py --book book-2
```
*This will create the raw transcript at `data/book-2_raw_ocr.md`.*

### Step 4: Clean Up the Transcript
Review the raw transcript at `data/book-2_raw_ocr.md` and clean up obvious spelling or OCR misreadings without altering the original meaning. Save the refined journal entry as `data/book-2_cleaned_ocr.md`.

---

## Technical Notes

- **Git Storage**: Raw images are automatically excluded from commits via `.gitignore` to keep the repository extremely lightweight. Only the `.md` transcripts and project scripts are pushed to GitHub.
- **OCR Quality**: The Vision framework has built-in `usesLanguageCorrection = true` and `recognitionLevel = .accurate` to optimize handwriting extraction on macOS.
