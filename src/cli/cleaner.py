import json
from datetime import datetime
from src.connector.gmail import trash_email
from src.intelligence.categoriser import categorise_email

TRASH_CATEGORIES = ['promotion', 'spam', 'newsletter']
def clean_inbox(service, emails, dry_run=True):
    report = {
        'total': len(emails),
        'trashed': [],
        'kept': [],
        'errors': []
    }

    for email in emails:
        try:
            result = categorise_email(email)
            email['analysis'] = result

            if result['suggested_action'] in ['trash', 'unsubscribe_and_trash']:
                if not dry_run:
                    trash_email(service, email['id'])
                report['trashed'].append(email)
            else:
                report['kept'].append(email)

        except Exception as e:
            report['errors'].append({
                'email': email,
                'error': str(e)
            })

    return report

def print_report(report, dry_run=True):
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"\n{'='*60}")
    print(f"CLEANUP REPORT [{mode}]")
    print(f"{'='*60}")
    print(f"Total emails scanned : {report['total']}")
    print(f"Emails to trash      : {len(report['trashed'])}")
    print(f"Emails to keep       : {len(report['kept'])}")
    print(f"Errors               : {len(report['errors'])}")
    print(f"\n--- TRASHED ---")
    for email in report['trashed']:
        analysis = email['analysis']
        print(f"  [{analysis['category']}] {email['subject'][:50]}")
        print(f"  From: {email['from']}")
        print(f"  Reason: {analysis['reason']}")
        print()
    if report['errors']:
        print(f"\n--- ERRORS ---")
        for err in report['errors']:
            print(f"  {err['email']['subject']} → {err['error']}")