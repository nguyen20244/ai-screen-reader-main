"""
browser/gemini_sender.py
Dùng expect_file_chooser + click nút "+" để upload ảnh tự động.
"""

import time
import tempfile
import logging
from pathlib import Path
from typing import Optional
from PIL import Image
import cloakbrowser

logger = logging.getLogger(__name__)

PROFILE_DIR      = Path(r"C:\gemini_profile")
GEMINI_URL       = "https://gemini.google.com/"
RESPONSE_TIMEOUT = 60
POLL_INTERVAL    = 1.5


class GeminiSender:

    def __init__(self):
        self._context = None
        self._page    = None
        self._started = False

    def start(self):
        if self._started:
            return

        PROFILE_DIR.mkdir(parents=True, exist_ok=True)

        logger.info("Khởi động CloakBrowser → Gemini...")
        self._context = cloakbrowser.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=["--disable-notifications"],
        )

        self._page = self._context.new_page()
        self._page.goto(GEMINI_URL, timeout=30000)
        time.sleep(3)

        if "accounts.google.com" in self._page.url:
            print("\n[ACTION] Chưa đăng nhập Google.")
            print("[ACTION] Hãy đăng nhập trong cửa sổ trình duyệt.")
            print("[ACTION] Sau khi vào được Gemini, nhấn Enter để tiếp tục...")
            input()

        logger.info("GeminiSender sẵn sàng.")
        self._started = True

    def close(self):
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        self._started = False
        self._page    = None
        self._context = None

    def send_image(
        self,
        image: Image.Image,
        prompt: str = "Đây là câu hỏi trên màn hình. Hãy phân tích và trả lời chính xác, ngắn gọn.",
    ) -> Optional[str]:
        if not self._started:
            self.start()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        image.save(tmp_path, format="PNG")

        try:
            return self._do_send(tmp_path, prompt)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def _do_send(self, image_path: str, prompt: str) -> Optional[str]:
        page = self._page

        self._new_conversation()

        # Chờ trang ổn định
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        time.sleep(1.0)

        # Đưa ảnh vào Windows clipboard rồi Ctrl+V vào textarea
        try:
            import win32clipboard
            from io import BytesIO

            img = Image.open(image_path).convert("RGB")
            bmp_io = BytesIO()
            img.save(bmp_io, format="BMP")
            bmp_data = bmp_io.getvalue()[14:]  # bỏ BMP file header 14 bytes

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
            win32clipboard.CloseClipboard()
            time.sleep(0.3)
            logger.debug("Đã đưa ảnh vào clipboard.")
        except Exception as e:
            logger.error(f"Clipboard thất bại: {e}")
            return None

        # Click vào textarea rồi Ctrl+V
        # Selector chính xác từ HTML: div.ql-editor bên trong rich-textarea
        try:
            textarea = page.locator(
                "rich-textarea div.ql-editor[contenteditable='true']"
            ).first
            textarea.click()
            time.sleep(0.3)
            textarea.press("Control+v")
            time.sleep(2.0)  # chờ Gemini xử lý ảnh
            logger.debug("Paste ảnh OK.")
        except Exception as e:
            logger.error(f"Paste vào textarea thất bại: {e}")
            return None

        # Gõ prompt (dùng lại cùng textarea)
        try:
            textarea.type(prompt, delay=20)
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Nhập prompt thất bại: {e}")
            return None

        # Gửi
        try:
            textarea.press("Enter")
            logger.debug("Đã gửi.")
        except Exception as e:
            logger.error(f"Gửi thất bại: {e}")
            return None

        return self._wait_for_response()

    def _new_conversation(self):
        try:
            # Selector chính xác từ HTML của Gemini
            btn = self._page.locator("a[href='/app'][aria-label='New chat']").first
            btn.click(timeout=3000)
            time.sleep(1.5)
            logger.debug("Mở conversation mới.")
        except Exception:
            logger.debug("Không tìm thấy New chat → goto Gemini URL.")
            self._page.goto(GEMINI_URL)
            time.sleep(3)

    def _wait_for_response(self) -> Optional[str]:
        page     = self._page
        deadline = time.time() + RESPONSE_TIMEOUT
        time.sleep(2)

        last_text    = ""
        stable_count = 0

        while time.time() < deadline:
            try:
                blocks = page.locator(
                    "model-response .markdown, "
                    "message-content .markdown, "
                    ".response-container .markdown, "
                    "div[data-response-id] .markdown, "
                    ".model-response-text"
                ).all()

                if blocks:
                    current_text = blocks[-1].inner_text()
                    if current_text and current_text == last_text:
                        stable_count += 1
                        if stable_count >= 3:
                            logger.info(f"Response nhận được ({len(current_text)} ký tự).")
                            return current_text.strip()
                    else:
                        stable_count = 0
                        last_text    = current_text

            except Exception as e:
                logger.debug(f"Poll error: {e}")

            time.sleep(POLL_INTERVAL)

        logger.warning("Timeout chờ response Gemini.")
        return last_text.strip() if last_text else None
