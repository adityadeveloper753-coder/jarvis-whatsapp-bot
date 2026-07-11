import os
from flask import Flask, request, jsonify
import google.generativeai as genai
from database_manager import JARVISDatabase

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

app = Flask(__name__)
db = JARVISDatabase()

# API Key config
API_KEY = os.environ.get("GEMINI_API_KEY") or "PLACEHOLDER_DO_NOT_PASTE_REAL_KEY_HERE"
genai.configure(api_key=API_KEY)

# AI Model setup - Asli naam lag gaya!
model = genai.GenerativeModel('gemini-2.5-flash')

@app.route('/', methods=['GET'])
def home():
    return "J.A.R.V.I.S. WhatsApp Engine is Syncing with Core Database... ONLINE! 🚀"

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    data = request.json
    
    sender = data.get("query", {}).get("sender", "").strip()
    message = data.get("query", {}).get("message", "").strip()
    
    print(f"\n[INCOMING WHATSAPP] From: {sender} | Msg: {message}")
    
    # 1. BLOCKLIST CHECK (Hamare SQLite database se)
    if db.is_number_blocked(sender):
        print(f"[BYPASS ENFORCED] Ignoring {sender}. No AI reply.")
        return jsonify({"replies": []})
        
    # 2. GENERATE PERSONALIZED JARVIS REPLY
    try:
        fav_lang = db.get_preference("language") or "Hinglish"
        fav_subj = db.get_preference("favorite_subject") or "Cybersecurity"
        
        prompt = f"""
        You are J.A.R.V.I.S., a highly advanced AI assistant.
        Respond to this WhatsApp message in a very short, friendly, and smart way.
        Tone: Conversational {fav_lang} (Mix of Hindi and English like a real chat).
        User Message: "{message}"
        """
        
        response = model.generate_content(prompt)
        jarvis_reply = response.text.replace("**", "").replace("*", "").strip()
        
        db.save_chat(f"WA_{sender}", message)
        db.save_chat("JARVIS_WA", jarvis_reply)
        
        # 🔥 YE LINE ADD KAR DI GAYI HAI TAASI BINA ERROR KE REPLY WHATSAPP PAR JAYE 🔥
        return jsonify({"replies": [{"message": jarvis_reply}]})
        
    except Exception as e:
        # Ye line hume batayegi ki asli error kahan aa raha hai
        print(f"❌ JARVIS CRASHED DUE TO: {e}")
        return jsonify({"replies": [{"message": "Sir, J.A.R.V.I.S. here. Mere system cores abhi ek priority update par hain. Main aapse thodi der mein baat karta hoon!"}]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)