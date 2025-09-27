from dotenv import load_dotenv
load_dotenv()

from flask import Flask, redirect, url_for, session, request, render_template_string, jsonify, g
import os
import datetime
from flask_cors import CORS
from google import genai
from google.genai import types
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import requests

import firebase_admin
from firebase_admin import credentials, auth, firestore

# --- Firebase Admin SDK Initialization ---
try:
    cred = credentials.Certificate("hackgt2025-firebase-adminsdk-fbsvc-1c9237b900.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"🔥 Error initializing Firebase Admin SDK: {e}")
# -----------------------------------------

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # DANGER: This is for local development only. Remove in production.
app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)
client = genai.Client()



# Middleware to verify Firebase ID token
@app.before_request
def verify_token():
    g.user = None
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        id_token = auth_header.split('Bearer ')[1]
        try:
            decoded_token = auth.verify_id_token(id_token)
            g.user = decoded_token
        except Exception as e:
            print(f"🔥 Error verifying token: {e}")

def get_user_context(uid):
    # TODO: Fetch user-specific context from Firestore
    return f"This is the context for user {uid}."

# --- Chat History Functions ---
def start_or_get_chat(user_id, chat_id=None):
    """
    Starts a new chat in Firestore if no chat_id is provided,
    otherwise returns the provided chat_id.
    """
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

# Direct Google Calendar API calls
def fetch_events_direct(access_token, max_results=15):
    """Direct API call to Google Calendar"""
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "maxResults": max_results,
        "orderBy": "startTime",
        "singleEvents": "true",
        "timeMin": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        print(f"Calendar API error: {response.status_code} - {response.text}")
        return []

def create_event_direct(access_token, name, start_time, end_time):
    """Direct API call to create calendar event"""
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
def get_user_chats(user_id):
    """
    Fetches all chat IDs and their basic information for a given user.
    """
    user_chats_ref = db.collection('users').document(user_id).collection('chats')
    chats = {}
    for chat_doc in user_chats_ref.stream():
        chats[chat_doc.id] = chat_doc.to_dict()
    return chats

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
    return created_event


# Routes
@app.route("/api/cal/events", methods=["POST"])
def get_events():
    """Get calendar events using access token from request"""
    if not request.json or 'accessToken' not in request.json:
        return jsonify({"error": "Missing accessToken in request body"}), 400
    
    access_token = request.json['accessToken']
    events = fetch_events_direct(access_token)
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
        "required": ["date", "time", "topic"],
    },
}

get_time_function = {
    "name": "get_time",
    "description": "Gets the current user's time",
    "parameters": {
        "type": "object",
        "properties": {
        },
        "required": [],
    },
}

def handle_schedule_meeting(args):
    """Handles the logic for the 'schedule_meeting' tool and returns a dictionary."""
    creds = get_credentials()
    if not creds:
        # If no credentials, we need to initiate the OAuth flow
        auth_url = authorize_flow()
        return {
            "response": "I need to authorize with your Google Calendar first.",
            "authorization_url": auth_url
        }

    try:
        print("scheduling meeting")
        topic = args.get('topic', 'Meeting')
        date = args.get('date')
        time = args.get('time')
        
        if not date or not time:
            return {"response": "I need a date and time to schedule the meeting. Quack."}

        start_datetime_str = f"{date}T{time}"
        start_datetime = datetime.datetime.fromisoformat(start_datetime_str)
        end_datetime = start_datetime + datetime.timedelta(hours=1) # Assume 1-hour meetings

        event = create_event(creds, topic, start_datetime, end_datetime)
        return {"response": f"I've scheduled a meeting about '{topic}'. Quack.", "event": event}

    except Exception as e:
        return jsonify({"error": f"Error creating event: {str(e)}"}), 500

def execute_function_call(function_call):
    """Executes the appropriate function based on the model's call and returns a dictionary."""
    if function_call.name == 'schedule_meeting':
        return handle_schedule_meeting(function_call.args)
    else:
        return jsonify({"error": f"Unknown function call: {function_call.name}"}), 400

def handle_gemini_response(response):
    """Processes the response from the Gemini model and returns a dictionary."""
    if response.candidates and response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        print(f"Function to call: {function_call.name}")
        print(f"Arguments: {function_call.args}")
        return execute_function_call(function_call)
    else:
        print("No function call found in the response.")
        print(response.text)
        return {"response": str(response.text) + " Quack."}

@app.route("/api/generate", methods=["POST"])
def generate():
    if not request.json or 'prompt' not in request.json:
        return jsonify({"error": "Missing 'prompt' in request body"}), 400
    
    prompt = request.json['prompt']
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/toolcall", methods=["POST"])
def genwithtools():
    if not g.user:
        return jsonify({"error": "Unauthorized"}), 401

    if not request.json or 'prompt' not in request.json:
        return jsonify({"error": "Missing 'prompt' in request body"}), 400

    user_id = g.user['uid']
    prompt = request.json['prompt']
    chat_id = request.json.get('chat_id') # Optional chat_id from client

    try:
        # Start a new chat or get the existing one
        active_chat_id = start_or_get_chat(user_id, chat_id)

        # Save user's message
        add_message_to_chat(user_id, active_chat_id, 'user', prompt)

        user_context = get_user_context(user_id)
        
        system_instructions = f"""You are a duck assistant that can schedule meetings. 
                                 Always try to use the 'schedule_meeting' tool when appropriate and always end with a quack.
                                 You should always consider the entire conversation history provided to generate your response.
                                 Here is some context about the user: {user_context}"""

        tools = types.Tool(function_declarations=[schedule_meeting_function])
        config = types.GenerateContentConfig(tools=[tools])

        # Get the history of the current chat to provide context to the model
        chat_ref = firestore.client().collection('users').document(user_id).collection('chats').document(active_chat_id)
        chat_history_snap = chat_ref.get()
        chat_history = chat_history_snap.to_dict().get('messages', [])

        # The 'contents' argument should be a list of alternating user/model messages
        # We add the system instructions first
        contents = [system_instructions]
        # Then add the existing chat history
        for message in chat_history:
            role = 'user' if message['role'] == 'user' else 'model'
            contents.append({'role': role, 'parts': [{'text': message['content']}]})
        # Finally, add the current user prompt
        contents.append({'role': 'user', 'parts': [{'text': prompt}]})


        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )

        # Process and save the agent's response
        agent_response_data = handle_gemini_response(response)
        agent_message = agent_response_data.get('response', '')

        add_message_to_chat(user_id, active_chat_id, 'agent', agent_message)

        # Add the chat_id to the response for the client
        agent_response_data['chat_id'] = active_chat_id

        return jsonify(agent_response_data)

    except Exception as e:
        print(f"Error in /api/toolcall: {e}")  # Log the error for debugging
        return jsonify({"error": str(e)}), 500

@app.route('/get_user_chats', methods=['GET'])
def get_user_chats_route():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    chats = get_user_chats(user_id)
    return jsonify(chats), 200

@app.route('/get_all_user_chats', methods=['GET'])
def get_all_user_chats_route():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    try:
        chats_data = {}
        chats = get_user_chats(user_id)
        for chat_id, chat_info in chats.items():
            # Retrieve the chat document to get the messages array
            chat_doc_ref = db.collection('users').document(user_id).collection('chats').document(chat_id)
            chat_doc = chat_doc_ref.get()
            
            messages = []
            if chat_doc.exists and 'messages' in chat_doc.to_dict():
                messages = chat_doc.to_dict()['messages']
            
            print(f"  Messages for chat {chat_id}: {messages}") # Debug print
            chats_data[chat_id] = messages
        
        print(f"All chats for user {user_id}:")
        for chat_id, messages in chats_data.items():
            print(f"  Chat ID: {chat_id}")
            for msg in messages:
                print(f"    - {msg.get('sender')}: {msg.get('text')}")
        
        return jsonify(chats_data), 200
    except Exception as e:
        print(f"Error fetching all user chats for user {user_id}: {e}")
        return jsonify({"error": str(e)}), 500




if __name__ == "__main__":
    app.run("localhost", 5000, debug=True, use_reloader=False)