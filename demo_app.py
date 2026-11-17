"""
AI Screen Reader - Demo Version
Automatically runs in demo mode without API requirements
"""
import sys
import os
import logging
from config import config
from gui import ScreenReaderGUI
from automation_engine import AutomationEngine
from demo_mode import DemoAI

def setup_logging():
    """Setup logging configuration"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/screen_reader_demo.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

class DemoScreenReaderApp:
    """Demo version of the screen reader app"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gui = None
        self.automation_engine = None
    
    def initialize(self):
        """Initialize the demo application"""
        self.logger.info("Initializing AI Screen Reader - DEMO MODE")
        
        # Initialize GUI
        self.gui = ScreenReaderGUI()
        self.gui.root.title("AI Screen Reader - DEMO MODE")
        
        # Initialize automation engine with demo AI
        gui_callbacks = {
            'update_text': self.gui.update_text_display,
            'update_questions': self.gui.update_questions_display,
            'update_answers': self.gui.update_answers_display,
            'update_last_scan': self.gui.update_last_scan
        }
        
        self.automation_engine = AutomationEngine(gui_callbacks)
        
        # Replace AI integration with demo
        self.automation_engine.ai_integration = DemoAI()
        
        # Connect GUI to automation engine
        self.connect_gui_to_engine()
        
        self.logger.info("Demo application initialized successfully")
        return True
    
    def connect_gui_to_engine(self):
        """Connect GUI controls to automation engine"""
        def reading_loop():
            interval = int(self.gui.interval_var.get())
            provider = "demo"
            
            if not self.automation_engine.start(interval, provider):
                self.gui.stop_reading()
                return
            
            while self.gui.is_running and self.automation_engine.is_running:
                self.gui.root.update()
                import time
                time.sleep(0.1)
            
            if not self.gui.is_running:
                self.automation_engine.stop()
        
        self.gui.reading_loop = reading_loop
        
        original_stop = self.gui.stop_reading
        def stop_reading():
            original_stop()
            self.automation_engine.stop()
        
        self.gui.stop_reading = stop_reading
        
        # Update provider dropdown to show demo
        self.gui.provider_var.set("demo")
    
    def run(self):
        """Run the demo application"""
        if not self.initialize():
            return 1
        
        try:
            self.logger.info("Starting DEMO GUI...")
            self.logger.info("Features available:")
            self.logger.info("- Screen capture: YES")
            self.logger.info("- OCR text extraction: YES (if Tesseract found)")
            self.logger.info("- Question detection: YES")
            self.logger.info("- AI answers: DEMO (sample answers)")
            
            self.gui.run()
            
        except KeyboardInterrupt:
            self.logger.info("Demo application interrupted by user")
            
        except Exception as e:
            self.logger.error(f"Demo application error: {e}")
            return 1
            
        finally:
            self.cleanup()
        
        return 0
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up demo...")
        
        if self.automation_engine:
            self.automation_engine.stop()
        
        self.logger.info("Demo cleanup completed")

def main():
    """Main entry point for demo"""
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("AI SCREEN READER - DEMO MODE")
    logger.info("=" * 60)
    logger.info("")
    logger.info("🎯 DEMO MODE FEATURES:")
    logger.info("✅ Full screen capture")
    logger.info("✅ OCR text extraction (with Tesseract)")
    logger.info("✅ Question detection")
    logger.info("✅ Sample AI answers (not real AI)")
    logger.info("✅ All GUI features")
    logger.info("")
    logger.info("💡 API KEY INFO:")
    logger.info("❌ OpenAI requires payment (your quota exceeded)")
    logger.info("❌ Anthropic key not configured")
    logger.info("✅ Demo mode provides sample answers")
    logger.info("")
    
    app = DemoScreenReaderApp()
    exit_code = app.run()
    
    logger.info("AI Screen Reader Demo Exiting")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
