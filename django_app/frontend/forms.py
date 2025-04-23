# forms.py
from django import forms


class ClassifierSettingsForm(forms.Form):
    days_to_analyze = forms.IntegerField(
        label="Analysis History (Days)",
        min_value=1,
        max_value=365,
        help_text="Number of days of history to analyze"
    )

    categories = forms.CharField(
        widget=forms.Textarea,
        help_text="Enter one category per line",
        label="Classification Categories"
    )

    temperature = forms.FloatField(
        min_value=0.0,
        max_value=2.0,
        step_size=0.1,
        help_text="Model creativity (0 = deterministic, 2 = creative)"
    )

    max_tokens = forms.IntegerField(
        min_value=100,
        max_value=2000,
        help_text="Maximum tokens per classification"
    )

    def clean_categories(self):
        categories = self.cleaned_data['categories'].split('\n')
        return [c.strip() for c in categories if c.strip()]