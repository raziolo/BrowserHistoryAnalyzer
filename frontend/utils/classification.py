import logging
from datetime import timedelta, datetime

from classifier.main import HistoryClassifier
from frontend.models import HistoryEvent, App_Settings
from frontend.utils.settings import set_setting, get_setting

classifier = HistoryClassifier()

def set_classification_status_complete():
    set_setting('classification_status', 1)
    set_setting('last_classification_date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return 0

def start_classification_with_callback(request, callback):
    start_classification()
    callback()

def start_classification():
    global classifier
    # Date range setup
    end_date = datetime.now()
    # Get the number of days to analyze from settings
    days_to_analyze = get_setting('days_to_analyze', default_value=7)
    start_date = end_date - timedelta(days= days_to_analyze)

    # Classification process
    print("\nClassifying history...")
    try:
        # Chrome classification
        chrome_results = classifier.classify_history("chrome", start_date, end_date)

        # Firefox classification
        firefox_results = classifier.classify_history("firefox", start_date, end_date)

        # Save results to database
        for entry in chrome_results:
            HistoryEvent.objects.update_or_create(
                url=entry['url'],
                defaults={
                    'last_visit': entry['last_visit'],
                    'title': entry['title'],
                    'visit_count': entry['visit_count'],
                    'category': entry['category'],
                    'browser': "chrome"
                }
            )
        for entry in firefox_results:
            HistoryEvent.objects.update_or_create(
                url=entry['url'],
                defaults={
                    'last_visit': entry['last_visit'],
                    'title': entry['title'],
                    'visit_count': entry['visit_count'],
                    'category': entry['category'],
                    'browser': "firefox"
                }
            )


        # Display summary
        print(f"\nClassification complete! Results saved to database.")
        print(f"Chrome entries processed: {len(chrome_results)}")
        print(f"Firefox entries processed: {len(firefox_results)}")

    except Exception as e:
        logging.error(f"Classification failed: {e}")
        return
