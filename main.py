import random
from flask import Flask, request, render_template_string, jsonify
import requests
import time
import os
import re

app = Flask(__name__)

# --- КЛЮЧИ ---
VT_API_KEY = os.getenv('VT_API_KEY')
HF_TOKEN = os.getenv('HF_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
CLOUDINARY_CLOUD = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
STATS_FILE = 'stats.txt'

def cld_img(public_id, ext='jpg'):
    if CLOUDINARY_CLOUD:
        return f"https://res.cloudinary.com/{CLOUDINARY_CLOUD}/image/upload/{public_id}.{ext}"
    return f"/static/{public_id}.{ext}"

def cld_vid(public_id):
    if CLOUDINARY_CLOUD:
        return f"https://res.cloudinary.com/{CLOUDINARY_CLOUD}/video/upload/{public_id}.mp4"
    return f"/static/{public_id}.mp4"

def get_real_stats():
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'w') as f: f.write("0,0")
    with open(STATS_FILE, 'r') as f:
        try:
            data = f.read().split(',')
            return int(data[0]), int(data[1])
        except: return 0, 0

def update_real_stats(is_virus=False):
    scans, viruses = get_real_stats()
    scans += 1
    if is_virus: viruses += 1
    with open(STATS_FILE, 'w') as f: f.write(f"{scans},{viruses}")

def ask_ai_opinion(url, stats):
    if not HF_TOKEN or 'ВСТАВЬ' in HF_TOKEN: return "Анализ сигнатур завершен успешно."
    prompt = (
        f"<s>[INST] Ты — CyberShield AI. Проверь URL: {url}. Угроз найдено: {stats['malicious']}. "
        f"Напиши короткий, технический вердикт. [/INST]"
    )
    try:
        API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 300, "temperature": 0.3}}
        res = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            return res.json()[0]['generated_text'].split("[/INST]")[-1].strip()
        return "Комплексная проверка не выявила активных угроз." if stats['malicious'] == 0 else "Зафиксирована вредоносная активность."
    except:
        return "Технический анализ завершен."

HTML_LAYOUT = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>CyberShield</title>
    <style>
        :root {
            --bg-dark: #1E1B4B;
            --card-bg: rgba(30, 27, 75, 0.8);
            --input-bg: rgba(15, 23, 42, 0.5);
            --nav-bg: rgba(30, 27, 75, 0.95);
            --accent-berry: #F472B6;
            --accent-frost: #818cf8;
            --grad-berry: linear-gradient(90deg, #1E1B4B, #312E81);
            --safe-green: #4ade80;
            --danger-red: #f87171;
            --text-main: #f1f5f9;
            --btn-static: #F472B6;
            --smooth: cubic-bezier(0.4, 0, 0.2, 1);
            --ultra-smooth: cubic-bezier(0.65, 0, 0.35, 1);
        }

        body.light-mode {
            --bg-dark: #fdf2f8;
            --card-bg: #ffffff;
            --input-bg: #ffffff;
            --nav-bg: rgba(255, 255, 255, 0.95);
            --grad-berry: linear-gradient(90deg, #fce7f3, #fdf2f8);
            --text-main: #1E1B4B;
        }

        body { 
            margin: 0; padding: 0; background-color: var(--bg-dark); color: var(--text-main); 
            font-family: 'Segoe UI', sans-serif; transition: background 0.5s var(--smooth); overflow-x: hidden; 
            min-height: 100vh; position: relative;
        }
        
        @keyframes ultraEntrance {
            0% { opacity: 0; transform: translateY(30px) scale(0.98); filter: blur(10px); }
            100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
        }

        .rays-container { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; pointer-events: none; overflow: hidden; }
        .ray { 
            position: absolute; 
            width: 1px; height: 180px;
            background: linear-gradient(to top, var(--accent-berry), transparent); 
            animation: rise linear infinite; opacity: 0; bottom: -200px;
            will-change: transform, opacity;
        }
        @keyframes rise { 
            0% { transform: translateY(0); opacity: 0; } 
            12% { opacity: 0.55; } 
            88% { opacity: 0.55; }
            100% { transform: translateY(-135vh); opacity: 0; } 
        }
        @keyframes rise-fade-mid { 
            0% { transform: translateY(0); opacity: 0; } 
            15% { opacity: 0.6; } 
            45% { transform: translateY(-55vh); opacity: 0.55; }
            55% { transform: translateY(-65vh); opacity: 0; }
            100% { transform: translateY(-130vh); opacity: 0; } 
        }
        @keyframes rise-fade-late { 
            0% { transform: translateY(0); opacity: 0; } 
            15% { opacity: 0.55; } 
            70% { transform: translateY(-85vh); opacity: 0.5; }
            85% { transform: translateY(-105vh); opacity: 0; }
            100% { transform: translateY(-130vh); opacity: 0; } 
        }

        .ray-thick {
            position: absolute;
            width: 3px; height: 240px;
            background: linear-gradient(to top, #ffffff 0%, var(--accent-berry) 30%, rgba(244,114,182,0.4) 70%, transparent 100%);
            box-shadow: 0 0 18px var(--accent-berry), 0 0 38px rgba(244,114,182,0.55);
            border-radius: 3px;
            animation: rise linear infinite; opacity: 0; bottom: -260px;
            will-change: transform, opacity;
        }
        body.light-mode .ray-thick {
            background: linear-gradient(to top, #ffffff 0%, #ec4899 30%, rgba(236,72,153,0.5) 70%, transparent 100%);
            box-shadow: 0 0 18px #ec4899, 0 0 40px rgba(236,72,153,0.5);
        }

        .ray-short {
            position: absolute; 
            width: 2px; height: 150px;
            background: linear-gradient(to top, #fff, var(--accent-berry), transparent); 
            animation: rise-short linear infinite; opacity: 0; bottom: -200px;
            will-change: transform, opacity;
            box-shadow: 0 0 10px var(--accent-berry);
        }
        @keyframes rise-short {
            0% { transform: translateY(0); opacity: 0; }
            15% { opacity: 1; }
            50% { transform: translateY(-50vh); opacity: 0; }
            100% { transform: translateY(-50vh); opacity: 0; }
        }

        /* Десктоп: контент сдвинут правее */
        .container { max-width: 650px; margin: 0 auto; padding: 30px 20px 50px 74px; }

        /* --- БОКОВОЕ МЕНЮ --- */
        .hamburger-btn {
            position: fixed; top: 14px; left: 8px; z-index: 10001;
            width: 44px; height: 44px; border-radius: 50%;
            background: rgba(30, 27, 75, 0.9); border: 2px solid var(--accent-berry);
            display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 5px;
            cursor: pointer; box-shadow: 0 0 15px rgba(244, 114, 182, 0.3);
            transition: all 0.4s var(--smooth); backdrop-filter: blur(5px);
        }
        .hamburger-btn:hover { transform: scale(1.06); box-shadow: 0 0 22px rgba(244, 114, 182, 0.65); }
        .hamburger-btn div { width: 22px; height: 2px; background: var(--accent-berry); transition: 0.4s var(--smooth); border-radius: 2px; }
        body.light-mode .hamburger-btn { background: linear-gradient(135deg, var(--accent-berry), #ec4899); border-color: #fff; box-shadow: 0 0 15px rgba(244,114,182,0.55); }
        body.light-mode .hamburger-btn div { background: #ffffff; }
        .hamburger-btn.open div:nth-child(1) { transform: translate(-7px, 7px) rotate(90deg); }
        .hamburger-btn.open div:nth-child(2) { opacity: 1; transform: rotate(90deg); }
        .hamburger-btn.open div:nth-child(3) { transform: translate(7px, -7px) rotate(90deg); }

        .menu-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(15, 23, 42, 0.35);
            z-index: 9998; opacity: 0; pointer-events: none;
            transition: opacity 0.45s var(--smooth);
        }
        .menu-overlay.active { opacity: 1; pointer-events: all; }

        /* ДЕСКТОП (> 700px): постоянный рейл 66px */
        .side-menu {
            position: fixed; top: 0; left: 0; height: 100%;
            width: 66px;
            background: var(--nav-bg); z-index: 9999;
            box-shadow: 4px 0 24px rgba(0,0,0,0.45);
            padding: 70px 8px 20px;
            display: flex; flex-direction: column; gap: 10px;
            transition: width 0.5s var(--ultra-smooth);
            border-right: 1px solid rgba(244, 114, 182, 0.3);
            box-sizing: border-box; overflow: hidden;
        }
        .side-menu.active { width: 262px; padding: 70px 14px 20px; }

        /* Гербы — только в раскрытом меню */
        .menu-emblems {
            display: flex; justify-content: center; align-items: center; gap: 14px;
            height: 0; overflow: hidden; opacity: 0;
            transition: height 0.4s var(--smooth), opacity 0.4s var(--smooth);
            margin-bottom: 0;
        }
        .side-menu.active .menu-emblems {
            height: 58px; opacity: 1; margin-bottom: 10px;
            transition-delay: 0.05s;
        }
        .menu-emblem-img { width: 44px; height: 44px; object-fit: contain; filter: drop-shadow(0 0 8px rgba(244,114,182,0.35)); }

        /* Пункты меню */
        .menu-item {
            padding: 12px 0; background: rgba(0,0,0,0.3); border-radius: 13px;
            font-weight: 800; font-size: 13.5px; cursor: pointer;
            border: 1px solid rgba(244, 114, 182, 0.12);
            transition: background 0.32s var(--smooth), color 0.32s var(--smooth),
                        border-color 0.32s, box-shadow 0.32s, transform 0.32s;
            color: var(--text-main); letter-spacing: 0.8px;
            display: flex; align-items: center;
            white-space: nowrap; overflow: hidden;
            justify-content: flex-start;
            padding-left: 0;
        }
        body.light-mode .menu-item { background: rgba(244, 114, 182, 0.1); }
        .menu-item .menu-ico {
            font-size: 21px; line-height: 1;
            flex: 0 0 66px; text-align: center; display: inline-block;
            transition: flex-basis 0.5s var(--ultra-smooth);
        }
        .side-menu.active .menu-item .menu-ico { flex-basis: 46px; }
        .menu-item .menu-label {
            opacity: 0; transform: translateX(-8px);
            transition: opacity 0.32s var(--smooth), transform 0.4s var(--smooth);
            display: inline-block; padding-right: 12px;
        }
        .side-menu.active .menu-item .menu-label { opacity: 1; transform: translateX(0); transition-delay: 0.08s; }
        .menu-item:hover, .menu-item.active {
            background: var(--btn-static); color: #1E1B4B;
            border-color: transparent; box-shadow: 0 0 14px rgba(244, 114, 182, 0.42);
            transform: scale(1.02);
        }

        .tg-menu-btn {
            margin-top: 5px; white-space: nowrap; font-size: 13px; text-transform: uppercase;
            opacity: 0; transform: translateY(8px);
            transition: opacity 0.4s var(--smooth), transform 0.4s var(--smooth);
            display: flex; justify-content: center; width: 100%; box-sizing: border-box;
            pointer-events: none;
        }
        .side-menu.active .tg-menu-btn { opacity: 1; transform: translateY(0); pointer-events: auto; transition-delay: 0.14s; }
        .side-menu hr { opacity: 0; transition: opacity 0.4s var(--smooth); }
        .side-menu.active hr { opacity: 1; }

        /* МОБИЛЬНЫЙ (≤ 700px): рейл скрыт полностью, только гамбургер */
        @media (max-width: 700px) {
            .container { padding-left: 20px; padding-top: 70px; }
            .hamburger-btn { left: 12px; top: 14px; }
            .side-menu { width: 0; padding: 70px 0 20px; border-right: none; }
            .side-menu.active { width: 260px; padding: 70px 12px 20px; border-right: 1px solid rgba(244,114,182,0.3); }
            .menu-overlay.active { background: rgba(10,15,40,0.6); }
        }

        .tg-super-btn {
            display: flex; align-items: center; justify-content: center; gap: 10px;
            background: linear-gradient(45deg, #0088cc, #00aaff); border-radius: 25px;
            padding: 12px 25px; color: white; font-weight: 900; font-size: 14px; letter-spacing: 1px;
            border: none; cursor: pointer; text-decoration: none;
            box-shadow: 0 4px 15px rgba(0, 136, 204, 0.3); transition: all 0.3s var(--smooth);
        }
        .tg-super-btn:hover { transform: translateY(-3px) scale(1.05); box-shadow: 0 8px 25px rgba(0, 136, 204, 0.6); }
        .tg-super-btn svg { width: 22px; height: 22px; fill: white; flex-shrink: 0; }

        .page-content { transition: opacity 0.5s ease; }
        
        .radar-box {
            background: var(--card-bg); border-radius: 25px; padding: 25px;
            border: 1px solid rgba(74, 222, 128, 0.3); text-align: center;
            margin-top: 20px; position: relative; overflow: hidden;
            animation: ultraEntrance 0.8s var(--ultra-smooth) backwards;
        }
        .radar-circle {
            width: 160px; height: 160px; border-radius: 50%; border: 2px solid rgba(74, 222, 128, 0.2);
            margin: 20px auto; position: relative; overflow: hidden;
            background: repeating-radial-gradient(transparent, transparent 20px, rgba(74, 222, 128, 0.05) 21px);
            box-shadow: 0 0 20px rgba(74, 222, 128, 0.1);
        }
        .radar-circle::after {
            content: ''; position: absolute; top: 0; left: 50%; width: 50%; height: 50%;
            background: linear-gradient(90deg, transparent, rgba(74, 222, 128, 0.6));
            transform-origin: bottom left; animation: radarSpin 2s linear infinite;
            border-radius: 0 100% 0 0;
        }
        @keyframes radarSpin { 100% { transform: rotate(360deg); } }
        .blip {
            width: 6px; height: 6px; background: var(--danger-red); border-radius: 50%;
            position: absolute; box-shadow: 0 0 10px var(--danger-red);
            animation: blipFlash 2s infinite; opacity: 0; z-index: 2;
        }
        .blip1 { top: 40px; left: 50px; animation-delay: 0.5s; }
        .blip2 { top: 100px; left: 120px; animation-delay: 1.2s; }
        .blip3 { top: 80px; left: 30px; animation-delay: 1.8s; background: #fbbf24; box-shadow: 0 0 10px #fbbf24;}
        @keyframes blipFlash { 0%, 100% { opacity: 0; } 50% { opacity: 1; } }
        .cyber-logs { background: rgba(0,0,0,0.3); border-radius: 15px; padding: 15px; text-align: left; height: 100px; overflow-y: auto; scrollbar-width: none; }
        .cyber-logs::-webkit-scrollbar { display: none; }

        .logo-main {
            font-size: 28px; font-weight: 800; letter-spacing: 2px; margin: 0;
            display: flex; align-items: center; justify-content: center; gap: 10px;
        }
        .logo-main span { flex-shrink: 0; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; }

        .search-card, .report-card { 
            animation: ultraEntrance 0.8s var(--ultra-smooth) backwards;
            transition: transform 0.4s var(--ultra-smooth), box-shadow 0.4s var(--ultra-smooth), border 0.3s;
        }

        .memo-box, .info-box, .game-section { 
            background: var(--card-bg); 
            border-radius: 20px; 
            margin-bottom: 20px; 
            border: 2px solid rgba(244, 114, 182, 0.1); 
            overflow: hidden; 
            display: grid; 
            transition: all 0.5s var(--ultra-smooth); 
            animation: ultraEntrance 0.8s var(--ultra-smooth) backwards;
        }
        
        .memo-box, .info-box { grid-template-rows: auto 0fr; }
        .memo-box.active, .info-box.active { grid-template-rows: auto 1fr; }

        .memo-box:hover, .info-box:hover, .game-section:hover,
        .memo-box:active, .info-box:active, .game-section:active {
            border: 2px solid transparent;
            background-image: linear-gradient(var(--card-bg), var(--card-bg)), 
                              linear-gradient(90deg, var(--accent-berry), var(--accent-frost));
            background-origin: border-box;
            background-clip: padding-box, border-box;
            box-shadow: 0 10px 25px rgba(244, 114, 182, 0.2);
            transform: translateY(-5px);
        }

        .search-card { background: var(--grad-berry); padding: 30px; border-radius: 25px; border: 1px solid rgba(244, 114, 182, 0.2); text-align: center; margin-bottom: 25px; }
        
        .input-wrapper { display: flex; align-items: center; background: var(--input-bg); border-radius: 50px; padding: 5px; border: 1px solid rgba(244, 114, 182, 0.3); margin-top: 20px; gap: 5px; }
        input[type="text"] { flex: 1; padding: 12px 15px; border: none; background: transparent; color: var(--text-main); outline: none; font-size: 14px; min-width: 0; }
        
        .btn-scan { 
            background: var(--btn-static); color: #1E1B4B; border: none; padding: 12px 22px; 
            border-radius: 50px; font-weight: bold; cursor: pointer; white-space: nowrap; 
            font-size: 14px; flex-shrink: 0; transition: transform 0.2s var(--smooth); 
        }
        .btn-scan:active { transform: scale(0.95); }

        #loading-overlay { display: none; padding: 20px; text-align: center; }
        .loader-ring { width: 40px; height: 40px; border: 4px solid rgba(244, 114, 182, 0.1); border-top: 4px solid var(--accent-berry); border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 10px; }
        @keyframes spin { 100% { transform: rotate(360deg); } }

        .report-card { background: var(--card-bg); border-radius: 25px; padding: 25px; margin-bottom: 25px; border: 1px solid rgba(244, 114, 182, 0.15); }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }
        .stat-box { background: rgba(0,0,0,0.1); padding: 15px; border-radius: 18px; text-align: center; border: 1px solid rgba(244, 114, 182, 0.1); }
        .stat-val { font-size: 22px; font-weight: bold; display: block; }
        
        .detail-box { 
            border-radius: 20px; padding: 5px; margin-bottom: 15px; position: relative; overflow: hidden; 
            background: rgba(0,0,0,0.2); border: 1px solid rgba(244, 114, 182, 0.1);
        }
        
        .detail-list { display: flex; flex-direction: column; gap: 8px; }
        
        .detail-row {
            position: relative;
            display: flex; align-items: center; gap: 12px;
            padding: 15px; border-radius: 15px; 
            background: rgba(30, 27, 75, 0.4);
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.05);
        }

        .detail-row::before {
            content: "";
            position: absolute;
            top: -100%; left: 0; width: 100%; height: 100%;
            background: linear-gradient(to bottom, transparent, rgba(129, 140, 248, 0.1), transparent);
            animation: waterfall 3s infinite linear;
        }

        @keyframes waterfall {
            0% { top: -100%; }
            100% { top: 100%; }
        }

        .danger .detail-row::before { background: linear-gradient(to bottom, transparent, rgba(248, 113, 113, 0.15), transparent); }
        .safe .detail-row::before { background: linear-gradient(to bottom, transparent, rgba(74, 222, 128, 0.15), transparent); }

        .detail-indicator {
            width: 4px; height: 20px; border-radius: 2px; flex-shrink: 0;
            position: relative; z-index: 2;
        }
        .danger .detail-indicator { background: var(--danger-red); box-shadow: 0 0 10px var(--danger-red); }
        .safe .detail-indicator { background: var(--safe-green); box-shadow: 0 0 10px var(--safe-green); }

        .detail-info { flex: 1; position: relative; z-index: 2; }
        .detail-label { font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; display: block; margin-bottom: 2px; }
        .danger .detail-label { color: var(--danger-red); }
        .safe .detail-label { color: var(--safe-green); }
        
        .detail-text { font-size: 13px; font-weight: 500; color: var(--text-main); }

        .shimmer-text {
            background: linear-gradient(0deg, #F472B6, #818cf8, #fdf2f8, #F472B6);
            background-size: 100% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmerVertical 3s linear infinite;
            font-weight: bold;
        }
        
        .status-safe {
            background: linear-gradient(90deg, #4ade80, #fdf2f8, #4ade80);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmerStatus 3s linear infinite;
        }
        .status-danger {
            background: linear-gradient(90deg, #f87171, #F472B6, #f87171);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmerStatus 3s linear infinite;
        }

        @keyframes shimmerVertical {
            0% { background-position: 0% 100%; }
            100% { background-position: 0% -100%; }
        }
        @keyframes shimmerStatus { to { background-position: 200% center; } }

        .ai-box { background: rgba(244, 114, 182, 0.05); border: 1px dashed var(--accent-berry); border-radius: 15px; padding: 15px; font-size: 14px; line-height: 1.6; }

        .memo-header, .info-header { padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; z-index: 2; }
        
        .chevron {
            width: 8px; height: 8px;
            border-bottom: 2px solid var(--accent-berry);
            border-right: 2px solid var(--accent-berry);
            transform: rotate(45deg);
            transition: transform 0.6s var(--ultra-smooth);
            margin-right: 10px; flex-shrink: 0;
        }
        .memo-box.active .chevron, .info-box.active .chevron { transform: rotate(-135deg); }

        .memo-content, .info-content { 
            overflow: hidden; 
            opacity: 0; 
            transform: scale(0.95);
            filter: blur(5px);
            transition: opacity 0.6s var(--ultra-smooth), transform 0.6s var(--ultra-smooth), filter 0.6s var(--ultra-smooth);
            padding: 0 20px;
        }
        .memo-box.active .memo-content, .info-box.active .info-content { opacity: 1; transform: scale(1); filter: blur(0); padding: 0 20px 20px; }

        .game-section { padding: 25px; position: relative; }
        
        .test-tabs { display: flex; gap: 10px; margin-bottom: 20px; background: rgba(0,0,0,0.2); padding: 5px; border-radius: 15px; }
        .tab-btn { flex: 1; padding: 10px; border: none; background: transparent; color: var(--text-main); font-size: 11px; font-weight: 800; cursor: pointer; border-radius: 10px; transition: all 0.3s; opacity: 0.5; }
        .tab-btn.active { background: var(--accent-berry); color: #1E1B4B; opacity: 1; }

        #quiz-area { position: relative; width: 100%; min-height: 160px; overflow: hidden; perspective: 1000px; }

        .quiz-option {
            padding: 15px; border-radius: 15px; margin-bottom: 10px; cursor: pointer;
            background: rgba(0,0,0,0.2); border: 1px solid rgba(244, 114, 182, 0.2);
            transition: all 0.3s var(--smooth); font-size: 14px;
        }
        .quiz-option:hover { border-color: var(--accent-berry); background: rgba(244, 114, 182, 0.1); }
        .quiz-option.correct { background: rgba(74, 222, 128, 0.2); border-color: var(--safe-green); color: var(--safe-green); }
        .quiz-option.wrong { background: rgba(248, 113, 113, 0.2); border-color: var(--danger-red); color: var(--danger-red); }
        .hidden { display: none !important; }
        .slide-left-to-right { animation: slideIn 0.4s var(--smooth); }
        @keyframes slideIn { from { transform: translateX(-60px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

        /* --- HOME PAGE --- */
        .home-hero {
            text-align: center; padding: 35px 10px 30px;
            animation: ultraEntrance 0.9s var(--ultra-smooth) backwards;
        }
        .hero-emblems {
            display: flex; justify-content: center; align-items: center; gap: 24px;
            margin-bottom: 24px;
        }
        .hero-emblem {
            width: 72px; height: 72px; object-fit: contain;
            filter: drop-shadow(0 0 14px rgba(244,114,182,0.4));
            transition: transform 0.4s var(--smooth), filter 0.4s;
        }
        .hero-emblem:hover { transform: scale(1.08); filter: drop-shadow(0 0 22px rgba(244,114,182,0.7)); }
        .home-hero-badge {
            display: inline-flex; align-items: center; gap: 6px;
            background: rgba(74, 222, 128, 0.1); border: 1px solid rgba(74, 222, 128, 0.3);
            border-radius: 50px; padding: 5px 14px; font-size: 11px; font-weight: 800;
            color: var(--safe-green); letter-spacing: 1px; margin-bottom: 18px;
        }
        .home-hero-title { font-size: clamp(22px, 5vw, 30px); font-weight: 800; margin: 0 0 14px; line-height: 1.25; }
        .home-hero-accent { color: var(--accent-berry); -webkit-text-fill-color: var(--accent-berry); }
        .home-hero-sub { font-size: 14px; color: var(--text-main); opacity: 0.82; max-width: 520px; margin: 0 auto 12px; line-height: 1.65; }
        .home-hero-extra { font-size: 13px; color: var(--text-main); opacity: 0.65; max-width: 500px; margin: 0 auto 22px; line-height: 1.6; }
        .home-hero-cta { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 10px; }
        .hero-btn {
            padding: 12px 26px; border-radius: 50px; font-weight: 800; font-size: 13px; letter-spacing: 0.8px;
            cursor: pointer; border: none; text-decoration: none; transition: all 0.35s var(--smooth);
        }
        .hero-btn.primary { background: var(--btn-static); color: #1E1B4B; box-shadow: 0 4px 18px rgba(244,114,182,0.35); }
        .hero-btn.primary:hover { transform: translateY(-3px); box-shadow: 0 8px 28px rgba(244,114,182,0.55); }
        .hero-btn.ghost { background: transparent; color: var(--text-main); border: 1.5px solid rgba(244,114,182,0.35); }
        .hero-btn.ghost:hover { border-color: var(--accent-berry); background: rgba(244,114,182,0.08); }

        .home-stats { display: flex; gap: 14px; margin: 10px 0 28px; flex-wrap: wrap; }
        .home-stat {
            flex: 1 1 120px; background: var(--card-bg); border-radius: 18px;
            padding: 18px 14px; text-align: center; border: 1px solid rgba(244,114,182,0.15);
            transition: transform 0.35s var(--smooth), box-shadow 0.35s;
        }
        .home-stat:hover { transform: translateY(-4px); box-shadow: 0 10px 22px rgba(244,114,182,0.15); }
        .home-stat-num { font-size: 26px; font-weight: 800; color: var(--accent-berry); }
        .home-stat-label { font-size: 11px; color: var(--text-main); opacity: 0.7; margin-top: 4px; }

        .home-section { margin-bottom: 30px; }
        .home-section-head { margin-bottom: 16px; }
        .home-section-head h3 { margin: 0 0 4px; font-size: 16px; }
        .home-section-head span { font-size: 12px; color: var(--text-main); opacity: 0.6; }

        .home-about-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 20px; }
        .home-about-card {
            background: var(--card-bg); border-radius: 18px; padding: 18px 16px;
            border: 1px solid rgba(244,114,182,0.1); cursor: pointer;
            transition: all 0.35s var(--smooth);
        }
        .home-about-card:hover { transform: translateY(-4px); border-color: var(--accent-berry); box-shadow: 0 10px 22px rgba(244,114,182,0.2); }
        .home-about-icon { font-size: 28px; margin-bottom: 10px; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; background: rgba(244,114,182,0.1); border-radius: 14px; }
        .home-about-title { font-size: 12px; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 6px; }
        .home-about-desc { font-size: 11.5px; color: var(--text-main); opacity: 0.7; line-height: 1.5; }

        .home-info-block {
            background: var(--card-bg); border-radius: 18px; padding: 22px 20px;
            border: 1px solid rgba(244,114,182,0.1); font-size: 13.5px; line-height: 1.7;
        }
        .home-info-block h4 { margin: 0 0 12px; font-size: 15px; }
        .home-info-block p { margin: 0 0 10px; }
        .home-info-block ul { padding-left: 18px; margin: 0; }
        .home-info-block li { margin-bottom: 5px; }

        /* АККОРДЕОН (видео/фото) */
        .accord-box {
            background: var(--card-bg); border-radius: 20px; overflow: hidden;
            border: 1px solid rgba(244,114,182,0.15);
            transition: border-color 0.35s var(--smooth), box-shadow 0.35s;
            animation: ultraEntrance 0.8s var(--ultra-smooth) backwards;
        }
        .accord-box:hover { border-color: rgba(244,114,182,0.4); box-shadow: 0 8px 24px rgba(244,114,182,0.12); }
        .accord-header {
            padding: 18px 20px; display: flex; justify-content: space-between; align-items: center;
            cursor: pointer; user-select: none;
        }
        .accord-title { font-weight: 800; font-size: 14.5px; margin-bottom: 3px; }
        .accord-subtitle { font-size: 11.5px; color: var(--text-main); opacity: 0.65; }
        .accord-chevron {
            font-size: 14px; color: var(--accent-berry);
            transition: transform 0.5s var(--ultra-smooth); flex-shrink: 0;
        }
        .accord-box.open .accord-chevron { transform: rotate(180deg); }
        .accord-content {
            display: grid; grid-template-rows: 0fr;
            transition: grid-template-rows 0.55s var(--ultra-smooth);
        }
        .accord-box.open .accord-content { grid-template-rows: 1fr; }
        .accord-inner { overflow: hidden; padding: 0 18px; }
        .accord-box.open .accord-inner { padding: 0 18px 18px; }

        /* ВИДЕО ТАБЫ */
        .vid-tabs { display: flex; gap: 10px; margin-bottom: 14px; }
        .vid-tab {
            flex: 1 1 110px;
            background: rgba(0,0,0,0.25); border: 1.5px solid rgba(244,114,182,0.2);
            border-radius: 14px; padding: 14px 10px 12px;
            cursor: pointer; color: var(--text-main);
            display: flex; flex-direction: column; align-items: center; gap: 8px;
            transition: background 0.3s, border-color 0.3s, transform 0.32s, box-shadow 0.32s;
            font-family: inherit;
        }
        .vid-tab-ico { font-size: 26px; }
        .vid-tab-text { font-size: 12px; font-weight: 700; letter-spacing: 0.3px; text-align: center; line-height: 1.4; }
        .vid-tab:hover { border-color: var(--accent-berry); transform: translateY(-3px); box-shadow: 0 8px 20px rgba(244,114,182,0.2); }
        .vid-tab.active { background: var(--btn-static); color: #1E1B4B; border-color: transparent; box-shadow: 0 6px 18px rgba(244,114,182,0.35); }
        .vid-tab.active .vid-tab-text { color: #1E1B4B; }
        body.light-mode .vid-tab { background: rgba(244,114,182,0.07); }
        .vid-player-wrap {
            border-radius: 14px; overflow: hidden;
            border: 1.5px solid rgba(244,114,182,0.25);
            background: #000;
            box-shadow: 0 8px 28px rgba(0,0,0,0.55);
        }
        .vid-player { width: 100%; display: block; max-height: 360px; object-fit: contain; }

        /* ФОТО КАРУСЕЛЬ С СТРЕЛКАМИ */
        .photo-carousel-wrap {
            position: relative;
            overflow: hidden;
            border-radius: 16px;
        }
        .photo-carousel-track-outer {
            overflow: hidden;
            border-radius: 14px;
        }
        .photo-carousel-track {
            display: flex;
            gap: 14px;
            transition: transform 0.55s var(--ultra-smooth);
        }
        .photo-card {
            flex: 0 0 calc(50% - 7px);
            border-radius: 14px; overflow: hidden;
            border: 1.5px solid rgba(244,114,182,0.18);
            background: var(--card-bg);
            cursor: pointer; position: relative;
            transition: transform 0.35s var(--smooth), border-color 0.35s, box-shadow 0.35s;
        }
        @media (max-width: 480px) { .photo-card { flex: 0 0 85%; } }
        .photo-card:hover { transform: translateY(-5px) scale(1.02); border-color: var(--accent-berry); box-shadow: 0 12px 28px rgba(244,114,182,0.3); }
        .photo-card img { width: 100%; display: block; aspect-ratio: 3/4; object-fit: cover; }
        @media (max-width: 480px) { .photo-card img { aspect-ratio: 4/3; } }
        .photo-card-label {
            padding: 8px 10px; font-size: 11.5px; font-weight: 800;
            letter-spacing: 0.4px; color: var(--text-main);
            background: var(--card-bg); text-align: center;
        }
        body.light-mode .photo-card { background: #fff; box-shadow: 0 2px 10px rgba(30,27,75,0.07); }

        /* Стрелки карусели — такие же как у ленты новостей */
        .photo-arrows {
            display: flex; justify-content: center; align-items: center; gap: 16px;
            margin-top: 14px;
        }
        .photo-arrow {
            width: 38px; height: 38px; border-radius: 50%;
            background: rgba(244,114,182,0.15); border: 1.5px solid rgba(244,114,182,0.35);
            color: var(--accent-berry); font-size: 20px; font-weight: 700;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: all 0.3s var(--smooth);
            user-select: none; flex-shrink: 0;
        }
        .photo-arrow:hover { background: var(--accent-berry); color: #1E1B4B; box-shadow: 0 4px 14px rgba(244,114,182,0.4); transform: scale(1.08); }
        .photo-arrow:active { transform: scale(0.92); }
        .photo-dots {
            display: flex; gap: 7px; align-items: center;
        }
        .photo-dot {
            width: 7px; height: 7px; border-radius: 50%;
            background: rgba(244,114,182,0.3); border: 1px solid rgba(244,114,182,0.5);
            cursor: pointer; transition: all 0.3s var(--smooth);
        }
        .photo-dot.active { background: var(--accent-berry); transform: scale(1.3); border-color: var(--accent-berry); }

        /* МОДАЛЬНОЕ ОКНО ФОТО */
        .photo-modal {
            position: fixed; inset: 0; z-index: 20000;
            background: rgba(10,10,30,0.92); backdrop-filter: blur(14px);
            display: flex; align-items: center; justify-content: center;
            padding: 20px; box-sizing: border-box;
            opacity: 0; pointer-events: none;
            transition: opacity 0.35s var(--smooth);
        }
        .photo-modal.open { opacity: 1; pointer-events: all; }
        .photo-modal-inner {
            position: relative; max-width: 92vw; max-height: 92vh;
            border-radius: 18px; overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.7);
            transform: scale(0.9); transition: transform 0.38s var(--ultra-smooth);
        }
        .photo-modal.open .photo-modal-inner { transform: scale(1); }
        .photo-modal img { width: 100%; max-height: 82vh; object-fit: contain; display: block; background: #000; }
        .photo-modal-close {
            position: absolute; top: 10px; right: 12px; z-index: 2;
            background: rgba(0,0,0,0.65); border: none; border-radius: 50%;
            width: 36px; height: 36px; cursor: pointer; font-size: 16px;
            color: #fff; display: flex; align-items: center; justify-content: center;
            transition: background 0.22s;
        }
        .photo-modal-close:hover { background: var(--accent-berry); color: #1E1B4B; }
        .photo-modal-cap {
            background: rgba(15,23,42,0.92); color: #fff;
            padding: 10px 16px; font-size: 13px; font-weight: 700; text-align: center;
        }

        /* ЛЕНТА НОВОСТЕЙ */
        .news-ticker-wrap {
            position: relative; overflow: hidden; border-radius: 18px;
        }
        .news-arrow-edge {
            position: absolute; top: 50%; transform: translateY(-50%);
            width: 34px; height: 34px; border-radius: 50%; z-index: 10;
            background: rgba(30,27,75,0.75); border: 1.5px solid rgba(244,114,182,0.5);
            color: var(--accent-berry); font-size: 20px; font-weight: 700;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: all 0.3s var(--smooth); backdrop-filter: blur(6px);
        }
        .news-arrow-edge.prev { left: 8px; }
        .news-arrow-edge.next { right: 8px; }
        .news-arrow-edge:hover { background: var(--accent-berry); color: #1E1B4B; box-shadow: 0 4px 14px rgba(244,114,182,0.45); transform: translateY(-50%) scale(1.1); }
        .news-arrow-edge:active { transform: translateY(-50%) scale(0.92); }
        .news-track {
            display: flex; gap: 14px; padding: 6px 50px;
            will-change: transform; cursor: grab; user-select: none;
        }
        .news-track.is-dragging { cursor: grabbing; }
        .news-tile {
            flex: 0 0 270px; height: 210px; border-radius: 16px; overflow: hidden;
            position: relative; text-decoration: none; color: var(--text-main);
            background: var(--card-bg); border: 1px solid rgba(244,114,182,0.18);
            transition: transform 0.35s var(--smooth), box-shadow 0.35s;
            flex-shrink: 0;
        }
        .news-tile:hover { transform: translateY(-5px); box-shadow: 0 12px 28px rgba(244,114,182,0.2); }
        .news-tile-img {
            position: absolute; inset: 0;
            background-size: cover; background-position: center;
            transition: transform 0.5s var(--smooth);
        }
        .news-tile:hover .news-tile-img { transform: scale(1.06); }
        .news-tile-pill {
            position: absolute; top: 10px; left: 10px; z-index: 2;
            background: var(--accent-berry); color: #1E1B4B;
            font-size: 10px; font-weight: 800; letter-spacing: 0.7px;
            padding: 3px 10px; border-radius: 50px;
        }
        .news-tile-fog {
            position: absolute; bottom: 0; left: 0; right: 0; z-index: 2;
            background: linear-gradient(to top, rgba(15,23,42,0.92), transparent);
            padding: 32px 14px 14px;
        }
        .news-tile-title { font-size: 13px; font-weight: 700; line-height: 1.4; margin-bottom: 4px; }
        .news-tile-source { font-size: 10px; opacity: 0.6; }

        /* СЕКЦИЯ ПУТИ */
        .home-path {
            background: var(--card-bg); border-radius: 16px; padding: 16px 18px;
            border: 1px solid rgba(244,114,182,0.1); margin-bottom: 12px;
            display: flex; align-items: flex-start; gap: 14px; cursor: pointer;
            transition: all 0.35s var(--smooth);
        }
        .home-path:hover { border-color: var(--accent-berry); background: rgba(244,114,182,0.07); transform: translateX(4px); }
        .home-path-num { 
            width: 32px; height: 32px; border-radius: 50%; background: var(--accent-berry);
            color: #1E1B4B; font-weight: 800; font-size: 14px; flex-shrink: 0;
            display: flex; align-items: center; justify-content: center;
        }
        .home-path-title { font-weight: 800; font-size: 13.5px; margin-bottom: 4px; }
        .home-path-desc { font-size: 12px; color: var(--text-main); opacity: 0.7; line-height: 1.5; }

        /* СИМ-СЕТКА */
        .sim-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 15px; }
        .sim-card {
            background: rgba(0,0,0,0.2); border: 1px solid rgba(244,114,182,0.15);
            border-radius: 16px; padding: 18px 8px;
            text-align: center; cursor: pointer;
            transition: all 0.35s var(--smooth);
        }
        .sim-card:hover { border-color: var(--accent-berry); background: rgba(244,114,182,0.1); transform: translateY(-4px); }

        /* ЧАТ */
        .chat-container { background: rgba(0,0,0,0.25); border-radius: 18px; overflow: hidden; border: 1px solid rgba(244,114,182,0.2); }
        .chat-header { padding: 14px 18px; background: rgba(244,114,182,0.1); font-size: 13px; font-weight: 800; letter-spacing: 1px; }
        .chat-messages { height: 280px; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; scrollbar-width: thin; scrollbar-color: var(--accent-berry) transparent; }
        .msg { max-width: 78%; padding: 10px 14px; border-radius: 16px; font-size: 13px; line-height: 1.5; word-break: break-word; }
        .msg.bot { background: rgba(129,140,248,0.15); border: 1px solid rgba(129,140,248,0.25); align-self: flex-start; }
        .msg.user { background: rgba(244,114,182,0.15); border: 1px solid rgba(244,114,182,0.25); align-self: flex-end; text-align: right; }
        .chat-input-area { display: flex; gap: 8px; padding: 12px 15px; background: rgba(0,0,0,0.2); border-top: 1px solid rgba(244,114,182,0.1); }
        .chat-send-btn { background: var(--accent-berry); color: #1E1B4B; border: none; border-radius: 12px; padding: 0 18px; font-size: 18px; cursor: pointer; transition: transform 0.2s; flex-shrink: 0; }
        .chat-send-btn:active { transform: scale(0.9); }

        /* PASSWORD PAGE */
        .pw-rules { margin: 18px 0; display: flex; flex-direction: column; gap: 8px; }
        .pw-rule { display: flex; align-items: center; gap: 10px; font-size: 13px; padding: 10px 14px; background: rgba(0,0,0,0.15); border-radius: 12px; border: 1px solid rgba(244,114,182,0.1); transition: border-color 0.3s; }
        .pw-rule.active { border-color: var(--safe-green); background: rgba(74,222,128,0.07); }
        .pw-rule-icon { width: 20px; text-align: center; font-size: 16px; flex-shrink: 0; }
        .pw-rule-icon::before { content: '✗'; color: var(--danger-red); }
        .pw-rule.active .pw-rule-icon::before { content: '✔'; color: var(--safe-green); }
        .pw-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 18px 0; }
        .pw-stat { background: rgba(0,0,0,0.15); border-radius: 14px; padding: 14px; text-align: center; border: 1px solid rgba(244,114,182,0.1); }
        .pw-stat-val { font-size: 22px; font-weight: 800; color: var(--accent-berry); display: block; margin-bottom: 4px; }
        .pw-stat-label { font-size: 10px; opacity: 0.65; text-transform: uppercase; letter-spacing: 0.8px; }

        /* ГОЛОСОВАЯ КНОПКА */
        .voice-btn {
            float: right; background: rgba(244,114,182,0.15); border: 1px solid rgba(244,114,182,0.3);
            border-radius: 50%; width: 32px; height: 32px; cursor: pointer;
            display: flex; align-items: center; justify-content: center; font-size: 14px;
            transition: all 0.3s; margin-left: 10px;
        }
        .voice-btn:hover { background: var(--accent-berry); color: #1E1B4B; }

        /* ПИНГ */
        .ping-indicator {
            display: inline-flex; align-items: center; gap: 6px; font-size: 11px;
            padding: 4px 12px; border-radius: 50px;
            background: rgba(74,222,128,0.1); border: 1px solid rgba(74,222,128,0.3); color: var(--safe-green);
        }
        .ping-indicator.warn { background: rgba(251,191,36,0.1); border-color: rgba(251,191,36,0.3); color: #fbbf24; }
        .ping-indicator.bad { background: rgba(248,113,113,0.1); border-color: rgba(248,113,113,0.3); color: var(--danger-red); }
        .ping-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; animation: pulseDot 1.5s infinite; }
        @keyframes pulseDot { 0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.5;transform:scale(0.7)} }

        /* ФУТЕР */
        .system-footer { text-align: center; padding: 30px 10px 20px; font-size: 11px; opacity: 0.5; }

        /* ГЕНЕРАТОР */
        .generator-card {
            margin-top: 18px; padding: 22px 18px; border-radius: 22px;
            background: linear-gradient(135deg, rgba(244,114,182,0.12), rgba(165,243,252,0.07));
            border: 1px solid rgba(244,114,182,0.3); text-align: center; position: relative; overflow: hidden;
            transition: all 0.4s var(--smooth);
        }
        .generator-card:hover { border-color: var(--accent-berry); box-shadow: 0 8px 24px rgba(244,114,182,0.3); }
        .generator-card h4 { margin: 0 0 6px; font-size: 15px; letter-spacing: 1px; }
        .generator-card p { font-size: 11.5px; opacity: 0.75; margin: 0 0 14px; }
        .btn-generate {
            width: 100%; padding: 13px; border: none; border-radius: 14px;
            background: linear-gradient(135deg, var(--accent-frost), var(--accent-berry));
            color: #1E1B4B; font-weight: 800; font-size: 13px; letter-spacing: 1.3px;
            cursor: pointer; transition: all 0.35s var(--smooth);
            box-shadow: 0 4px 14px rgba(244,114,182,0.35);
        }
        .btn-generate:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(244,114,182,0.55); }
        .btn-generate:active { transform: translateY(0) scale(0.98); }

        /* МОБИЛЬНАЯ */
        @media (max-width: 600px) {
            .container { padding: 18px; padding-top: 70px; }
            .sim-grid { grid-template-columns: repeat(3, 1fr); gap: 8px; }
            .sim-card { padding: 12px 4px; }
            .home-about-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
            .news-tile { flex: 0 0 240px; height: 200px; }
        }

        @media (hover: none), (pointer: coarse) {
            .home-stat, .home-path, .news-tile, .sim-card,
            .memo-box, .info-box, .home-about-card, .quiz-option,
            .hero-btn, .news-arrow-edge, .menu-item, .photo-arrow {
                -webkit-tap-highlight-color: transparent;
                transition: transform 0.35s var(--ultra-smooth), box-shadow 0.35s var(--ultra-smooth),
                            background 0.35s var(--smooth), border-color 0.35s var(--smooth), opacity 0.35s var(--smooth);
            }
            .home-about-card:active, .sim-card:active, .home-stat:active,
            .quiz-option:active, .home-path:active { transform: scale(0.97); opacity: 0.92; }
            .news-tile:active { transform: translateY(-3px) scale(0.98); }
            .menu-item:active { transform: scale(0.98); }
            .hero-btn:active { transform: translateY(2px) scale(0.97); }
            .news-arrow-edge:active { transform: translateY(-50%) scale(0.92); }
        }
    </style>
</head>
<body id="body-tag">
    <div class="rays-container" id="rays"></div>
    
    <div class="hamburger-btn" onclick="toggleMenu()" id="hamburger">
        <div></div><div></div><div></div>
    </div>
    <div class="menu-overlay" id="menu-overlay" onclick="toggleMenu()"></div>
    <div class="side-menu" id="side-menu">

        <!-- Реальные гербы РБ и МВД — показываются при раскрытии -->
        <div class="menu-emblems">
            <img class="menu-emblem-img" src="''' + cld_img('cybershield/emblem_rb', 'png') + '''" 
                 onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Coat_of_Arms_of_Belarus.svg/80px-Coat_of_Arms_of_Belarus.svg.png'"
                 alt="Герб РБ" title="Герб Республики Беларусь">
            <img class="menu-emblem-img" src="''' + cld_img('cybershield/emblem_mvd', 'png') + '''" 
                 onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Emblem_of_the_Ministry_of_Internal_Affairs_%28Belarus%29.svg/80px-Emblem_of_the_Ministry_of_Internal_Affairs_%28Belarus%29.svg.png'"
                 alt="МВД РБ" title="МВД Республики Беларусь">
        </div>

        <a class="menu-item active" id="menu-tab-home" onclick="switchPage('home')">
            <span class="menu-ico">🏠</span><span class="menu-label">ГЛАВНАЯ</span>
        </a>
        <a class="menu-item" id="menu-tab-scanner" onclick="switchPage('scanner')">
            <span class="menu-ico">🛡️</span><span class="menu-label">ПРОВЕРЯТОР</span>
        </a>
        <a class="menu-item" id="menu-tab-info" onclick="switchPage('info')">
            <span class="menu-ico">📚</span><span class="menu-label">ИНФОРМАЦИЯ / ТЕСТЫ</span>
        </a>
        <a class="menu-item" id="menu-tab-password" onclick="switchPage('password')">
            <span class="menu-ico">🔑</span><span class="menu-label">ПАРОЛЬНЫЙ СТРАЖ</span>
        </a>
        
        <hr style="width:80%;border:none;border-top:1px solid rgba(244,114,182,0.3);margin:auto auto 10px auto;">
        
        <a href="https://t.me/CyberNodes_bot" target="_blank" class="tg-super-btn tg-menu-btn">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.19-.08-.05-.19-.02-.27 0-.12.03-1.96 1.25-5.54 3.67-.52.36-.99.54-1.41.53-.46-.01-1.35-.26-2.01-.48-.81-.27-1.46-.42-1.4-.88.03-.23.36-.48.98-.74 3.84-1.68 6.4-2.78 7.68-3.32 3.65-1.53 4.41-1.8 4.9-1.81.11 0 .35.03.48.14.11.09.14.22.14.35-.01.12-.01.24-.02.35z"/></svg>
            НАШ БОТ
        </a>
    </div>

    <div class="container">

        <!-- ============================= ГЛАВНАЯ ============================= -->
        <div id="page-home" class="page-content">

            <section class="home-hero">
                <div class="hero-emblems">
                    <img class="hero-emblem" 
                         src="''' + cld_img('cybershield/emblem_rb', 'png') + '''"
                         onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Coat_of_Arms_of_Belarus.svg/120px-Coat_of_Arms_of_Belarus.svg.png'"
                         alt="Герб Республики Беларусь" title="Республика Беларусь">
                    <img class="hero-emblem" 
                         src="''' + cld_img('cybershield/emblem_mvd', 'png') + '''"
                         onerror="this.src='https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Emblem_of_the_Ministry_of_Internal_Affairs_%28Belarus%29.svg/120px-Emblem_of_the_Ministry_of_Internal_Affairs_%28Belarus%29.svg.png'"
                         alt="МВД Республики Беларусь" title="МВД Республики Беларусь">
                </div>
                <h1 class="home-hero-title">Защита, которая<br><span class="home-hero-accent">говорит на твоём языке</span></h1>
                <p class="home-hero-sub">CyberShield — белорусский интеллектуальный щит. Проверка ссылок, разоблачение мошенников и тренировка реакции на цифровые угрозы — всё в одном месте, простым языком и без рекламы.</p>
                <p class="home-hero-extra">Каждый день в сети появляются десятки новых поддельных сайтов, фейковых писем «от банка» и звонков «из службы безопасности». Мы помогаем понять, как они работают, и учим спокойно, без паники, отказывать злоумышленнику. Проект сделан для всех — школьников, родителей, пожилых людей и тех, кто впервые открыл интернет.</p>
                <div class="home-hero-cta">
                    <a class="hero-btn primary" onclick="switchPage('scanner')">Проверить ссылку</a>
                    <a class="hero-btn ghost" onclick="switchPage('info')">Информация о киберзащите</a>
                </div>
            </section>

            <section class="home-stats">
                <div class="home-stat">
                    <div class="home-stat-num">{{ stats_count }}</div>
                    <div class="home-stat-label">Ссылок проверено</div>
                </div>
                <div class="home-stat">
                    <div class="home-stat-num">{{ total_threats }}</div>
                    <div class="home-stat-label">Угроз раскрыто</div>
                </div>
                <div class="home-stat">
                    <div class="home-stat-num">100%</div>
                    <div class="home-stat-label">Бесплатно и анонимно</div>
                </div>
            </section>

            <section class="home-section">
                <div class="home-section-head">
                    <h3>🛡️ О нашем сервисе</h3>
                    <span>Нажмите на нужный блок — откроется соответствующая вкладка</span>
                </div>
                <div class="home-about-grid">
                    <div class="home-about-card" onclick="switchPage('scanner')">
                        <div class="home-about-icon">🛡️</div>
                        <div class="home-about-title">ПРОВЕРЯТОР ССЫЛОК</div>
                        <div class="home-about-desc">Глубокий анализ URL через VirusTotal и собственный ИИ-вердикт.</div>
                    </div>
                    <div class="home-about-card" onclick="switchPage('info')">
                        <div class="home-about-icon">📚</div>
                        <div class="home-about-title">ИНФОРМАЦИЯ И ТЕСТЫ</div>
                        <div class="home-about-desc">Памятка по безопасности, справочник угроз и кибер-экзамен.</div>
                    </div>
                    <div class="home-about-card" onclick="switchPage('info')">
                        <div class="home-about-icon">🔥</div>
                        <div class="home-about-title">СИМУЛЯЦИИ С ИИ</div>
                        <div class="home-about-desc">Сразитесь с виртуальным мошенником. ИИ Groq отыграет реальную атаку.</div>
                    </div>
                    <div class="home-about-card" onclick="switchPage('password')">
                        <div class="home-about-icon">🔑</div>
                        <div class="home-about-title">ПАРОЛЬНЫЙ СТРАЖ</div>
                        <div class="home-about-desc">Анализ криптостойкости и генератор по-настоящему надёжных паролей.</div>
                    </div>
                </div>

                <div class="home-info-block">
                    <h4 class="shimmer-text">💎 Почему это важно</h4>
                    <p>По данным МВД Беларуси, более 70% хищений со счетов граждан начинаются с обычной ссылки или телефонного звонка. Мошенники не «взламывают» технику — они взламывают невнимательность.</p>
                    <p>Сервис не собирает ваши данные, не сохраняет пароли и не передаёт ссылки третьим лицам.</p>
                    <ul>
                        <li>Полностью бесплатно и без регистрации.</li>
                        <li>Понятный язык — без сложной терминологии.</li>
                        <li>Тренировки построены на реальных белорусских кейсах.</li>
                        <li>Подходит для уроков ОБЖ, классных часов и семейных бесед.</li>
                    </ul>
                </div>
            </section>

            <!-- ===== ВИДЕО (аккордеон, Cloudinary) ===== -->
            <section class="home-section">
                <div class="accord-box" id="accord-video">
                    <div class="accord-header" onclick="toggleAccord('accord-video')">
                        <div>
                            <div class="accord-title">🎬 Видеоматериалы по кибербезопасности</div>
                            <span class="accord-subtitle">Официальные обучающие ролики — Управление «К» МВД РБ</span>
                        </div>
                        <div class="accord-chevron">▼</div>
                    </div>
                    <div class="accord-content">
                        <div class="accord-inner">
                            <div class="vid-tabs" id="vid-tabs">
                                <button class="vid-tab active" data-src="''' + cld_vid('cybershield/video_bezopasnost') + '''" onclick="selectVideo(this)">
                                    <span class="vid-tab-ico">🌐</span>
                                    <span class="vid-tab-text">Безопасность<br>в интернете</span>
                                </button>
                                <button class="vid-tab" data-src="''' + cld_vid('cybershield/video_soobscheniya') + '''" onclick="selectVideo(this)">
                                    <span class="vid-tab-ico">📨</span>
                                    <span class="vid-tab-text">Сообщения<br>от мошенников</span>
                                </button>
                                <button class="vid-tab" data-src="''' + cld_vid('cybershield/video_vygryshi') + '''" onclick="selectVideo(this)">
                                    <span class="vid-tab-ico">🎰</span>
                                    <span class="vid-tab-text">Внезапные<br>выигрыши</span>
                                </button>
                            </div>
                            <div class="vid-player-wrap">
                                <video id="main-video" class="vid-player" controls preload="metadata" playsinline>
                                    <source id="main-video-src" src="''' + cld_vid('cybershield/video_bezopasnost') + '''" type="video/mp4">
                                    Ваш браузер не поддерживает видео.
                                </video>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ===== ФОТО КАРУСЕЛЬ СО СТРЕЛКАМИ (Cloudinary) ===== -->
            <section class="home-section">
                <div class="accord-box" id="accord-photo">
                    <div class="accord-header" onclick="toggleAccord('accord-photo')">
                        <div>
                            <div class="accord-title">🖼️ Информационные материалы</div>
                            <span class="accord-subtitle">Официальные памятки от МВД и Управления «К» Республики Беларусь</span>
                        </div>
                        <div class="accord-chevron">▼</div>
                    </div>
                    <div class="accord-content">
                        <div class="accord-inner">
                            <!-- Карусель с стрелками -->
                            <div class="photo-carousel-wrap">
                                <div class="photo-carousel-track-outer">
                                    <div class="photo-carousel-track" id="photo-track">
                                        <div class="photo-card" onclick="openPhotoModal('''' + cld_img('cybershield/img_apk') + """','Вирусные APK-файлы — как защититься')">
                                            <img src=\"""" + cld_img('cybershield/img_apk') + """\" 
                                                 onerror="this.src='https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=400'"
                                                 alt="Вирусные APK-файлы" loading="lazy">
                                            <div class="photo-card-label">🦠 Вирусные APK-файлы</div>
                                        </div>
                                        <div class="photo-card" onclick="openPhotoModal('""" + cld_img('cybershield/img_kids') + """','Безопасный интернет для детей')">
                                            <img src=\"""" + cld_img('cybershield/img_kids') + """\"
                                                 onerror="this.src='https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=400'"
                                                 alt="Безопасный интернет для детей" loading="lazy">
                                            <div class="photo-card-label">👦 Безопасный интернет</div>
                                        </div>
                                        <div class="photo-card" onclick="openPhotoModal('""" + cld_img('cybershield/img_konkurs', 'png') + """','#КиберПраво: твой щит в сети — конкурс')">
                                            <img src=\"""" + cld_img('cybershield/img_konkurs', 'png') + """\"
                                                 onerror="this.src='https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=400'"
                                                 alt="#КиберПраво конкурс" loading="lazy">
                                            <div class="photo-card-label">🏆 #КиберПраво</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <!-- Стрелки и точки — такой же стиль как у памятки -->
                            <div class="photo-arrows">
                                <button class="photo-arrow" id="photo-prev" aria-label="Назад">&#8249;</button>
                                <div class="photo-dots" id="photo-dots">
                                    <div class="photo-dot active" onclick="goToPhotoSlide(0)"></div>
                                    <div class="photo-dot" onclick="goToPhotoSlide(1)"></div>
                                    <div class="photo-dot" onclick="goToPhotoSlide(2)"></div>
                                </div>
                                <button class="photo-arrow" id="photo-next" aria-label="Вперёд">&#8250;</button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ===== НОВОСТИ ===== -->
            <section class="home-section">
                <div class="home-section-head">
                    <h3>📰 Лента кибербезопасности</h3>
                    <span>Официальные источники — Республика Беларусь</span>
                </div>
                <div class="news-ticker-wrap" id="news-ticker">
                    <button class="news-arrow-edge prev" id="news-prev" aria-label="Назад">&#8249;</button>
                    <button class="news-arrow-edge next" id="news-next" aria-label="Вперёд">&#8250;</button>
                    <div class="news-track" id="news-track">
                        <a href="https://mvd.gov.by/ru/page/upravlenie-k" target="_blank" rel="noopener" class="news-tile">
                            <div class="news-tile-img" style="background-image: url('https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80&fit=crop&auto=format');"></div>
                            <span class="news-tile-pill">МВД РБ</span>
                            <div class="news-tile-fog">
                                <div class="news-tile-title">Управление «К» — киберполиция Беларуси</div>
                                <div class="news-tile-source">mvd.gov.by</div>
                            </div>
                        </a>
                        <a href="https://pravo.by" target="_blank" rel="noopener" class="news-tile">
                            <div class="news-tile-img" style="background-image: url('https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=800&q=80&fit=crop&auto=format');"></div>
                            <span class="news-tile-pill">PRAVO.BY</span>
                            <div class="news-tile-fog">
                                <div class="news-tile-title">Законы РБ о персональных данных</div>
                                <div class="news-tile-source">pravo.by</div>
                            </div>
                        </a>
                        <a href="https://oac.gov.by" target="_blank" rel="noopener" class="news-tile">
                            <div class="news-tile-img" style="background-image: url('https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&q=80&fit=crop&auto=format');"></div>
                            <span class="news-tile-pill">ОАЦ · CERT</span>
                            <div class="news-tile-fog">
                                <div class="news-tile-title">Оперативно-аналитический центр при Президенте РБ</div>
                                <div class="news-tile-source">oac.gov.by</div>
                            </div>
                        </a>
                        <a href="https://www.belta.by/society/" target="_blank" rel="noopener" class="news-tile">
                            <div class="news-tile-img" style="background-image: url('https://images.unsplash.com/photo-1495020689067-958852a7765e?w=800&q=80&fit=crop&auto=format');"></div>
                            <span class="news-tile-pill">БелТА</span>
                            <div class="news-tile-fog">
                                <div class="news-tile-title">Сводки об угрозах и интернет-мошенничестве</div>
                                <div class="news-tile-source">belta.by</div>
                            </div>
                        </a>
                        <a href="https://mir.pravo.by" target="_blank" rel="noopener" class="news-tile">
                            <div class="news-tile-img" style="background-image: url('https://images.unsplash.com/photo-1551434678-e076c223a692?w=800&q=80&fit=crop&auto=format');"></div>
                            <span class="news-tile-pill">КИБЕРПРАВО</span>
                            <div class="news-tile-fog">
                                <div class="news-tile-title">Республиканский проект правового просвещения</div>
                                <div class="news-tile-source">mir.pravo.by</div>
                            </div>
                        </a>
                        <a href="https://www.mvd.gov.by/ru/news" target="_blank" rel="noopener" class="news-tile">
                            <div class="news-tile-img" style="background-image: url('https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800&q=80&fit=crop&auto=format');"></div>
                            <span class="news-tile-pill">СВОДКИ МВД</span>
                            <div class="news-tile-fog">
                                <div class="news-tile-title">Свежие схемы мошенничества и предупреждения</div>
                                <div class="news-tile-source">mvd.gov.by/ru/news</div>
                            </div>
                        </a>
                        <a href="https://www.nbrb.by" target="_blank" rel="noopener" class="news-tile">
                            <div class="news-tile-img" style="background-image: url('https://images.unsplash.com/photo-1601597111158-2fceff292cdc?w=800&q=80&fit=crop&auto=format');"></div>
                            <span class="news-tile-pill">НАЦБАНК РБ</span>
                            <div class="news-tile-fog">
                                <div class="news-tile-title">Финансовая безопасность и защита банковских карт</div>
                                <div class="news-tile-source">nbrb.by</div>
                            </div>
                        </a>
                        <a href="https://www.mininform.gov.by" target="_blank" rel="noopener" class="news-tile">
                            <div class="news-tile-img" style="background-image: url('https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&q=80&fit=crop&auto=format');"></div>
                            <span class="news-tile-pill">МИНИНФОРМ</span>
                            <div class="news-tile-fog">
                                <div class="news-tile-title">Министерство информации РБ — медиаграмотность</div>
                                <div class="news-tile-source">mininform.gov.by</div>
                            </div>
                        </a>
                        <a href="https://edu.gov.by" target="_blank" rel="noopener" class="news-tile">
                            <div class="news-tile-img" style="background-image: url('https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&q=80&fit=crop&auto=format');"></div>
                            <span class="news-tile-pill">МИНОБР РБ</span>
                            <div class="news-tile-fog">
                                <div class="news-tile-title">Цифровая грамотность школьников и студентов</div>
                                <div class="news-tile-source">edu.gov.by</div>
                            </div>
                        </a>
                        <a href="https://kgb.by" target="_blank" rel="noopener" class="news-tile">
                            <div class="news-tile-img" style="background-image: url('https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80&fit=crop&auto=format');"></div>
                            <span class="news-tile-pill">КГБ РБ</span>
                            <div class="news-tile-fog">
                                <div class="news-tile-title">Информационная безопасность государства</div>
                                <div class="news-tile-source">kgb.by</div>
                            </div>
                        </a>
                    </div>
                </div>
            </section>

            <!-- Модальное окно для просмотра фото -->
            <div id="photo-modal" class="photo-modal" onclick="closePhotoModal()">
                <div class="photo-modal-inner" onclick="event.stopPropagation()">
                    <button class="photo-modal-close" onclick="closePhotoModal()">✕</button>
                    <img id="photo-modal-img" src="" alt="">
                    <div id="photo-modal-cap" class="photo-modal-cap"></div>
                </div>
            </div>

        </div>

        <!-- ============================= ПРОВЕРЯТОР ============================= -->
        <div id="page-scanner" class="page-content" style="display:none;opacity:0;">
            <div class="search-card">
                <h1 class="logo-main shimmer-text"><span>🛡️</span> CyberShield</h1>
                <p style="color:#cbd5e1;font-size:14px;">Экспертный анализ сетевого мошенничества</p>
                <form id="check-form" action="/check" method="POST" onsubmit="showLoading()">
                    <div class="input-wrapper">
                        <input type="text" id="url-input-field" name="url" placeholder="Вставьте ссылку" required>
                        <button type="submit" class="btn-scan">ПРОВЕРИТЬ</button>
                    </div>
                </form>
                <div id="loading-overlay">
                    <div class="loader-ring"></div>
                    <p class="shimmer-text" style="font-size:14px;">ЗАПУСК ИИ-СКАНЕРА...</p>
                </div>
            </div>

            {% if verdict_text %}
            <div class="report-card">
                <h3 id="last-verdict-title" style="text-align:center;" class="{{ 'status-danger' if stats and stats.malicious > 0 else 'status-safe' }}">
                    {{ 'УГРОЗА ОБНАРУЖЕНА' if stats and stats.malicious > 0 else 'СИСТЕМА БЕЗОПАСНА' }}
                </h3>
                <div class="stats-grid">
                    <div class="stat-box"><span class="stat-val" style="color:var(--danger-red)">{{stats.malicious}}</span><span style="font-size:10px;">ВИРУСЫ</span></div>
                    <div class="stat-box"><span class="stat-val" style="color:#fbbf24">{{stats.suspicious}}</span><span style="font-size:10px;">РИСКИ</span></div>
                    <div class="stat-box"><span class="stat-val" style="color:var(--safe-green)">{{stats.harmless}}</span><span style="font-size:10px;">ЧИСТО</span></div>
                </div>
                <div class="detail-box {{ 'danger' if stats.malicious > 0 else 'safe' }}">
                    <div class="detail-list">
                        {% for item in detail_items %}
                        <div class="detail-row">
                            <div class="detail-indicator"></div>
                            <div class="detail-info">
                                <span class="detail-label">{{ item.label }}</span>
                                <span class="detail-text">{{ item.text }}</span>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                <div class="ai-box">
                    <button class="voice-btn" id="speak-btn" onclick="speakText()"><span>🔊</span></button>
                    <b class="shimmer-text" style="font-size:11px;display:block;margin-bottom:8px;letter-spacing:1px;">ВЕРДИКТ ИИ</b>
                    <div id="ai-verdict-text">{{ ai_text }}</div>
                </div>
            </div>
            {% endif %}

            <div class="radar-box">
                <h4 class="shimmer-text" style="margin:0 0 5px;font-size:16px;">🌐 ЦЕНТР МОНИТОРИНГА</h4>
                <p style="font-size:11px;color:var(--text-main);opacity:0.7;margin-bottom:15px;">Логирование активности узлов CyberShield</p>
                <div class="radar-circle">
                    <div class="blip blip1"></div>
                    <div class="blip blip2"></div>
                    <div class="blip blip3"></div>
                </div>
                <div class="cyber-logs" id="cyber-logs">
                    <div style="color:var(--safe-green);font-family:monospace;font-size:11px;">> СЕТЬ CyberShield АКТИВНА. ОЖИДАНИЕ ЗАПРОСОВ...</div>
                </div>
            </div>
            <div style="text-align:center;margin-top:16px;">
                <span class="ping-indicator" id="ping-indicator">
                    <span class="ping-dot"></span>
                    <span id="ping-value">--- ms</span>
                </span>
            </div>
        </div>

        <!-- ============================= ИНФОРМАЦИЯ ============================= -->
        <div id="page-info" class="page-content" style="display:none;opacity:0;">
            <div class="memo-box" id="memo-container">
                <div class="memo-header" onclick="toggleAccordion('memo-container')">
                    <span class="shimmer-text">💡 Памятка по безопасности</span>
                    <div class="chevron"></div>
                </div>
                <div class="memo-content">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                        <div><b class="shimmer-text" style="font-size:12px;">Правила проверки:</b><ul style="padding-left:15px;font-size:11px;"><li>Сверяйте домен по каждой букве.</li><li>HTTPS — не гарантия 100% защиты.</li><li>Не переходите по сокращённым ссылкам.</li><li>Проверяйте возраст домена сайта.</li><li>Используйте только CyberShield.</li></ul></div>
                        <div><b class="shimmer-text" style="font-size:12px;">Меры защиты:</b><ul style="padding-left:15px;font-size:11px;"><li>Включите 2FA во всех сервисах.</li><li>Регулярно очищайте кэш и cookie.</li><li>Не сохраняйте пароли в браузере.</li><li>Обновляйте ОС и браузер вовремя.</li><li>Используйте сложные разные пароли.</li></ul></div>
                    </div>
                </div>
            </div>

            <div class="report-card">
                <h3 class="shimmer-text" style="text-align:center;margin-top:0;">📖 СПРАВОЧНИК</h3>
                <p style="font-size:13px;color:var(--text-main);text-align:center;opacity:0.8;margin-bottom:20px;">Продвинутая база данных кибер-угроз нового поколения.</p>
                <div class="detail-box safe">
                    <div class="detail-row">
                        <div class="detail-indicator" style="background:var(--safe-green);box-shadow:0 0 10px var(--safe-green);"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color:var(--safe-green);">ТРОЯН</span>
                            <span class="detail-text">Вредоносное программное обеспечение, маскирующееся под легитимный софт для скрытного внедрения в систему.</span>
                        </div>
                    </div>
                    <div class="detail-row" style="margin-top:10px;">
                        <div class="detail-indicator" style="background:var(--danger-red);box-shadow:0 0 10px var(--danger-red);"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color:var(--danger-red);">ВИШИНГ</span>
                            <span class="detail-text">Форма социальной инженерии через голосовую связь. Метод направлен на получение доступа к данным через манипуляции.</span>
                        </div>
                    </div>
                    <div class="detail-row" style="margin-top:10px;">
                        <div class="detail-indicator" style="background:var(--accent-berry);box-shadow:0 0 10px var(--accent-berry);"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color:var(--accent-berry);">СТИЛЛЕР</span>
                            <span class="detail-text">Вредоносное ПО для кражи конфиденциальных данных: паролей из браузеров, cookies и ключей криптокошельков.</span>
                        </div>
                    </div>
                    <div class="detail-row" style="margin-top:10px;">
                        <div class="detail-indicator" style="background:#ef4444;box-shadow:0 0 10px #ef4444;"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color:#ef4444;">РЕНСОМВЕР</span>
                            <span class="detail-text">Программа-вымогатель. Шифрует файлы на устройстве или блокирует доступ к ОС, требуя от жертвы откуп.</span>
                        </div>
                    </div>
                    <div class="detail-row" style="margin-top:10px;">
                        <div class="detail-indicator" style="background:var(--accent-frost);box-shadow:0 0 10px var(--accent-frost);"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color:var(--accent-frost);">СОЦИАЛЬНАЯ ИНЖЕНЕРИЯ 2.0 (DEEPVOICE)</span>
                            <span class="detail-text">Мошенники используют ИИ для подделки голосов ваших родственников. Если близкий просит деньги — обязательно перезвоните ему лично.</span>
                        </div>
                    </div>
                    <div class="detail-row" style="margin-top:10px;">
                        <div class="detail-indicator" style="background:#fbbf24;box-shadow:0 0 10px #fbbf24;"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color:#fbbf24;">QR-ФИШИНГ (КВИШИНГ)</span>
                            <span class="detail-text">Размещение поддельных QR-кодов поверх настоящих. Всегда проверяйте URL-адрес после сканирования кода камерой.</span>
                        </div>
                    </div>
                    <div class="detail-row" style="margin-top:10px;">
                        <div class="detail-indicator" style="background:#a78bfa;box-shadow:0 0 10px #a78bfa;"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color:#a78bfa;">АТАКА ГОМОГРАФОВ (PUNYCODE)</span>
                            <span class="detail-text">Использование визуально похожих букв из разных алфавитов. Для браузера это разные сайты!</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="game-section" id="game-root">
                <div class="test-tabs">
                    <button class="tab-btn active" id="tab1" onclick="switchTest(1)">ВНИМАТЕЛЬНОСТЬ</button>
                    <button class="tab-btn" id="tab2" onclick="switchTest(2)">ГРАМОТНОСТЬ</button>
                </div>
                <div id="game-header">
                    <h4 class="shimmer-text" style="margin:0 0 15px;font-size:18px;">🎮 Кибер-Экзамен</h4>
                    <button class="btn-scan" id="start-game" style="width:100%;padding:15px;">НАЧАТЬ ТЕСТ</button>
                </div>
                <div id="quiz-area" class="hidden">
                    <div id="quiz-container">
                        <p id="question-num" class="shimmer-text" style="font-size:12px;margin-bottom:8px;"></p>
                        <div id="options"></div>
                    </div>
                </div>
            </div>

            <div class="memo-box active" style="margin-top:20px;">
                <div class="memo-header"><span class="shimmer-text">🤖 ИИ-Помощник CyberShield</span></div>
                <div class="memo-content" style="padding-bottom:20px;">
                    <p style="font-size:12px;margin-bottom:10px;">Спросите нашего ИИ (Groq), как защититься от угроз или что делать в подозрительной ситуации.</p>
                    <div id="helper-chat-box" class="cyber-logs" style="height:180px;background:rgba(0,0,0,0.4);margin-bottom:10px;display:flex;flex-direction:column;gap:8px;">
                        <div style="color:var(--accent-frost);font-size:12px;">ИИ: Привет! Напиши мне свою проблему, и я подскажу, как обезопасить свои данные.</div>
                    </div>
                    <div class="input-wrapper" style="margin-top:0;">
                        <input type="text" id="helper-input" placeholder="Ваш вопрос...">
                        <button class="btn-scan" onclick="sendHelperMessage()">СПРОСИТЬ</button>
                    </div>
                </div>
            </div>
            
            <div class="game-section" id="sim-root">
                <h4 class="shimmer-text" style="margin:0 0 5px;font-size:18px;text-align:center;">🔥 ЗОНА СИМУЛЯЦИЙ</h4>
                <p style="font-size:11px;color:var(--text-main);opacity:0.7;margin-bottom:15px;text-align:center;">Тренировка противодействия реальным угрозам с ИИ Groq</p>
                <div id="sim-selector">
                    <div class="sim-grid">
                        <div class="sim-card" onclick="openSimulation('Социальная инженерия')">
                            <span style="font-size:24px;display:block;margin-bottom:5px;">🎭</span>
                            <b style="font-size:12px;color:var(--accent-berry);">СОЦ. ИНЖЕНЕРИЯ</b>
                        </div>
                        <div class="sim-card" onclick="openSimulation('Техподдержка')">
                            <span style="font-size:24px;display:block;margin-bottom:5px;">👨‍💻</span>
                            <b style="font-size:12px;color:var(--accent-berry);">ТЕХПОДДЕРЖКА</b>
                        </div>
                        <div class="sim-card" onclick="openSimulation('Шантаж')">
                            <span style="font-size:24px;display:block;margin-bottom:5px;">🔒</span>
                            <b style="font-size:12px;color:var(--accent-berry);">ШАНТАЖ</b>
                        </div>
                    </div>
                    <div style="text-align:center;">
                        <p style="font-size:13px;margin-bottom:15px;">Наш ИИ будет писать как реальный мошенник. Твоя цель — не передать личные данные и правильно завершить разговор.</p>
                    </div>
                </div>
                <div id="sim-chat" class="hidden">
                    <div class="chat-container">
                        <div class="chat-header shimmer-text">ДИАЛОГ: НЕИЗВЕСТНЫЙ АБОНЕНТ</div>
                        <div class="chat-messages" id="chat-messages-box"></div>
                        <div class="chat-input-area" id="chat-input-area">
                            <input type="text" id="sim-input" placeholder="Введите ответ..." autocomplete="off">
                            <button class="chat-send-btn" onclick="sendSimMessageReq()">➤</button>
                        </div>
                    </div>
                    <button class="btn-scan" onclick="closeSim()" style="width:100%;margin-top:15px;background:transparent;border:1px solid var(--accent-berry);color:var(--text-main);">ПРЕРВАТЬ СИМУЛЯЦИЮ</button>
                </div>
            </div>
        </div>

        <!-- ============================= ПАРОЛЬНЫЙ СТРАЖ ============================= -->
        <div id="page-password" class="page-content" style="display:none;opacity:0;">
            <div class="search-card">
                <h1 class="logo-main shimmer-text"><span>🔑</span> Парольный Страж</h1>
                <p style="color:#cbd5e1;font-size:14px;">Криптографический анализ надёжности паролей</p>
                <div class="input-wrapper" style="margin-top:20px;">
                    <input type="text" id="password-input" placeholder="Введите пароль для анализа" autocomplete="off">
                </div>
            </div>

            <div id="password-report" style="display:none;">
                <div class="report-card">
                    <h3 class="shimmer-text" style="text-align:center;margin-top:0;">📊 АНАЛИЗ ПАРОЛЯ</h3>
                    <div class="pw-stats">
                        <div class="pw-stat"><span class="pw-stat-val" id="pw-length-val">0</span><span class="pw-stat-label">Символов</span></div>
                        <div class="pw-stat"><span class="pw-stat-val" id="pw-entropy-val">0</span><span class="pw-stat-label">Бит энтропии</span></div>
                        <div class="pw-stat"><span class="pw-stat-val" id="pw-time-val">—</span><span class="pw-stat-label">Время взлома</span></div>
                    </div>
                    <p id="password-result-text" style="text-align:center;font-size:14px;margin:0 0 18px;"></p>
                    <div class="pw-rules">
                        <div class="pw-rule" data-rule="length8"><span class="pw-rule-icon"></span>Минимум 8 символов</div>
                        <div class="pw-rule" data-rule="length12"><span class="pw-rule-icon"></span>Минимум 12 символов</div>
                        <div class="pw-rule" data-rule="upper"><span class="pw-rule-icon"></span>Заглавные буквы (A-Z)</div>
                        <div class="pw-rule" data-rule="lower"><span class="pw-rule-icon"></span>Строчные буквы (a-z)</div>
                        <div class="pw-rule" data-rule="digit"><span class="pw-rule-icon"></span>Цифры (0-9)</div>
                        <div class="pw-rule" data-rule="special"><span class="pw-rule-icon"></span>Спецсимволы (!@#$...)</div>
                        <div class="pw-rule" data-rule="nocommon"><span class="pw-rule-icon"></span>Не из списка утечек</div>
                    </div>
                </div>
            </div>

            <div class="generator-card">
                <h4>🎲 ГЕНЕРАТОР ПАРОЛЕЙ</h4>
                <p>Создайте криптографически стойкий пароль одним нажатием</p>
                <button class="btn-generate" onclick="generateStrongPassword()">СГЕНЕРИРОВАТЬ НАДЁЖНЫЙ ПАРОЛЬ</button>
            </div>

            <div class="home-info-block" style="margin-top:20px;">
                <h4 class="shimmer-text">🔐 Правила создания паролей</h4>
                <ul>
                    <li>Используйте разные пароли для каждого сервиса.</li>
                    <li>Не используйте личные данные: имя, дату рождения.</li>
                    <li>Минимальная длина — 12 символов для важных аккаунтов.</li>
                    <li>Храните пароли в надёжном менеджере (Bitwarden, KeePass).</li>
                    <li>Включите двухфакторную аутентификацию везде, где возможно.</li>
                </ul>
            </div>
        </div>

        <div class="system-footer">
            CyberShield · Защита цифрового пространства · Беларусь<br>
            <small>При поддержке МВД РБ · Управление «К»</small>
        </div>
    </div>

    <script>
        // === ЛУЧИ ===
        (function buildRays(){
            const container = document.getElementById('rays');
            const configs = [
                {cls:'ray',      count:18, minDur:8,  maxDur:18, minDelay:0, maxDelay:16},
                {cls:'ray-thick',count:6,  minDur:12, maxDur:22, minDelay:0, maxDelay:20},
                {cls:'ray-short',count:10, minDur:5,  maxDur:10, minDelay:0, maxDelay:12},
            ];
            const anims = ['rise','rise','rise','rise-fade-mid','rise-fade-late'];
            configs.forEach(({cls,count,minDur,maxDur,minDelay,maxDelay})=>{
                for(let i=0;i<count;i++){
                    const el = document.createElement('div');
                    el.className = cls;
                    const dur  = (minDur  + Math.random()*(maxDur-minDur)).toFixed(2);
                    const dlay = (minDelay + Math.random()*(maxDelay-minDelay)).toFixed(2);
                    const left = (Math.random()*100).toFixed(1);
                    const anim = (cls==='ray') ? anims[Math.floor(Math.random()*anims.length)] : 'rise';
                    el.style.cssText = `left:${left}%;animation-name:${anim};animation-duration:${dur}s;animation-delay:-${dlay}s;`;
                    container.appendChild(el);
                }
            });
        })();

        // === МЕНЮ ===
        function toggleMenu(){
            const m = document.getElementById('side-menu');
            const h = document.getElementById('hamburger');
            const o = document.getElementById('menu-overlay');
            const isOpen = m.classList.toggle('active');
            h.classList.toggle('open', isOpen);
            o.classList.toggle('active', isOpen);
        }

        // === ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК ===
        function switchPage(page){
            const pages = ['home','scanner','info','password'];
            pages.forEach(p=>{
                const el = document.getElementById('page-'+p);
                const mi = document.getElementById('menu-tab-'+p);
                if(p===page){
                    el.style.display='block';
                    setTimeout(()=>el.style.opacity='1',10);
                    if(mi) mi.classList.add('active');
                } else {
                    el.style.opacity='0';
                    el.style.display='none';
                    if(mi) mi.classList.remove('active');
                }
            });
            const m = document.getElementById('side-menu');
            const h = document.getElementById('hamburger');
            const o = document.getElementById('menu-overlay');
            m.classList.remove('active'); h.classList.remove('open'); o.classList.remove('active');
            window.scrollTo({top:0,behavior:'smooth'});
        }

        // === АККОРДЕОН (видео/фото) ===
        function toggleAccord(id){
            const box = document.getElementById(id);
            box.classList.toggle('open');
        }

        // === АККОРДЕОН (информация) ===
        function toggleAccordion(id){
            const box = document.getElementById(id);
            box.classList.toggle('active');
        }

        // === ВЫБОР ВИДЕО ===
        function selectVideo(btn){
            document.querySelectorAll('.vid-tab').forEach(b=>b.classList.remove('active'));
            btn.classList.add('active');
            const src = btn.dataset.src;
            const video = document.getElementById('main-video');
            const source = document.getElementById('main-video-src');
            source.src = src;
            video.load();
        }

        // === ФОТО КАРУСЕЛЬ СО СТРЕЛКАМИ ===
        (function setupPhotoCarousel(){
            const track = document.getElementById('photo-track');
            if (!track) return;
            const cards = track.querySelectorAll('.photo-card');
            const total = cards.length;
            let current = 0;

            function getSlideWidth(){
                if (!cards[0]) return 0;
                return cards[0].offsetWidth + 14;
            }

            function updateDots(){
                document.querySelectorAll('.photo-dot').forEach((d,i)=>{
                    d.classList.toggle('active', i===current);
                });
            }

            function goTo(idx){
                if (idx < 0) idx = total - 1;
                if (idx >= total) idx = 0;
                current = idx;
                const w = getSlideWidth();
                track.style.transform = 'translateX(-' + (current * w) + 'px)';
                updateDots();
            }

            window.goToPhotoSlide = goTo;

            const prev = document.getElementById('photo-prev');
            const next = document.getElementById('photo-next');
            if(prev) prev.addEventListener('click', ()=>goTo(current-1));
            if(next) next.addEventListener('click', ()=>goTo(current+1));

            // touch/swipe
            let touchStartX = 0;
            track.addEventListener('touchstart', e=>{ touchStartX = e.touches[0].clientX; },{passive:true});
            track.addEventListener('touchend', e=>{
                const dx = e.changedTouches[0].clientX - touchStartX;
                if(Math.abs(dx)>40){ dx<0 ? goTo(current+1) : goTo(current-1); }
            },{passive:true});

            window.addEventListener('resize', ()=>goTo(current));
            updateDots();
        })();

        // === МОДАЛЬНОЕ ОКНО ФОТО ===
        function openPhotoModal(src, cap){
            const modal = document.getElementById('photo-modal');
            document.getElementById('photo-modal-img').src = src;
            document.getElementById('photo-modal-cap').textContent = cap;
            modal.classList.add('open');
            document.body.style.overflow = 'hidden';
        }
        function closePhotoModal(){
            document.getElementById('photo-modal').classList.remove('open');
            document.body.style.overflow = '';
        }

        // === ЗАГРУЗКА ===
        function showLoading(){
            document.getElementById('loading-overlay').style.display='block';
        }

        // === ГОЛОС ===
        function speakText(){
            const text = document.getElementById('ai-verdict-text')?.innerText || '';
            if(text && 'speechSynthesis' in window){
                window.speechSynthesis.cancel();
                const utt = new SpeechSynthesisUtterance(text);
                utt.lang='ru-RU'; utt.rate=0.95;
                window.speechSynthesis.speak(utt);
            }
        }

        // === РАДАР ЛОГИ ===
        function addRadarLog(msg, type='info'){
            const logs = document.getElementById('cyber-logs');
            if(!logs) return;
            const colors = {info:'var(--accent-frost)', safe:'var(--safe-green)', danger:'var(--danger-red)', warn:'#fbbf24'};
            const line = document.createElement('div');
            line.style.cssText = `color:${colors[type]||colors.info};font-family:monospace;font-size:11px;animation:ultraEntrance 0.5s var(--ultra-smooth);`;
            line.textContent = '> ' + msg;
            logs.appendChild(line);
            logs.scrollTop = logs.scrollHeight;
        }

        // === ТЕСТ ===
        const questions1 = [
            {q:"Банк просит PIN по телефону?",win:"Положить трубку",lose:"Назвать PIN"},
            {q:"Незнакомая ссылка от друга в мессенджере?",win:"Проверить в CyberShield",lose:"Открыть сразу"},
            {q:"Сайт просит отключить антивирус?",win:"Закрыть страницу",lose:"Отключить антивирус"},
            {q:"Выиграл приз, нужно перевести «комиссию»?",win:"Игнорировать",lose:"Перевести деньги"},
            {q:"HTTPS на сайте — значит он безопасен?",win:"Нет, это не гарантия",lose:"Да, полностью безопасен"},
            {q:"Незнакомец просит реквизиты карты?",win:"Отказать",lose:"Сообщить"},
            {q:"Пришло письмо «вы выиграли iPhone»?",win:"Удалить как спам",lose:"Перейти по ссылке"},
            {q:"Сайт банка выглядит как настоящий, но URL другой?",win:"Закрыть — это фишинг",lose:"Войти в аккаунт"},
            {q:"Звонят из «службы безопасности» банка?",win:"Перезвонить самому на официальный номер",lose:"Сообщить данные карты"},
            {q:"Приложение просит доступ к SMS?",win:"Отказать подозрительному приложению",lose:"Разрешить всегда"},
        ];
        const questions2 = [
            {q:"Что такое фишинг?",win:"Поддельный сайт для кражи данных",lose:"Вид рыбной ловли"},
            {q:"Что такое двухфакторная аутентификация?",win:"Дополнительный код подтверждения входа",lose:"Два пароля для почты"},
            {q:"Что означает HTTPS?",win:"Шифрованное соединение с сайтом",lose:"Сайт проверен государством"},
            {q:"Что такое троян?",win:"Вредонос под видом легального ПО",lose:"Антивирус Греции"},
            {q:"Что такое социальная инженерия?",win:"Манипуляции для получения данных",lose:"Профессия инженера"},
            {q:"Что делать при утечке пароля?",win:"Срочно сменить и включить 2FA",lose:"Подождать и посмотреть"},
            {q:"Что такое VPN?",win:"Шифрованный туннель для интернет-трафика",lose:"Вирус защиты"},
            {q:"Что такое ренсомвер?",win:"Вымогатель, шифрующий файлы",lose:"Антиспам-фильтр"},
            {q:"Как проверить возраст домена?",win:"Через WHOIS-сервис",lose:"Посмотреть в браузере"},
            {q:"Что такое стиллер?",win:"ПО для кражи паролей и cookies",lose:"Программа для уборки"},
        ];
        let activeSet=[...questions1], currentQ=0, score=0, canClick=true;
        function switchTest(num){
            document.getElementById('tab1').classList.toggle('active',num===1);
            document.getElementById('tab2').classList.toggle('active',num===2);
            activeSet=(num===1)?[...questions1]:[...questions2];
            resetGameUI();
        }
        function initGame(){
            if(activeSet.length===0) activeSet=[...questions1];
            activeSet.sort(()=>Math.random()-0.5);
            currentQ=0; score=0; canClick=true;
            resetGameUI();
            document.getElementById('game-header').style.display='none';
            document.getElementById('quiz-area').classList.remove('hidden');
            showQuestion();
        }
        document.getElementById('start-game').onclick=initGame;
        function showQuestion(){
            canClick=true;
            const q=activeSet[currentQ];
            document.getElementById('question-num').innerText=`ШАГ ${currentQ+1} ИЗ ${activeSet.length}`;
            const options=[{t:q.win,w:true},{t:q.lose,w:false}].sort(()=>Math.random()-0.5);
            document.getElementById('options').innerHTML=`
                <div class="slide-left-to-right">
                    <p style="font-weight:bold;margin-bottom:15px;font-size:15px;">${q.q}</p>
                    <div class="quiz-option" onclick="handleSelect(this,${options[0].w})">${options[0].t}</div>
                    <div class="quiz-option" onclick="handleSelect(this,${options[1].w})">${options[1].t}</div>
                </div>`;
        }
        function handleSelect(el,isCorrect){
            if(!canClick) return;
            canClick=false;
            if(isCorrect){score++;el.classList.add('correct');}else{el.classList.add('wrong');}
            setTimeout(()=>{
                const sw=document.querySelector('.slide-left-to-right');
                if(sw){sw.style.transition='all 0.4s var(--smooth)';sw.style.transform='translateX(150%)';sw.style.opacity='0';}
                setTimeout(()=>{ if(currentQ<activeSet.length-1){currentQ++;showQuestion();}else{finishQuiz();} },400);
            },400);
        }
        function finishQuiz(){
            let rank="Новичок 🛡️";
            if(score>=4)rank="Ученик 🔍";
            if(score>=7)rank="Специалист 🧠";
            if(score==10)rank="Кибер-Эксперт 👑";
            addRadarLog(`ТЕСТ ЗАВЕРШЕН. РЕЗУЛЬТАТ: ${score}/10. РАНГ: ${rank}`,score>=7?'safe':'warn');
            document.getElementById('quiz-area').innerHTML=`
                <div style="text-align:center;animation:ultraEntrance 0.8s var(--ultra-smooth);">
                    <h4 class="shimmer-text" style="font-size:22px;margin-bottom:15px;">ИТОГ: ${score}/${activeSet.length}</h4>
                    <p style="font-size:16px;margin-bottom:25px;">Твой ранг:<br><b style="font-size:18px;">${rank}</b></p>
                    <button id="restart-btn" class="btn-scan" style="width:100%;padding:15px;">ЗАНОВО</button>
                </div>`;
            document.getElementById('restart-btn').onclick=initGame;
        }
        function resetGameUI(){
            document.getElementById('game-header').style.display='block';
            document.getElementById('quiz-area').classList.add('hidden');
            document.getElementById('quiz-area').innerHTML='<div id="quiz-container"><p id="question-num" class="shimmer-text"></p><div id="options"></div></div>';
        }

        if(localStorage.getItem('theme')==='light') document.body.classList.add('light-mode');

        // === ЛЕНТА НОВОСТЕЙ ===
        (function setupNewsTicker(){
            const wrap=document.getElementById('news-ticker');
            const track=document.getElementById('news-track');
            if(!wrap||!track) return;
            const originals=Array.from(track.children);
            originals.forEach(el=>{ const clone=el.cloneNode(true);clone.setAttribute('aria-hidden','true');track.appendChild(clone); });
            let pos=0, halfWidth=0, autoTimer=null, isHover=false, isDragging=false;
            let startX=0, startPos=0, pointerMoved=0;
            const DRAG_THRESHOLD=6, TILE_STEP=284, AUTO_INTERVAL_MS=35, AUTO_SPEED_PX=0.6;
            function recalc(){ halfWidth=track.scrollWidth/2; }
            recalc(); window.addEventListener('resize',recalc);
            function applyTransform(){
                if(halfWidth>0){ if(pos<=-halfWidth)pos+=halfWidth; if(pos>0)pos-=halfWidth; }
                track.style.transform='translateX('+pos+'px)';
            }
            function tick(){ if(isHover||isDragging)return; pos-=AUTO_SPEED_PX; track.style.transition='none'; applyTransform(); }
            function startAuto(){ if(autoTimer)return; autoTimer=setInterval(tick,AUTO_INTERVAL_MS); }
            wrap.addEventListener('mouseenter',()=>{isHover=true;}); wrap.addEventListener('mouseleave',()=>{isHover=false;});
            const prev=document.getElementById('news-prev'); const next=document.getElementById('news-next');
            function smoothJump(delta){ track.style.transition='transform 0.6s var(--ultra-smooth)'; pos+=delta; applyTransform(); setTimeout(()=>{track.style.transition='none';},650); }
            if(prev)prev.addEventListener('click',()=>smoothJump(TILE_STEP));
            if(next)next.addEventListener('click',()=>smoothJump(-TILE_STEP));
            function onDown(e){ isDragging=true; pointerMoved=0; startX=(e.touches?e.touches[0].clientX:e.clientX); startPos=pos; track.classList.add('is-dragging'); track.style.transition='none'; }
            function onMove(e){ if(!isDragging)return; const x=(e.touches?e.touches[0].clientX:e.clientX); const dx=x-startX; pointerMoved=Math.abs(dx); pos=startPos+dx; applyTransform(); if(pointerMoved>DRAG_THRESHOLD&&e.cancelable)e.preventDefault(); }
            function onUp(){ if(!isDragging)return; isDragging=false; track.classList.remove('is-dragging'); }
            track.querySelectorAll('a.news-tile').forEach(a=>{ a.addEventListener('click',function(ev){ if(pointerMoved>DRAG_THRESHOLD){ev.preventDefault();ev.stopPropagation();} }); });
            track.addEventListener('mousedown',onDown); window.addEventListener('mousemove',onMove); window.addEventListener('mouseup',onUp);
            track.addEventListener('touchstart',onDown,{passive:true}); track.addEventListener('touchmove',onMove,{passive:false}); track.addEventListener('touchend',onUp);
            setTimeout(()=>{ recalc(); startAuto(); },200);
        })();

        // === СИМУЛЯЦИЯ ===
        let currentSimTheme="", simHistory=[], simTurn=0;
        function openSimulation(themeName){
            currentSimTheme=themeName;
            document.getElementById('sim-selector').classList.add('hidden');
            document.getElementById('sim-chat').classList.remove('hidden');
            document.getElementById('chat-messages-box').innerHTML='';
            document.getElementById('chat-input-area').style.display='flex';
            simHistory=[]; simTurn=0;
            addRadarLog(`ЗАПУСК ИИ-СИМУЛЯЦИИ: ${themeName}`,'warn');
            appendBotMessage("ИИ печатает...");
            fetch('/cs/sim_chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:'',history:[],theme:currentSimTheme,is_start:true,turn:0})})
            .then(r=>r.json()).then(data=>{ const box=document.getElementById('chat-messages-box'); box.lastChild.remove(); appendBotMessage(data.reply); simHistory=data.history; simTurn=data.turn||0; })
            .catch(()=>{ document.getElementById('chat-messages-box').lastChild.remove(); appendBotMessage("Ошибка сети. Модель недоступна."); });
        }
        function closeSim(){ document.getElementById('sim-chat').classList.add('hidden'); document.getElementById('sim-selector').classList.remove('hidden'); }
        function appendBotMessage(text){ const box=document.getElementById('chat-messages-box'); const msg=document.createElement('div'); msg.className='msg bot'; msg.innerText=text; box.appendChild(msg); box.scrollTop=box.scrollHeight; }
        function appendUserMessage(text){ const box=document.getElementById('chat-messages-box'); const msg=document.createElement('div'); msg.className='msg user'; msg.innerText=text; box.appendChild(msg); box.scrollTop=box.scrollHeight; }
        function sendSimMessageReq(){
            const input=document.getElementById('sim-input'); const text=input.value.trim(); if(!text)return;
            appendUserMessage(text); input.value=''; appendBotMessage("ИИ печатает...");
            fetch('/cs/sim_chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:text,history:simHistory,theme:currentSimTheme,is_start:false,turn:simTurn})})
            .then(r=>r.json()).then(data=>{ const box=document.getElementById('chat-messages-box'); box.lastChild.remove(); simTurn=data.turn||simTurn; if(data.is_ended){appendBotMessage(data.reply);setTimeout(()=>finishChatSimFinal(data.score,null),600);}else{appendBotMessage(data.reply);simHistory=data.history;} })
            .catch(()=>{ document.getElementById('chat-messages-box').lastChild.remove(); appendBotMessage("Произошла ошибка связи с Groq."); });
        }
        document.getElementById('sim-input').addEventListener('keypress',function(e){ if(e.key==='Enter')sendSimMessageReq(); });
        function finishChatSimFinal(score,finalMsg){
            document.getElementById('chat-input-area').style.display='none';
            if(finalMsg)appendBotMessage(finalMsg);
            let verdict=score>50?"✅ ВЫ СПРАВИЛИСЬ!":"❌ ДАННЫЕ СКОМПРОМЕТИРОВАНЫ!";
            addRadarLog(`СИМУЛЯЦИЯ ЗАВЕРШЕНА. ВЫЖИВАЕМОСТЬ: ${score}%`,score>50?'safe':'danger');
            setTimeout(()=>{
                const box=document.getElementById('chat-messages-box');
                const resultMsg=document.createElement('div');
                resultMsg.style.cssText='text-align:center;padding:20px;background:rgba(0,0,0,0.4);border-radius:15px;margin-top:10px;animation:ultraEntrance 0.8s var(--ultra-smooth);';
                resultMsg.innerHTML=`<h3 class="shimmer-text" style="margin-top:0;">${verdict}</h3><p style="font-size:24px;font-weight:bold;margin:10px 0;color:${score>50?'var(--safe-green)':'var(--danger-red)'}">${score}% УСПЕХА</p><button class="btn-scan" onclick="closeSim()" style="margin-top:10px;width:100%;">НАЗАД В МЕНЮ</button>`;
                box.appendChild(resultMsg); box.scrollTop=box.scrollHeight;
            },800);
        }

        // === ИИ ПОМОЩНИК ===
        let helperHistory=[];
        function sendHelperMessage(){
            const input=document.getElementById('helper-input'); const text=input.value.trim(); if(!text)return;
            const box=document.getElementById('helper-chat-box');
            box.innerHTML+=`<div style="color:var(--safe-green);font-size:12px;"><b>Вы:</b> ${text}</div>`;
            input.value=''; box.scrollTop=box.scrollHeight;
            fetch('/cs/helper_chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:text,history:helperHistory})})
            .then(r=>r.json()).then(data=>{ box.innerHTML+=`<div style="color:var(--accent-frost);font-size:12px;"><b>ИИ:</b> ${data.reply}</div>`; helperHistory=data.history; box.scrollTop=box.scrollHeight; })
            .catch(()=>{ box.innerHTML+=`<div style="color:var(--danger-red);font-size:12px;">Система временно недоступна.</div>`; });
        }
        document.getElementById('helper-input').addEventListener('keypress',function(e){ if(e.key==='Enter')sendHelperMessage(); });

        // === ПАРОЛЬНЫЙ СТРАЖ ===
        const COMMON_PASSWORDS=new Set(["123456","123456789","12345678","12345","qwerty","password","111111","123123","abc123","1234567","000000","iloveyou","qwerty123","admin","welcome","monkey","dragon","letmein","football","passw0rd","master","pass","qazwsx","qwerty1","123qwe","ytrewq","klaster","superman","11111111","sunshine","1q2w3e4r","zxcvbnm"]);
        function analyzePassword(pw){
            const rules={length8:pw.length>=8,length12:pw.length>=12,upper:/[A-ZА-ЯЁ]/.test(pw),lower:/[a-zа-яё]/.test(pw),digit:/\d/.test(pw),special:/[^A-Za-zА-Яа-яЁё0-9]/.test(pw),nocommon:pw.length>0&&!COMMON_PASSWORDS.has(pw.toLowerCase())};
            let pool=0;
            if(rules.lower)pool+=26; if(rules.upper)pool+=26; if(rules.digit)pool+=10; if(rules.special)pool+=32;
            const entropy=pw.length>0&&pool>0?Math.round(pw.length*Math.log2(pool)):0;
            const guessesPerSec=1e10; const seconds=pool>0?Math.pow(pool,pw.length)/guessesPerSec:0;
            let timeStr="мгновенно";
            if(!rules.nocommon&&pw.length>0)timeStr="мгновенно";
            else if(seconds<1)timeStr="мгновенно";
            else if(seconds<60)timeStr=Math.round(seconds)+" сек";
            else if(seconds<3600)timeStr=Math.round(seconds/60)+" мин";
            else if(seconds<86400)timeStr=Math.round(seconds/3600)+" ч";
            else if(seconds<31536000)timeStr=Math.round(seconds/86400)+" дн";
            else if(seconds<31536000*1000)timeStr=Math.round(seconds/31536000)+" лет";
            else timeStr="века";
            const score=Object.values(rules).filter(Boolean).length;
            let level,color;
            if(pw.length===0){level="Введите пароль для анализа";color="var(--text-main)";}
            else if(!rules.nocommon){level="❌ КРИТИЧНО: пароль есть в утечках, взлом мгновенный";color="var(--danger-red)";}
            else if(score<=3){level="⚠️ СЛАБЫЙ — лёгкая мишень для атаки";color="var(--danger-red)";}
            else if(score<=5){level="🟡 СРЕДНИЙ — приемлемо для непубличных аккаунтов";color="#fbbf24";}
            else if(score===6){level="✅ ХОРОШИЙ — устойчив к большинству атак";color="var(--safe-green)";}
            else{level="🛡️ КРЕПОСТЬ — высочайшая криптостойкость";color="var(--safe-green)";}
            return{rules,entropy,timeStr,level,color};
        }
        function renderPasswordReport(pw){
            const report=document.getElementById('password-report');
            if(pw.length===0){report.style.display='none';return;}
            if(report.style.display==='none'){report.style.display='block';report.style.animation='ultraEntrance 0.6s var(--ultra-smooth)';}
            const a=analyzePassword(pw);
            document.getElementById('pw-length-val').innerText=pw.length;
            document.getElementById('pw-entropy-val').innerText=a.entropy;
            document.getElementById('pw-time-val').innerText=a.timeStr;
            document.querySelectorAll('.pw-rule').forEach(row=>{ const r=row.dataset.rule; row.classList.toggle('active',!!a.rules[r]); });
            const result=document.getElementById('password-result-text');
            result.innerText=a.level; result.style.color=a.color; result.style.fontWeight='bold';
        }
        function generateStrongPassword(){
            const lower="abcdefghijkmnpqrstuvwxyz",upper="ABCDEFGHJKLMNPQRSTUVWXYZ",digits="23456789",special="!@#$%^&*()_+-=[]{}";
            const all=lower+upper+digits+special; let pw="";
            pw+=lower[Math.floor(Math.random()*lower.length)];
            pw+=upper[Math.floor(Math.random()*upper.length)];
            pw+=digits[Math.floor(Math.random()*digits.length)];
            pw+=special[Math.floor(Math.random()*special.length)];
            for(let i=0;i<12;i++)pw+=all[Math.floor(Math.random()*all.length)];
            pw=pw.split('').sort(()=>Math.random()-0.5).join('');
            const input=document.getElementById('password-input'); input.value=pw; renderPasswordReport(pw); input.focus();
        }
        document.getElementById('password-input').addEventListener('input',function(e){ renderPasswordReport(e.target.value); });

        // === ПИНГ ===
        async function measurePing(){
            const indicator=document.getElementById('ping-indicator'); const valueEl=document.getElementById('ping-value');
            const start=performance.now();
            try{
                const res=await fetch('/cs/ping?t='+start,{cache:'no-store'});
                if(!res.ok)throw new Error('bad');
                const ms=Math.round(performance.now()-start);
                valueEl.innerText=ms+' ms'; indicator.classList.remove('warn','bad');
                if(ms>600)indicator.classList.add('bad'); else if(ms>250)indicator.classList.add('warn');
            }catch(e){ valueEl.innerText='--- ms'; indicator.classList.remove('warn'); indicator.classList.add('bad'); }
        }
        measurePing(); setInterval(measurePing,5000);
    </script>
</body>
</html>
'''

def _ru_plural(n, forms):
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11: return forms[0]
    if 2 <= n10 <= 4 and not (12 <= n100 <= 14): return forms[1]
    return forms[2]

@app.route('/')
def home():
    scans, viruses = get_real_stats()
    scans_word = _ru_plural(scans, ('ПРОВЕРКА', 'ПРОВЕРКИ', 'ПРОВЕРОК'))
    return render_template_string(
        HTML_LAYOUT,
        total_scans=scans, total_threats=viruses,
        stats_count=scans, scans_word=scans_word,
        current_page='home',
        verdict_text=None, stats=None, detail_items=[], ai_text=''
    )

@app.route('/check', methods=['POST'])
def check():
    url = request.form.get('url', '').strip()
    scans, viruses = get_real_stats()
    time.sleep(1)
    verdict_text = None
    stats = None
    detail_items = []
    ai_text = ''
    try:
        if not VT_API_KEY:
            raise Exception("VT_API_KEY not set")
        res = requests.post(
            "https://www.virustotal.com/api/v3/urls",
            data={"url": url},
            headers={"x-apikey": VT_API_KEY},
            timeout=20
        )
        analysis_id = res.json()['data']['id']
        data = None
        for _ in range(6):
            time.sleep(5)
            report = requests.get(
                f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                headers={"x-apikey": VT_API_KEY},
                timeout=20
            )
            if report.status_code == 200:
                temp_data = report.json()['data']['attributes']
                if temp_data['status'] == 'completed' or temp_data['stats']['harmless'] > 0:
                    data = temp_data
                    break

        if data:
            stats = data['stats']
            update_real_stats(is_virus=stats['malicious'] > 0)
            verdict_text = 'УГРОЗА' if stats['malicious'] > 0 else 'ЧИСТО'
            ai_text = ask_ai_opinion(url, stats)

            parsed = re.match(r'https?://([^/]+)', url)
            domain = parsed.group(1) if parsed else url
            is_safe = stats['malicious'] == 0

            detail_items = [
                {'label': 'ПРОВЕРЯЕМЫЙ URL', 'text': url[:60] + ('...' if len(url) > 60 else '')},
                {'label': 'ДОМЕН', 'text': domain},
                {'label': 'АНТИВИРУСОВ ПРОВЕРИЛО', 'text': str(sum(stats.values()))},
                {'label': 'ВРЕДОНОСНЫХ СИГНАТУР', 'text': str(stats['malicious'])},
                {'label': 'ПОДОЗРИТЕЛЬНЫХ', 'text': str(stats['suspicious'])},
                {'label': 'БЕЗОПАСНЫХ ПРОВЕРОК', 'text': str(stats['harmless'])},
                {'label': 'СТАТУС', 'text': '✅ БЕЗОПАСНО' if is_safe else '⚠️ УГРОЗА ОБНАРУЖЕНА'},
            ]
        else:
            ai_text = "Анализ занял слишком много времени. Повторите позже."
            verdict_text = 'ОШИБКА'

    except Exception as e:
        ai_text = f"Ошибка анализа: {str(e)[:80]}"
        verdict_text = 'ОШИБКА'

    scans2, viruses2 = get_real_stats()
    scans_word = _ru_plural(scans2, ('ПРОВЕРКА', 'ПРОВЕРКИ', 'ПРОВЕРОК'))
    return render_template_string(
        HTML_LAYOUT,
        total_scans=scans2, total_threats=viruses2,
        stats_count=scans2, scans_word=scans_word,
        current_page='scanner',
        verdict_text=verdict_text, stats=stats,
        detail_items=detail_items, ai_text=ai_text
    )

@app.route('/cs/ping')
def ping():
    return jsonify({'ok': True})

@app.route('/cs/sim_chat', methods=['POST'])
def sim_chat():
    data = request.json
    text = data.get('text', '')
    history = data.get('history', [])
    theme = data.get('theme', '')
    is_start = data.get('is_start', False)
    turn = data.get('turn', 0)

    if not GROQ_API_KEY:
        return jsonify({'reply': 'GROQ_API_KEY не настроен.', 'history': history, 'turn': turn, 'is_ended': False})

    SIM_MAX_TURNS = 4
    system_prompt = (
        f"Ты — мошенник, симулирующий атаку типа «{theme}». "
        "Разговаривай убедительно, давай давление. "
        "Цель пользователя — не поддаться. "
        "После 4 ходов подведи итог и выдай JSON: {{\"score\": 0-100, \"verdict\": \"...\"}}"
    )

    if is_start:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Начни симуляцию атаки типа «{theme}». Первое сообщение мошенника."}
        ]
    else:
        messages = [{"role": "system", "content": system_prompt}] + history
        messages.append({"role": "user", "content": text})
        turn += 1

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": "llama3-8b-8192", "messages": messages, "max_tokens": 400, "temperature": 0.8},
            timeout=20
        )
        reply = r.json()['choices'][0]['message']['content']
        messages.append({"role": "assistant", "content": reply})

        is_ended = turn >= SIM_MAX_TURNS
        score = 70
        if is_ended:
            try:
                m = re.search(r'"score"\s*:\s*(\d+)', reply)
                if m: score = int(m.group(1))
            except: pass

        return jsonify({'reply': reply, 'history': messages[1:], 'turn': turn, 'is_ended': is_ended, 'score': score})
    except Exception as e:
        return jsonify({'reply': f'Ошибка: {str(e)[:60]}', 'history': history, 'turn': turn, 'is_ended': False})

@app.route('/cs/helper_chat', methods=['POST'])
def helper_chat():
    data = request.json
    text = data.get('text', '')
    history = data.get('history', [])

    if not GROQ_API_KEY:
        return jsonify({'reply': 'GROQ_API_KEY не настроен. Добавьте ключ в переменные окружения.', 'history': history})

    system_prompt = (
        "Ты — CyberShield AI, эксперт по кибербезопасности. "
        "Отвечай кратко, по-русски, практическими советами. "
        "Помогай пользователям защититься от мошенников и угроз в интернете."
    )
    messages = [{"role": "system", "content": system_prompt}] + history
    messages.append({"role": "user", "content": text})

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": "llama3-8b-8192", "messages": messages, "max_tokens": 300, "temperature": 0.5},
            timeout=20
        )
        reply = r.json()['choices'][0]['message']['content']
        messages.append({"role": "assistant", "content": reply})
        return jsonify({'reply': reply, 'history': messages[1:]})
    except Exception as e:
        return jsonify({'reply': f'Ошибка связи: {str(e)[:60]}', 'history': history})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
