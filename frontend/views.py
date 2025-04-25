import logging
import threading
import time
from datetime import datetime, timedelta

import requests
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django_tables2 import SingleTableView

from backupManager.main import BrowserHistoryReader
from classifier.main import HistoryClassifier
from .models import App_Settings, HistoryEvent
from main import setup_backup
from HistoryApp import app_settings
from django.shortcuts import render, redirect
from .forms import SettingsForm
from django.core.serializers.json import DjangoJSONEncoder
import json
from typing import Dict, List

logger = app_settings.LOGGER

def reset_classification_status(request):
    """Reset the classification status to 'Complete'."""
    App_Settings.objects.filter(name='classification_status').update(value=1)
    messages.success(request, "Classification status reset to complete.")
    return redirect('classification')

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


def get_recent_history(browser: str, limit: int = 20) -> List[Dict]:
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
    try:
        response = requests.get('http://127.0.0.1:1234/v1/models')
    except Exception as e:
        logging.error(f"Error pinging LM Studio: {e}")
        return {
            'ping': False,
            'ping_time': 0,
            'model_list': []
        }
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
    App_Settings.objects.filter(name='classification_status').update(value=1)
    return 0

def start_classification_with_callback(request, callback):
    start_classification()
    callback()

def start_classification():
    global classifier
    # Date range setup
    end_date = datetime.now()
    # Get the number of days to analyze from settings
    days_to_analyze = App_Settings.objects.get(name='days_to_analyze').value
    start_date = end_date - timedelta(days= days_to_analyze)
    print(days_to_analyze)

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
        # has selected model in settings
        current_model = App_Settings.objects.get(name='current_model').value
        # Check if the model is set
        if not current_model:
            messages.error(request, "No model selected in settings.")
            return redirect('settings')

        # Avvia la classification in background
        threading.Thread(target=start_classification_with_callback,
                         args=(request, set_classification_status_complete),
                         daemon=True).start()

        App_Settings.objects.filter(name='classification_status').update(value=0)
        time.sleep(2) # Attendi un attimo per assicurarti che il thread di classificazione sia avviato
        # Torni subito questa risposta JSON
        return redirect('classification')

    can_start_classification = None
    try:
        status = App_Settings.objects.get(name='classification_status').value
        print(status)
        if status == 0:
            can_start_classification = False
        elif status == 1:
            can_start_classification = True
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


def get_classification_status(request):
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

    db_status = App_Settings.objects.get(name='classification_status').value

    if data['remaining'] == 0 and db_status == 1:
        # Classification is complete
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

def get_setting(name, default_value):
    """Helper function to get a setting value or return a default."""
    try:
        setting = App_Settings.objects.get(name=name)
        return setting.value # JSONField returns the python object
    except App_Settings.DoesNotExist:
        return default_value
    except (json.JSONDecodeError, TypeError): # Handle potential issues if value isn't valid JSON or expected type
        logger.warning(f"Could not decode setting '{name}'. Returning default.")
        return default_value

def fetch_available_models():
    """Fetches the list of available models from LM Studio API."""
    api_url = 'http://127.0.0.1:1234/v1/models'
    model_list = []
    error_message = None
    try:
        # Increased timeout for potentially slow API
        response = requests.get(api_url, timeout=10)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        if 'data' in data and isinstance(data['data'], list):
            # Extract model IDs - assuming each item in 'data' is a dict with an 'id' key
            model_list = [{'id': model.get('id')}
                          for model in data['data'] if model.get('id')]
            if not model_list:
                error_message = "API returned empty model list."
                logger.warning(f"LM Studio API ({api_url}) returned empty or invalid model list structure.")
        else:
            error_message = "Invalid response format from API."
            logger.error(f"Invalid response format from LM Studio API ({api_url}): {data}")

    except requests.exceptions.ConnectionError:
        error_message = "Could not connect to LM Studio API. Is it running?"
        logger.error(f"ConnectionError connecting to LM Studio API ({api_url}).")
    except requests.exceptions.Timeout:
        error_message = "Connection to LM Studio API timed out."
        logger.error(f"Timeout connecting to LM Studio API ({api_url}).")
    except requests.exceptions.RequestException as e:
        error_message = f"Error fetching models: {e}"
        logger.error(f"Error fetching models from LM Studio API ({api_url}): {e}")
    except (json.JSONDecodeError, KeyError) as e:
         error_message = "Error parsing API response."
         logger.error(f"Error parsing LM Studio API ({api_url}) response: {e}")

    return model_list, error_message


def settings_view(request):
    # Fetch available models and potential error message
    available_models, model_fetch_error = fetch_available_models()

    # Create choices for the form field (list of tuples)
    # Use model['id'] for both value and display text
    model_choices = [('', '--- Select a Model ---')] # Add a default empty choice
    model_choices.extend((model['id'], model['id']) for model in available_models)

    # Define defaults
    defaults = {
        'days_to_analyze': 7,
        'temperature': 0.1,
        'max_tokens': 1000,
        'categories': [
            "Social Media", "News", "Technology", "Shopping", "Education"
        ],
        'current_model': None # Default for the new setting
    }

    if request.method == 'POST':
        # Pass dynamic choices to the form during POST validation
        form = SettingsForm(request.POST, model_choices=model_choices)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            categories_list = cleaned_data['categories'] # Already a list

            # Save settings using update_or_create
            App_Settings.objects.update_or_create(
                name='days_to_analyze',
                defaults={'value': cleaned_data['days_to_analyze']}
            )
            App_Settings.objects.update_or_create(
                name='temperature',
                defaults={'value': cleaned_data['temperature']}
            )
            App_Settings.objects.update_or_create(
                name='max_tokens',
                defaults={'value': cleaned_data['max_tokens']}
            )
            # Store the categories list directly as JSON
            App_Settings.objects.update_or_create(
                name='categories',
                defaults={'value': categories_list}
            )
            # Update classification_parameters based on categories
            classification_params = {
                "categories": categories_list,
                "Other": False # Or derive as needed
            }
            App_Settings.objects.update_or_create(
                name='classification_parameters',
                defaults={'value': classification_params}
            )
            # Save the selected model
            App_Settings.objects.update_or_create(
                name='current_model',
                defaults={'value': cleaned_data['current_model']} # Store the selected model ID
            )

            messages.success(request, 'Settings updated successfully!')
            return redirect('settings') # Use your actual URL name
        else:
            # Form is invalid, add error messages if needed (e.g., API error)
             if model_fetch_error:
                 messages.error(request, f"Could not refresh model list: {model_fetch_error}")

    else: # GET Request
        # Load initial data from the database
        initial_data = {
            'days_to_analyze': get_setting('days_to_analyze', defaults['days_to_analyze']),
            'temperature': get_setting('temperature', defaults['temperature']),
            'max_tokens': get_setting('max_tokens', defaults['max_tokens']),
            'current_model': get_setting('current_model', defaults['current_model']), # Load current model
        }
        current_categories_list = get_setting('categories', defaults['categories'])
        if isinstance(current_categories_list, list):
             initial_data['categories'] = "\n".join(current_categories_list)
        else:
             initial_data['categories'] = "\n".join(defaults['categories']) # Fallback

        # Pass dynamic choices AND initial data to the form for GET
        form = SettingsForm(initial=initial_data, model_choices=model_choices)

        # Display error message if model fetching failed on GET
        if model_fetch_error:
            messages.warning(request, f"Could not fetch model list: {model_fetch_error}")


    # Fetch current categories again for bubble display
    current_categories_for_bubbles = get_setting('categories', defaults['categories'])
    if not isinstance(current_categories_for_bubbles, list):
        current_categories_for_bubbles = []

    context = {
        'form': form,
        'current_categories': current_categories_for_bubbles,
        'model_fetch_error': model_fetch_error # Pass error to template if needed for specific UI
    }
    return render(request, 'frontend/settings.html', context)