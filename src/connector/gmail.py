import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def authenticate():
    creds = None
    token_path = os.path.join(BASE_DIR, 'token.json')
    credentials_path = os.path.join(BASE_DIR, 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=8080, open_browser=False)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def fetch_emails(service, limit=20):
    results = service.users().messages().list(
        userId='me',
        maxResults=limit
    ).execute()

    messages = results.get('messages', [])
    emails = []

    for msg in messages:
        full_msg = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()

        headers = full_msg.get('payload', {}).get('headers', [])
        header_map = {h['name']: h['value'] for h in headers}

        emails.append({
            'id': msg['id'],
            'from': header_map.get('From', 'Unknown'),
            'subject': header_map.get('Subject', 'No Subject'),
            'date': header_map.get('Date', 'Unknown'),
            'snippet': full_msg.get('snippet', ''),
            'label_ids': full_msg.get('labelIds', [])
        })

    return emails

def trash_email(service, email_id):
    service.users().messages().trash(
        userId='me',
        id=email_id
    ).execute()
    return True

