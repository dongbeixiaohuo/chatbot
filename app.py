# -*- coding: utf-8 -*-
import os
import requests
import re
import logging
logging.basicConfig(filename='flask.log', level=logging.DEBUG)
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from flask_cors import CORS
app = Flask(__name__)
CORS(app, origins=['https://www.huihe360.net'])

OPENAI_API_KEY = "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"
# 将此处替换为您的钉钉机器人Webhook地址
DINGDING_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=9ef971bc59f6af0e4f3b52c07b67f5c201df8dc6d9f401f65665fa4cf790419d"

@app.route("/")
def index():
    return render_template("index.html") #/tmp/Python-3.9.5/templates/index.html

@app.route("/ask", methods=["POST"])
def ask_question():
    question = request.json.get("question")
    client_ip = request.remote_addr
    try:
        response = get_chatgpt_response(question)
        with open("questions.txt", "a") as f:
            f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Client IP: {client_ip}\n")
            f.write(f"Question: {question}\n")
            f.write("-" * 50 + "\n")
        return jsonify({"response": response})
    except Exception as e:
        error = str(e)
        return jsonify({"error": error})

@app.route('/aichat', methods=['POST'])
def aichat():
    data = request.get_json()
    text = data.get('text', {}).get('content')

    if text:
        try:
            answer = get_chatgpt_response(text)
            send_to_dingding(answer)
        except Exception as e:
            error = str(e)
            send_to_dingding(f"Error: {error}")
    else:
        return "没有收到有效的消息", 400

    return "OK", 200
def format_answer(answer):
    parts = re.split(r'(\d+\.)', answer)
    formatted_answer = ''.join([f'\n{part.strip()}' if part.strip().endswith('.') else f' {part.strip()}' for part in parts]).strip()
    return formatted_answer

def get_chatgpt_response(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000,
        "temperature": 0.5
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    
    if response.status_code != 200:
        raise Exception(f"Error in ChatGPT API: {response.text}")
    
    answer = response.json()["choices"][0]["message"]["content"].strip()
    formatted_answer = format_answer(answer)
    return formatted_answer


def send_to_dingding(message):
    headers = {'Content-Type': 'application/json'}
    payload = {
        "msgtype": "text",
        "text": {
            "content": message
        }
    }

    response = requests.post(DINGDING_WEBHOOK, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        print("发送钉钉消息失败:", response.text)

if __name__ == "__main__":
     app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=('/var/www/html/9497562_huihe360.net_public.crt', '/var/www/html/9497562_huihe360.net.key'))
