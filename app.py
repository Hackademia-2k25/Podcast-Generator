from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from gtts import gTTS
import google.generativeai as genai
from googletrans import Translator

app = Flask(__name__)

UPLOAD_FOLDER = './uploads'
OUTPUT_FOLDER = './static/outputs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Configure Gemini API
GEMINI_API_KEY = 'AIzaSyA1FxMeqWr6hMPt09herdHCMIaZX1OL0k0'  # Replace with your actual Gemini API key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Ensure necessary folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def translate_text(text, target_language):
    try:
        translator = Translator()
        translated = translator.translate(text, dest=target_language)
        print(f"Translated text: {translated.text[:100]}...")
        return translated.text
    except Exception as e:
        print(f"Translation Error: {e}")
        return None

def generate_conversation_with_gemini(text):
    try:
        prompt = f"Create a conversational script based on this text:\n{text}"
        response = model.generate_content(prompt)
        print(f"Generated conversation script: {response.text[:100]}...")
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

def convert_to_audio(text, language):
    try:
        print(f"Generating audio for language: {language}, text: {text[:100]}...")
        tts = gTTS(text=text, lang=language, slow=False)
        audio_path = os.path.join(app.config['OUTPUT_FOLDER'], 'translated_podcast.mp3')
        tts.save(audio_path)
        print(f"Audio saved at: {audio_path}")
        return audio_path
    except Exception as e:
        print(f"Audio Conversion Error: {e}")
        return None

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_podcast():
    try:
        if 'file' not in request.files or 'language' not in request.form or 'style' not in request.form:
            return jsonify({"error": "Missing file, language, or style input"}), 400

        file = request.files['file']
        language = request.form['language']
        style = request.form['style']

        if file.filename == '':
            return jsonify({"error": "Empty file uploaded"}), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        with open(file_path, 'r') as f:
            document_text = f.read()

        if not document_text.strip():
            return jsonify({"error": "Uploaded file is empty"}), 400

        print(f"Document text: {document_text[:100]}...")

        conversation_script = generate_conversation_with_gemini(document_text)
        if not conversation_script:
            return jsonify({"error": "Failed to generate conversation script"}), 500

        if style == "brief":
            conversation_script = conversation_script[:500]
        elif style == "easy":
            conversation_script = f"Simple version:\n{conversation_script}"

        translated_text = translate_text(conversation_script, language)
        if not translated_text:
            return jsonify({"error": "Failed to translate text"}), 500

        audio_path = convert_to_audio(translated_text, language)
        if not audio_path:
            return jsonify({"error": "Failed to generate audio"}), 500

        return redirect(url_for('result'))
    except Exception as e:
        print(f"Error in generate_podcast: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/result', methods=['GET', 'POST'])
def result():
    podcast_file_url = url_for('static', filename='outputs/translated_podcast.mp3')

    if request.method == 'POST':
        feedback = request.form.get('feedback', '')
        print(f"User Feedback: {feedback}")
        return redirect(url_for('home'))

    return render_template('result.html', podcast_file_url=podcast_file_url)

if __name__ == '__main__':
    app.run(debug=True)
