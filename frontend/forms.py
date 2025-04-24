# forms.py
from django import forms


# frontend/forms.py
from django import forms
import json

# frontend/forms.py
from django import forms
import json

class SettingsForm(forms.Form):
    days_to_analyze = forms.IntegerField(
        label="Days to Analyze",
        min_value=1,
        max_value=365,
        # initial=7, # Initial is now set in the view based on DB
        help_text="Number of past days of history to fetch and classify.",
        widget=forms.NumberInput(attrs={'class': 'input input-bordered w-full'})
    )
    temperature = forms.FloatField(
        label="LLM Temperature",
        min_value=0.0,
        max_value=2.0,
        # initial=0.1,
        help_text="Controls randomness in the classification (0.0=deterministic, 2.0=very random).",
        widget=forms.NumberInput(attrs={'step': '0.1', 'class': 'input input-bordered w-full'})
    )
    max_tokens = forms.IntegerField(
        label="LLM Max Tokens",
        min_value=50,
        max_value=8192, # Increased typical max
        # initial=1000,
        help_text="Maximum number of tokens the classification model can use per request.",
        widget=forms.NumberInput(attrs={'class': 'input input-bordered w-full'})
    )
    # New field for selecting the model
    current_model = forms.ChoiceField(
        label="Active Language Model",
        choices=[], # Choices will be set dynamically in __init__
        required=False, # Allow no selection if API fails or user doesn't choose
        help_text="Select the model to use for classification (fetched from LM Studio).",
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'})
    )
    categories = forms.CharField(
        label="Edit Categories", # Changed label slightly
        # initial="Social Media\nNews...",
        help_text="Enter one category per line.", # Simplified help text here
        widget=forms.Textarea(attrs={'class': 'textarea textarea-bordered h-48', 'placeholder': 'Enter one category per line'})
    )


    def __init__(self, *args, **kwargs):
        # Pop the custom argument before calling super().__init__
        model_choices = kwargs.pop('model_choices', [])
        super().__init__(*args, **kwargs)
        # Set the choices for the current_model field
        if model_choices:
            self.fields['current_model'].choices = model_choices
        else:
            # Provide a fallback if no choices are available (e.g., API error)
            self.fields['current_model'].choices = [('', '--- No models found or API error ---')]
            self.fields['current_model'].widget.attrs['disabled'] = True # Disable if no models


    def clean_categories(self):
        """
        Cleans the categories input string into a list of non-empty strings.
        """
        categories_string = self.cleaned_data.get('categories', '')
        categories_list = [
            line.strip() for line in categories_string.splitlines() if line.strip()
        ]
        if not categories_list:
            # Make categories optional if needed, or keep validation
            # raise forms.ValidationError("Please provide at least one category.")
            pass # Allow empty categories list if desired
        return categories_list # Return the list directly