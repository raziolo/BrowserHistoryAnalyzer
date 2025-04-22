# classifier.py
import json
import logging
import sqlite3
import time
from pathlib import Path
from pprint import pprint
from typing import List, Dict, Optional
from openai import OpenAI
from datetime import datetime
import app_settings
# AI model name from settings.py

logger = app_settings.LOGGER


class HistoryClassifier:
    def __init__(self, model_name: str = "local-model", base_url: str = "http://localhost:1234/v1"):
        self.client = OpenAI(base_url=base_url, api_key="not-needed")
        self.model_name = app_settings.AI_MODEL_NAME
        self.backup_dir = Path(__file__).resolve().parent.parent / "backupManager" / "history_backups"
        self.classified_dir = Path(__file__).resolve().parent / "classified"
        self._create_classified_dir()
        self._init_db()  # Add database initialization





    def _init_db(self):
        """Initialize SQLite database with classified entries table"""
        db_path = self.classified_dir / "classified_history.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                url TEXT,
                last_visit TEXT,
                title TEXT,
                visit_count INTEGER,
                category TEXT,
                browser TEXT,
                UNIQUE(url, last_visit)
            )
        ''')
        conn.commit()
        conn.close()

    def save_classified_data(self, results: List[Dict], browser: str) -> Optional[Path]:
        """Save classified results to SQLite database"""
        if not results:
            logger.warning("No results to save")
            return None

        db_path = self.classified_dir / "classified_history.db"
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            for entry in results:
                cursor.execute('''
                    INSERT OR IGNORE INTO history 
                    (url, last_visit, title, visit_count, category, browser)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    entry['url'],
                    entry['last_visit'],
                    entry['title'],
                    entry.get('visit_count', 0),
                    entry['category'],
                    browser.lower()
                ))

            conn.commit()
            logger.info(f"Saved classified data to {db_path}")
            return db_path
        except Exception as e:
            logger.error(f"Database save failed: {e}")
            return None
        finally:
            conn.close()

    def _create_classified_dir(self) -> bool:
        """Create classified data directory if needed"""
        try:
            self.classified_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create classified directory: {e}")
            return False


    def _load_latest_backup(self, browser: str) -> Optional[List[Dict]]:
        """Load most recent backup file for a browser"""
        try:
            backups = list(self.backup_dir.glob(f"{browser.lower()}_history.json"))
            if not backups:
                logger.warning(f"No backups found for {browser}")
                return None

            latest_backup = max(backups, key=lambda f: f.stat().st_mtime)
            with open(latest_backup, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Failed to load {browser} backup: {e}")
            return None

    def _generate_category(self, entry: Dict) -> Dict:
        """Classify a single history entry using local model"""
        prompt = f"""
            Classify this entry into one of: {', '.join(app_settings.CLASSIFICATION_PARAMETERS['categories'])}
            Entry: "{entry['title']}" ({entry['url']})
            If none apply, reply Other.
            Respond with exactly one category name.
            """

        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=app_settings.CLASSIFICATION_PARAMETERS['temperature'],
                max_tokens=app_settings.CLASSIFICATION_PARAMETERS['max_tokens']
            )

            category = response.choices[0].message.content.strip()
            return {**entry, "category": category}

        except Exception as e:
            logger.error(f"Classification failed for {entry['url']}: {e}")
            return {**entry, "category": "Classification Failed"}

    def classify_history(self, browser: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Classify history within date range with robust date handling"""
        history = self._load_latest_backup(browser)
        if not history:
            return []


        filtered = []
        for entry in history:
            # Validate date field
            if not entry.get('last_visit'):
                logger.warning(f"Skipping entry with missing date: {entry['url']}")
                continue

            try:
                entry_date = datetime.strptime(
                    entry['last_visit'],
                    "%Y-%m-%d %H:%M:%S"  # Match Chrome/Firefox format
                )
                if start_date <= entry_date <= end_date:
                    filtered.append(entry)
            except ValueError as e:
                logger.warning(f"Invalid date '{entry['last_visit']}' in {entry['url']}: {e}")

        # Rest of processing remains the same
        results = []
        for idx, entry in enumerate(filtered):
            continue
            classified_entry = self._generate_category(entry)
            results.append(classified_entry)
            if (idx + 1) % 5 == 0:
                time.sleep(1)

        return results

    def print_results(self, results: List[Dict], save_path: Optional[Path] = None):
        """Display classification results with save location"""
        if not results:
            print("No results to display")
            return

        print(f"\nClassification Results ({len(results)} entries)")
        if save_path:
            print(f"Saved to: {save_path}")

        for entry in results[:5]:  # Show first 5 entries
            print(f"\n[{entry['category']}] {entry['title']}")
            print(f"URL: {entry['url']}")
            print(f"Visits: {entry['visit_count']} | Last: {entry['last_visit']}")
            print("-" * 80)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    classifier = HistoryClassifier(
        model_name='gemma-3-4b-it', # granite-3.1-8b-instruct
        base_url='http://localhost:1234/v1'
    )

    print("Classifying Chrome History:")
    chrome_results = classifier.classify_history("Chrome")
    chrome_save_path = classifier.save_classified_data(chrome_results, "Chrome")
    classifier.print_results(chrome_results, chrome_save_path)

    print("\nClassifying Firefox History:")
    firefox_results = classifier.classify_history("Firefox")
    firefox_save_path = classifier.save_classified_data(firefox_results, "Firefox")
    classifier.print_results(firefox_results, firefox_save_path)