from pathlib import Path
from datetime import datetime
import shutil
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = Path.cwd()
FILES = [
    (SCRIPT_DIR / "gemini_bridge.py", ROOT / "gemini_bridge.py"),
    (SCRIPT_DIR / "screen_capture.py", ROOT / "screen_capture.py"),
    (SCRIPT_DIR / "browser" / "gemini_sender.py", ROOT / "browser" / "gemini_sender.py"),
]

def main():
    if not all((ROOT / p).exists() for p in ("gemini_bridge.py", "screen_capture.py", "browser")):
        print("LOI: Hay chay lenh tu thu muc goc ai-screen-reader-main.")
        sys.exit(1)
    missing = [str(src) for src, _ in FILES if not src.exists()]
    if missing:
        print("LOI: Thieu file trong goi sua:\n" + "\n".join(missing))
        sys.exit(1)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = ROOT / f"backup_before_fast_fix_v4_{stamp}"
    backup.mkdir(parents=True, exist_ok=True)
    for _, dst in FILES:
        if dst.exists():
            target = backup / dst.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, target)
    for src, dst in FILES:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
            print(f"Da cap nhat: {dst.relative_to(ROOT)}")
    print("\nDA CAI BAN FAST V4.")
    print(f"Backup: {backup}")
    print("Kiem tra: python -m compileall gemini_bridge.py browser\\gemini_sender.py screen_capture.py")
    print("Chay: python gemini_bridge.py")

if __name__ == "__main__":
    main()
