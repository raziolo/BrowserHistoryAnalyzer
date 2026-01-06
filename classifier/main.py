# classifier.py
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HistoryApp.settings')

import django
django.setup()

import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional
from openai import OpenAI
from datetime import datetime
from HistoryApp import app_settings
from frontend.utils.settings import get_setting

# AI model name from settings.py

logger = app_settings.LOGGER


class HistoryClassifier:
    def __init__(self, model_name: str = "local-model", base_url: str = "http://localhost:1234/v1"):
        self.client = OpenAI(base_url=base_url, api_key="not-needed")
        self.model_name = get_setting('current_model', default_value=model_name)
        self.model_thinking = False
        self.backup_dir = app_settings.BACKUP_DIR
        self.status = {}
        self.temperature = get_setting('temperature', default_value=0.1)
        self.max_tokens = get_setting('max_tokens', default_value=1000)
        self.current_categories = get_setting('categories', default_value=['Work', 'Personal', 'Other'])

    def _extract_json_array(self, text: str) -> List[Dict]:
        """Best-effort extraction of a JSON array from model output."""
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            start = text.find('[')
            end = text.rfind(']')
            if start == -1 or end == -1 or end <= start:
                raise
            data = json.loads(text[start:end + 1])

        if isinstance(data, dict) and 'results' in data:
            data = data['results']
        if not isinstance(data, list):
            raise ValueError("Expected a JSON list of results.")
        return data


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

    def _generate_categories_batch(self, entries: List[Dict]) -> List[Dict]:
        """Classify a batch of history entries using a single model request."""
        lines = []
        for idx, entry in enumerate(entries, start=1):
            title = entry.get('title', '').strip()
            url = entry.get('url', '').strip()
            lines.append(f"{idx}. {title} ({url})")

        prompt = (
            "Classify each entry into one of these categories: "
            f"{', '.join(self.current_categories)}.\n"
            "Return a JSON array of objects with fields \"index\" and \"category\".\n"
            "Use \"Other\" if the entry doesn't fit any category.\n"
            "Return only JSON.\n\n"
            "Entries:\n"
            + "\n".join(lines)
        )

        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content.strip()
            if self.model_thinking and "</think>" in content:
                content = content.split("</think>")[0].strip()

            parsed = self._extract_json_array(content)
            results_by_index = {}
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                index = item.get('index')
                category = item.get('category')
                try:
                    index = int(index)
                except (TypeError, ValueError):
                    continue
                if not isinstance(category, str):
                    continue
                category = category.strip()
                if category not in self.current_categories:
                    category = "Other"
                results_by_index[index] = category

            results = []
            for idx, entry in enumerate(entries, start=1):
                category = results_by_index.get(idx)
                if not category:
                    results.append(self._generate_category(entry))
                    continue
                results.append({**entry, "category": category})

            return results

        except Exception as e:
            logger.error(f"Batch classification failed: {e}")
            return [self._generate_category(entry) for entry in entries]

    def _generate_category(self, entry: Dict) -> Dict:
        """Classify a single history entry using local model"""
        prompt = f"""Analyze this browsing history entry and classify it into one of these categories: 
                {', '.join(self.current_categories)}.

                Entry: {entry['title']} ({entry['url']})
                Provide only the category name, nothing else.
                If the entry doesn't fit any category, return "Other"."""

        logger.info(f"Classifying entry: {entry['url']}")

        if get_setting('classification_status', 1) == 1:
            logger.info(f"Classification is disabled. Skipping entry: {entry['url']}")
            return {**entry, "category": "Classification Disabled"}

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

    def classify_history(
        self,
        browser: str,
        start_date: datetime,
        end_date: datetime,
        skip_urls: Optional[set] = None,
        batch_size: Optional[int] = None,
    ) -> List[Dict]:
        """Classify history within date range with robust date handling"""
        self.model_name = get_setting('current_model', default_value=self.model_name)
        self.temperature = get_setting('temperature', default_value=self.temperature)
        self.max_tokens = get_setting('max_tokens', default_value=self.max_tokens)
        self.current_categories = get_setting('categories', default_value=self.current_categories)
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

        skip_urls = skip_urls or set()
        deduped = []
        seen = set()
        for entry in filtered:
            url = entry.get('url')
            last_visit = entry.get('last_visit')
            if not url:
                continue
            if url in skip_urls:
                continue
            key = (url, last_visit)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(entry)

        if not deduped:
            logger.warning(f"No entries to classify for {browser} after filtering.")
            return []

        num_entries = len(deduped)
        processed = 0

        # Rest of processing remains the same
        results = []
        effective_batch_size = batch_size or get_setting('classification_batch_size', default_value=8)
        if not isinstance(effective_batch_size, int) or effective_batch_size < 1:
            effective_batch_size = 1

        for start in range(0, num_entries, effective_batch_size):
            if get_setting('classification_status', 1) == 1:
                logger.info("Classification disabled. Stopping batch processing.")
                break

            batch = deduped[start:start + effective_batch_size]
            if effective_batch_size > 1:
                batch_results = self._generate_categories_batch(batch)
            else:
                batch_results = [self._generate_category(entry) for entry in batch]

            for classified_entry in batch_results:
                processed += 1
                logger.info(
                    f"Classified entry: {classified_entry['url']} -> {classified_entry['category']}"
                )
                if classified_entry['category'] == "Classification Disabled":
                    logger.info(f"Classification disabled for {classified_entry['url']}")
                    continue
                results.append(classified_entry)

                self.status = {
                    "browser": browser.lower(),
                    "total": num_entries,
                    "processed": processed,
                    "remaining": num_entries - processed
                }

            time.sleep(0.05)  # Small pause per batch to avoid overwhelming the model



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

    # Initialize classifier with model and API URL
    classifier = HistoryClassifier(
        model_name='gemma-3-4b-it',  # or 'granite-3.1-8b-instruct'
        base_url='http://localhost:1234/v1'
    )

    # Define a default 30-day date range
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    print("Classifying Chrome History:")
    chrome_results = classifier.classify_history("chrome", start_date, end_date)
    classifier.print_results(chrome_results)

    print("\nClassifying Firefox History:")
    firefox_results = classifier.classify_history("firefox", start_date, end_date)
    classifier.print_results(firefox_results)


