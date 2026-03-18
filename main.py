from src.connector.gmail import authenticate, fetch_emails
from src.intelligence.categoriser import categorise_email
from src.cli.cleaner import clean_inbox, print_report

def main():
    print("Connecting to Gmail...")
    service = authenticate()
    print("Connected.\n")

    print("Fetching last 10 emails...\n")
    emails = fetch_emails(service, limit=10)

    report = clean_inbox(service, emails, dry_run=False)
    print_report(report, dry_run=False)

if __name__ == "__main__":
    main()