"""
AI Screen Reader with Free AI Alternatives
"""
import sys
import os
import logging
from config import config
from gui import ScreenReaderGUI
from automation_engine import AutomationEngine
from free_ai_alternatives import FreeAIManager

def setup_logging():
    """Setup logging configuration"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/screen_reader_free.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

class FreeAIScreenReaderApp:
    """Screen reader app with free AI alternatives"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gui = None
        self.automation_engine = None
        self.free_ai = None
    
    def initialize(self):
        """Initialize the application with free AI"""
        self.logger.info("Initializing AI Screen Reader with FREE AI")
        
        # Initialize free AI manager
        self.free_ai = FreeAIManager()
        available_providers = self.free_ai.get_available_providers()
        
        self.logger.info(f"Available free AI providers: {available_providers}")
        
        if not available_providers:
            self.logger.warning("No free AI providers available")
            print("\n" + "="*60)
            print("NO FREE AI PROVIDERS AVAILABLE")
            print("="*60)
            print("\nRecommended: Install Ollama for free local AI")
            print("1. Run: install_ollama.bat")
            print("2. Follow the installation instructions")
            print("3. Run this app again")
            print("\nAlternative: Use demo mode")
            print("Run: demo_app.py")
            return False
        
        # Initialize GUI
        self.gui = ScreenReaderGUI()
        self.gui.root.title("AI Screen Reader - FREE AI")
        
        # Initialize automation engine
        gui_callbacks = {
            'update_text': self.gui.update_text_display,
            'update_questions': self.gui.update_questions_display,
            'update_answers': self.gui.update_answers_display,
            'update_last_scan': self.gui.update_last_scan
        }
        
        self.automation_engine = AutomationEngine(gui_callbacks)
        
        # Replace AI integration with free AI
        self.automation_engine.ai_integration = self.free_ai
        
        # Connect GUI to automation engine
        self.connect_gui_to_engine()
        
        self.logger.info("Free AI application initialized successfully")
        return True
    
    def connect_gui_to_engine(self):
        """Connect GUI controls to automation engine"""
        def reading_loop():
            interval = int(self.gui.interval_var.get())
            
            # Use first available provider
            available_providers = self.free_ai.get_available_providers()
            provider = available_providers[0] if available_providers else "none"
            
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
        
        # Update provider dropdown
        available_providers = self.free_ai.get_available_providers()
        if available_providers:
            self.gui.provider_var.set(available_providers[0])
    
    def run(self):
        """Run the application"""
        if not self.initialize():
            return 1
        
        try:
            self.logger.info("Starting FREE AI GUI...")
            
            available_providers = self.free_ai.get_available_providers()
            for provider in available_providers:
                if provider == 'ollama':
                    self.logger.info("✓ Ollama: Local AI (completely free)")
                elif provider == 'huggingface':
                    self.logger.info("✓ HuggingFace: Free API tier")
                elif provider == 'gemini':
                    self.logger.info("✓ Gemini: Google's free tier")
            
            self.gui.run()
            
        except KeyboardInterrupt:
            self.logger.info("Free AI application interrupted by user")
            
        except Exception as e:
            self.logger.error(f"Free AI application error: {e}")
            return 1
            
        finally:
            self.cleanup()
        
        return 0
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up free AI app...")
        
        if self.automation_engine:
            self.automation_engine.stop()
        
        self.logger.info("Free AI cleanup completed")

def main():
    """Main entry point"""
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("AI SCREEN READER - FREE AI VERSION")
    logger.info("=" * 60)
    logger.info("")
    logger.info("FREE AI OPTIONS:")
    logger.info("1. Ollama - Local AI (best option)")
    logger.info("   - Completely free")
    logger.info("   - No API limits")
    logger.info("   - Works offline")
    logger.info("   - Install: run install_ollama.bat")
    logger.info("")
    logger.info("2. HuggingFace - Free API tier")
    logger.info("   - Free tier available")
    logger.info("   - Internet required")
    logger.info("   - Some rate limits")
    logger.info("")
    logger.info("3. Google Gemini - Free tier")
    logger.info("   - Requires free API key")
    logger.info("   - Good performance")
    logger.info("")
    
    app = FreeAIScreenReaderApp()
    exit_code = app.run()
    
    logger.info("Free AI Screen Reader Exiting")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
