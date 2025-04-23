import time
DAYS_TO_ANALYZE = 2  # Analyze history from last N days
# Configure classification parameters
CLASSIFICATION_PARAMETERS = {
    "categories": [
        # Core verticals
        "Social Media",
        "News",
        "Media",
        "E‑commerce",
        "Shopping",
        "Education",
        "Learning",
        "Video",
        "Streaming",
        "Music",
        "Audio",
        "Technology",
        "Gadgets",
        "Finance",
        "Banking",
        "Health",
        "Fitness",
        "Travel",
        "Transportation",
        "Sports",
        "Government",
        "Politics",
        "Jobs",
        "Career",
        "Lifestyle",
        "Hobbies",
        "Food",
        "Cooking",
        "Real Estate",
        "Science",
        "Research",
        "Art",
        "Culture",
        "Forums",
        "Q&A",
        "Blogs",
        "Personal",
        "Adult",
        "Utilities",
        "Productivity",
        "Search"
        # Fallback
        "Other"
    ],
    "temperature": 0.1, # Lower temperature for more deterministic results, higher for more creative ones
    "max_tokens": 1000  # allow a bit more room for multi‑word labels
}


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

    # Run the Django development server
    call_command('makemigrations')
    # call_command('flush', '--no-input')

    time.sleep(0.1)
    call_command('makemigrations', 'frontend')
    time.sleep(0.1)
    call_command('migrate')
    time.sleep(0.1)
    call_command('collectstatic', '--noinput')

    base_settings = ['classification_status']

    for setting in base_settings:
        if App_Settings.objects.filter(name=setting).exists():
            App_Settings.objects.filter(name=setting).update(value="Complete")
        else:
            App_Settings.objects.update_or_create(
                name=setting,
                value=False,
            )

    call_command('runserver' , '9876')


if __name__ == "__main__":
    main()
    # main()