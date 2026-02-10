import zipfile
import xml.etree.ElementTree as ET
import os

def read_docx(file_path):
    try:
        with zipfile.ZipFile(file_path) as z:
            xml_content = z.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # XML namespaces
            namespaces = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            }
            
            text_content = []
            for p in tree.findall('.//w:p', namespaces):
                texts = [node.text for node in p.findall('.//w:t', namespaces) if node.text]
                if texts:
                    text_content.append(''.join(texts))
            
            return '\n'.join(text_content)
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
