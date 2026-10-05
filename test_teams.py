"""Quick test: sends one simple message to your Teams channel."""

import os

import requests

url = os.environ.get("TEAMS_WEBHOOK_URL", "")
if not url:
    print("ERROR: Set TEAMS_WEBHOOK_URL first.")
else:
    payload = {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [{"type": "TextBlock", "text": "Hello from Python! 👋", "wrap": True}],
            },
        }],
    }
    response = requests.post(url, json=payload, timeout=15)
    print("Status code:", response.status_code)