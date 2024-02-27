import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/tasks"]

def main():
    """Shows basic usage of the Google Calendar API and Google Tasks API.
    Prints the start and name of the next 10 events and tasks on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Build Google Calendar API service
        calendar_service = build("calendar", "v3", credentials=creds)
        
        # Build Google Tasks API service
        tasks_service = build("tasks", "v1", credentials=creds)

        # Get the current time
        now = datetime.datetime.utcnow()

        # Calculate the end time (10 days from now)
        end_time = now + datetime.timedelta(days=10)

        # Get upcoming events
        events_result = calendar_service.events().list(
            calendarId="primary",
            timeMin=now.isoformat() + "Z",  # 'Z' indicates UTC time
            timeMax=end_time.isoformat() + "Z",  # 'Z' indicates UTC time
            maxResults=10,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
        else:
            print("Upcoming events:")
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                print(start, event["summary"])

        # Get tasks
        tasks_result = tasks_service.tasks().list(
            tasklist="@default",
            maxResults=10
        ).execute()
        tasks = tasks_result.get("items", [])

        if not tasks:
            print("No upcoming tasks found.")
        else:
            print("Upcoming tasks:")
            for task in tasks:
                print(task["title"])

    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()
