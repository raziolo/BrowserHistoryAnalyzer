# frontend/filters.py
import django_filters
from .models import HistoryEvent
from django import forms
from django.db.models import Q # Keep Q import if needed later

class HistoryEventFilter(django_filters.FilterSet):
    # --- Generate choices explicitly ---

    # Get distinct, non-empty categories from the database
    distinct_categories = HistoryEvent.objects.exclude(category__isnull=True).exclude(category='') \
                          .order_by('category').values_list('category', flat=True).distinct()
    # Create the choices list (value, label)
    category_choices = [('', 'All Categories')] + [(cat, cat) for cat in distinct_categories]

    # Get distinct, non-empty browsers from the database
    distinct_browsers = HistoryEvent.objects.exclude(browser__isnull=True).exclude(browser='') \
                        .order_by('browser').values_list('browser', flat=True).distinct()
    # Create the choices list (value, label)
    browser_choices = [('', 'All Browsers')] + [(b, b) for b in distinct_browsers]

    # --- Define Filters using generated choices ---
    q = django_filters.CharFilter(
        method='search_filter',
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'Search Title, URL, Category...', 'class': 'input input-bordered input-sm w-full max-w-xs'})
    )

    category = django_filters.ChoiceFilter(
        choices=category_choices, # Use the explicitly built list
        widget=forms.Select(attrs={'class': 'select select-bordered select-sm'})
    )

    browser = django_filters.ChoiceFilter(
        choices=browser_choices, # Use the explicitly built list
        widget=forms.Select(attrs={'class': 'select select-bordered select-sm'})
    )

    class Meta:
        model = HistoryEvent
        fields = ['q', 'category', 'browser'] # Only fields used for explicit filters/search

    def search_filter(self, queryset, name, value):
        # Apply Q object search across multiple fields
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(url__icontains=value) |
                Q(category__icontains=value)
            )
        return queryset