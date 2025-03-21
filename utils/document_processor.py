import os
import PyPDF2
import docx
import io
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import tempfile

def process_document(file_path, file_type):
    """
    Process document based on its file type and extract text.
    
    Args:
        file_path (str): Path to the document file
        file_type (str): MIME type of the file
    
    Returns:
        str: Extracted text from the document
    """
    try:
        if 'pdf' in file_type:
            return process_pdf(file_path)
        elif 'docx' in file_type:
            return process_docx(file_path)
        elif 'txt' in file_type or 'text' in file_type:
            return process_txt(file_path)
        else:
            return "Unsupported file type"
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        return None

def process_pdf(file_path):
    """
    Extract text from PDF file. If text extraction fails (e.g., scanned PDF),
    attempt OCR.
    
    Args:
        file_path (str): Path to the PDF file
    
    Returns:
        str: Extracted text from the PDF
    """
    # First try direct text extraction
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        
        # If text extraction worked and got meaningful content, return it
        if text.strip() and len(text) > 100:
            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
    
    # If direct extraction failed or got little text, try OCR
    try:
        return ocr_pdf(file_path)
    except Exception as e:
        print(f"Error performing OCR on PDF: {str(e)}")
        return None

def ocr_pdf(file_path):
    """
    Perform OCR on a PDF file.
    
    Args:
        file_path (str): Path to the PDF file
    
    Returns:
        str: Extracted text from OCR
    """
    # Convert PDF to images
    images = convert_from_path(file_path)
    
    full_text = ""
    
    # Process each page
    for i, image in enumerate(images):
        # Save the image temporarily
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            image.save(tmp.name)
            # Perform OCR
            text = pytesseract.image_to_string(Image.open(tmp.name))
            full_text += text + "\n\n"
            # Clean up
            os.unlink(tmp.name)
    
    return full_text

def process_docx(file_path):
    """
    Extract text from DOCX file.
    
    Args:
        file_path (str): Path to the DOCX file
    
    Returns:
        str: Extracted text from the DOCX
    """
    doc = docx.Document(file_path)
    full_text = []
    
    for para in doc.paragraphs:
        full_text.append(para.text)
    
    return '\n'.join(full_text)

def process_txt(file_path):
    """
    Extract text from TXT file.
    
    Args:
        file_path (str): Path to the TXT file
    
    Returns:
        str: Extracted text from the TXT
    """
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        return file.read()
