from datetime import datetime, timezone
from src.connector.gmail import trash_email
from src.intelligence.categoriser import categorise_email

AUTO_TRASH_LABELS = [
    'SPAM',
    'CATEGORY_PROMOTIONS',
    'CATEGORY_SOCIAL'
]


def should_auto_trash(email: dict) -> bool:
    return any(label in email.get('label_ids', []) for label in AUTO_TRASH_LABELS)


def _matched_labels(email: dict) -> list[str]:
    """Return only the label_ids that triggered auto-trash."""
    return [label for label in email.get('label_ids', []) if label in AUTO_TRASH_LABELS]


def clean_inbox(service, emails: list, dry_run: bool = True) -> dict:
    report = {
        'run_at': datetime.now(timezone.utc).isoformat(),
        'total': len(emails),
        'trashed': [],
        'kept': [],
        'errors': []
    }

    for email in emails:
        try:
            if should_auto_trash(email):
                matched = _matched_labels(email)
                email['analysis'] = {
                    'category': 'auto-filtered',
                    'intent': 'detected by gmail label',
                    'priority': 'low',
                    'suggested_action': 'trash',
                    'confidence': 1.0,
                    'reason': f"Auto-trashed based on Gmail label: {', '.join(matched)}"
                }
                if not dry_run:
                    trash_email(service, email['id'])
                report['trashed'].append(email)

            else:
                result = categorise_email(email)

                if result is None:
                    report['errors'].append({
                        'email': email,
                        'error': 'categorise_email returned None — API failure or unparseable response, check logs'
                    })
                    continue

                email['analysis'] = result

                if result['suggested_action'] == 'trash':
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


def print_report(report: dict, dry_run: bool = True) -> None:
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"\n{'='*60}")
    print(f"CLEANUP REPORT [{mode}]  —  {report.get('run_at', 'unknown time')}")
    print(f"{'='*60}")
    print(f"Total emails scanned : {report['total']}")
    print(f"Emails to trash      : {len(report['trashed'])}")
    print(f"Emails to keep       : {len(report['kept'])}")
    print(f"Errors               : {len(report['errors'])}")

    print(f"\n--- TRASHED ({len(report['trashed'])}) ---")
    for email in report['trashed']:
        analysis = email.get('analysis', {})
        confidence = analysis.get('confidence', 0.0)
        print(f"  [{analysis.get('category', 'unknown')}] {email.get('subject', '(no subject)')[:50]}")
        print(f"  From    : {email.get('from', 'unknown')}")
        print(f"  Reason  : {analysis.get('reason', 'n/a')}")
        print(f"  Action  : {analysis.get('suggested_action', 'n/a')}  |  confidence: {confidence:.2f}")
        print()

    print(f"\n--- KEPT ({len(report['kept'])}) ---")
    for email in report['kept']:
        analysis = email.get('analysis', {})
        confidence = analysis.get('confidence', 0.0)
        print(f"  [{analysis.get('category', 'unknown')}] {email.get('subject', '(no subject)')[:50]}")
        print(f"  From    : {email.get('from', 'unknown')}")
        print(f"  Reason  : {analysis.get('reason', 'n/a')}")
        print(f"  Action  : {analysis.get('suggested_action', 'n/a')}  |  confidence: {confidence:.2f}")
        print()

    if report['errors']:
        print(f"\n--- ERRORS ({len(report['errors'])}) ---")
        for err in report['errors']:
            subject = err['email'].get('subject', '(no subject)')
            print(f"  {subject} → {err['error']}")