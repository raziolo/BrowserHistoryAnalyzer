import logging
from datetime import datetime, timedelta

from HistoryApp import app_settings
from backupManager.helpers import check_backup_freshness, check_backup_existence
from frontend.analytics import get_category_distribution, get_daily_visits, get_recent_history


def make_backup_card():
    backup_files = check_backup_existence(app_settings.BACKUP_DIR)
    backup_card_data = {
        "has_backup": False,
        "is_fresh": False,
        "last_backup_time": None,  # Formatted string timestamp
        "tooltip_message": "No backups found."  # Default message
    }

    if backup_files:  # Check if list is not None and not empty
        backup_card_data["has_backup"] = True
        is_fresh, latest_file = check_backup_freshness(backup_files,
                                                       max_age=timedelta(days=1))  # Use your desired max_age
        backup_card_data["is_fresh"] = is_fresh

        if latest_file:
            try:
                backup_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
                # Format the time nicely - adjust strftime format as needed
                backup_card_data["last_backup_time"] = backup_time.strftime("%Y-%m-%d %H:%M")

                if is_fresh:
                    backup_card_data[
                        "tooltip_message"] = f"Backup is recent. Completed: {backup_card_data['last_backup_time']}"
                else:
                    # Calculate age for the tooltip message
                    age = datetime.now() - backup_time
                    age_str = f"{age.days} days" if age.days > 0 else f"{age.seconds // 3600} hours"
                    backup_card_data[
                        "tooltip_message"] = f"Backup is STALE (older than {age_str}). Last: {backup_card_data['last_backup_time']}"

            except Exception as e:
                logging.error(f"Error formatting backup time: {e}")
                backup_card_data["last_backup_time"] = "Error"
                backup_card_data["tooltip_message"] = "Error retrieving backup details."
                # Decide if an error state should be treated as 'not fresh'
                backup_card_data["is_fresh"] = False
                backup_card_data[
                    "has_backup"] = False  # Treat error as no usable backup maybe? Or add specific error state?
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


def make_lm_studio_ping():
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

def dashboard_context():
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


