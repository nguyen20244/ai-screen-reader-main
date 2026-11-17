"""
Test script for AI Screen Reader components
"""
import logging
import sys
from config import config
from screen_capture import ScreenCapture
from ocr_processor import OCRProcessor
from question_detector import QuestionDetector
from ai_integration import AIIntegration

def setup_test_logging():
    """Setup logging for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def test_screen_capture():
    """Test screen capture functionality"""
    print("\n" + "="*50)
    print("TESTING SCREEN CAPTURE")
    print("="*50)
    
    try:
        capture = ScreenCapture()
        
        # Test basic screen capture
        print("Testing basic screen capture...")
        screenshot = capture.capture_screen()
        
        if screenshot:
            print(f"✓ Screen captured successfully: {screenshot.size}")
            
            # Test image preprocessing
            print("Testing image preprocessing...")
            processed = capture.preprocess_image(screenshot)
            print(f"✓ Image preprocessed: {processed.size}")
            
            # Test image resizing
            print("Testing image resizing...")
            resized = capture.resize_image(processed, 1.5)
            print(f"✓ Image resized: {resized.size}")
            
            return True
        else:
            print("✗ Failed to capture screen")
            return False
            
    except Exception as e:
        print(f"✗ Screen capture test failed: {e}")
        return False

def test_ocr():
    """Test OCR functionality"""
    print("\n" + "="*50)
    print("TESTING OCR")
    print("="*50)
    
    try:
        ocr = OCRProcessor()
        
        # Test screen text extraction
        print("Testing screen text extraction...")
        text = ocr.extract_text_from_screen()
        
        if text:
            print(f"✓ Text extracted successfully: {len(text)} characters")
            print(f"Sample text: {text[:100]}...")
            return True
        else:
            print("✗ No text extracted")
            return False
            
    except Exception as e:
        print(f"✗ OCR test failed: {e}")
        return False

def test_question_detection():
    """Test question detection"""
    print("\n" + "="*50)
    print("TESTING QUESTION DETECTION")
    print("="*50)
    
    try:
        detector = QuestionDetector()
        
        # Test with sample text containing questions
        sample_text = """
        1. What is the capital of France?
        A) London
        B) Berlin
        C) Paris
        D) Madrid
        
        2. Which of the following is a programming language?
        A) HTML
        B) Python
        C) CSS
        D) SQL
        
        Choose the correct answer for each question.
        """
        
        print("Testing question detection with sample text...")
        questions = detector.detect_questions(sample_text)
        
        print(f"✓ Detected {len(questions)} questions")
        
        for i, question in enumerate(questions, 1):
            print(f"Question {i}: {question.text[:50]}...")
            print(f"  Type: {question.question_type}")
            print(f"  Confidence: {question.confidence}")
            if question.options:
                print(f"  Options: {len(question.options)}")
        
        return len(questions) > 0
        
    except Exception as e:
        print(f"✗ Question detection test failed: {e}")
        return False

def test_ai_integration():
    """Test AI integration"""
    print("\n" + "="*50)
    print("TESTING AI INTEGRATION")
    print("="*50)
    
    try:
        ai = AIIntegration()
        
        # Check available providers
        providers = ai.get_available_providers()
        print(f"Available AI providers: {providers}")
        
        if not providers:
            print("✗ No AI providers available (check API keys)")
            return False
        
        # Test with a simple question
        from question_detector import Question
        
        test_question = Question(
            text="What is 2 + 2?",
            question_type="test",
            confidence=1.0
        )
        
        for provider in providers:
            print(f"\nTesting {provider}...")
            response = ai.answer_question(test_question, provider)
            
            if response.error:
                print(f"✗ {provider} failed: {response.error}")
            else:
                print(f"✓ {provider} response: {response.answer[:100]}...")
                print(f"  Processing time: {response.processing_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"✗ AI integration test failed: {e}")
        return False

def test_full_pipeline():
    """Test the complete pipeline"""
    print("\n" + "="*50)
    print("TESTING FULL PIPELINE")
    print("="*50)
    
    try:
        # Initialize all components
        capture = ScreenCapture()
        ocr = OCRProcessor()
        detector = QuestionDetector()
        ai = AIIntegration()
        
        print("1. Capturing screen...")
        screenshot = capture.capture_screen()
        if not screenshot:
            print("✗ Failed to capture screen")
            return False
        
        print("2. Extracting text...")
        text = ocr.extract_text_from_image(screenshot)
        if not text:
            print("✗ No text extracted")
            return False
        
        print(f"   Extracted {len(text)} characters")
        
        print("3. Detecting questions...")
        questions = detector.detect_questions(text)
        print(f"   Found {len(questions)} questions")
        
        if questions:
            print("4. Getting AI answers...")
            providers = ai.get_available_providers()
            
            if providers:
                # Test with first question and first available provider
                response = ai.answer_question(questions[0], providers[0])
                
                if response.error:
                    print(f"✗ AI response failed: {response.error}")
                else:
                    print(f"✓ Got AI response: {response.answer[:100]}...")
            else:
                print("✗ No AI providers available")
        
        print("✓ Full pipeline test completed")
        return True
        
    except Exception as e:
        print(f"✗ Full pipeline test failed: {e}")
        return False

def main():
    """Run all tests"""
    setup_test_logging()
    
    print("AI SCREEN READER - COMPONENT TESTS")
    print("=" * 60)
    
    tests = [
        ("Screen Capture", test_screen_capture),
        ("OCR", test_ocr),
        ("Question Detection", test_question_detection),
        ("AI Integration", test_ai_integration),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The application should work correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
