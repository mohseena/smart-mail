# smart-mail

An AI-powered email automation tool that connects to Gmail, intelligently categorises emails using Claude API, and automatically cleans your inbox on a schedule.

## How It Works

smart-mail is built in three layers:

1. **Connector** — Authenticates with Gmail via OAuth 2.0 and fetches email metadata
2. **Intelligence** — Sends each email to Claude API which categorises it as `newsletter`, `promotion`, `spam`, `transactional`, or `personal` and suggests an action
3. **Cleaner** — Acts on Claude's decisions, moving flagged emails to trash and generating an audit report

## Tech Stack

- Python 3.10+
- Gmail API (Google Cloud)
- Claude API (Anthropic)
- httpx, google-auth, python-dotenv

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/mohseena/smart-mail.git
cd smart-mail
```

### 2. Create a virtual environment

```bash
virtualenv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Gmail API

- Go to [Google Cloud Console](https://console.cloud.google.com)
- Create a new project
- Enable the Gmail API
- Create OAuth 2.0 credentials (Desktop App)
- Download and save as `credentials.json` in the project root

### 5. Configure Anthropic API

- Get your API key from [console.anthropic.com](https://console.anthropic.com)
- Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your-api-key-here
```

### 6. Authenticate with Gmail

Run once to authenticate — a browser window will open:

```bash
python3 main.py
```

After logging in, `token.json` is saved and future runs skip this step.

## Usage

### Dry run (preview only — nothing is deleted)

```bash
python3 main.py
```

### Live run (moves flagged emails to trash)

```bash
python3 main.py --live
```

### JSON output (agent-native structured output)

```bash
python3 main.py --json
```

### Custom email limit (default: 200)

```bash
python3 main.py --live --limit=500
```

### Combine flags

```bash
python3 main.py --live --limit=200 --json
```

### Example output (human readable)

```
CLEANUP REPORT [LIVE]
============================================================
Total emails scanned : 10
Emails to trash      : 4
Emails to keep       : 6
Errors               : 0

--- TRASHED ---
  [promotion] Time to upgrade your sunscreen
  From: Nykaa <noreply@nykaa.com>
  Reason: Marketing email promoting skincare products

  [promotion] Guangzhou awaits
  From: IndiGo <mailers@marketing.goindigo.in>
  Reason: Airline marketing email promoting flight deals
```

### Example output (JSON mode)

```json
{
  "total": 10,
  "trashed": 4,
  "kept": 6,
  "errors": 0,
  "emails": [
    {
      "id": "18e4f2a1b3c",
      "from": "Nykaa <noreply@nykaa.com>",
      "subject": "Time to upgrade your sunscreen",
      "category": "promotion",
      "suggested_action": "unsubscribe_and_trash",
      "confidence": 0.9,
      "reason": "Marketing email promoting skincare products"
    }
  ]
}
```

## Automation

To run automatically every Sunday at 9pm, add this to your crontab (`crontab -e`):

```
0 21 * * 0 cd /path/to/smart-mail && source venv/bin/activate && python3 main.py --live --limit=200 >> logs/cleanup.log 2>&1
```

## Project Structure

```
smart-mail/
├── src/
│   ├── connector/
│   │   └── gmail.py          # Gmail authentication and operations
│   ├── intelligence/
│   │   └── categoriser.py    # Claude API integration and email categorisation
│   └── cli/
│       └── cleaner.py        # Cleanup logic and reporting
├── main.py                   # Entry point
├── requirements.txt          # Python dependencies
├── .env                      # API keys (not committed)
├── credentials.json          # Gmail OAuth credentials (not committed)
└── .gitignore
```

## Security

- OAuth credentials and API keys are never committed to the repository
- Emails are moved to trash, not permanently deleted — recoverable for 30 days
- Dry run mode available to preview decisions before executing
