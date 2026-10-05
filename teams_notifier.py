"""
Reusable helper for posting alert cards to a Microsoft Teams channel
through a Teams Workflows webhook.
"""

import requests

# Icon and Adaptive Card text color for each priority level
PRIORITY_STYLE = {
    "Critical": ("🔴", "attention"),
    "High": ("🟠", "warning"),
}


def _post_card(webhook_url, card_body):
    """Wrap Adaptive Card content in the message format Teams Workflows expects and send it."""
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": card_body,
                },
            }
        ],
    }
    response = requests.post(webhook_url, json=payload, timeout=15)
    response.raise_for_status()  # turns HTTP errors (like 400 or 404) into Python exceptions


def send_ticket_alert(webhook_url, ticket):
    """Post one ticket as an alert card."""
    icon, color = PRIORITY_STYLE.get(ticket["priority"], ("🔵", "default"))
    body = [
        {
            "type": "TextBlock",
            "text": f"{icon} {ticket['priority']} ticket #{ticket['ticket_id']}",
            "weight": "Bolder",
            "size": "Medium",
            "color": color,
            "wrap": True,
        },
        {"type": "TextBlock", "text": ticket["summary"], "wrap": True},
        {
            "type": "FactSet",
            "facts": [
                {"title": "Category", "value": ticket["category"]},
                {"title": "Assigned team", "value": ticket["assigned_team"]},
                {"title": "Submitted by", "value": ticket["submitted_by"]},
            ],
        },
        {
            "type": "TextBlock",
            "text": f"Original ticket: {ticket['description']}",
            "wrap": True,
            "isSubtle": True,
            "size": "Small",
        },
    ]
    _post_card(webhook_url, body)


def send_run_summary(webhook_url, total, counts):
    """Post one summary card at the end of a run."""
    facts = [{"title": level, "value": str(counts.get(level, 0))}
             for level in ["Critical", "High", "Medium", "Low", "Unknown"]]
    body = [
        {
            "type": "TextBlock",
            "text": f"✅ Ticket triage run complete: {total} tickets processed",
            "weight": "Bolder",
            "size": "Medium",
            "wrap": True,
        },
        {"type": "FactSet", "facts": facts},
    ]
    _post_card(webhook_url, body)