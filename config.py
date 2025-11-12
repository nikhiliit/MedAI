import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    PUSHOVER_USER = os.getenv("PUSHOVER_USER")
    PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
    PUSHOVER_URL = "https://api.pushover.net/1/messages.json"
