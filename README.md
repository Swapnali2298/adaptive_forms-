
# 📝 PDF to AEM CRX Package Converter

This Python tool extracts text, images, and tables from PDFs (including scanned PDFs using OCR), and automatically generates a CRX package ready for AEM (Adobe Experience Manager).

It uses:
- **EasyOCR** for Optical Character Recognition (OCR)
- **PyMuPDF** (`fitz`) for PDF rendering
- **pdfplumber** for table extraction (from text-based PDFs)

---

## 🚀 Features
- Extracts text from scanned and digital PDFs.
- Detects and extracts tables from text-based PDFs.
- Generates `.content.xml` compatible with AEM JCR structure.
- Packages everything into a ready-to-install CRX package (`pdf_form_package.zip`).

---

## 📂 Folder Structure (Generated Package)
output_crx/
│
├── META-INF/
│ └── vault/
│ ├── filter.xml
│ └── properties.xml
│
└── jcr_root/
└── apps/
└── pdfforms/
├── .content.xml (Auto-generated XML)
└── form.json (Extracted PDF data)
