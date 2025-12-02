import streamlit as st
import requests
import time
from urllib.parse import quote
from collections import Counter
import concurrent.futures

# --- CONFIGURATION ---
st.set_page_config(page_title="LoL Duo Analyst V31", layout="wide")

# --- API KEY ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ API Key missing. Add RIOT_API_KEY to Streamlit secrets.")
    st.stop()

# --- ASSETS ---
BACKGROUND_IMAGE_URL = "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123"
CLOWN_IMAGE_URL = "https://raw.githubusercontent.com/[YOUR_GITHUB_NAME]/[REPO_NAME]/main/clown.jpg"
DD_VERSION = "13.24.1"

# --- AUTO-UPDATE VERSION ---
@st.cache_data(ttl=3600)
def get_dd_version():
    try: return requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
    except: return "14.23.1"

DD_VERSION = get_dd_version()

# --- TRADUCTIONS (PHRASES COMPLEXES) ---
TRANSLATIONS = {
    "FR": {
        "title": "LoL Duo Analyst",
        "btn_scan": "LANCER L'ANALYSE COMPLÈTE",
        "placeholder": "Exemple: Sardoche#EUW",
        "dpm_btn": "🔗 Voir sur dpm.lol",
        "input_label": "Riot ID du Joueur",
        
        # Phrases d'analyse
        "desc_boosted_hard": "{duo} surclasse largement {target} dans presque tous les domaines. L'écart de niveau est flagrant.",
        "desc_boosted_soft": "{duo} mène la danse et prend les initiatives. {target} suit le rythme mais pèse moins sur la partie.",
        "desc_equal": "Excellente synergie. Les deux joueurs ont un impact comparable et se complètent bien.",
        "desc_booster_soft": "{target} est le moteur du duo. C'est souvent lui qui débloque les situations.",
        "desc_booster_hard": "{target} joue à un niveau bien supérieur à ce rang. Il porte littéralement le duo.",

        "solo": "JOUEUR SOLO",
        "solo_sub": "Aucun duo récurrent détecté sur les 20 dernières parties.",
        "loading": "Calcul des points forts et faibles...",
        "error_no_games": "Aucune partie trouvée.",
        
        # Stats Labels
        "lbl_quality": "✅ POINT FORT",
        "lbl_flaw": "⚠️ POINT FAIBLE",
        "lbl_kda": "KDA",
        "lbl_dpm": "DÉGÂTS/MIN",
        "lbl_gold": "GOLD/MIN",
        "lbl_vis": "VISION",
        "lbl_obj": "OBJECTIFS",
        "lbl_towers": "TOURS",
    },
    "EN": {
        "title": "LoL Duo Analyst",
        "btn_scan": "START FULL ANALYSIS",
        "placeholder": "Example: Faker#KR1",
        "dpm_btn": "🔗 Check dpm.lol",
        "input_label": "Player Riot ID",
        
        "desc_boosted_hard": "{duo} heavily outperforms {target} in almost every metric. The skill gap is significant.",
        "desc_boosted_soft": "{duo} is leading the charge. {target} follows up but has less overall impact.",
        "desc_equal": "Great synergy. Both players have comparable impact and complement each other.",
        "desc_booster_soft": "{target} is the engine of this duo. They usually make the play-making decisions.",
        "desc_booster_hard": "{target} is playing at a much higher level. They are hard carrying the duo.",

        "solo": "SOLO PLAYER",
        "solo_sub": "No recurring partner found.",
        "loading": "Analyzing strengths and weaknesses...",
        "error_no_games": "No games found.",
        
        "lbl_quality": "✅ STRENGTH",
        "lbl_flaw": "⚠️ WEAKNESS",
        "lbl_kda": "KDA", "lbl_dpm": "DMG/MIN", "lbl_gold": "GOLD/MIN", "lbl_vis": "VISION", "lbl_obj": "OBJECTIVES", "lbl_towers": "TOWERS"
    }
}

# --- CSS STYLES ---
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    
    .stApp {{
        background-image: url("{BACKGROUND_IMAGE_URL}");
        background-size: 150px; background-repeat: repeat; background-attachment: fixed;
    }}
    
    .block-container {{
        max-width: 1400px !important; padding: 2rem !important; margin: auto !important;
        background: rgba(12, 12, 12, 0.96); backdrop-filter: blur(20px);
        border-radius: 0px; border-bottom: 2px solid #333; box-shadow: 0 20px 50px rgba(0,0,0,0.9);
    }}
    
    .main-title {{
        font-size: 60px; font-weight: 900; color: white; text-align: center; margin-bottom: 30px;
        text-transform: uppercase; letter-spacing: -2px;
        background: -webkit-linear-gradient(#eee, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    
    /* CUSTOM INPUT LABEL HEADER */
    .input-header {{
        display: flex; align-items: center; gap: 10px; margin-bottom: -15px;
    }}
    .custom-label {{ font-size: 14px; font-weight: 700; color: #fff; }}
    
    .dpm-btn-mini {{
        background: rgba(37, 99, 235, 0.2); color: #60a5fa;
        font-size: 11px; padding: 2px 8px; border-radius: 4px;
        text-decoration: none; border: 1px solid rgba(37, 99, 235, 0.5);
        transition: 0.2s;
    }}
    .dpm-btn-mini:hover {{ background: #2563eb; color: white; }}

    /* PANELS */
    .player-panel {{ background: rgba(255, 255, 255, 0.03); border-radius: 16px; padding: 25px; height: 100%; border: 1px solid rgba(255,255,255,0.05); }}
    
    .player-name {{ font-size: 32px; font-weight: 900; color: white; text-align: center; margin-bottom: 20px; }}
    
    /* FEEDBACK BOXES */
    .feedback-box {{
        padding: 10px; border-radius: 8px; margin-bottom: 5px; font-size: 13px; font-weight: 600;
        display: flex; align-items: center;
    }}
    .fb-good {{ background: rgba(0, 255, 153, 0.1); color: #00ff99; border-left: 3px solid #00ff99; }}
    .fb-bad {{ background: rgba(255, 68, 68, 0.1); color: #ff6666; border-left: 3px solid #ff4444; }}

    /* STATS ROW */
    .stat-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }}
    .stat-label {{ font-size: 13px; color: #888; font-weight: 600; }}
    .stat-value {{ font-size: 18px; color: white; font-weight: 700; }}
    .stat-dpm {{ font-size: 12px; color: #aaa; margin-left: 5px; }}

    .verdict-banner {{ text-align: center; padding: 30px; margin-bottom: 40px; border-radius: 16px; background: rgba(0,0,0,0.4); border: 1px solid #333; }}
    .verdict-text {{ font-size: 22px; font-weight: 500; color: #ddd; line-height: 1.4; }}

    .stButton > button {{
        width: 100%; height: 55px; background: linear-gradient(90deg, #ff0055, #ff2222);
        color: white; font-size: 18px; font-weight: 800; border: none; border-radius: 8px;
        text-transform: uppercase; transition: 0.2s;
    }}
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 20px rgba(255,0,85,0.3); }}
    
    .champ-img {{ width: 55px; height: 55px; border-radius: 50%; border: 2px solid #444; margin: 0 4px; }}
    p, label {{ color: #eee !important; }}
    </style>
    """, unsafe_allow_html=True
)

# --- HEADER & LANGUAGE ---
c_title, c_lang = st.columns([5, 1])
with c_lang:
    selected_lang = st.selectbox("Language", ["FR", "EN"], label_visibility="collapsed")
T = TRANSLATIONS[selected_lang]

st.markdown(f'<div class="main-title">{T["title"]}</div>', unsafe_allow_html=True)

# --- FORMULAIRE CUSTOM ---
with st.form("search_form"):
    c1, c2, c3 = st.columns([3, 1, 1], gap="medium")
    
    with c1:
        # Custom Label + Button Header
        st.markdown(f"""
        <div class="input-header">
            <span class="custom-label">{T['input_label']}</span>
            <a href="https://dpm.lol" target="_blank" class="dpm-btn-mini">{T['dpm_btn']}</a>
        </div>
        """, unsafe_allow_html=True)
        # Input sans label (label_visibility hidden ne marche pas bien ici, on laisse vide)
        riot_id_input = st.text_input("LabelCaché", placeholder=T["placeholder"], label_visibility="collapsed")
        
    with c2:
        st.markdown(f"<span class='custom-label'>Region</span>", unsafe_allow_html=True)
        region_select = st.selectbox("Region", ["EUW1", "NA1", "KR", "EUN1", "TR1"], label_visibility="collapsed")
        
    with c3:
        st.markdown(f"<span class='custom-label'>Mode</span>", unsafe_allow_html=True)
        queue_type = st.selectbox("Mode", ["Solo/Duo", "Flex"], label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button(T["btn_scan"])

# --- FONCTIONS ---
def get_champ_url(champ_name):
    if not champ_name: return "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Poro_0.jpg"
    clean = champ_name.replace(" ", "").replace("'", "").replace(".", "")
    if clean.lower() == "wukong": clean = "MonkeyKing"
    if clean.lower() == "renataglasc": clean = "Renata"
    if clean.lower() == "nunu&willump": clean = "Nunu"
    if clean.lower() == "kogmaw": clean = "KogMaw"
    if clean.lower() == "reksai": clean = "RekSai"
    if clean.lower() == "drmundo": clean = "DrMundo"
    if clean.lower() == "belveth": clean = "Belveth"
    return f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/img/champion/{clean}.png"

def analyze_qualities(stats, lang_dict):
    """Détermine un point fort et un point faible"""
    qualities = []
    flaws = []
    
    # Seuils arbitraires basés sur une moyenne SoloQ
    if stats['kda'] > 3.0: qualities.append("Survivalist (KDA)")
    elif stats['kda'] < 1.8: flaws.append("Feeder (KDA < 2)")
    
    if stats['dpm'] > 700: qualities.append("Heavy Hitter (High DPM)")
    elif stats['dpm'] < 300: flaws.append("Low Impact (Low DPM)")
    
    if stats['vis'] > 25: qualities.append("Map Control (Vision)")
    elif stats['vis'] < 10: flaws.append("Blind (No Vision)")
    
    if stats['obj'] > 5000: qualities.append("Objective Focus")
    elif stats['obj'] < 1000: flaws.append("Ignores Objectives")
    
    # Fallbacks
    q = qualities[0] if qualities else "Balanced Playstyle"
    f = flaws[0] if flaws else "No major flaw"
    
    return q, f

def render_stat_row(label, val, unit=""):
    val_display = f"{val}{unit}"
    if isinstance(val, int) and val > 1000: val_display = f"{val/1000:.1f}k"
    st.markdown(f"""<div class="stat-row"><div class="stat-label">{label}</div><div class="stat-value">{val_display}</div></div>""", unsafe_allow_html=True)

# --- CACHED FUNCTIONS ---
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

# --- LOGIQUE ---
if submitted:
    def get_regions(region_code):
        if region_code in ["EUW1", "EUN1", "TR1", "RU"]: return "europe"
        elif region_code == "KR": return "asia"
        else: return "americas"

    if not riot_id_input or "#" not in riot_id_input:
        st.error("⚠️ Format: Name#TAG")
    else:
        name_raw, tag = riot_id_input.split("#")
        name_encoded = quote(name_raw)
        region = get_regions(region_select)
        q_id = 420 if queue_type == "Solo/Duo" else 440
        
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
                    st.stop()
            except Exception as e:
                st.error(f"API Error: {e}")
                st.stop()

            # ANALYSIS
            duo_data = {} 
            target_name = riot_id_input 
            
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
                                    'gold': p['goldEarned'] / duration_min, # Gold per min
                                    'vis': p['visionScore'],
                                    'obj': p.get('damageDealtToObjectives', 0),
                                    'towers': p.get('challenges', {}).get('turretTakedowns', 0),
                                    'champ': p['championName']
                                }
                            my_s = get_stats(me)
                            for p in participants:
                                if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                                    full_id = f"{p.get('riotIdGameName')}#{p.get('riotIdTagLine')}"
                                    if full_id not in duo_data:
                                        duo_data[full_id] = {
                                            'name': p.get('riotIdGameName'), 'games': 0, 'wins': 0,
                                            'stats': {'kda':0, 'dpm':0, 'gold':0, 'vis':0, 'obj':0, 'towers':0},
                                            'my_stats_vs': {'kda':0, 'dpm':0, 'gold':0, 'vis':0, 'obj':0, 'towers':0},
                                            'champs': [], 'my_champs': []    
                                        }
                                    d = duo_data[full_id]
                                    d['games'] += 1
                                    if p['win']: d['wins'] += 1
                                    d['champs'].append(p['championName'])
                                    d['my_champs'].append(my_s['champ'])
                                    duo_s = get_stats(p)
                                    for k in d['stats']:
                                        d['stats'][k] += duo_s[k]
                                        d['my_stats_vs'][k] += my_s[k]
                    except: pass 

            # RESULT
            st.markdown("---")
            best_duo = None
            max_g = 0
            for k, v in duo_data.items():
                if v['games'] > max_g:
                    max_g = v['games']
                    best_duo = v
            
            if best_duo and max_g >= 4:
                g = best_duo['games']
                duo_name = best_duo['name']
                
                def avg_f(d, key): return round(d[key] / g, 2)
                def avg(d, key): return int(d[key] / g)
                
                s_me = best_duo['my_stats_vs']
                s_duo = best_duo['stats']
                
                # --- CALCUL V29 (FAIR) ---
                def calc_score(s):
                    kda = s['kda'] / g
                    dpm = s['dpm'] / g
                    obj = s['obj'] / g 
                    vis = s['vis'] / g
                    # On triple l'importance des objectifs et KDA
                    score = (kda * 150) + (dpm * 0.4) + (obj * 0.3) + (vis * 10)
                    return score

                score_me = calc_score(s_me)
                score_duo = calc_score(s_duo)
                ratio = score_me / max(1, score_duo)
                
                if ratio > 1.35: state = "BOOSTER_HARD"
                elif ratio > 1.1: state = "BOOSTER_SOFT"
                elif ratio < 0.75: state = "BOOSTED_HARD"
                elif ratio < 0.9: state = "BOOSTED_SOFT"
                else: state = "EQUAL"

                winrate = int((best_duo['wins']/g)*100)

                # --- CONFIGURATION TEXTES ---
                if state == "BOOSTED_HARD":
                    color = "#ff4444"
                    desc = T["desc_boosted_hard"].format(target=target_name, duo=duo_name)
                elif state == "BOOSTED_SOFT":
                    color = "#FFA500"
                    desc = T["desc_boosted_soft"].format(target=target_name, duo=duo_name)
                elif state == "BOOSTER_HARD":
                    color = "#FFD700"
                    desc = T["desc_booster_hard"].format(target=target_name)
                elif state == "BOOSTER_SOFT":
                    color = "#00BFFF"
                    desc = T["desc_booster_soft"].format(target=target_name, duo=duo_name)
                else:
                    color = "#00ff99"
                    desc = T["desc_equal"]

                st.markdown(f"""
                <div class="verdict-banner" style="border-color:{color}">
                    <div class="verdict-text">{desc}</div>
                    <div style="margin-top:10px; font-size:14px; color:#888;">{g} Games • {winrate}% Winrate</div>
                </div>
                """, unsafe_allow_html=True)

                # --- PANELS ---
                col_left, col_right = st.columns(2, gap="large")
                
                # --- LEFT (ME) ---
                with col_left:
                    # Qualités
                    stats_me = {
                        'kda': avg_f(s_me, 'kda'), 'dpm': avg(s_me, 'dpm'),
                        'vis': avg(s_me, 'vis'), 'obj': avg(s_me, 'obj')
                    }
                    qual, flaw = analyze_qualities(stats_me, T)
                    
                    st.markdown(f"""
                    <div class="player-panel">
                        <div class="player-name">{target_name}</div>
                        <div style="display:flex; justify-content:center; gap:10px; margin-bottom:20px;">
                            <div class="feedback-box fb-good">{T['lbl_quality']}: {qual}</div>
                            <div class="feedback-box fb-bad">{T['lbl_flaw']}: {flaw}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Icons
                    top_champs = [c[0] for c in Counter(best_duo['my_champs']).most_common(3)]
                    html_champs = "<div class='champ-row' style='justify-content:center; margin-bottom:20px;'>"
                    for ch in top_champs: html_champs += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
                    html_champs += "</div>"
                    st.markdown(html_champs, unsafe_allow_html=True)
                    
                    render_stat_row(T["lbl_kda"], stats_me['kda'])
                    render_stat_row(T["lbl_dpm"], stats_me['dpm'])
                    render_stat_row(T["lbl_gold"], int(avg(s_me, 'gold')))
                    render_stat_row(T["lbl_vis"], stats_me['vis'])
                    render_stat_row(T["lbl_obj"], stats_me['obj'])
                    st.markdown("</div>", unsafe_allow_html=True)

                # --- RIGHT (DUO) ---
                with col_right:
                    stats_duo = {
                        'kda': avg_f(s_duo, 'kda'), 'dpm': avg(s_duo, 'dpm'),
                        'vis': avg(s_duo, 'vis'), 'obj': avg(s_duo, 'obj')
                    }
                    qual_d, flaw_d = analyze_qualities(stats_duo, T)
                    
                    st.markdown(f"""
                    <div class="player-panel">
                        <div class="player-name">{duo_name}</div>
                        <div style="display:flex; justify-content:center; gap:10px; margin-bottom:20px;">
                            <div class="feedback-box fb-good">{T['lbl_quality']}: {qual_d}</div>
                            <div class="feedback-box fb-bad">{T['lbl_flaw']}: {flaw_d}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    top_champs_d = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                    html_champs_d = "<div class='champ-row' style='justify-content:center; margin-bottom:20px;'>"
                    for ch in top_champs_d: html_champs_d += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
                    html_champs_d += "</div>"
                    st.markdown(html_champs_d, unsafe_allow_html=True)
                    
                    render_stat_row(T["lbl_kda"], stats_duo['kda'])
                    render_stat_row(T["lbl_dpm"], stats_duo['dpm'])
                    render_stat_row(T["lbl_gold"], int(avg(s_duo, 'gold')))
                    render_stat_row(T["lbl_vis"], stats_duo['vis'])
                    render_stat_row(T["lbl_obj"], stats_duo['obj'])
                    st.markdown("</div>", unsafe_allow_html=True)

            else:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="verdict-banner" style="border-color:#00ff99">
                    <div style="font-size:32px; font-weight:900; color:#00ff99;">{T["solo"]}</div>
                    <div style="font-size:18px; color:#ddd; margin-top:10px;">{T["solo_sub"]}</div>
                </div>
                """, unsafe_allow_html=True)
