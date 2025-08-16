import pytesseract
from PIL import Image
import numpy as np

class OCRService:
    def __init__(self):
        # Configure tesseract if needed
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'  # Adjust path if needed
        pass
    
    def extract_text(self, image):
        """Extract text from image using Tesseract OCR"""
        try:
            # Convert PIL image to format suitable for tesseract
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Use tesseract to extract text
            text = pytesseract.image_to_string(image, config='--psm 6')
            
            # Clean up the text
            cleaned_text = self._clean_text(text)
            
            return cleaned_text
        
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return ""
    
    def _clean_text(self, text):
        """Clean and preprocess extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned = ' '.join(lines)
        
        return cleaned