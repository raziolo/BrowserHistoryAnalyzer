# classifier.py
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Optional
from openai import OpenAI
from datetime import datetime
from HistoryApp import app_settings
from frontend.models import App_Settings

# AI model name from settings.py

logger = app_settings.LOGGER


class HistoryClassifier:
    def __init__(self, model_name: str = "local-model", base_url: str = "http://localhost:1234/v1"):
        self.client = OpenAI(base_url=base_url, api_key="not-needed")
        self.model_name = App_Settings.objects.get(name='current_model').value
        self.model_thinking = False
        self.backup_dir = app_settings.BACKUP_DIR
        self.status = {}
        self.temperature = App_Settings.objects.get(name='temperature').value
        self.max_tokens = App_Settings.objects.get(name='max_tokens').value
        self.current_categories = App_Settings.objects.get(name='categories').value


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
        prompt = f"""Analyze this browsing history entry and classify it into one of these categories: 
                {', '.join(self.current_categories)}.

                Entry: {entry['title']} ({entry['url']})
                Provide only the category name, nothing else.
                If the entry doesn't fit any category, return "Other"."""

        logger.info(f"Classifying entry: {entry['url']}")

        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            category = response.choices[0].message.content.strip()
            # Validate category against known categories
            if self.model_thinking:
                category = category.split("</think>")[0].strip()
                #try to match one of the categories
                category = next((cat for cat in self.current_categories if cat.lower() in category.lower()), "Other")

            if category not in self.current_categories:
                logger.warning(f"Unknown category '{category}' for {entry['url']}")
                category = "Other"

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

        if not filtered:
            logger.warning(f"No entries found for {browser} within the specified date range")
            return []

        # get number of entries

        num_entries = len(filtered)
        processed = 0

        # Rest of processing remains the same
        results = []
        for idx, entry in enumerate(filtered):
            classified_entry = self._generate_category(entry)
            # Update progress
            processed += 1

            logger.info(f"Classified entry: {classified_entry['url']} -> {classified_entry['category']}")
            results.append(classified_entry)
            if (idx + 1) % 5 == 0:
                time.sleep(0.1)  # Rate limit to avoid overwhelming the model

            self.status = {
                "browser": browser.lower(),
                "total": num_entries,
                "processed": processed,
                "remaining": num_entries - processed
            }



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
    chrome_results = classifier.classify_history("chrome")
    classifier.print_results(chrome_results)

    print("\nClassifying Firefox History:")
    firefox_results = classifier.classify_history("firefox")
    classifier.print_results(firefox_results)

