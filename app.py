import streamlit as st
import streamlit.components.v1 as components
import requests
import time
from urllib.parse import quote
from collections import Counter
import concurrent.futures
import threading

# --- CONFIGURATION ---
st.set_page_config(page_title="LoL Duo Analyst V53", layout="wide")

# --- API KEY ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ API Key missing. Add RIOT_API_KEY to Streamlit secrets.")
    st.stop()

# --- ASSETS ---
BACKGROUND_IMAGE_URL = "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123"
DD_VERSION = "13.24.1"

# --- QUEUE MAP ---
QUEUE_MAP = {
    "Ranked Solo/Duo": 420,
    "Ranked Flex": 440,
    "Draft Normal": 400,
    "Quickplay": 490,
    "ARAM": 450,
    "Arena": 1700
}

# --- AUTO-UPDATE VERSION ---
@st.cache_data(ttl=3600)
def get_dd_version():
    try: return requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
    except: return "14.23.1"

DD_VERSION = get_dd_version()

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
        "error_no_games": "Aucune partie trouvée.", "error_hint": "Vérifie la région ou le mode de jeu."
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
        "error_no_games": "No games found.", "error_hint": "Check Region."
    },
    "ES": {"title":"Analista LoL","btn_scan":"ANALIZAR","placeholder":"Ejemplo: Ibai#EUW","label_id":"Riot ID","dpm_btn":"Ver dpm.lol","v_hyper":"MVP TOTAL","s_hyper":"Domina a {duo}","v_tactician":"ESTRATEGA","s_tactician":"Macro para {duo}","v_fighter":"GLADIADOR","s_fighter":"Daño","v_solid":"DUO SOLIDO","s_solid":"Sinergia con {duo}","v_passive":"PASIVO","s_passive":"Seguro","v_struggle":"DIFICULTAD","s_struggle":"Sufre vs {duo}","solo":"SOLO","solo_sub":"Sin duo","loading":"Cargando...","role_hyper":"CARRY","role_lead":"LIDER","role_equal":"SOCIO","role_supp":"APOYO","role_gap":"NOVATO","q_surv":"Inmortal","q_dmg":"Daño","q_obj":"Torres","q_vis":"Vision","q_bal":"Balance","q_supp":"Support","f_feed":"Muere","f_afk":"Poco daño","f_no_obj":"Sin obj","f_blind":"Ciego","f_farm":"Farm","f_ok":"Bien","stats":"STATS","combat":"COMBATE","eco":"ECONOMIA","vision":"VISION","error_no_games":"Error","error_hint":"Region?"},
    "KR": {"title":"LoL 듀오 분석","btn_scan":"분석 시작","placeholder":"예: Hide on bush#KR1","label_id":"Riot ID","dpm_btn":"dpm.lol 확인","v_hyper":"하드 캐리","s_hyper":"{target} > {duo}","v_tactician":"전략가","s_tactician":"운영","v_fighter":"전투광","s_fighter":"딜","v_solid":"완벽 듀오","s_solid":"{target} & {duo}","v_passive":"버스","s_passive":"안전","v_struggle":"고전","s_struggle":"역부족","solo":"솔로","solo_sub":"듀오 없음","loading":"분석 중...","role_hyper":"캐리","role_lead":"리더","role_equal":"파트너","role_supp":"서포터","role_gap":"신입","q_surv":"생존","q_dmg":"딜량","q_obj":"철거","q_vis":"시야","q_bal":"밸런스","q_supp":"서폿","f_feed":"데스","f_afk":"딜부족","f_no_obj":"운영부족","f_blind":"시야부족","f_farm":"CS","f_ok":"굿","stats":"통계","combat":"전투","eco":"경제","vision":"시야","error_no_games":"없음","error_hint":"지역?"}
}

# --- MAP DRAPEAUX ---
LANG_MAP = {"🇫🇷 FR": "FR", "🇺🇸 EN": "EN", "🇪🇸 ES": "ES", "🇰🇷 KR": "KR"}

# --- ROLES MAPPING ---
ROLE_ICONS = {"TOP": "🛡️ TOP", "JUNGLE": "🌲 JUNGLE", "MIDDLE": "🧙 MID", "BOTTOM": "🏹 ADC", "UTILITY": "🩹 SUPP", "UNKNOWN": "❓ FILL"}

# --- CSS STYLES ---
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    @font-face {{ font-family: 'Noto Color Emoji'; src: local('Noto Color Emoji'), default; }}
    .stApp {{ background-image: url("{BACKGROUND_IMAGE_URL}"); background-size: 150px; background-repeat: repeat; background-attachment: fixed; }}
    .block-container {{ max-width: 1400px !important; padding: 1rem !important; margin: auto !important; background: rgba(12, 12, 12, 0.96); backdrop-filter: blur(20px); border-radius: 0px; border-bottom: 2px solid #333; box-shadow: 0 20px 50px rgba(0,0,0,0.9); }}
    .main-title {{ font-size: 40px; font-weight: 900; text-align: center; margin-bottom: 20px; text-transform: uppercase; letter-spacing: -1px; background: linear-gradient(90deg, #00c6ff, #0072ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0 0 8px rgba(0, 114, 255, 0.4)); }}
    @media (min-width: 800px) {{ .main-title {{ font-size: 60px; }} }}
    
    .dpm-button-small {{ display: flex; align-items: center; justify-content: center; background-color: rgba(37, 99, 235, 0.2); color: #60a5fa !important; height: 25px; border-radius: 4px; text-decoration: none; font-weight: 600; font-size: 11px; border: 1px solid #2563eb; width: fit-content; padding: 0 10px; }}
    .dpm-button-small:hover {{ background-color: #2563eb; color: white !important; }}
    
    .input-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }}
    .input-label {{ font-size: 14px; font-weight: 700; color: #ddd; text-transform: uppercase; }}
    .stForm > div[data-testid="stFormEnterToSubmit"] {{ display: none; }}
    
    .player-panel {{ background: rgba(255, 255, 255, 0.03); border-radius: 16px; padding: 15px; height: 100%; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 10px; }}
    .player-name {{ font-size: 24px; font-weight: 900; color: white; text-align: center; margin-bottom: 2px; }}
    @media (min-width: 800px) {{ .player-name {{ font-size: 32px; }} }}
    .role-badge {{ font-size: 12px; font-weight: 700; color: #aaa; text-align: center; margin-bottom: 10px; letter-spacing: 1px; opacity: 0.8; }}
    .player-role {{ font-size: 14px; font-weight: 700; text-align: center; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; padding: 5px; border-radius: 4px; background: rgba(255,255,255,0.05); }}
    
    .color-gold {{ color: #FFD700; border-color: #FFD700; }} .color-blue {{ color: #00BFFF; border-color: #00BFFF; }} .color-green {{ color: #00ff99; border-color: #00ff99; }} .color-orange {{ color: #FFA500; border-color: #FFA500; }} .color-red {{ color: #ff4444; border-color: #ff4444; }}
    
    .stat-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }}
    .stat-label {{ font-size: 12px; color: #888; font-weight: 600; }}
    .stat-value {{ font-size: 16px; color: white; font-weight: 700; }}
    .stat-diff {{ font-size: 11px; font-weight: 600; margin-left: 6px; padding: 2px 4px; border-radius: 3px; }}
    .pos {{ color: #00ff99; background: rgba(0,255,153,0.1); }} .neg {{ color: #ff4444; background: rgba(255,68,68,0.1); }} .neutral {{ color: #666; }}
    
    .feedback-row {{ display: flex; gap: 5px; justify-content: center; margin-bottom: 15px; flex-wrap: wrap; }}
    .fb-box {{ padding: 4px 8px; border-radius: 6px; font-size: 10px; font-weight: 700; text-transform: uppercase; white-space: nowrap; }}
    .fb-good {{ background: rgba(0, 255, 153, 0.1); color: #00ff99; border: 1px solid #00ff99; }}
    .fb-bad {{ background: rgba(255, 68, 68, 0.1); color: #ff6666; border: 1px solid #ff4444; }}
    
    .verdict-banner {{ text-align: center; padding: 20px; margin-bottom: 30px; border-radius: 16px; background: rgba(0,0,0,0.4); border: 1px solid #333; }}
    .champ-img {{ width: 45px; height: 45px; border-radius: 50%; border: 2px solid #444; margin: 0 2px; }}
    .stButton > button {{ width: 100%; height: 55px; background: linear-gradient(90deg, #ff0055, #ff2222) !important; color: white !important; font-size: 18px; font-weight: 800; border: none; border-radius: 8px; text-transform: uppercase; letter-spacing: 1px; -webkit-appearance: none; appearance: none; }}
    .stButton > button:active {{ transform: scale(0.98); background: #ff0055 !important; }}
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
        st.markdown(f"""<div class="input-row"><span class="input-label">{T['label_id']}</span><a href="https://dpm.lol" target="_blank" class="dpm-button-small">{T['dpm_btn']}</a></div>""", unsafe_allow_html=True)
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

# --- NOM CORRIGÉ : analyze_qualities ---
def analyze_qualities(stats, role, lang_dict):
    qualities, flaws = [], []
    
    if stats['kda'] > 3.5: qualities.append(lang_dict.get("q_surv", "High KDA"))
    if stats['obj'] > 5000: qualities.append(lang_dict.get("q_obj", "Obj Dmg"))
    if stats['dpm'] > 750: qualities.append(lang_dict.get("q_dmg", "High Dmg"))
    if stats['vis'] > 35: qualities.append(lang_dict.get("q_vis", "Vision"))
    
    flaw = lang_dict.get("f_ok", "Solid")
    if role == "UTILITY":
        if stats['vis'] < 20: flaw = lang_dict.get("f_blind", "No Vis")
        elif stats['kda'] < 2.0: flaw = lang_dict.get("f_feed", "Feed")
    elif role == "JUNGLE":
        if stats['obj'] < 1000: flaw = lang_dict.get("f_no_obj", "No Obj")
        elif stats['kda'] < 2.0: flaw = lang_dict.get("f_feed", "Feed")
    else:
        if stats['dpm'] < 300: flaw = lang_dict.get("f_afk", "Low Dmg")
        elif stats['kda'] < 1.8: flaw = lang_dict.get("f_feed", "Feed")
        elif stats['gold'] < 300: flaw = lang_dict.get("f_farm", "Low Farm")

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
                if resp_acc.status_code != 200:
                    st.error(f"Error {resp_acc.status_code}")
                    st.stop()
                puuid = resp_acc.json().get("puuid")
                resp_matches = get_matches_from_api(puuid, region, API_KEY, q_id)
                match_ids = resp_matches.json()
                if not match_ids:
                    st.warning(T['error_no_games'])
                    st.info(f"{T['error_hint']} ({queue_label})")
                    st.stop()
            except Exception as e:
                st.error(f"API Error: {e}")
                st.stop()

            # ANALYSIS
            duo_data = {} 
            target_name = riot_id_input 
            data_lock = threading.Lock()
            
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

                col_left, col_right = st.columns(2, gap="large")
                
                # APPEL CORRECT
                qual, flaw = analyze_qualities(stats_me, main_role_me, T)
                qual_d, flaw_d = analyze_qualities(stats_duo, main_role_duo, T)

                with col_left:
                    st.markdown(f"""<div class="player-panel"><div class="player-name">{target_name}</div>
                    <div class="role-badge">{ROLE_ICONS.get(main_role_me, 'UNK')}</div>
                    <div class="player-role {role_me_color}">{T.get(role_me_key, 'PLAYER')}</div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="feedback-row"><div class="fb-box fb-good">{qual}</div><div class="fb-box fb-bad">{flaw}</div></div>""", unsafe_allow_html=True)
                    top_champs = [c[0] for c in Counter(best_duo['my_champs']).most_common(3)]
                    html_champs = "<div class='champ-row' style='justify-content:center; margin-bottom:20px;'>"
                    for ch in top_champs: html_champs += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
                    html_champs += "</div>"
                    st.markdown(html_champs, unsafe_allow_html=True)
                    render_stat_row("KDA", stats_me['kda'], stats_me['kda'] - stats_duo['kda'])
                    render_stat_row("DPM", stats_me['dpm'], stats_me['dpm'] - stats_duo['dpm'])
                    render_stat_row("GOLD", int(avg(s_me, 'gold')), int(avg(s_me, 'gold')) - int(avg(s_duo, 'gold')))
                    render_stat_row("VISION", stats_me['vis'], stats_me['vis'] - stats_duo['vis'])
                    render_stat_row("OBJ DMG", stats_me['obj'], stats_me['obj'] - stats_duo['obj'])
                    st.markdown("</div>", unsafe_allow_html=True)

                with col_right:
                    st.markdown(f"""<div class="player-panel"><div class="player-name">{duo_name}</div>
                    <div class="role-badge">{ROLE_ICONS.get(main_role_duo, 'UNK')}</div>
                    <div class="player-role {role_duo_color}">{T.get(role_duo_key, 'PLAYER')}</div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="feedback-row"><div class="fb-box fb-good">{qual_d}</div><div class="fb-box fb-bad">{flaw_d}</div></div>""", unsafe_allow_html=True)
                    top_champs_d = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                    html_champs_d = "<div class='champ-row' style='justify-content:center; margin-bottom:20px;'>"
                    for ch in top_champs_d: html_champs_d += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
                    html_champs_d += "</div>"
                    st.markdown(html_champs_d, unsafe_allow_html=True)
                    render_stat_row("KDA", stats_duo['kda'], stats_duo['kda'] - stats_me['kda'])
                    render_stat_row("DPM", stats_duo['dpm'], stats_duo['dpm'] - stats_me['dpm'])
                    render_stat_row("GOLD", int(avg(s_duo, 'gold')), int(avg(s_duo, 'gold')) - int(avg(s_me, 'gold')))
                    render_stat_row("VISION", stats_duo['vis'], stats_duo['vis'] - stats_me['vis'])
                    render_stat_row("OBJ DMG", stats_duo['obj'], stats_duo['obj'] - stats_me['obj'])
                    st.markdown("</div>", unsafe_allow_html=True)

            else:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.markdown(f"""<div class="verdict-banner" style="border-color:#00ff99"><div style="font-size:32px; font-weight:900; color:#00ff99;">{T["solo"]}</div><div style="font-size:18px; color:#ddd; margin-top:10px;">{T["solo_sub"]}</div></div>""", unsafe_allow_html=True)
