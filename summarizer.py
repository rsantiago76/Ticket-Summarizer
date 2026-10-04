"""
Project 1: AI Ticket Summarizer
Reads IT support tickets from a CSV, asks an AI model to summarize and
classify each one, and saves the results to a new CSV.
"""

import csv
import json
import os

from openai import OpenAI

INPUT_FILE = "tickets.csv"
OUTPUT_FILE = "tickets_summarized.csv"

# These come from your Azure resource (see setup steps). Never hard-code the key.
AZURE_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")      # e.g. https://my-resource.openai.azure.com
AZURE_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")        # the name YOU gave your model deployment

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
        response_format={"type": "json_object"},  # asks the model to return valid JSON
    )
    text = response.choices[0].message.content.strip()
    # Just in case the model wraps JSON in ```json fences; strip them just in case.
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def save_results(path, rows):
    """Write the analyzed tickets to a new CSV file."""
    fieldnames = ["ticket_id", "submitted_by", "description", "summary", "category", "priority"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if not (AZURE_ENDPOINT and AZURE_API_KEY and DEPLOYMENT):
        print("ERROR: Set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY and AZURE_OPENAI_DEPLOYMENT first.")
        return

    client = OpenAI(
        base_url=AZURE_ENDPOINT.rstrip("/") + "/openai/v1/",
        api_key=AZURE_API_KEY,
    )
    tickets = read_tickets(INPUT_FILE)
    print(f"Loaded {len(tickets)} tickets.\n")

    results = []
    for ticket in tickets:
        try:
            analysis = analyze_ticket(client, ticket["description"])
        except Exception as e:
            # Don't let one bad ticket stop the whole run; flag it for a human.
            print(f"[{ticket['ticket_id']}] FAILED: {e}")
            analysis = {"summary": "NEEDS HUMAN REVIEW", "category": "Unknown", "priority": "Unknown"}

        row = {**ticket, **analysis}
        results.append(row)
        print(f"[{row['ticket_id']}] {row['priority']:<8} {row['category']:<9} {row['summary']}")

    save_results(OUTPUT_FILE, results)
    print(f"\nDone! Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
