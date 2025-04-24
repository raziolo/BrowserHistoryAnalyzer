import time
import json # Though not strictly needed for saving with JSONField via ORM




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




    def load_initial_settings():
        print("Loading initial App Settings...")

        base_settings = {
            'classification_status': "Complete",  # String value
            'days_to_analyze': 1,  # Integer value
            'classification_parameters': {  # Dictionary (will be stored as JSON)
                "categories": [
                    "Social Media", "News", "Media", "E‑commerce", "Shopping",
                    "Education", "Learning", "Video", "Streaming", "Music", "Audio",
                    "Technology", "Gadgets", "Finance", "Banking", "Health", "Fitness",
                    "Travel", "Transportation", "Sports", "Government", "Politics",
                    "Jobs", "Career", "Lifestyle", "Hobbies", "Food", "Cooking",
                    "Real Estate", "Science", "Research", "Art", "Culture", "Forums",
                    "Q&A", "Blogs", "Personal", "Adult", "Utilities", "Productivity",
                    "Other"
                ],
            },
            'temperature': 0.1,  # Float value
            'max_tokens': 1000,  # Integer value
            'current_model': "",
            'settings_loaded': True,
        }

        # --- Process base_settings ---
        for key, value in base_settings.items():
            obj, created = App_Settings.objects.update_or_create(
                name=key,  # Field to match on
                defaults={'value': value}  # Field(s) to set or update
                # Django's JSONField handles serialization
            )
            if created:
                print(f"  Created setting: {key}")
            else:
                print(f"  Updated setting: {key}")

        # --- Explicitly create the 'categories' setting from the list ---
        # This is crucial because the view/form expects a top-level 'categories' setting
        # containing JUST the list of strings.
        category_list = base_settings.get('classification_parameters', {}).get('categories', [])
        if category_list:  # Only create if categories were found
            obj, created = App_Settings.objects.update_or_create(
                name='categories',
                defaults={'value': category_list}  # Store the list directly
            )
            if created:
                print(f"  Created setting: categories (list)")
            else:
                print(f"  Updated setting: categories (list)")
        else:
            print(
                "  Warning: Could not find categories list in base_settings['classification_parameters'] to create 'categories' setting.")

        print("Initial settings loading complete.")

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

    # Run the Django development server
    call_command('makemigrations')
    # call_command('flush', '--no-input')

    time.sleep(0.1)
    call_command('makemigrations', 'frontend')
    time.sleep(0.1)
    call_command('migrate')
    time.sleep(0.1)
    call_command('collectstatic', '--noinput')

    call_command('runserver' , '9876')




if __name__ == "__main__":
    main()
    # main()
