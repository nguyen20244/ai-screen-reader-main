# 🚀 START HERE - AI Screen Reader Quick Start

## 📋 **What You Need to Do**

### **1. Install Python (Required)**

**Option A: Microsoft Store (Easiest)**
1. Press `Windows + R`
2. Type: `ms-windows-store://pdp/?ProductId=9NRWMJP3717K`
3. Press Enter → Microsoft Store opens
4. Click "Install" for Python 3.11

**Option B: Download from Website**
1. Go to [python.org/downloads](https://python.org/downloads/)
2. Download Python 3.8+
3. **IMPORTANT**: Check "Add Python to PATH" during installation

### **2. Install Tesseract OCR (Required)**
1. Go to [Tesseract Releases](https://github.com/tesseract-ocr/tesseract/releases)
2. Download: `tesseract-ocr-w64-setup-v5.x.x.exe`
3. Install to default location: `C:\Program Files\Tesseract-OCR\`

### **3. Get API Keys (At least one required)**
- **OpenAI**: [Get Key Here](https://platform.openai.com/api-keys)
- **Anthropic**: [Get Key Here](https://console.anthropic.com/)

---

## 🎯 **How to Start the Application**

### **Method 1: Automatic Setup (Recommended)**

1. **Double-click** `setup_and_run.bat`
2. Follow the prompts
3. The script will:
   - Check Python installation
   - Install required packages
   - Help you configure API keys
   - Start the application

### **Method 2: PowerShell Script**

1. **Right-click** on `start_app.ps1`
2. Select "Run with PowerShell"
3. Follow the prompts

### **Method 3: Manual Commands**

Open Command Prompt or PowerShell in this folder and run:

```bash
# Install dependencies
pip install -r requirements.txt

# Copy configuration template
copy .env.example .env

# Edit .env file with your API keys
notepad .env

# Test everything works
python test_components.py

# Start the application
python main.py
```

---

## ⚙️ **Configuration**

### **Edit .env File**
Open `.env` file and add your API keys:

```env
# Add your API keys here (get at least one)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Tesseract path (usually auto-detected)
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

# Settings (optional)
REFRESH_INTERVAL=30
DEFAULT_AI_PROVIDER=claude
```

---

## 🎮 **Using the Application**

1. **Start the app** using one of the methods above
2. **Configure settings** in the GUI:
   - Set refresh interval (default: 30 seconds)
   - Choose AI provider (Claude or OpenAI)
3. **Click "Start Reading"** to begin
4. **View results** in the tabs:
   - **Extracted Text**: What the OCR reads from your screen
   - **Detected Questions**: Questions and MCQs found
   - **AI Answers**: Generated answers with explanations

---

## 🔧 **Troubleshooting**

### **Common Issues & Solutions**

| Problem | Solution |
|---------|----------|
| "Python not found" | Install Python and add to PATH |
| "Tesseract not found" | Install Tesseract OCR |
| "No API key found" | Add valid API keys to .env file |
| "No text extracted" | Check screen has readable text |
| "Permission denied" | Run as Administrator |

### **Test Your Setup**
Run this command to test everything:
```bash
python test_components.py
```

### **Check Logs**
If something goes wrong, check the log file:
- Location: `logs/screen_reader.log`
- Contains detailed error information

---

## 📱 **Perfect For**

- **Online MCQ Exams**: Automatically detects and answers multiple choice questions
- **Study Sessions**: Get explanations for complex questions
- **Educational Content**: Extract and analyze text from any screen
- **Accessibility**: Helps users with reading difficulties

---

## 🎯 **Example Usage**

1. Open a browser with MCQ questions
2. Start the AI Screen Reader
3. Every 30 seconds it will:
   - Capture your screen
   - Extract all text using OCR
   - Detect questions like:
     ```
     What is the capital of France?
     A) London
     B) Berlin
     C) Paris
     D) Madrid
     ```
   - Provide AI answer: "C) Paris - Paris is the capital and largest city of France..."

---

## 🆘 **Need Help?**

1. **Run the test script**: `python test_components.py`
2. **Check the logs**: Look in `logs/screen_reader.log`
3. **Verify prerequisites**: Make sure Python, Tesseract, and API keys are set up
4. **Try different settings**: Adjust refresh interval or screen region

---

## 🔒 **Privacy & Security**

- **Your data stays local**: Only questions are sent to AI APIs
- **API keys are secure**: Stored locally in .env file
- **No tracking**: No telemetry or usage data collected
- **Open source**: You can review all the code

---

**🎉 Ready to start? Double-click `setup_and_run.bat` and follow the prompts!**
