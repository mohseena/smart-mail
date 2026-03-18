import os
import json
import httpx
import certifi
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    http_client=httpx.Client(verify=False)
)

SYSTEM_PROMPT = """
You are an email categorisation assistant.
Given email metadata, you must respond with ONLY a JSON object — no explanation, no preamble.

Categories:
- newsletter: bulk sent, has unsubscribe link, informational content
- promotion: sales, offers, discounts, marketing
- spam: unsolicited, suspicious sender, irrelevant
- transactional: receipts, OTPs, order confirmations, bank alerts
- personal: real person sending a direct message

Respond with exactly this structure:
{
  "category": "newsletter|promotion|spam|transactional|personal",
  "intent": "one short phrase describing what the email wants",
  "priority": "high|medium|low",
  "suggested_action": "keep|trash|unsubscribe_and_trash",
  "confidence": 0.0 to 1.0,
  "reason": "one line explanation"
}
"""

def categorise_email(email):
    prompt = f"""
From: {email['from']}
Subject: {email['subject']}
Date: {email['date']}
Snippet: {email['snippet']}
Labels: {', '.join(email['label_ids'])}

Categorise this email.
"""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    result = response.content[0].text
    return json.loads(result)