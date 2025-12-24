from flask import Flask, jsonify, render_template
from threading import Thread
import logging
import json
import os
import random
import string

# 關閉 Flask 的啟動訊息
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# 存放機器人數據
bot_stats = {
    "guild_count": 0,
    "member_count": 0
}
bot_commands = {}

# === 新增：動態代碼資料庫 ===
CODE_DB_FILE = "xmas_dynamic.json"

def save_code_to_db(code, score):
    """將生成的代碼寫入 JSON 檔案"""
    data = {}
    if os.path.exists(CODE_DB_FILE):
        try:
            with open(CODE_DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except: pass
    
    data[code] = score
    
    with open(CODE_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/commands')
def commands():
    return render_template('commands.html', categories=bot_commands)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# === 新增：專屬照片頁面 ===
@app.route('/secret-photo')
def show_friend_photo():
    return render_template('photo.html')

# === 新增：生成隨機襪子代碼的 API ===
@app.route('/api/generate_sock')
def generate_sock():
    # 1. 隨機生成 6 碼亂數 (例如: A7B92F)
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    code = f"SOCK-{random_str}"
    
    # 2. 隨機決定分數 (可以設權重，讓高分比較難出)
    score = random.choices([10, 30, 50, 100], weights=[50, 30, 15, 5], k=1)[0]
    
    # 3. 存入資料庫讓機器人讀取
    save_code_to_db(code, score)
    
    # 4. 回傳給網頁
    return jsonify({"code": code, "score": score})

@app.route('/api/stats')
def get_stats():
    return jsonify(bot_stats)

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive(bot):
    server = Thread(target=run)
    server.start()
