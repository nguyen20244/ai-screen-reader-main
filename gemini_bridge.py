"""Gemini bridge with full-screen capture, duplicate suppression and feedback-loop guard."""

import hashlib
import logging
import queue
import time

import pyperclip
from PIL import Image, ImageChops

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
    """Capture full screen, send one verified image at a time, then resume watching."""

    def __init__(self):
        self.capture = ScreenCapture()
        # Explicitly force OS-level full-screen capture. Never select/focus a browser.
        self.capture.set_capture_mode("full_screen")
        self.sender = GeminiSender()
        self._queue = queue.Queue(maxsize=1)
        self._last_image_hash = None
        self._stopping = False
        self._processing = False

    @staticmethod
    def _image_hash(image: Image.Image) -> str:
        """Stable low-resolution perceptual-ish hash; ignores tiny rendering noise."""
        small = image.convert("L").resize((32, 32), Image.Resampling.LANCZOS)
        pixels = small.tobytes()
        # Quantize grayscale to reduce noise from cursor/anti-aliasing.
        quantized = bytes(value // 16 for value in pixels)
        return hashlib.sha256(quantized).hexdigest()

    @staticmethod
    def _images_nearly_equal(first: Image.Image, second: Image.Image) -> bool:
        if first.size != second.size:
            second = second.resize(first.size, Image.Resampling.BILINEAR)
        a = first.convert("L").resize((32, 32), Image.Resampling.BILINEAR)
        b = second.convert("L").resize((32, 32), Image.Resampling.BILINEAR)
        diff = ImageChops.difference(a, b)
        histogram = diff.histogram()
        total = sum(histogram)
        changed = sum(count for value, count in enumerate(histogram) if value > 18)
        return (changed / max(total, 1)) < 0.015

    def start(self):
        logger.info("Khởi động GeminiSender...")
        self.sender.start()
        logger.info("Chế độ chụp: FULL SCREEN (không lấy cửa sổ trình duyệt).")
        logger.info("Bắt đầu theo dõi màn hình...")
        self.capture.start_diff_watcher(on_change=self._on_screen_change)
        logger.info("GeminiBridge đang chạy. Nhấn Ctrl+C để dừng.")
        self._main_loop()

    def stop(self):
        if self._stopping:
            return
        self._stopping = True
        logger.info("Đang dừng GeminiBridge...")
        self.capture.stop_diff_watcher()
        self.sender.close()
        logger.info("Đã dừng.")

    def _on_screen_change(self, image: Image.Image):
        """Watcher callback: keep only the newest distinct frame."""
        try:
            if self._processing:
                logger.debug("Bỏ qua frame vì Gemini đang xử lý ảnh trước đó.")
                return
            image_hash = self._image_hash(image)
            if image_hash == self._last_image_hash:
                logger.debug("Bỏ qua ảnh trùng hash.")
                return

            # If there is already a pending frame, replace it with the newest one.
            try:
                old_image = self._queue.get_nowait()
                if self._images_nearly_equal(old_image, image):
                    self._queue.put_nowait(old_image)
                    logger.debug("Bỏ qua frame gần giống ảnh đang chờ.")
                    return
            except queue.Empty:
                pass

            self._queue.put_nowait(image.copy())
            self._last_image_hash = image_hash
            logger.info("Màn hình đổi → đưa ảnh mới nhất vào queue.")
        except queue.Full:
            logger.warning("Queue đầy; bỏ qua frame mới.")
        except Exception:
            logger.exception("Queue error")

    def _clear_pending_frames(self):
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def _main_loop(self):
        try:
            while not self._stopping:
                try:
                    image = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                # Pause watcher BEFORE opening/using Gemini. This prevents Gemini's
                # own UI and upload progress from becoming the next screenshot.
                self.capture.pause_diff_watcher()
                self._clear_pending_frames()
                self._processing = True
                started = time.monotonic()
                try:
                    logger.info("Đang gửi ảnh (%s), chờ xác nhận upload...", image.size)
                    response = self.sender.send_image(image, prompt=PROMPT)
                    elapsed = time.monotonic() - started
                    if response:
                        logger.info("Nhận câu trả lời sau %.1f giây (%d ký tự).", elapsed, len(response))
                        logger.info("\n%s\n", response)
                        try:
                            pyperclip.copy(response)
                            logger.info("✓ Đã copy response vào clipboard.")
                        except Exception:
                            logger.exception("Không thể copy response vào clipboard.")
                    else:
                        logger.error("Gemini không trả về câu trả lời. Kiểm tra log upload ở trên.")
                except Exception:
                    logger.exception("Lỗi gửi Gemini")
                finally:
                    # Resume with a fresh baseline so Gemini's own window is not
                    # interpreted as a new question when the watcher wakes up.
                    self._clear_pending_frames()
                    self._processing = False
                    self.capture.resume_diff_watcher(reset_baseline=True)
        except KeyboardInterrupt:
            self.stop()


if __name__ == "__main__":
    bridge = GeminiBridge()
    bridge.start()
