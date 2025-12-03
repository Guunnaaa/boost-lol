import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import plotly.graph_objects as go
from urllib.parse import quote
from collections import Counter
import concurrent.futures
import threading
import html
import time
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="LoL Duo Analyst V72 (Percent Diff)", layout="wide")

# --- API KEY ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except (FileNotFoundError, KeyError):
    API_KEY = os.environ.get("RIOT_API_KEY")

if not API_KEY:
    st.error("⚠️ API Key missing. Add RIOT_API_KEY to Streamlit secrets or Env Vars.")
    st.stop()

# --- ASSETS & CONSTANTES ---
BACKGROUND_IMAGE_URL = "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123"

QUEUE_MAP = {
    "Ranked Solo/Duo": 420,
    "Ranked Flex": 440,
    "Draft Normal": 400,
    "ARAM": 450,
    "Arena": 1700
}

ROLE_ICONS = {
    "TOP": "🛡️ TOP", "JUNGLE": "🌲 JUNGLE", "MIDDLE": "🧙 MID", 
    "BOTTOM": "🏹 ADC", "UTILITY": "🩹 SUPP", "UNKNOWN": "❓ FILL"
}

# --- TRADUCTIONS ---
TRANSLATIONS = {
    "FR": {
        "title": "LoL Duo Analyst",
        "btn_scan": "LANCER L'ANALYSE",
        "placeholder": "Exemple: Kameto#EUW",
        "label_id": "Riot ID", "lbl_region": "RÉGION", "lbl_mode": "MODE", "dpm_btn": "🔗 Voir sur dpm.lol",
        "lbl_duo_detected": "🚨 DUO DÉTECTÉ AVEC {duo} 🚨",
        
        "v_hyper": "CARRY MACHINE", "s_hyper": "{target} inflige des dégâts monstrueux comparé à {duo}",
        "v_survivor": "IMMORTEL", "s_survivor": "{target} survit et joue propre, {duo} meurt trop souvent",
        "v_tactician": "MASTERMIND", "s_tactician": "{target} gagne grâce à la vision et au map control",
        "v_breacher": "DESTRUCTEUR", "s_breacher": "{target} prend les tours, {duo} regarde",
        "v_solid": "DUO FUSIONNEL", "s_solid": "Synergie parfaite entre {target} et {duo}",
        
        "v_passenger": "PASSAGER", "s_passenger": "{target} se laisse porter par {duo} (Dégâts faibles)",
        "v_feeder": "ZONE DE DANGER", "s_feeder": "{target} passe trop de temps à l'écran gris vs {duo}",
        "v_struggle": "EN DIFFICULTÉ", "s_struggle": "{target} peine à suivre le rythme de {duo}",

        "solo": "LOUP SOLITAIRE", "solo_sub": "Aucun duo récurrent détecté sur 20 parties.",
        "loading": "Analyse tactique en cours...",
        
        "q_surv": "Injouable (KDA)", "q_dmg": "Gros Dégâts", "q_obj": "Destructeur", "q_vis": "Contrôle Map",
        "f_feed": "Meurt trop souvent", "f_blind": "Vision faible", "f_afk": "Dégâts faibles",
        "error_no_games": "Aucune partie trouvée.", "error_hint": "Vérifie la région ou le mode de jeu."
    },
    "EN": {
        "title": "LoL Duo Analyst", "btn_scan": "START ANALYSIS", "placeholder": "Example: Faker#KR1",
        "label_id": "Riot ID", "lbl_region": "REGION", "lbl_mode": "MODE", "dpm_btn": "🔗 Check dpm.lol", 
        "lbl_duo_detected": "🚨 DUO DETECTED WITH {duo} 🚨",
        
        "v_hyper": "DMG CARRY", "s_hyper": "{target} is dealing massive damage compared to {duo}",
        "v_survivor": "IMMORTAL", "s_survivor": "{target} survives, {duo} dies too much",
        "v_tactician": "MASTERMIND", "s_tactician": "{target} wins via vision & macro",
        "v_breacher": "BREACHER", "s_breacher": "{target} takes towers, {duo} watches",
        "v_solid": "PERFECT DUO", "s_solid": "Perfect synergy between {target} and {duo}",
        
        "v_passenger": "PASSENGER", "s_passenger": "{target} is getting carried by {duo} (Low Dmg)",
        "v_feeder": "DANGER ZONE", "s_feeder": "{target} sees grey screen too often vs {duo}",
        "v_struggle": "STRUGGLING", "s_struggle": "{target} can't keep up with {duo}",

        "solo": "SOLO PLAYER", "solo_sub": "No recurring partner found.",
        "loading": "Analyzing...", "q_surv": "Unkillable", "q_dmg": "Heavy Hitter", "q_obj": "Destroyer", "q_vis": "Map Control",
        "f_feed": "Too fragile", "f_blind": "Blind", "f_afk": "Low Dmg", "error_no_games": "No games found.", "error_hint": "Check Region."
    }
}
TRANSLATIONS["ES"] = TRANSLATIONS["EN"]
TRANSLATIONS["KR"] = TRANSLATIONS["EN"]

# --- MAP DRAPEAUX ---
LANG_MAP = {"🇫🇷 FR": "FR", "🇺🇸 EN": "EN", "🇪🇸 ES": "ES", "🇰🇷 KR": "KR"}

# --- CSS MODERNE ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    
    .stApp {{
        background-image: url("{BACKGROUND_IMAGE_URL}");
        background-size: 150px; background-repeat: repeat; background-attachment: fixed;
    }}
    
    .block-container {{
        max-width: 1400px !important; 
        padding-top: 3rem !important; padding-bottom: 3rem !important;
        background: rgba(12, 12, 12, 0.95); backdrop-filter: blur(15px);
        border-radius: 15px; border: 1px solid #333; box-shadow: 0 20px 50px rgba(0,0,0,0.9);
        margin-top: 20px !important;
    }}

    .main-title {{
        font-size: 55px; font-weight: 900; text-align: center; margin-bottom: 30px; margin-top: 10px;
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 10px rgba(0, 114, 255, 0.5)); text-transform: uppercase;
    }}
    
    .player-card {{
        background: rgba(30, 30, 30, 0.5); border-radius: 16px; padding: 25px;
        border: 1px solid rgba(255,255,255,0.08); text-align: center; height: 100%;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.2);
    }}
    .player-name {{ font-size: 28px; font-weight: 800; color: white; margin-bottom: 5px; word-break: break-all; }}
    .player-sub {{ font-size: 14px; color: #aaa; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }}

    .badge {{
        display: inline-block; padding: 4px 8px; border-radius: 4px; 
        font-size: 11px; font-weight: 700; margin: 2px; text-transform: uppercase;
    }}
    .b-green {{ background: rgba(0, 255, 153, 0.15); color: #00ff99; border: 1px solid #00ff99; }}
    .b-red {{ background: rgba(255, 68, 68, 0.15); color: #ff6666; border: 1px solid #ff4444; }}
    .b-blue {{ background: rgba(0, 191, 255, 0.15); color: #00BFFF; border: 1px solid #00BFFF; }}
    .b-gold {{ background: rgba(255, 215, 0, 0.15); color: #FFD700; border: 1px solid #FFD700; }}

    .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px; }}
    .stat-item {{ background: rgba(0,0,0,0.3); padding: 12px; border-radius: 10px; text-align: left; border: 1px solid rgba(255,255,255,0.05); }}
    .stat-val-container {{ display: flex; align-items: center; gap: 8px; }}
    .stat-val {{ font-size: 20px; font-weight: 700; color: white; }}
    .stat-lbl {{ font-size: 11px; color: #999; text-transform: uppercase; margin-top: 4px; font-weight: 600; letter-spacing: 0.5px; }}
    
    .stat-diff {{ font-size: 12px; font-weight: 700; padding: 2px 5px; border-radius: 4px; }}
    .pos {{ color: #00ff99; background: rgba(0,255,153,0.15); }} 
    .neg {{ color: #ff4444; background: rgba(255,68,68,0.15); }}
    .neutral {{ color: #888; }}

    .verdict-box {{
        text-align: center; padding: 30px; border-radius: 16px; margin: 20px 0 40px 0;
        background: rgba(20, 20, 20, 0.8); border: 2px solid #333;
    }}
    
    .dpm-btn {{
        background: rgba(37, 99, 235, 0.2); color: #60a5fa !important; padding: 5px 10px;
        border-radius: 6px; text-decoration: none; font-size: 12px; border: 1px solid #2563eb;
    }}

    .stButton > button {{
        width: 100%; height: 55px; background: linear-gradient(135deg, #ff0055, #cc0044);
        color: white; font-size: 20px; font-weight: 800; border: none; border-radius: 10px;
        text-transform: uppercase; transition: 0.3s;
    }}
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 25px rgba(255,0,60,0.5); }}
    
    .stTextInput > label {{ display: none; }}
    .stForm > div[data-testid="stFormEnterToSubmit"] {{ display: none; }}
</style>
""", unsafe_allow_html=True)

# --- HEADER & LANGUAGE ---
c_title, c_lang = st.columns([5, 1])
with c_lang:
    selected_label = st.selectbox("Lang", list(LANG_MAP.keys()), label_visibility="collapsed")
    lang_code = LANG_MAP[selected_label]

T = TRANSLATIONS.get(lang_code, TRANSLATIONS["EN"])
st.markdown(f'<div class="main-title">{T["title"]}</div>', unsafe_allow_html=True)

# --- FORMULAIRE ---
with st.form("search_form"):
    c1, c2, c3 = st.columns([3, 1, 1], gap="small")
    with c1:
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
            <span style="font-size:14px; font-weight:700; color:#ddd;">{T['label_id']}</span>
            <a href="https://dpm.lol" target="_blank" class="dpm-btn">{T['dpm_btn']}</a>
        </div>""", unsafe_allow_html=True)
        riot_id_input = st.text_input("HiddenLabel", placeholder=T["placeholder"], label_visibility="collapsed")
    with c2:
        st.markdown(f"<span style='font-size:14px; font-weight:700; color:#ddd;'>{T['lbl_region']}</span>", unsafe_allow_html=True)
        region_select = st.selectbox("RegionLabel", ["EUW1", "NA1", "KR", "EUN1", "TR1"], label_visibility="collapsed")
    with c3:
        st.markdown(f"<span style='font-size:14px; font-weight:700; color:#ddd;'>{T['lbl_mode']}</span>", unsafe_allow_html=True)
        queue_label = st.selectbox("ModeLabel", list(QUEUE_MAP.keys()), label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button(T["btn_scan"])

# --- HELPERS ---
@st.cache_data(ttl=3600)
def get_dd_version():
    try: 
        resp = requests.get("https://ddragon.leagueoflegends.com/api/versions.json", timeout=5)
        if resp.status_code == 200: return resp.json()[0]
    except: pass
    return "14.23.1"

DD_VERSION = get_dd_version()

def get_champ_url(champ_name):
    if not champ_name: return "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Poro_0.jpg"
    clean = str(champ_name).replace(" ", "").replace("'", "").replace(".", "")
    mapping = {"wukong": "MonkeyKing", "renataglasc": "Renata", "nunu&willump": "Nunu", "kogmaw": "KogMaw", "reksai": "RekSai", "drmundo": "DrMundo", "belveth": "Belveth"}
    return f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/img/champion/{mapping.get(clean.lower(), clean)}.png"

def safe_format(text, target, duo):
    try: return text.format(target=html.escape(str(target)), duo=html.escape(str(duo)))
    except: return text

# --- LOGIQUE SCORE & STYLE ---
def determine_playstyle(stats, role, lang_dict):
    badges = []
    kda = stats.get('kda', 0)
    vis = stats.get('vis_min', 0)
    kp = stats.get('kp', 0)
    dmg = stats.get('dmg_min', 0)
    obj = stats.get('obj', 0)
    sk = stats.get('solokills', 0)

    if kda >= 4.0: badges.append((lang_dict.get("q_surv", "Survival"), "b-gold"))
    if vis >= 2.0 or (role == "UTILITY" and vis >= 2.5): badges.append((lang_dict.get("q_vis", "Oracle"), "b-blue")) 
    if kp >= 0.65: badges.append(("Teamplayer", "b-green"))
    if dmg >= 800: badges.append((lang_dict.get("q_dmg", "Damage"), "b-red"))
    if sk >= 2.5: badges.append(("Duelist", "b-red"))
    if obj >= 5000: badges.append((lang_dict.get("q_obj", "Breacher"), "b-gold"))
    
    if kda < 1.5: badges.append((lang_dict.get("f_feed", "Grey Screen"), "b-red"))
    if vis < 0.4 and role != "ADC": badges.append((lang_dict.get("f_blind", "Blind"), "b-red"))
    if dmg < 300 and role not in ["UTILITY", "JUNGLE"]: badges.append((lang_dict.get("f_afk", "AFK"), "b-blue"))

    if not badges: badges.append(("Standard", "b-blue"))
    return badges[:3] 

def create_radar(data_list, names, colors, title=None):
    categories = ['Combat', 'Gold', 'Vision', 'Objectifs', 'Survie']
    fig = go.Figure()
    for i, data in enumerate(data_list):
        safe_name = html.escape(str(names[i]))
        fig.add_trace(go.Scatterpolar(r=data, theta=categories, fill='toself', name=safe_name, line_color=colors[i], opacity=0.7, marker=dict(size=5)))
    fig.update_layout(
        polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#555', gridcolor='#444'), angularaxis=dict(linecolor='#555', gridcolor='#444', tickfont=dict(color='#eee'))),
        showlegend=True, legend=dict(font=dict(color='white'), orientation="h", y=-0.15, x=0.5, xanchor="center", bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=60, r=60, t=20, b=60), height=400
    )
    return fig

# --- API ---
def safe_request(url):
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200: return resp
        elif resp.status_code == 429: time.sleep(1); return None 
        return None
    except: return None

@st.cache_data(ttl=600)
def get_puuid(name, tag, region, api_key):
    return safe_request(f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={api_key}")

@st.cache_data(ttl=120)
def get_matches(puuid, region, api_key, q_id):
    return safe_request(f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue={q_id}&start=0&count=15&api_key={api_key}")

def fetch_match(m_id, region, api_key):
    r = safe_request(f"https://{region}.api.riotgames.com/lol/match/v5/matches/{m_id}?api_key={api_key}")
    return r.json() if r else {}

# --- MAIN LOOP ---
if submitted:
    def get_regions(r):
        if r in ["EUW1", "EUN1", "TR1", "RU"]: return "europe"
        elif r == "KR": return "asia"
        else: return "americas"

    if "#" not in riot_id_input:
        st.error("⚠️ Format: Name#TAG")
    else:
        parts = riot_id_input.split("#")
        name_raw, tag = parts[0].strip(), parts[1].strip()
        region = get_regions(region_select)
        q_id = QUEUE_MAP.get(queue_label, 420)
        
        with st.spinner(T["loading"]):
            try:
                r_acc = get_puuid(quote(name_raw), tag, region, API_KEY)
                if not r_acc: st.error(T["error_no_games"]); st.stop()
                puuid = r_acc.json().get("puuid")
                
                r_match = get_matches(puuid, region, API_KEY, q_id)
                if not r_match: st.warning(T['error_no_games']); st.stop()
                match_ids = r_match.json()
                if not match_ids: st.warning(T['error_no_games']); st.stop()
            except Exception as e:
                st.error(f"API Error: {e}"); st.stop()

            duo_data = {}
            target_name = riot_id_input
            data_lock = threading.Lock()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                future_to_match = {executor.submit(fetch_match, m, region, API_KEY): m for m in match_ids}
                for future in concurrent.futures.as_completed(future_to_match):
                    try:
                        data = future.result()
                        if not data or 'info' not in data: continue
                        info = data['info']
                        duration = info.get('gameDuration', 0)
                        if duration < 300: continue
                        duration_min = duration / 60.0
                        
                        parts = info.get('participants', [])
                        me = next((p for p in parts if p['puuid'] == puuid), None)
                        if not me: continue
                        target_name = me.get('riotIdGameName', target_name)
                        
                        def ext(p):
                            c = p.get('challenges', {})
                            return {
                                'kills': p.get('kills',0), 'deaths': p.get('deaths',0), 'assists': p.get('assists',0),
                                'dmg': p.get('totalDamageDealtToChampions',0), 'gold': p.get('goldEarned',0), 'vis': p.get('visionScore',0),
                                'obj': p.get('damageDealtToObjectives',0), 'towers': p.get('turretTakedowns',0),
                                'kp': c.get('killParticipation',0), 'solokills': c.get('soloKills',0),
                                'champ': p.get('championName','Unknown'), 'role': p.get('teamPosition','UNKNOWN'), 'win': p.get('win',False)
                            }
                        my_s = ext(me)
                        
                        with data_lock:
                            for p in parts:
                                if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                                    gid = f"{p.get('riotIdGameName')}#{p.get('riotIdTagLine')}"
                                    if gid not in duo_data:
                                        duo_data[gid] = {'name': p.get('riotIdGameName'), 'games': 0, 'wins': 0, 'champs': [], 'roles': [], 's_duo': [], 's_me': []}
                                    d = duo_data[gid]
                                    d['games'] += 1
                                    if p['win']: d['wins'] += 1
                                    d['champs'].append(p.get('championName'))
                                    d['roles'].append(p.get('teamPosition'))
                                    
                                    duo_s = ext(p)
                                    for s, norm in [(duo_s, d['s_duo']), (my_s, d['s_me'])]:
                                        n = s.copy()
                                        n['dmg_min'] = s['dmg'] / duration_min
                                        n['gold_min'] = s['gold'] / duration_min
                                        n['vis_min'] = s['vis'] / duration_min
                                        norm.append(n)
                    except: pass

            st.markdown("<div id='result'></div>", unsafe_allow_html=True)
            best_duo = None
            max_g = 0
            for k, v in duo_data.items():
                if v['games'] > max_g: max_g = v['games']; best_duo = v
            
            if best_duo and max_g >= 2:
                g = best_duo['games']
                duo_name = html.escape(best_duo['name'])
                t_safe = html.escape(target_name)
                wr = int((best_duo['wins']/g)*100)
                
                try: r_duo = Counter(best_duo['roles']).most_common(1)[0][0]
                except: r_duo = "UNKNOWN"
                try: r_me = Counter([x['role'] for x in best_duo['s_me']]).most_common(1)[0][0]
                except: r_me = "UNKNOWN"
                
                ch_duo = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                ch_me = [c[0] for c in Counter([x['champ'] for x in best_duo['s_me']]).most_common(3)]
                
                def avg(l): return {k: sum(d[k] for d in l)/len(l) for k in l[0] if isinstance(l[0][k], (int,float))} if l else {}
                avg_duo = avg(best_duo['s_duo'])
                avg_me = avg(best_duo['s_me'])
                
                def ckda(s): return round((s.get('kills',0)+s.get('assists',0))/max(1,s.get('deaths',1)), 2)
                avg_duo['kda'] = ckda(avg_duo)
                avg_me['kda'] = ckda(avg_me)

                # --- VERDICT LOGIC ---
                def score(s, r):
                    sc = min(5, s['kda']) + (s['kp']*4) + min(3, (s['vis_min']/(2.0 if r=="UTILITY" else 1.0))*2)
                    sc += min(4, s['dmg_min']/700) if r!="UTILITY" else 0
                    return sc + min(4, (s['obj']/5000) + (s['towers']*0.5))
                
                s_me = score(avg_me, r_me)
                s_duo = score(avg_duo, r_duo)
                ratio = s_me / max(0.1, s_duo)

                diff_kda = (avg_me['kda'] - avg_duo['kda']) / 1.5
                diff_dmg = (avg_me['dmg_min'] - avg_duo['dmg_min']) / 400
                diff_vis = (avg_me['vis_min'] - avg_duo['vis_min']) / 0.8
                diff_obj = (avg_me['obj'] - avg_duo['obj']) / 3000
                
                title, color, sub = T["v_solid"], "#00ff99", safe_format(T["s_solid"], t_safe, duo_name)
                
                if ratio > 1.15:
                    max_diff = max(diff_kda, diff_dmg, diff_vis, diff_obj)
                    if max_diff == diff_kda: title, color, sub = T["v_survivor"], "#FFD700", safe_format(T["s_survivor"], t_safe, duo_name)
                    elif max_diff == diff_vis: title, color, sub = T["v_tactician"], "#00BFFF", safe_format(T["s_tactician"], t_safe, duo_name)
                    elif max_diff == diff_obj: title, color, sub = T["v_breacher"], "#FFA500", safe_format(T["s_breacher"], t_safe, duo_name)
                    else: title, color, sub = T["v_hyper"], "#ff0055", safe_format(T["s_hyper"], t_safe, duo_name)
                elif ratio < 0.85:
                    min_diff = min(diff_kda, diff_dmg, diff_vis)
                    if min_diff == diff_kda: title, color, sub = T["v_feeder"], "#ff4444", safe_format(T["s_feeder"], t_safe, duo_name)
                    elif min_diff == diff_dmg: title, color, sub = T["v_passenger"], "#888888", safe_format(T["s_passenger"], t_safe, duo_name)
                    else: title, color, sub = T["v_struggle"], "#ff4444", safe_format(T["s_struggle"], t_safe, duo_name)

                components.html(f"<script>window.parent.document.querySelector('.verdict-box').scrollIntoView({{behavior:'smooth'}});</script>", height=0)

                st.markdown(f"""
                <div class="verdict-box" style="border-color:{color}">
                    <div style="font-size:14px; font-weight:700; color:#aaa; margin-bottom:5px; text-transform:uppercase;">{safe_format(T['lbl_duo_detected'], target=t_safe, duo=duo_name)}</div>
                    <div style="font-size:45px; font-weight:900; color:{color}; margin-bottom:10px;">{title}</div>
                    <div style="font-size:18px; color:#eee; font-style:italic;">"{sub}"</div>
                    <div style="margin-top:15px; color:#888; font-weight:600;">{g} Games • {wr}% Winrate</div>
                </div>
                """, unsafe_allow_html=True)

                def norm(val, max_v): return min(100, (val / max_v) * 100)
                d_me = [norm(avg_me.get('dmg_min',0), 1000), norm(avg_me.get('gold_min',0), 600), norm(avg_me.get('vis_min',0), 2.5), norm(avg_me.get('obj',0), 8000), norm(avg_me.get('kda',0), 5)]
                d_duo = [norm(avg_duo.get('dmg_min',0), 1000), norm(avg_duo.get('gold_min',0), 600), norm(avg_duo.get('vis_min',0), 2.5), norm(avg_duo.get('obj',0), 8000), norm(avg_duo.get('kda',0), 5)]
                st.plotly_chart(create_radar([d_me, d_duo], [t_safe, duo_name], ['#00c6ff', '#ff0055']), use_container_width=True, config={'displayModeBar': False})
                
                col1, col2 = st.columns(2, gap="large")
                bdg_me = determine_playstyle(avg_me, r_me, T)
                bdg_duo = determine_playstyle(avg_duo, r_duo, T)
                
                def d_card(n, c, s, b, r_i, diff, clr):
                    bdg_h = "".join([f"<span class='badge {x[1]}'>{x[0]}</span>" for x in b])
                    ch_h = "".join([f"<img src='{get_champ_url(x)}' style='width:55px; border-radius:50%; border:2px solid #333; margin:4px;'>" for x in c])
                    
                    def sl(l, v, d_v, p=False, k=False):
                        val_str = f"{int(v*100)}%" if p else (f"{v:.2f}" if k else (f"{int(v/1000)}k" if v>1000 else f"{int(v)}"))
                        
                        # --- MODIFICATION: CALCUL POURCENTAGE ---
                        if p:
                            pct_val = d_v # Pour KP c'est déjà en %
                        else:
                            other = v - d_v
                            if abs(other) < 0.01: pct_val = 100 if v > other else 0
                            else: pct_val = (d_v / abs(other)) * 100
                            
                        if pct_val > 0: dh = f"<span class='stat-diff pos'>+{int(pct_val)}%</span>"
                        elif pct_val < 0: dh = f"<span class='stat-diff neg'>{int(pct_val)}%</span>"
                        else: dh = f"<span class='stat-diff neutral'>=</span>"
                        
                        return f"""<div class="stat-item"><div class="stat-val-container"><div class="stat-val">{val_str}</div>{dh}</div><div class="stat-lbl">{l}</div></div>"""

                    gr = f"""<div class="stat-grid">
                        {sl("KDA", s.get('kda',0), diff.get('kda',0), k=True)}
                        {sl("KP", s.get('kp',0), diff.get('kp',0)*100, p=True)}
                        {sl("DPM", s.get('dmg_min',0), diff.get('dmg_min',0))}
                        {sl("VIS/M", s.get('vis_min',0), diff.get('vis_min',0))}
                        {sl("OBJ", s.get('obj',0), diff.get('obj',0))}
                        {sl("GOLD/M", s.get('gold_min',0), diff.get('gold_min',0))}
                    </div>"""
                    st.markdown(f"""<div class="player-card" style="border-top: 4px solid {clr};"><div class="player-name">{n}</div><div class="player-sub">{r_i}</div><div style="margin:10px 0;">{bdg_h}</div><div style="margin-bottom:15px;">{ch_h}</div>{gr}</div>""", unsafe_allow_html=True)

                diff_m = {k: avg_me.get(k,0)-avg_duo.get(k,0) for k in avg_me if isinstance(avg_me[k],(int,float))}
                diff_d = {k: avg_duo.get(k,0)-avg_me.get(k,0) for k in avg_duo if isinstance(avg_duo[k],(int,float))}

                with col1: d_card(t_safe, ch_me, avg_me, bdg_me, ROLE_ICONS.get(r_me,"UNK"), diff_m, '#00c6ff')
                with col2: d_card(duo_name, ch_duo, avg_duo, bdg_duo, ROLE_ICONS.get(r_duo,"UNK"), diff_d, '#ff0055')

            else:
                st.markdown(f"""<div class="verdict-box" style="border-color:#888;"><div style="font-size:32px; font-weight:900; color:#888;">{T["solo"]}</div><div style="font-size:16px; color:#aaa;">{T["solo_sub"]}</div></div>""", unsafe_allow_html=True)
