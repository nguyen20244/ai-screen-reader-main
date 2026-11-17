"""
Simple script to check if Python and required packages are available
"""
import sys
import subprocess
import importlib

def check_python_version():
    """Check Python version"""
    print(f"Python version: {sys.version}")
    
    version_info = sys.version_info
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    else:
        print("✅ Python version is compatible")
        return True

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} is installed")
        return True
    except ImportError:
        print(f"❌ {package_name} is NOT installed")
        return False

def install_package(package_name):
    """Try to install a package"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package_name}")
        return False

def main():
    print("🔍 Checking Python Environment for AI Screen Reader")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Please install Python 3.8 or higher")
        return False
    
    print("\n📦 Checking required packages...")
    
    packages = [
        ("pillow", "PIL"),
        ("pytesseract", "pytesseract"),
        ("pyautogui", "pyautogui"),
        ("opencv-python", "cv2"),
        ("numpy", "numpy"),
        ("openai", "openai"),
        ("anthropic", "anthropic"),
        ("python-dotenv", "dotenv")
    ]
    
    missing_packages = []
    
    for package_name, import_name in packages:
        if not check_package(package_name, import_name):
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        
        install_choice = input("\nWould you like to install missing packages? (y/n): ")
        if install_choice.lower() == 'y':
            print("\n📥 Installing missing packages...")
            for package in missing_packages:
                install_package(package)
        else:
            print("\n❌ Cannot run application without required packages")
            return False
    
    print("\n🎉 All packages are available!")
    
    # Check Tesseract
    print("\n🔍 Checking Tesseract OCR...")
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract OCR is installed: {version}")
    except Exception as e:
        print(f"❌ Tesseract OCR issue: {e}")
        print("Please install Tesseract OCR from: https://github.com/tesseract-ocr/tesseract/releases")
        return False
    
    # Check .env file
    print("\n🔍 Checking configuration...")
    import os
    if os.path.exists('.env'):
        print("✅ .env file exists")
        
        from dotenv import load_dotenv
        load_dotenv()
        
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        if openai_key and openai_key != 'your_openai_key_here':
            print("✅ OpenAI API key configured")
        else:
            print("⚠️  OpenAI API key not configured")
        
        if anthropic_key and anthropic_key != 'your_anthropic_key_here':
            print("✅ Anthropic API key configured")
        else:
            print("⚠️  Anthropic API key not configured")
        
        if not ((openai_key and openai_key != 'your_openai_key_here') or 
                (anthropic_key and anthropic_key != 'your_anthropic_key_here')):
            print("❌ No valid API keys found. Please edit .env file with your API keys.")
            return False
    else:
        print("❌ .env file not found. Please copy .env.example to .env and add your API keys.")
        return False
    
    print("\n🎉 Environment check completed successfully!")
    print("✅ Ready to run AI Screen Reader!")
    
    run_choice = input("\nWould you like to run the application now? (y/n): ")
    if run_choice.lower() == 'y':
        print("\n🚀 Starting AI Screen Reader...")
        try:
            import main
            # This will start the application
        except Exception as e:
            print(f"❌ Error starting application: {e}")
            return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("\nPress Enter to exit...")
