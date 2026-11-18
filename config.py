"""
Configuration management for the AI Screen Reader
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the screen reader application"""
    
    def __init__(self):
        # API Keys
        self.openai_api_key: Optional[str] = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key: Optional[str] = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_api_key: Optional[str] = os.getenv('GEMINI_API_KEY')
        
        # Application Settings
        self.refresh_interval: int = int(os.getenv('REFRESH_INTERVAL', 30))
        self.default_ai_provider: str = os.getenv('DEFAULT_AI_PROVIDER', 'claude')
        
        # OCR Settings
        self.tesseract_path: Optional[str] = os.getenv('TESSERACT_PATH')
        
        # Screen Capture Settings
        self.capture_full_screen: bool = True
        self.capture_region: Optional[tuple] = None  # (x, y, width, height)

        # Crop sau khi chụp — cắt bỏ browser UI, taskbar, sidebar
        # Chỉnh các giá trị này trong .env hoặc trực tiếp ở đây
        # Mặc định: lấy vùng câu hỏi Cyber Campus (không có sidebar nav lớn)
        self.crop_enabled: bool = os.getenv('CROP_ENABLED', 'true').lower() == 'true'
        self.crop_left:    float = float(os.getenv('CROP_LEFT',   '0.00'))  # giữ từ cạnh trái
        self.crop_top:     float = float(os.getenv('CROP_TOP',    '0.08'))  # bỏ browser bar trên
        self.crop_right:   float = float(os.getenv('CROP_RIGHT',  '1.00'))  # giữ đến cạnh phải
        self.crop_bottom:  float = float(os.getenv('CROP_BOTTOM', '0.95'))  # bỏ taskbar dưới
        
        # Question Detection Settings
        self.question_patterns = [
            r'\?',  # Questions ending with ?
            r'(?i)^[A-D]\)',  # MCQ options A) B) C) D)
            r'(?i)^[1-9]\d*\.',  # Numbered questions
            r'(?i)what\s+is',  # What is questions
            r'(?i)which\s+of',  # Which of questions
            r'(?i)choose\s+the',  # Choose the questions
            r'(?i)select\s+the',  # Select the questions
        ]
        
        # GUI Settings
        self.window_width: int = 1000
        self.window_height: int = 700
        self.font_size: int = 10
        
    def validate_api_keys(self) -> dict:
        """Validate that required API keys are present"""
        validation = {
            'openai': bool(self.openai_api_key),
            'anthropic': bool(self.anthropic_api_key),
            'gemini': bool(self.gemini_api_key)
        }
        return validation
    
    def get_available_providers(self) -> list:
        """Get list of available AI providers based on API keys"""
        providers = []
        validation = self.validate_api_keys()

        if validation['openai']:
            providers.append('openai')
        if validation['anthropic']:
            providers.append('claude')
        if validation['gemini']:
            providers.append('gemini')

        return providers
    
    def set_capture_region(self, x: int, y: int, width: int, height: int):
        """Set custom screen capture region"""
        self.capture_region = (x, y, width, height)
        self.capture_full_screen = False
    
    def reset_to_full_screen(self):
        """Reset to full screen capture"""
        self.capture_full_screen = True
        self.capture_region = None

# Global configuration instance
config = Config()
