import logging
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
LOGGER = logging.getLogger(__name__)

# Shared Configuration
BACKUP_DIR = Path(__file__).parent.parent / "backupManager" / "history_backups"

# CLASSIFIER CONFIGURATION
import django
django.setup()

DAYS_TO_ANALYZE = 1 # Fallback  # Analyze history from last N days


def load_initial_settings():
    from frontend.models import App_Settings

    print("Loading initial App Settings...")

    base_settings = {
        'classification_status': 1,  # String value
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

