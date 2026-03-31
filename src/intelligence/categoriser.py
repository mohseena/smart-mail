import os
import json
import httpx
import logging
import anthropic
from anthropic import Anthropic
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)

load_dotenv()

logger = logging.getLogger(__name__)

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

For suggested_action, use these guidelines:
- Newsletters from professional or utility sources (job boards, Leetcode, LinkedIn, GitHub release notes, developer tools) → keep
- Newsletters from commercial brands (retail, beauty, fashion, travel, food delivery) → trash, even if the content looks educational or informational. Sender intent is commercial regardless of content format.
- Release notes: keep only if the sender is a developer tool, API, or technical product. Marketing emails disguised as product updates → trash.
- Promotions and spam → trash

Respond with exactly this structure:
{
  "category": "newsletter|promotion|spam|transactional|personal",
  "intent": "one short phrase describing what the email wants",
  "priority": "high|medium|low",
  "suggested_action": "keep|trash",
  "confidence": 0.0 to 1.0,
  "reason": "one line explanation"
}
"""


# ---------------------------------------------------------------------------
# Core API call — decorated with retry
# ---------------------------------------------------------------------------

@retry(
    retry=retry_if_exception_type((
        anthropic.APIConnectionError,  # network-level failure
        anthropic.APITimeoutError,     # request timed out
        anthropic.InternalServerError, # 5xx from Anthropic
    )),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),  # 2s → 4s → 8s
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def _call_claude(prompt: str) -> str:
    """
    Single attempt to call the Anthropic SDK.
    Returns the raw text response. Raises anthropic exceptions on failure
    so tenacity can decide whether to retry.
    """
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def categorise_email(email: dict) -> dict | None:
    """
    Categorise a single email using Claude.

    Returns a dict on success, or None if the API call fails after retries
    or returns unparseable output — so the caller can skip gracefully.
    """
    prompt = f"""
From: {email.get('from', 'unknown')}
Subject: {email.get('subject', '(no subject)')}
Date: {email.get('date', 'unknown')}
Snippet: {email.get('snippet', '')}
Labels: {', '.join(email.get('label_ids', []))}

Categorise this email.
"""

    try:
        raw = _call_claude(prompt)

    except RetryError as exc:
        original = exc.last_attempt.exception()
        logger.error(
            "Claude API failed after 3 attempts for '%s' | %s: %s",
            email.get('subject', '(no subject)'),
            type(original).__name__,
            original,
        )
        return None

    except anthropic.AuthenticationError as exc:
        # Bad API key — retrying won't help, fail loudly
        logger.error("Authentication failed — check ANTHROPIC_API_KEY: %s", exc)
        return None

    except anthropic.BadRequestError as exc:
        # Prompt was rejected (e.g. policy violation) — not retryable
        logger.error(
            "Bad request for email '%s': %s",
            email.get('subject', '(no subject)'),
            exc,
        )
        return None

    except Exception as exc:
        logger.error(
            "Unexpected error categorising '%s': %s: %s",
            email.get('subject', '(no subject)'),
            type(exc).__name__,
            exc,
        )
        return None

    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        logger.error(
            "Failed to parse Claude response for '%s': %s | raw: %s",
            email.get('subject', '(no subject)'),
            exc,
            raw,
        )
        return None