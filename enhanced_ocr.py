"""
Enhanced OCR with EasyOCR and multiple OCR engines
"""
import logging
import numpy as np
from PIL import Image
import cv2
from typing import List, Dict, Optional, Tuple
import time

# Import OCR engines
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

class EnhancedOCR:
    """Enhanced OCR with multiple engines and preprocessing"""
    
    def __init__(self, use_gpu=False):
        self.logger = logging.getLogger(__name__)
        self.use_gpu = use_gpu
        
        # Initialize EasyOCR
        self.easyocr_reader = None
        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['en'], gpu=use_gpu)
                self.logger.info("EasyOCR initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize EasyOCR: {e}")
                
        # Check Tesseract
        self.tesseract_available = TESSERACT_AVAILABLE
        if TESSERACT_AVAILABLE:
            try:
                pytesseract.get_tesseract_version()
                self.logger.info("Tesseract available")
            except Exception as e:
                self.tesseract_available = False
                self.logger.warning(f"Tesseract not available: {e}")
    
    def preprocess_image(self, image: Image.Image, method='adaptive') -> Image.Image:
        """Preprocess image for better OCR accuracy"""
        
        # Convert PIL to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        if method == 'adaptive':
            # Adaptive thresholding - works well for varying lighting
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
        elif method == 'otsu':
            # Otsu's thresholding - good for bimodal images
            _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == 'denoise':
            # Denoising + thresholding
            denoised = cv2.fastNlMeansDenoising(gray)
            _, processed = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            processed = gray
        
        # Convert back to PIL
        return Image.fromarray(processed)
    
    def extract_text_easyocr(self, image: Image.Image, confidence_threshold=0.5) -> List[Dict]:
        """Extract text using EasyOCR"""
        if not self.easyocr_reader:
            return []
        
        try:
            # Convert PIL to numpy array
            img_array = np.array(image)
            
            # Get results
            results = self.easyocr_reader.readtext(img_array)
            
            # Format results
            formatted_results = []
            for (bbox, text, confidence) in results:
                if confidence >= confidence_threshold:
                    formatted_results.append({
                        'text': text.strip(),
                        'confidence': confidence,
                        'bbox': bbox,
                        'engine': 'easyocr'
                    })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"EasyOCR failed: {e}")
            return []
    
    def extract_text_tesseract(self, image: Image.Image, config='--psm 6') -> List[Dict]:
        """Extract text using Tesseract"""
        if not self.tesseract_available:
            return []
        
        try:
            # Get text with confidence data
            data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
            
            results = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                confidence = int(data['conf'][i])
                text = data['text'][i].strip()
                
                if confidence > 30 and text:  # Filter low confidence and empty text
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
                    
                    results.append({
                        'text': text,
                        'confidence': confidence / 100.0,  # Normalize to 0-1
                        'bbox': bbox,
                        'engine': 'tesseract'
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Tesseract failed: {e}")
            return []
    
    def extract_text_multi_engine(self, image: Image.Image, preprocess_methods=['adaptive', 'original']) -> Dict:
        """Extract text using multiple engines and preprocessing methods"""
        
        all_results = {
            'easyocr': [],
            'tesseract': [],
            'combined_text': '',
            'best_confidence': 0.0,
            'processing_time': 0.0
        }
        
        start_time = time.time()
        
        # Try different preprocessing methods
        for method in preprocess_methods:
            if method == 'original':
                processed_image = image
            else:
                processed_image = self.preprocess_image(image, method)
            
            # EasyOCR
            if self.easyocr_reader:
                easyocr_results = self.extract_text_easyocr(processed_image)
                all_results['easyocr'].extend(easyocr_results)
            
            # Tesseract
            if self.tesseract_available:
                tesseract_results = self.extract_text_tesseract(processed_image)
                all_results['tesseract'].extend(tesseract_results)
        
        # Combine and deduplicate results
        combined_results = all_results['easyocr'] + all_results['tesseract']
        
        # Sort by confidence and remove duplicates
        unique_texts = set()
        filtered_results = []
        
        for result in sorted(combined_results, key=lambda x: x['confidence'], reverse=True):
            text_lower = result['text'].lower().strip()
            if text_lower and text_lower not in unique_texts:
                unique_texts.add(text_lower)
                filtered_results.append(result)
        
        # Create combined text
        all_results['combined_text'] = ' '.join([r['text'] for r in filtered_results])
        all_results['best_confidence'] = max([r['confidence'] for r in filtered_results], default=0.0)
        all_results['processing_time'] = time.time() - start_time
        
        return all_results
    
    def get_best_text(self, image: Image.Image) -> str:
        """Get the best text extraction result"""
        
        # Try EasyOCR first (usually better for modern interfaces)
        if self.easyocr_reader:
            results = self.extract_text_multi_engine(image, ['adaptive', 'original'])
            if results['combined_text'].strip():
                self.logger.info(f"OCR completed in {results['processing_time']:.2f}s with confidence {results['best_confidence']:.2f}")
                return results['combined_text']
        
        # Fallback to Tesseract
        if self.tesseract_available:
            try:
                text = pytesseract.image_to_string(image, config='--psm 6').strip()
                if text:
                    self.logger.info("OCR completed using Tesseract fallback")
                    return text
            except Exception as e:
                self.logger.error(f"Tesseract fallback failed: {e}")
        
        return "No text detected"
    
    def analyze_image_quality(self, image: Image.Image) -> Dict:
        """Analyze image quality for OCR"""
        
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Calculate metrics
        height, width = gray.shape
        
        # Sharpness (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Contrast (standard deviation)
        contrast = gray.std()
        
        # Brightness (mean)
        brightness = gray.mean()
        
        # Text-like regions (edge density)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (height * width)
        
        return {
            'width': width,
            'height': height,
            'sharpness': laplacian_var,
            'contrast': contrast,
            'brightness': brightness,
            'edge_density': edge_density,
            'quality_score': min(100, (laplacian_var / 100 + contrast / 50 + edge_density * 1000) / 3 * 100)
        }
