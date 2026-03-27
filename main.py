import sys
import json
from src.connector.gmail import authenticate, fetch_emails
from src.intelligence.categoriser import categorise_email
from src.cli.cleaner import clean_inbox, print_report

def output_json(report):
    output = {
        'total': report['total'],
        'trashed': len(report['trashed']),
        'kept': len(report['kept']),
        'errors': len(report['errors']),
        'emails': []
    }

    for email in report['trashed'] + report['kept']:
        analysis = email.get('analysis', {})
        output['emails'].append({
            'id': email['id'],
            'from': email['from'],
            'subject': email['subject'],
            'category': analysis.get('category', 'unknown'),
            'suggested_action': analysis.get('suggested_action', 'unknown'),
            'confidence': analysis.get('confidence', 0),
            'reason': analysis.get('reason', '')
        })

    print(json.dumps(output, indent=2))

def main():
    json_mode = '--json' in sys.argv
    dry_run = '--live' not in sys.argv
    limit = 200
    for arg in sys.argv:
        if arg.startswith('--limit='):
            limit = int(arg.split('=')[1])

    print("Connecting to Gmail...", file=sys.stderr)
    service = authenticate()
    print("Connected.\n", file=sys.stderr)

    print("Fetching last 10 emails...\n", file=sys.stderr)
    emails = fetch_emails(service, limit=limit)

    report = clean_inbox(service, emails, dry_run=dry_run)

    if json_mode:
        output_json(report)
    else:
        print_report(report, dry_run=dry_run)

if __name__ == "__main__":
    main()