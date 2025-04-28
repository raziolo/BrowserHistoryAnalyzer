# frontend/templatetags/frontend_tags.py

from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Returns the URL-encoded query string for the current page,
    updating the parameters with any kwargs passed to the tag.

    Example usage:
    <a href="?{% param_replace page=1 %}">Page 1</a>
    <a href="?{% param_replace page=paginator.next_page_number sort='name' %}">Next Page</a>
    """
    query_params = context['request'].GET.copy() # Get a mutable copy of GET parameters

    # Update the parameters with the kwargs provided
    for key, value in kwargs.items():
        query_params[key] = str(value) # Ensure value is a string

    # Remove parameters that are set to empty string in kwargs (useful for clearing filters)
    # Or handle None values if needed. For pagination, usually just setting the page is enough.
    # Example: if value is None and key in query_params: del query_params[key]

    # Encode the parameters back into a query string
    # Use urlencode(safe='/') if you have path parameters mixed in, otherwise normal encode is fine
    return query_params.urlencode()