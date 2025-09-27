from flask import Flask, redirect, url_for, session, request
from flask import render_template_string
import os
import datetime
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Google OAuth settings
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CLIENT_SECRETS_FILE = "credentials.json"  

# downloaded from Google Cloud

# Replace with your web app URL
REDIRECT_URI = "http://localhost:5000/oauth2callback"


@app.route("/")
def index():
    if "credentials" in session:
        creds = Credentials(**session["credentials"])
        service = build("calendar", "v3", credentials=creds)

        # Get the next 10 events
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        # Save credentials back to session in case they were refreshed
        session["credentials"] = creds_to_dict(creds)

        # Render events
        html = "<h2>Upcoming 10 events:</h2><ul>"
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            html += f"<li>{start}: {event.get('summary', 'No Title')}</li>"
        html += "</ul>"
        html += '<a href="/logout">Logout</a>'
        return render_template_string(html)
    else:
        return '<a href="/authorize">Authorize Google Calendar</a>'


@app.route("/authorize")
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )
    session["state"] = state
    return redirect(authorization_url)


@app.route("/oauth2callback")
def oauth2callback():
    state = session["state"]
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI,
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session["credentials"] = creds_to_dict(creds)
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("credentials", None)
    return redirect(url_for("index"))


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


if __name__ == "__main__":
    app.run("localhost", 5000, debug=True)
