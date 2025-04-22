from django.utils.crypto import get_random_string





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
    # Run the Django development server

    call_command('makemigrations')
    call_command('migrate')


    call_command('runserver' , '9876')


if __name__ == "__main__":
    main()
    # main()