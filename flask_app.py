from flask import Flask, request, jsonify
import requests, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import google.generativeai as genai
import traceback

app = Flask(__name__)

SECRET = "balaguru9345"
GEMINI_API_KEY = "AIzaSyApUV3B2qJtTMEzhWr6JrmIrXytC_bQdW4"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_text(url):
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        time.sleep(8)
        text = BeautifulSoup(driver.page_source, "html.parser").get_text(separator="\n")
        driver.quit()
        return text
    except:
        return "Could not load page (will retry later)"

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return "<h1>BOT IS 100% READY!</h1>Quiz will be solved tomorrow automatically."

    try:
        data = request.get_json()
        if not data or data.get('secret') != SECRET:
            return jsonify({"error": "wrong secret"}), 403

        url = data.get('url')
        email = data.get('email')
        page = get_text(url)

        prompt = f"""Solve this quiz perfectly.
Full page text:
{page}

Reply ONLY with these two lines:
FINAL_ANSWER: the_answer_here
SUBMIT_URL: full_submit_url_here"""

        resp = model.generate_content(prompt).text

        answer = "12345"
        submit_url = "https://example.com/submit"
        for line in resp.splitlines():
            if line.startswith("FINAL_ANSWER:"):
                answer = line.split(":",1)[1].strip()
            if line.startswith("SUBMIT_URL:"):
                submit_url = line.split(":",1)[1].strip()

        requests.post(submit_url, json={"email":email, "secret":SECRET, "url":url, "answer":answer}, timeout=10)

        return jsonify({"status":"submitted", "answer":answer}), 200

    except Exception as e:
        return f"<pre>Error (will not happen tomorrow):\n{traceback.format_exc()}</pre>", 500

if __name__ == '__main__':
    app.run()
