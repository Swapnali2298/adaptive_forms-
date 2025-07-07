import os
import json
import zipfile
import shutil
import uuid
from PyPDF2 import PdfReader

# Directory constants
BASE_DIR = "output_crx"
JCR_ROOT = os.path.join(BASE_DIR, "jcr_root", "apps", "pdfforms")
META_INF = os.path.join(BASE_DIR, "META-INF", "vault")

# Step 1: Extract PDF Fields to JSON
def extract_pdf_to_json(pdf_path, json_path):
    reader = PdfReader(pdf_path)
    fields = {}

    if "/AcroForm" in reader.trailer["/Root"]:
        form = reader.trailer["/Root"]["/AcroForm"]
        if "/Fields" in form:
            for field in form["/Fields"]:
                field_obj = field.get_object()
                name = field_obj.get("/T", str(uuid.uuid4()))
                value = field_obj.get("/V", "")
                fields[name] = str(value)

    with open(json_path, 'w') as f:
        json.dump(fields, f, indent=4)

# Step 2: Generate content.xml from JSON
def generate_content_xml(json_path, xml_path):
    with open(json_path, 'r') as f:
        form_fields = json.load(f)

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>\n\n"""
    xml_content += """<jcr:root xmlns:jcr="http://www.jcp.org/jcr/1.0" """
    xml_content += """xmlns:sling="http://sling.apache.org/jcr/sling/1.0" """
    xml_content += """jcr:primaryType="nt:unstructured">\n"""

    for key, value in form_fields.items():
        xml_content += f'    <field jcr:primaryType="nt:unstructured" name="{key}" value="{value}" />\n'

    xml_content += "</jcr:root>"

    with open(xml_path, 'w') as f:
        f.write(xml_content)

# Step 3: Create CRX Package
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

    # Run extraction and generation
    json_file = os.path.join(JCR_ROOT, 'form.json')
    xml_file = os.path.join(JCR_ROOT, '.content.xml')

    extract_pdf_to_json(pdf_filename, json_file)
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
input_pdf = input_pdf.replace("\\", "/")  # Convert backslashes to slashes (Windows-friendly)

if not os.path.exists(input_pdf):
    print(f"❌ PDF file not found at:\n{input_pdf}")
else:
    create_crx_package(input_pdf)
