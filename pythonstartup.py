from flask import Flask, request, jsonify
import os
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai
from bs4 import BeautifulSoup
import pypdf2
import pandas as pd
import numpy as np

app = Flask(__name__)

# Set your secret (change 'your-secret-here' to a random string, like 'abc123secret', copy for form later)
SECRET = 'balaguru9345'

# Set your Gemini API key (paste the key you copied earlier)
genai.configure(api_key='AIzaSyApUV3B2qJtTMEzhWr6JrmIrXytC_bQdW4')

# Create Gemini model (free tier)
model = genai.GenerativeModel('gemini-1.5-flash')  # Free model, good for tasks

def solve_quiz(url, email, secret):
    # Step 1: Use headless browser to render the quiz page
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(5)  # Wait for JS to load
    html = driver.page_source
    task_text = BeautifulSoup(html, 'html.parser').get_text()  # Get clean text
    driver.quit()

    # Step 2: Use LLM as agent to solve the task. We'll loop for reasoning.
    # Define simple tools for LLM (function calling)
    tools = [
        {
            'name': 'download_file',
            'description': 'Download a file from URL and return content. For PDFs, extract text.',
            'parameters': {'url': 'string'}
        },
        {
            'name': 'execute_python',
            'description': 'Run Python code for analysis, like sum a column. Return result.',
            'parameters': {'code': 'string'}
        }
        # Add more if needed, like 'read_pdf_page'
    ]

    # Prompt LLM with task
    prompt = f"Solve this quiz task step by step. Use tools if needed. Task: {task_text}\nOutput the final answer and submit URL."
    response = model.generate_content(prompt)  # Simple call, add function calling loop for better agent

    # For better: Implement a loop where LLM calls tools
    # Example simple loop (expand if needed):
    answer = None
    submit_url = None
    while not answer:
        resp = model.generate_content(prompt)
        text = resp.text
        # Parse if tool call (manual for simple)
        if 'download' in text.lower():
            # Extract URL from text, download
            file_url = ...  # Parse
            content = requests.get(file_url).content
            if file_url.endswith('.pdf'):
                reader = pypdf2.PdfReader(content)
                page_text = reader.pages[1].extract_text()  # Example page 2
                prompt += f"\nPDF content: {page_text}"
        elif 'execute' in text.lower():
            # Extract code, exec safely (be careful, use exec in namespace)
            code = ...  # Parse
            local = {}
            exec(code, {}, local)
            result = local.get('result')
            prompt += f"\nCode result: {result}"
        else:
            # Assume final
            answer = text.split('answer:')[1].strip() if 'answer:' in text else text
            submit_url = text.split('post to ')[1].strip() if 'post to' in text else 'https://example.com/submit'  # Parse properly

    # Step 3: Submit the answer
    payload = {
        'email': email,
        'secret': secret,
        'url': url,
        'answer': answer
    }
    start_time = time.time()
    while time.time() - start_time < 180:  # 3 min
        resp = requests.post(submit_url, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            if data['correct']:
                if 'url' in data:
                    # Recurse for next
                    solve_quiz(data['url'], email, secret)
                break
            else:
                # Retry: Re-solve or adjust
                prompt += f"\nWrong: {data['reason']}. Try again."
        time.sleep(10)  # Wait before retry

@app.route('/', methods=['POST'])
def handle_request():
    data = request.get_json()
    if not data or data.get('secret') != SECRET:
        return jsonify({'error': 'Invalid secret'}), 403
    if 'email' not in data or 'url' not in data:
        return jsonify({'error': 'Invalid JSON'}), 400

    # Process in background? For simple, process here (assume quick)
    solve_quiz(data['url'], data['email'], SECRET)

    return jsonify({'status': 'processing'}), 200

if __name__ == '__main__':
    app.run()
