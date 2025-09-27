from flask import Flask, redirect, url_for, session, request, render_template_string
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
import datetime
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Google OAuth settings
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.readonly"
]
CLIENT_SECRETS_FILE = "credentials.json"  
REDIRECT_URI = "http://localhost:5000/oauth2callback"  


def get_credentials():
    """Get credentials from session, return Credentials object or None"""
    if "credentials" in session:
        creds = Credentials(**session["credentials"])
        session["credentials"] = creds_to_dict(creds)  # refresh in session
        return creds
    return None


def fetch_events(creds, max_results=10):
    """Fetch upcoming events from Google Calendar"""
    service = build("calendar", "v3", credentials=creds)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])


def display_events(events):
    """Return HTML string for events list"""
    html = "<h2>Upcoming Events:</h2><ul>"
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        html += f"<li>{start}: {event.get('summary', 'No Title')}</li>"
    html += "</ul>"
    html += '<a href="/logout">Logout</a>'
    return html


def authorize_flow():
    """Start OAuth flow and return authorization URL"""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )
    session["state"] = state
    return authorization_url


def handle_oauth2_callback():
    state = session.get("state")  
    if not state: 
        return redirect(url_for("authorize"))
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI,
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session["credentials"] = creds_to_dict(creds)


def creds_to_dict(creds):
    """Convert Credentials object to dict for session storage"""
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }


def create_event(creds, summary, start_time, end_time):
    """Create a new event in Google Calendar"""
    service = build("calendar", "v3", credentials=creds)
    event = {
        "summary": summary,
        "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
    }
    created_event = service.events().insert(calendarId="primary", body=event).execute()
    return created_event


# Routes

@app.route("/")
def index():
    creds = get_credentials()
    if creds:
        events = fetch_events(creds)
        html = display_events(events)
        return render_template_string(html)
    else:
        return '<a href="/authorize">Authorize Google Calendar</a>'


@app.route("/authorize")
def authorize():
    session.clear()
    return redirect(authorize_flow())


@app.route("/oauth2callback")
def oauth2callback():
    handle_oauth2_callback()
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("credentials", None)
    return redirect(url_for("index"))


# Optional: Route to create an event (example)
@app.route("/create-event")
def create_event_route():
    creds = get_credentials()
    if not creds:
        return redirect(url_for("authorize"))
    
    # Example: create a dummy event 1 hour from now
    now = datetime.datetime.now(datetime.timezone.utc)
    start_time = now + datetime.timedelta(hours=1)
    end_time = start_time + datetime.timedelta(hours=1)
    create_event(creds, "Test Event", start_time, end_time)
    print ("event created")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run("localhost", 5000, debug=True)
