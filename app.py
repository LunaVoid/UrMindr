from flask import Flask, redirect, url_for, session, request, render_template_string
import os
import datetime
from flask import jsonify
from flask_cors import CORS
from google import genai
from google.genai import types
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # is this bad
app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)
client = genai.Client()

# --- Firebase Admin SDK Initialization ---
try:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"🔥 Error initializing Firebase Admin SDK: {e}")
# -----------------------------------------

# Middleware to verify Firebase ID token
@app.before_request
def verify_token():
    g.user = None
    id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    if id_token:
        try:
            decoded_token = auth.verify_id_token(id_token)
            g.user = decoded_token
        except Exception as e:
            print(f"🔥 Error verifying token: {e}")
            # Optionally, you could return a 401 Unauthorized response here
            # return jsonify({"error": "Unauthorized"}), 401
            pass # For now, we'll let unauthenticated requests through to public endpoints

def get_user_context(uid):
    # TODO: Fetch user-specific context from Firestore
    # For example, you could fetch the last 10 messages from a user's chat history.
    return f"This is the context for user {uid}."

# --- Chat History Functions ---

def start_or_get_chat(user_id, chat_id=None):
    """
    Starts a new chat in Firestore if no chat_id is provided,
    otherwise returns the provided chat_id.
    """
    db = firestore.client()
    user_chats_ref = db.collection('users').document(user_id).collection('chats')
    
    if chat_id:
        # TODO: Optionally, verify the chat_id exists before returning.
        return chat_id
    else:
        # Create a new chat document
        new_chat_ref = user_chats_ref.document()
        new_chat_ref.set({
            'startTime': datetime.datetime.now(datetime.timezone.utc),
            'messages': []
        })
        return new_chat_ref.id

def add_message_to_chat(user_id, chat_id, role, content):
    """
    Adds a message to a specific chat's 'messages' array in Firestore.
    """
    db = firestore.client()
    chat_ref = db.collection('users').document(user_id).collection('chats').document(chat_id)
    
    message = {
        'role': role,
        'content': content,
        'timestamp': datetime.datetime.now(datetime.timezone.utc)
    }
    
    # Atomically add the new message to the 'messages' array
    chat_ref.update({
        'messages': firestore.ArrayUnion([message])
    })

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

@app.route("/api/cal/events")
def events():
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

def handle_schedule_meeting(args):
    """Handles the logic for the 'schedule_meeting' tool."""
    creds = get_credentials()
    if not creds:
        # If no credentials, we need to initiate the OAuth flow
        auth_url = authorize_flow()
        return jsonify({
            "response": "I need to authorize with your Google Calendar first.",
            "authorization_url": auth_url
        }), 200

    try:
        # The model might not provide all arguments, so we use .get()
        topic = args.get('topic', 'Meeting')
        date = args.get('date')
        time = args.get('time')
        
        if not date or not time:
            return jsonify({"response": "I need a date and time to schedule the meeting. Quack."}), 200

        start_datetime_str = f"{date}T{time}"
        start_datetime = datetime.datetime.fromisoformat(start_datetime_str)
        end_datetime = start_datetime + datetime.timedelta(hours=1) # Assume 1-hour meetings

        event = create_event(creds, topic, start_datetime, end_datetime)
        return jsonify({"response": f"I've scheduled a meeting about '{topic}'. Quack.", "event": event}), 200

    except Exception as e:
        return jsonify({"error": f"Error creating event: {str(e)}"}), 500

def execute_function_call(function_call):
    """Executes the appropriate function based on the model's call."""
    if function_call.name == 'schedule_meeting':
        return handle_schedule_meeting(function_call.args)
    else:
        return jsonify({"error": f"Unknown function call: {function_call.name}"}), 400

def handle_gemini_response(response):
    """Processes the response from the Gemini model."""
    if response.candidates and response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        print(f"Function to call: {function_call.name}")
        print(f"Arguments: {function_call.args}")
        return execute_function_call(function_call)
    else:
        # No function call, just return the text response
        print("No function call found in the response.")
        print(response.text)
        return jsonify({"response": str(response.text) + " Quack."}), 200

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
    user_context = get_user_context(g.user['uid'])
    
    system_instructions = f"""You are a duck assistant that can schedule meetings. 
                             Always try to use the 'schedule_meeting' tool when appropriate and always end with a quack.
                             Here is some context about the user: {user_context}"""

    tools = types.Tool(function_declarations=[schedule_meeting_function])
    config = types.GenerateContentConfig(tools=[tools])

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[system_instructions, prompt],
            config=config,
        )
        return handle_gemini_response(response)
    except Exception as e:
        print(f"Error in /api/toolcall: {e}") # Log the error for debugging
        return jsonify({"error": str(e)}), 500




if __name__ == "__main__":
    app.run("localhost", 5000, debug=True)
