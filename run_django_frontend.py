import time

def main():
    import os
    import sys
    from pathlib import Path

    # Get the current working directory
    current_directory = Path(__file__).resolve().parent

    # Add the parent directory to the system path
    sys.path.append(str(current_directory.parent))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HistoryApp.settings')

    import django
    django.setup()

    from django.core.management import call_command
    from frontend.models import App_Settings
    from HistoryApp.app_settings import load_initial_settings

    # Run the Django development server
    call_command('makemigrations')
    # call_command('flush', '--no-input')

    time.sleep(0.1)
    call_command('makemigrations', 'frontend')
    time.sleep(0.1)
    call_command('migrate')
    time.sleep(0.1)
    call_command('collectstatic', '--noinput')

    if App_Settings.objects.filter(name='settings_loaded').exists():

        settings_loaded = App_Settings.objects.get(name='settings_loaded').value
        if not settings_loaded:
            print("Settings not loaded, proceeding to load initial settings.")
            load_initial_settings()
        else:
            print("Settings already loaded, skipping initial settings load.")
    else:
        print("Settings not loaded, proceeding to load initial settings.")
        load_initial_settings()

    print(App_Settings.objects)

    call_command('runserver' , '9876')




if __name__ == "__main__":
    main()
    # main()
