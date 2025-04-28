from django.contrib import messages
from django.shortcuts import redirect

from HistoryApp import app_settings
from backupManager.main import BrowserHistoryReader


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


def flush_db(request):
    """Flush the database and reset the classification status."""
    from django.core.management import call_command

    call_command('flush', interactive=False)
    call_command('migrate')
    call_command('collectstatic', interactive=False)
    call_command('makemigrations', 'frontend')
    app_settings.load_initial_settings()
    messages.success(request, "Database flushed and initial settings loaded successfully.")

    return redirect('home')