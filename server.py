from flask import Flask, request, Response
import requests
import os
import openai

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # לשימוש ב-Whisper

@app.route('/api/upload', methods=['POST'])
def upload_audio():
    try:
        if 'file' not in request.files:
            return Response("שגיאה: לא התקבל קובץ", mimetype="text/plain; charset=utf-8", status=400)
        
        audio_file = request.files['file']
        audio_path = "/tmp/input_audio.wav"
        audio_file.save(audio_path)

        # שימוש ב-Whisper להמרת קול לטקסט
        with open(audio_path, "rb") as f:
            whisper_response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                files={"file": f},
                data={"model": "whisper-1"}
            ).json()
        
        user_text = whisper_response.get("text", "").strip()
        if not user_text:
            return Response("לא זוהה דיבור, נסה שוב.", mimetype="text/plain; charset=utf-8")

        # שליחת השאלה ל-AI לקבלת תשובה
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        data = {"model": "openai/gpt-3.5-turbo", "messages": [{"role": "user", "content": user_text}]}

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
        response_json = response.json()

        ai_response = response_json["choices"][0]["message"]["content"].strip()
        return Response(ai_response, mimetype="text/plain; charset=utf-8")

    except Exception as e:
        return Response(f"שגיאה: {str(e)}", mimetype="text/plain; charset=utf-8", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
