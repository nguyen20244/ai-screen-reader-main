"""Upload screenshots to Gemini and send the prompt only after attachment verification."""

import logging
import tempfile
import time
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image
import cloakbrowser

logger = logging.getLogger(__name__)

PROFILE_DIR = Path(r"C:\gemini_profile")
GEMINI_URL = "https://gemini.google.com/"
RESPONSE_TIMEOUT = 75
POLL_INTERVAL = 0.35
ATTACHMENT_POLL_INTERVAL = 0.2
ATTACHMENT_STABLE_SECONDS = 0.6
UPLOAD_TIMEOUT = 45


class GeminiSender:
    def __init__(self):
        self._context = None
        self._page = None
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
        self._page.goto(GEMINI_URL, wait_until="domcontentloaded", timeout=45000)
        try:
            self._page.locator("rich-textarea div.ql-editor[contenteditable='true']").first.wait_for(
                state="visible", timeout=30000
            )
        except Exception:
            if "accounts.google.com" in self._page.url:
                print("\n[ACTION] Hãy đăng nhập Google trong cửa sổ Gemini.")
                input("[ACTION] Sau khi đăng nhập và thấy ô nhập Gemini, nhấn Enter...")
            else:
                logger.warning("Chưa xác nhận được ô nhập Gemini khi khởi động; sẽ kiểm tra lại khi gửi.")
        self._started = True
        logger.info("GeminiSender sẵn sàng.")

    def close(self):
        try:
            if self._context:
                self._context.close()
        except Exception:
            logger.exception("Lỗi khi đóng trình duyệt Gemini")
        self._started = False
        self._page = None
        self._context = None

    def send_image(self, image: Image.Image, prompt: str = "Đọc ảnh và trả lời chính xác, ngắn gọn.") -> Optional[str]:
        if not self._started:
            self.start()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image_path = tmp.name
        try:
            image.convert("RGB").save(image_path, format="PNG", optimize=False, compress_level=1)
            logger.info("Ảnh chụp đã lưu tạm: %s (%d bytes)", image_path, Path(image_path).stat().st_size)
            return self._do_send(image_path, prompt)
        finally:
            try:
                Path(image_path).unlink(missing_ok=True)
            except OSError:
                logger.warning("Không xóa được file ảnh tạm: %s", image_path)

    def _new_conversation(self):
        page = self._page
        try:
            button = page.locator("a[href='/app'][aria-label='New chat']").first
            button.click(timeout=4000)
            page.locator("rich-textarea div.ql-editor[contenteditable='true']").first.wait_for(
                state="visible", timeout=15000
            )
            logger.debug("Đã mở cuộc trò chuyện mới.")
        except Exception:
            logger.debug("Không mở được New chat bằng nút; điều hướng về Gemini.")
            page.goto(GEMINI_URL, wait_until="domcontentloaded", timeout=45000)
            page.locator("rich-textarea div.ql-editor[contenteditable='true']").first.wait_for(
                state="visible", timeout=30000
            )

    def _put_image_on_clipboard(self, image_path: str) -> bool:
        import win32clipboard
        from PIL import Image as PILImage

        with PILImage.open(image_path) as source:
            image = source.convert("RGB")
            bitmap = BytesIO()
            image.save(bitmap, format="BMP")
            dib_data = bitmap.getvalue()[14:]

        last_error = None
        for attempt in range(1, 6):
            opened = False
            try:
                win32clipboard.OpenClipboard()
                opened = True
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib_data)
                logger.info("Đã nạp ảnh vào clipboard (%d x %d).", image.size[0], image.size[1])
                return True
            except Exception as exc:
                last_error = exc
                logger.warning("Clipboard thử lần %d/5 thất bại: %s", attempt, exc)
                time.sleep(0.35 * attempt)
            finally:
                if opened:
                    try:
                        win32clipboard.CloseClipboard()
                    except Exception:
                        pass
        logger.error("Không thể đưa ảnh vào clipboard: %s", last_error)
        return False

    def _attachment_state(self):
        """Inspect visible Gemini attachment previews and active upload indicators."""
        return self._page.evaluate("""() => {
            const visible = (el) => {
              if (!el) return false;
              const style = window.getComputedStyle(el);
              const rect = el.getBoundingClientRect();
              return style.display !== 'none' && style.visibility !== 'hidden'
                && Number(style.opacity || 1) > 0
                && rect.width > 0 && rect.height > 0;
            };

            const attachmentSelectors = [
              'rich-textarea img',
              'rich-textarea [data-test-id*="attachment"]',
              'rich-textarea [aria-label*="Remove"]',
              'rich-textarea [aria-label*="Xóa"]',
              '[data-test-id*="attachment"] img',
              '[class*="attachment"] img',
              '[class*="preview"] img',
              'file-preview',
              'image-preview',
              'button[aria-label*="Remove image"]',
              'button[aria-label*="Remove attachment"]'
            ];

            let found = false;
            for (const selector of attachmentSelectors) {
              try {
                if (Array.from(document.querySelectorAll(selector)).some(visible)) {
                  found = true;
                  break;
                }
              } catch (_) {}
            }

            if (!found) {
              found = Array.from(document.images).some(img => {
                const src = img.getAttribute('src') || '';
                return (src.startsWith('blob:') || src.startsWith('data:image/'))
                  && img.complete && img.naturalWidth > 40 && img.naturalHeight > 40
                  && visible(img);
              });
            }

            // Ignore stale/hidden body text. Only visible progress UI counts.
            const progressElements = Array.from(document.querySelectorAll(
              '[role="progressbar"], [aria-label*="Uploading"], [aria-label*="uploading"], [aria-label*="Đang tải lên"]'
            )).filter(visible);

            const uploading = progressElements.some(el => {
              const value = el.getAttribute('aria-valuenow');
              if (value !== null && value !== '') {
                const numeric = Number(value);
                return Number.isFinite(numeric) && numeric < 100;
              }
              // An indeterminate progressbar is active; a generic aria-label alone
              // is not enough because Gemini can leave stale labels in the DOM.
              return el.getAttribute('role') === 'progressbar'
                && el.getAttribute('aria-valuenow') === null;
            });

            const sendButton = Array.from(document.querySelectorAll(
              'button[aria-label*="Send"], button[aria-label*="Gửi"], button[data-testid*="send"]'
            )).find(visible);
            const sendEnabled = !!sendButton && !sendButton.disabled
              && sendButton.getAttribute('aria-disabled') !== 'true';

            return { found, uploading, sendEnabled, progressCount: progressElements.length };
        }""")

    def _wait_for_image_attachment(self) -> bool:
        """Wait for a visible attachment preview and a stable completion state."""
        deadline = time.monotonic() + UPLOAD_TIMEOUT
        stable_since = None
        last_state = None

        while time.monotonic() < deadline:
            try:
                state = self._attachment_state()
                found = bool(state.get("found"))
                uploading = bool(state.get("uploading"))

                # Fast but safe: require a visible preview and no active upload indicator.
                # Do not treat an enabled Send button as proof that upload has finished.
                ready = found and not uploading
                if ready:
                    if stable_since is None:
                        stable_since = time.monotonic()
                    if time.monotonic() - stable_since >= ATTACHMENT_STABLE_SECONDS:
                        logger.info("✓ Gemini đã nhận ảnh; upload ổn định, có thể gửi prompt.")
                        return True
                else:
                    stable_since = None

                if state != last_state:
                    logger.info(
                        "Trạng thái upload: attachment=%s, uploading=%s, send_enabled=%s, progress=%s",
                        found, uploading, state.get("sendEnabled"), state.get("progressCount", 0)
                    )
                    last_state = state
            except Exception as exc:
                logger.debug("Chưa đọc được trạng thái attachment: %s", exc)
                stable_since = None

            time.sleep(ATTACHMENT_POLL_INTERVAL)

        logger.error(
            "UPLOAD TIMEOUT sau %d giây: không xác nhận được ảnh đính kèm ổn định. "
            "Đã hủy gửi prompt để tránh gửi câu hỏi không có ảnh.", UPLOAD_TIMEOUT
        )
        return False

    def _do_send(self, image_path: str, prompt: str) -> Optional[str]:
        page = self._page
        self._new_conversation()
        composer = page.locator("rich-textarea div.ql-editor[contenteditable='true']").first
        composer.wait_for(state="visible", timeout=20000)

        # A fresh conversation should have an empty composer before the new paste.
        try:
            before_paste = self._attachment_state()
            if before_paste.get("found"):
                logger.warning("Composer vẫn có attachment trước khi paste; kiểm tra thao tác New chat.")
        except Exception:
            logger.debug("Không đọc được trạng thái composer trước khi paste.")

        if not self._put_image_on_clipboard(image_path):
            return None

        try:
            composer.click(timeout=10000)
            composer.press("Control+v", timeout=10000)
        except Exception as exc:
            logger.exception("Không paste được ảnh vào Gemini: %s", exc)
            return None

        logger.info("Đã paste ảnh; đang chờ Gemini xác nhận attachment (tối đa %ds)...", UPLOAD_TIMEOUT)
        if not self._wait_for_image_attachment():
            return None

        # Do not type/send anything until attachment verification succeeds.
        try:
            composer.click(timeout=10000)
            composer.fill(prompt, timeout=10000)
            composer.press("Enter", timeout=10000)
            logger.info("Đã gửi prompt kèm ảnh đã xác nhận.")
        except Exception:
            logger.exception("Không thể nhập/gửi prompt sau khi upload ảnh.")
            return None

        return self._wait_for_response()

    def _wait_for_response(self) -> Optional[str]:
        page = self._page
        deadline = time.monotonic() + RESPONSE_TIMEOUT
        time.sleep(0.3)
        last_text = ""
        stable_count = 0
        while time.monotonic() < deadline:
            try:
                blocks = page.locator(
                    "model-response .markdown, message-content .markdown, "
                    ".response-container .markdown, div[data-response-id] .markdown, "
                    ".model-response-text"
                ).all()
                if blocks:
                    current_text = blocks[-1].inner_text().strip()
                    if current_text and current_text == last_text:
                        stable_count += 1
                        if stable_count >= 2:
                            logger.info("Response nhận được (%d ký tự).", len(current_text))
                            return current_text
                    else:
                        stable_count = 0
                        last_text = current_text
            except Exception as exc:
                logger.debug("Lỗi khi kiểm tra response: %s", exc)
            time.sleep(POLL_INTERVAL)
        logger.warning("Timeout chờ response Gemini sau %d giây.", RESPONSE_TIMEOUT)
        return last_text or None
