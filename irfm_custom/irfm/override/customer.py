import frappe
import pytz
from datetime import datetime, date


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
    # Prevent recursion using a flag (ensure it's not already being calculated)
    if doc.get('__is_calculating_time_difference', False):
        print("Recursion detected. Skipping calculation.")
        return
    
    # Set flag to indicate we're calculating the time difference
    doc.__is_calculating_time_difference = True
    print(f"Started calculating time difference for {doc.name}")

    try:
        # Get the current time in America/Toronto timezone
        toronto_tz = pytz.timezone('America/Toronto')
        toronto_time = datetime.now(toronto_tz).strftime('%H:%M:%S')  # Only time, no date
        print(f"Toronto Time (timezone-aware): {toronto_time}")

        # Get the current time in the custom time zone from the document (timezone-aware)
        custom_time_zone = doc.custom_time_zone  # Ensure this field exists in your doc
        custom_tz = pytz.timezone(custom_time_zone)
        custom_time = datetime.now(custom_tz).strftime('%H:%M:%S')  # Only time, no date
        print(f"Custom Time ({custom_time_zone}, timezone-aware): {custom_time}")

        # Calculate the time difference
        toronto_time_obj = datetime.strptime(toronto_time, '%H:%M:%S')  # Convert to datetime object for calculation
        custom_time_obj = datetime.strptime(custom_time, '%H:%M:%S')  # Convert to datetime object for calculation

        # Calculate the time difference
        time_difference = custom_time_obj - toronto_time_obj
        print(f"Time Difference in raw form: {time_difference}")

        # Print the time difference in seconds for debugging
        time_diff_in_seconds = time_difference.total_seconds()
        print(f"Time Difference in seconds: {time_diff_in_seconds}")

        # Convert the difference to hours and minutes
        hours = int(time_diff_in_seconds // 3600)
        minutes = int((time_diff_in_seconds % 3600) // 60)
        print(f"Calculated Time Difference: {hours} hours {minutes} minutes")

        # Store the result in the 'custom_time_difference' field
        doc.custom_time_difference = f"{hours} hours {minutes} minutes"
        doc.save()
        print(f"Saved time difference for {doc.name}: {doc.custom_time_difference}")

    finally:
        # Reset the flag after the method finishes
        doc.__is_calculating_time_difference = False
        print(f"Finished calculating time difference for {doc.name}")
