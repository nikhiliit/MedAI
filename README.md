# MedAI - Medical AI Helper

**MedAI** is a command-line medical helper that reads lab reports and gives general medical advice using different AI language models and smart tools. This project shows how to create AI assistants that can use tools to perform tasks, with safety features for medical use.

**This codebase transforms basic LLM chat into agentic AI using tools.** Instead of just answering questions, the AI can now take actions like saving patient information, sending alerts, and moderating content through structured JSON tool calls.

## What MedAI Can Do

**🔬 Medical Tasks:**
- Reads PDF lab reports and extracts information
- Gives general medical advice with safety warnings
- Works with different AI models (OpenAI, Google Gemini, Ollama)

**🛠️ Smart Tools:**
- **Patient Contact Tool**: Saves patient requests for appointments and sends phone alerts
- **Safety Check Tool**: Catches bad or unsafe medical questions and alerts admins
- **Smart Decisions**: AI automatically chooses which tools to use during conversations

**📱 Alert System:**
- Sends instant notifications when tools are used
- Alerts for patient contacts and safety issues
- Manages notifications for medical work

## From Basic Chat to Agentic AI

**Basic LLM Chat** (Traditional):
- AI only talks and answers questions
- No real actions taken
- Limited to conversation only

**Agentic LLM** (This Codebase):
- AI can perform real tasks through JSON tools
- Takes actions like saving data and sending alerts
- Becomes an active assistant, not just a chat bot

## How It Works

This code shows examples of:
- **Multiple AI Models**: Easy switching between different AI services
- **Tool-Based AI**: AI that uses tools to do specific tasks
- **Medical Safety**: Checks for bad content and follows medical rules
- **Live Monitoring**: Sends alerts when things happen
- **Command Line App**: Interactive medical helper you can chat with

## Learning Examples

This project teaches how to build AI helpers using tools. Here are the two main tools:

**Tool 1: Patient Contact Saver**
- Gets patient requests for future appointments
- Sends alerts to system managers
- Saves contact info for later follow-up

**Tool 2: Safety Checker**
- Watches for bad or dangerous medical questions
- Flags questions that break safety rules
- Alerts managers about security issues
- Keeps AI safe and responsible in healthcare

## Getting Started

1. Install required packages: `pip install -r requirements.txt`
2. Create a `.env` file with your keys:
   ```
   OPENAI_API_KEY=your_openai_key
   GOOGLE_API_KEY=your_google_key  # Optional
   PUSHOVER_USER=your_pushover_user
   PUSHOVER_TOKEN=your_pushover_token
   ```
3. Add your lab report PDF file to the folder (or give the path)
4. Run: `python main.py --pdf your_lab_report.pdf`

## Run Options

```bash
python main.py --pdf path/to/your/lab_report.pdf
python main.py --pdf-path path/to/your/lab_report.pdf
python main.py --help  # See all options
```

**Default:** If no PDF given, it looks for `lab_report.pdf` in current folder.

## Main Features

- **Multiple AI Models**: Works with OpenAI, Google Gemini, and Ollama
- **Lab Report Reader**: Extracts text from PDF medical reports
- **Tool Actions**: Handles patient contacts and safety checks
- **Command Line Chat**: Interactive medical conversations
- **Phone Alerts**: Sends notifications when tools are used
- **Medical Safety**: Follows healthcare rules and warnings

## AI Models Supported

- **OpenAI GPT-4o-mini** (needs OPENAI_API_KEY)
- **Google Gemini 2.5 Flash** (needs GOOGLE_API_KEY)
- **Ollama Qwen3 1.7B** (needs local Ollama setup)

## Available Tools

- `record_patient_interest`: Saves patient contact info and sends alerts
- `record_unknown_medical_query`: Logs questions outside the system's scope
- `flag_inappropriate_content`: Flags unsafe or rule-breaking questions

### How Tools Work

![MedAI Tool Flow](figures/MedAI.png)

The picture above shows how tools work step by step:
1. **User Asks** → AI gets the question and sees available tools
2. **AI Chooses** → AI decides if it needs to use a tool
3. **Tool Runs** → Code functions do their job and give results
4. **AI Continues** → AI uses tool results to give final answer
5. **Alert Sent** → Phone notification sent when tools are used

## Chat Commands

- `/help` - See all available commands
- `/system` - Change the AI's instructions
- `/clear` - Reset the conversation
- `/quit` - Exit the chat

## How to Use

The app will check which AI models you have set up and let you choose one. It reads lab reports from PDF files and gives medical advice while keeping things safe and professional.
