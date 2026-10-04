# AI Ticket Summarizer

An AI-powered automation that reads IT support tickets, then summarizes, categorizes, and prioritizes each one using Azure OpenAI. Built as the first project in a portfolio focused on AI orchestration for Managed Services.

## The Problem

Service desk analysts spend time reading every incoming ticket, deciding what it's about, and judging how urgent it is. This manual triage is repetitive, slow, and inconsistent from one analyst to the next.

## What It Does

1. Reads support tickets from a CSV file
2. Sends each ticket to an Azure OpenAI model (gpt-5-mini) with a structured prompt
3. Receives back a one-sentence summary, a category, and a priority level as JSON
4. Saves the enriched results to a new CSV file

```
tickets.csv  -->  summarizer.py  -->  Azure OpenAI (gpt-5-mini)  -->  tickets_summarized.csv
```

## Results

- Triaged 20 sample tickets automatically in [X] seconds
- Manual triage typically takes 1–2 minutes per ticket, or roughly 20–40 minutes for the same batch
- Security incidents (phishing click) and customer-facing outages (website 500 error) were correctly flagged as Critical
- Routine requests (out-of-office setup, sticky keyboard) were correctly flagged as Low

| Ticket | AI Summary | Category | Priority |
|---|---|---|---|
| 1008 | Clicked a phishing email link requesting bank login verification | Security | Critical |
| 1012 | Customer-facing website is returning HTTP 500 errors | Software | Critical |
| 1003 | Third-floor printer is offline before a client meeting | Hardware | High |
| 1019 | User asks how to set up an out-of-office reply | Software | Low |

## Key Design Decisions

**Structured output.** The prompt requires JSON with fixed fields, and the API call uses JSON mode. This turns a conversational AI into a reliable component that code can act on.

**Rules for consistency.** A fixed category list and a written priority guide are included in the prompt. Without them, early testing returned invented categories like "Printer / Network" and overrated priorities.

**Safe failure.** If any single ticket fails, the script flags it as "NEEDS HUMAN REVIEW" and continues instead of crashing. This was verified during setup, when a configuration error caused every call to fail and the script still completed cleanly.

**Secrets handling.** The API key is read from an environment variable and is never stored in code or committed to the repository.

## Tech Stack

- Python 3
- Azure OpenAI in Microsoft Foundry (gpt-5-mini deployment)
- OpenAI Python SDK (Azure v1 endpoint)

## Setup

1. Create an Azure OpenAI or Microsoft Foundry resource and deploy a chat model.
2. Install the dependency:
   ```
   pip install -r requirements.txt
   ```
3. Set environment variables (PowerShell):
   ```
   $env:AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
   $env:AZURE_OPENAI_API_KEY="your-key"
   $env:AZURE_OPENAI_DEPLOYMENT="your-deployment-name"
   ```
4. Run:
   ```
   python summarizer.py
   ```

## Next Steps

- Route Critical and High tickets to a Microsoft Teams channel automatically
- Move the API key into Azure Key Vault
- Replace the CSV input with a live ticketing system connection
