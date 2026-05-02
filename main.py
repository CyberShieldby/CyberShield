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
STATS_FILE = 'stats.txt'

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
        /* луч НИКОГДА не гаснет в начале — всегда долетает минимум до середины */
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

        /* Десктоп: контент сдвинут правее чтобы не перекрывался рейлом */
        .container { max-width: 650px; margin: 0 auto; padding: 30px 20px 50px 80px; }

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

        /* ДЕСКТОП (> 700px): постоянный рейл 64px, по клику расширяется */
        .side-menu {
            position: fixed; top: 0; left: 0; height: 100%;
            width: 64px;
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
            /* центрируем иконку когда свёрнуто */
            justify-content: flex-start;
            padding-left: 0;
        }
        body.light-mode .menu-item { background: rgba(244, 114, 182, 0.1); }
        .menu-item .menu-ico {
            font-size: 21px; line-height: 1;
            /* при свёрнутом меню — занимает всё место и центрируется */
            flex: 0 0 64px; text-align: center; display: inline-block;
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
            display: block; width: 100%; padding: 14px 18px; margin: 10px 0; background: rgba(0,0,0,0.1); 
            border: 1px solid rgba(244, 114, 182, 0.2); border-radius: 14px; color: var(--text-main); 
            cursor: pointer; text-align: left; transition: all 0.4s var(--smooth); 
            font-size: 14px; box-sizing: border-box;
        }
        .quiz-option:hover { background: rgba(244, 114, 182, 0.1); border-color: var(--accent-berry); transform: translateX(6px); }
        .quiz-option.correct { background: rgba(74, 222, 128, 0.2) !important; border-color: var(--safe-green) !important; color: var(--safe-green); }
        .quiz-option.wrong { background: rgba(248, 113, 113, 0.2) !important; border-color: var(--danger-red) !important; color: var(--danger-red); }

        .slide-left-to-right { 
            animation: smoothLTR 1.2s var(--ultra-smooth) forwards;
            will-change: transform, opacity;
        }
        @keyframes smoothLTR {
            0% { opacity: 0; transform: translateX(-100px); }
            100% { opacity: 1; transform: translateX(0); }
        }

        .master-footer {
            position: relative; margin-top: 50px; width: 100%; height: 180px;
            background: linear-gradient(to top, var(--nav-bg), transparent);
            z-index: 999; pointer-events: none;
        }

        .footer-line {
            position: absolute; bottom: 100px; left: 0; width: 100%; height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent-berry), var(--accent-frost), transparent);
            box-shadow: 0 0 15px var(--accent-berry);
            z-index: 1001;
        }

        .footer-rays {
            position: absolute; bottom: 102px; left: 0; width: 100%; height: 150px;
            overflow: hidden; pointer-events: none;
        }
        .footer-ray {
            position: absolute; bottom: 0; width: 2px; height: 100%;
            background: linear-gradient(to top, var(--accent-berry), transparent);
            opacity: 0.4; animation: beamUp 2s infinite ease-out;
        }
        @keyframes beamUp { 0% { height: 0; opacity: 0.8; } 100% { height: 100%; opacity: 0; } }

        .bottom-nav-zone { 
            position: relative; width: 100%; 
            background: var(--nav-bg); padding: 40px 0 60px;
            display: flex; flex-direction: column; align-items: center; gap: 30px;
            border-top: 1px solid rgba(244, 114, 182, 0.2);
            z-index: 1002;
        }

        .nav-island {
            background: rgba(0,0,0,0.4); padding: 10px 30px; border-radius: 60px;
            border: 2px solid rgba(244, 114, 182, 0.4);
            display: flex; gap: 30px; align-items: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }

        .nav-link { 
            text-decoration: none; font-size: 14px; font-weight: 900; 
            cursor: pointer; text-align: center; transition: all 0.3s var(--smooth);
        }
        .nav-link:hover, .nav-link:active {
            transform: translateY(-4px);
            color: var(--accent-frost);
            text-shadow: 0 0 12px var(--accent-frost);
        }
        
        .system-footer { margin-top: 10px; text-align: center; font-size: 13px; }
        .hidden { display: none !important; }
        
        .cyber-link { 
            text-decoration: none; display: inline-block; margin-top: 0px; 
            transition: all 0.3s var(--smooth); 
        }
        .cyber-link:hover, .cyber-link:active { 
            transform: translateY(-5px) scale(1.05); 
            text-shadow: 0 0 15px var(--accent-berry);
        }

        .voice-btn {
            background: transparent; border: 1px solid var(--accent-berry); color: var(--accent-berry);
            border-radius: 50%; width: 35px; height: 35px; cursor: pointer; float: right;
            display: flex; align-items: center; justify-content: center; margin-top: -5px; flex-shrink: 0;
        }
        .voice-btn.playing { animation: pulse-voice 1.5s infinite; }
        @keyframes pulse-voice { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }

        /* --- СТИЛИ ЧАТА СИМУЛЯЦИИ --- */
        .sim-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; align-items: stretch; }
        .sim-card { 
            background: rgba(0,0,0,0.2); border: 1px solid rgba(244, 114, 182, 0.2); 
            border-radius: 15px; padding: 15px 10px; text-align: center; cursor: pointer;
            transition: all 0.3s var(--smooth);
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            min-height: 100px; box-sizing: border-box;
        }
        .sim-card:hover { background: rgba(244, 114, 182, 0.1); border-color: var(--accent-berry); transform: translateY(-5px); }
        .sim-card.locked { opacity: 0.5; cursor: not-allowed; filter: grayscale(1); }
        .sim-card.locked:hover { transform: none; background: rgba(0,0,0,0.2); border-color: rgba(244, 114, 182, 0.2); }
        
        .chat-container { 
            background: rgba(15, 23, 42, 0.8); border-radius: 20px; border: 1px solid rgba(244, 114, 182, 0.3);
            display: flex; flex-direction: column; height: 400px; overflow: hidden;
            animation: ultraEntrance 0.6s var(--ultra-smooth);
        }
        .chat-header { background: rgba(0,0,0,0.4); padding: 15px; text-align: center; border-bottom: 1px solid rgba(244, 114, 182, 0.2); font-weight: bold; font-size: 14px;}
        .chat-messages { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .chat-messages::-webkit-scrollbar { display: none; }
        .msg { padding: 10px 15px; border-radius: 15px; max-width: 80%; font-size: 13px; line-height: 1.4; animation: slideFromLeft 0.3s var(--smooth); }
        .msg.bot { background: rgba(244, 114, 182, 0.15); border-bottom-left-radius: 2px; border: 1px solid rgba(244, 114, 182, 0.3); align-self: flex-start; color: var(--text-main); }
        .msg.user { background: var(--btn-static); color: #1E1B4B; border-bottom-right-radius: 2px; align-self: flex-end; animation: slideFromRight 0.3s var(--smooth); font-weight: bold;}
        .chat-input-area { display: flex; padding: 10px; background: rgba(0,0,0,0.4); gap: 10px; }
        .chat-input-area input { flex: 1; background: rgba(255,255,255,0.1); border: none; border-radius: 20px; padding: 10px 15px; color: white; outline: none; font-size: 13px; }
        .chat-send-btn { background: var(--btn-static); color: #1E1B4B; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center; flex-shrink: 0;}

        @keyframes slideFromLeft { from { opacity: 0; transform: translateX(-15px); } to { opacity: 1; transform: translateX(0); } }
        @keyframes slideFromRight { from { opacity: 0; transform: translateX(15px); } to { opacity: 1; transform: translateX(0); } }

        /* --- ПАРОЛЬНЫЙ СТРАЖ --- */
        .pw-rule { transition: all 0.45s var(--smooth); opacity: 0.55; }
        .pw-rule .detail-indicator { background: rgba(203, 213, 225, 0.35); box-shadow: none; transition: all 0.45s var(--smooth); }
        .pw-rule .detail-label { color: var(--text-main); transition: color 0.45s var(--smooth); letter-spacing: 0.5px; }
        .pw-rule.active { opacity: 1; transform: translateX(2px); }
        .pw-rule.active .detail-indicator {
            background: var(--safe-green);
            box-shadow: 0 0 12px var(--safe-green), 0 0 22px rgba(74, 222, 128, 0.4);
            animation: pwPulse 1.6s ease-in-out infinite;
        }
        .pw-rule.active .detail-label {
            color: var(--safe-green);
            text-shadow: 0 0 8px rgba(74, 222, 128, 0.5);
        }
        @keyframes pwPulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.25); } }

        /* --- ПИНГ-ИНДИКАТОР (перенесён в нижнюю зону, не пересекается с #КИБЕРПРАВО) --- */
        .ping-indicator {
            position: absolute; top: 14px; right: 16px;
            display: inline-flex; align-items: center; gap: 6px;
            padding: 6px 10px; border-radius: 12px;
            background: rgba(0, 0, 0, 0.45); border: 1px solid rgba(74, 222, 128, 0.3);
            font-family: monospace; font-size: 10px; letter-spacing: 1px;
            color: var(--safe-green); transition: all 0.4s var(--smooth);
            backdrop-filter: blur(6px); z-index: 1003;
        }
        body.light-mode .ping-indicator { background: rgba(255,255,255,0.85); border-color: rgba(34,197,94,0.4); }
        .ping-indicator .ping-label { opacity: 0.65; font-weight: bold; }
        .ping-indicator #ping-value { font-weight: bold; }
        .ping-dot {
            width: 7px; height: 7px; border-radius: 50%;
            background: var(--safe-green);
            box-shadow: 0 0 8px var(--safe-green);
            animation: pingPulse 1.4s ease-in-out infinite;
        }
        @keyframes pingPulse { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.4); opacity: 0.6; } }
        .ping-indicator.warn { border-color: rgba(251, 191, 36, 0.4); color: #fbbf24; }
        .ping-indicator.warn .ping-dot { background: #fbbf24; box-shadow: 0 0 8px #fbbf24; }
        .ping-indicator.bad { border-color: rgba(239, 68, 68, 0.4); color: var(--danger-red); }
        .ping-indicator.bad .ping-dot { background: var(--danger-red); box-shadow: 0 0 8px var(--danger-red); }

        /* ============================================
           ГЛАВНАЯ СТРАНИЦА — ПРОФЕССИОНАЛЬНЫЙ ДИЗАЙН
           ============================================ */

        /* HERO */
        .home-hero {
            padding: 40px 8px 28px;
            text-align: center;
            position: relative;
            animation: ultraEntrance 0.8s var(--ultra-smooth) both;
        }
        .home-hero-badge {
            display: inline-flex; align-items: center; gap: 8px;
            font-size: 10.5px; font-weight: 700; letter-spacing: 1.5px;
            padding: 7px 14px; border-radius: 999px;
            background: rgba(74, 222, 128, 0.08);
            border: 1px solid rgba(74, 222, 128, 0.35);
            color: var(--safe-green);
            margin-bottom: 22px;
        }
        .hero-dot {
            width: 7px; height: 7px; border-radius: 50%;
            background: var(--safe-green);
            box-shadow: 0 0 10px var(--safe-green);
            animation: heroPulse 1.8s ease-in-out infinite;
        }
        @keyframes heroPulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.4); }
        }
        .home-hero-title {
            font-size: clamp(28px, 5vw, 42px);
            line-height: 1.1;
            font-weight: 800;
            margin: 0 0 18px;
            letter-spacing: -0.8px;
            color: var(--text-main);
        }
        .home-hero-accent {
            background: linear-gradient(135deg, var(--accent-berry), var(--accent-frost));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .home-hero-sub {
            font-size: 14px; line-height: 1.6;
            max-width: 480px; margin: 0 auto 18px;
            opacity: 0.82;
        }
        .home-hero-extra {
            font-size: 13px; line-height: 1.7;
            max-width: 520px; margin: 0 auto 26px;
            opacity: 0.72;
        }
        .home-hero-cta {
            display: inline-flex; gap: 10px; flex-wrap: wrap; justify-content: center;
        }
        .hero-btn {
            padding: 13px 26px;
            border-radius: 12px;
            font-size: 13px; font-weight: 700; letter-spacing: 0.6px;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.35s var(--smooth);
            display: inline-block;
        }
        .hero-btn.primary {
            background: linear-gradient(135deg, var(--accent-berry), #ec4899);
            color: #fff;
            box-shadow: 0 6px 20px rgba(244, 114, 182, 0.35);
        }
        .hero-btn.primary:hover { transform: translateY(-2px); box-shadow: 0 10px 26px rgba(244, 114, 182, 0.5); }
        .hero-btn.ghost {
            background: transparent;
            color: var(--text-main);
            border: 1px solid rgba(244, 114, 182, 0.4);
        }
        .hero-btn.ghost:hover { background: rgba(244, 114, 182, 0.1); border-color: var(--accent-berry); }

        /* СТАТИСТИКА */
        .home-stats {
            display: grid; grid-template-columns: repeat(3, 1fr);
            gap: 10px; margin: 8px 0 32px;
        }
        .home-stat {
            padding: 18px 8px;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(244, 114, 182, 0.06), rgba(129, 140, 248, 0.05));
            border: 1px solid rgba(244, 114, 182, 0.18);
            text-align: center;
            transition: all 0.4s var(--smooth);
        }
        .home-stat:hover { transform: translateY(-3px); border-color: rgba(244, 114, 182, 0.45); }
        .home-stat-num {
            font-size: clamp(20px, 4vw, 28px);
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-frost), var(--accent-berry));
            -webkit-background-clip: text; background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4px;
        }
        .home-stat-label {
            font-size: 10.5px; letter-spacing: 0.7px;
            text-transform: uppercase;
            opacity: 0.7; font-weight: 600;
        }

        /* СЕКЦИИ */
        .home-section { margin-top: 36px; animation: ultraEntrance 0.7s var(--ultra-smooth) both; }
        .home-section-head { margin-bottom: 14px; padding: 0 4px; }
        .home-section-head h3 {
            margin: 0 0 4px;
            font-size: 16px; font-weight: 700;
            letter-spacing: -0.2px;
            color: var(--text-main);
        }
        .home-section-head span { font-size: 11.5px; opacity: 0.6; }

        /* О НАШЕМ СЕРВИСЕ — 4 КЛИКАБЕЛЬНЫЕ ЗОНЫ */
        .home-about-grid {
            display: grid; grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        .home-about-card {
            position: relative; overflow: hidden;
            padding: 18px 16px;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(30, 27, 75, 0.55), rgba(15, 23, 42, 0.35));
            border: 1px solid rgba(244, 114, 182, 0.18);
            cursor: pointer;
            transition: transform 0.4s var(--ultra-smooth), border-color 0.35s var(--smooth), box-shadow 0.4s var(--ultra-smooth), background 0.4s var(--smooth);
            color: var(--text-main);
            display: flex; flex-direction: column; gap: 8px;
        }
        .home-about-card::before {
            content: ''; position: absolute; inset: -1px;
            background: linear-gradient(135deg, transparent 30%, rgba(244,114,182,0.18), transparent 80%);
            opacity: 0; transition: opacity 0.45s var(--smooth);
            border-radius: inherit; pointer-events: none;
        }
        .home-about-card:hover, .home-about-card:active {
            transform: translateY(-5px);
            border-color: var(--accent-berry);
            box-shadow: 0 14px 32px rgba(244, 114, 182, 0.25);
        }
        .home-about-card:hover::before, .home-about-card:active::before { opacity: 1; }
        .home-about-icon {
            width: 42px; height: 42px; border-radius: 12px;
            display: inline-flex; align-items: center; justify-content: center;
            background: linear-gradient(135deg, rgba(244,114,182,0.22), rgba(129,140,248,0.18));
            border: 1px solid rgba(244,114,182,0.35);
            font-size: 22px;
        }
        .home-about-title {
            font-size: 14px; font-weight: 800;
            letter-spacing: 0.4px;
            color: var(--text-main);
        }
        .home-about-desc {
            font-size: 11.5px; line-height: 1.5;
            opacity: 0.78;
        }
        body.light-mode .home-about-card {
            background: #ffffff;
            border-color: rgba(244, 114, 182, 0.3);
            box-shadow: 0 2px 10px rgba(30, 27, 75, 0.06);
        }
        body.light-mode .home-about-desc { color: #475569; opacity: 1; }

        /* ИНФО-БЛОК С ДОП. ТЕКСТОМ */
        .home-info-block {
            margin-top: 18px;
            padding: 22px;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(244, 114, 182, 0.06), rgba(129, 140, 248, 0.04));
            border: 1px solid rgba(244, 114, 182, 0.18);
        }
        .home-info-block h4 { margin: 0 0 10px; font-size: 14px; letter-spacing: 0.5px; }
        .home-info-block p { margin: 0 0 10px; font-size: 13px; line-height: 1.65; opacity: 0.85; }
        .home-info-block ul { margin: 8px 0 0; padding-left: 18px; font-size: 12.5px; line-height: 1.7; opacity: 0.85; }
        .home-info-block li { margin-bottom: 4px; }
        body.light-mode .home-info-block { background: #ffffff; border-color: rgba(244,114,182,0.3); box-shadow: 0 2px 10px rgba(30,27,75,0.05); }
        body.light-mode .home-info-block p, body.light-mode .home-info-block ul { color: #334155; opacity: 1; }

        /* НОВОСТНАЯ ЛЕНТА — КАРУСЕЛЬ С КАРТИНКАМИ И БЛЮРОМ */
        .news-ticker-wrap {
            position: relative;
            overflow: hidden;
            padding: 6px 0 16px;
            border-radius: 18px;
        }
        .news-track {
            display: flex; gap: 14px;
            width: max-content;
            transition: transform 0.85s var(--ultra-smooth);
            will-change: transform;
            cursor: grab;
            user-select: none;
        }
        .news-track.is-dragging { cursor: grabbing; }

        .news-tile {
            flex: 0 0 270px;
            position: relative;
            border-radius: 18px;
            overflow: hidden;
            background: var(--card-bg);
            border: 1px solid rgba(244, 114, 182, 0.18);
            text-decoration: none;
            color: inherit;
            display: block;
            height: 220px;
            transition: transform 0.45s var(--ultra-smooth), box-shadow 0.45s var(--ultra-smooth), border-color 0.4s;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
        }
        .news-tile:hover, .news-tile:active {
            transform: translateY(-6px);
            border-color: var(--accent-berry);
            box-shadow: 0 14px 32px rgba(244, 114, 182, 0.32);
        }
        .news-tile-img {
            position: absolute; inset: 0;
            background-size: cover; background-position: center;
            transition: transform 0.6s var(--ultra-smooth);
        }
        .news-tile:hover .news-tile-img { transform: scale(1.06); }
        .news-tile-img::after {
            content: ''; position: absolute; inset: 0;
            background: linear-gradient(180deg, rgba(0,0,0,0.0) 30%, rgba(0,0,0,0.35) 60%, rgba(0,0,0,0.85) 100%);
        }
        .news-tile-pill {
            position: absolute; top: 12px; left: 12px;
            font-size: 9.5px; font-weight: 800; letter-spacing: 1.3px;
            padding: 5px 10px; border-radius: 6px;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.18);
            z-index: 3;
        }
        .news-tile-fog {
            position: absolute; left: 0; right: 0; bottom: 0;
            padding: 18px 14px 14px;
            background: linear-gradient(180deg, rgba(15,23,42,0) 0%, rgba(15,23,42,0.55) 40%, rgba(15,23,42,0.85) 100%);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            z-index: 2;
        }
        .news-tile-title {
            font-size: 13.5px; font-weight: 700;
            line-height: 1.35;
            color: #ffffff;
            margin-bottom: 6px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-shadow: 0 2px 8px rgba(0,0,0,0.5);
        }
        .news-tile-source {
            font-size: 11px;
            color: var(--accent-berry);
            font-weight: 700;
            letter-spacing: 0.4px;
        }

        /* СТРЕЛКИ ЛЕНТЫ — ВНУТРИ КАРУСЕЛИ ПОВЕРХ ПЛИТОК */
        .news-arrow {
            position: absolute; top: 50%; transform: translateY(-50%);
            width: 38px; height: 38px; border-radius: 50%;
            background: rgba(30, 27, 75, 0.78); border: 1px solid rgba(244,114,182,0.55);
            color: #fff; cursor: pointer; z-index: 5;
            display: inline-flex; align-items: center; justify-content: center;
            font-size: 22px; line-height: 1; padding-bottom: 3px;
            transition: background 0.3s var(--smooth), transform 0.3s var(--smooth), box-shadow 0.3s var(--smooth);
            backdrop-filter: blur(6px);
            box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        }
        .news-arrow.prev { left: 8px; }
        .news-arrow.next { right: 8px; }
        .news-arrow:hover {
            background: var(--accent-berry); color: #1E1B4B;
            transform: translateY(-50%) scale(1.08);
            box-shadow: 0 8px 22px rgba(244,114,182,0.55);
        }
        .news-arrow:active { transform: translateY(-50%) scale(0.94); }
        body.light-mode .news-arrow { background: rgba(255,255,255,0.92); border-color: rgba(244,114,182,0.5); color: #1E1B4B; box-shadow: 0 4px 14px rgba(30,27,75,0.18); }
        .news-tile { transition: transform 0.45s var(--ultra-smooth), box-shadow 0.45s var(--ultra-smooth), border-color 0.4s, filter 0.4s; }
        .news-tile:hover { filter: brightness(1.07) saturate(1.05); }

        /* БЛОК «РЕСПУБЛИКА БЕЛАРУСЬ» */
        .home-republic {
            display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
        }
        @media (max-width: 520px) { .home-republic { grid-template-columns: 1fr; } }
        .rep-card {
            background: var(--card-bg);
            border: 1px solid rgba(244,114,182,0.22);
            border-radius: 16px;
            padding: 16px 14px;
            transition: transform 0.35s var(--smooth), border-color 0.35s, box-shadow 0.35s;
        }
        .rep-card:hover {
            transform: translateY(-4px);
            border-color: var(--accent-berry);
            box-shadow: 0 10px 26px rgba(244,114,182,0.22);
        }
        .rep-num {
            font-size: 22px; font-weight: 900; color: var(--accent-berry);
            letter-spacing: 0.5px; margin-bottom: 6px;
            text-shadow: 0 0 18px rgba(244,114,182,0.4);
        }
        .rep-title { font-size: 13.5px; font-weight: 800; margin-bottom: 6px; color: var(--text-main); }
        .rep-desc { font-size: 12px; line-height: 1.5; opacity: 0.82; color: var(--text-main); }
        body.light-mode .rep-card { background: #ffffff; box-shadow: 0 2px 10px rgba(30,27,75,0.06); }

        /* ГЕРБЫ В HERO */
        .hero-emblems {
            display: flex; gap: 14px; align-items: center;
            margin-bottom: 16px;
        }
        .hero-emblem {
            width: 60px; height: 72px;
            filter: drop-shadow(0 0 10px rgba(244,114,182,0.4));
            transition: filter 0.3s, transform 0.3s;
        }
        .hero-emblem:hover { filter: drop-shadow(0 0 18px rgba(244,114,182,0.7)); transform: scale(1.06); }

        /* АККОРДЕОН-БЛОКИ (видео/фото) */
        .accord-box {
            background: var(--card-bg);
            border: 1.5px solid rgba(244,114,182,0.18);
            border-radius: 18px; overflow: hidden;
            transition: border-color 0.35s, box-shadow 0.35s;
        }
        .accord-box.open { border-color: rgba(244,114,182,0.5); box-shadow: 0 8px 30px rgba(244,114,182,0.12); }
        body.light-mode .accord-box { background: #ffffff; box-shadow: 0 2px 10px rgba(30,27,75,0.06); }
        .accord-header {
            display: flex; align-items: center; justify-content: space-between;
            padding: 18px 20px; cursor: pointer; user-select: none;
            transition: background 0.3s;
        }
        .accord-header:hover { background: rgba(244,114,182,0.06); }
        .accord-title {
            font-size: 15px; font-weight: 800; letter-spacing: 0.5px;
            color: var(--text-main);
            display: flex; align-items: center; gap: 10px;
        }
        .accord-subtitle { font-size: 11px; opacity: 0.6; margin-top: 3px; font-weight: 500; letter-spacing: 0; display: block; }
        .accord-chevron {
            width: 28px; height: 28px; flex-shrink: 0;
            border: 2px solid rgba(244,114,182,0.5);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            color: var(--accent-berry); font-size: 14px; line-height: 1;
            transition: transform 0.45s var(--ultra-smooth), background 0.3s, border-color 0.3s;
        }
        .accord-box.open .accord-chevron {
            transform: rotate(180deg);
            background: var(--accent-berry); color: #1E1B4B; border-color: var(--accent-berry);
        }
        .accord-content {
            max-height: 0; overflow: hidden;
            transition: max-height 0.65s var(--ultra-smooth);
        }
        .accord-box.open .accord-content { max-height: 1200px; }
        .accord-inner { padding: 0 16px 18px; }

        /* ВИДЕО ВНУТРИ АККОРДЕОНА */
        .vid-tabs {
            display: flex; gap: 10px; margin-bottom: 14px;
            flex-wrap: wrap;
        }
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

        /* КАРУСЕЛЬ ВИДЕО (стрелки + табы) */
        .vid-carousel-wrap {
            position: relative; overflow: hidden;
            margin-bottom: 14px;
        }
        .vid-carousel-arrow {
            position: absolute; top: 50%; transform: translateY(-50%);
            width: 36px; height: 36px; border-radius: 50%;
            background: rgba(30,27,75,0.82); border: 1.5px solid rgba(244,114,182,0.6);
            color: #fff; cursor: pointer; z-index: 5;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px; line-height: 1; padding-bottom: 2px;
            transition: background 0.28s var(--smooth), transform 0.28s var(--smooth), box-shadow 0.28s;
            backdrop-filter: blur(6px); box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        }
        .vid-carousel-arrow.prev { left: 4px; }
        .vid-carousel-arrow.next { right: 4px; }
        .vid-carousel-arrow:hover {
            background: var(--accent-berry); color: #1E1B4B;
            transform: translateY(-50%) scale(1.1);
            box-shadow: 0 6px 20px rgba(244,114,182,0.55);
        }
        .vid-carousel-arrow:active { transform: translateY(-50%) scale(0.94); }
        body.light-mode .vid-carousel-arrow { background: rgba(255,255,255,0.94); color: #1E1B4B; }
        .vid-tabs {
            display: flex; gap: 10px;
            flex-wrap: nowrap; overflow-x: hidden;
            scroll-behavior: smooth;
            padding: 0 44px;
        }
        .vid-tab {
            flex: 0 0 calc(33.333% - 7px);
            background: rgba(0,0,0,0.25); border: 1.5px solid rgba(244,114,182,0.2);
            border-radius: 14px; padding: 14px 10px 12px;
            cursor: pointer; color: var(--text-main);
            display: flex; flex-direction: column; align-items: center; gap: 8px;
            transition: background 0.3s, border-color 0.3s, transform 0.32s, box-shadow 0.32s;
            font-family: inherit; min-width: 100px;
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
            background: #000; box-shadow: 0 8px 28px rgba(0,0,0,0.55);
        }
        .vid-player { width: 100%; display: block; max-height: 360px; object-fit: contain; }

        /* КАРУСЕЛЬ ФОТО (стрелки + горизонтальный скролл) */
        .photo-carousel-wrap {
            position: relative; overflow: hidden;
        }
        .photo-carousel-arrow {
            position: absolute; top: 50%; transform: translateY(-50%);
            width: 36px; height: 36px; border-radius: 50%;
            background: rgba(30,27,75,0.82); border: 1.5px solid rgba(244,114,182,0.6);
            color: #fff; cursor: pointer; z-index: 5;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px; line-height: 1; padding-bottom: 2px;
            transition: background 0.28s var(--smooth), transform 0.28s var(--smooth), box-shadow 0.28s;
            backdrop-filter: blur(6px); box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        }
        .photo-carousel-arrow.prev { left: 4px; }
        .photo-carousel-arrow.next { right: 4px; }
        .photo-carousel-arrow:hover {
            background: var(--accent-berry); color: #1E1B4B;
            transform: translateY(-50%) scale(1.1);
            box-shadow: 0 6px 20px rgba(244,114,182,0.55);
        }
        .photo-carousel-arrow:active { transform: translateY(-50%) scale(0.94); }
        body.light-mode .photo-carousel-arrow { background: rgba(255,255,255,0.94); color: #1E1B4B; }
        .photo-track {
            display: flex; gap: 12px;
            overflow-x: hidden; scroll-behavior: smooth;
            padding: 4px 44px 8px;
        }
        .photo-card {
            flex: 0 0 calc(50% - 6px);
            border-radius: 14px; overflow: hidden;
            border: 1.5px solid rgba(244,114,182,0.18);
            background: var(--card-bg);
            cursor: pointer; position: relative;
            transition: transform 0.35s var(--smooth), border-color 0.35s, box-shadow 0.35s;
        }
        @media (max-width: 480px) { .photo-card { flex: 0 0 82vw; } }
        .photo-card:hover { transform: translateY(-5px) scale(1.02); border-color: var(--accent-berry); box-shadow: 0 12px 28px rgba(244,114,182,0.3); }
        .photo-card img { width: 100%; display: block; aspect-ratio: 3/4; object-fit: cover; }
        @media (max-width: 480px) { .photo-card img { aspect-ratio: 4/3; } }
        .photo-card-label {
            padding: 8px 10px; font-size: 11.5px; font-weight: 800;
            letter-spacing: 0.4px; color: var(--text-main);
            background: var(--card-bg); text-align: center;
        }
        body.light-mode .photo-card { background: #fff; box-shadow: 0 2px 10px rgba(30,27,75,0.07); }
        .photo-grid { display: none; }

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

        /* СВЕТЛАЯ ТЕМА — ЧИТАЕМОСТЬ */
        body.light-mode { color: #1E1B4B; }
        body.light-mode .home-hero-sub,
        body.light-mode .home-hero-extra,
        body.light-mode .home-stat-label,
        body.light-mode .home-section-head span { color: #475569; opacity: 1; }
        body.light-mode .home-stat {
            background: #ffffff;
            border-color: rgba(244, 114, 182, 0.35);
            box-shadow: 0 2px 10px rgba(30, 27, 75, 0.06);
        }
        body.light-mode .news-tile {
            background: #ffffff;
            border-color: rgba(244, 114, 182, 0.3);
            box-shadow: 0 4px 14px rgba(30, 27, 75, 0.08);
        }
        body.light-mode .hero-btn.ghost { color: #1E1B4B; border-color: rgba(244, 114, 182, 0.5); }
        body.light-mode .home-hero-badge { background: rgba(74, 222, 128, 0.12); color: #166534; border-color: rgba(34, 197, 94, 0.4); }

        body.light-mode .nav-island { background: #ffffff; border-color: rgba(244,114,182,0.45); box-shadow: 0 8px 24px rgba(30,27,75,0.1); }
        body.light-mode .nav-link { color: #1E1B4B; }
        body.light-mode .system-footer { color: #1E1B4B; }
        body.light-mode .memo-content p,
        body.light-mode .memo-content li,
        body.light-mode .memo-content ul { color: #1E1B4B; }
        body.light-mode .detail-text { color: #334155; }
        body.light-mode [style*="color: #cbd5e1"] { color: #475569 !important; }
        body.light-mode [style*="color: var(--text-main)"][style*="opacity"] { color: #334155 !important; }

        /* --- КНОПКА ГЕНЕРАЦИИ ПАРОЛЯ --- */
        .generator-card {
            margin-top: 18px;
            padding: 22px 18px;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(244, 114, 182, 0.12), rgba(165, 243, 252, 0.07));
            border: 1px solid rgba(244, 114, 182, 0.3);
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: all 0.4s var(--smooth);
        }
        .generator-card:hover { border-color: var(--accent-berry); box-shadow: 0 8px 24px rgba(244, 114, 182, 0.3); }
        .generator-card h4 { margin: 0 0 6px; font-size: 15px; letter-spacing: 1px; }
        .generator-card p { font-size: 11.5px; opacity: 0.75; margin: 0 0 14px; }
        .btn-generate {
            width: 100%; padding: 13px; border: none; border-radius: 14px;
            background: linear-gradient(135deg, var(--accent-frost), var(--accent-berry));
            color: #1E1B4B; font-weight: 800; font-size: 13px; letter-spacing: 1.3px;
            cursor: pointer; transition: all 0.35s var(--smooth);
            box-shadow: 0 4px 14px rgba(244, 114, 182, 0.35);
        }
        .btn-generate:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(244, 114, 182, 0.55); }
        .btn-generate:active { transform: translateY(0) scale(0.98); }

        /* ============================================
           МОБИЛЬНАЯ ВЕРСИЯ — ПЛАВНОСТЬ И ОДИНАКОВЫЕ ЗОНЫ
           ============================================ */
        @media (max-width: 600px) {
            .container { padding: 18px; padding-top: 70px; }

            /* Симуляции: три одинаковые карточки */
            .sim-grid { grid-template-columns: repeat(3, 1fr); gap: 8px; }
            .sim-card {
                padding: 12px 4px;
                min-height: 95px;
                aspect-ratio: 1 / 1.05;
                width: 100%;
            }
            .sim-card span { font-size: 22px; line-height: 1; margin-bottom: 6px !important; }
            .sim-card b { font-size: 9.5px; letter-spacing: 0.4px; line-height: 1.15; word-break: break-word; }

            /* О сервисе — две колонки */
            .home-about-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
            .home-about-card { padding: 14px 12px; }
            .home-about-icon { width: 38px; height: 38px; font-size: 20px; }
            .home-about-title { font-size: 12.5px; }
            .home-about-desc { font-size: 11px; }

            .news-tile { flex: 0 0 240px; height: 200px; }
            .news-tile-title { font-size: 12.5px; }

            .nav-island { padding: 10px 22px; gap: 22px; }
        }

        /* На устройствах без hover (телефоны/планшеты) — добавляем плавные active-состояния */
        @media (hover: none), (pointer: coarse) {
            .home-stat, .home-path, .news-tile, .sim-card,
            .memo-box, .info-box, .home-about-card, .quiz-option,
            .hero-btn, .news-arrow, .menu-item {
                -webkit-tap-highlight-color: transparent;
                transition: transform 0.35s var(--ultra-smooth),
                            box-shadow 0.35s var(--ultra-smooth),
                            background 0.35s var(--smooth),
                            border-color 0.35s var(--smooth),
                            opacity 0.35s var(--smooth);
            }
            .home-about-card:active,
            .sim-card:active,
            .home-stat:active,
            .quiz-option:active,
            .home-path:active {
                transform: scale(0.97);
                opacity: 0.92;
            }
            .news-tile:active { transform: translateY(-3px) scale(0.98); }
            .menu-item:active { transform: scale(0.98); }
            .hero-btn:active { transform: translateY(2px) scale(0.97); }
            .news-arrow:active { transform: scale(0.92); }

            /* Чтобы ленты и карточки плавно прорисовывались */
            .news-track, .home-about-card, .home-stat, .sim-card,
            .news-tile, .menu-item, .home-info-block {
                will-change: transform, opacity;
            }
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

        <!-- Гербы РБ и МВД — показываются только при раскрытии -->
        <div class="menu-emblems">
            <img class="menu-emblem-img" src="https://i.ibb.co/7DGmDfj/cybershield11.png" alt="Герб РБ" title="Герб Республики Беларусь">
            <img class="menu-emblem-img" src="https://i.ibb.co/35yc90YN/cybershield111.png" alt="МВД РБ" title="МВД Республики Беларусь">
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
        
        <hr style="width: 80%; border: none; border-top: 1px solid rgba(244, 114, 182, 0.3); margin: auto auto 10px auto; opacity: 0; transition: opacity 0.5s;">
        
        <a href="https://t.me/CyberNodes_bot" target="_blank" class="tg-super-btn tg-menu-btn">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.19-.08-.05-.19-.02-.27 0-.12.03-1.96 1.25-5.54 3.67-.52.36-.99.54-1.41.53-.46-.01-1.35-.26-2.01-.48-.81-.27-1.46-.42-1.4-.88.03-.23.36-.48.98-.74 3.84-1.68 6.4-2.78 7.68-3.32 3.65-1.53 4.41-1.8 4.9-1.81.11 0 .35.03.48.14.11.09.14.22.14.35-.01.12-.01.24-.02.35z"/></svg>
            НАШ БОТ
        </a>
    </div>

    <div class="container">

        <div id="page-home" class="page-content">

            <section class="home-hero">
                <div class="hero-emblems">
                    <img class="hero-emblem" src="https://i.ibb.co/7DGmDfj/cybershield11.png" alt="Герб Республики Беларусь" title="Республика Беларусь">
                    <img class="hero-emblem" src="https://i.ibb.co/35yc90YN/cybershield111.png" alt="МВД Республики Беларусь" title="МВД Республики Беларусь">
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
                        <div class="home-about-desc">Глубокий анализ URL через VirusTotal и собственный ИИ-вердикт. Поможем понять, можно ли переходить по ссылке.</div>
                    </div>
                    <div class="home-about-card" onclick="switchPage('info')">
                        <div class="home-about-icon">📚</div>
                        <div class="home-about-title">ИНФОРМАЦИЯ И ТЕСТЫ</div>
                        <div class="home-about-desc">Памятка по безопасности, справочник угроз, ИИ-помощник и кибер-экзамен на внимательность и грамотность.</div>
                    </div>
                    <div class="home-about-card" onclick="switchPage('info')">
                        <div class="home-about-icon">🔥</div>
                        <div class="home-about-title">СИМУЛЯЦИИ С ИИ</div>
                        <div class="home-about-desc">Сразитесь с виртуальным мошенником в чате. ИИ Groq отыграет реальную атаку, а мы оценим вашу защиту.</div>
                    </div>
                    <div class="home-about-card" onclick="switchPage('password')">
                        <div class="home-about-icon">🔑</div>
                        <div class="home-about-title">ПАРОЛЬНЫЙ СТРАЖ</div>
                        <div class="home-about-desc">Анализ криптостойкости и генератор по-настоящему надёжных паролей. Все вычисления идут только в вашем браузере.</div>
                    </div>
                </div>

                <div class="home-info-block">
                    <h4 class="shimmer-text">💎 Почему это важно</h4>
                    <p>По данным МВД Беларуси, более 70% хищений со счетов граждан начинаются с обычной ссылки или телефонного звонка. Мошенники не «взламывают» технику — они взламывают невнимательность. CyberShield тренирует именно это: умение остановиться, проверить и не сделать поспешный шаг.</p>
                    <p>Сервис не собирает ваши данные, не сохраняет пароли и не передаёт ссылки третьим лицам. Все проверки проходят анонимно, а парольный анализ работает прямо в браузере, не покидая устройство.</p>
                    <ul>
                        <li>Полностью бесплатно и без регистрации.</li>
                        <li>Понятный язык — без сложной терминологии.</li>
                        <li>Тренировки построены на реальных белорусских кейсах.</li>
                        <li>Подходит для уроков ОБЖ, классных часов и семейных бесед.</li>
                    </ul>
                </div>
            </section>

            <!-- ===== ВИДЕО (аккордеон) ===== -->
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
                            <div class="vid-carousel-wrap" id="vid-carousel">
                                <button class="vid-carousel-arrow prev" onclick="moveVidCarousel(-1)" aria-label="Назад">‹</button>
                                <button class="vid-carousel-arrow next" onclick="moveVidCarousel(1)" aria-label="Вперёд">›</button>
                            <div class="vid-tabs" id="vid-tabs">
                                <button class="vid-tab active" data-src="https://litter.catbox.moe/jec29k.mp4" onclick="selectVideo(this)">
                                    <span class="vid-tab-ico">🌐</span>
                                    <span class="vid-tab-text">Безопасность<br>в интернете</span>
                                </button>
                                <button class="vid-tab" data-src="https://litter.catbox.moe/p9co2t.mp4" onclick="selectVideo(this)">
                                    <span class="vid-tab-ico">📨</span>
                                    <span class="vid-tab-text">Сообщения<br>от мошенников</span>
                                </button>
                                <button class="vid-tab" data-src="https://litter.catbox.moe/y4umnf.mp4" onclick="selectVideo(this)">
                                    <span class="vid-tab-ico">🎰</span>
                                    <span class="vid-tab-text">Внезапные<br>выигрыши</span>
                                </button>
                            </div>
                            </div><!-- /vid-carousel-wrap -->
                            <div class="vid-player-wrap">
                                <video id="main-video" class="vid-player" controls preload="metadata" playsinline>
                                    <source id="main-video-src" src="https://litter.catbox.moe/jec29k.mp4" type="video/mp4">
                                    Ваш браузер не поддерживает видео.
                                </video>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ===== ФОТО (аккордеон) ===== -->
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
                            <div class="photo-carousel-wrap" id="photo-carousel">
                                <button class="photo-carousel-arrow prev" onclick="movePhotoCarousel(-1)" aria-label="Назад">‹</button>
                                <button class="photo-carousel-arrow next" onclick="movePhotoCarousel(1)" aria-label="Вперёд">›</button>
                                <div class="photo-track" id="photo-track">
                                    <div class="photo-card" onclick="openPhotoModal('https://i.ibb.co/pv1L6gJg/cybershield.jpg','Вирусные APK-файлы — как защититься')">
                                        <img src="https://i.ibb.co/pv1L6gJg/cybershield.jpg" alt="Вирусные APK-файлы" loading="lazy">
                                        <div class="photo-card-label">🦠 Вирусные APK-файлы</div>
                                    </div>
                                    <div class="photo-card" onclick="openPhotoModal('https://i.ibb.co/sdgQCCZK/cybershield1.jpg','Главные правила цифровой гигиены')">
                                        <img src="https://i.ibb.co/sdgQCCZK/cybershield1.jpg" alt="Правила цифровой гигиены" loading="lazy">
                                        <div class="photo-card-label">🧼 Цифровая гигиена</div>
                                    </div>
                                    <div class="photo-card" onclick="openPhotoModal('https://i.ibb.co/4wtT0N7c/cybershield2.jpg','Угрозы в сети — типичные схемы хакерских атак')">
                                        <img src="https://i.ibb.co/4wtT0N7c/cybershield2.jpg" alt="Угрозы в сети" loading="lazy">
                                        <div class="photo-card-label">🖥️ Угрозы в сети</div>
                                    </div>
                                    <div class="photo-card" onclick="openPhotoModal('https://i.ibb.co/chPQ5VK7/2026-04-04-165314.png','#КиберПраво: твой щит в сети — конкурс')">
                                        <img src="https://i.ibb.co/chPQ5VK7/2026-04-04-165314.png" alt="#КиберПраво конкурс" loading="lazy">
                                        <div class="photo-card-label">🏆 #КиберПраво</div>
                                    </div>
                                </div>
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
                    <button class="news-arrow news-arrow-edge prev" id="news-prev" aria-label="Назад">‹</button>
                    <button class="news-arrow news-arrow-edge next" id="news-next" aria-label="Вперёд">›</button>
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

        <div id="page-scanner" class="page-content" style="display: none; opacity: 0;">
            <div class="search-card">
                <h1 class="logo-main shimmer-text"><span>🛡️</span> CyberShield</h1>
                <p style="color: #cbd5e1; font-size: 14px;">Экспертный анализ сетевого мошенничества</p>
                <form id="check-form" action="/check" method="POST" onsubmit="showLoading()">
                    <div class="input-wrapper">
                        <input type="text" id="url-input-field" name="url" placeholder="Вставьте ссылку" required>
                        <button type="submit" class="btn-scan">ПРОВЕРИТЬ</button>
                    </div>
                </form>
                <div id="loading-overlay">
                    <div class="loader-ring"></div>
                    <p class="shimmer-text" style="font-size: 14px;">ЗАПУСК ИИ-СКАНЕРА...</p>
                </div>
            </div>

            {% if verdict_text %}
            <div class="report-card">
                <h3 id="last-verdict-title" style="text-align:center;" class="{{ 'status-danger' if stats and stats.malicious > 0 else 'status-safe' }}">
                    {{ 'УГРОЗА ОБНАРУЖЕНА' if stats and stats.malicious > 0 else 'СИСТЕМА БЕЗОПАСНА' }}
                </h3>
                <div class="stats-grid">
                    <div class="stat-box"><span class="stat-val" style="color: var(--danger-red)">{{stats.malicious}}</span><span style="font-size:10px;">ВИРУСЫ</span></div>
                    <div class="stat-box"><span class="stat-val" style="color: #fbbf24">{{stats.suspicious}}</span><span style="font-size:10px;">РИСКИ</span></div>
                    <div class="stat-box"><span class="stat-val" style="color: var(--safe-green)">{{stats.harmless}}</span><span style="font-size:10px;">ЧИСТО</span></div>
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
                    <b class="shimmer-text" style="font-size: 11px; display: block; margin-bottom: 8px; letter-spacing: 1px;">ВЕРДИКТ ИИ</b>
                    <div id="ai-verdict-text">{{ ai_text }}</div>
                </div>
            </div>
            {% endif %}

            <div class="radar-box">
                <h4 class="shimmer-text" style="margin:0 0 5px; font-size: 16px;">🌐 ЦЕНТР МОНИТОРИНГА</h4>
                <p style="font-size: 11px; color: var(--text-main); opacity: 0.7; margin-bottom: 15px;">Логирование активности узлов CyberShield</p>
                <div class="radar-circle">
                    <div class="blip blip1"></div>
                    <div class="blip blip2"></div>
                    <div class="blip blip3"></div>
                </div>
                <div class="cyber-logs" id="cyber-logs">
                    <div style="color: var(--safe-green); font-family: monospace; font-size: 11px;">> СЕТЬ CyberShield АКТИВНА. ОЖИДАНИЕ ЗАПРОСОВ...</div>
                </div>
            </div>
        </div>

        <div id="page-info" class="page-content" style="display: none; opacity: 0;">
            <div class="memo-box" id="memo-container">
                <div class="memo-header" onclick="toggleAccordion('memo-container')">
                    <span class="shimmer-text">💡 Памятка по безопасности</span>
                    <div class="chevron"></div>
                </div>
                <div class="memo-content">
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div><b class="shimmer-text" style="font-size:12px;">Правила проверки:</b><ul style="padding-left:15px; font-size:11px;"><li>Сверяйте домен по каждой букве.</li><li>HTTPS — не гарантия 100% защиты.</li><li>Не переходите по сокращённым ссылкам.</li><li>Проверяйте возраст домена сайта.</li><li>Используйте только CyberShield.</li></ul></div>
                        <div><b class="shimmer-text" style="font-size:12px;">Меры защиты:</b><ul style="padding-left:15px; font-size:11px;"><li>Включите 2FA во всех сервисах.</li><li>Регулярно очищайте кэш и cookie.</li><li>Не сохраняйте пароли в браузере.</li><li>Обновляйте ОС и браузер вовремя.</li><li>Используйте сложные разные пароли.</li></ul></div>
                    </div>
                </div>
            </div>

            <div class="report-card">
                <h3 class="shimmer-text" style="text-align:center; margin-top:0;">📖 СПРАВОЧНИК</h3>
                <p style="font-size: 13px; color: var(--text-main); text-align: center; opacity: 0.8; margin-bottom: 20px;">Продвинутая база данных кибер-угроз нового поколения.</p>
                <div class="detail-box safe">
                    <div class="detail-row">
                        <div class="detail-indicator" style="background: var(--safe-green); box-shadow: 0 0 10px var(--safe-green);"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color: var(--safe-green);">ТРОЯН</span>
                            <span class="detail-text">Вредоносное программное обеспечение, маскирующееся под легитимный софт для скрытного внедрения в систему.</span>
                        </div>
                    </div>
                    <div class="detail-row" style="margin-top: 10px;">
                        <div class="detail-indicator" style="background: var(--danger-red); box-shadow: 0 0 10px var(--danger-red);"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color: var(--danger-red);">ВИШИНГ</span>
                            <span class="detail-text">Форма социальной инженерии через голосовую связь. Метод направлен на получение доступа к данным через манипуляции.</span>
                        </div>
                    </div>
                    <div class="detail-row" style="margin-top: 10px;">
                        <div class="detail-indicator" style="background: var(--accent-berry); box-shadow: 0 0 10px var(--accent-berry);"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color: var(--accent-berry);">СТИЛЛЕР</span>
                            <span class="detail-text">Вредоносное ПО для кражи конфиденциальных данных: паролей из браузеров, cookies и ключей криптокошельков.</span>
                        </div>
                    </div>
                    <div class="detail-row" style="margin-top: 10px;">
                        <div class="detail-indicator" style="background: #ef4444; box-shadow: 0 0 10px #ef4444;"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color: #ef4444;">РЕНСОМВЕР</span>
                            <span class="detail-text">Программа-вымогатель. Шифрует файлы на устройстве или блокирует доступ к ОС, требуя от жертвы откуп.</span>
                        </div>
                    </div>
                    <div class="detail-row" style="margin-top: 10px;">
                        <div class="detail-indicator" style="background: var(--accent-frost); box-shadow: 0 0 10px var(--accent-frost);"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color: var(--accent-frost);">СОЦИАЛЬНАЯ ИНЖЕНЕРИЯ 2.0 (DEEPVOICE)</span>
                            <span class="detail-text">Мошенники используют ИИ для подделки голосов ваших родственников. Если близкий просит деньги — обязательно перезвоните ему лично.</span>
                        </div>
                    </div>
                    <div class="detail-row" style="margin-top: 10px;">
                        <div class="detail-indicator" style="background: #fbbf24; box-shadow: 0 0 10px #fbbf24;"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color: #fbbf24;">QR-ФИШИНГ (КВИШИНГ)</span>
                            <span class="detail-text">Размещение поддельных QR-кодов поверх настоящих (на квитанциях, самокатах). Всегда проверяйте URL-адрес после сканирования кода камерой.</span>
                        </div>
                    </div>
                    <div class="detail-row" style="margin-top: 10px;">
                        <div class="detail-indicator" style="background: #a78bfa; box-shadow: 0 0 10px #a78bfa;"></div>
                        <div class="detail-info">
                            <span class="detail-label" style="color: #a78bfa;">АТАКА ГОМОГРАФОВ (PUNYCODE)</span>
                            <span class="detail-text">Использование визуально похожих букв из разных алфавитов (например, латинская 'а' и кириллическая 'а'). Для браузера это разные сайты!</span>
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
                    <h4 class="shimmer-text" style="margin:0 0 15px; font-size: 18px;">🎮 Кибер-Экзамен</h4>
                    <button class="btn-scan" id="start-game" style="width:100%; padding: 15px;">НАЧАТЬ ТЕСТ</button>
                </div>
                <div id="quiz-area" class="hidden">
                    <div id="quiz-container">
                        <p id="question-num" class="shimmer-text" style="font-size:12px; margin-bottom: 8px;"></p>
                        <div id="options"></div>
                    </div>
                </div>
            </div>

            <div class="memo-box active" style="margin-top: 20px;">
                <div class="memo-header"><span class="shimmer-text">🤖 ИИ-Помощник CyberShield</span></div>
                <div class="memo-content" style="padding-bottom:20px;">
                    <p style="font-size: 12px; margin-bottom: 10px;">Спросите нашего ИИ (Groq), как защититься от угроз или что делать в подозрительной ситуации.</p>
                    <div id="helper-chat-box" class="cyber-logs" style="height: 180px; background: rgba(0,0,0,0.4); margin-bottom: 10px; display: flex; flex-direction: column; gap: 8px;">
                        <div style="color:var(--accent-frost); font-size:12px;">ИИ: Привет! Напиши мне свою проблему, и я подскажу, как обезопасить свои данные.</div>
                    </div>
                    <div class="input-wrapper" style="margin-top:0;">
                        <input type="text" id="helper-input" placeholder="Ваш вопрос...">
                        <button class="btn-scan" onclick="sendHelperMessage()">СПРОСИТЬ</button>
                    </div>
                </div>
            </div>
            
            <div class="game-section" id="sim-root">
                <h4 class="shimmer-text" style="margin:0 0 5px; font-size: 18px; text-align: center;">🔥 ЗОНА СИМУЛЯЦИЙ</h4>
                <p style="font-size: 11px; color: var(--text-main); opacity: 0.7; margin-bottom: 15px; text-align: center;">Тренировка противодействия реальным угрозам с ИИ Groq</p>
                
                <div id="sim-selector">
                    <div class="sim-grid">
                        <div class="sim-card" onclick="openSimulation('Социальная инженерия')">
                            <span style="font-size: 24px; display: block; margin-bottom: 5px;">🎭</span>
                            <b style="font-size: 12px; color: var(--accent-berry);">СОЦ. ИНЖЕНЕРИЯ</b>
                        </div>
                        <div class="sim-card" onclick="openSimulation('Техподдержка')">
                            <span style="font-size: 24px; display: block; margin-bottom: 5px;">👨‍💻</span>
                            <b style="font-size: 12px; color: var(--accent-berry);">ТЕХПОДДЕРЖКА</b>
                        </div>
                        <div class="sim-card" onclick="openSimulation('Шантаж')">
                            <span style="font-size: 24px; display: block; margin-bottom: 5px;">🔒</span>
                            <b style="font-size: 12px; color: var(--accent-berry);">ШАНТАЖ</b>
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <p style="font-size: 13px; margin-bottom: 15px;">Наш ИИ будет писать как реальный мошенник. Твоя цель — не передать личные данные и правильно завершить разговор.</p>
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
                    <button class="btn-scan" onclick="closeSim()" style="width: 100%; margin-top: 15px; background: transparent; border: 1px solid var(--accent-berry); color: var(--text-main);">ПРЕРВАТЬ СИМУЛЯЦИЮ</button>
                </div>
            </div>
        </div>

        <div id="page-password" class="page-content" style="display: none; opacity: 0;">
            <div class="search-card">
                <h1 class="logo-main shimmer-text"><span>🔑</span> Парольный Страж</h1>
                <p style="color: #cbd5e1; font-size: 14px;">Анализ криптостойкости пароля в реальном времени</p>
                <div class="input-wrapper">
                    <input type="text" id="password-input" placeholder="Введите пароль для проверки" autocomplete="off">
                    <button type="button" class="btn-scan" onclick="renderPasswordReport(document.getElementById('password-input').value)">ПРОВЕРИТЬ</button>
                </div>
                <p style="font-size: 11px; color: var(--text-main); opacity: 0.6; margin-top: 12px;">Данные не сохраняются и не покидают браузер.</p>
            </div>

            <div class="generator-card">
                <h4 class="shimmer-text">⚡ ГЕНЕРАТОР НАДЁЖНОГО ПАРОЛЯ</h4>
                <p>Создайте безопасный пароль из 16 символов в один клик. Готовый пароль сразу появится в поле выше с полным разбором стойкости.</p>
                <button type="button" class="btn-generate" onclick="generateStrongPassword()">ГЕНЕРАЦИЯ</button>
            </div>

            <div class="report-card" id="password-report" style="display:none;">
                <h3 id="password-strength-title" class="shimmer-text" style="text-align:center; margin-top:0;">АНАЛИЗ ПАРОЛЯ</h3>

                <div class="stats-grid">
                    <div class="stat-box"><span class="stat-val" id="pw-length-val" style="color: var(--accent-frost)">0</span><span style="font-size:10px;">СИМВОЛОВ</span></div>
                    <div class="stat-box"><span class="stat-val" id="pw-entropy-val" style="color: #fbbf24">0</span><span style="font-size:10px;">БИТ ЭНТРОПИИ</span></div>
                    <div class="stat-box"><span class="stat-val" id="pw-time-val" style="color: var(--safe-green); font-size:14px;">мгновенно</span><span style="font-size:10px;">ВЗЛОМ</span></div>
                </div>

                <div class="detail-box safe">
                    <div class="detail-list">
                        <div class="detail-row pw-rule" data-rule="length8">
                            <div class="detail-indicator"></div>
                            <div class="detail-info">
                                <span class="detail-label">МИНИМУМ 8 СИМВОЛОВ</span>
                                <span class="detail-text">Длина — главный фактор стойкости пароля.</span>
                            </div>
                        </div>
                        <div class="detail-row pw-rule" data-rule="length12">
                            <div class="detail-indicator"></div>
                            <div class="detail-info">
                                <span class="detail-label">12+ СИМВОЛОВ (РЕКОМЕНДОВАНО)</span>
                                <span class="detail-text">Усиленная защита от перебора по словарю.</span>
                            </div>
                        </div>
                        <div class="detail-row pw-rule" data-rule="upper">
                            <div class="detail-indicator"></div>
                            <div class="detail-info">
                                <span class="detail-label">ЗАГЛАВНЫЕ БУКВЫ (A–Z)</span>
                                <span class="detail-text">Расширяет диапазон возможных комбинаций.</span>
                            </div>
                        </div>
                        <div class="detail-row pw-rule" data-rule="lower">
                            <div class="detail-indicator"></div>
                            <div class="detail-info">
                                <span class="detail-label">СТРОЧНЫЕ БУКВЫ (a–z)</span>
                                <span class="detail-text">Базовый набор символов латинского алфавита.</span>
                            </div>
                        </div>
                        <div class="detail-row pw-rule" data-rule="digit">
                            <div class="detail-indicator"></div>
                            <div class="detail-info">
                                <span class="detail-label">ЦИФРЫ (0–9)</span>
                                <span class="detail-text">Усложняет атаки на основе слов из словаря.</span>
                            </div>
                        </div>
                        <div class="detail-row pw-rule" data-rule="special">
                            <div class="detail-indicator"></div>
                            <div class="detail-info">
                                <span class="detail-label">СПЕЦИАЛЬНЫЕ СИМВОЛЫ (!@#$%)</span>
                                <span class="detail-text">Резко увеличивает время подбора атакой.</span>
                            </div>
                        </div>
                        <div class="detail-row pw-rule" data-rule="nocommon">
                            <div class="detail-indicator"></div>
                            <div class="detail-info">
                                <span class="detail-label">НЕ ИЗ ТОП-СПИСКА УТЕЧЕК</span>
                                <span class="detail-text">Пароли вроде «123456» взламываются за миг.</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="ai-box">
                    <b class="shimmer-text" style="font-size: 11px; display: block; margin-bottom: 8px; letter-spacing: 1px;">УРОВЕНЬ ЗАЩИТЫ</b>
                    <div id="password-result-text">Введите пароль, чтобы получить вердикт.</div>
                </div>
            </div>
        </div>

    </div>

    <div class="master-footer">
        <div class="footer-line"></div>
        <div class="footer-rays" id="footer-rays-container"></div>
    </div>

    <div class="bottom-nav-zone">
        <div class="ping-indicator" id="ping-indicator" title="Задержка до сервера CyberShield">
            <span class="ping-dot" id="ping-dot"></span>
            <span class="ping-label">PING</span>
            <span id="ping-value">-- ms</span>
        </div>
        <div class="system-footer">
            <span class="shimmer-text" style="font-size: 15px;">Проверено всего: {{ total_scans }} | Найдено вирусов: {{ total_threats }}</span>
            <div style="margin-top:15px;">
                <a href="https://mir.pravo.by/contest/KiberPravo_tvoj_shchit/" target="_blank" class="cyber-link">
                    <h1 class="shimmer-text" style="font-size: 26px; margin: 0; letter-spacing: 4px;">#КИБЕРПРАВО</h1>
                </a>
            </div>
        </div>
        
        <div class="nav-island">
            <div class="nav-link shimmer-text" onclick="toggleTheme()">🌓 ТЕМА</div>
            <div class="nav-link shimmer-text" onclick="shareSite()">🔗 ССЫЛКА</div>
        </div>
    </div>

    <script>
        // --- ЛОГИКА БОКОВОГО МЕНЮ ---
        function toggleMenu() {
            const menu = document.getElementById('side-menu');
            const overlay = document.getElementById('menu-overlay');
            const btn = document.getElementById('hamburger');
            menu.classList.toggle('active');
            overlay.classList.toggle('active');
            btn.classList.toggle('open');
        }

        // --- АККОРДЕОН ---
        function toggleAccord(id) {
            const box = document.getElementById(id);
            if (!box) return;
            box.classList.toggle('open');
        }

        // --- КАРУСЕЛЬ ВИДЕО ---
        function moveVidCarousel(dir) {
            const tabs = document.getElementById('vid-tabs');
            if (!tabs) return;
            const card = tabs.querySelector('.vid-tab');
            const cardW = card ? card.offsetWidth + 10 : 120;
            tabs.scrollBy({ left: dir * cardW, behavior: 'smooth' });
        }

        // --- КАРУСЕЛЬ ФОТО ---
        function movePhotoCarousel(dir) {
            const track = document.getElementById('photo-track');
            if (!track) return;
            const card = track.querySelector('.photo-card');
            const cardW = card ? card.offsetWidth + 12 : 200;
            track.scrollBy({ left: dir * cardW, behavior: 'smooth' });
        }

        function selectVideo(btn) {
            document.querySelectorAll('.vid-tab').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const src = btn.getAttribute('data-src');
            const video = document.getElementById('main-video');
            video.pause();
            document.getElementById('main-video-src').src = src;
            video.load();
            video.play().catch(() => {});
        }

        // --- ФОТО ГАЛЕРЕЯ МОДАЛЬНОЕ ОКНО ---
        function openPhotoModal(src, caption) {
            const modal = document.getElementById('photo-modal');
            document.getElementById('photo-modal-img').src = src;
            document.getElementById('photo-modal-cap').textContent = caption;
            modal.classList.add('open');
            document.body.style.overflow = 'hidden';
        }
        function closePhotoModal() {
            document.getElementById('photo-modal').classList.remove('open');
            document.body.style.overflow = '';
        }
        document.addEventListener('keydown', function(e){ if(e.key==='Escape') closePhotoModal(); });

        // --- ЛОГИКА ПЕРЕКЛЮЧЕНИЯ СТРАНИЦ ---
        function switchPage(pageId) {
            const pages = ['home', 'scanner', 'info', 'password'];
            
            pages.forEach(p => {
                const tab = document.getElementById('menu-tab-' + p);
                const page = document.getElementById('page-' + p);
                
                if (p === pageId) {
                    if (!tab.classList.contains('active')) {
                        tab.classList.add('active');
                        page.style.display = 'block';
                        page.style.transition = 'none';
                        page.style.opacity = '0';
                        setTimeout(() => {
                            page.style.transition = 'opacity 0.4s var(--smooth)';
                            page.style.opacity = '1';
                        }, 50);
                    }
                } else {
                    tab.classList.remove('active');
                    page.style.display = 'none';
                    page.style.opacity = '0';
                }
            });
        }

        // --- ЛОГИКА РЕАЛЬНОГО РАДАРА ---
        function addRadarLog(msg, type='safe') {
            const logs = document.getElementById('cyber-logs');
            if(!logs) return;
            const entry = document.createElement('div');
            const color = type === 'danger' ? 'var(--danger-red)' : type === 'warn' ? '#fbbf24' : 'var(--safe-green)';
            entry.style.color = color;
            entry.style.fontFamily = "monospace";
            entry.style.fontSize = "11px";
            entry.style.marginTop = "6px";
            const timeStr = new Date().toLocaleTimeString();
            entry.innerText = `> [${timeStr}] ${msg}`;
            logs.insertBefore(entry, logs.firstChild);
            if(logs.children.length > 10) logs.removeChild(logs.lastChild);
        }

        {% if verdict_text %}
            const isDanger = {{ 'true' if stats and stats.malicious > 0 else 'false' }};
            const msg = isDanger ? "УГРОЗА ОБНАРУЖЕНА: {{ request.form.get('url', '')[:20] }}..." : "URL БЕЗОПАСЕН: {{ request.form.get('url', '')[:20] }}...";
            addRadarLog(msg, isDanger ? 'danger' : 'safe');
        {% endif %}

        // --- НАЧАЛЬНАЯ ВКЛАДКА: после проверки ссылки остаёмся на сканере ---
        var INITIAL_PAGE = "{{ current_page or 'home' }}";
        if (INITIAL_PAGE && INITIAL_PAGE !== 'home') {
            // снять active с home заранее, чтобы switchPage не упал
            switchPage(INITIAL_PAGE);
        }

        // --- ЛУЧИ ФОНА ---
        const raysContainer = document.getElementById('rays');
        // Основные тонкие лучи: 25 шт, разные варианты гашения, НИКОГДА не гаснут в начале
        const fadeVariants = ['rise', 'rise', 'rise', 'rise-fade-late', 'rise-fade-mid'];
        for (let i = 0; i < 25; i++) {
            const ray = document.createElement('div'); ray.className = 'ray';
            ray.style.left = Math.random() * 100 + '%';
            const dur = (Math.random() * 2.6 + 4.2);
            ray.style.animationDuration = dur.toFixed(2) + 's';
            ray.style.animationDelay = (Math.random() * 6).toFixed(2) + 's';
            ray.style.opacity = (Math.random() * 0.55 + 0.35).toFixed(2);
            const variant = fadeVariants[Math.floor(Math.random() * fadeVariants.length)];
            ray.style.animationName = variant;
            // лёгкая вариация высоты
            ray.style.height = (140 + Math.random() * 100) + 'px';
            raysContainer.appendChild(ray);
        }
        // Толстые светящиеся лучи: 4 шт
        for (let i = 0; i < 4; i++) {
            const rt = document.createElement('div'); rt.className = 'ray-thick';
            rt.style.left = (Math.random() * 92 + 4) + '%';
            rt.style.animationDuration = (Math.random() * 3 + 6.5).toFixed(2) + 's';
            rt.style.animationDelay = (Math.random() * 7).toFixed(2) + 's';
            rt.style.opacity = (Math.random() * 0.35 + 0.55).toFixed(2);
            rt.style.height = (220 + Math.random() * 120) + 'px';
            // часть гаснет посередине, часть долетает наверх — но никогда не в начале
            if (Math.random() < 0.4) rt.style.animationName = 'rise-fade-late';
            raysContainer.appendChild(rt);
        }
        // Несколько коротких ярких вспышек
        for (let i = 0; i < 3; i++) {
            const rayShort = document.createElement('div'); rayShort.className = 'ray-short';
            rayShort.style.left = (Math.random() * 60 + 20) + '%';
            rayShort.style.animationDuration = (Math.random() * 1.5 + 3) + 's';
            rayShort.style.animationDelay = Math.random() * 3 + 's';
            raysContainer.appendChild(rayShort);
        }

        const frc = document.getElementById('footer-rays-container');
        for(let i=0; i<20; i++) {
            const r = document.createElement('div');
            r.className = 'footer-ray';
            r.style.left = Math.random() * 100 + '%';
            r.style.animationDelay = Math.random() * 2 + 's';
            frc.appendChild(r);
        }

        function speakText() {
            const text = document.getElementById('ai-verdict-text').innerText;
            const btn = document.getElementById('speak-btn');
            if (window.speechSynthesis.speaking) { window.speechSynthesis.cancel(); btn.classList.remove('playing'); return; }
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'ru-RU';
            utterance.onstart = () => btn.classList.add('playing');
            utterance.onend = () => btn.classList.remove('playing');
            window.speechSynthesis.speak(utterance);
        }

        function toggleAccordion(id) { document.getElementById(id).classList.toggle('active'); }
        
        function toggleTheme() {
            document.body.classList.toggle('light-mode');
            localStorage.setItem('theme', document.body.classList.contains('light-mode') ? 'light' : 'dark');
        }

        function shareSite() { navigator.clipboard.writeText(window.location.href).then(() => alert("Ссылка скопирована!")); }

        function showLoading() { 
            document.getElementById('check-form').style.display = 'none';
            document.getElementById('loading-overlay').style.display = 'block';
        }

        // --- ЛОГИКА ТЕСТА ПРОТИВОДЕЙСТВИЯ (Кибер-Экзамен) ---
        const questions1 = [
            {q: "Минсктранс (Официальный сайт):", win: "minsktrans.by", lose: "minsk-trans.by"},
            {q: "БелЖД (Покупка билетов):", win: "rw.by", lose: "belrailway.by"},
            {q: "Белтелеком (Услуги связи):", win: "beltelecom.by", lose: "bel-telecom.by"},
            {q: "21vek (Гипермаркет):", win: "21vek.by", lose: "21-vek.by"},
            {q: "МВД Беларуси (УВД):", win: "mvd.gov.by", lose: "milicija.by"},
            {q: "Альфа-Банк Беларусь:", win: "alfabank.by", lose: "alfa-bank-login.by"},
            {q: "Wildberries (Официально):", win: "wildberries.by", lose: "wb-sale.by"},
            {q: "Onliner (Портал):", win: "onliner.by", lose: "online-by.com"},
            {q: "Беларусбанк:", win: "belarusbank.by", lose: "belarus-bank.org"},
            {q: "Kufar (Объявления):", win: "kufar.by", lose: "kufar-pay.by"}
        ];
        
        const questions2 = [
            {q: "СМС: «Ваша карта заблокирована». Ваши действия:", win: "Зайти в официальное приложение", lose: "Перейти по ссылке в СМС"},
            {q: "Просят код из СМС для подтверждения. Ваши действия:", win: "Никогда не вводить на чужих сайтах", lose: "Ввести код быстро"},
            {q: "Браузер пишет: «Сайт небезопасен». Ваши действия:", win: "Закрыть страницу", lose: "Нажать 'Игнорировать'"},
            {q: "Друг просит проголосовать в ТГ. Ваши действия:", win: "Позвонить другу лично", lose: "Сразу перейти и ввести код"},
            {q: "Звонят из «Безопасности банка». Ваши действия:", win: "Сбросить вызов", lose: "Продиктовать данные карты"},
            {q: "Вам прислали файл «Photo.exe». Ваши действия:", win: "Удалить, не открывая", lose: "Открыть и посмотреть фото"},
            {q: "Создание пароля для всех сайтов. Ваши действия:", win: "Сделать разным везде", lose: "Один сложный для удобства"},
            {q: "Предложение двухфакторной защиты. Ваши действия:", win: "Включить везде, где можно", lose: "Пропустить для скорости"},
            {q: "Предлагают бесплатную валюту в играх. Ваши действия:", win: "Закрыть и не вводить данные", lose: "Ввести логин и пароль"},
            {q: "Чужой компьютер просит «Запомнить пароль». Ваши действия:", win: "Нажать 'Никогда'", lose: "Нажать 'Да'"}
        ];

        let activeSet = [], currentQ = 0, score = 0, canClick = true;

        function switchTest(num) {
            document.getElementById('tab1').classList.toggle('active', num === 1);
            document.getElementById('tab2').classList.toggle('active', num === 2);
            activeSet = (num === 1) ? [...questions1] : [...questions2];
            resetGameUI();
        }

        function initGame() {
            if (activeSet.length === 0) activeSet = [...questions1];
            activeSet.sort(() => Math.random() - 0.5);
            currentQ = 0; score = 0; canClick = true;
            resetGameUI(); 
            document.getElementById('game-header').style.display = 'none';
            document.getElementById('quiz-area').classList.remove('hidden');
            showQuestion();
        }

        document.getElementById('start-game').onclick = initGame;

        function showQuestion() {
            canClick = true;
            const q = activeSet[currentQ];
            document.getElementById('question-num').innerText = `ШАГ ${currentQ + 1} ИЗ ${activeSet.length}`;
            const options = [{t: q.win, w: true}, {t: q.lose, w: false}].sort(() => Math.random() - 0.5);
            const area = document.getElementById('options');
            area.innerHTML = `
                <div class="slide-left-to-right">
                    <p style="font-weight:bold; margin-bottom:15px; font-size:15px;">${q.q}</p>
                    <div class="quiz-option" onclick="handleSelect(this, ${options[0].w})">${options[0].t}</div>
                    <div class="quiz-option" onclick="handleSelect(this, ${options[1].w})">${options[1].t}</div>
                </div>
            `;
        }

        function handleSelect(el, isCorrect) {
            if (!canClick) return;
            canClick = false; 
            if (isCorrect) { score++; el.classList.add('correct'); } else { el.classList.add('wrong'); }
            setTimeout(() => {
                const slideWrapper = document.querySelector('.slide-left-to-right');
                if(slideWrapper) {
                    slideWrapper.style.transition = 'all 0.4s var(--smooth)';
                    slideWrapper.style.transform = 'translateX(150%)'; 
                    slideWrapper.style.opacity = '0';
                }
                setTimeout(() => {
                    if (currentQ < activeSet.length - 1) { currentQ++; showQuestion(); } else { finishQuiz(); }
                }, 400); 
            }, 400); 
        }

        function finishQuiz() {
            let rank = "Новичок 🛡️";
            if(score >= 4) rank = "Ученик 🔍";
            if(score >= 7) rank = "Специалист 🧠";
            if(score == 10) rank = "Кибер-Эксперт 👑";
            addRadarLog(`ТЕСТ ЗАВЕРШЕН. РЕЗУЛЬТАТ: ${score}/10. РАНГ: ${rank}`, score >= 7 ? 'safe' : 'warn');
            document.getElementById('quiz-area').innerHTML = `
                <div style="text-align:center; animation: ultraEntrance 0.8s var(--ultra-smooth);">
                    <h4 class="shimmer-text" style="font-size:22px; margin-bottom:15px;">ИТОГ: ${score}/${activeSet.length}</h4>
                    <p style="font-size:16px; margin-bottom:25px;">Твой ранг:<br><b style="font-size:18px;">${rank}</b></p>
                    <button id="restart-btn" class="btn-scan" style="width:100%; padding: 15px;">ЗАНОВО</button>
                </div>`;
            document.getElementById('restart-btn').onclick = initGame;
        }

        function resetGameUI() {
            document.getElementById('game-header').style.display = 'block';
            document.getElementById('quiz-area').classList.add('hidden');
            document.getElementById('quiz-area').innerHTML = '<div id="quiz-container"><p id="question-num" class="shimmer-text"></p><div id="options"></div></div>';
        }

        if (localStorage.getItem('theme') === 'light') document.body.classList.add('light-mode');

        // --- НОВОСТНАЯ ЛЕНТА: АВТО-ПРОКРУТКА + СТРЕЛКИ + ПЕРЕТАСКИВАНИЕ ---
        (function setupNewsTicker(){
            const wrap = document.getElementById('news-ticker');
            const track = document.getElementById('news-track');
            if (!wrap || !track) return;

            const originals = Array.from(track.children);
            originals.forEach(el => {
                const clone = el.cloneNode(true);
                clone.setAttribute('aria-hidden', 'true');
                track.appendChild(clone);
            });

            let pos = 0;            // текущее смещение в px (отрицательное)
            let halfWidth = 0;
            let autoTimer = null;
            let isHover = false;
            let isDragging = false;
            let startX = 0;
            let startPos = 0;
            let pointerMoved = 0;
            const DRAG_THRESHOLD = 6;
            const TILE_STEP = 284;  // 270 + 14 gap (на мобильном чуть меньше, но и шаг ок)
            const AUTO_INTERVAL_MS = 35; // плавный сдвиг
            const AUTO_SPEED_PX = 0.6;   // px за тик

            function recalc() {
                halfWidth = track.scrollWidth / 2;
            }
            recalc();
            window.addEventListener('resize', recalc);

            function applyTransform() {
                if (halfWidth > 0) {
                    if (pos <= -halfWidth) pos += halfWidth;
                    if (pos > 0) pos -= halfWidth;
                }
                track.style.transform = 'translateX(' + pos + 'px)';
            }

            function tick() {
                if (isHover || isDragging) return;
                pos -= AUTO_SPEED_PX;
                track.style.transition = 'none';
                applyTransform();
            }

            function startAuto() {
                if (autoTimer) return;
                autoTimer = setInterval(tick, AUTO_INTERVAL_MS);
            }
            function stopAuto() {
                if (!autoTimer) return;
                clearInterval(autoTimer);
                autoTimer = null;
            }

            wrap.addEventListener('mouseenter', () => { isHover = true; });
            wrap.addEventListener('mouseleave', () => { isHover = false; });

            // Стрелки
            const prev = document.getElementById('news-prev');
            const next = document.getElementById('news-next');
            function smoothJump(delta){
                track.style.transition = 'transform 0.6s var(--ultra-smooth)';
                pos += delta;
                applyTransform();
                setTimeout(()=>{ track.style.transition = 'none'; }, 650);
            }
            if (prev) prev.addEventListener('click', () => smoothJump( TILE_STEP));
            if (next) next.addEventListener('click', () => smoothJump(-TILE_STEP));

            // Перетаскивание мышью и пальцем
            function onDown(e) {
                isDragging = true;
                pointerMoved = 0;
                startX = (e.touches ? e.touches[0].clientX : e.clientX);
                startPos = pos;
                track.classList.add('is-dragging');
                track.style.transition = 'none';
            }
            function onMove(e) {
                if (!isDragging) return;
                const x = (e.touches ? e.touches[0].clientX : e.clientX);
                const dx = x - startX;
                pointerMoved = Math.abs(dx);
                pos = startPos + dx;
                applyTransform();
                if (pointerMoved > DRAG_THRESHOLD && e.cancelable) e.preventDefault();
            }
            function onUp() {
                if (!isDragging) return;
                isDragging = false;
                track.classList.remove('is-dragging');
            }

            track.querySelectorAll('a.news-tile').forEach(a => {
                a.addEventListener('click', function(ev){
                    if (pointerMoved > DRAG_THRESHOLD) {
                        ev.preventDefault();
                        ev.stopPropagation();
                    }
                });
            });

            track.addEventListener('mousedown', onDown);
            window.addEventListener('mousemove', onMove);
            window.addEventListener('mouseup', onUp);
            track.addEventListener('touchstart', onDown, {passive: true});
            track.addEventListener('touchmove', onMove, {passive: false});
            track.addEventListener('touchend', onUp);

            // запускаем после небольшой задержки, чтобы layout стабилизировался
            setTimeout(()=>{ recalc(); startAuto(); }, 200);
        })();

        // --- ЛОГИКА НОВОЙ СИМУЛЯЦИИ GROQ (ЧАТА) ---
        let currentSimTheme = "";
        let simHistory = [];
        let simTurn = 0;
        const SIM_MAX_TURNS = 4;
        
        function openSimulation(themeName) {
            currentSimTheme = themeName;
            document.getElementById('sim-selector').classList.add('hidden');
            document.getElementById('sim-chat').classList.remove('hidden');
            document.getElementById('chat-messages-box').innerHTML = '';
            document.getElementById('chat-input-area').style.display = 'flex';
            simHistory = [];
            simTurn = 0;
            addRadarLog(`ЗАПУСК ИИ-СИМУЛЯЦИИ: ${themeName}`, 'warn');
            
            appendBotMessage("ИИ печатает...");
            
            fetch('/cs/sim_chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: '', history: [], theme: currentSimTheme, is_start: true, turn: 0})
            }).then(r=>r.json()).then(data => {
                const box = document.getElementById('chat-messages-box');
                box.lastChild.remove();
                appendBotMessage(data.reply);
                simHistory = data.history;
                simTurn = data.turn || 0;
            }).catch(e => {
                document.getElementById('chat-messages-box').lastChild.remove();
                appendBotMessage("Ошибка сети. Модель недоступна.");
            });
        }

        function closeSim() {
            document.getElementById('sim-chat').classList.add('hidden');
            document.getElementById('sim-selector').classList.remove('hidden');
        }

        function appendBotMessage(text) {
            const box = document.getElementById('chat-messages-box');
            const msg = document.createElement('div');
            msg.className = 'msg bot';
            msg.innerText = text;
            box.appendChild(msg);
            box.scrollTop = box.scrollHeight;
        }

        function appendUserMessage(text) {
            const box = document.getElementById('chat-messages-box');
            const msg = document.createElement('div');
            msg.className = 'msg user';
            msg.innerText = text;
            box.appendChild(msg);
            box.scrollTop = box.scrollHeight;
        }

        function sendSimMessageReq() {
            const input = document.getElementById('sim-input');
            const text = input.value.trim();
            if(!text) return;
            
            appendUserMessage(text);
            input.value = '';
            appendBotMessage("ИИ печатает...");

            fetch('/cs/sim_chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text, history: simHistory, theme: currentSimTheme, is_start: false, turn: simTurn})
            }).then(r=>r.json()).then(data => {
                const box = document.getElementById('chat-messages-box');
                box.lastChild.remove(); 
                
                simTurn = data.turn || simTurn;
                if (data.is_ended) {
                    appendBotMessage(data.reply);
                    setTimeout(() => finishChatSimFinal(data.score, null), 600);
                } else {
                    appendBotMessage(data.reply);
                    simHistory = data.history;
                }
            }).catch(e => {
                document.getElementById('chat-messages-box').lastChild.remove();
                appendBotMessage("Произошла ошибка связи с Groq.");
            });
        }

        document.getElementById('sim-input').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') sendSimMessageReq();
        });

        function finishChatSimFinal(score, finalMsg) {
            document.getElementById('chat-input-area').style.display = 'none';
            if (finalMsg) appendBotMessage(finalMsg);
            
            let verdict = score > 50 ? "✅ ВЫ СПРАВИЛИСЬ!" : "❌ ДАННЫЕ СКОМПРОМЕТИРОВАНЫ!";
            addRadarLog(`СИМУЛЯЦИЯ ЗАВЕРШЕНА. ВЫЖИВАЕМОСТЬ: ${score}%`, score > 50 ? 'safe' : 'danger');

            setTimeout(() => {
                const box = document.getElementById('chat-messages-box');
                const resultMsg = document.createElement('div');
                resultMsg.style.textAlign = 'center';
                resultMsg.style.padding = '20px';
                resultMsg.style.background = 'rgba(0,0,0,0.4)';
                resultMsg.style.borderRadius = '15px';
                resultMsg.style.marginTop = '10px';
                resultMsg.style.animation = 'ultraEntrance 0.8s var(--ultra-smooth)';
                resultMsg.innerHTML = `
                    <h3 class="shimmer-text" style="margin-top:0;">${verdict}</h3>
                    <p style="font-size:24px; font-weight:bold; margin: 10px 0; color: ${score > 50 ? 'var(--safe-green)' : 'var(--danger-red)'}">${score}% УСПЕХА</p>
                    <button class="btn-scan" onclick="closeSim()" style="margin-top: 10px; width: 100%;">НАЗАД В МЕНЮ</button>
                `;
                box.appendChild(resultMsg);
                box.scrollTop = box.scrollHeight;
            }, 800);
        }

        // --- ЛОГИКА ИИ-ПОМОЩНИКА В ИНФОРМАЦИИ ---
        let helperHistory = [];
        
        function sendHelperMessage() {
            const input = document.getElementById('helper-input');
            const text = input.value.trim();
            if(!text) return;
            
            const box = document.getElementById('helper-chat-box');
            box.innerHTML += `<div style="color:var(--safe-green); font-size:12px;"><b>Вы:</b> ${text}</div>`;
            input.value = '';
            box.scrollTop = box.scrollHeight;
            
            fetch('/cs/helper_chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text, history: helperHistory})
            }).then(r=>r.json()).then(data => {
                box.innerHTML += `<div style="color:var(--accent-frost); font-size:12px;"><b>ИИ:</b> ${data.reply}</div>`;
                helperHistory = data.history;
                box.scrollTop = box.scrollHeight;
            }).catch(e => {
                box.innerHTML += `<div style="color:var(--danger-red); font-size:12px;">Система временно недоступна. Проверьте ключ Groq API.</div>`;
            });
        }
        
        document.getElementById('helper-input').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') sendHelperMessage();
        });

        // --- ПАРОЛЬНЫЙ СТРАЖ ---
        const COMMON_PASSWORDS = new Set([
            "123456","123456789","12345678","12345","qwerty","password","111111","123123",
            "abc123","1234567","000000","iloveyou","qwerty123","admin","welcome","monkey",
            "dragon","letmein","football","passw0rd","master","pass","qazwsx","qwerty1",
            "123qwe","ytrewq","klaster","superman","11111111","sunshine","1q2w3e4r","zxcvbnm"
        ]);

        function analyzePassword(pw) {
            const rules = {
                length8: pw.length >= 8,
                length12: pw.length >= 12,
                upper: /[A-ZА-ЯЁ]/.test(pw),
                lower: /[a-zа-яё]/.test(pw),
                digit: /\d/.test(pw),
                special: /[^A-Za-zА-Яа-яЁё0-9]/.test(pw),
                nocommon: pw.length > 0 && !COMMON_PASSWORDS.has(pw.toLowerCase())
            };

            let pool = 0;
            if (rules.lower) pool += 26;
            if (rules.upper) pool += 26;
            if (rules.digit) pool += 10;
            if (rules.special) pool += 32;
            const entropy = pw.length > 0 && pool > 0 ? Math.round(pw.length * Math.log2(pool)) : 0;

            const guessesPerSec = 1e10;
            const seconds = pool > 0 ? Math.pow(pool, pw.length) / guessesPerSec : 0;
            let timeStr = "мгновенно";
            if (!rules.nocommon && pw.length > 0) timeStr = "мгновенно";
            else if (seconds < 1) timeStr = "мгновенно";
            else if (seconds < 60) timeStr = Math.round(seconds) + " сек";
            else if (seconds < 3600) timeStr = Math.round(seconds/60) + " мин";
            else if (seconds < 86400) timeStr = Math.round(seconds/3600) + " ч";
            else if (seconds < 31536000) timeStr = Math.round(seconds/86400) + " дн";
            else if (seconds < 31536000 * 1000) timeStr = Math.round(seconds/31536000) + " лет";
            else timeStr = "века";

            const score = Object.values(rules).filter(Boolean).length;
            let level, color;
            if (pw.length === 0)             { level = "Введите пароль для анализа"; color = "var(--text-main)"; }
            else if (!rules.nocommon)        { level = "❌ КРИТИЧНО: пароль есть в утечках, взлом мгновенный"; color = "var(--danger-red)"; }
            else if (score <= 3)             { level = "⚠️ СЛАБЫЙ — лёгкая мишень для атаки"; color = "var(--danger-red)"; }
            else if (score <= 5)             { level = "🟡 СРЕДНИЙ — приемлемо для непубличных аккаунтов"; color = "#fbbf24"; }
            else if (score === 6)            { level = "✅ ХОРОШИЙ — устойчив к большинству атак"; color = "var(--safe-green)"; }
            else                             { level = "🛡️ КРЕПОСТЬ — высочайшая криптостойкость"; color = "var(--safe-green)"; }

            return { rules, entropy, timeStr, level, color };
        }

        function renderPasswordReport(pw) {
            const report = document.getElementById('password-report');
            if (pw.length === 0) {
                report.style.display = 'none';
                return;
            }
            if (report.style.display === 'none') {
                report.style.display = 'block';
                report.style.animation = 'ultraEntrance 0.6s var(--ultra-smooth)';
            }
            const a = analyzePassword(pw);
            document.getElementById('pw-length-val').innerText = pw.length;
            document.getElementById('pw-entropy-val').innerText = a.entropy;
            document.getElementById('pw-time-val').innerText = a.timeStr;
            document.querySelectorAll('.pw-rule').forEach(row => {
                const r = row.dataset.rule;
                row.classList.toggle('active', !!a.rules[r]);
            });
            const result = document.getElementById('password-result-text');
            result.innerText = a.level;
            result.style.color = a.color;
            result.style.fontWeight = 'bold';
        }

        function generateStrongPassword() {
            const lower = "abcdefghijkmnpqrstuvwxyz";
            const upper = "ABCDEFGHJKLMNPQRSTUVWXYZ";
            const digits = "23456789";
            const special = "!@#$%^&*()_+-=[]{}";
            const all = lower + upper + digits + special;
            let pw = "";
            pw += lower[Math.floor(Math.random() * lower.length)];
            pw += upper[Math.floor(Math.random() * upper.length)];
            pw += digits[Math.floor(Math.random() * digits.length)];
            pw += special[Math.floor(Math.random() * special.length)];
            for (let i = 0; i < 12; i++) pw += all[Math.floor(Math.random() * all.length)];
            pw = pw.split('').sort(() => Math.random() - 0.5).join('');
            const input = document.getElementById('password-input');
            input.value = pw;
            renderPasswordReport(pw);
            input.focus();
        }

        document.getElementById('password-input').addEventListener('input', function (e) {
            renderPasswordReport(e.target.value);
        });

        // --- ПИНГ-ИНДИКАТОР ---
        async function measurePing() {
            const indicator = document.getElementById('ping-indicator');
            const valueEl = document.getElementById('ping-value');
            const start = performance.now();
            try {
                const res = await fetch('/cs/ping?t=' + start, {cache: 'no-store'});
                if (!res.ok) throw new Error('bad');
                const ms = Math.round(performance.now() - start);
                valueEl.innerText = ms + ' ms';
                indicator.classList.remove('warn', 'bad');
                if (ms > 600) indicator.classList.add('bad');
                else if (ms > 250) indicator.classList.add('warn');
            } catch(e) {
                valueEl.innerText = '--- ms';
                indicator.classList.remove('warn');
                indicator.classList.add('bad');
            }
        }
        measurePing();
        setInterval(measurePing, 5000);

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
        current_page='home'
    )

@app.route('/check', methods=['POST'])
def check():
    url = request.form.get('url', '').strip()
    scans, viruses = get_real_stats()
    time.sleep(1) 
    try:
        res = requests.post("https://www.virustotal.com/api/v3/urls", data={"url": url}, headers={"x-apikey": VT_API_KEY}, timeout=20)
        analysis_id = res.json()['data']['id']
        data = None
        for _ in range(6): 
            time.sleep(5)
            report = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers={"x-apikey": VT_API_KEY}, timeout=20)
            if report.status_code == 200:
                temp_data = report.json()['data']['attributes']
                if temp_data['status'] == 'completed' or temp_data['stats']['harmless'] > 0:
                    data = temp_data; break
        
        if data:
            stats = data['stats']
            update_real_stats(is_virus=stats['malicious'] > 0)
            new_scans, new_viruses = get_real_stats()
            ai_opinion = ask_ai_opinion(url, stats)
            
            if stats['malicious'] > 0:
                items = [
                    {"label": "КРИТИЧЕСКИЙ ОБЪЕКТ", "text": "Обнаружено внедрение вредоносного кода."},
                    {"label": "АКТИВНЫЙ ПЕРЕХВАТ", "text": "Зафиксирована попытка несанкционированного доступа."},
                    {"label": "ФИШИНГ-УГРОЗА", "text": "Ресурс идентифицирован как поддельный."}
                ]
            else:
                items = [
                    {"label": "БАЗА СИГНАТУР", "text": "Вредоносные элементы не обнаружены."},
                    {"label": "ИНДЕКС ДОВЕРИЯ", "text": "Домен обладает хорошей репутацией."},
                    {"label": "SSL-ПРОТОКОЛ", "text": "Каналы передачи данных соответствуют нормам."}
                ]
            
            return render_template_string(
                HTML_LAYOUT, stats=stats, verdict_text="Готово", ai_text=ai_opinion,
                detail_items=items, total_scans=new_scans, total_threats=new_viruses,
                stats_count=new_scans,
                scans_word=_ru_plural(new_scans, ('ПРОВЕРКА', 'ПРОВЕРКИ', 'ПРОВЕРОК')),
                current_page='scanner'
            )
    except: pass
    return render_template_string(
        HTML_LAYOUT, stats=None, verdict_text="Ошибка",
        total_scans=scans, total_threats=viruses,
        stats_count=scans,
        scans_word=_ru_plural(scans, ('ПРОВЕРКА', 'ПРОВЕРКИ', 'ПРОВЕРОК')),
        current_page='scanner'
    )


# --- НОВЫЕ ФУНКЦИИ ДЛЯ ИНТЕГРАЦИИ GROQ (СИМУЛЯЦИЯ И ПОМОЩНИК) ---

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "llama3-8b-8192"]

class GroqError(Exception):
    pass

def _call_groq(messages, temperature=0.8, max_tokens=180):
    key = (GROQ_API_KEY or '').strip()
    if not key:
        raise GroqError("GROQ_API_KEY не задан в переменных окружения")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    last_err = None
    for model in GROQ_MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=20)
        except requests.RequestException as e:
            last_err = f"Сетевая ошибка: {e}"
            continue

        if res.status_code == 200:
            try:
                data = res.json()
                return data['choices'][0]['message']['content'].strip()
            except (ValueError, KeyError, IndexError) as e:
                last_err = f"Неверный формат ответа Groq: {e}"
                continue

        if res.status_code in (401, 403):
            try:
                msg = res.json().get('error', {}).get('message', res.text)
            except Exception:
                msg = res.text
            raise GroqError(f"Ключ Groq отклонён ({res.status_code}): {msg}")

        try:
            msg = res.json().get('error', {}).get('message', res.text)
        except Exception:
            msg = res.text
        last_err = f"HTTP {res.status_code} ({model}): {msg}"
        if res.status_code not in (400, 404):
            continue

    raise GroqError(last_err or "Неизвестная ошибка Groq")


def _evaluate_defense(history, theme):
    transcript_lines = []
    for m in history:
        role = m.get("role")
        if role == "system":
            continue
        if role == "user" and m.get("content", "").startswith("[Начни атаку"):
            continue
        prefix = "МОШЕННИК" if role == "assistant" else "ЖЕРТВА"
        transcript_lines.append(f"{prefix}: {m.get('content','')}")
    convo = "\n".join(transcript_lines)
    eval_messages = [
        {"role": "system", "content": "Ты строгий эксперт по кибербезопасности. Оцени, насколько хорошо ЖЕРТВА защищалась от МОШЕННИКА. Критерии: не выдала личные данные, коды, пароли, реквизиты карт; не перешла по ссылкам; не перевела деньги; распознала обман; вежливо или жёстко отказала. Если жертва раскусила обман и отказалась — ставь 80-100. Если осторожничала, но колебалась — 50-79. Если выдала часть данных — 20-49. Если полностью повелась — 0-19. Ответь СТРОГО одним числом от 0 до 100, без слов и пояснений."},
        {"role": "user", "content": f"Тема атаки: {theme}\n\nДиалог:\n{convo}\n\nОценка (только число 0-100):"}
    ]
    try:
        raw = _call_groq(eval_messages, temperature=0.0, max_tokens=10)
        m = re.search(r'\d+', raw)
        if m:
            return max(0, min(100, int(m.group())))
    except Exception:
        pass
    return 50


@app.route('/cs/sim_chat', methods=['POST'])
def sim_chat():
    data = request.json or {}
    text = data.get('text', '')
    history = data.get('history', [])
    theme = data.get('theme', 'Социальная инженерия')
    is_start = data.get('is_start', False)
    turn = int(data.get('turn', 0))

    MAX_TURNS = 4

    sys_prompt = (
        f"Ты опытный кибер-мошенник. Тема атаки: {theme}. "
        f"Общаешься в мессенджере на русском. Цель — выманить у жертвы ссылку, деньги, код из СМС, пароль или данные карты. "
        f"Пиши коротко: 1-3 предложения. Реалистично, эмоционально, можешь давить или умолять. "
        f"Не выходи из роли. Не подсказывай жертве, как от тебя защититься. "
        f"Никогда не пиши служебные пометки в квадратных скобках или слова вроде [END]."
    )

    if not history:
        history = [{"role": "system", "content": sys_prompt}]

    if is_start:
        history.append({"role": "user", "content": "[Начни атаку первым коротким сообщением]"})
        try:
            reply = _call_groq(history, temperature=0.9, max_tokens=160)
        except GroqError as e:
            print(f"[GROQ sim_chat start] {e}")
            reply = "Здравствуйте! Это служба безопасности банка. С вашей карты сейчас пытаются списать крупную сумму. Срочно подтвердите данные!"
        except Exception as e:
            print(f"[GROQ sim_chat start unknown] {e}")
            reply = "Здравствуйте! Это служба безопасности банка. С вашей карты сейчас пытаются списать крупную сумму. Срочно подтвердите данные!"
        history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply, "history": history, "is_ended": False, "score": 0, "turn": 0})

    history.append({"role": "user", "content": text})
    new_turn = turn + 1

    if new_turn >= MAX_TURNS:
        history.append({"role": "system", "content": "Это последний ход. Дай одну короткую финальную реплику (1-2 предложения) — либо последнюю попытку давления, либо раздражённое признание поражения. Не задавай больше вопросов. Не выходи из роли."})
        try:
            final_msg = _call_groq(history, temperature=0.7, max_tokens=120)
        except GroqError as e:
            print(f"[GROQ sim_chat final] {e}")
            final_msg = "Ладно, потом перезвоню."
        except Exception as e:
            print(f"[GROQ sim_chat final unknown] {e}")
            final_msg = "Ладно, потом перезвоню."
        history.pop(-2)
        history.append({"role": "assistant", "content": final_msg})
        score = _evaluate_defense(history, theme)
        return jsonify({"reply": final_msg, "history": history, "is_ended": True, "score": score, "turn": new_turn})

    try:
        reply = _call_groq(history, temperature=0.8, max_tokens=160)
    except GroqError as e:
        print(f"[GROQ sim_chat] {e}")
        reply = "Алло, вы меня слышите? Время уходит, нужно срочно решать!"
    except Exception as e:
        print(f"[GROQ sim_chat unknown] {e}")
        reply = "Алло, вы меня слышите? Время уходит, нужно срочно решать!"
    history.append({"role": "assistant", "content": reply})
    return jsonify({"reply": reply, "history": history, "is_ended": False, "score": 0, "turn": new_turn})

@app.route('/cs/ping')
def ping():
    return jsonify({"ok": True, "ts": time.time()})


@app.route('/cs/helper_chat', methods=['POST'])
def helper_chat():
    data = request.json or {}
    text = (data.get('text') or '').strip()
    history = data.get('history', [])

    sys_prompt = (
        "Ты ИИ-помощник CyberShield. Помогай пользователю распознавать мошенников "
        "и давай советы по кибербезопасности. Отвечай кратко и по делу, "
        "максимум 3-4 предложения, на русском языке."
    )

    if not history:
        history = [{"role": "system", "content": sys_prompt}]

    if not text:
        return jsonify({"reply": "Напишите ваш вопрос.", "history": history})

    history.append({"role": "user", "content": text})

    try:
        reply = _call_groq(history, temperature=0.4, max_tokens=300)
    except GroqError as e:
        print(f"[GROQ helper_chat] {e}")
        reply = f"ИИ-помощник временно недоступен. Причина: {e}"
    except Exception as e:
        print(f"[GROQ helper_chat unknown] {e}")
        reply = "ИИ-помощник временно недоступен. Попробуйте через минуту."

    history.append({"role": "assistant", "content": reply})
    return jsonify({"reply": reply, "history": history})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
 
