#!/usr/bin/env python3
"""
MedAI - Medical AI Assistant Web App
Deployable on Hugging Face Spaces
Uses Google Gemini Flash model with tool calling
"""

import os
import json
import requests
from dotenv import load_dotenv
from pypdf import PdfReader
from openai import OpenAI
import gradio as gr

# Load environment variables
load_dotenv(override=True)

# Configuration
class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    PUSHOVER_USER = os.getenv("PUSHOVER_USER")
    PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
    PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

# Tool Functions
def send_pushover_notification(message):
    """Send notification via Pushover."""
    if Config.PUSHOVER_USER and Config.PUSHOVER_TOKEN:
        payload = {
            "user": Config.PUSHOVER_USER,
            "token": Config.PUSHOVER_TOKEN,
            "message": message
        }
        try:
            requests.post(Config.PUSHOVER_URL, data=payload)
        except Exception as e:
            print(f"Pushover notification failed: {e}")

def record_patient_interest(email, name="Not provided", medical_notes="Not provided"):
    """Record patient interest and send notification."""
    message = f"Patient interest: {name} ({email}) - Notes: {medical_notes}"
    print(f"Tool called: record_patient_interest")
    send_pushover_notification(message)
    return {"recorded": "ok", "action": "patient_interest_recorded"}

def record_unknown_medical_query(query, reason="out_of_context"):
    """Record unknown medical query and send notification."""
    message = f"Unknown medical query: {query} (Reason: {reason})"
    print(f"Tool called: record_unknown_medical_query")
    send_pushover_notification(message)
    return {"recorded": "ok", "action": "query_recorded"}

def flag_inappropriate_content(content, violation_type):
    """Flag inappropriate content and send notification."""
    message = f"Inappropriate content flagged: {violation_type} - {content[:100]}..."
    print(f"Tool called: flag_inappropriate_content")
    send_pushover_notification(message)
    return {"flagged": "ok", "action": "content_flagged"}

# Tool Definitions for Gemini
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "record_patient_interest",
            "description": "Record when a patient shows interest in medical services or consultation",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Patient's email address"},
                    "name": {"type": "string", "description": "Patient's name"},
                    "medical_notes": {"type": "string", "description": "Medical notes or concerns"}
                },
                "required": ["email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_unknown_medical_query",
            "description": "Record medical questions that cannot be answered due to lack of context or expertise",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The unanswered medical question"},
                    "reason": {"type": "string", "description": "Reason why it couldn't be answered"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "flag_inappropriate_content",
            "description": "Flag content that violates medical community guidelines",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The inappropriate content"},
                    "violation_type": {"type": "string", "description": "Type of violation"}
                },
                "required": ["content", "violation_type"]
            }
        }
    }
]

TOOL_FUNCTIONS = {
    "record_patient_interest": record_patient_interest,
    "record_unknown_medical_query": record_unknown_medical_query,
    "flag_inappropriate_content": flag_inappropriate_content
}

class MedAI:
    """Medical AI Assistant using Google Gemini Flash."""

    def __init__(self, pdf_file=None):
        """Initialize the Medical AI Assistant."""
        self.client = None
        self.lab_report_content = ""
        self.system_prompt = ""
        self.pdf_file = pdf_file
        self.client_initialized = False
        # Don't initialize client immediately - do it lazily
        self._load_lab_report()
        self._create_system_prompt()

    def _initialize_client(self):
        """Initialize Google Gemini client lazily."""
        if self.client_initialized:
            return

        if not Config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        try:
            self.client = OpenAI(
                api_key=Config.GOOGLE_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            self.client_initialized = True
            print("✅ Google Gemini client initialized")
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini client: {e}")

    def _load_lab_report(self):
        """Load lab report from PDF file."""
        try:
            if self.pdf_file:
                # Use uploaded PDF file
                reader = PdfReader(self.pdf_file)
                lab_report = ""
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        lab_report += text
                self.lab_report_content = lab_report
                print(f"✅ Lab report loaded from uploaded file ({len(lab_report)} characters)")
            else:
                # Try default file for HF Spaces
                pdf_path = "lab_report.pdf"
                if os.path.exists(pdf_path):
                    reader = PdfReader(pdf_path)
                    lab_report = ""
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            lab_report += text
                    self.lab_report_content = lab_report
                    print(f"✅ Lab report loaded from {pdf_path} ({len(lab_report)} characters)")
                else:
                    print("⚠️ No lab report available. Please upload a PDF file for analysis.")
                    self.lab_report_content = "No lab report available. Please upload a PDF file containing your lab results for personalized analysis."
        except Exception as e:
            print(f"❌ Error loading lab report: {e}")
            self.lab_report_content = f"Error loading lab report: {str(e)}. Please try uploading a valid PDF file."

    def _create_system_prompt(self):
        """Create the medical system prompt."""
        name = "Dr. AI"

        self.system_prompt = f"""You are acting as {name}, a skilled medical assistant and healthcare professional.
        You are answering questions on {name}'s medical analysis website,
        particularly questions related to blood reports, lab test results, medical diagnostics, and health analysis.

        Your responsibility is to represent {name} for interactions on the website as faithfully as possible,
        providing accurate, professional, and helpful explanations of lab results and medical information.

        You are given detailed lab report data from blood tests and medical examinations which you can use to answer questions.

        Be professional, accurate, and compassionate, as if talking to a patient or healthcare provider who needs to understand their lab results.
        Always explain medical terms in simple, understandable language while maintaining accuracy.
        If you don't have specific information about a particular test or result, say so clearly.

        Available actions:
        - Record patient interest when they want to be contacted
        - Record unknown queries that are outside your scope
        - Flag inappropriate content that violates medical guidelines

        ## Lab Report Data:
        {self.lab_report_content}

        Guidelines:
        - Never provide specific medical diagnoses
        - Always recommend consulting healthcare professionals for serious concerns

        If you don't have specific information about a particular test or result, use your record_unknown_medical_query tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to basic lab interpretation.

        If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_patient_interest tool.

        For dangerous or unethical requests about medications or self-treatment, use your flag_inappropriate_content tool immediately to flag violations.

        With this context, please assist users with understanding their lab results, explaining medical terminology, and providing general guidance about blood tests and medical diagnostics."""

    def handle_tool_calls(self, tool_calls):
        """Handle tool function calls."""
        results = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if function_name in TOOL_FUNCTIONS:
                result = TOOL_FUNCTIONS[function_name](**arguments)
                results.append({
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id
                })
        return results

    def chat(self, message, history):
        """Main chat function for Gradio interface."""
        if not message.strip():
            return ""

        # Try to initialize client if not done yet
        try:
            self._initialize_client()
        except ValueError as e:
            if "GOOGLE_API_KEY" in str(e):
                return "❌ **Configuration Required**\n\nTo use this medical AI assistant, you need to set the GOOGLE_API_KEY environment variable.\n\n**For HF Spaces**: The API key should be configured in Space secrets.\n\n**For local development**: Set the GOOGLE_API_KEY environment variable."
            else:
                return f"❌ Configuration error: {str(e)}"

        if not self.client:
            return "❌ AI assistant failed to initialize. Please check your configuration."

        # Build messages from history
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation history
        if history:
            for user_msg, bot_msg in history:
                messages.append({"role": "user", "content": user_msg})
                messages.append({"role": "assistant", "content": bot_msg})

        # Add current message
        messages.append({"role": "user", "content": message})

        try:
            # First API call with tools
            response = self.client.chat.completions.create(
                model="gemini-2.5-flash",
                messages=messages,
                tools=TOOLS
            )

            # Check if tools were called
            if response.choices[0].finish_reason == "tool_calls":
                tool_calls = response.choices[0].message.tool_calls
                tool_results = self.handle_tool_calls(tool_calls)

                # Add tool call and results to messages
                messages.append(response.choices[0].message)
                messages.extend(tool_results)

                # Get final response
                final_response = self.client.chat.completions.create(
                    model="gemini-2.5-flash",
                    messages=messages
                )
                return final_response.choices[0].message.content
            else:
                # No tools called, return direct response
                content = response.choices[0].message.content
                if content:
                    return content
                else:
                    return "I apologize, but I couldn't generate a response. Please try rephrasing your question."

        except Exception as e:
            error_msg = f"❌ Error communicating with AI: {str(e)}"
            print(error_msg)
            return error_msg

# Global variable to store the current MedAI instance
current_medai = None

def process_pdf_upload(pdf_file):
    """Process uploaded PDF and create new MedAI instance."""
    global current_medai
    try:
        if pdf_file is None:
            return "❌ Please upload a PDF file first."

        # Check if we have API key configured
        if not Config.GOOGLE_API_KEY:
            return "❌ GOOGLE_API_KEY not configured. Please set the API key in environment variables or HF Space secrets to enable AI functionality."

        current_medai = MedAI(pdf_file)
        return f"✅ PDF processed successfully! ({len(current_medai.lab_report_content)} characters extracted)\n\nYou can now ask me questions about your lab results."
    except Exception as e:
        return f"❌ Error processing PDF: {str(e)}. Please ensure it's a valid PDF file."

def chat_with_medai(message, history):
    """Chat function that uses the current MedAI instance."""
    global current_medai

    # Check if API key is configured
    if not Config.GOOGLE_API_KEY:
        return "❌ **API Key Required**\n\nTo use this medical AI assistant, you need to configure the GOOGLE_API_KEY:\n\n• **HF Spaces**: Set it in Space secrets\n• **Local**: Set GOOGLE_API_KEY environment variable\n\nThe PDF upload will work, but AI responses require the API key."

    if current_medai is None:
        return "Please upload a lab report PDF first to start analyzing your results."

    return current_medai.chat(message, history)

def create_demo():
    """Create and return the Gradio demo."""
    global current_medai

    try:
        # Try to initialize MedAI, but don't fail if API key is missing
        try:
            current_medai = MedAI()
            print("🤖 MedAI initialized successfully")
            initialization_success = True
        except ValueError as e:
            if "GOOGLE_API_KEY" in str(e):
                print("⚠️ GOOGLE_API_KEY not configured - app will show configuration message")
                current_medai = None
                initialization_success = False
            else:
                print(f"❌ Failed to initialize MedAI: {e}")
                current_medai = None
                initialization_success = False

        # Create Gradio interface with file upload
        with gr.Blocks(title="🩺 MedAI - Medical AI Assistant", theme="soft") as interface:

            gr.Markdown("# 🩺 MedAI - Medical AI Assistant")
            gr.Markdown("""
            **Welcome to MedAI!** Your AI medical assistant for understanding lab reports and medical information.

            **⚠️ Important Medical Disclaimer:**
            - This AI provides general information only
            - Never provides specific medical diagnoses
            - Always consult healthcare professionals for medical concerns
            - Not a substitute for professional medical advice
            """)

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📄 Upload Lab Report")
                    pdf_upload = gr.File(
                        label="Upload your lab report PDF",
                        file_types=[".pdf"],
                        type="filepath"
                    )
                    upload_status = gr.Textbox(
                        label="Upload Status",
                        interactive=False,
                        value="Please upload a PDF file to begin analysis." if initialization_success else "⚠️ API key not configured. Configure GOOGLE_API_KEY to enable AI responses."
                    )
                    upload_btn = gr.Button("Process PDF", variant="primary")

                with gr.Column(scale=2):
                    gr.Markdown("### 💬 Chat with Dr. AI")
                    gr.Markdown("""
                    **Ask me about:**
                    - Blood test results and what they mean
                    - Medical terminology explanations
                    - General health information
                    - Lab report analysis

                    **I can also:**
                    - Record your contact information if you want to be contacted
                    - Flag inappropriate content for safety
                    - Notify medical staff about important queries
                    """)

                    chatbot = gr.Chatbot(
                        type="messages",
                        examples=[
                            "What does a high hemoglobin level mean?",
                            "Can you explain my cholesterol results?",
                            "What are normal blood sugar ranges?",
                            "How do I interpret liver function tests?"
                        ]
                    )
                    msg = gr.Textbox(
                        placeholder="Ask me about your lab results...",
                        show_label=False
                    )
                    clear = gr.Button("Clear Chat")

            # Event handlers
            upload_btn.click(
                process_pdf_upload,
                inputs=[pdf_upload],
                outputs=[upload_status]
            )

            msg.submit(
                chat_with_medai,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            )

            clear.click(
                lambda: ([], ""),
                outputs=[chatbot, msg],
                queue=False
            )

        return interface

    except Exception as e:
        print(f"❌ Failed to initialize MedAI: {e}")

        # Fallback interface for errors
        def error_chat(message, history):
            return f"❌ MedAI is not available due to configuration issues: {str(e)}\n\nPlease check that:\n- GOOGLE_API_KEY is set\n- Try uploading a lab report PDF for analysis"

        return gr.ChatInterface(
            fn=error_chat,
            type="messages",
            title="🩺 MedAI - Configuration Error",
            description="MedAI could not be initialized. Please check configuration."
        )

if __name__ == "__main__":
    # Create and launch the Gradio app
    demo = create_demo()
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", 7860)),
        show_error=True,
        share=False  # Disable public sharing for medical app
    )
