# frontend/analytics.py
from typing import List, Dict

from django.db.models import Count, F, Sum, Min, Max
# If using DateTimeField and PostgreSQL/MySQL, you might use ExtractWeekDay
# from django.db.models.functions import ExtractWeekDay
from datetime import datetime, timedelta
from urllib.parse import urlparse
import pandas as pd # Still optional, but useful for complex date handling
from collections import Counter # Useful for counting days

from backupManager.helpers import get_oldest_entry_in_backups
from frontend.models import HistoryEvent


def get_domain(url):
    """Extracts the domain name from a URL."""
    try:
        return urlparse(url).netloc.replace('www.', '')
    except:
        return "Invalid URL"

def calculate_dashboard_analytics(queryset):
    """
    Calculates various analytics metrics from a HistoryEvent queryset.
    """
    analytics_data = {
        # --- Existing KPIs ---
        'total_visits': 0,
        'unique_urls': 0,
        'unique_domains': 0,
        'category_distribution': {},
        'browser_distribution': {},
        'visit_trend': [],
        'top_domains': [],
        'activity_by_hour': {},
        'total_visit_count_sum': 0,
        'first_visit_date': None,
        'last_visit_date': None,
        # --- NEW Pattern/Prediction KPIs & Data ---
        'most_active_day': None,        # String name of the day
        'most_active_day_entries_count': 0, # Count of entries for that day
        'activity_by_day_of_week': [], # List of {'day': 'Mon', 'count': N}
        'most_probable_category': None, # String name of category
        'most_probable_category_perc': 0.0, # Percentage
        'category_probabilities': [],   # List of {'category': 'Tech', 'perc': P, 'count': N}
        'dominant_browser': None, # Most common browser
        'dominant_browser_perc' : 0.0, # Percentage of total visits
        # --- Data Coverage ---
        'dates_match': False,
        'oldest_database_entry_date' : None,
        'oldest_classified_entry_date' : None,
    }

    if not queryset.exists():
        return analytics_data

    total_visits = queryset.count() # Calculate total visits once
    analytics_data['total_visits'] = total_visits

    # --- Basic KPIs ---
    analytics_data['unique_urls'] = queryset.values('url').distinct().count()
    total_vc_agg = queryset.aggregate(total_vc=Sum('visit_count'))
    analytics_data['total_visit_count_sum'] = total_vc_agg.get('total_vc', 0) or 0

    date_agg = queryset.aggregate(
        min_date=Min('last_visit'),
        max_date=Max('last_visit')
    )
    try:
        analytics_data['first_visit_date'] = datetime.strptime(date_agg['min_date'][:19], '%Y-%m-%d %H:%M:%S') if date_agg.get('min_date') else None
        analytics_data['last_visit_date'] = datetime.strptime(date_agg['max_date'][:19], '%Y-%m-%d %H:%M:%S') if date_agg.get('max_date') else None
    except (ValueError, TypeError):
        analytics_data['first_visit_date'] = None
        analytics_data['last_visit_date'] = None

    # --- Distributions ---
    category_counts = queryset.values('category').annotate(count=Count('id')).order_by('-count')
    analytics_data['category_distribution'] = {item['category']: item['count'] for item in category_counts}

    browser_counts = queryset.values('browser').annotate(count=Count('id')).order_by('-count')
    analytics_data['browser_distribution'] = {item['browser']: item['count'] for item in browser_counts}

    # --- Top Domains ---
    domain_counts = {}
    for url in queryset.values_list('url', flat=True).distinct():
        domain = get_domain(url)
        if domain != "Invalid URL" and domain:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
    analytics_data['unique_domains'] = len(domain_counts)
    sorted_domains = sorted(domain_counts.items(), key=lambda item: item[1], reverse=True)
    analytics_data['top_domains'] = sorted_domains[:10]

    # --- Visit Trend (Daily) & Day of Week Analysis ---
    # Use Python's datetime for reliable day extraction from text dates
    daily_counts = Counter()
    day_of_week_counts = Counter() # 0=Mon, 1=Tue, ..., 6=Sun
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    date_data = queryset.values_list('last_visit', flat=True)
    valid_dates_processed = 0
    for date_str in date_data:
        try:
            # Use first 10 chars for date, first 19 for datetime
            dt_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
            dt_full = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')

            # Daily Trend Data
            day_str = dt_date.strftime('%Y-%m-%d')
            daily_counts[day_str] += 1

            # Day of Week Data
            day_of_week_counts[dt_full.weekday()] += 1 # Monday is 0
            valid_dates_processed += 1
        except (ValueError, TypeError):
            continue # Skip invalid date strings

    # Format Daily Trend
    sorted_days = sorted(daily_counts.items())
    analytics_data['visit_trend'] = [{'date': day, 'count': count} for day, count in sorted_days]

    # Format Day of Week & Find Most Active
    if valid_dates_processed > 0:
        # Prepare data for chart (ensure all days are present, even if count is 0)
        analytics_data['activity_by_day_of_week'] = [
            {'day': day_names[i], 'count': day_of_week_counts.get(i, 0)}
            for i in range(7) # 0 through 6
        ]
        # Find most active day
        if day_of_week_counts:
            most_active_day_num = max(day_of_week_counts, key=day_of_week_counts.get)
            analytics_data['most_active_day'] = day_names[most_active_day_num]
            analytics_data['most_active_day_entries_count'] = day_of_week_counts[most_active_day_num]
    else:
         analytics_data['activity_by_day_of_week'] = [{'day': name, 'count': 0} for name in day_names]


    # --- Activity by Hour ---
    hourly_counts = Counter()
    valid_times_processed = 0
    for time_str in date_data: # Reuse fetched date strings
         try:
             dt = datetime.strptime(time_str[:19], '%Y-%m-%d %H:%M:%S')
             hourly_counts[dt.hour] += 1
             valid_times_processed += 1
         except (ValueError, TypeError):
             continue
    if valid_times_processed > 0:
        analytics_data['activity_by_hour'] = [{'hour': h, 'count': hourly_counts.get(h, 0)} for h in range(24)]
    else:
        analytics_data['activity_by_hour'] = [{'hour': h, 'count': 0} for h in range(24)]


    # --- Category Probabilities & Most Probable ---
    if total_visits > 0 and analytics_data['category_distribution']:
        category_probs = []
        max_prob = 0.0
        most_prob_cat = None
        most_prob_perc = 0.0

        # Sort categories by count (already done by category_counts query)
        sorted_categories = sorted(analytics_data['category_distribution'].items(), key=lambda item: item[1], reverse=True)

        for category, count in sorted_categories:
            probability = (count / total_visits) * 100
            category_probs.append({'category': category, 'perc': round(probability, 2), 'count': count})
            if probability > max_prob:
                max_prob = probability
                most_prob_cat = category
                most_prob_perc = round(probability, 2)

        analytics_data['category_probabilities'] = category_probs[:10] # Show top 10 probabilities
        analytics_data['most_probable_category'] = most_prob_cat
        analytics_data['most_probable_category_perc'] = most_prob_perc

    # --- Dominant Browser ---
    if total_visits > 0:
        browser_counts = analytics_data['browser_distribution']
        dominant_browser = max(browser_counts, key=browser_counts.get)
        dominant_browser_count = browser_counts[dominant_browser]
        dominant_browser_perc = (dominant_browser_count / total_visits) * 100

        analytics_data['dominant_browser'] = str(dominant_browser)[0].upper() + str(dominant_browser)[1:]
        analytics_data['dominant_browser_perc'] = round(dominant_browser_perc, 2)
    else:
        analytics_data['dominant_browser'] = None
        analytics_data['dominant_browser_perc'] = 0

    # --- Data Coverage ---
    # Check if the first and last visit dates match the database entries
    oldest_classified_entry_date_str = queryset.aggregate(Min('last_visit'))['last_visit__min']
    oldest_classified_entry_date_obj = datetime.strptime(oldest_classified_entry_date_str, '%Y-%m-%d %H:%M:%S')
    oldest_backup_entry_date = get_oldest_entry_in_backups()

    print(f"Oldest classified entry date: {oldest_classified_entry_date_str}")
    print(f"Oldest backup entry date: {oldest_backup_entry_date}")

    analytics_data['dates_match'] = oldest_classified_entry_date_obj == oldest_backup_entry_date
    analytics_data['oldest_classified_entry_date'] = oldest_classified_entry_date_obj
    analytics_data['oldest_backups_entry_date'] = oldest_backup_entry_date

    return analytics_data

def get_category_distribution(browser: str) -> Dict[str, int]:
    """
    Counts history entries per category for a given browser.
    Excludes entries with None or empty string categories.
    """
    qs = HistoryEvent.objects.filter(browser=browser.lower()) \
        .exclude(category__isnull=True) \
        .exclude(category='') \
        .values('category') \
        .annotate(count=Count('id')) \
        .order_by('-count') # Order by count descending

    # Create the dictionary safely, skipping potential None keys if exclude didn't catch them
    # (Though exclude should handle None)
    distribution = {
        item['category']: item['count']
        for item in qs if item.get('category') is not None
    }
    return distribution


def get_daily_visits(browser: str) -> List[Dict]:
    """
    Counts history entries per day for a given browser by processing dates in Python.
    """
    # Fetch only the last_visit strings for the specified browser
    visit_dates_str = HistoryEvent.objects.filter(browser=browser.lower()).values_list('last_visit', flat=True)

    daily_counts = Counter()

    for date_str in visit_dates_str:
        if not date_str: # Skip None or empty strings
            continue
        try:
            # Extract only the date part 'YYYY-MM-DD' assuming this format
            # Adjust slicing/parsing if your format is different
            day_part = date_str[:10]
            # Optional: Validate the format if needed
            # datetime.strptime(day_part, '%Y-%m-%d')
            daily_counts[day_part] += 1
        except (ValueError, TypeError, IndexError):
            # Log warning about bad date format if necessary
            # logger.warning(f"Could not parse date string: {date_str}")
            continue # Skip malformed date strings

    # Convert the Counter object to the desired list of dictionaries format, sorted by date
    result = [{'day': day, 'count': count} for day, count in sorted(daily_counts.items())]
    return result


from datetime import datetime
from typing import List, Dict # Ensure these are imported
from .models import HistoryEvent

def get_recent_history(browser: str, limit: int = 20) -> List[Dict]:
    """
    Gets the most recent history entries for a browser, sorted chronologically in Python.
    """
    # Fetch relevant fields. Fetch slightly more than limit initially if possible,
    # as DB ordering is unreliable. If performance is critical and IDs correlate
    # perfectly with time, ordering by '-id' in DB might be an alternative.
    # For guaranteed correctness with text dates, Python sort is better.
    # Let's fetch a bit more to increase chance of getting the true latest.
    fetch_limit = limit * 2
    initial_qs = HistoryEvent.objects.filter(
                    browser=browser.lower()
                        ).order_by(
                            '-id'
                                ).values(
                                    'url', 'title', 'category', 'last_visit', 'visit_count')[:fetch_limit]

    history_list = list(initial_qs)

    # Define a helper function to parse dates robustly
    def parse_visit_date(item):
        raw_date = item.get('last_visit')
        if not raw_date:
            return datetime.min # Assign very old date for sorting Nones last
        try:
            # Adapt the format string ('%Y-%m-%d %H:%M:%S') if needed
            # Taking first 19 chars assumes format like 'YYYY-MM-DD HH:MM:SS.microseconds'
            return datetime.strptime(raw_date[:19], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError, IndexError):
            # logger.warning(f"Could not parse date string for sorting: {raw_date}")
            return datetime.min # Assign very old date on error

    # Sort the fetched list in Python based on the parsed date, descending (most recent first)
    history_list.sort(key=parse_visit_date, reverse=True)

    # Return only the requested number of items
    return history_list[:limit]