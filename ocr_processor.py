"""
OCR text extraction module for the AI Screen Reader
"""
import pytesseract
from PIL import Image
import re
import logging
from typing import Optional, List, Dict
from config import config
from screen_capture import ScreenCapture

try:
    from enhanced_ocr import EnhancedOCR
    ENHANCED_OCR_AVAILABLE = True
except ImportError:
    ENHANCED_OCR_AVAILABLE = False

class OCRProcessor:
    """Handles OCR text extraction from images"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.screen_capture = ScreenCapture()

        # Initialize enhanced OCR if available
        self.enhanced_ocr = None
        if ENHANCED_OCR_AVAILABLE:
            try:
                self.enhanced_ocr = EnhancedOCR(use_gpu=False)  # Set to True if you have GPU
                self.logger.info("Enhanced OCR (EasyOCR) initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Enhanced OCR: {e}")

        # Set Tesseract path if configured
        import os
        tesseract_found = False

        if config.tesseract_path and os.path.exists(config.tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = config.tesseract_path
            tesseract_found = True
            self.logger.info(f"Using configured Tesseract: {config.tesseract_path}")
        else:
            # Try common Windows installation paths
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Users\root\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    tesseract_found = True
                    self.logger.info(f"Found Tesseract at: {path}")
                    break

        if not tesseract_found:
            self.logger.warning("Tesseract not found - OCR quality will be poor")

        # OCR configuration for better accuracy
        self.ocr_config = '--oem 3 --psm 6'
    
    def extract_text_from_image(self, image: Image.Image) -> Optional[str]:
        """
        Extract text from PIL Image using OCR

        Args:
            image: PIL Image to extract text from

        Returns:
            Extracted text string or None if extraction fails
        """
        try:
            # Try enhanced OCR first if available
            if self.enhanced_ocr:
                text = self.enhanced_ocr.get_best_text(image)
                if text and text != "No text detected":
                    cleaned_text = self.clean_text(text)
                    self.logger.info(f"Enhanced OCR extracted {len(cleaned_text)} characters")
                    return cleaned_text

            # Fallback to Tesseract
            # Preprocess image for better OCR
            processed_image = self.screen_capture.preprocess_image(image)

            # Resize image for better OCR accuracy
            resized_image = self.screen_capture.resize_image(processed_image, 2.0)

            # Extract text using Tesseract
            text = pytesseract.image_to_string(resized_image, config=self.ocr_config)

            # Clean up the extracted text
            cleaned_text = self.clean_text(text)

            self.logger.info(f"Tesseract extracted {len(cleaned_text)} characters of text")
            return cleaned_text

        except Exception as e:
            self.logger.error(f"OCR text extraction failed: {e}")
            return None
    
    def extract_text_from_screen(self, region: Optional[tuple] = None) -> Optional[str]:
        """
        Capture screen and extract text in one operation
        
        Args:
            region: Optional region tuple (x, y, width, height)
            
        Returns:
            Extracted text string or None if fails
        """
        try:
            # Capture screen
            screenshot = self.screen_capture.capture_screen(region)
            if not screenshot:
                return None
            
            # Extract text
            return self.extract_text_from_image(screenshot)
            
        except Exception as e:
            self.logger.error(f"Screen text extraction failed: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        Line breaks are preserved so questions and A) B) C) D) options stay line-based.
        Digits and identifiers are not altered.
        """
        if not text:
            return ""

        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.splitlines()]
        return '\n'.join(line for line in lines if line)

    def get_text_with_confidence(self, image: Image.Image) -> Dict:
        """
        Extract text with confidence scores
        
        Args:
            image: PIL Image to extract text from
            
        Returns:
            Dictionary with text and confidence information
        """
        try:
            processed_image = self.screen_capture.preprocess_image(image)
            resized_image = self.screen_capture.resize_image(processed_image, 2.0)
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(resized_image, output_type=pytesseract.Output.DICT)
            
            # Filter out low confidence text
            confident_text = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) > 30:  # Only include text with >30% confidence
                    word = data['text'][i].strip()
                    if word:
                        confident_text.append(word)
                        confidences.append(int(conf))
            
            result = {
                'text': ' '.join(confident_text),
                'average_confidence': sum(confidences) / len(confidences) if confidences else 0,
                'word_count': len(confident_text),
                'low_confidence_words': len([c for c in data['conf'] if 0 < int(c) <= 30])
            }
            
            self.logger.debug(f"OCR confidence analysis: {result['average_confidence']:.1f}% avg")
            return result
            
        except Exception as e:
            self.logger.error(f"Confidence OCR failed: {e}")
            return {'text': '', 'average_confidence': 0, 'word_count': 0, 'low_confidence_words': 0}
    
    def extract_structured_text(self, image: Image.Image) -> List[str]:
        """
        Extract text and attempt to maintain structure (lines, paragraphs)
        
        Args:
            image: PIL Image to extract text from
            
        Returns:
            List of text lines
        """
        try:
            processed_image = self.screen_capture.preprocess_image(image)
            resized_image = self.screen_capture.resize_image(processed_image, 2.0)
            
            # Use different PSM mode for better line detection
            config_line = '--oem 3 --psm 4'
            text = pytesseract.image_to_string(resized_image, config=config_line)
            
            # Split into lines and clean
            lines = [self.clean_text(line) for line in text.split('\n')]
            lines = [line for line in lines if line.strip()]  # Remove empty lines
            
            return lines
            
        except Exception as e:
            self.logger.error(f"Structured text extraction failed: {e}")
            return []
