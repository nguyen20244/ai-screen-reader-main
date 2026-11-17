"""
Window-specific capture for better OCR accuracy
"""
import logging
import pyautogui
from PIL import Image
import psutil
import win32gui
import win32process
import win32con
from typing import Optional, List, Tuple

class WindowCapture:
    """Capture specific windows instead of full screen"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def find_browser_windows(self) -> List[dict]:
        """Find all browser windows"""
        browser_processes = [
            'chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe', 
            'brave.exe', 'vivaldi.exe', 'safari.exe'
        ]
        
        windows = []
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_text:
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        process_name = process.name().lower()
                        
                        if any(browser in process_name for browser in browser_processes):
                            rect = win32gui.GetWindowRect(hwnd)
                            windows.append({
                                'hwnd': hwnd,
                                'title': window_text,
                                'process': process_name,
                                'rect': rect,
                                'area': (rect[2] - rect[0]) * (rect[3] - rect[1])
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            return True
        
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        # Sort by area (largest first) to get main browser window
        windows.sort(key=lambda x: x['area'], reverse=True)
        
        return windows
    
    def get_active_browser_window(self) -> Optional[dict]:
        """Get the currently active browser window"""
        try:
            # Get foreground window
            hwnd = win32gui.GetForegroundWindow()
            window_text = win32gui.GetWindowText(hwnd)
            
            if window_text:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                process_name = process.name().lower()
                
                browser_processes = [
                    'chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe', 
                    'brave.exe', 'vivaldi.exe', 'safari.exe'
                ]
                
                if any(browser in process_name for browser in browser_processes):
                    rect = win32gui.GetWindowRect(hwnd)
                    return {
                        'hwnd': hwnd,
                        'title': window_text,
                        'process': process_name,
                        'rect': rect
                    }
        except Exception as e:
            self.logger.debug(f"Could not get active browser window: {e}")
        
        return None
    
    def capture_browser_content(self, focus_content_area=True) -> Optional[Image.Image]:
        """Capture browser content area (excluding UI elements)"""
        
        # First try to get active browser window
        browser_window = self.get_active_browser_window()
        
        if not browser_window:
            # If no active browser, get the largest browser window
            browser_windows = self.find_browser_windows()
            if not browser_windows:
                self.logger.warning("No browser windows found")
                return None
            browser_window = browser_windows[0]
        
        rect = browser_window['rect']
        x, y, right, bottom = rect
        
        # Adjust coordinates to focus on content area (exclude browser UI)
        if focus_content_area:
            # Estimate browser UI dimensions
            title_bar_height = 30
            address_bar_height = 40
            tab_bar_height = 35
            
            # Adjust capture area
            y += title_bar_height + address_bar_height + tab_bar_height
            x += 5  # Small margin from left
            right -= 5  # Small margin from right
            bottom -= 5  # Small margin from bottom
        
        width = right - x
        height = bottom - y
        
        if width <= 0 or height <= 0:
            self.logger.warning("Invalid window dimensions")
            return None
        
        try:
            # Bring window to front
            win32gui.SetForegroundWindow(browser_window['hwnd'])
            
            # Small delay to ensure window is focused
            import time
            time.sleep(0.1)
            
            # Capture the specific region
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            
            self.logger.info(f"Captured browser content: {width}x{height} from {browser_window['process']}")
            return screenshot
            
        except Exception as e:
            self.logger.error(f"Failed to capture browser window: {e}")
            return None
    
    def capture_window_by_title(self, title_contains: str) -> Optional[Image.Image]:
        """Capture window that contains specific title text"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if title_contains.lower() in window_text.lower():
                    rect = win32gui.GetWindowRect(hwnd)
                    windows.append({
                        'hwnd': hwnd,
                        'title': window_text,
                        'rect': rect
                    })
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        if not windows:
            self.logger.warning(f"No window found containing '{title_contains}'")
            return None
        
        # Use first matching window
        window = windows[0]
        rect = window['rect']
        x, y, right, bottom = rect
        
        width = right - x
        height = bottom - y
        
        try:
            # Bring window to front
            win32gui.SetForegroundWindow(window['hwnd'])
            
            # Small delay
            import time
            time.sleep(0.1)
            
            # Capture
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            
            self.logger.info(f"Captured window '{window['title']}': {width}x{height}")
            return screenshot
            
        except Exception as e:
            self.logger.error(f"Failed to capture window: {e}")
            return None
