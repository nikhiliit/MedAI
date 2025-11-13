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

    def __init__(self):
        """Initialize the Medical AI Assistant."""
        self.client = None
        self.lab_report_content = ""
        self.system_prompt = ""
        self._initialize_client()
        self._load_lab_report()
        self._create_system_prompt()

    def _initialize_client(self):
        """Initialize Google Gemini client."""
        if not Config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        try:
            self.client = OpenAI(
                api_key=Config.GOOGLE_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            print("✅ Google Gemini client initialized")
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini client: {e}")

    def _load_lab_report(self):
        """Load lab report from PDF file."""
        pdf_path = "lab_report.pdf"  # Default filename for HF Spaces

        try:
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
                print(f"⚠️ Lab report file not found: {pdf_path}")
                self.lab_report_content = "No lab report available. Please upload a lab_report.pdf file."
        except Exception as e:
            print(f"❌ Error loading lab report: {e}")
            self.lab_report_content = "Error loading lab report."

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

        if not self.client:
            return "❌ AI assistant is not properly configured. Please check API keys."

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

def create_demo():
    """Create and return the Gradio demo."""
    try:
        medai = MedAI()
        print("🤖 MedAI initialized successfully")

        # Create Gradio interface
        interface = gr.ChatInterface(
            fn=medai.chat,
            type="messages",
            title="🩺 MedAI - Medical AI Assistant",
            description="""
            **Welcome to MedAI!** Your AI medical assistant for understanding lab reports and medical information.

            **⚠️ Important Medical Disclaimer:**
            - This AI provides general information only
            - Never provides specific medical diagnoses
            - Always consult healthcare professionals for medical concerns
            - Not a substitute for professional medical advice

            **Ask me about:**
            - Blood test results and what they mean
            - Medical terminology explanations
            - General health information
            - Lab report analysis

            **I can also:**
            - Record your contact information if you want to be contacted
            - Flag inappropriate content for safety
            - Notify medical staff about important queries
            """,
            theme="soft",
            examples=[
                "What does a high hemoglobin level mean?",
                "Can you explain my cholesterol results?",
                "What are normal blood sugar ranges?",
                "How do I interpret liver function tests?"
            ]
        )

        return interface

    except Exception as e:
        print(f"❌ Failed to initialize MedAI: {e}")

        # Fallback interface for errors
        def error_chat(message, history):
            return f"❌ MedAI is not available due to configuration issues: {str(e)}\n\nPlease check that:\n- GOOGLE_API_KEY is set\n- lab_report.pdf exists (optional)"

        return gr.ChatInterface(
            fn=error_chat,
            title="🩺 MedAI - Configuration Error",
            description="MedAI could not be initialized. Please check configuration."
        )

if __name__ == "__main__":
    # Create and launch the Gradio app
    demo = create_demo()
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", 7860)),
        show_error=True
    )
