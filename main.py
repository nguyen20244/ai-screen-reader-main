"""
Main application file for the AI Screen Reader
"""
import sys
import os
import logging
import tkinter as tk
from tkinter import messagebox
from config import config
from gui import ScreenReaderGUI
from automation_engine import AutomationEngine

def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/screen_reader.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels for different modules
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []
    
    try:
        import pytesseract
        # Test if tesseract is accessible
        pytesseract.get_tesseract_version()
    except Exception as e:
        # For now, just warn about Tesseract but don't block startup
        print(f"Warning: Tesseract OCR not found: {e}")
        print("OCR functionality will be limited. Install from: https://github.com/tesseract-ocr/tesseract")
        # missing_deps.append("Tesseract OCR (install from https://github.com/tesseract-ocr/tesseract)")
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        import PIL
    except ImportError:
        missing_deps.append("Pillow")
    
    try:
        import pyautogui
    except ImportError:
        missing_deps.append("pyautogui")
    
    # Check API keys
    api_keys_available = config.validate_api_keys()
    if not any(api_keys_available.values()):
        missing_deps.append("API Keys (OpenAI or Anthropic) - check .env file")
    
    return missing_deps

def create_env_file_if_needed():
    """Create .env file from example if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            return True
    return False

class ScreenReaderApp:
    """Main application class"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gui = None
        self.automation_engine = None
    
    def initialize(self):
        """Initialize the application"""
        self.logger.info("Initializing AI Screen Reader...")
        
        # Check dependencies
        missing_deps = check_dependencies()
        if missing_deps:
            error_msg = "Missing dependencies:\n" + "\n".join(f"- {dep}" for dep in missing_deps)
            self.logger.error(error_msg)
            
            # Show error in GUI if possible
            root = tk.Tk()
            root.withdraw()  # Hide main window
            messagebox.showerror("Missing Dependencies", error_msg)
            root.destroy()
            return False
        
        # Create .env file if needed
        if create_env_file_if_needed():
            self.logger.info("Created .env file from template. Please edit it with your API keys.")
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(
                "Configuration Required", 
                "A .env file has been created. Please edit it with your API keys before running the application."
            )
            root.destroy()
            return False
        
        # Initialize GUI
        self.gui = ScreenReaderGUI()
        
        # Initialize automation engine with GUI callbacks
        gui_callbacks = {
            'update_text': lambda t: self.gui.post_ui(self.gui.update_text_display, t),
            'update_questions': lambda q: self.gui.post_ui(self.gui.update_questions_display, q),
            'update_answers': lambda r: self.gui.post_ui(self.gui.update_answers_display, r),
            'update_last_scan': lambda: self.gui.post_ui(self.gui.update_last_scan)
        }
        
        self.automation_engine = AutomationEngine(gui_callbacks)
        
        # Connect GUI to automation engine
        self.connect_gui_to_engine()
        
        self.logger.info("Application initialized successfully")
        return True
    
    def connect_gui_to_engine(self):
        """Connect GUI controls to automation engine"""
        # Override GUI's reading loop with actual implementation
        def reading_loop():
            try:
                interval = int(self.gui.interval_var.get())
            except ValueError:
                interval = None  # None -> engine uses config default
            provider = self.gui.provider_var.get()
            
            if not self.automation_engine.start(interval, provider):
                self.gui.stop_reading()
                messagebox.showerror("Error", "Failed to start automation engine")
                return
            
            # Engine runs in its own worker thread; the Tk main loop keeps the UI responsive
        
        # Replace the GUI's reading loop
        self.gui.reading_loop = reading_loop
        
        # Override GUI's stop method to also stop automation
        original_stop = self.gui.stop_reading
        def stop_reading():
            original_stop()
            self.automation_engine.stop()
        
        self.gui.stop_reading = stop_reading
    
    def run(self):
        """Run the application"""
        if not self.initialize():
            return 1
        
        try:
            self.logger.info("Starting GUI...")
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
    # Setup logging first
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("AI Screen Reader Starting")
    logger.info("=" * 50)
    
    # Create and run application
    app = ScreenReaderApp()
    exit_code = app.run()
    
    logger.info("AI Screen Reader Exiting")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
