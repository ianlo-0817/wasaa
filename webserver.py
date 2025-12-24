from flask import Flask, jsonify, render_template, send_from_directory
from threading import Thread
import logging
import json
import os
import random
import string
import time

# 關閉 Flask 的啟動訊息
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, template_folder='.', static_folder='.')

# 存放機器人數據
bot_stats = {
    "guild_count": 158,
    "member_count": 52340
}

# === 新增：聖誕節相關數據 ===
christmas_data = {
    "total_codes_generated": 0,
    "claimed_codes": {},
    "available_codes": {}
}

# === 動態代碼資料庫 ===
CODE_DB_FILE = "xmas_dynamic.json"

def save_code_to_db(code, score):
    """將生成的代碼寫入 JSON 檔案"""
    data = {}
    if os.path.exists(CODE_DB_FILE):
        try:
            with open(CODE_DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            pass
    
    # 添加時間戳記
    data[code] = {
        "score": score,
        "created_at": time.time(),
        "claimed": False,
        "claimed_by": None
    }
    
    # 更新計數器
    christmas_data["total_codes_generated"] += 1
    christmas_data["available_codes"][code] = data[code]
    
    with open(CODE_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_existing_codes():
    """載入已存在的代碼"""
    if os.path.exists(CODE_DB_FILE):
        try:
            with open(CODE_DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for code, info in data.items():
                    if info.get("claimed", False):
                        christmas_data["claimed_codes"][code] = info
                    else:
                        christmas_data["available_codes"][code] = info
                christmas_data["total_codes_generated"] = len(data)
        except:
            pass

# 啟動時載入現有代碼
load_existing_codes()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/commands')
def commands():
    return render_template('commands.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# === 新增：專屬照片頁面 ===
@app.route('/secret-photo')
def show_friend_photo():
    return render_template('photo.html')

# === 新增：聖誕節統計 API ===
@app.route('/api/christmas_stats')
def christmas_stats():
    stats = {
        "total_generated": christmas_data["total_codes_generated"],
        "available": len(christmas_data["available_codes"]),
        "claimed": len(christmas_data["claimed_codes"]),
        "top_score": max([info.get("score", 0) for info in christmas_data["claimed_codes"].values()], default=0)
    }
    return jsonify(stats)

# === 生成隨機襪子代碼的 API ===
@app.route('/api/generate_sock')
def generate_sock():
    # 1. 隨機生成 8 碼亂數 (例如: A7B9-2FX8)
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    code = f"SOCK-{random_str[:4]}-{random_str[4:]}"
    
    # 2. 隨機決定分數 (可以設權重，讓高分比較難出)
    score_weights = {
        10: 50,   # 50% 機率
        30: 30,   # 30% 機率
        50: 15,   # 15% 機率
        100: 5    # 5% 機率
    }
    score = random.choices(
        list(score_weights.keys()),
        weights=list(score_weights.values()),
        k=1
    )[0]
    
    # 3. 存入資料庫讓機器人讀取
    save_code_to_db(code, score)
    
    # 4. 回傳給網頁
    return jsonify({
        "code": code,
        "score": score,
        "message": "🎅 恭喜找到聖誕襪！",
        "total_generated": christmas_data["total_codes_generated"]
    })

@app.route('/api/stats')
def get_stats():
    """提供機器人統計數據給首頁"""
    # 這裡應該從 Discord bot 獲取實際數據
    # 暫時使用預設值
    return jsonify(bot_stats)

# === 新增：聖誕襪音效 ===
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/claim_status/<code>')
def claim_status(code):
    """查詢代碼兌換狀態"""
    if code in christmas_data["claimed_codes"]:
        info = christmas_data["claimed_codes"][code]
        return jsonify({
            "claimed": True,
            "score": info.get("score", 0),
            "claimed_by": info.get("claimed_by", "未知"),
            "claimed_at": info.get("claimed_at", "未知時間")
        })
    elif code in christmas_data["available_codes"]:
        return jsonify({
            "claimed": False,
            "score": christmas_data["available_codes"][code].get("score", 0),
            "available": True
        })
    else:
        return jsonify({"error": "代碼不存在"}), 404

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive(bot):
    # 更新機器人統計數據
    global bot_stats
    if bot:
        bot_stats["guild_count"] = len(bot.guilds)
        bot_stats["member_count"] = sum(guild.member_count for guild in bot.guilds)
    
    server = Thread(target=run)
    server.start()
