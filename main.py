#!/usr/bin/env python3
"""
This script provides a command-line interface for interacting with multiple LLMs
(OpenAI GPT, Google Gemini, and Ollama models) as a medical assistant.
"""

import os
import sys
import threading
import time
import argparse
from dotenv import load_dotenv
from pypdf import PdfReader
from llm_manager import LLMManager
from tools import TOOLS
from utils import show_processing_spinner, stop_spinner, prompt_model_selection

# Global variables for model selection and system prompt
llm_manager = None
current_model = None
current_system_prompt = ""
lab_report_content = ""

def load_lab_report(pdf_path: str = "lab_report.pdf") -> str:
    """Load and extract text from lab report PDF file."""
    try:
        reader = PdfReader(pdf_path)
        lab_report = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                lab_report += text
        print(f"✅ Lab report loaded from {pdf_path} ({len(lab_report)} characters)")
        return lab_report
    except FileNotFoundError:
        print(f"❌ Lab report file not found: {pdf_path}")
        return ""
    except Exception as e:
        print(f"❌ Error loading lab report: {e}")
        return ""

def create_medical_system_prompt(lab_report: str) -> str:
    """Create system prompt for medical assistant persona."""
    name = "Dr. AI"

    system_prompt = f"""You are acting as {name}, a skilled medical assistant and healthcare professional.
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
        {lab_report}

        Guidelines:
        - Never provide specific medical diagnoses
        - Always recommend consulting healthcare professionals for serious concerns

        If you don't have specific information about a particular test or result, use your record_unknown_medical_query tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to basic lab interpretation.

        If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_patient_interest tool.

        For dangerous or unethical requests about medications or self-treatment, use your flag_inappropriate_content tool immediately to flag violations.

        With this context, please assist users with understanding their lab results, explaining medical terminology, and providing general guidance about blood tests and medical diagnostics."""

    return system_prompt

def initialize_llm_manager(pdf_path: str = "lab_report.pdf"):
    """Initialize the LLM manager globally."""
    global llm_manager, current_model

    load_dotenv(override=True)

    llm_manager = LLMManager()
    available_models = llm_manager.get_available_model_names()

    if available_models:
        current_model = prompt_model_selection(available_models)
    else:
        print("❌ No models available")
        sys.exit(1)

    global lab_report_content, current_system_prompt
    lab_report_content = load_lab_report(pdf_path)
    if lab_report_content:
        current_system_prompt = create_medical_system_prompt(lab_report_content)
        print("✅ Medical assistant system prompt created")
    else:
        current_system_prompt = "You are a helpful medical assistant. Please ask me questions about lab reports and medical tests."
        print("⚠️ Using default system prompt (no lab report loaded)")

    print("🤖 LLM Manager Initialized")

def update_system_prompt(system_prompt: str):
    """Update the current system prompt."""
    global current_system_prompt
    current_system_prompt = system_prompt
    return f"System prompt updated! ({len(system_prompt)} chars)"

def chat(message, history=None):
    """Chat function for CLI interface."""
    global llm_manager, current_model, current_system_prompt

    if not message.strip():
        return ""

    if not llm_manager or not current_model:
        return "❌ No LLM available. Please check your setup."

    model_key = llm_manager.get_model_key_from_name(current_model)
    if not model_key:
        return f"❌ Model '{current_model}' not found."

    messages = []
    if current_system_prompt.strip():
        messages.append({"role": "system", "content": current_system_prompt})

    if history:
        for user_msg, bot_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": bot_msg})

    messages.append({"role": "user", "content": message})

    print(f"🤖 Sending {len(messages)} messages to {current_model} with {len(TOOLS)} tools")
    response = llm_manager.chat_with_model(model_key, messages, TOOLS)

    if response:
        return response
    else:
        return f"❌ Failed to get response from {current_model}. Please try again."

def cli_chat_interface(pdf_path: str = "lab_report.pdf"):
    """Run the CLI chat interface."""
    global llm_manager, current_model, current_system_prompt

    if not llm_manager:
        initialize_llm_manager(pdf_path)

    print(f"\n🩺 Medical LLM Analyzer - {current_model}")
    print("=" * 60)
    print("I'm Dr. AI, your medical assistant!")
    print("Ask me questions about blood reports, lab test results, and medical diagnostics.")
    print()
    print("Commands:")
    print("  /help     - Show this help")
    print("  /system   - Set system prompt")
    print("  /clear    - Clear conversation history")
    print("  /quit     - Exit the chat")
    print("=" * 60)

    conversation_history = []

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.startswith('/'):
                if user_input == '/quit':
                    print("👋 Goodbye!")
                    break
                elif user_input == '/help':
                    print("Commands:")
                    print("  /help     - Show this help")
                    print("  /system   - Set system prompt")
                    print("  /clear    - Clear conversation history")
                    print("  /quit     - Exit the chat")
                    continue
                elif user_input == '/clear':
                    conversation_history = []
                    print("🧹 Conversation history cleared.")
                    continue
                elif user_input == '/system':
                    new_prompt = input("Enter new system prompt: ").strip()
                    update_system_prompt(new_prompt)
                    print(f"✅ System prompt updated! ({len(new_prompt)} chars)")
                    continue
                else:
                    print("❌ Unknown command. Type /help for available commands.")
                    continue

            conversation_history.append({"role": "user", "content": user_input})

            spinner_thread = threading.Thread(target=show_processing_spinner, daemon=True)
            spinner_thread.start()

            try:
                response = chat(user_input, conversation_history)
            finally:
                stop_spinner()
                time.sleep(0.1)

            if response:
                print(f"🩺 Dr. AI: {response}")
                conversation_history.append({"role": "assistant", "content": response})
            else:
                print(f"\n❌ Failed to get response from {current_model}")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Medical LLM Analyzer - AI Medical Assistant")
    parser.add_argument(
        "--pdf",
        type=str,
        default="lab_report.pdf",
        help="Path to the lab report PDF file (default: lab_report.pdf)"
    )
    parser.add_argument(
        "--pdf-path",
        type=str,
        dest="pdf",
        help="Alias for --pdf"
    )

    args = parser.parse_args()

    try:
        cli_chat_interface(args.pdf)

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
