"""
gemini_bridge.py
Fix: CloakBrowser/Playwright phải chạy trên main thread.
Dùng queue để diff watcher (thread phụ) đẩy ảnh vào,
main thread xử lý và gửi lên Gemini.
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
    """
    Flow:
      diff watcher thread → đẩy ảnh vào _queue
      main thread         → lấy ảnh từ _queue → gửi Gemini → clipboard
    """

    def __init__(self):
        self.capture = ScreenCapture()
        self.sender  = GeminiSender()
        self._queue  = queue.Queue(maxsize=1)  # chỉ giữ 1 ảnh mới nhất

    def start(self):
        logger.info("Khởi động GeminiSender...")
        self.sender.start()

        logger.info("Bắt đầu theo dõi màn hình...")
        self.capture.start_diff_watcher(on_change=self._on_screen_change)

        logger.info("GeminiBridge đang chạy. Nhấn Ctrl+C để dừng.")
        self._main_loop()

    def stop(self):
        logger.info("Đang dừng GeminiBridge...")
        self.capture.stop_diff_watcher()
        self.sender.close()
        logger.info("Đã dừng.")

    # ------------------------------------------------------------------
    # Callback từ diff watcher thread — CHỈ đẩy vào queue, không làm gì khác
    # ------------------------------------------------------------------

    def _on_screen_change(self, image: Image.Image):
        try:
            # Nếu queue đầy (đang xử lý) → bỏ qua frame cũ, giữ frame mới
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            self._queue.put_nowait(image)
            logger.info("Màn hình đổi → đưa vào queue.")
        except Exception as e:
            logger.error(f"Queue error: {e}")

    # ------------------------------------------------------------------
    # Main loop — chạy trên main thread, Playwright OK
    # ------------------------------------------------------------------

    def _main_loop(self):
        try:
            while True:
                try:
                    # Chờ ảnh mới từ queue (timeout 1s để có thể Ctrl+C)
                    image = self._queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                logger.info("Gửi ảnh lên Gemini...")
                try:
                    response = self.sender.send_image(image, prompt=PROMPT)
                except Exception as e:
                    logger.error(f"Lỗi gửi Gemini: {e}")
                    continue

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
