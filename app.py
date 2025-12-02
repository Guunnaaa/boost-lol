import streamlit as st
import requests
import time
from urllib.parse import quote
from collections import Counter
import concurrent.futures

# --- CONFIGURATION ---
st.set_page_config(page_title="LoL Duo Investigator V28", layout="wide")

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

# --- TRADUCTIONS ---
TRANSLATIONS = {
    "FR": {
        "title": "LoL Duo Investigator",
        "btn_scan": "LANCER L'ANALYSE",
        "placeholder": "Exemple: Sardoche#EUW",
        "dpm_btn": "🔍 Trouver un pseudo sur dpm.lol",
        "verdict_boosted": "PASSAGER DÉTECTÉ",
        "sub_boosted": "{target} se fait carry par {duo}",
        "verdict_booster": "CHAUFFEUR DÉTECTÉ",
        "sub_booster": "{target} booste {duo}",
        "verdict_clean": "DUO SOLIDE",
        "sub_clean": "Contribution égale",
        "solo": "JOUEUR SOLO",
        "solo_sub": "Aucun duo récurrent sur 20 parties.",
        "loading": "Analyse tactique en cours...",
        "role_driver": "CHAUFFEUR",
        "role_pass": "PASSAGER",
        "role_equal": "PARTENAIRE",
        "stats": "STATS DE",
        "error_no_games": "Aucune partie trouvée.",
        "error_hint": "Vérifie la Région. Ce joueur fait-il de la SoloQ ?"
    },
    "EN": {
        "title": "LoL Duo Investigator",
        "btn_scan": "START ANALYSIS",
        "placeholder": "Example: Faker#KR1",
        "dpm_btn": "🔍 Find Summoner on dpm.lol",
        "verdict_boosted": "PASSENGER DETECTED",
        "sub_boosted": "{target} is carried by {duo}",
        "verdict_booster": "DRIVER DETECTED",
        "sub_booster": "{target} is boosting {duo}",
        "verdict_clean": "SOLID DUO",
        "sub_clean": "Equal Contribution",
        "solo": "SOLO PLAYER",
        "solo_sub": "No recurring duo found.",
        "loading": "Tactical analysis in progress...",
        "role_driver": "DRIVER",
        "role_pass": "PASSENGER",
        "role_equal": "PARTNER",
        "stats": "STATS FOR",
        "error_no_games": "No games found.",
        "error_hint": "Check Region. Does this player play SoloQ?"
    },
    # ... (Autres langues gardées simple pour gain de place)
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
        font-size: 60px; font-weight: 900; color: white; text-align: center; margin-bottom: 20px;
        text-transform: uppercase; letter-spacing: -2px;
        background: -webkit-linear-gradient(#eee, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    
    .dpm-button {{
        display: inline-block; background-color: rgba(37, 99, 235, 0.15); color: #60a5fa !important;
        text-align: center; padding: 6px 15px; border-radius: 20px; text-decoration: none;
        font-weight: 600; font-size: 12px; border: 1px solid #2563eb; margin-top: 8px; transition: all 0.2s ease;
        float: right;
    }}
    .dpm-button:hover {{ background-color: #2563eb; color: white !important; box-shadow: 0 0 10px rgba(37, 99, 235, 0.6); }}

    .player-panel {{ background: rgba(255, 255, 255, 0.03); border-radius: 20px; padding: 30px; height: 100%; border: 1px solid rgba(255,255,255,0.05); }}
    .panel-header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px; }}
    .player-name {{ font-size: 36px; font-weight: 900; color: white; margin-bottom: 5px; }}
    .player-role {{ font-size: 18px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; }}
    
    .role-driver {{ color: #FFD700; }}
    .role-pass {{ color: #ff4444; }}
    .role-equal {{ color: #00ff99; }}

    .stat-row {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
    .stat-label {{ font-size: 16px; color: #aaa; font-weight: 600; }}
    .stat-value {{ font-size: 22px; color: white; font-weight: 800; }}
    .stat-diff {{ font-size: 13px; font-weight: 600; margin-left: 10px; }}
    .pos {{ color: #00ff99; }} .neg {{ color: #ff4444; }} .neutral {{ color: #666; }}

    .verdict-banner {{ text-align: center; padding: 40px; margin-bottom: 50px; border-radius: 20px; background: rgba(0,0,0,0.3); border: 2px solid #333; }}

    .stButton > button {{
        width: 100%; height: 60px; background: linear-gradient(90deg, #ff0055, #ff2222);
        color: white; font-size: 24px; font-weight: 800; border: none; border-radius: 12px;
        text-transform: uppercase; transition: 0.2s; letter-spacing: 1px;
    }}
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 30px rgba(255,0,85,0.4); }}
    
    .champ-img {{ width: 70px; height: 70px; border-radius: 50%; border: 2px solid #444; margin: 0 5px; }}
    p, label {{ color: #eee !important; }}
    </style>
    """, unsafe_allow_html=True
)

# --- HEADER & LANGUAGE ---
c_title, c_lang = st.columns([5, 1])
with c_lang:
    selected_lang = st.selectbox("Language", ["FR", "EN"], label_visibility="collapsed")

T = TRANSLATIONS.get(selected_lang, TRANSLATIONS["EN"])

st.markdown(f'<div class="main-title">{T["title"]}</div>', unsafe_allow_html=True)

# --- FORMULAIRE ---
with st.form("search_form"):
    c1, c2, c3 = st.columns([4, 1, 1], gap="small")
    with c1:
        riot_id_input = st.text_input("Riot ID", placeholder=T["placeholder"])
        st.markdown(f'<a href="https://dpm.lol" target="_blank" class="dpm-button">{T["dpm_btn"]}</a>', unsafe_allow_html=True)
    with c2:
        region_select = st.selectbox("Region", ["EUW1", "NA1", "KR", "EUN1", "TR1"])
    with c3:
        # Option pour chercher en Flex si pas de SoloQ
        queue_type = st.selectbox("Mode", ["Solo/Duo", "Flex"], index=0)
    
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

def render_stat_row(label, val, diff, unit=""):
    if diff > 0: diff_html = f"<span class='stat-diff pos'>+{round(diff, 1)}{unit}</span>"
    elif diff < 0: diff_html = f"<span class='stat-diff neg'>{round(diff, 1)}{unit}</span>"
    else: diff_html = f"<span class='stat-diff neutral'>=</span>"

    val_display = f"{val}{unit}"
    if isinstance(val, int) and val > 1000: val_display = f"{val/1000:.1f}k"

    st.markdown(f"""<div class="stat-row"><div class="stat-label">{label}</div><div style="display:flex; align-items:baseline;"><div class="stat-value">{val_display}</div>{diff_html}</div></div>""", unsafe_allow_html=True)

# --- CACHED FUNCTIONS ---
@st.cache_data(ttl=600)
def get_puuid_from_api(name, tag, region, api_key):
    url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={api_key}"
    return requests.get(url)

# Cache plus court pour les matchs (2min) pour éviter le blocage "0 games"
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
        st.error("⚠️ Format invalide/Invalid format (Name#TAG)")
    else:
        name_raw, tag = riot_id_input.split("#")
        name_encoded = quote(name_raw)
        region = get_regions(region_select)
        
        # Queue ID Map
        q_id = 420 if queue_type == "Solo/Duo" else 440
        
        with st.spinner(T["loading"]):
            try:
                # 1. PUUID
                resp_acc = get_puuid_from_api(name_encoded, tag, region, API_KEY)
                if resp_acc.status_code != 200:
                    st.error(f"Player not found / Joueur introuvable (Error {resp_acc.status_code})")
                    st.stop()
                puuid = resp_acc.json().get("puuid")

                # 2. MATCH IDs
                resp_matches = get_matches_from_api(puuid, region, API_KEY, q_id)
                match_ids = resp_matches.json()
                
                if not match_ids:
                    # Message d'erreur personnalisé
                    st.warning(f"⚠️ {T['error_no_games']}")
                    st.info(f"💡 {T['error_hint']} ({queue_type})")
                    st.stop()
                    
            except Exception as e:
                st.error(f"API Error: {e}")
                st.stop()

            # 2. ANALYSIS
            duo_data = {} 
            target_name = riot_id_input 
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_match = {executor.submit(fetch_match_detail, m_id, region, API_KEY): m_id for m_id in match_ids}
                
                for future in concurrent.futures.as_completed(future_to_match):
                    try:
                        data = future.result()
                        if 'info' not in data: continue
                        participants = data['info']['participants']
                        me = next((p for p in participants if p['puuid'] == puuid), None)
                        
                        if me:
                            target_name = me.get('riotIdGameName', name_raw)
                            my_s = {
                                'kda': (me['kills'] + me['assists']) / max(1, me['deaths']),
                                'dmg': me['totalDamageDealtToChampions'],
                                'gold': me['goldEarned'],
                                'vis': me['visionScore'],
                                'obj': me.get('damageDealtToObjectives', 0),
                                'towers': me.get('challenges', {}).get('turretTakedowns', 0),
                                'champ': me['championName']
                            }

                            for p in participants:
                                if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                                    full_id = f"{p.get('riotIdGameName')}#{p.get('riotIdTagLine')}"
                                    if full_id not in duo_data:
                                        duo_data[full_id] = {
                                            'name': p.get('riotIdGameName'), 'games': 0, 'wins': 0,
                                            'stats': {'kda':0, 'dmg':0, 'gold':0, 'vis':0, 'obj':0, 'towers':0},
                                            'my_stats_vs': {'kda':0, 'dmg':0, 'gold':0, 'vis':0, 'obj':0, 'towers':0},
                                            'champs': [], 'my_champs': []    
                                        }
                                    d = duo_data[full_id]
                                    d['games'] += 1
                                    if p['win']: d['wins'] += 1
                                    d['champs'].append(p['championName'])
                                    d['my_champs'].append(my_s['champ'])
                                    
                                    d['stats']['kda'] += (p['kills'] + p['assists']) / max(1, p['deaths'])
                                    d['stats']['dmg'] += p['totalDamageDealtToChampions']
                                    d['stats']['gold'] += p['goldEarned']
                                    d['stats']['vis'] += p['visionScore']
                                    d['stats']['obj'] += p.get('damageDealtToObjectives', 0)
                                    d['stats']['towers'] += p.get('challenges', {}).get('turretTakedowns', 0)
                                    
                                    d['my_stats_vs']['kda'] += my_s['kda']
                                    d['my_stats_vs']['dmg'] += my_s['dmg']
                                    d['my_stats_vs']['gold'] += my_s['gold']
                                    d['my_stats_vs']['vis'] += my_s['vis']
                                    d['my_stats_vs']['obj'] += my_s['obj']
                                    d['my_stats_vs']['towers'] += my_s['towers']
                    except: pass 

            # 3. VERDICT
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
                
                def avg(d, key): return int(d[key] / g)
                def avg_f(d, key): return round(d[key] / g, 2)
                
                s_me = best_duo['my_stats_vs']
                s_duo = best_duo['stats']
                
                score_combat_me = (s_me['kda'] * 2) + (s_me['dmg'] / 1000)
                score_combat_duo = (s_duo['kda'] * 2) + (s_duo['dmg'] / 1000)
                score_eco_me = s_me['gold']
                score_eco_duo = s_duo['gold']
                score_vis_me = s_me['vis']
                score_vis_duo = s_duo['vis']
                score_obj_me = s_me['obj'] + (s_me['towers'] * 2000)
                score_obj_duo = s_duo['obj'] + (s_duo['towers'] * 2000)
                
                def check_win(m, d):
                    if m > d * 1.1: return 1, 0
                    if d > m * 1.1: return 0, 1
                    return 0, 0
                
                w1, d1 = check_win(score_combat_me, score_combat_duo)
                w2, d2 = check_win(score_eco_me, score_eco_duo)
                w3, d3 = check_win(score_vis_me, score_vis_duo)
                w4, d4 = check_win(score_obj_me, score_obj_duo)
                
                my_wins = w1 + w2 + w3 + w4
                duo_wins = d1 + d2 + d3 + d4
                
                status = "EQUAL"
                if duo_wins >= my_wins + 2: status = "BOOSTED"
                elif my_wins >= duo_wins + 2: status = "BOOSTER"
                
                winrate = int((best_duo['wins']/g)*100)

                # --- DISPLAY ---
                st.markdown("<br>", unsafe_allow_html=True)
                
                if status == "BOOSTED":
                    header_color = "#ff4444"
                    title_text = T["verdict_boosted"]
                    sub_text = T["sub_boosted"].format(target=target_name, duo=duo_name)
                    if "http" in CLOWN_IMAGE_URL:
                        c1, c2, c3 = st.columns([1, 1, 1])
                        with c2: st.image(CLOWN_IMAGE_URL, use_column_width=True)

                elif status == "BOOSTER":
                    header_color = "#FFD700"
                    title_text = T["verdict_booster"]
                    sub_text = T["sub_booster"].format(target=target_name, duo=duo_name)
                else:
                    header_color = "#00ff99"
                    title_text = T["verdict_clean"]
                    sub_text = T["sub_clean"]

                st.markdown(f"""
                <div class="verdict-banner" style="border-color:{header_color}">
                    <div style="font-size:48px; font-weight:900; color:{header_color}; margin-bottom:10px;">{title_text}</div>
                    <div style="font-size:20px; color:#ddd;">{sub_text}</div>
                    <div style="margin-top:20px; font-size:16px; color:#888;">{g} Games • {winrate}% Winrate</div>
                </div>
                """, unsafe_allow_html=True)

                # --- PANELS ---
                col_left, col_mid, col_right = st.columns([10, 1, 10]) 
                
                with col_left:
                    r = T["role_driver"] if status=='BOOSTER' else (T["role_pass"] if status=='BOOSTED' else T["role_equal"])
                    c = 'role-driver' if status=='BOOSTER' else ('role-pass' if status=='BOOSTED' else 'role-equal')
                    st.markdown(f"""
                    <div class="player-panel">
                        <div class="panel-header" style="border-color:{header_color if status=='BOOSTER' else '#333'}">
                            <div class="player-name">{target_name}</div>
                            <div class="player-role {c}">{r}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    top_champs = [c[0] for c in Counter(best_duo['my_champs']).most_common(3)]
                    html_champs = "<div class='champ-row' style='justify-content:center;'>"
                    for ch in top_champs: html_champs += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
                    html_champs += "</div>"
                    st.markdown(html_champs, unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center; color:#888; margin-bottom:15px'>{T['stats']} {target_name}</div>", unsafe_allow_html=True)
                    render_stat_row("KDA", avg_f(s_me, 'kda'), avg_f(s_me, 'kda') - avg_f(s_duo, 'kda'))
                    render_stat_row("Damage", avg(s_me, 'dmg'), avg(s_me, 'dmg') - avg(s_duo, 'dmg'))
                    render_stat_row("Gold", avg(s_me, 'gold'), avg(s_me, 'gold') - avg(s_duo, 'gold'))
                    render_stat_row("Vision", avg(s_me, 'vis'), avg(s_me, 'vis') - avg(s_duo, 'vis'))
                    render_stat_row("Obj Dmg", avg(s_me, 'obj'), avg(s_me, 'obj') - avg(s_duo, 'obj'))
                    render_stat_row("Towers", avg_f(s_me, 'towers'), avg_f(s_me, 'towers') - avg_f(s_duo, 'towers'))
                    st.markdown("</div>", unsafe_allow_html=True)

                with col_right:
                    r = T["role_driver"] if status=='BOOSTED' else (T["role_pass"] if status=='BOOSTER' else T["role_equal"])
                    c = 'role-driver' if status=='BOOSTED' else ('role-pass' if status=='BOOSTER' else 'role-equal')
                    st.markdown(f"""
                    <div class="player-panel">
                        <div class="panel-header" style="border-color:{header_color if status=='BOOSTED' else '#333'}">
                            <div class="player-name">{duo_name}</div>
                            <div class="player-role {c}">{r}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    top_champs_duo = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                    html_champs_d = "<div class='champ-row' style='justify-content:center;'>"
                    for ch in top_champs_duo: html_champs_d += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
                    html_champs_d += "</div>"
                    st.markdown(html_champs_d, unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center; color:#888; margin-bottom:15px'>{T['stats']} {duo_name}</div>", unsafe_allow_html=True)
                    render_stat_row("KDA", avg_f(s_duo, 'kda'), avg_f(s_duo, 'kda') - avg_f(s_me, 'kda'))
                    render_stat_row("Damage", avg(s_duo, 'dmg'), avg(s_duo, 'dmg') - avg(s_me, 'dmg'))
                    render_stat_row("Gold", avg(s_duo, 'gold'), avg(s_duo, 'gold') - avg(s_me, 'gold'))
                    render_stat_row("Vision", avg(s_duo, 'vis'), avg(s_duo, 'vis') - avg(s_me, 'vis'))
                    render_stat_row("Obj Dmg", avg(s_duo, 'obj'), avg(s_duo, 'obj') - avg(s_me, 'obj'))
                    render_stat_row("Towers", avg_f(s_duo, 'towers'), avg_f(s_duo, 'towers') - avg_f(s_me, 'towers'))
                    st.markdown("</div>", unsafe_allow_html=True)

            else:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="verdict-banner" style="border-color:#00ff99">
                    <div style="font-size:32px; font-weight:900; color:#00ff99;">{T["solo"]}</div>
                    <div style="font-size:18px; color:#ddd; margin-top:10px;">{T["solo_sub"]}</div>
                </div>
                """, unsafe_allow_html=True)
