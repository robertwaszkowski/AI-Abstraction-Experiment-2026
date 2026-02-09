file_path = "c:/Users/pawel/Desktop/MIPB2/Re_ Projekt ai/Change of Employment Conditions/docx_content.txt"
with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
    print(repr(content))
