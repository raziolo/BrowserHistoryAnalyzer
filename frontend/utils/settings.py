import json

import requests

from HistoryApp import app_settings
from frontend.models import App_Settings

logger = app_settings.LOGGER

def fetch_available_models():
    """Fetches the list of available models from LM Studio API."""
    api_url = 'http://127.0.0.1:1234/v1/models'
    model_list = []
    error_message = None
    try:
        # Increased timeout for potentially slow API
        response = requests.get(api_url, timeout=10)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        if 'data' in data and isinstance(data['data'], list):
            # Extract model IDs - assuming each item in 'data' is a dict with an 'id' key
            model_list = [{'id': model.get('id')}
                          for model in data['data'] if model.get('id')]
            if not model_list:
                error_message = "API returned empty model list."
                logger.warning(f"LM Studio API ({api_url}) returned empty or invalid model list structure.")
        else:
            error_message = "Invalid response format from API."
            logger.error(f"Invalid response format from LM Studio API ({api_url}): {data}")

    except requests.exceptions.ConnectionError:
        error_message = "Could not connect to LM Studio API. Is it running?"
        logger.error(f"ConnectionError connecting to LM Studio API ({api_url}).")
    except requests.exceptions.Timeout:
        error_message = "Connection to LM Studio API timed out."
        logger.error(f"Timeout connecting to LM Studio API ({api_url}).")
    except requests.exceptions.RequestException as e:
        error_message = f"Error fetching models: {e}"
        logger.error(f"Error fetching models from LM Studio API ({api_url}): {e}")
    except (json.JSONDecodeError, KeyError) as e:
         error_message = "Error parsing API response."
         logger.error(f"Error parsing LM Studio API ({api_url}) response: {e}")

    return model_list, error_message

def get_setting(name, default_value):
    """Helper function to get a setting value or return a default."""
    try:
        setting = App_Settings.objects.get(name=name)
        return setting.value # JSONField returns the python object
    except App_Settings.DoesNotExist:
        return default_value
    except (json.JSONDecodeError, TypeError): # Handle potential issues if value isn't valid JSON or expected type
        logger.warning(f"Could not decode setting '{name}'. Returning default.")
        return default_value


def set_setting(name, value):
    """Helper function to set a setting value."""
    try:
        App_Settings.objects.update_or_create(
            name=name,
            defaults={'value': value}  # JSONField handles serialization
        )
    except Exception as e:
        logger.error(f"Error setting '{name}': {e}")