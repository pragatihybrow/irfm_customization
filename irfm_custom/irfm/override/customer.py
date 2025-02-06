import frappe
import pytz
from datetime import datetime, date
from datetime import datetime, timedelta


def check_box(doc, method):
    check_fields = [
        "custom_monday", "custom_tuesday", "custom_wednesday", 
        "custom_thursday", "custom_friday", "custom_saturday", "custom_sunday"
    ]

    # Find all checked fields
    checked_days = [field for field in check_fields if getattr(doc, field)]

    # If more than 2 are checked, uncheck the first checked one
    if len(checked_days) > 2:
        first_checked = checked_days[0]  # Get the first checked field
        setattr(doc, first_checked, 0)  # Uncheck it


def calculate_time_difference_in_custom_timezone(doc, method):
    if doc.get('__is_calculating_time_difference', False):
        print("Recursion detected. Skipping calculation.")
        return
    
    doc.__is_calculating_time_difference = True
    print(f"Started calculating time difference for {doc.name}")

    try:
        # Get the current time in UTC
        now_utc = datetime.now(pytz.utc)

        # Convert to respective time zones
        toronto_tz = pytz.timezone('America/Toronto')
        custom_tz = pytz.timezone(doc.custom_time_zone)

        toronto_time = now_utc.astimezone(toronto_tz).time()  # Extract HH:MM:SS
        custom_time = now_utc.astimezone(custom_tz).time()  # Extract HH:MM:SS

        # Debugging prints
        print(f"Toronto Time (HH:MM:SS): {toronto_time}")
        print(f"Custom Time ({doc.custom_time_zone}, HH:MM:SS): {custom_time}")

        # Convert times to timedelta
        toronto_timedelta = timedelta(hours=toronto_time.hour, minutes=toronto_time.minute, seconds=toronto_time.second)
        custom_timedelta = timedelta(hours=custom_time.hour, minutes=custom_time.minute, seconds=custom_time.second)

        # Calculate time difference
        time_difference_seconds = (custom_timedelta.total_seconds() - toronto_timedelta.total_seconds())

        # Adjust to keep within -12 to +12 hour range
        if time_difference_seconds < -12 * 3600:
            time_difference_seconds += 24 * 3600
        elif time_difference_seconds > 12 * 3600:
            time_difference_seconds -= 24 * 3600

        # Convert seconds to hours and minutes
        hours = int(time_difference_seconds // 3600)
        minutes = int((time_difference_seconds % 3600) // 60)

        print(f"Calculated Time Difference: {hours} hours {minutes} minutes")

        # Store the result
        doc.custom_time_difference = f"{hours} hours {minutes} minutes"
        doc.save()
        print(f"Saved time difference for {doc.name}: {doc.custom_time_difference}")

    finally:
        doc.__is_calculating_time_difference = False
        print(f"Finished calculating time difference for {doc.name}")
