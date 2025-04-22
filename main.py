# main.py (project root)
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from backupManager.main import BrowserHistoryReader
from classifier.main import HistoryClassifier

# Configuration
BACKUP_DIR = Path(__file__).parent / "backupManager" / "history_backups"
DAYS_TO_ANALYZE = 7  # Analyze history from last 7 days


def setup_backup() -> bool:
    """Ensure backup directory exists and has recent data"""
    try:
        # Create backup directory if needed
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # Check if backups exist
        backups = list(BACKUP_DIR.glob("*_history.json"))
        if not backups:
            print("No backups found - creating new ones...")
            return True

        # Check backup freshness (max 1 day old)
        latest_backup = max(backups, key=lambda f: f.stat().st_mtime)
        backup_age = datetime.now() - datetime.fromtimestamp(latest_backup.stat().st_mtime)
        return backup_age.days >= 1

    except Exception as e:
        logging.error(f"Backup setup failed: {e}")
        return False


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Initialize components
    backup_creator = BrowserHistoryReader()
    classifier = HistoryClassifier()

    # Backup management
    needs_backup = setup_backup()
    if needs_backup:
        print("Creating new backups...")
        chrome_history = backup_creator.get_chrome_history()
        if chrome_history:
            backup_creator.backup_history(chrome_history, "Chrome")

        firefox_history = backup_creator.get_firefox_history()
        if firefox_history:
            backup_creator.backup_history(firefox_history, "Firefox")

    # Date range setup
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS_TO_ANALYZE)

    # Classification process
    print("\nClassifying history...")
    try:
        # Chrome classification
        chrome_results = classifier.classify_history("Chrome", start_date, end_date)
        classifier.save_classified_data(chrome_results, "Chrome")

        # Firefox classification
        firefox_results = classifier.classify_history("Firefox", start_date, end_date)
        classifier.save_classified_data(firefox_results, "Firefox")

        # Display summary
        print(f"\nClassification complete! Results saved to database.")
        print(f"Chrome entries processed: {len(chrome_results)}")
        print(f"Firefox entries processed: {len(firefox_results)}")

    except Exception as e:
        logging.error(f"Classification failed: {e}")
        return


if __name__ == "__main__":
    main()