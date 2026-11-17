"""
screen_capture.py — AI Screen Reader
Thêm: screen-diff trigger (tự động scan khi màn hình thay đổi đủ nhiều)
"""

import time
import threading
import pyautogui
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Optional, Tuple, Callable
import logging
from config import config

try:
    from window_capture import WindowCapture
    WINDOW_CAPTURE_AVAILABLE = True
except ImportError:
    WINDOW_CAPTURE_AVAILABLE = False

pyautogui.FAILSAFE = False

# Ngưỡng % pixel thay đổi để coi là "màn hình đổi"
DIFF_THRESHOLD = 0.04   # 4% — tăng nếu trigger quá nhiễu, giảm nếu bỏ sót
# Interval giữa 2 lần check diff (giây) — nhỏ hơn = nhạy hơn, tốn CPU hơn
DIFF_CHECK_INTERVAL = 1.0


class ScreenCapture:
    """Handles screen capture + screen-diff auto trigger"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.window_capture = None
        if WINDOW_CAPTURE_AVAILABLE:
            try:
                self.window_capture = WindowCapture()
                self.logger.info("Window capture initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize window capture: {e}")

        self.capture_mode = 'browser'

        # --- Screen diff state ---
        self._prev_frame: Optional[np.ndarray] = None
        self._diff_thread: Optional[threading.Thread] = None
        self._diff_running = False
        self._on_change_callback: Optional[Callable] = None
        self.paused = False  # GeminiBridge set True khi đang xử lý

    # ------------------------------------------------------------------
    # Capture
    # ------------------------------------------------------------------

    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Image.Image]:
        try:
            screenshot = None

            if self.capture_mode == 'browser' and self.window_capture:
                screenshot = self.window_capture.capture_browser_content()
                if screenshot:
                    self.logger.info(f"Browser content captured: {screenshot.size}")
                    return screenshot
                else:
                    self.logger.warning("Browser capture failed, falling back to full screen")

            if region:
                screenshot = pyautogui.screenshot(region=region)
            elif config.capture_region and not config.capture_full_screen:
                screenshot = pyautogui.screenshot(region=config.capture_region)
            else:
                screenshot = pyautogui.screenshot()

            if screenshot:
                self.logger.info(f"Screenshot captured: {screenshot.size}")
            return screenshot

        except Exception as e:
            self.logger.error(f"Failed to capture screen: {e}")
            return None

    # ------------------------------------------------------------------
    # Screen-diff trigger
    # ------------------------------------------------------------------

    def start_diff_watcher(self, on_change: Callable):
        """
        Bắt đầu theo dõi thay đổi màn hình.

        Args:
            on_change: callback(image: Image.Image) gọi khi màn hình thay đổi đủ nhiều.
                       Nhận vào PIL Image của frame mới.
        """
        if self._diff_running:
            self.logger.warning("Diff watcher đang chạy rồi.")
            return

        self._on_change_callback = on_change
        self._diff_running       = True
        self._prev_frame         = None

        self._diff_thread = threading.Thread(
            target=self._diff_loop,
            daemon=True,
            name="ScreenDiffWatcher",
        )
        self._diff_thread.start()
        self.logger.info("Screen diff watcher started.")

    def stop_diff_watcher(self):
        """Dừng watcher."""
        self._diff_running = False
        if self._diff_thread:
            self._diff_thread.join(timeout=3)
        self.logger.info("Screen diff watcher stopped.")

    def _diff_loop(self):
        """Background thread: liên tục so sánh frame."""
        while self._diff_running:
            try:
                # Bỏ qua khi đang xử lý Gemini
                if self.paused:
                    time.sleep(DIFF_CHECK_INTERVAL)
                    continue

                screenshot = self.capture_screen()
                if screenshot is None:
                    time.sleep(DIFF_CHECK_INTERVAL)
                    continue

                # Downscale để so sánh nhanh (không cần full res)
                small = screenshot.resize((320, 180), Image.Resampling.BILINEAR)
                frame = np.array(small.convert("L"))  # grayscale

                if self._prev_frame is not None:
                    diff        = cv2.absdiff(self._prev_frame, frame)
                    changed_pct = np.count_nonzero(diff > 15) / diff.size

                    if changed_pct >= DIFF_THRESHOLD:
                        self.logger.info(
                            f"Màn hình thay đổi {changed_pct:.1%} → trigger scan"
                        )
                        # Gọi callback với ảnh full-res
                        if self._on_change_callback:
                            try:
                                self._on_change_callback(screenshot)
                            except Exception as cb_err:
                                self.logger.error(f"on_change callback error: {cb_err}")

                        # Reset prev để tránh trigger liên tục cùng 1 frame
                        self._prev_frame = frame
                        # Chờ thêm 3s trước khi check tiếp (debounce)
                        time.sleep(3.0)
                        continue

                self._prev_frame = frame

            except Exception as e:
                self.logger.error(f"Diff loop error: {e}")

            time.sleep(DIFF_CHECK_INTERVAL)

    # ------------------------------------------------------------------
    # Existing helpers (giữ nguyên)
    # ------------------------------------------------------------------

    def set_capture_mode(self, mode: str):
        if mode in ['full_screen', 'browser', 'active_window']:
            self.capture_mode = mode
            self.logger.info(f"Capture mode set to: {mode}")
        else:
            self.logger.warning(f"Invalid capture mode: {mode}")

    def get_browser_windows(self):
        if self.window_capture:
            return self.window_capture.find_browser_windows()
        return []

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')

            img_array = np.array(image)
            gray      = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

            mean_brightness = np.mean(gray)
            is_dark_mode    = mean_brightness < 100

            if is_dark_mode:
                gray = cv2.bitwise_not(gray)

            clahe    = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)

            _, thresh = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            kernel  = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

            self.logger.debug(f"Image preprocessing completed (dark_mode: {is_dark_mode})")
            return Image.fromarray(cleaned)

        except Exception as e:
            self.logger.error(f"Image preprocessing failed: {e}")
            return image

    def resize_image(self, image: Image.Image, scale_factor: float = 2.0) -> Image.Image:
        try:
            new_size     = (int(image.width * scale_factor), int(image.height * scale_factor))
            resized_image = image.resize(new_size, Image.Resampling.LANCZOS)
            self.logger.debug(f"Image resized from {image.size} to {new_size}")
            return resized_image
        except Exception as e:
            self.logger.error(f"Image resizing failed: {e}")
            return image

    def save_screenshot(self, image: Image.Image, filename: str) -> bool:
        try:
            image.save(filename)
            self.logger.info(f"Screenshot saved to {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {e}")
            return False

    def get_screen_size(self) -> Tuple[int, int]:
        try:
            size = pyautogui.size()
            return size.width, size.height
        except Exception as e:
            self.logger.error(f"Failed to get screen size: {e}")
            return (1920, 1080)
