import os
import google.genai as genai

# Configure the API key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model
model = genai.GenerativeModel('gemini-pro')

def generate_text(prompt):
    """Generates text using the Gemini model."""
    response = model.generate_content(prompt)
    return response.text

if __name__ == "__main__":
    # Example usage
    prompt = "Explain how AI works in a few words"
    response_text = generate_text(prompt)
    print(response_text)