from flask import Flask, redirect, url_for, session, request, render_template_string
import os
import datetime
from flask import jsonify
from flask_cors import CORS
from google import genai
from dotenv import load_dotenv
from google.genai import types
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # is this bad
app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)
client = genai.Client()


# Google OAuth settings
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.readonly"
]
CLIENT_SECRETS_FILE = "credentials.json"  
REDIRECT_URI = "http://localhost:5000/oauth2callback"  

def creds_to_dict(creds):
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }

def get_credentials():
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

def authorize_flow():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline", 
        include_granted_scopes="true"
    )
    session["state"] = state
    return authorization_url

def display_events(events):
    html = "<h2>Upcoming Events:</h2><ul>"
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        html += f"<li>{start}: {event.get('summary', 'No Title')}</li>"
    html += "</ul>"
    html += '<a href="/logout">Logout</a>'
    return html

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

def create_event(creds, name, start_time, end_time):
    service = build("calendar", "v3", credentials=creds)
    event = {
        "summary": name,
        "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
    }
    created_event = service.events().insert(calendarId="primary", body=event).execute()
    return jsonify({"event": created_event})


# Routes

# Calendar
@app.route("/api/cal/getevents")
def index():
    creds = get_credentials()
    if creds:
        events = fetch_events(creds) # GETS EVENTS-----------------------------
        html = display_events(events)
        return render_template_string(html)
    else:
        return '<a href="/authorize">Authorize Google Calendar</a>'


@app.route("/api/cal/authorize")
def authorize():
    session.clear()
    return redirect(authorize_flow())


@app.route("/api/cal/oauth2callback")
def oauth2callback():
    handle_oauth2_callback()
    return redirect(url_for("index"))


@app.route("/api/cal/logout")
def logout():
    session.pop("credentials", None)
    return redirect(url_for("index"))


# Optional: Route to create an event (example)
@app.route("/api/cal/create-event")
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


@app.route("/api/cal/auth-url", methods=["POST"])
def auth_url():
    id_token = request.json.get("idToken")
    if id_token:
        try:
            decoded = firebase_auth.verify_id_token(id_token)
            session["firebase_uid"] = decoded["uid"]
        except Exception as e:
            return jsonify({"error": "invalid id token"}), 401
    authorization_url = authorize_flow() 
    return jsonify({"authorization_url": authorization_url})

@app.route("/api/cal/events")
def events_route():
    creds = get_credentials()
    if not creds:
        return jsonify({"error": "Not authorized"}), 401
    
    events = fetch_events(creds)
    return jsonify({"events": events})


# Function Calling

schedule_meeting_function = {
    "name": "schedule_meeting",
    "description": "Schedules a meeting with specified attendees at a given time and date.",
    "parameters": {
        "type": "object",
        "properties": {
            "attendees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of people attending the meeting.",
            },
            "date": {
                "type": "string",
                "description": "Date of the meeting (e.g., '2024-07-29')",
            },
            "time": {
                "type": "string",
                "description": "Time of the meeting (e.g., '15:00')",
            },
            "topic": {
                "type": "string",
                "description": "The subject or topic of the meeting.",
            },
        },
        "required": ["attendees", "date", "time", "topic"],
    },
}

@app.route("/api/generate", methods=["POST"])
def generate():
    if not request.json or 'prompt' not in request.json:
        return jsonify({"error": "Missing 'prompt' in request body"}), 400
    
    prompt = request.json['prompt']
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        print(response.text)
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/toolcall", methods=["POST"])
def genwithtools():
    tools = types.Tool(function_declarations=[schedule_meeting_function])
    config = types.GenerateContentConfig(tools=[tools])

    if not request.json or 'prompt' not in request.json:
        return jsonify({"error": "Missing 'prompt' in request body"}), 400
    
    prompt = request.json['prompt']

    try:
        # "Schedule a meeting with Bob and Alice for 03/14/2025 at 10:00 AM about the Q3 planning."
        # Send request with function declarations
        response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
        )

        # Check for a function call
        if response.candidates[0].content.parts[0].function_call:
            function_call = response.candidates[0].content.parts[0].function_call
            print(f"Function to call: {function_call.name}")
            print(f"Arguments: {function_call.args}")
            return jsonify({"function": str(function_call.name)+" " + str(function_call.args)}), 200
        
        #  result = schedule_meeting(**function_call.args)
        else:
            print("No function call found in the response.")
            print(response.text)
            return jsonify({"function": "None Called"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == "__main__":
    app.run("localhost", 5000, debug=True)
