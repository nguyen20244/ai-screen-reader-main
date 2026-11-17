"""
gemini_bridge.py
- Chụp TOÀN MÀN HÌNH (không dùng window_capture để tránh chụp nhầm Gemini)
- Paste ảnh vào Gemini qua Windows clipboard + Ctrl+V
"""

import logging
import queue
import threading
import time
import pyperclip
from PIL import Image

from screen_capture import ScreenCapture
from browser.gemini_sender import GeminiSender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("GeminiBridge")

PROMPT = (
    "Đây là ảnh chụp màn hình chứa câu hỏi. "
    "Hãy đọc kỹ và trả lời CHÍNH XÁC, NGẮN GỌN. "
    "Nếu là câu hỏi trắc nghiệm, chỉ cần trả lời đáp án đúng (A/B/C/D) "
    "kèm giải thích 1-2 câu."
)


class GeminiBridge:

    def __init__(self):
        self.capture  = ScreenCapture()
        # Dùng full screen thay vì browser capture
        # để tránh chụp nhầm cửa sổ Gemini
        self.capture.set_capture_mode('full_screen')
        self.sender   = GeminiSender()
        self._queue   = queue.Queue(maxsize=1)

    def start(self):
        logger.info("Khởi động GeminiSender...")
        self.sender.start()

        logger.info("Bắt đầu theo dõi màn hình (full screen)...")
        self.capture.start_diff_watcher(on_change=self._on_screen_change)

        logger.info("GeminiBridge đang chạy. Nhấn Ctrl+C để dừng.")
        self._main_loop()

    def stop(self):
        logger.info("Đang dừng...")
        self.capture.stop_diff_watcher()
        self.sender.close()
        logger.info("Đã dừng.")

    def _on_screen_change(self, image: Image.Image):
        if self.capture.paused:
            return
        try:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            self._queue.put_nowait(image)
            logger.info("Màn hình đổi → đưa vào queue.")
        except Exception as e:
            logger.error(f"Queue error: {e}")

    def _main_loop(self):
        try:
            while True:
                try:
                    image = self._queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                self.capture.paused = True
                logger.info("Gửi ảnh lên Gemini...")

                try:
                    response = self.sender.send_image(image, prompt=PROMPT)
                except Exception as e:
                    logger.error(f"Lỗi gửi Gemini: {e}")
                    continue
                finally:
                    time.sleep(3.0)
                    self.capture._prev_frame = None
                    self.capture.paused = False
                    logger.info("Tiếp tục theo dõi màn hình.")

                if response:
                    logger.info(f"\n{'='*50}\n{response}\n{'='*50}")
                    try:
                        pyperclip.copy(response)
                        logger.info("✓ Đã copy response vào clipboard.")
                    except Exception:
                        pass
                else:
                    logger.warning("Không nhận được response từ Gemini.")

        except KeyboardInterrupt:
            self.stop()


if __name__ == "__main__":
    bridge = GeminiBridge()
    bridge.start()
