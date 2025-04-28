# frontend/context_processors.py

import logging
from .models import App_Settings
from HistoryApp import app_settings # Assuming your logger is configured here
from .utils.settings import get_setting, set_setting

logger = app_settings.LOGGER

def classification_status_processor(request):
    """
    Adds the classification status to the template context.
    """
    can_start = True # Default: Assume classification can start or is complete
    db_status = 1    # Default DB status value corresponding to 'complete'

    try:
        # Fetch the status from the database
        # Ensure 'classification_status' matches the 'name' field in your App_Settings model
        db_status = get_setting('classification_status', default_value=1)

        if db_status == 0:
            can_start = False # Classification is running

    except App_Settings.DoesNotExist:
        # If the setting doesn't exist, assume it's not running
        logger.warning("App_Settings entry 'classification_status' not found. Assuming classification is not running.")
        can_start = True
        set_setting('classification_status', 1) # Default to 'complete'

    except Exception as e:
        # Log any other errors during fetch and default to 'can_start = True'
        logger.error(f"Error fetching classification status from DB: {e}. Defaulting to 'can_start=True'.")
        can_start = True
        set_setting('classification_status', 1) # Default to 'complete'

    return {
        'can_start_classification': can_start,
    }