import zipfile
import os

def inspect_docx(file_path):
    try:
        with zipfile.ZipFile(file_path) as z:
            xml_content = z.read('word/document.xml')
            print(f"--- XML Start of {os.path.basename(file_path)} ---")
            print(xml_content[:1000]) # Print first 1000 chars
            print("\n")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

files = [
    "c:/Users/pawel/Desktop/MIPB2/Re_ Projekt ai/Change of Employment Conditions/Change of Employment Conditions Data.docx",
    "c:/Users/pawel/Desktop/MIPB2/Re_ Projekt ai/Change of Employment Conditions/Change of Employment Conditions Test Scenario.docx"
]

for f in files:
    inspect_docx(f)
