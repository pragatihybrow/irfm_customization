import frappe
import pytz
from datetime import datetime, date,time
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


# def calculate_time_difference_in_custom_timezone(doc, method):
#     if doc.get('__is_calculating_time_difference', False):
#         print("Recursion detected. Skipping calculation.")
#         return
    
#     doc.__is_calculating_time_difference = True
#     print(f"Started calculating time difference for {doc.name}")

#     try:
#         # Get the current time in UTC
#         now_utc = datetime.now(pytz.utc)

#         # Convert to respective time zones
#         toronto_tz = pytz.timezone('America/Toronto')
#         custom_tz = pytz.timezone(doc.custom_time_zone)

#         toronto_time = now_utc.astimezone(toronto_tz).time()  # Extract HH:MM:SS
#         custom_time = now_utc.astimezone(custom_tz).time()  # Extract HH:MM:SS

#         # Debugging prints
#         print(f"Toronto Time (HH:MM:SS): {toronto_time}")
#         print(f"Custom Time ({doc.custom_time_zone}, HH:MM:SS): {custom_time}")

#         # Convert times to timedelta
#         toronto_timedelta = timedelta(hours=toronto_time.hour, minutes=toronto_time.minute, seconds=toronto_time.second)
#         custom_timedelta = timedelta(hours=custom_time.hour, minutes=custom_time.minute, seconds=custom_time.second)

#         # Calculate time difference
#         time_difference_seconds = (custom_timedelta.total_seconds() - toronto_timedelta.total_seconds())

#         # Adjust to keep within -12 to +12 hour range
#         if time_difference_seconds < -12 * 3600:
#             time_difference_seconds += 24 * 3600
#         elif time_difference_seconds > 12 * 3600:
#             time_difference_seconds -= 24 * 3600

#         # Convert seconds to hours and minutes
#         hours = int(time_difference_seconds // 3600)
#         minutes = int((time_difference_seconds % 3600) // 60)

#         print(f"Calculated Time Difference: {hours} hours {minutes} minutes")

#         # Store the result
#         doc.custom_time_difference = f"{hours} hours {minutes} minutes"
#         doc.save()
#         print(f"Saved time difference for {doc.name}: {doc.custom_time_difference}")

#         # Adjust the custom_company_deadline_time_ based on the time difference
#         if doc.custom_company_deadline_time_:
#             # Convert custom_company_deadline_time_ from string (HH:MM:SS) to timedelta
#             deadline_time_str = doc.custom_company_deadline_time_
#             deadline_time = datetime.strptime(deadline_time_str, "%H:%M:%S").time()

#             # Convert deadline_time to timedelta
#             deadline_timedelta = timedelta(hours=deadline_time.hour, minutes=deadline_time.minute, seconds=deadline_time.second)

#             # Apply the time difference to the deadline
#             adjusted_deadline_timedelta = deadline_timedelta + timedelta(seconds=time_difference_seconds)

#             # Ensure the adjusted time stays within 24 hours
#             if adjusted_deadline_timedelta.days < 0:
#                 adjusted_deadline_timedelta += timedelta(days=1)
#             elif adjusted_deadline_timedelta.days > 0:
#                 adjusted_deadline_timedelta -= timedelta(days=1)

#             # Convert the adjusted timedelta back to time
#             adjusted_deadline = (datetime.min + adjusted_deadline_timedelta).time()

#             # Store the adjusted deadline time
#             doc.custom_deadline_time = adjusted_deadline
#             doc.save()
#             print(f"Adjusted custom_deadline_time for {doc.name}: {doc.custom_deadline_time}")

#     finally:
#         doc.__is_calculating_time_difference = False
#         print(f"Finished calculating time difference for {doc.name}")




def calculate_time_difference_in_custom_timezone(doc, method):
    if doc.get('__is_calculating_time_difference', False):
        print("Recursion detected. Skipping calculation.")
        return
    
    doc.__is_calculating_time_difference = True
    print(f"Started calculating time difference for {doc.name}")

    try:
        # Get the current time in UTC
        now_utc = datetime.now(pytz.utc)
        print(f"Current UTC Time: {now_utc}")

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

        # Debugging print
        print(f"Toronto Timedelta: {toronto_timedelta}")
        print(f"Custom Timedelta: {custom_timedelta}")

        # Calculate time difference
        time_difference_seconds = (custom_timedelta.total_seconds() - toronto_timedelta.total_seconds())
        print(f"Raw Time Difference in Seconds: {time_difference_seconds}")

        # Adjust to keep within -12 to +12 hour range
        if time_difference_seconds < -12 * 3600:
            time_difference_seconds += 24 * 3600
            print("Adjusted time difference: < -12 hours, wrapped around to 24 hours")
        elif time_difference_seconds > 12 * 3600:
            time_difference_seconds -= 24 * 3600
            print("Adjusted time difference: > 12 hours, wrapped around to 24 hours")

        # Convert seconds to hours and minutes
        hours = int(time_difference_seconds // 3600)
        minutes = int((time_difference_seconds % 3600) // 60)
        print(f"Calculated Time Difference: {hours} hours {minutes} minutes")

        # Store the result
        doc.custom_time_difference = f"{hours} hours {minutes} minutes"
        doc.save()
        print(f"Saved time difference for {doc.name}: {doc.custom_time_difference}")

        # Adjust the custom_company_deadline_time_ based on the time difference
        if doc.custom_company_deadline_time_:
            # Convert custom_company_deadline_time_ from string (HH:MM:SS) to timedelta
            deadline_time_str = doc.custom_company_deadline_time_
            print(f"Original custom_company_deadline_time_: {deadline_time_str}")

            deadline_time = datetime.strptime(deadline_time_str, "%H:%M:%S").time()
            print(f"Converted Deadline Time to Time object: {deadline_time}")

            # Convert deadline_time to timedelta for easier time manipulation
            deadline_timedelta = timedelta(hours=deadline_time.hour, minutes=deadline_time.minute, seconds=deadline_time.second)
            print(f"Converted Deadline Time to Timedelta: {deadline_timedelta}")

            # If time is ahead (positive difference), we add the difference
            if time_difference_seconds > 0:
                adjusted_deadline_timedelta = deadline_timedelta + timedelta(seconds=time_difference_seconds)
                print(f"Time is ahead, adding time difference: {adjusted_deadline_timedelta}")
            # If time is behind (negative difference), we subtract the difference
            else:
                adjusted_deadline_timedelta = deadline_timedelta - timedelta(seconds=abs(time_difference_seconds))
                print(f"Time is behind, subtracting time difference: {adjusted_deadline_timedelta}")

            # Ensure the adjusted time stays within 24 hours
            if adjusted_deadline_timedelta.days < 0:
                adjusted_deadline_timedelta += timedelta(days=1)
                print("Adjusted deadline: wrapped around to positive time")
            elif adjusted_deadline_timedelta.days > 0:
                adjusted_deadline_timedelta -= timedelta(days=1)
                print("Adjusted deadline: wrapped around to positive time")

            # Convert the adjusted timedelta back to time (HH:MM:SS)
            adjusted_deadline = (datetime.min + adjusted_deadline_timedelta).time()
            print(f"Final Adjusted Deadline Time: {adjusted_deadline}")

            # Store the adjusted deadline time
            doc.custom_deadline_time = adjusted_deadline
            doc.save()
            print(f"Saved Adjusted custom_deadline_time_: {doc.custom_deadline_time}")

    finally:
        doc.__is_calculating_time_difference = False
        print(f"Finished calculating time difference for {doc.name}")
