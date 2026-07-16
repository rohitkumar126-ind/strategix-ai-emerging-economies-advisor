from flask import Flask
from dotenv import load_dotenv
import os
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)

@app.route('/')
def home():
    response = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents="Say hello and confirm you are working correctly."
    )
    return response.text

if __name__ == '__main__':
    app.run(debug=True)