import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import plotly.graph_objects as go
from urllib.parse import quote
from collections import Counter
import concurrent.futures
import threading

# --- 1. CONFIGURATION & NETTOYAGE ---
st.set_page_config(page_title="LoL Duo Analyst", layout="wide", initial_sidebar_state="collapsed")

# --- CSS HIDE STREAMLIT BRANDING ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            [data-testid="stToolbar"] {visibility: hidden;}
            .stDeployButton {display:none;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- API KEY ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ Configuration requise : Ajoute ta clé API dans les secrets.")
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

# --- MAP DRAPEAUX ---
LANG_MAP = {"🇫🇷 FR": "FR", "🇺🇸 EN": "EN", "🇪🇸 ES": "ES", "🇰🇷 KR": "KR"}

# --- TRADUCTIONS ---
TRANSLATIONS = {
    "FR": {
        "title": "LoL Duo Analyst", "btn_scan": "LANCER L'ANALYSE", "placeholder": "Exemple: Kameto#EUW", "label_id": "Riot ID", "dpm_btn": "🔗 Voir sur dpm.lol",
        "v_hyper": "MVP TOTAL", "s_hyper": "{target} porte {duo} sur ses épaules (1v9)",
        "v_tactician": "MASTERMIND", "s_tactician": "{target} gagne la game pour {duo} grâce à la macro",
        "v_fighter": "GLADIATEUR", "s_fighter": "{target} fait les dégâts, {duo} prend les objectifs",
        "v_solid": "DUO FUSIONNEL", "s_solid": "Synergie parfaite entre {target} et {duo}",
        "v_passive": "EN RETRAIT", "s_passive": "{target} joue safe et laisse {duo} mener le jeu",
        "v_struggle": "EN DIFFICULTÉ", "s_struggle": "{target} peine à suivre le rythme imposé par {duo}",
        "solo": "LOUP SOLITAIRE", "solo_sub": "Aucun duo récurrent détecté sur 20 parties.",
        "loading": "Analyse tactique en cours...",
        "role_hyper": "CARRY", "role_lead": "MENEUR", "role_equal": "PARTENAIRE", "role_supp": "SOUTIEN", "role_gap": "ROOKIE",
        "q_surv": "Injouable (KDA)", "q_dmg": "Gros Dégâts", "q_obj": "Destructeur", "q_vis": "Contrôle Map", "q_bal": "Polyvalent", "q_supp": "Excellent Support",
        "f_feed": "Meurt trop souvent", "f_afk": "Dégâts faibles", "f_no_obj": "Ignore objectifs", "f_blind": "Vision faible", "f_farm": "Farm faible", "f_ok": "Solide",
        "stats": "STATS", "combat": "COMBAT", "eco": "ÉCONOMIE", "vision": "VISION & MAP",
        "error_no_games": "Aucune partie trouvée.", "error_hint": "Vérifie la région ou le mode de jeu.",
        "traffic_jam": "🚦 TROP DE MONDE ! Les serveurs Riot surchauffent. Réessaie dans 30 secondes."
    },
    "EN": {
        "title": "LoL Duo Analyst", "btn_scan": "START ANALYSIS", "placeholder": "Example: Faker#KR1", "label_id": "Riot ID", "dpm_btn": "🔗 Check dpm.lol",
        "v_hyper": "TOTAL MVP", "s_hyper": "{target} is hard carrying {duo}",
        "v_tactician": "MASTERMIND", "s_tactician": "{target} wins for {duo} via macro",
        "v_fighter": "GLADIATOR", "s_fighter": "{target} deals dmg, {duo} takes objs",
        "v_solid": "PERFECT DUO", "s_solid": "Perfect synergy between {target} and {duo}",
        "v_passive": "PASSIVE", "s_passive": "{target} plays safe, {duo} leads",
        "v_struggle": "STRUGGLING", "s_struggle": "{target} can't keep up with {duo}",
        "solo": "SOLO PLAYER", "solo_sub": "No recurring partner found.",
        "loading": "Analyzing...", "role_hyper": "CARRY", "role_lead": "LEADER", "role_equal": "PARTNER", "role_supp": "SUPPORT", "role_gap": "ROOKIE",
        "q_surv": "Unkillable", "q_dmg": "Heavy Hitter", "q_obj": "Destroyer", "q_vis": "Map Control", "q_bal": "Balanced", "q_supp": "Great Support",
        "f_feed": "Too fragile", "f_afk": "Low Dmg", "f_no_obj": "No Objs", "f_blind": "Blind", "f_farm": "Low Farm", "f_ok": "Solid",
        "stats": "STATS", "combat": "COMBAT", "eco": "ECONOMY", "vision": "VISION",
        "error_no_games": "No games found.", "error_hint": "Check Region.",
        "traffic_jam": "🚦 HIGH TRAFFIC! Riot servers are busy. Please retry in 30 seconds."
    },
    "ES": {"title":"Analista LoL","btn_scan":"ANALIZAR","placeholder":"Ejemplo: Ibai#EUW","label_id":"Riot ID","dpm_btn":"Ver dpm.lol","v_hyper":"MVP TOTAL","s_hyper":"Domina a {duo}","v_tactician":"ESTRATEGA","s_tactician":"Macro para {duo}","v_fighter":"GLADIADOR","s_fighter":"Daño","v_solid":"DUO SOLIDO","s_solid":"Sinergia con {duo}","v_passive":"PASIVO","s_passive":"Seguro","v_struggle":"DIFICULTAD","s_struggle":"Sufre vs {duo}","solo":"SOLO","solo_sub":"Sin duo","loading":"Cargando...","role_hyper":"CARRY","role_lead":"LIDER","role_equal":"SOCIO","role_supp":"APOYO","role_gap":"NOVATO","q_surv":"Inmortal","q_dmg":"Daño","q_obj":"Torres","q_vis":"Vision","q_bal":"Balance","q_supp":"Support","f_feed":"Muere","f_afk":"Poco daño","f_no_obj":"Sin obj","f_blind":"Ciego","f_farm":"Farm","f_ok":"Bien","stats":"STATS","combat":"COMBATE","eco":"ECONOMIA","vision":"VISION","error_no_games":"Error","error_hint":"Region?", "traffic_jam": "🚦 Mucho trafico! Reintenta pronto."},
    "KR": {"title":"LoL 듀오 분석","btn_scan":"분석 시작","placeholder":"예: Hide on bush#KR1","label_id":"Riot ID","dpm_btn":"dpm.lol 확인","v_hyper":"하드 캐리","s_hyper":"{target} > {duo}","v_tactician":"전략가","s_tactician":"운영","v_fighter":"전투광","s_fighter":"딜","v_solid":"완벽 듀오","s_solid":"{target} & {duo}","v_passive":"버스","s_passive":"안전","v_struggle":"고전","s_struggle":"역부족","solo":"솔로","solo_sub":"듀오 없음","loading":"분석 중...","role_hyper":"캐리","role_lead":"리더","role_equal":"파트너","role_supp":"서포터","role_gap":"신입","q_surv":"생존","q_dmg":"딜량","q_obj":"철거","q_vis":"시야","q_bal":"밸런스","q_supp":"서폿","f_feed":"데스","f_afk":"딜부족","f_no_obj":"운영부족","f_blind":"시야부족","f_farm":"CS","f_ok":"굿","stats":"통계","combat":"전투","eco":"경제","vision":"시야","error_no_games":"없음","error_hint":"지역?", "traffic_jam": "🚦 트래픽 초과! 잠시 후 다시 시도하세요."}
}

# --- CSS DESIGN PRO ---
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    @font-face {{ font-family: 'Noto Color Emoji'; src: local('Noto Color Emoji'), default; }}
    
    .stApp {{
        background-image: url("{BACKGROUND_IMAGE_URL}");
        background-size: 150px; background-repeat: repeat; background-attachment: fixed;
    }}
    
    /* CONTAINER PRINCIPAL OPTIMISÉ */
    .block-container {{
        max-width: 1400px !important; 
        padding-top: 1rem !important; 
        padding-bottom: 3rem !important;
        background: rgba(12, 12, 12, 0.96); backdrop-filter: blur(20px);
        border-radius: 0px; border-bottom: 2px solid #333; box-shadow: 0 20px 60px rgba(0,0,0,0.95);
        margin-top: 0px !important;
    }}

    .main-title {{
        font-size: 48px; font-weight: 900; text-align: center; margin-bottom: 25px; margin-top: 20px;
        text-transform: uppercase; letter-spacing: -1px;
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 15px rgba(0, 114, 255, 0.4));
    }}
    
    /* BOUTON SCAN - LE SEUL QUI DOIT RESSORTIR */
    .stButton > button {{
        width: 100%; height: 60px; 
        background: linear-gradient(135deg, #ff0055 0%, #ff2244 100%);
        color: white !important; font-size: 20px; font-weight: 800; 
        border: none; border-radius: 12px; letter-spacing: 1px;
        text-transform: uppercase; transition: all 0.2s;
        box-shadow: 0 4px 15px rgba(255, 0, 85, 0.3);
    }}
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(255,0,85,0.5); }}
    .stButton > button:active {{ transform: scale(0.98); }}

    /* BOUTON DPM DISCRET */
    .dpm-button-small {{
        display: flex; align-items: center; justify-content: center;
        background-color: rgba(37, 99, 235, 0.15); color: #60a5fa !important;
        height: 25px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 11px;
        border: 1px solid rgba(37, 99, 235, 0.4); width: fit-content; padding: 0 10px;
    }}
    .dpm-button-small:hover {{ background-color: #2563eb; color: white !important; }}
    
    /* LABELS & INPUTS */
    .input-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }}
    .input-label {{ font-size: 13px; font-weight: 700; color: #aaa; text-transform: uppercase; letter-spacing: 0.5px; }}
    .stTextInput > label {{ display: none; }}
    .stForm > div[data-testid="stFormEnterToSubmit"] {{ display: none; }}
    
    /* CARTE JOUEUR */
    .player-panel {{ 
        background: rgba(255, 255, 255, 0.03); border-radius: 16px; padding: 20px; height: 100%; 
        border: 1px solid rgba(255,255,255,0.06); margin-bottom: 10px; 
    }}
    .player-name {{ font-size: 26px; font-weight: 900; color: white; text-align: center; margin-bottom: 2px; text-shadow: 0 2px 10px rgba(0,0,0,0.5); }}
    
    .role-badge {{ font-size: 12px; font-weight: 700; color: #888; text-align: center; margin-bottom: 12px; letter-spacing: 1px; opacity: 0.9; }}
    
    .player-role {{ 
        font-size: 14px; font-weight: 800; text-align: center; text-transform: uppercase; 
        letter-spacing: 1px; margin-bottom: 15px; padding: 6px; border-radius: 6px; 
        background: rgba(0,0,0,0.3);
    }}
    
    /* COULEURS DES ROLES */
    .color-gold {{ color: #FFD700; border: 1px solid rgba(255, 215, 0, 0.3); }} 
    .color-blue {{ color: #00BFFF; border: 1px solid rgba(0, 191, 255, 0.3); }} 
    .color-green {{ color: #00ff99; border: 1px solid rgba(0, 255, 153, 0.3); }} 
    .color-orange {{ color: #FFA500; border: 1px solid rgba(255, 165, 0, 0.3); }} 
    .color-red {{ color: #ff4444; border: 1px solid rgba(255, 68, 68, 0.3); }}
    
    /* STATS ROWS */
    .stat-row {{ display: flex; justify-content: space-between; align-items: center; padding: 9px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }}
    .stat-label {{ font-size: 12px; color: #999; font-weight: 600; }}
    .stat-value {{ font-size: 16px; color: white; font-weight: 700; font-family: 'Consolas', monospace; }}
    .stat-diff {{ font-size: 11px; font-weight: 600; margin-left: 6px; padding: 1px 5px; border-radius: 3px; }}
    .pos {{ color: #00ff99; background: rgba(0,255,153,0.1); }} 
    .neg {{ color: #ff4444; background: rgba(255,68,68,0.1); }} 
    .neutral {{ color: #666; }}
    
    /* FEEDBACK BADGES */
    .feedback-row {{ display: flex; gap: 8px; justify-content: center; margin-bottom: 15px; flex-wrap: wrap; }}
    .fb-box {{ padding: 5px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase; white-space: nowrap; }}
    .fb-good {{ background: rgba(0, 255, 153, 0.1); color: #00ff99; border: 1px solid rgba(0, 255, 153, 0.3); }}
    .fb-bad {{ background: rgba(255, 68, 68, 0.1); color: #ff6666; border: 1px solid rgba(255, 68, 68, 0.3); }}
    
    .verdict-banner {{ text-align: center; padding: 25px; margin-bottom: 30px; border-radius: 16px; background: rgba(0,0,0,0.4); border: 2px solid #333; box-shadow: inset 0 0 50px rgba(0,0,0,0.3); }}
    .champ-img {{ width: 45px; height: 45px; border-radius: 50%; border: 2px solid #444; margin: 0 3px; transition: 0.2s; }}
    .champ-img:hover {{ transform: scale(1.1); border-color: white; }}
    
    p, label {{ color: #eee !important; font-weight: 600; font-size: 13px; }}
    </style>
    """, unsafe_allow_html=True
)

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
        <div class="input-row">
            <span class="input-label">{T['label_id']}</span>
            <a href="https://dpm.lol" target="_blank" class="dpm-button-small">{T['dpm_btn']}</a>
        </div>""", unsafe_allow_html=True)
        riot_id_input = st.text_input("HiddenLabel", placeholder=T["placeholder"], label_visibility="collapsed")
    with c2:
        st.markdown(f"<div style='margin-bottom:5px'><span class='input-label'>Region</span></div>", unsafe_allow_html=True)
        region_select = st.selectbox("Region", ["EUW1", "NA1", "KR", "EUN1", "TR1"], label_visibility="collapsed")
    with c3:
        st.markdown(f"<div style='margin-bottom:5px'><span class='input-label'>Mode</span></div>", unsafe_allow_html=True)
        queue_label = st.selectbox("Mode", list(QUEUE_MAP.keys()), label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button(T["btn_scan"])

# --- FONCTIONS ---
def get_champ_url(champ_name):
    if not champ_name: return "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Poro_0.jpg"
    clean = champ_name.replace(" ", "").replace("'", "").replace(".", "")
    mapping = {"wukong": "MonkeyKing", "renataglasc": "Renata", "nunu&willump": "Nunu", "kogmaw": "KogMaw", "reksai": "RekSai", "drmundo": "DrMundo", "belveth": "Belveth"}
    return f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/img/champion/{mapping.get(clean.lower(), clean)}.png"

def safe_format(text, target, duo):
    try: return text.format(target=target, duo=duo)
    except: return text

def analyze_qualities(stats, role, lang_dict):
    qualities, flaws = [], []
    
    if stats['kda'] > 3.5: qualities.append(lang_dict.get("q_surv", "High KDA"))
    if stats['obj'] > 5000: qualities.append(lang_dict.get("q_obj", "Obj Dmg"))
    if stats['dpm'] > 750: qualities.append(lang_dict.get("q_dmg", "High Dmg"))
    if stats['vis'] > 35: qualities.append(lang_dict.get("q_vis", "Vision"))
    
    # Calcul maillon faible
    scores = {
        'kda': stats['kda'] / 3.0,
        'vis': stats['vis'] / 25.0,
    }
    if role != "UTILITY":
        scores['dpm'] = stats['dpm'] / 500.0
        scores['gold'] = stats['gold'] / 400.0
    
    if role == "JUNGLE": scores['obj'] = stats['obj'] / 4000.0
    elif role != "UTILITY": scores['obj'] = stats['obj'] / 2500.0

    worst_stat = min(scores, key=scores.get) if scores else 'kda'
    
    flaws_map = {
        'kda': lang_dict.get("f_feed", "Feed"),
        'dpm': lang_dict.get("f_afk", "Low Dmg"),
        'vis': lang_dict.get("f_blind", "No Vis"),
        'obj': lang_dict.get("f_no_obj", "No Obj"),
        'gold': lang_dict.get("f_farm", "Low Farm")
    }
    
    flaw = flaws_map.get(worst_stat, "Ok")
    q = qualities[0] if qualities else lang_dict.get("q_bal", "Balanced")
    if role == "UTILITY" and q == lang_dict.get("q_bal"): q = lang_dict.get("q_supp", "Support")
    return q, flaw

def render_stat_row(label, val, diff, unit=""):
    if diff > 0: diff_html = f"<span class='stat-diff pos'>+{round(diff, 1)}{unit}</span>"
    elif diff < 0: diff_html = f"<span class='stat-diff neg'>{round(diff, 1)}{unit}</span>"
    else: diff_html = f"<span class='stat-diff neutral'>=</span>"
    val_display = f"{val}{unit}"
    if isinstance(val, int) and val > 1000: val_display = f"{val/1000:.1f}k"
    st.markdown(f"""<div class="stat-row"><div class="stat-label">{label}</div><div style="display:flex; align-items:center;"><div class="stat-value">{val_display}</div>{diff_html}</div></div>""", unsafe_allow_html=True)

# --- API ---
@st.cache_data(ttl=600)
def get_puuid_from_api(name, tag, region, api_key):
    url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={api_key}"
    return requests.get(url)

@st.cache_data(ttl=120)
def get_matches_from_api(puuid, region, api_key, queue_id):
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue={queue_id}&start=0&count=20&api_key={api_key}"
    return requests.get(url)

def fetch_match_detail(match_id, region, api_key):
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={api_key}"
    return requests.get(url).json()

# --- APP ---
if submitted:
    def get_regions(region_code):
        if region_code in ["EUW1", "EUN1", "TR1", "RU"]: return "europe"
        elif region_code == "KR": return "asia"
        else: return "americas"

    if not riot_id_input or "#" not in riot_id_input:
        st.error("⚠️ Format invalide")
    else:
        name_raw, tag = riot_id_input.split("#")
        name_encoded = quote(name_raw)
        region = get_regions(region_select)
        q_id = QUEUE_MAP[queue_label]
        
        with st.spinner(T["loading"]):
            try:
                resp_acc = get_puuid_from_api(name_encoded, tag, region, API_KEY)
                if resp_acc.status_code == 403:
                    st.error("⛔ API KEY EXPIRED (403). Regenerate it at developer.riotgames.com")
                    st.stop()
                elif resp_acc.status_code == 429:
                    st.warning(T.get("traffic_jam", "🚦 Traffic Jam! Wait 2 min."))
                    st.stop()
                elif resp_acc.status_code != 200:
                    st.error(f"Error {resp_acc.status_code}")
                    st.stop()
                puuid = resp_acc.json().get("puuid")

                resp_matches = get_matches_from_api(puuid, region, API_KEY, q_id)
                match_ids = resp_matches.json()
                if not match_ids:
                    st.warning(T['error_no_games'])
                    st.stop()
            except Exception as e:
                st.error(f"API Error: {e}")
                st.stop()

            # ANALYSIS
            duo_data = {} 
            target_name = riot_id_input 
            data_lock = threading.Lock()
            
            # LIMITATION THREADS POUR ÉVITER LE CRASH CPU SUR TIKTOK
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_match = {executor.submit(fetch_match_detail, m_id, region, API_KEY): m_id for m_id in match_ids}
                for future in concurrent.futures.as_completed(future_to_match):
                    try:
                        data = future.result()
                        if 'info' not in data: continue
                        duration_min = data['info']['gameDuration'] / 60
                        if duration_min < 5: continue 
                        participants = data['info']['participants']
                        me = next((p for p in participants if p['puuid'] == puuid), None)
                        if me:
                            target_name = me.get('riotIdGameName', name_raw)
                            def get_stats(p):
                                return {
                                    'kda': (p['kills'] + p['assists']) / max(1, p['deaths']),
                                    'dpm': p['totalDamageDealtToChampions'] / duration_min,
                                    'gold': p['goldEarned'] / duration_min,
                                    'vis': p['visionScore'],
                                    'obj': p.get('damageDealtToObjectives', 0),
                                    'towers': p.get('challenges', {}).get('turretTakedowns', 0),
                                    'champ': p['championName']
                                }
                            my_s = get_stats(me)
                            with data_lock:
                                for p in participants:
                                    if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                                        full_id = f"{p.get('riotIdGameName')}#{p.get('riotIdTagLine')}"
                                        if full_id not in duo_data:
                                            duo_data[full_id] = {
                                                'name': p.get('riotIdGameName'), 'games': 0, 'wins': 0,
                                                'stats': {'kda':0, 'dpm':0, 'gold':0, 'vis':0, 'obj':0, 'towers':0},
                                                'my_stats_vs': {'kda':0, 'dpm':0, 'gold':0, 'vis':0, 'obj':0, 'towers':0},
                                                'champs': [], 'my_champs': [], 'roles': [], 'my_roles': []    
                                            }
                                        d = duo_data[full_id]
                                        d['games'] += 1
                                        if p['win']: d['wins'] += 1
                                        d['champs'].append(p['championName'])
                                        d['my_champs'].append(my_s['champ'])
                                        d['roles'].append(p.get('teamPosition', 'UNKNOWN'))
                                        d['my_roles'].append(me.get('teamPosition', 'UNKNOWN'))
                                        duo_s = get_stats(p)
                                        for k in d['stats']:
                                            d['stats'][k] += duo_s[k]
                                            d['my_stats_vs'][k] += my_s[k]
                    except: pass 

            st.markdown("<div id='result'></div>", unsafe_allow_html=True)
            best_duo = None
            max_g = 0
            for k, v in duo_data.items():
                if v['games'] > max_g:
                    max_g = v['games']
                    best_duo = v
            
            if best_duo and max_g >= 2:
                g = best_duo['games']
                duo_name = best_duo['name']
                
                try: main_role_me = Counter(best_duo['my_roles']).most_common(1)[0][0]
                except: main_role_me = "UNKNOWN"
                try: main_role_duo = Counter(best_duo['roles']).most_common(1)[0][0]
                except: main_role_duo = "UNKNOWN"
                
                def avg_f(d, key): return round(d[key] / g, 2)
                def avg(d, key): return int(d[key] / g)
                
                s_me = best_duo['my_stats_vs']
                s_duo = best_duo['stats']
                
                def calc_score(s, role):
                    kda = s['kda'] / g
                    dpm = s['dpm'] / g
                    obj = s['obj'] / g 
                    vis = s['vis'] / g
                    obj_factor = 0.15 if role == "JUNGLE" else 0.35 
                    score = (kda * 150) + (dpm * 0.4) + (obj * obj_factor) + (vis * 15)
                    return score

                score_me = calc_score(s_me, main_role_me)
                score_duo = calc_score(s_duo, main_role_duo)
                ratio = score_me / max(1, score_duo)
                
                if ratio > 1.35: state = "BOOSTER_HARD"
                elif ratio > 1.1: state = "BOOSTER_SOFT"
                elif ratio < 0.75: state = "BOOSTED_HARD"
                elif ratio < 0.9: state = "BOOSTED_SOFT"
                else: state = "EQUAL"

                winrate = int((best_duo['wins']/g)*100)

                header_color, title_text, sub_text = "#00ff99", T.get("v_solid", "SOLID"), T.get("s_solid", "Equal")
                role_me_key, role_me_color = "role_equal", "color-green"
                role_duo_key, role_duo_color = "role_equal", "color-green"

                if state == "BOOSTED_HARD":
                    header_color, title_text = "#ff4444", T.get("v_struggle")
                    sub_text = safe_format(T.get("s_struggle", ""), target_name, duo_name)
                    role_me_key, role_me_color = "role_gap", "color-red"
                    role_duo_key, role_duo_color = "role_hyper", "color-gold"
                elif state == "BOOSTED_SOFT":
                    header_color, title_text = "#FFA500", T.get("v_passive")
                    sub_text = safe_format(T.get("s_passive", ""), target_name, duo_name)
                    role_me_key, role_me_color = "role_supp", "color-orange"
                    role_duo_key, role_duo_color = "role_lead", "color-blue"
                elif state == "BOOSTER_HARD":
                    header_color, title_text = "#FFD700", T.get("v_hyper")
                    sub_text = safe_format(T.get("s_hyper", ""), target_name, duo_name)
                    role_me_key, role_me_color = "role_hyper", "color-gold"
                    role_duo_key, role_duo_color = "role_gap", "color-red"
                elif state == "BOOSTER_SOFT":
                    header_color, title_text = "#00BFFF", T.get("v_tactician")
                    sub_text = safe_format(T.get("s_tactician", ""), target_name, duo_name)
                    role_me_key, role_me_color = "role_lead", "color-blue"
                    role_duo_key, role_duo_color = "role_supp", "color-orange"

                components.html(f"<script>window.parent.document.querySelector('.verdict-banner').scrollIntoView({{behavior:'smooth'}});</script>", height=0)

                st.markdown(f"""
                <div class="verdict-banner" style="border-color:{header_color}">
                    <div style="font-size:42px; font-weight:900; color:{header_color}; margin-bottom:10px;">{title_text}</div>
                    <div style="font-size:18px; color:#ddd;">{sub_text}</div>
                    <div style="margin-top:15px; font-size:14px; color:#888;">{g} Games • {winrate}% Winrate</div>
                </div>""", unsafe_allow_html=True)

                # DATA GRAPH
                def norm(val, max_v): return min(100, (val / max_v) * 100)
                data_me_norm = [norm(avg_f(s_me, 'dpm'), 1000), norm(avg_f(
