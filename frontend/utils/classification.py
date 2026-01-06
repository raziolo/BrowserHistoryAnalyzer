import logging
from datetime import datetime, timedelta

from classifier.main import HistoryClassifier
from frontend.models import HistoryEvent
from frontend.utils.settings import set_setting

classifier = HistoryClassifier()

def set_classification_status_complete():
    set_setting('classification_status', 1)
    set_setting('last_classification_date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return 0

def start_classification_with_callback(start_date, end_date, reclassify_existing, callback):
    start_classification(start_date, end_date, reclassify_existing)
    callback()

def _upsert_history_events(entries, browser):
    if not entries:
        return

    urls = [entry.get('url') for entry in entries if entry.get('url')]
    existing = HistoryEvent.objects.filter(browser=browser, url__in=urls)
    existing_by_url = {event.url: event for event in existing}
    to_update = []
    to_create = []

    for entry in entries:
        url = entry.get('url')
        if not url:
            continue
        event = existing_by_url.get(url)
        if event:
            event.last_visit = entry.get('last_visit')
            event.title = entry.get('title')
            event.visit_count = entry.get('visit_count')
            event.category = entry.get('category')
            event.browser = browser
            to_update.append(event)
        else:
            to_create.append(HistoryEvent(
                url=url,
                last_visit=entry.get('last_visit'),
                title=entry.get('title'),
                visit_count=entry.get('visit_count'),
                category=entry.get('category'),
                browser=browser,
            ))

    if to_create:
        HistoryEvent.objects.bulk_create(to_create, batch_size=500)
    if to_update:
        HistoryEvent.objects.bulk_update(
            to_update,
            fields=['last_visit', 'title', 'visit_count', 'category', 'browser'],
            batch_size=500,
        )

def start_classification(start_date=None, end_date=None, reclassify_existing=False):
    global classifier
    # Date range setup (fallbacks if needed)
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=7)

    # Classification process
    print("\nClassifying history...")
    try:
        start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")

        chrome_skip_urls = set()
        firefox_skip_urls = set()
        if not reclassify_existing:
            chrome_skip_urls = set(
                HistoryEvent.objects.filter(
                    browser="chrome",
                    last_visit__gte=start_str,
                    last_visit__lte=end_str,
                ).values_list('url', flat=True)
            )
            firefox_skip_urls = set(
                HistoryEvent.objects.filter(
                    browser="firefox",
                    last_visit__gte=start_str,
                    last_visit__lte=end_str,
                ).values_list('url', flat=True)
            )

        # Chrome classification
        chrome_results = classifier.classify_history(
            "chrome",
            start_date,
            end_date,
            skip_urls=chrome_skip_urls,
        )

        # Firefox classification
        firefox_results = classifier.classify_history(
            "firefox",
            start_date,
            end_date,
            skip_urls=firefox_skip_urls,
        )

        # Save results to database
        _upsert_history_events(chrome_results, "chrome")
        _upsert_history_events(firefox_results, "firefox")


        # Display summary
        print(f"\nClassification complete! Results saved to database.")
        print(f"Chrome entries processed: {len(chrome_results)}")
        print(f"Firefox entries processed: {len(firefox_results)}")

    except Exception as e:
        logging.error(f"Classification failed: {e}")
        return
