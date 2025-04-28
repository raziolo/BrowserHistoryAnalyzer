from django.contrib import messages
from django.shortcuts import render, redirect

from frontend.forms import SettingsForm
from frontend.models import App_Settings
from frontend.utils.settings import get_setting, fetch_available_models


def settings_view(request):
    # Fetch available models and potential error message
    available_models, model_fetch_error = fetch_available_models()

    # Create choices for the form field (list of tuples)
    # Use model['id'] for both value and display text
    model_choices = [('', '--- Select a Model ---')] # Add a default empty choice
    model_choices.extend((model['id'], model['id']) for model in available_models)

    # Define defaults
    defaults = {
        'days_to_analyze': 7,
        'temperature': 0.1,
        'max_tokens': 1000,
        'categories': [
            "Social Media", "News", "Technology", "Shopping", "Education"
        ],
        'current_model': None # Default for the new setting
    }

    if request.method == 'POST':
        # Pass dynamic choices to the form during POST validation
        form = SettingsForm(request.POST, model_choices=model_choices)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            categories_list = cleaned_data['categories'] # Already a list

            # Save settings using update_or_create
            App_Settings.objects.update_or_create(
                name='days_to_analyze',
                defaults={'value': cleaned_data['days_to_analyze']}
            )
            App_Settings.objects.update_or_create(
                name='temperature',
                defaults={'value': cleaned_data['temperature']}
            )
            App_Settings.objects.update_or_create(
                name='max_tokens',
                defaults={'value': cleaned_data['max_tokens']}
            )
            # Store the categories list directly as JSON
            App_Settings.objects.update_or_create(
                name='categories',
                defaults={'value': categories_list}
            )
            # Update classification_parameters based on categories
            classification_params = {
                "categories": categories_list,
                "Other": False # Or derive as needed
            }
            App_Settings.objects.update_or_create(
                name='classification_parameters',
                defaults={'value': classification_params}
            )
            # Save the selected model
            App_Settings.objects.update_or_create(
                name='current_model',
                defaults={'value': cleaned_data['current_model']} # Store the selected model ID
            )

            messages.success(request, 'Settings updated successfully!')
            return redirect('settings') # Use your actual URL name
        else:
            # Form is invalid, add error messages if needed (e.g., API error)
             if model_fetch_error:
                 messages.error(request, f"Could not refresh model list: {model_fetch_error}")

    else: # GET Request
        # Load initial data from the database
        initial_data = {
            'days_to_analyze': get_setting('days_to_analyze', defaults['days_to_analyze']),
            'temperature': get_setting('temperature', defaults['temperature']),
            'max_tokens': get_setting('max_tokens', defaults['max_tokens']),
            'current_model': get_setting('current_model', defaults['current_model']), # Load current model
        }
        current_categories_list = get_setting('categories', defaults['categories'])
        if isinstance(current_categories_list, list):
             initial_data['categories'] = "\n".join(current_categories_list)
        else:
             initial_data['categories'] = "\n".join(defaults['categories']) # Fallback

        # Pass dynamic choices AND initial data to the form for GET
        form = SettingsForm(initial=initial_data, model_choices=model_choices)

        # Display error message if model fetching failed on GET
        if model_fetch_error:
            messages.warning(request, f"Could not fetch model list: {model_fetch_error}")


    # Fetch current categories again for bubble display
    current_categories_for_bubbles = get_setting('categories', defaults['categories'])
    if not isinstance(current_categories_for_bubbles, list):
        current_categories_for_bubbles = []

    context = {
        'form': form,
        'current_categories': current_categories_for_bubbles,
        'model_fetch_error': model_fetch_error # Pass error to template if needed for specific UI
    }
    return render(request, 'frontend/settings.html', context)


