from flask import Flask, request, jsonify
from flask_cors import CORS


load_dotenv()

app = Flask(__name__)
CORS(app) 
client = genai.Client()

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

    



