# MedAI Web App - Hugging Face Spaces Deployment

This is the web-deployable version of MedAI using Google Gemini Flash model.

## 🚀 Quick Deploy to Hugging Face Spaces

1. **Create New Space**: Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. **Choose Settings**:
   - Space name: `medai-assistant`
   - License: MIT
   - SDK: Gradio
   - Hardware: CPU Basic (free)

3. **Upload Files**:
   - `app.py` (main application)
   - `requirements_app.txt` (rename to `requirements.txt`)
   - `lab_report.pdf` (your medical lab report)
   - `.env` file with your API keys

4. **Set Secrets** (in Space settings):
   - `GOOGLE_API_KEY`: Your Google Gemini API key
   - `PUSHOVER_USER`: Your Pushover user key (optional)
   - `PUSHOVER_TOKEN`: Your Pushover token (optional)

5. **Deploy**: HF Spaces will automatically install dependencies and run `app.py`

## 📋 Required Files

- `app.py` - Main web application
- `requirements_app.txt` - Python dependencies
- `.env` - Environment variables (API keys)

## 📄 PDF Upload Feature

**New Feature**: Users can now upload their own lab report PDFs directly in the web interface!

### How It Works:
1. **Upload PDF**: Click "Upload your lab report PDF" and select a PDF file
2. **Process**: Click "Process PDF" to extract and analyze the content
3. **Chat**: Ask questions about your lab results with personalized responses
4. **Re-upload**: Upload different reports anytime to analyze new results

### Benefits:
- ✅ **Flexible**: No need to pre-upload PDFs to the Space
- ✅ **Private**: PDFs stay in your browser session
- ✅ **Personalized**: Get specific answers about your lab results
- ✅ **Dynamic**: Switch between different lab reports easily

## 🔧 Local Testing

```bash
# Install dependencies
pip install -r requirements_app.txt

# Create .env file with your keys
cp env_example.txt .env
# Edit .env with your actual API keys

# Add your lab_report.pdf (optional)

# Run locally
python app.py
```

## 🛠️ Features

- **Medical AI Chat**: Uses Google Gemini 2.5 Flash
- **PDF Processing**: Reads and analyzes lab reports
- **Tool Calling**: Three medical safety tools
- **Pushover Notifications**: Alerts for patient contacts and safety issues
- **Web Interface**: Gradio-based chat interface
- **Medical Safety**: Built-in disclaimers and ethical guidelines

## 🔑 API Keys Required

### Required
- **Google Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Optional (for notifications)
- **Pushover Keys**: Get from [Pushover.net](https://pushover.net/)

## 📱 Tool Functions

1. **Patient Contact**: Records interest and sends notifications
2. **Unknown Queries**: Logs questions outside AI's scope
3. **Safety Monitoring**: Flags inappropriate medical content

## ⚠️ Medical Disclaimer

This AI assistant:
- Provides general medical information only
- Never gives specific diagnoses
- Always recommends professional medical consultation
- Is not a substitute for healthcare providers

## 🔍 Troubleshooting

**App won't start:**
- Check API keys in Space secrets
- Ensure `lab_report.pdf` is uploaded (optional)

**Tools not working:**
- Verify Pushover keys are set
- Check Space logs for errors

**PDF not loading:**
- Ensure file is named exactly `lab_report.pdf`
- Check PDF is not password-protected
