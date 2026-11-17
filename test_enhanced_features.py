"""
Test script for enhanced OCR and window capture features
"""
import logging
import time
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_window_capture():
    """Test window capture functionality"""
    logger.info("Testing Window Capture...")
    
    try:
        from window_capture import WindowCapture
        
        window_capture = WindowCapture()
        
        # Find browser windows
        browser_windows = window_capture.find_browser_windows()
        logger.info(f"Found {len(browser_windows)} browser windows:")
        
        for i, window in enumerate(browser_windows):
            logger.info(f"  {i+1}. {window['process']} - {window['title'][:50]}...")
        
        # Try to capture browser content
        if browser_windows:
            logger.info("Attempting to capture browser content...")
            screenshot = window_capture.capture_browser_content()
            
            if screenshot:
                logger.info(f"✅ Browser capture successful: {screenshot.size}")
                screenshot.save("test_browser_capture.png")
                logger.info("Saved as test_browser_capture.png")
                return screenshot
            else:
                logger.warning("❌ Browser capture failed")
        else:
            logger.warning("No browser windows found")
            
    except ImportError as e:
        logger.error(f"Window capture not available: {e}")
    except Exception as e:
        logger.error(f"Window capture test failed: {e}")
    
    return None

def test_enhanced_ocr(image=None):
    """Test enhanced OCR functionality"""
    logger.info("Testing Enhanced OCR...")
    
    try:
        from enhanced_ocr import EnhancedOCR
        
        enhanced_ocr = EnhancedOCR(use_gpu=False)
        
        if image is None:
            # Create a test image with text
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple test image
            test_image = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(test_image)
            
            # Add some test text
            try:
                # Try to use a system font
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            draw.text((20, 50), "Are you an expert on data structures?", fill='black', font=font)
            draw.text((20, 100), "A) vector  B) deque  C) stack  D) segment tree", fill='black', font=font)
            
            test_image.save("test_text_image.png")
            logger.info("Created test image: test_text_image.png")
            image = test_image
        
        # Test different OCR methods
        logger.info("Testing multi-engine OCR...")
        results = enhanced_ocr.extract_text_multi_engine(image)
        
        logger.info(f"✅ Enhanced OCR Results:")
        logger.info(f"  EasyOCR results: {len(results['easyocr'])}")
        logger.info(f"  Tesseract results: {len(results['tesseract'])}")
        logger.info(f"  Combined text: {results['combined_text'][:100]}...")
        logger.info(f"  Best confidence: {results['best_confidence']:.2f}")
        logger.info(f"  Processing time: {results['processing_time']:.2f}s")
        
        # Test simple text extraction
        logger.info("Testing simple text extraction...")
        simple_text = enhanced_ocr.get_best_text(image)
        logger.info(f"✅ Simple extraction: {simple_text[:100]}...")
        
        # Test image quality analysis
        logger.info("Testing image quality analysis...")
        quality = enhanced_ocr.analyze_image_quality(image)
        logger.info(f"✅ Image quality score: {quality['quality_score']:.1f}/100")
        
        return results
        
    except ImportError as e:
        logger.error(f"Enhanced OCR not available: {e}")
    except Exception as e:
        logger.error(f"Enhanced OCR test failed: {e}")
    
    return None

def test_screen_capture_modes():
    """Test different screen capture modes"""
    logger.info("Testing Screen Capture Modes...")
    
    try:
        from screen_capture import ScreenCapture
        
        screen_capture = ScreenCapture()
        
        # Test browser mode
        logger.info("Testing browser capture mode...")
        screen_capture.set_capture_mode('browser')
        browser_screenshot = screen_capture.capture_screen()
        
        if browser_screenshot:
            logger.info(f"✅ Browser mode: {browser_screenshot.size}")
            browser_screenshot.save("test_browser_mode.png")
        else:
            logger.warning("❌ Browser mode failed")
        
        # Test full screen mode
        logger.info("Testing full screen mode...")
        screen_capture.set_capture_mode('full_screen')
        full_screenshot = screen_capture.capture_screen()
        
        if full_screenshot:
            logger.info(f"✅ Full screen mode: {full_screenshot.size}")
            full_screenshot.save("test_fullscreen_mode.png")
        else:
            logger.warning("❌ Full screen mode failed")
        
        return browser_screenshot or full_screenshot
        
    except Exception as e:
        logger.error(f"Screen capture test failed: {e}")
    
    return None

def test_ocr_processor():
    """Test the updated OCR processor"""
    logger.info("Testing OCR Processor...")
    
    try:
        from ocr_processor import OCRProcessor
        
        ocr_processor = OCRProcessor()
        
        # Test with a simple image
        test_image = Image.new('RGB', (300, 100), color='white')
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(test_image)
        
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 30), "Test OCR Processing", fill='black', font=font)
        
        # Extract text
        extracted_text = ocr_processor.extract_text_from_image(test_image)
        
        if extracted_text:
            logger.info(f"✅ OCR Processor extracted: '{extracted_text.strip()}'")
        else:
            logger.warning("❌ OCR Processor failed")
        
        return extracted_text
        
    except Exception as e:
        logger.error(f"OCR Processor test failed: {e}")
    
    return None

def main():
    """Run all tests"""
    logger.info("🚀 Starting Enhanced Features Test")
    logger.info("=" * 50)
    
    # Test 1: Window Capture
    browser_image = test_window_capture()
    
    logger.info("-" * 30)
    
    # Test 2: Enhanced OCR
    ocr_results = test_enhanced_ocr(browser_image)
    
    logger.info("-" * 30)
    
    # Test 3: Screen Capture Modes
    screen_image = test_screen_capture_modes()
    
    logger.info("-" * 30)
    
    # Test 4: OCR Processor
    processor_result = test_ocr_processor()
    
    logger.info("=" * 50)
    logger.info("🎉 Enhanced Features Test Complete!")
    
    # Summary
    logger.info("📊 Test Summary:")
    logger.info(f"  Window Capture: {'✅ Working' if browser_image else '❌ Failed'}")
    logger.info(f"  Enhanced OCR: {'✅ Working' if ocr_results else '❌ Failed'}")
    logger.info(f"  Screen Capture: {'✅ Working' if screen_image else '❌ Failed'}")
    logger.info(f"  OCR Processor: {'✅ Working' if processor_result else '❌ Failed'}")

if __name__ == "__main__":
    main()
