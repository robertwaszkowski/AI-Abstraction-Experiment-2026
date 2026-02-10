
import docx
import os
import sys

# Hardcoded path to the file of interest (relative to this script location)
target_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Process to Roles Mapping.docx"))

print(f"Reading: {target_path}")

try:
    doc = docx.Document(target_path)
    print("=== START OF DOC ===")
    for p in doc.paragraphs:
        if p.text.strip():
            print(p.text.strip())
    print("=== END OF DOC ===")
except Exception as e:
    print(f"Error: {e}")
