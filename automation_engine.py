"""
Automation engine for the AI Screen Reader
Coordinates screen capture, OCR, question detection, and AI responses
"""
import threading
import time
import logging
from typing import Optional, List, Callable
from datetime import datetime
from config import config
from screen_capture import ScreenCapture
from ocr_processor import OCRProcessor
from question_detector import QuestionDetector, Question
from ai_integration import AIIntegration, AIResponse

class AutomationEngine:
    """Main automation engine that coordinates all components"""
    
    def __init__(self, gui_callbacks: Optional[dict] = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.screen_capture = ScreenCapture()
        self.ocr_processor = OCRProcessor()
        self.question_detector = QuestionDetector()
        self.ai_integration = AIIntegration()
        
        # GUI callbacks for updating display
        self.gui_callbacks = gui_callbacks or {}
        
        # State management
        self.is_running = False
        self.current_thread: Optional[threading.Thread] = None
        self.last_text = ""
        self.last_questions: List[Question] = []
        self.last_responses: List[AIResponse] = []
        
        # Statistics
        self.stats = {
            'scans_completed': 0,
            'questions_detected': 0,
            'ai_queries_made': 0,
            'errors_encountered': 0,
            'start_time': None
        }
    
    def start(self, interval: int = None, provider: str = None) -> bool:
        """
        Start the automation engine
        
        Args:
            interval: Scan interval in seconds (uses config default if None)
            provider: AI provider to use (uses config default if None)
            
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running:
            self.logger.warning("Automation engine is already running")
            return False
        
        # Update configuration
        if interval:
            config.refresh_interval = interval
        if provider:
            config.default_ai_provider = provider
        
        # Validate AI provider availability
        available_providers = self.ai_integration.get_available_providers()
        if config.default_ai_provider not in available_providers:
            self.logger.error(f"AI provider '{config.default_ai_provider}' not available")
            return False
        
        # Start the automation loop
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        self.current_thread = threading.Thread(target=self._automation_loop, daemon=True)
        self.current_thread.start()
        
        self.logger.info(f"Automation engine started with {config.refresh_interval}s interval")
        return True
    
    def stop(self):
        """Stop the automation engine"""
        if not self.is_running:
            self.logger.warning("Automation engine is not running")
            return
        
        self.is_running = False
        
        # Wait for thread to finish (with timeout)
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join(timeout=5.0)
        
        self.logger.info("Automation engine stopped")
    
    def _automation_loop(self):
        """Main automation loop (runs in separate thread)"""
        self.logger.info("Starting automation loop")
        
        while self.is_running:
            try:
                # Perform one scan cycle
                self._perform_scan_cycle()
                
                # Update statistics
                self.stats['scans_completed'] += 1
                
                # Wait for next cycle
                self._wait_for_next_cycle()
                
            except Exception as e:
                self.logger.error(f"Error in automation loop: {e}")
                self.stats['errors_encountered'] += 1
                
                # Continue after error with a short delay
                time.sleep(5)
        
        self.logger.info("Automation loop ended")
    
    def _perform_scan_cycle(self):
        """Perform one complete scan cycle"""
        cycle_start = time.time()
        
        # Step 1: Capture screen
        self.logger.debug("Capturing screen...")
        screenshot = self.screen_capture.capture_screen()
        if not screenshot:
            self.logger.error("Failed to capture screen")
            return
        
        # Step 2: Extract text using OCR
        self.logger.debug("Extracting text...")
        extracted_text = self.ocr_processor.extract_text_from_image(screenshot)
        if not extracted_text:
            self.logger.warning("No text extracted from screen")
            extracted_text = ""
        
        # Update GUI with extracted text
        self._call_gui_callback('update_text', extracted_text)
        
        # Step 3: Detect questions
        self.logger.debug("Detecting questions...")
        questions = self.question_detector.detect_questions(extracted_text)
        
        # Update GUI with questions
        self._call_gui_callback('update_questions', questions)
        
        if questions:
            self.logger.info(f"Detected {len(questions)} questions")
            self.stats['questions_detected'] += len(questions)
            
            # Step 4: Get AI answers for questions
            self.logger.debug("Getting AI answers...")
            responses = []
            
            for question in questions:
                try:
                    response = self.ai_integration.answer_question(
                        question, 
                        config.default_ai_provider
                    )
                    responses.append(response)
                    self.stats['ai_queries_made'] += 1
                    
                    self.logger.info(f"Got answer for: {question.text[:50]}...")
                    
                    # Small delay between API calls to avoid rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"Failed to get AI answer: {e}")
                    error_response = AIResponse(
                        answer=f"Error: {str(e)}",
                        provider=config.default_ai_provider,
                        model="error",
                        error=str(e)
                    )
                    responses.append(error_response)
            
            # Update GUI with answers
            self._call_gui_callback('update_answers', responses)
            
            # Store results
            self.last_questions = questions
            self.last_responses = responses
        else:
            self.logger.debug("No questions detected")
        
        # Store current text
        self.last_text = extracted_text
        
        # Update last scan time in GUI
        self._call_gui_callback('update_last_scan')
        
        cycle_time = time.time() - cycle_start
        self.logger.debug(f"Scan cycle completed in {cycle_time:.2f}s")
    
    def _wait_for_next_cycle(self):
        """Wait for the next scan cycle with interruption support"""
        wait_time = config.refresh_interval
        start_wait = time.time()
        
        while self.is_running and (time.time() - start_wait) < wait_time:
            time.sleep(0.1)  # Check every 100ms if we should stop
    
    def _call_gui_callback(self, callback_name: str, *args):
        """Call GUI callback if available"""
        if callback_name in self.gui_callbacks:
            try:
                callback = self.gui_callbacks[callback_name]
                if callable(callback):
                    callback(*args)
            except Exception as e:
                self.logger.error(f"GUI callback '{callback_name}' failed: {e}")
    
    def get_stats(self) -> dict:
        """Get automation statistics"""
        stats = self.stats.copy()
        
        if stats['start_time']:
            runtime = datetime.now() - stats['start_time']
            stats['runtime_seconds'] = runtime.total_seconds()
            stats['runtime_formatted'] = str(runtime).split('.')[0]  # Remove microseconds
        
        return stats
    
    def get_last_results(self) -> dict:
        """Get the last scan results"""
        return {
            'text': self.last_text,
            'questions': self.last_questions,
            'responses': self.last_responses,
            'timestamp': datetime.now()
        }
    
    def perform_single_scan(self) -> dict:
        """Perform a single scan cycle and return results"""
        if self.is_running:
            self.logger.warning("Cannot perform single scan while automation is running")
            return {}
        
        self.logger.info("Performing single scan...")
        self._perform_scan_cycle()
        return self.get_last_results()
    
    def test_components(self) -> dict:
        """Test all components and return status"""
        results = {
            'screen_capture': False,
            'ocr': False,
            'question_detection': False,
            'ai_integration': {}
        }
        
        try:
            # Test screen capture
            screenshot = self.screen_capture.capture_screen()
            results['screen_capture'] = screenshot is not None
            
            if screenshot:
                # Test OCR
                text = self.ocr_processor.extract_text_from_image(screenshot)
                results['ocr'] = text is not None
                
                if text:
                    # Test question detection
                    questions = self.question_detector.detect_questions(text)
                    results['question_detection'] = True
            
            # Test AI providers
            for provider in ['openai', 'claude']:
                results['ai_integration'][provider] = self.ai_integration.test_connection(provider)
                
        except Exception as e:
            self.logger.error(f"Component testing failed: {e}")
        
        return results
