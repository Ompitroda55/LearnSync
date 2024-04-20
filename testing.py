from datetime import datetime

# print("Hello World!")
# print(datetime.now().date())


from datetime import datetime, timedelta

def time_difference_to_string(start_time, end_time):
    time_diff = end_time - start_time

    # Calculate days, hours, and minutes
    days = time_diff.days
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    # Convert to string representation based on magnitude
    if days > 0:
        if hours == 0:
            return f"{days} days"
        elif hours == 1:
            return f"{days} days and 1 hour"
        else:
            return f"{days} days and {hours} hours"
    elif hours > 0:
        if minutes == 0:
            return f"{hours} hours"
        elif minutes == 1:
            return f"{hours} hours and 1 minute"
        else:
            return f"{hours} hours and {minutes} minutes"
    else:
        return f"{minutes} minutes"

# Example usage
start_time = datetime(2024, 4, 19, 0, 0, 0)
end_time = datetime.now()

time_str = time_difference_to_string(start_time, end_time)
print(datetime.now())
print(time_str)  # Output: 2 days and 4 hours and 30 minutes
