"""Gemini bridge with full-screen capture, duplicate suppression and feedback-loop guard."""

import hashlib
import logging
import queue
import re
import threading
import time
import tempfile
import os

import numpy as np
import pyperclip
from PIL import Image, ImageChops

from config import config
from screen_capture import ScreenCapture
from browser.gemini_sender import GeminiSender

# ---------------------------------------------------------------------------
# Text-to-speech (gTTS — giọng Việt chuẩn, cần internet)
# ---------------------------------------------------------------------------
try:
    from gtts import gTTS
    import pygame
    pygame.mixer.init()
    TTS_AVAILABLE = True
except Exception as _tts_init_err:
    TTS_AVAILABLE = False
    logging.getLogger("TTS").warning("gTTS/pygame không khởi động được: %s", _tts_init_err)

_tts_lock = threading.Lock()


def _extract_answer_for_tts(response: str) -> str:
    """
    Rút gọn response để đọc: chỉ lấy dòng Đáp án + 1-2 câu giải thích đầu.
    Bỏ tên file ảnh (image_*.png) và ký hiệu markdown.
    """
    # Xóa dòng tên file ảnh
    text = re.sub(r'\bimage_[0-9a-f]+\.png\b', '', response)
    # Xóa markdown bold/italic
    text = re.sub(r'[*_`#]', '', text)
    # Xóa dòng trống thừa
    text = re.sub(r'\n{2,}', '\n', text).strip()
    # Giới hạn độ dài: lấy tối đa 3 câu đầu
    sentences = re.split(r'(?<=[.!?])\s+', text)
    short = ' '.join(sentences[:3])
    return short


def speak(text: str):
    """Đọc text tiếng Việt ra loa trong background thread (non-blocking)."""
    if not TTS_AVAILABLE:
        return

    def _run():
        tmp = None
        with _tts_lock:
            try:
                tts = gTTS(text=text, lang='vi')
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                    tmp = f.name
                tts.save(tmp)
                pygame.mixer.music.load(tmp)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            except Exception as e:
                logging.getLogger("TTS").warning("TTS lỗi: %s", e)
            finally:
                if tmp and os.path.exists(tmp):
                    try:
                        os.unlink(tmp)
                    except Exception:
                        pass

    threading.Thread(target=_run, daemon=True).start()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("GeminiBridge")

PROMPT = (
    "Đây là ảnh chụp màn hình chứa câu hỏi. "
    "Hãy đọc kỹ và trả lời CHÍNH XÁC, NGẮN GỌN. "
    "nếu ảnh sai hoặc bị lỗi thì nhắn ảnh lỗi là được. k cần dài dòng "
    "Nếu là câu hỏi trắc nghiệm, chỉ cần trả lời câu mấy ví dụ câu 1  đáp án đúng là (A/B/C/D)  "
    "nhắn lại 3 lần. ví dụ câu 1  đáp án đúng là (A/B/C/D),câu 1  đáp án đúng là (A/B/C/D),câu 1  đáp án đúng là (A/B/C/D) "
)

# --- Tuning constants -------------------------------------------------------
# Hash dùng độ phân giải cao hơn để phân biệt text khác nhau
HASH_RESIZE = (128, 96)         # (W, H) — đủ nhỏ để nhanh, đủ lớn để thấy text

# Ngưỡng "gần giống" trong queue — chỉ bỏ nếu thực sự không đổi gì
NEARLY_EQUAL_THRESHOLD = 0.004  # <0.4% pixel thay đổi mới bỏ qua


class GeminiBridge:
    """Capture full screen, send one verified image at a time, then resume watching."""

    def __init__(self):
        self.capture = ScreenCapture()
        self.capture.set_capture_mode("full_screen")
        self.sender = GeminiSender()
        self._queue = queue.Queue(maxsize=1)
        self._last_sent_hash = None   # hash của ảnh đã gửi Gemini (không phải ảnh thô)
        self._stopping = False
        self._processing = False

    # ------------------------------------------------------------------
    # Hash helpers — dùng vùng content, không dùng full frame
    # ------------------------------------------------------------------

    @staticmethod
    def _crop_content(image: Image.Image) -> Image.Image:
        """
        Cắt ảnh theo config.crop_* để chỉ giữ vùng câu hỏi.
        Điều chỉnh CROP_LEFT/TOP/RIGHT/BOTTOM trong .env hoặc config.py.
        Nếu crop_enabled=False, trả về ảnh gốc.
        """
        if not config.crop_enabled:
            return image
        w, h = image.size
        left   = int(w * config.crop_left)
        top    = int(h * config.crop_top)
        right  = int(w * config.crop_right)
        bottom = int(h * config.crop_bottom)
        cropped = image.crop((left, top, right, bottom))
        logger.debug(
            "Crop: (%d,%d)→(%d,%d) [%.0f%%L %.0f%%T %.0f%%R %.0f%%B] → %s",
            left, top, right, bottom,
            config.crop_left*100, config.crop_top*100,
            config.crop_right*100, config.crop_bottom*100,
            cropped.size,
        )
        return cropped

    @staticmethod
    def _image_hash(image: Image.Image) -> str:
        """
        Hash vùng content với độ phân giải đủ cao để phân biệt câu hỏi khác nhau.

        FIX: Trước đây dùng 32x32 + quantize //16 → mất quá nhiều chi tiết text
        → hai trang quiz khác nhau cho cùng hash.
        Bây giờ: crop content → resize 128x96 → grayscale → quantize //4 (ít mất hơn).
        """
        content = GeminiBridge._crop_content(image)
        small = content.convert("L").resize(HASH_RESIZE, Image.Resampling.LANCZOS)
        pixels = small.tobytes()
        # Quantize nhẹ hơn: //4 thay vì //16, giữ lại nhiều chi tiết text hơn
        quantized = bytes(v >> 2 for v in pixels)
        return hashlib.sha256(quantized).hexdigest()

    @staticmethod
    def _images_nearly_equal(first: Image.Image, second: Image.Image) -> bool:
        """
        So sánh hai ảnh trên vùng content với ngưỡng thấp hơn.

        FIX: Trước đây threshold 0.015 (1.5%) trên ảnh 32x32 rất dễ bỏ sót thay đổi nhỏ.
        Bây giờ dùng numpy mean absolute difference trên crop 128x96, threshold 0.004.
        """
        a = GeminiBridge._crop_content(first).convert("L").resize(HASH_RESIZE, Image.Resampling.BILINEAR)
        b = GeminiBridge._crop_content(second).convert("L").resize(HASH_RESIZE, Image.Resampling.BILINEAR)
        arr_a = np.array(a, dtype=np.float32)
        arr_b = np.array(b, dtype=np.float32)
        diff = np.abs(arr_a - arr_b)
        changed_pct = np.count_nonzero(diff > 10) / diff.size
        nearly = changed_pct < NEARLY_EQUAL_THRESHOLD
        if nearly:
            logger.debug("nearly_equal: %.4f%% pixel thay đổi (< %.3f%% → bỏ qua)",
                         changed_pct * 100, NEARLY_EQUAL_THRESHOLD * 100)
        else:
            logger.debug("NOT nearly_equal: %.4f%% pixel thay đổi → đây là trang mới",
                         changed_pct * 100)
        return nearly

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Watcher callback
    # ------------------------------------------------------------------

    def _on_screen_change(self, image: Image.Image):
        """Watcher callback: keep only the newest distinct frame."""
        try:
            if self._processing:
                logger.debug("Bỏ qua frame vì Gemini đang xử lý ảnh trước đó.")
                return

            new_hash = self._image_hash(image)

            # So sánh với ảnh ĐÃ GỬI Gemini (không phải frame thô trước đó)
            # FIX: Trước đây _last_image_hash là hash frame thô → mỗi lần resume
            # baseline bị reset nên hash không còn đúng nữa, dẫn đến bỏ sót.
            if new_hash == self._last_sent_hash:
                logger.debug("Content giống trang đã gửi lần cuối → bỏ qua.")
                return

            # Nếu queue đang có frame chờ, so sánh với frame đó
            try:
                old_image = self._queue.get_nowait()
                if self._images_nearly_equal(old_image, image):
                    self._queue.put_nowait(old_image)
                    logger.debug("Bỏ qua frame gần giống ảnh đang chờ trong queue.")
                    return
                # Frame mới khác → thay thế bằng frame mới nhất
                logger.debug("Frame mới khác ảnh đang chờ → thay thế bằng frame mới.")
            except queue.Empty:
                pass

            self._queue.put_nowait(image.copy())
            logger.info("Màn hình đổi → đưa ảnh mới nhất vào queue (hash: %s…)", new_hash[:12])

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

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _main_loop(self):
        try:
            while not self._stopping:
                try:
                    image = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                self.capture.pause_diff_watcher()
                self._clear_pending_frames()
                self._processing = True
                started = time.monotonic()

                # Tính hash TRƯỚC khi gửi để lưu lại
                sent_hash = self._image_hash(image)

                try:
                    # Crop ảnh trước khi gửi — bỏ browser UI, taskbar, vùng trắng
                    send_image = self._crop_content(image)
                    logger.info(
                        "Gửi ảnh đã crop: %s → %s (crop=%s)",
                        image.size, send_image.size, config.crop_enabled,
                    )
                    response = self.sender.send_image(send_image, prompt=PROMPT)
                    elapsed = time.monotonic() - started

                    if response:
                        # Lưu hash ảnh đã gửi thành công
                        self._last_sent_hash = sent_hash
                        logger.info("Nhận câu trả lời sau %.1f giây (%d ký tự).", elapsed, len(response))
                        logger.info("\n%s\n", response)
                        try:
                            pyperclip.copy(response)
                            logger.info("✓ Đã copy response vào clipboard.")
                        except Exception:
                            logger.exception("Không thể copy response vào clipboard.")
                        # Đọc đáp án ra loa
                        tts_text = _extract_answer_for_tts(response)
                        logger.info("🔊 Đọc: %s", tts_text[:80])
                        speak(tts_text)
                    else:
                        logger.error("Gemini không trả về câu trả lời. Kiểm tra log upload ở trên.")
                except Exception:
                    logger.exception("Lỗi gửi Gemini")
                finally:
                    self._clear_pending_frames()
                    self._processing = False
                    self.capture.resume_diff_watcher(reset_baseline=True)

        except KeyboardInterrupt:
            self.stop()


if __name__ == "__main__":
    bridge = GeminiBridge()
    bridge.start()
