from datetime import datetime

from django.shortcuts import render, redirect

from backupManager.main import BrowserHistoryReader
from main import setup_backup
import app_settings


# Create your views here.
def home(request):
    """Renders the home page."""


    context = {
        "backup_card_data": make_dashboard_context(),
        "backup_dir": app_settings.BACKUP_DIR,
    }

    return render(request, 'frontend/home.html' , context)

def make_dashboard_context():
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
        # Get the last backup date
        backups = list(app_settings.BACKUP_DIR.glob("*_history.json"))
        latest_backup = max(backups, key=lambda f: f.stat().st_mtime)
        backup_card_data["last_backup"] = latest_backup.stat().st_mtime
        # Format the last backup date
        nf_last_backup_date = latest_backup.stat().st_mtime
        # Convert to datetime object
        nf_last_backup_date = datetime.fromtimestamp(nf_last_backup_date)
        backup_card_data["last_backup"] = nf_last_backup_date.strftime("%Y-%m-%d %H:%M:%S")

    return backup_card_data


def make_backup(request):
    reader = BrowserHistoryReader()
    chrome_history = reader.get_chrome_history()
    if chrome_history:
        reader.backup_history(chrome_history, "Chrome")

    firefox_history = reader.get_firefox_history()
    if firefox_history:
        reader.backup_history(firefox_history, "Firefox")
    print("OK")
    return redirect('home')