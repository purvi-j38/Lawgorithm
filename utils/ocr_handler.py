import os
import pytesseract
from PIL import Image
import tempfile
from pdf2image import convert_from_path
import io

def perform_ocr(image_path):
    """
    Perform OCR on an image file.
    
    Args:
        image_path (str): Path to the image file
    
    Returns:
        str: Extracted text from the image
    """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Perform OCR
        text = pytesseract.image_to_string(img)
        
        return text
    except Exception as e:
        print(f"OCR error: {str(e)}")
        return ""

def perform_ocr_on_bytes(image_bytes):
    """
    Perform OCR on image bytes.
    
    Args:
        image_bytes (bytes): Image data as bytes
    
    Returns:
        str: Extracted text from the image
    """
    try:
        # Create image from bytes
        img = Image.open(io.BytesIO(image_bytes))
        
        # Perform OCR
        text = pytesseract.image_to_string(img)
        
        return text
    except Exception as e:
        print(f"OCR error: {str(e)}")
        return ""

def ocr_pdf_file(pdf_path):
    """
    Perform OCR on all pages of a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        str: Extracted text from all pages
    """
    try:
        # Convert PDF to list of images
        images = convert_from_path(pdf_path)
        
        text_results = []
        
        # Process each page
        for i, img in enumerate(images):
            # Save the image temporarily
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                img.save(temp_file.name)
                
                # Perform OCR on the page
                page_text = perform_ocr(temp_file.name)
                text_results.append(f"--- Page {i+1} ---\n{page_text}")
                
                # Remove temporary file
                os.unlink(temp_file.name)
        
        # Combine results from all pages
        return "\n\n".join(text_results)
    except Exception as e:
        print(f"PDF OCR error: {str(e)}")
        return ""

def preprocess_image_for_ocr(image_path):
    """
    Preprocess an image to improve OCR results.
    
    Args:
        image_path (str): Path to the image file
    
    Returns:
        PIL.Image: Preprocessed image
    """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Convert to grayscale
        img = img.convert('L')
        
        # Increase contrast - simple method
        # In a real app, more advanced preprocessing would be used
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        return img
    except Exception as e:
        print(f"Image preprocessing error: {str(e)}")
        return None

def extract_text_with_enhanced_ocr(image_path):
    """
    Perform enhanced OCR with preprocessing.
    
    Args:
        image_path (str): Path to the image file
    
    Returns:
        str: Extracted text from the image
    """
    try:
        # Preprocess the image
        processed_img = preprocess_image_for_ocr(image_path)
        
        if processed_img:
            # Create temporary file for the preprocessed image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                processed_img.save(temp_file.name)
                
                # OCR configuration options for better results
                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(processed_img, config=custom_config)
                
                # Remove temporary file
                os.unlink(temp_file.name)
                
                return text
        else:
            return ""
    except Exception as e:
        print(f"Enhanced OCR error: {str(e)}")
        return ""
