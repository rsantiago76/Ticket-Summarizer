"""
Project 2: AI Ticket Summarizer with Teams Alerts
Reads IT support tickets from a CSV, asks an AI model to summarize and
classify each one, assigns it to a team, saves the results to a new CSV,
and posts High and Critical tickets to a Microsoft Teams channel.
"""

import csv
import json
import os
import time
from collections import Counter

from openai import OpenAI

from teams_notifier import send_run_summary, send_ticket_alert

INPUT_FILE = "tickets.csv"
OUTPUT_FILE = "tickets_summarized.csv"

# These come from environment variables. Never hard-code keys or webhook URLs.
AZURE_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")
TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL", "")  # optional

# Which priorities trigger a Teams alert
ALERT_PRIORITIES = {"Critical", "High"}

# Routing rules: which team owns each category
TEAM_ROUTING = {
    "Network": "Network Team",
    "Security": "Security Team",
    "Access": "Identity & Access Team",
    "Hardware": "Desktop Support",
    "Software": "Application Support",
    "Request": "Service Desk",
    "Other": "Service Desk",
}

PROMPT_TEMPLATE = """You are an IT service desk analyst. Analyze this support ticket.

Ticket: {description}

Respond with ONLY a JSON object, no other text, in exactly this format:
{{
  "summary": "one short sentence describing the issue",
  "category": "one of: Hardware, Software, Network, Access, Security, Request, Other",
  "priority": "one of: Low, Medium, High, Critical"
}}

Priority guide:
- Critical: security incident, outage affecting customers or many users
- High: a team or business-critical task is blocked
- Medium: one user is blocked but has a workaround or it is time-sensitive
- Low: minor annoyance, how-to question, or routine request"""


def read_tickets(path):
    """Read tickets from a CSV file and return a list of dictionaries."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def analyze_ticket(client, description):
    """Send one ticket to the AI and return its parsed JSON answer."""
    response = client.chat.completions.create(
        model=DEPLOYMENT,  # in Azure, "model" means your deployment name
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(description=description)}],
        response_format={"type": "json_object"},
    )
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def assign_team(category):
    """Look up the owning team; anything unexpected goes to the Service Desk."""
    return TEAM_ROUTING.get(category, "Service Desk")


def save_results(path, rows):
    """Write the analyzed tickets to a new CSV file."""
    fieldnames = ["ticket_id", "submitted_by", "description",
                  "summary", "category", "priority", "assigned_team"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if not (AZURE_ENDPOINT and AZURE_API_KEY and DEPLOYMENT):
        print("ERROR: Set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY and AZURE_OPENAI_DEPLOYMENT first.")
        return

    if not TEAMS_WEBHOOK_URL:
        print("NOTE: TEAMS_WEBHOOK_URL is not set, so no Teams alerts will be sent.\n")

    client = OpenAI(
        base_url=AZURE_ENDPOINT.rstrip("/").removesuffix("/openai/v1") + "/openai/v1/",
        api_key=AZURE_API_KEY,
    )
    tickets = read_tickets(INPUT_FILE)
    print(f"Loaded {len(tickets)} tickets.\n")

    results = []
    alerts_sent = 0
    for ticket in tickets:
        try:
            analysis = analyze_ticket(client, ticket["description"])
        except Exception as e:
            print(f"[{ticket['ticket_id']}] FAILED: {e}")
            analysis = {"summary": "NEEDS HUMAN REVIEW", "category": "Unknown", "priority": "Unknown"}

        row = {**ticket, **analysis}
        row["assigned_team"] = assign_team(row["category"])
        results.append(row)
        print(f"[{row['ticket_id']}] {row['priority']:<8} {row['category']:<9} -> {row['assigned_team']}")

        if TEAMS_WEBHOOK_URL and row["priority"] in ALERT_PRIORITIES:
            try:
                send_ticket_alert(TEAMS_WEBHOOK_URL, row)
                alerts_sent += 1
                print("           Teams alert sent")
                time.sleep(1)  # small pause so we don't flood the channel
            except Exception as e:
                # A Teams problem should never stop ticket processing.
                print(f"           Teams alert FAILED: {e}")

    save_results(OUTPUT_FILE, results)

    counts = Counter(r["priority"] for r in results)
    if TEAMS_WEBHOOK_URL:
        try:
            send_run_summary(TEAMS_WEBHOOK_URL, len(results), counts)
        except Exception as e:
            print(f"Teams summary FAILED: {e}")

    print(f"\nDone! Results saved to {OUTPUT_FILE}")
    print(f"Teams alerts sent: {alerts_sent}")


if __name__ == "__main__":
    main()