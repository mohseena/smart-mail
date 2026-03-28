import json
from datetime import datetime
from src.connector.gmail import trash_email
from src.intelligence.categoriser import categorise_email

TRASH_CATEGORIES = ['promotion', 'spam', 'newsletter']
AUTO_TRASH_LABELS = [
    'SPAM',
    'CATEGORY_PROMOTIONS',
    'CATEGORY_SOCIAL'
]

def should_auto_trash(email):
    return any(label in email['label_ids'] for label in AUTO_TRASH_LABELS)

def clean_inbox(service, emails, dry_run=True):
    report = {
        'total': len(emails),
        'trashed': [],
        'kept': [],
        'errors': []
    }

    for email in emails:
        try:
            if should_auto_trash(email):
                email['analysis'] = {
                    'category': 'auto-filtered',
                    'intent': 'detected by gmail label',
                    'priority': 'low',
                    'suggested_action': 'trash',
                    'confidence': 1.0,
                    'reason': f"Auto-trashed based on Gmail label: {', '.join(email['label_ids'])}"
                }
                if not dry_run:
                    trash_email(service, email['id'])
                report['trashed'].append(email)
            else:
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