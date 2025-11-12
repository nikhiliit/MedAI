import json
import os
import requests
from openai import OpenAI
from typing import Optional, Dict, Any, List
from config import Config
from tools import TOOL_FUNCTIONS

class LLMManager:
    def __init__(self):
        self.openai_key = Config.OPENAI_API_KEY
        self.google_key = Config.GOOGLE_API_KEY
        self.ollama_available = self._check_ollama()
        self.available_models = self._initialize_clients()

    def _check_ollama(self) -> bool:
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def _initialize_clients(self) -> Dict[str, Any]:
        available = {}

        if self.openai_key:
            try:
                client = OpenAI(api_key=self.openai_key)
                available["openai"] = {
                    "client": client,
                    "model": "gpt-4o-mini",
                    "name": "OpenAI GPT-4o-mini"
                }
                print("✅ OpenAI client initialized")
            except Exception as e:
                print(f"❌ Failed to initialize OpenAI: {e}")

        if self.google_key:
            try:
                client = OpenAI(
                    api_key=self.google_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                )
                available["google"] = {
                    "client": client,
                    "model": "gemini-2.5-flash",
                    "name": "Google Gemini 2.5 Flash"
                }
                print("✅ Google Gemini client initialized")
            except Exception as e:
                print(f"❌ Failed to initialize Google Gemini: {e}")

        if self.ollama_available:
            try:
                client = OpenAI(
                    base_url='http://localhost:11434/v1',
                    api_key='ollama'
                )
                available["ollama"] = {
                    "client": client,
                    "model": "qwen3:1.7b",
                    "name": "Ollama Qwen3 1.7B"
                }
                print("✅ Ollama client initialized")
            except Exception as e:
                print(f"❌ Failed to initialize Ollama: {e}")

        if not available:
            print("❌ No LLM clients could be initialized.")
            return {}

        return available

    def handle_tool_calls(self, tool_calls):
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

    def chat_with_model(self, model_key: str, messages: List[Dict[str, str]], tools=None) -> Optional[str]:
        if model_key not in self.available_models:
            return None

        model_info = self.available_models[model_key]
        client = model_info["client"]
        model = model_info["model"]

        try:
            if tools:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools
                )

                if response.choices[0].finish_reason == "tool_calls":
                    tool_calls = response.choices[0].message.tool_calls
                    tool_results = self.handle_tool_calls(tool_calls)

                    messages.append(response.choices[0].message)
                    messages.extend(tool_results)

                    final_response = client.chat.completions.create(
                        model=model,
                        messages=messages
                    )
                    return final_response.choices[0].message.content
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages
                )

            message_obj = response.choices[0].message
            content = message_obj.content

            if not content and getattr(message_obj, 'reasoning', None):
                content = message_obj.reasoning

            return content if content else None
        except Exception as e:
            print(f"❌ Error with {model_info['name']}: {e}")
            return None

    def get_available_model_names(self) -> List[str]:
        return [info["name"] for info in self.available_models.values()]

    def get_model_key_from_name(self, display_name: str) -> Optional[str]:
        for key, info in self.available_models.items():
            if info["name"] == display_name:
                return key
        return None
