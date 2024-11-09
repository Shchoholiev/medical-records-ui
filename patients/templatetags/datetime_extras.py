# patients/templatetags/datetime_extras.py

from django import template
from django.utils import timezone
from datetime import datetime
import pytz

register = template.Library()

@register.filter
def iso_to_local(value, date_format="%Y-%m-%d %H:%M:%S"):
    """
    Converts an ISO 8601 UTC date string to local time and formats it.
    :param value: The ISO date string to convert (e.g., "2023-10-27T18:24:15.425024+00:00").
    :param date_format: The format for displaying the date.
    :return: A string representing the local date in the specified format.
    """
    try:
        # Parse the ISO 8601 UTC date string
        utc_date = datetime.fromisoformat(value)
        if utc_date.tzinfo is None:
            utc_date = utc_date.replace(tzinfo=pytz.UTC)
        
        # Convert to local timezone
        local_date = utc_date.astimezone(timezone.get_current_timezone())
        
        # Format and return the local date
        return local_date.strftime(date_format)
    except (ValueError, TypeError) as e:
        # Return the original value if there's an error in conversion
        return value
