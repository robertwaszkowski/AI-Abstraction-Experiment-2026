import zipfile
import xml.etree.ElementTree as ET
import os
import sys

# Set stdout to utf-8
sys.stdout.reconfigure(encoding='utf-8')

def read_docx(file_path):
    try:
        with zipfile.ZipFile(file_path) as z:
            xml_content = z.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # Find all text nodes recursively
            texts = []
            for node in tree.iter():
                if node.tag.endswith('}t'): # w:t
                    if node.text:
                        texts.append(node.text)
                elif node.tag.endswith('}p'): # w:p
                    texts.append('\n') # Newline for paragraphs
                elif node.tag.endswith('}tab'): # w:tab
                    texts.append('\t')
            
            return ''.join(texts)
    except Exception as e:
        return f"Error reading {file_path}: {e}"

files = [
    "c:/Users/pawel/Desktop/MIPB2/Re_ Projekt ai/Change of Employment Conditions/Change of Employment Conditions Data.docx",
    "c:/Users/pawel/Desktop/MIPB2/Re_ Projekt ai/Change of Employment Conditions/Change of Employment Conditions Test Scenario.docx"
]

for f in files:
    print(f"--- Content of {os.path.basename(f)} ---")
    print(read_docx(f))
    print("\n" + "="*50 + "\n")
