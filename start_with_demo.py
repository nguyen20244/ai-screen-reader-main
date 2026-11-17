"""
Start AI Screen Reader with demo mode if API keys don't work
"""
import sys
import os
import logging
import tkinter as tk
from tkinter import messagebox
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
            logging.FileHandler('logs/screen_reader.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_api_keys():
    """Test if API keys work"""
    from ai_integration import AIIntegration
    from question_detector import Question
    
    ai = AIIntegration()
    providers = ai.get_available_providers()
    
    working_providers = []
    
    for provider in providers:
        try:
            test_question = Question(
                text="Test question",
                question_type="test",
                confidence=1.0
            )
            
            response = ai.answer_question(test_question, provider)
            if not response.error:
                working_providers.append(provider)
        except Exception as e:
            print(f"Provider {provider} failed: {e}")
    
    return working_providers

class ScreenReaderAppWithDemo:
    """Main application class with demo mode support"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gui = None
        self.automation_engine = None
        self.demo_mode = False
    
    def initialize(self):
        """Initialize the application"""
        self.logger.info("Initializing AI Screen Reader...")
        
        # Test API keys
        working_providers = test_api_keys()
        
        if not working_providers:
            self.logger.warning("No working API providers found. Starting in demo mode.")
            
            # Ask user if they want demo mode
            root = tk.Tk()
            root.withdraw()
            
            result = messagebox.askyesno(
                "API Keys Issue",
                "No working API keys found.\n\n"
                "Issues detected:\n"
                "• OpenAI: Quota exceeded (requires payment)\n"
                "• Anthropic: Invalid key\n\n"
                "Would you like to start in DEMO MODE?\n"
                "Demo mode will show sample answers without using real AI APIs."
            )
            
            root.destroy()
            
            if not result:
                return False
            
            self.demo_mode = True
        
        # Initialize GUI
        self.gui = ScreenReaderGUI()
        
        # Initialize automation engine
        gui_callbacks = {
            'update_text': self.gui.update_text_display,
            'update_questions': self.gui.update_questions_display,
            'update_answers': self.gui.update_answers_display,
            'update_last_scan': self.gui.update_last_scan
        }
        
        self.automation_engine = AutomationEngine(gui_callbacks)
        
        # Replace AI integration with demo if needed
        if self.demo_mode:
            self.automation_engine.ai_integration = DemoAI()
            self.logger.info("Demo mode activated - using sample AI responses")
        
        # Connect GUI to automation engine
        self.connect_gui_to_engine()
        
        self.logger.info("Application initialized successfully")
        return True
    
    def connect_gui_to_engine(self):
        """Connect GUI controls to automation engine"""
        def reading_loop():
            interval = int(self.gui.interval_var.get())
            provider = "demo" if self.demo_mode else self.gui.provider_var.get()
            
            if not self.automation_engine.start(interval, provider):
                self.gui.stop_reading()
                messagebox.showerror("Error", "Failed to start automation engine")
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
        
        # Update GUI title if in demo mode
        if self.demo_mode:
            self.gui.root.title("AI Screen Reader - DEMO MODE")
    
    def run(self):
        """Run the application"""
        if not self.initialize():
            return 1
        
        try:
            self.logger.info("Starting GUI...")
            if self.demo_mode:
                self.logger.info("Running in DEMO MODE - sample answers will be provided")
            self.gui.run()
            
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            return 1
            
        finally:
            self.cleanup()
        
        return 0
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up...")
        
        if self.automation_engine:
            self.automation_engine.stop()
        
        self.logger.info("Cleanup completed")

def main():
    """Main entry point"""
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("AI Screen Reader Starting (with Demo Mode)")
    logger.info("=" * 50)
    
    app = ScreenReaderAppWithDemo()
    exit_code = app.run()
    
    logger.info("AI Screen Reader Exiting")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
