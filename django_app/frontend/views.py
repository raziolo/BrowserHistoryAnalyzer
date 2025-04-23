import logging
import threading
import time
from datetime import datetime, timedelta

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django_tables2 import SingleTableView

from backupManager.main import BrowserHistoryReader
from classifier.main import HistoryClassifier
from .models import App_Settings, HistoryEvent
from main import setup_backup
from django_app.HistoryApp import app_settings
from django.shortcuts import render, redirect
from .forms import ClassifierSettingsForm
from django.core.serializers.json import DjangoJSONEncoder
import json
from typing import Dict, List


def get_category_distribution(browser: str) -> Dict[str, int]:
    from django.db.models import Count
    qs = HistoryEvent.objects.filter(browser=browser.lower()) \
        .values('category') \
        .annotate(count=Count('id')) \
        .order_by('-count')

    return {item['category']: item['count'] for item in qs}


def get_daily_visits(browser: str) -> List[Dict]:
    from django.db.models import Count, Func

    class Date(Func):
        function = 'DATE'

    qs = HistoryEvent.objects.filter(browser=browser.lower()) \
        .annotate(day=Date('last_visit')) \
        .values('day') \
        .annotate(count=Count('id')) \
        .order_by('day')

    return list(qs)


def get_recent_history(browser: str, limit: int = 10) -> List[Dict]:
    qs = HistoryEvent.objects.filter(browser=browser.lower()) \
             .order_by('-last_visit') \
             .values('url', 'title', 'category', 'last_visit', 'visit_count')[:limit]

    return list(qs)

classifier = HistoryClassifier()


# Create your views here.
def home(request):
    """Renders the home page."""

    context = {
        "backup_card_data": make_backup_card(request),
        "backup_dir": app_settings.BACKUP_DIR,
        'dashboard_data': dashboard_context(request),
        'generation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'lm_studio': make_lm_studio_ping(request),
    }

    return render(request, 'frontend/home.html', context)


def make_lm_studio_ping(request):
    # make a request to 127.0.0.1:7860/v1
    import requests

    response = requests.get('http://127.0.0.1:1234/v1/models')

    return {
        'ping' : True if response.status_code == 200 else False,
        'ping_time' : response.elapsed.total_seconds(),
        'model_list' : response.json()['data'],

    }


def make_backup_card(request):

    backups = None

    backup_card_data = {
        "chrome" : {
            "status" : False,
        },
        "firefox" : {
            "status" : False,
        },
        'last_backup' : '',
    }


    # Check if backup is needed
    if setup_backup():
        backup_card_data["chrome"]["status"] = False
        backup_card_data["firefox"]["status"] = False
    else:
        backup_card_data["chrome"]["status"] = True
        backup_card_data["firefox"]["status"] = True
        backup_card_data["last_backup"] = get_latest_backup_date()

    return backup_card_data


def get_latest_backup_date():
    try:
        # Get the last backup date
        backups = list(app_settings.BACKUP_DIR.glob("*_history.json"))
        latest_backup = max(backups, key=lambda f: f.stat().st_mtime)
        # Format the last backup date
        nf_last_backup_date = latest_backup.stat().st_mtime
        # Convert to datetime object
        nf_last_backup_date = datetime.fromtimestamp(nf_last_backup_date)
        return nf_last_backup_date.strftime("%Y-%m-%d %H:%M:%S")

    except ValueError:
        return "NaD"
    except Exception as e:
        logging.error(f"Error retrieving latest backup date: {e}")
        return "NaD"

def dashboard_context(request):
    # Collect data
    chrome_categories = get_category_distribution('chrome')
    firefox_categories = get_category_distribution('firefox')

    timeline_data = {
        'chrome': get_daily_visits('chrome'),
        'firefox': get_daily_visits('firefox'),
    }

    recent_history = {
        'chrome': get_recent_history('chrome'),
        'firefox': get_recent_history('firefox'),
    }

    # Prepare chart data
    chart_data = {

        'timeline_labels': sorted(
            list({entry['day'] for entry in timeline_data['chrome'] + timeline_data['firefox']})),
        'chrome_timeline': [entry['count'] for entry in timeline_data['chrome']],
        'firefox_timeline': [entry['count'] for entry in timeline_data['firefox']],
    }

    chrome_labels = list(chrome_categories.keys())
    chrome_values = list(chrome_categories.values())
    firefox_labels = list(firefox_categories.keys())
    firefox_values = list(firefox_categories.values())

    chrome_category_data = list(zip(chrome_labels, chrome_values))
    firefox_category_data = list(zip(firefox_labels, firefox_values))

    # create an object with the data
    dashboard_data = {
        'generated_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'chrome_category_data': chrome_category_data,
        'firefox_category_data': firefox_category_data,
        'chart_data': chart_data,
        'recent_history': recent_history,
        'total_entries': {
            'chrome': sum(chrome_categories.values()),
            'firefox': sum(firefox_categories.values())
        }
    }
    return dashboard_data


def make_backup(request):
    reader = BrowserHistoryReader()
    chrome_history = reader.get_chrome_history()
    if chrome_history:
        reader.backup_history(chrome_history, "Chrome")

    firefox_history = reader.get_firefox_history()
    if firefox_history:
        reader.backup_history(firefox_history, "Firefox")
        # Check if backups exist

    backups = list(app_settings.BACKUP_DIR.glob("*_history.json"))

    if not backups:
        messages.error(request, "Error during Backup")
    else:
        messages.success(request, "Backup completed successfully")
    return redirect('home')

def set_classification_status_complete():
    App_Settings.objects.update(name='classification_status', value='Complete')
    return 0

def start_classification_with_callback(request, callback):
    start_classification(request)
    callback()

def start_classification(request):
    global classifier
    # Date range setup
    end_date = datetime.now()
    start_date = end_date - timedelta(days=app_settings.DAYS_TO_ANALYZE)

    # Classification process
    print("\nClassifying history...")
    try:
        # Chrome classification
        chrome_results = classifier.classify_history("chrome", start_date, end_date)
        # classifier.save_classified_data(chrome_results, "Chrome")

        # Firefox classification
        firefox_results = classifier.classify_history("firefox", start_date, end_date)
        # classifier.save_classified_data(firefox_results, "Firefox")

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


def classification(request):
    if request.method == 'POST':
        # Avvia la classification in background
        threading.Thread(target=start_classification_with_callback,
                         args=(request, set_classification_status_complete),
                         daemon=True).start()

        App_Settings.objects.update(
            name='classification_status',
            value='In progress',
        )
        time.sleep(2) # Attendi un attimo per assicurarti che il thread di classificazione sia avviato
        # Torni subito questa risposta JSON
        return redirect('classification')

    can_start_classification = None
    try:
        classification_status = App_Settings.objects.get(name='classification_status').value
        if classification_status == 'In progress':
            can_start_classification = False
        elif classification_status == 'Completed':
            can_start_classification = True
        else:
            can_start_classification = True
    except App_Settings.DoesNotExist:
        pass # Handle the case where the setting does not exist
    except Exception as e:
        logging.error(f"Error retrieving classification status: {e}")
        can_start_classification = True

    latest_backup = get_latest_backup_date()

    # Passa il valore a template
    context = {
        'can_start_classification': can_start_classification,
        'last_backup': latest_backup,
    }

    return render(request, 'frontend/classification.html', context)


def classification_status(request):
    """Check the status of the classification process."""
    global classifier

    status = classifier.status

    data = {
        'total': status.get('total', 0),
        'processed': status.get('processed', 0),
        'remaining': status.get('remaining', 0),
        'progress': int((status.get('processed', 0) / max(1, status.get('total', 1))) * 100) if status.get('total', 0) > 0 else 0,
        'browser': status.get('browser', 'Unknown'),
    }

    # Check if the classification is complete
    if data['remaining'] == 0:
        # Update the status in the database
        App_Settings.objects.update(name='classification_status', value='Complete')
        # Create empty response with redirect header
        response = HttpResponse()
        response['HX-Redirect'] = reverse('classification')
        return response

    return render(request, 'components/progress.html', data)


from .tables import HistoryEventTable


class HistoryEventListView(SingleTableView):
    model = HistoryEvent
    table_class = HistoryEventTable
    # full page
    template_name = 'frontend/history_list.html'
    # django-tables2 pagination
    table_pagination = {"per_page": 10}

    def get_template_names(self):
        # django-htmx makes this True when an HTMX request comes in
        if getattr(self.request, "htmx", False):
            return ['frontend/history_table_partial.html']
        return [self.template_name]

    def get_queryset(self):
        return super().get_queryset().order_by('-visit_count')

def settings_view(request):


    # Get current settings
    settings = {
        'days_to_analyze': 5,
        'categories': [],
        'temperature': 0.1,
        'max_tokens': 1000
    }

    # Load from database if available
    try:
        settings['days_to_analyze'] = int(App_Settings.objects.get(name='DAYS_TO_ANALYZE').value)
        params = json.loads(App_Settings.objects.get(name='CLASSIFICATION_PARAMETERS').value)
        settings.update(params)
    except App_Settings.DoesNotExist:
        pass

    if request.method == 'POST':
        form = ClassifierSettingsForm(request.POST)
        if form.is_valid():
            # Save settings to database
            App_Settings.objects.update_or_create(
                name='DAYS_TO_ANALYZE',
                defaults={'value': str(form.cleaned_data['days_to_analyze'])}
            )

            params = {
                'categories': form.cleaned_data['categories'],
                'temperature': form.cleaned_data['temperature'],
                'max_tokens': form.cleaned_data['max_tokens']
            }

            App_Settings.objects.update_or_create(
                name='CLASSIFICATION_PARAMETERS',
                defaults={'value': json.dumps(params, cls=DjangoJSONEncoder)}
            )

            return redirect('settings')
    else:
        initial_data = {
            'days_to_analyze': settings['days_to_analyze'],
            'categories': '\n'.join(settings['categories']),
            'temperature': settings['temperature'],
            'max_tokens': settings['max_tokens']
        }
        form = ClassifierSettingsForm(initial=initial_data)

    return render(request, 'frontend/settings.html', {'form': form})