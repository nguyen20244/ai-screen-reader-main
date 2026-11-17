"""
browser/gemini_session.py
Chạy 1 lần để login Gemini và lưu session:
    python browser/gemini_session.py
"""

import time
from pathlib import Path
import cloakbrowser

# Thay dòng này trong cả 2 file:
PROFILE_DIR = Path("data/gemini_profile").resolve()

# Thành đường dẫn profile của FACECHEK, ví dụ:
PROFILE_DIR = Path(r"C:\Users\nguyen\Desktop\New folder (2)\New folder\FACECHEK\data\cloak_profile").resolve()
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

GEMINI_URL = "https://gemini.google.com/"


def open_session():
    print(f"[INFO] Profile lưu tại: {PROFILE_DIR}")
    print("[INFO] Đang khởi động CloakBrowser...")

    context = cloakbrowser.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,
        args=["--disable-notifications"],
    )

    page = context.new_page()
    page.goto(GEMINI_URL, timeout=30000)
    time.sleep(3)

    # Kiểm tra đã login chưa
    if "accounts.google.com" in page.url or "signin" in page.url:
        print("[ACTION] Chưa đăng nhập Google.")
        print("[ACTION] Hãy đăng nhập tài khoản Google trong cửa sổ trình duyệt.")
        print("[ACTION] Sau khi vào được Gemini, nhấn Enter tại đây.")
        input()
    else:
        print("[OK] Đã đăng nhập Gemini.")

    print(f"[OK] Session đã lưu tại: {PROFILE_DIR}")
    input("Nhấn Enter để đóng trình duyệt...")
    context.close()


if __name__ == "__main__":
    open_session()
