import requests
from config import Config

def send_pushover_notification(message):
    payload = {
        "user": Config.PUSHOVER_USER,
        "token": Config.PUSHOVER_TOKEN,
        "message": message
    }
    requests.post(Config.PUSHOVER_URL, data=payload)

def record_patient_interest(email, name="Not provided", medical_notes="Not provided"):
    message = f"Patient interest: {name} ({email}) - Notes: {medical_notes}"
    print(f"Tool called: record_patient_interest")
    send_pushover_notification(message)
    return {"recorded": "ok", "action": "patient_interest_recorded"}

def record_unknown_medical_query(query, reason="out_of_context"):
    message = f"Unknown medical query: {query} (Reason: {reason})"
    print(f"Tool called: record_unknown_medical_query")
    send_pushover_notification(message)
    return {"recorded": "ok", "action": "query_recorded"}

def flag_inappropriate_content(content, violation_type):
    message = f"Inappropriate content flagged: {violation_type} - {content[:100]}..."
    print(f"Tool called: flag_inappropriate_content")
    send_pushover_notification(message)
    return {"flagged": "ok", "action": "content_flagged"}

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
