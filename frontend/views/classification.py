import logging
import threading
import time
from datetime import datetime, timedelta

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from frontend.utils.classification import start_classification_with_callback, set_classification_status_complete
from frontend.utils.settings import get_setting, set_setting

from frontend.utils.classification import classifier


DATE_FORMAT = "%Y-%m-%d"

def classification(request):
    if request.method == 'POST':
        # has selected model in settings
        current_model = get_setting('current_model', default_value=None)
        # Check if the model is set
        if not current_model:
            messages.error(request, "No model selected in settings.")
            return redirect('settings')

        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        reclassify_existing = request.POST.get('reclassify_existing') == 'on'

        try:
            start_date = datetime.strptime(start_date_str, DATE_FORMAT).date()
            end_date = datetime.strptime(end_date_str, DATE_FORMAT).date()
        except (TypeError, ValueError):
            messages.error(request, "Please provide valid start and end dates.")
            return redirect('classification')

        if end_date < start_date:
            messages.error(request, "End date must be the same as or after start date.")
            return redirect('classification')

        start_date_dt = datetime.combine(start_date, datetime.min.time())
        end_date_dt = datetime.combine(end_date, datetime.min.time()) + timedelta(days=1) - timedelta(seconds=1)

        set_setting('last_classification_start_date', start_date_str)
        set_setting('last_classification_end_date', end_date_str)
        set_setting('last_classification_reclassify', reclassify_existing)

        # Avvia la classification in background
        threading.Thread(target=start_classification_with_callback,
                         args=(start_date_dt, end_date_dt, reclassify_existing, set_classification_status_complete),
                         daemon=True).start()

        set_setting('classification_status', 0)
        time.sleep(2) # Attendi un attimo per assicurarti che il thread di classificazione sia avviato
        # Torni subito questa risposta JSON
        return redirect('classification')

    can_start_classification = None
    try:
        status = get_setting('classification_status', default_value=1)
        if status == 0:
            can_start_classification = False
        elif status == 1:
            can_start_classification = True
    except Exception as e:
        logging.error(f"Error retrieving classification status: {e}")
        can_start_classification = True

    last_classification_date = get_setting('last_classification_date', default_value="")
    today = datetime.now().date()
    default_start = (today - timedelta(days=7)).strftime(DATE_FORMAT)
    default_end = today.strftime(DATE_FORMAT)
    start_date = get_setting('last_classification_start_date', default_start)
    end_date = get_setting('last_classification_end_date', default_end)
    reclassify_existing = get_setting('last_classification_reclassify', False)

    # Passa il valore a template
    context = {
        'can_start_classification': can_start_classification,
        'last_classification_date': last_classification_date,
        'start_date': start_date,
        'end_date': end_date,
        'reclassify_existing': reclassify_existing,
    }

    return render(request, 'frontend/classification.html', context)


def get_classification_status(request):
    """Check the status of the classification process."""

    status = classifier.status

    data = {
        'total': status.get('total', 0),
        'processed': status.get('processed', 0),
        'remaining': status.get('remaining', 0),
        'progress': int((status.get('processed', 0) / max(1, status.get('total', 1))) * 100) if status.get('total', 0) > 0 else 0,
        'browser': status.get('browser', 'Unknown'),
    }

    db_status = get_setting('classification_status', default_value=1)

    if data['remaining'] == 0 and db_status == 1:
        # Classification is complete
        response = HttpResponse()
        response['HX-Redirect'] = reverse('classification')
        return response

    return render(request, 'components/progress.html', data)

def reset_classification_status(request):
    """Reset the classification status to 'Complete'."""
    set_setting('classification_status', 1)
    messages.success(request, "Classification status reset to complete.")
    return redirect('classification')
