from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes
client = genai.Client()

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

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



