# AI Screen Reader - Setup Guide

## Overview

This AI Screen Reader automatically captures your screen every 30 seconds, extracts text using OCR, detects questions (especially MCQs), and provides AI-generated answers using Claude or ChatGPT.

## Prerequisites

### 1. Python 3.8+
- Download from [python.org](https://python.org)
- Make sure to check "Add Python to PATH" during installation

### 2. Tesseract OCR
- **Windows**: Download installer from [GitHub releases](https://github.com/tesseract-ocr/tesseract/releases)
  - Install to default location: `C:\Program Files\Tesseract-OCR\`
  - Add to PATH or update `.env` file with the path
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### 3. API Keys
You need at least one of these:
- **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Anthropic API Key**: Get from [Anthropic Console](https://console.anthropic.com/)

## Installation

### Option 1: Automatic (Windows)
1. Run `install.bat`
2. Follow the prompts

### Option 2: Manual
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create configuration file:
   ```bash
   copy .env.example .env    # Windows
   cp .env.example .env      # macOS/Linux
   ```

3. Edit `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

## Testing

Before running the main application, test all components:

```bash
python test_components.py
```

This will test:
- Screen capture
- OCR text extraction
- Question detection
- AI integration
- Full pipeline

## Running the Application

```bash
python main.py
```

## Usage

1. **Start the Application**: Run `python main.py`

2. **Configure Settings**:
   - Set refresh interval (default: 30 seconds)
   - Choose AI provider (Claude or OpenAI)

3. **Start Reading**: Click "Start Reading" button

4. **Monitor Results**:
   - **Extracted Text** tab: Shows OCR results from screen
   - **Detected Questions** tab: Shows identified questions and MCQs
   - **AI Answers** tab: Shows AI-generated answers

5. **Stop Reading**: Click "Stop Reading" button

## Features

### Screen Capture
- Captures full screen or custom regions
- Automatic image preprocessing for better OCR
- Configurable capture intervals

### OCR (Optical Character Recognition)
- Uses Tesseract OCR engine
- Image preprocessing for better accuracy
- Confidence scoring for text quality

### Question Detection
- Detects various question types:
  - Multiple choice questions (A, B, C, D)
  - Numbered questions
  - "What is..." questions
  - "Which of..." questions
  - True/False questions
- Extracts MCQ options automatically

### AI Integration
- Supports both Claude (Anthropic) and ChatGPT (OpenAI)
- Automatic question formatting
- Error handling and retry logic

## Configuration Options

Edit `config.py` or use the GUI to configure:

- **Refresh Interval**: How often to scan (default: 30 seconds)
- **AI Provider**: Claude or OpenAI
- **Screen Region**: Full screen or custom area
- **OCR Settings**: Tesseract configuration
- **Question Patterns**: Customize question detection

## Troubleshooting

### Common Issues

1. **"Tesseract not found"**
   - Install Tesseract OCR
   - Add to PATH or set `TESSERACT_PATH` in `.env`

2. **"No API key found"**
   - Add your API keys to `.env` file
   - Make sure the file is in the same directory as `main.py`

3. **"No text extracted"**
   - Check if screen has readable text
   - Try adjusting OCR settings
   - Ensure good contrast on screen

4. **"AI provider not available"**
   - Check API key validity
   - Verify internet connection
   - Check API service status

### Performance Tips

1. **Improve OCR Accuracy**:
   - Use high contrast text
   - Avoid small fonts
   - Ensure good lighting/screen brightness

2. **Reduce Resource Usage**:
   - Increase refresh interval
   - Use smaller screen regions
   - Close unnecessary applications

3. **Better Question Detection**:
   - Use clear question formatting
   - Ensure questions are visible on screen
   - Avoid overlapping windows

## File Structure

```
screen-reader/
├── main.py                 # Main application entry point
├── config.py              # Configuration management
├── screen_capture.py      # Screen capture functionality
├── ocr_processor.py       # OCR text extraction
├── question_detector.py   # Question detection logic
├── ai_integration.py      # AI API integration
├── gui.py                 # GUI interface
├── automation_engine.py   # Main automation logic
├── test_components.py     # Component testing
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .env                  # Your configuration (create this)
├── README.md             # Project documentation
├── SETUP_GUIDE.md        # This setup guide
└── logs/                 # Application logs
```

## Support

If you encounter issues:

1. Run `python test_components.py` to identify problems
2. Check the `logs/screen_reader.log` file for errors
3. Ensure all prerequisites are properly installed
4. Verify API keys are valid and have sufficient credits

## Security Notes

- Keep your API keys secure and never share them
- The `.env` file contains sensitive information
- Consider using environment variables in production
- Monitor your API usage to avoid unexpected charges
