import os
import json
import zipfile
import shutil
import fitz  # PyMuPDF
import easyocr
import pdfplumber

# Directory constants
BASE_DIR = "output_crx"
JCR_ROOT = os.path.join(BASE_DIR, "jcr_root", "apps", "pdfforms")
META_INF = os.path.join(BASE_DIR, "META-INF", "vault")

# Step 1: Extract Text + Tables from PDF using EasyOCR + pdfplumber
def extract_pdf_text_images(pdf_path, json_path):
    result = {"text_pages": [], "images": [], "tables": []}

    reader = easyocr.Reader(['en'])  # You can add more languages if needed

    pdf_doc = fitz.open(pdf_path)
    for idx, page in enumerate(pdf_doc):
        pix = page.get_pixmap(dpi=200)  # Render page to image
        image_bytes = pix.tobytes("png")

        # OCR on image
        text = reader.readtext(image_bytes, detail=0, paragraph=True)
        text_combined = "\n".join(text)
        result["text_pages"].append({
            "page": idx + 1,
            "text": text_combined.strip()
        })

    # Extract tables with pdfplumber (works only for text-based PDFs)
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                result["tables"].append({
                    "page": page_num + 1,
                    "table": table
                })

    # Save JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ Extracted text & tables to {json_path}")

# Step 2: Generate content.xml from JSON
def generate_content_xml(json_path, xml_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>\n\n"""
    xml_content += """<jcr:root xmlns:jcr="http://www.jcp.org/jcr/1.0" """
    xml_content += """xmlns:sling="http://sling.apache.org/jcr/sling/1.0" """
    xml_content += """jcr:primaryType="nt:unstructured">\n"""

    # Add OCR text from pages
    for page in data.get("text_pages", []):
        page_number = page["page"]
        text = page["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        xml_content += f'    <page_{page_number} jcr:primaryType="nt:unstructured" text="{text}" />\n'

    # Add Tables (optional, simplified)
    for idx, table in enumerate(data.get("tables", [])):
        xml_content += f'    <table_{idx + 1} jcr:primaryType="nt:unstructured" page="{table["page"]}" />\n'

    xml_content += "</jcr:root>"

    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)

# Step 3: Create CRX Package (Zip)
def create_crx_package(pdf_filename):
    # Prepare folders
    shutil.rmtree(BASE_DIR, ignore_errors=True)
    os.makedirs(JCR_ROOT, exist_ok=True)
    os.makedirs(META_INF, exist_ok=True)

    # Create dummy filter.xml & properties.xml
    with open(os.path.join(META_INF, 'filter.xml'), 'w') as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>\n
<workspaceFilter version="1.0">
    <filter root="/apps/pdfforms" />
</workspaceFilter>""")

    with open(os.path.join(META_INF, 'properties.xml'), 'w') as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>\n
<properties xmlns="http://www.day.com/jcr/vault/1.0">
    <entry key="packageFormatVersion" value="2"/>
    <entry key="packageType" value="content"/>
</properties>""")

    # Extract text/images/tables
    json_file = os.path.join(JCR_ROOT, 'form.json')
    xml_file = os.path.join(JCR_ROOT, '.content.xml')

    extract_pdf_text_images(pdf_filename, json_file)
    generate_content_xml(json_file, xml_file)

    # Zip it
    zip_filename = 'pdf_form_package.zip'
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, BASE_DIR)
                zipf.write(filepath, arcname)

    print(f"\n✅ CRX Package created: {zip_filename}")

# Step 4: Single-click execution
input_pdf = input("\n📄 Enter the PDF file path: ").strip().strip('"').strip("'")
input_pdf = input_pdf.replace("\\", "/")  # Windows-friendly

if not os.path.exists(input_pdf):
    print(f"❌ PDF file not found at:\n{input_pdf}")
else:
    create_crx_package(input_pdf)
