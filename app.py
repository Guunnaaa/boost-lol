import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import plotly.graph_objects as go
from urllib.parse import quote
from collections import Counter
import concurrent.futures
import threading

# --- CONFIGURATION ---
st.set_page_config(page_title="LoL Duo Analyst V73", layout="wide")

# --- API KEY ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ API Key missing. Add RIOT_API_KEY to Streamlit secrets.")
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
        "title": "LoL Duo Analyst", "btn_scan": "LANCER L'ANALYSE", "placeholder": "Exemple: Kameto#EUW", "label_id": "Riot ID", "lbl_region": "RÉGION", "lbl_mode": "MODE", "dpm_btn": "🔗 Voir sur dpm.lol", "lbl_duo_detected": "DUO DÉTECTÉ AVEC {duo}",
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
        "stats": "STATS", "combat": "COMBAT", "eco": "ÉCONOMIE", "vision": "VISION & MAP", "error_no_games": "Aucune partie trouvée.", "error_hint": "Vérifie la région ou le mode de jeu."
    },
    "EN": {
        "title": "LoL Duo Analyst", "btn_scan": "START ANALYSIS", "placeholder": "Example: Faker#KR1", "label_id": "Riot ID", "lbl_region": "REGION", "lbl_mode": "MODE", "dpm_btn": "🔗 Check dpm.lol", "lbl_duo_detected": "DUO DETECTED WITH {duo}",
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
        "stats": "STATS", "combat": "COMBAT", "eco": "ECONOMY", "vision": "VISION", "error_no_games": "No games found.", "error_hint": "Check Region."
    },
    "ES": {"title":"Analista LoL","btn_scan":"ANALIZAR","placeholder":"Ejemplo: Ibai#EUW","label_id":"Riot ID","lbl_region":"REGIÓN","lbl_mode":"MODO","dpm_btn":"Ver dpm.lol","lbl_duo_detected":"DUO CON {duo}","v_hyper":"MVP TOTAL","s_hyper":"Domina a {duo}","v_tactician":"ESTRATEGA","s_tactician":"Macro para {duo}","v_fighter":"GLADIADOR","s_fighter":"Daño","v_solid":"DUO SOLIDO","s_solid":"Sinergia con {duo}","v_passive":"PASIVO","s_passive":"Seguro","v_struggle":"DIFICULTAD","s_struggle":"Sufre vs {duo}","solo":"SOLO","solo_sub":"Sin duo","loading":"Cargando...","role_hyper":"CARRY","role_lead":"LIDER","role_equal":"SOCIO","role_supp":"APOYO","role_gap":"NOVATO","q_surv":"Inmortal","q_dmg":"Daño","q_obj":"Torres","q_vis":"Vision","q_bal":"Balance","q_supp":"Support","f_feed":"Muere","f_afk":"Poco daño","f_no_obj":"Sin obj","f_blind":"Ciego","f_farm":"Farm","f_ok":"Bien","stats":"STATS","combat":"COMBATE","eco":"ECONOMIA","vision":"VISION","error_no_games":"Error","error_hint":"Region?"},
    "KR": {"title":"LoL 듀오 분석","btn_scan":"분석 시작","placeholder":"예: Hide on bush#KR1","label_id":"Riot ID","lbl_region":"지역","lbl_mode":"모드","dpm_btn":"dpm.lol 확인","lbl_duo_detected":"{duo} 와 듀오","v_hyper":"하드 캐리","s_hyper":"{target} > {duo}","v_tactician":"전략가","s_tactician":"운영","v_fighter":"전투광","s_fighter":"딜","v_solid":"완벽 듀오","s_solid":"{target} & {duo}","v_passive":"버스","s_passive":"안전","v_struggle":"고전","s_struggle":"역부족","solo":"솔로","solo_sub":"듀오 없음","loading":"분석 중...","role_hyper":"캐리","role_lead":"리더","role_equal":"파트너","role_supp":"서포터","role_gap":"신입","q_surv":"생존","q_dmg":"딜량","q_obj":"철거","q_vis":"시야","q_bal":"밸런스","q_supp":"서폿","f_feed":"데스","f_afk":"딜부족","f_no_obj":"운영부족","f_blind":"시야부족","f_farm":"CS","f_ok":"굿","stats":"통계","combat":"전투","eco":"경제","vision":"시야","error_no_games":"없음","error_hint":"지역?"}
}

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
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        background: rgba(12, 12, 12, 0.95); backdrop-filter: blur(15px);
        border-radius: 15px; border: 1px solid #333; box-shadow: 0 20px 50px rgba(0,0,0,0.9);
        margin-top: 20px !important;
    }}

    /* TITRE */
    .main-title {{
        font-size: 55px; font-weight: 900; text-align: center; margin-bottom: 30px; margin-top: 10px;
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 10px rgba(0, 114, 255, 0.5)); text-transform: uppercase;
    }}
    @media (max-width: 800px) {{ .main-title {{ font-size: 40px; }} }}
    
    /* CARTE JOUEUR */
    .player-card {{
        background: rgba(30, 30, 30, 0.5); border-radius: 16px; padding: 25px;
        border: 1px solid rgba(255,255,255,0.08); text-align: center; height: 100%;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.2);
    }}
    .player-name {{ font-size: 28px; font-weight: 800; color: white; margin-bottom: 5px; }}
    .player-sub {{ font-size: 14px; color: #aaa; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }}

    /* BADGES */
    .badge {{
        display: inline-block; padding: 4px 8px; border-radius: 4px; 
        font-size: 11px; font-weight: 700; margin: 2px; text-transform: uppercase;
    }}
    .b-green {{ background: rgba(0, 255, 153, 0.15); color: #00ff99; border: 1px solid #00ff99; }}
    .b-red {{ background: rgba(255, 68, 68, 0.15); color: #ff6666; border: 1px solid #ff4444; }}
    .b-blue {{ background: rgba(0, 191, 255, 0.15); color: #00BFFF; border: 1px solid #00BFFF; }}
    .b-gold {{ background: rgba(255, 215, 0, 0.15); color: #FFD700; border: 1px solid #FFD700; }}

    /* STATS GRID */
    .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px; margin-bottom: 0px; }}
    .stat-item {{ background: rgba(0,0,0,0.3); padding: 12px; border-radius: 10px; text-align: left; border: 1px solid rgba(255,255,255,0.05); }}
    .stat-val-container {{ display: flex; align-items: center; gap: 8px; }}
    .stat-val {{ font-size: 20px; font-weight: 700; color: white; }}
    .stat-lbl {{ font-size: 11px; color: #999; text-transform: uppercase; margin-top: 4px; font-weight: 600; letter-spacing: 0.5px; }}
    
    .stat-diff {{ font-size: 12px; font-weight: 700; padding: 2px 5px; border-radius: 4px; }}
    .pos {{ color: #00ff99; background: rgba(0,255,153,0.15); }} 
    .neg {{ color: #ff4444; background: rgba(255,68,68,0.15); }}
    .neutral {{ color: #888; }}

    /* VERDICT BANNER */
    .verdict-box {{
        text-align: center; padding: 30px; border-radius: 16px; margin: 20px 0 40px 0;
        background: rgba(20, 20, 20, 0.8); border: 2px solid #333;
    }}
    
    /* DPM BUTTON */
    .dpm-btn {{
        background: rgba(37, 99, 235, 0.2); color: #60a5fa !important; padding: 5px 10px;
        border-radius: 6px; text-decoration: none; font-size: 12px; border: 1px solid #2563eb;
    }}

    /* BUTTON SCAN */
    .stButton > button {{
        width: 100%; height: 55px; background: linear-gradient(135deg, #ff0055, #cc0044);
        color: white; font-size: 20px; font-weight: 800; border: none; border-radius: 10px;
        text-transform: uppercase; transition: 0.3s;
    }}
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 25px rgba(255,0,60,0.5); }}
    
    /* HIDE INPUT LABEL */
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
    try: return requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
    except: return "14.23.1"

DD_VERSION = get_dd_version()

def get_champ_url(champ_name):
    if not champ_name: return "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Poro_0.jpg"
    clean = champ_name.replace(" ", "").replace("'", "").replace(".", "")
    mapping = {"wukong": "MonkeyKing", "renataglasc": "Renata", "nunu&willump": "Nunu", "kogmaw": "KogMaw", "reksai": "RekSai", "drmundo": "DrMundo", "belveth": "Belveth"}
    return f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/img/champion/{mapping.get(clean.lower(), clean)}.png"

def safe_format(text, target, duo):
    try: return text.format(target=target, duo=duo)
    except: return text

# --- LOGIQUE SCORE & STYLE ---
def determine_playstyle(stats, role, lang_dict):
    badges = []
    if stats['kda'] >= 4.0: badges.append((lang_dict.get("q_surv", "KDA Player"), "b-gold"))
    if stats['vis_min'] >= 2.0 or (role == "UTILITY" and stats['vis_min'] >= 2.5): badges.append((lang_dict.get("q_vis", "Oracle"), "b-blue")) 
    if stats['kp'] >= 0.65: badges.append(("Teamplayer", "b-green"))
    if stats['dmg_min'] >= 800: badges.append((lang_dict.get("q_dmg", "Heavy Hitter"), "b-red"))
    if stats['solokills'] >= 2.5: badges.append(("Duelist", "b-red"))
    if stats['obj'] >= 5000: badges.append((lang_dict.get("q_obj", "Breacher"), "b-gold"))
    
    if stats['kda'] < 1.5: badges.append((lang_dict.get("f_feed", "Grey Screen"), "b-red"))
    if stats['vis_min'] < 0.4 and role != "ADC": badges.append((lang_dict.get("f_blind", "Blind"), "b-red"))
    if stats['dmg_min'] < 300 and role not in ["UTILITY", "JUNGLE"]: badges.append(("AFK Farm", "b-blue"))

    if not badges: badges.append(("Standard", "b-blue"))
    return badges[:3] 

def analyze_qualities(stats, role, lang_dict):
    qualities, flaws = [], []
    
    # CORRECTION DES CLÉS DPM/GOLD_MIN QUI ETAIENT NOMMEES DMG/GOLD
    if stats['kda'] > 3.5: qualities.append(lang_dict.get("q_surv", "Solid KDA"))
    if stats['obj'] > 5000: qualities.append(lang_dict.get("q_obj", "Obj Dmg"))
    if stats['dmg_min'] > 750: qualities.append(lang_dict.get("q_dmg", "High Dmg"))
    if stats['vis_min'] > 35: qualities.append(lang_dict.get("q_vis", "Vision"))
    
    scores = {
        'kda': stats['kda'] / 3.0,
        'dmg_min': stats['dmg_min'] / 500.0,
        'vis_min': stats['vis_min'] / 2.0,
        'obj': stats['obj'] / 3000.0,
        'gold_min': stats['gold_min'] / 400.0
    }
    
    # Filtre Rôle
    if role == "UTILITY":
        scores.pop('dmg_min', None)
        scores.pop('gold_min', None)
    elif role == "JUNGLE":
        scores['obj'] = stats['obj'] / 5000.0
    
    worst_stat = min(scores, key=scores.get) if scores else 'kda'
    
    flaws_map = {
        'kda': lang_dict.get("f_feed", "Feed"),
        'dmg_min': lang_dict.get("f_afk", "Low Dmg"),
        'vis_min': lang_dict.get("f_blind", "No Vis"),
        'obj': lang_dict.get("f_no_obj", "No Obj"),
        'gold_min': lang_dict.get("f_farm", "Low Farm")
    }
    
    flaw = flaws_map.get(worst_stat, "Ok")
    q = qualities[0] if qualities else lang_dict.get("q_bal", "Balanced")
    if role == "UTILITY" and q == lang_dict.get("q_bal"): q = lang_dict.get("q_supp", "Support")
    return q, flaw

# --- FONCTION GRAPHIQUE ---
def create_radar(data_list, names, colors, title=None, height=400, show_legend=True):
    categories = ['Combat', 'Gold', 'Vision', 'Objectifs', 'Survie']
    fig = go.Figure()
    for i, data in enumerate(data_list):
        fig.add_trace(go.Scatterpolar(
            r=data, theta=categories, fill='toself', name=names[i],
            line_color=colors[i], opacity=0.7, marker=dict(size=5)
        ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#555', gridcolor='#444', gridwidth=1),
            angularaxis=dict(linecolor='#555', gridcolor='#444', gridwidth=1, tickfont=dict(color='#eee', size=12, weight='bold'))
        ),
        showlegend=show_legend,
        legend=dict(font=dict(color='white', size=12), orientation="h", y=-0.15, x=0.5, xanchor="center", bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=60, t=40 if title else 20, b=60),
        height=height,
        title=dict(text=title, x=0.5, y=0.95, font=dict(color='white', size=16)) if title else None
    )
    return fig

# --- API ---
@st.cache_data(ttl=600)
def get_puuid(name, tag, region, api_key):
    url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={api_key}"
    return requests.get(url)

@st.cache_data(ttl=120)
def get_matches(puuid, region, api_key, q_id):
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue={q_id}&start=0&count=20&api_key={api_key}"
    return requests.get(url)

def fetch_match(m_id, region, api_key):
    return requests.get(f"https://{region}.api.riotgames.com/lol/match/v5/matches/{m_id}?api_key={api_key}").json()

# --- MAIN ---
if submitted:
    def get_regions(region_code):
        if region_code in ["EUW1", "EUN1", "TR1", "RU"]: return "europe"
        elif region_code == "KR": return "asia"
        else: return "americas"

    if "#" not in riot_id_input:
        st.error("⚠️ Format invalide. Utilise: Nom#TAG")
    else:
        name_raw, tag = riot_id_input.split("#")
        region = get_regions(region_select)
        q_id = QUEUE_MAP[queue_label]
        
        with st.spinner(T["loading"]):
            try:
                r_acc = get_puuid(quote(name_raw), tag, region, API_KEY)
                if r_acc.status_code != 200:
                    st.error(T["error_no_games"])
                    st.stop()
                puuid = r_acc.json().get("puuid")
                r_match = get_matches(puuid, region, API_KEY, q_id)
                match_ids = r_match.json()
                if not match_ids:
                    st.warning(f"{T['error_no_games']} ({queue_label})")
                    st.stop()
            except Exception as e:
                st.error(f"Erreur API: {e}")
                st.stop()

            duo_data = {}
            target_name = riot_id_input
            data_lock = threading.Lock()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_match = {executor.submit(fetch_match, m, region, API_KEY): m for m in match_ids}
                for future in concurrent.futures.as_completed(future_to_match):
                    try:
                        data = future.result()
                        if 'info' not in data: continue
                        info = data['info']
                        duration_min = info['gameDuration'] / 60
                        if duration_min < 5: continue 
                        participants = info['participants']
                        me = next((p for p in participants if p['puuid'] == puuid), None)
                        if not me: continue
                        target_name = me['riotIdGameName']
                        
                        def extract_stats(p):
                            return {
                                'kills': p['kills'], 'deaths': p['deaths'], 'assists': p['assists'],
                                'dmg': p['totalDamageDealtToChampions'],
                                'gold': p['goldEarned'], 'vis': p['visionScore'],
                                'obj': p.get('damageDealtToObjectives', 0), 'towers': p.get('turretTakedowns', 0),
                                'kp': p.get('challenges', {}).get('killParticipation', 0),
                                'solokills': p.get('challenges', {}).get('soloKills', 0),
                                'champ': p['championName'], 'role': p.get('teamPosition', 'UNKNOWN'), 'win': p['win']
                            }
                        my_s = extract_stats(me)
                        with data_lock:
                            for p in info['participants']:
                                if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                                    full_id = f"{p.get('riotIdGameName')}#{p.get('riotIdTagLine')}"
                                    if full_id not in duo_data:
                                        duo_data[full_id] = {'name': p.get('riotIdGameName'), 'games': 0, 'wins': 0, 'champs': [], 'roles': [], 'stats_duo': [], 'stats_me': []}
                                    d = duo_data[full_id]
                                    d['games'] += 1
                                    if p['win']: d['wins'] += 1
                                    d['champs'].append(p['championName'])
                                    d['roles'].append(p.get('teamPosition', 'UNKNOWN'))
                                    duo_s = extract_stats(p)
                                    for s, norm in [(duo_s, d['stats_duo']), (my_s, d['stats_me'])]:
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
                duo_name = best_duo['name']
                winrate = int((best_duo['wins']/g)*100)
                try: role_duo = Counter(best_duo['roles']).most_common(1)[0][0]
                except: role_duo = "UNKNOWN"
                try: role_me = Counter([x['role'] for x in best_duo['stats_me']]).most_common(1)[0][0]
                except: role_me = "UNKNOWN"
                top_champs_duo = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                top_champs_me = [c[0] for c in Counter([x['champ'] for x in best_duo['stats_me']]).most_common(3)]
                
                def avg_stats(stat_list):
                    res = {}
                    keys = stat_list[0].keys()
                    for k in keys:
                        if isinstance(stat_list[0][k], (int, float)): res[k] = sum(d[k] for d in stat_list) / len(stat_list)
                    return res
                avg_duo = avg_stats(best_duo['stats_duo'])
                avg_me = avg_stats(best_duo['stats_me'])
                def calc_kda(s): return round((s['kills'] + s['assists']) / max(1, s['deaths']), 2)
                avg_duo['kda'] = calc_kda(avg_duo)
                avg_me['kda'] = calc_kda(avg_me)

                def get_impact_score(s, role):
                    score = 0
                    score += min(5, s['kda']) 
                    score += (s['kp'] * 4)
                    vis_target = 2.0 if role == "UTILITY" else 1.0
                    score += min(3, (s['vis_min'] / vis_target) * 2)
                    if role != "UTILITY": score += min(4, s['dmg_min'] / 700)
                    obj_score = (s['obj'] / 5000) + (s['towers'] * 0.5)
                    score += min(4, obj_score)
                    return score

                score_me = get_impact_score(avg_me, role_me)
                score_duo = get_impact_score(avg_duo, role_duo)
                ratio = score_me / max(0.1, score_duo)
                
                if ratio > 1.35: title, color, sub = T["v_hyper"], "#FFD700", safe_format(T.get("s_hyper", ""), target_name, duo_name)
                elif ratio > 1.15: title, color, sub = T["v_lead"], "#00BFFF", safe_format(T.get("s_lead", ""), target_name, duo_name)
                elif ratio < 0.75: title, color, sub = T["v_struggle"], "#ff4444", safe_format(T.get("s_struggle", ""), target_name, duo_name)
                elif ratio < 0.9: title, color, sub = T["v_supp"], "#FFA500", safe_format(T.get("s_supp", ""), target_name, duo_name)
                else: title, color, sub = T["v_solid"], "#00ff99", T.get("s_solid", "")

                components.html(f"<script>window.parent.document.querySelector('.verdict-box').scrollIntoView({{behavior:'smooth'}});</script>", height=0)

                st.markdown(f"""<div class="verdict-box" style="border-color:{color}"><div style="font-size:14px; font-weight:700; color:#aaa; margin-bottom:5px; text-transform:uppercase;">{safe_format(T['lbl_duo_detected'], target=target_name, duo=duo_name)}</div><div style="font-size:45px; font-weight:900; color:{color}; margin-bottom:10px;">{title}</div><div style="font-size:18px; color:#eee; font-style:italic;">"{sub}"</div><div style="margin-top:15px; color:#888; font-weight:600;">{g} Games ensemble • {winrate}% Winrate</div></div>""", unsafe_allow_html=True)

                def norm(val, max_v): return min(100, (val / max_v) * 100)
                data_me_norm = [norm(avg_me['dmg_min'], 1000), norm(avg_me['gold_min'], 600), norm(avg_me['vis_min'], 2.5), norm(avg_me['obj'], 8000), norm(avg_me['kda'], 5)]
                data_duo_norm = [norm(avg_duo['dmg_min'], 1000), norm(avg_duo['gold_min'], 600), norm(avg_duo['vis_min'], 2.5), norm(avg_duo['obj'], 8000), norm(avg_duo['kda'], 5)]
                st.plotly_chart(create_radar([data_me_norm, data_duo_norm], [target_name, duo_name], ['#00c6ff', '#ff0055']), use_container_width=True, config={'displayModeBar': False}, theme=None)
                
                col1, col2 = st.columns(2, gap="large")
                badges_me = determine_playstyle(avg_me, role_me, T)
                badges_duo = determine_playstyle(avg_duo, role_duo, T)
                qual, flaw = analyze_qualities(avg_me, role_me, T)
                qual_d, flaw_d = analyze_qualities(avg_duo, role_duo, T)

                def display_player_card(name, champs, stats, badges, role_icon, diff_stats, color_theme, q, f):
                    badges_html = "".join([f"<span class='badge {b[1]}'>{b[0]}</span>" for b in badges])
                    champs_html = "".join([f"<img src='{get_champ_url(c)}' style='width:55px; border-radius:50%; border:2px solid #333; margin:4px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);'>" for c in champs])
                    def stat_line(label, value, diff_val, is_percent=False, is_kda=False):
                        val_str = f"{int(value*100)}%" if is_percent else (f"{value:.2f}" if is_kda else (f"{int(value/1000)}k" if value > 1000 else f"{int(value)}"))
                        diff_html = f"<span class='stat-diff pos'>+{diff_val:.1f}</span>" if diff_val > 0 else (f"<span class='stat-diff neg'>{diff_val:.1f}</span>" if diff_val < 0 else f"<span class='stat-diff neutral'>=</span>")
                        return f"""<div class="stat-item"><div class="stat-val-container"><div class="stat-val">{val_str}</div>{diff_html}</div><div class="stat-lbl">{label}</div></div>"""
                    fb_html = f"""<div class="feedback-row"><div class="fb-box fb-good">{q}</div><div class="fb-box fb-bad">{f}</div></div>"""
                    stat_grid_html = f"""<div class="stat-grid">{stat_line("KDA", stats['kda'], diff_stats['kda'], is_kda=True)}{stat_line("KP", stats['kp'], diff_stats['kp']*100, is_percent=True)}{stat_line("DPM", stats['dmg_min'], diff_stats['dmg_min'])}{stat_line("VIS/M", stats['vis_min'], diff_stats['vis_min'])}{stat_line("OBJ DMG", stats['obj'], diff_stats['obj'])}{stat_line("GOLD/M", stats['gold_min'], diff_stats['gold_min'])}</div>"""
                    st.markdown(f"""<div class="player-card" style="border-top: 4px solid {color_theme};"><div class="player-name">{name}</div><div class="player-sub">{role_icon}</div>{fb_html}<div style="margin:10px 0;">{badges_html}</div><div style="margin-bottom:15px;">{champs_html}</div>{stat_grid_html}</div>""", unsafe_allow_html=True)

                diff_me = {k: avg_me[k] - avg_duo[k] for k in avg_me if isinstance(avg_me[k], (int, float))}
                diff_duo = {k: avg_duo[k] - avg_me[k] for k in avg_duo if isinstance(avg_duo[k], (int, float))}

                with col1: display_player_card(target_name, top_champs_me, avg_me, badges_me, ROLE_ICONS.get(role_me, "UNK"), diff_me, '#00c6ff', qual, flaw)
                with col2: display_player_card(duo_name, top_champs_duo, avg_duo, badges_duo, ROLE_ICONS.get(role_duo, "UNK"), diff_duo, '#ff0055', qual_d, flaw_d)

            else:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"""<div class="verdict-box" style="border-color:#888;"><div style="font-size:32px; font-weight:900; color:#888;">{T["solo"]}</div><div style="font-size:16px; color:#aaa;">{T["solo_sub"]}</div></div>""", unsafe_allow_html=True)
