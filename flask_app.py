
# FINAL WORKING CODE - JUST PASTE THIS
from flask import Flask, request, jsonify
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import google.generativeai as genai

app = Flask(__name__)

# CHANGE ONLY THESE TWO LINES
SECRET = "balaguru2025secret"          # ← remember this exact word
GEMINI_API_KEY = "PUT_YOUR_REAL_GEMINI_KEY_HERE"   # ← paste your key here

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_page(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(7)
    html = driver.page_source
    driver.quit()
    return BeautifulSoup(html, "html.parser").get_text(separator="\n")

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return "<h1>Quiz Bot is LIVE!</h1>Ready for tomorrow's contest."

    data = request.get_json()
    if not data or data.get("secret") != SECRET:
        return jsonify({"error": "wrong secret"}), 403

    quiz_url = data.get("url")
    email = data.get("email")

    page_text = get_page(quiz_url)

    prompt = f"""You are the world's best data analyst.
Solve the quiz exactly. Here is the full page text:

{page_text}

Reply ONLY in this exact format (nothing else):

FINAL_ANSWER: <put the exact answer here>
SUBMIT_URL: <full submit url here>"""

    response = model.generate_content(prompt)
    reply = response.text

    answer = "12345"
    submit = "https://example.com/submit"
    for line in reply.splitlines():
        if line.startswith("FINAL_ANSWER:"):
            answer = line.replace("FINAL_ANSWER:", "").strip()
        if line.startswith("SUBMIT_URL:"):
            submit = line.replace("SUBMIT_URL:", "").strip()

    payload = {"email": email, "secret": SECRET, "url": quiz_url, "answer": answer}
    requests.post(submit, json=payload)

    return jsonify({"status": "submitted", "answer": answer}), 200

if __name__ == "__main__":
    app.run()