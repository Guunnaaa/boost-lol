import streamlit as st
import requests
import time
from urllib.parse import quote
from collections import Counter
import concurrent.futures

# --- CONFIGURATION ---
st.set_page_config(page_title="LoL Duo Investigator V30", layout="wide")

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

# --- TRADUCTIONS COMPLÈTES (CORRECTIF KEYERROR) ---
TRANSLATIONS = {
    "FR": {
        "title": "LoL Duo Investigator",
        "btn_scan": "LANCER L'ANALYSE",
        "placeholder": "Exemple: Sardoche#EUW",
        "dpm_btn": "🔗 Voir sur dpm.lol",
        
        # Clés Verdicts
        "v_hyper": "CHEF DE GUERRE",
        "s_hyper": "{target} porte la game sur ses épaules",
        "v_carry": "LEADER TACTIQUE",
        "s_carry": "{target} mène, {duo} suit le rythme",
        "v_solid": "DUO D'ÉLITE",
        "s_solid": "Synergie et contribution égales",
        "v_protected": "SOUTIEN ACTIF",
        "s_protected": "{target} contribue (Obj/KDA) mais {duo} domine",
        "v_passenger": "TOURISTE VIP",
        "s_passenger": "{target} se fait totalement carry par {duo}",

        "solo": "LOUP SOLITAIRE",
        "solo_sub": "Aucun duo récurrent sur 20 parties.",
        "loading": "Analyse tactique en cours...",
        
        # Rôles
        "role_hyper": "BOSS",
        "role_carry": "LEADER",
        "role_solid": "PARTNER",
        "role_protected": "PROTÉGÉ",
        "role_passenger": "VIP",
        
        "stats": "PERF DE",
        "combat": "COMBAT",
        "eco": "ÉCONOMIE",
        "vision": "VISION",
        "error_no_games": "Aucune partie trouvée.",
        "error_hint": "Vérifie la région."
    },
    "EN": {
        "title": "LoL Duo Investigator",
        "btn_scan": "START SCAN",
        "placeholder": "Example: Faker#KR1",
        "dpm_btn": "🔗 Check dpm.lol",
        
        "v_hyper": "WARLORD",
        "s_hyper": "{target} is hard carrying the game",
        "v_carry": "TACTICAL LEADER",
        "s_carry": "{target} leads, {duo} follows",
        "v_solid": "ELITE DUO",
        "s_solid": "Perfect Synergy",
        "v_protected": "ACTIVE SUPPORT",
        "s_protected": "{target} helps (Obj/KDA) but {duo} dominates",
        "v_passenger": "VIP PASSENGER",
        "s_passenger": "{target} is heavily carried by {duo}",

        "solo": "LONE WOLF",
        "solo_sub": "No recurring partner found.",
        "loading": "Tactical analysis in progress...",
        
        "role_hyper": "BOSS",
        "role_carry": "LEADER",
        "role_solid": "PARTNER",
        "role_protected": "PROTÉGÉ",
        "role_passenger": "VIP",
        
        "stats": "STATS FOR",
        "combat": "COMBAT",
        "eco": "ECONOMY",
        "vision": "VISION",
        "error_no_games": "No games found.",
        "error_hint": "Check Region."
    },
    "ES": {
        "title": "Detector LoL",
        "btn_scan": "ANALIZAR",
        "placeholder": "Ejemplo: Ibai#EUW",
        "dpm_btn": "Ver dpm.lol",
        "v_hyper": "GENERAL", "s_hyper": "{target} carrilea fuerte",
        "v_carry": "LIDER", "s_carry": "{target} lidera, {duo} sigue",
        "v_solid": "DUO SÓLIDO", "s_solid": "Contribución igual",
        "v_protected": "ESCUDERO", "s_protected": "{target} ayuda pero {duo} domina",
        "v_passenger": "TURISTA", "s_passenger": "{target} es carrileado totalmente",
        "solo": "SOLO", "solo_sub": "Sin duo",
        "loading": "Cargando...",
        "role_hyper": "BOSS", "role_carry": "LIDER", "role_solid": "SOCIO", "role_protected": "AYUDA", "role_passenger": "VIP",
        "stats": "STATS", "combat":"COMBATE", "eco":"ECONOMIA", "vision":"VISION", "error_no_games":"No partidas", "error_hint":"Region?"
    },
    "KR": {
        "title": "LoL 듀오 분석",
        "btn_scan": "분석 시작",
        "placeholder": "예: Hide on bush#KR1",
        "dpm_btn": "dpm.lol 확인",
        "v_hyper": "하드 캐리", "s_hyper": "{target} 님이 캐리 중",
        "v_carry": "리더", "s_carry": "{target} 리드, {duo} 서포트",
        "v_solid": "완벽 듀오", "s_solid": "동등한 실력",
        "v_protected": "서포터", "s_protected": "{target} 도움, {duo} 지배",
        "v_passenger": "버스 승객", "s_passenger": "{target} 님이 업혀갑니다",
        "solo": "솔로", "solo_sub": "듀오 없음",
        "loading": "분석 중...",
        "role_hyper": "대장", "role_carry": "리더", "role_solid": "파트너", "role_protected": "보호", "role_passenger": "승객",
        "stats": "통계", "combat":"전투", "eco":"경제", "vision":"시야", "error_no_games":"게임 없음", "error_hint":"지역 확인"
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
        font-size: 60px; font-weight: 900; color: white; text-align: center; margin-bottom: 20px;
        text-transform: uppercase; letter-spacing: -2px;
        background: -webkit-linear-gradient(#eee, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    
    .dpm-button-small {{
        display: flex; align-items: center; justify-content: center;
        background-color: #2563eb; color: white !important;
        height: 46px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px;
        border: 1px solid #1d4ed8; margin-top: 28px; transition: 0.2s;
    }}
    .dpm-button-small:hover {{ background-color: #1d4ed8; transform: translateY(-1px); box-shadow: 0 4px 10px rgba(37,99,235,0.4); }}

    .player-panel {{ background: rgba(255, 255, 255, 0.03); border-radius: 20px; padding: 25px; height: 100%; border: 1px solid rgba(255,255,255,0.05); }}
    .panel-header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 15px; margin-bottom: 15px; }}
    .player-name {{ font-size: 32px; font-weight: 900; color: white; margin-bottom: 5px; }}
    .player-role {{ font-size: 16px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; }}
    
    /* NEW ROLES COLORS */
    .r-hyper {{ color: #FFD700; }} /* Gold */
    .r-carry {{ color: #00BFFF; }} /* Deep Sky Blue */
    .r-solid {{ color: #00ff99; }} /* Green */
    .r-prot {{ color: #FFA500; }} /* Orange */
    .r-pass {{ color: #ff4444; }} /* Red */

    .stat-row {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
    .stat-label {{ font-size: 14px; color: #888; font-weight: 600; text-transform: uppercase; }}
    .stat-value {{ font-size: 20px; color: white; font-weight: 800; }}
    .stat-diff {{ font-size: 12px; font-weight: 600; margin-left: 8px; }}
    .pos {{ color: #00ff99; }} .neg {{ color: #ff4444; }} .neutral {{ color: #666; }}

    .verdict-banner {{ text-align: center; padding: 30px; margin-bottom: 40px; border-radius: 20px; background: rgba(0,0,0,0.3); border: 2px solid #333; }}

    .stButton > button {{
        width: 100%; height: 60px; background: linear-gradient(90deg, #ff0055, #ff2222);
        color: white; font-size: 20px; font-weight: 800; border: none; border-radius: 12px;
        text-transform: uppercase; transition: 0.2s; letter-spacing: 1px;
    }}
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 30px rgba(255,0,85,0.4); }}
    
    .champ-img {{ width: 60px; height: 60px; border-radius: 50%; border: 2px solid #444; margin: 0 5px; }}
    p, label {{ color: #eee !important; font-weight: 600; font-size: 14px; }}
    </style>
    """, unsafe_allow_html=True
)

# --- HEADER & LANGUAGE ---
c_title, c_lang = st.columns([5, 1])
with c_lang:
    selected_lang = st.selectbox("Language", ["FR", "EN", "ES", "KR"], label_visibility="collapsed")

T = TRANSLATIONS[selected_lang]

st.markdown(f'<div class="main-title">{T["title"]}</div>', unsafe_allow_html=True)

# --- FORMULAIRE ---
with st.form("search_form"):
    c_input, c_dpm, c_reg, c_mode, c_lang = st.columns([4, 1.2, 1.2, 1.2, 1], gap="small")
    with c_lang:
        # Hack invisible pour garder l'alignement
        st.write("")
    with c_input:
        riot_id_input = st.text_input("Riot ID", placeholder=T["placeholder"])
    with c_dpm:
        st.markdown(f'<a href="https://dpm.lol" target="_blank" class="dpm-button-small">{T["dpm_btn"]}</a>', unsafe_allow_html=True)
    with c_reg:
        region_select = st.selectbox("Region", ["EUW1", "NA1", "KR", "EUN1", "TR1"])
    with c_mode:
        queue_type = st.selectbox("Mode", ["Solo/Duo", "Flex"])
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
        st.error("⚠️ Format invalid: Name#TAG")
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

            # 2. ANALYSIS
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
                                    'gold': p['goldEarned'],
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
                
                def avg_f(d, key): return round(d[key] / g, 2)
                def avg(d, key): return int(d[key] / g)
                
                s_me = best_duo['my_stats_vs']
                s_duo = best_duo['stats']
                
                def calc_score(s):
                    kda = s['kda'] / g
                    dpm = s['dpm'] / g
                    obj = s['obj'] / g
                    vis = s['vis'] / g
                    score = (kda * 100) + (dpm * 0.5) + (obj * 0.15) + (vis * 10)
                    return score

                score_me = calc_score(s_me)
                score_duo = calc_score(s_duo)
                ratio = score_me / max(1, score_duo)
                
                if ratio > 1.3: state = "BOOSTER_HARD" 
                elif ratio > 1.1: state = "BOOSTER_SOFT" 
                elif ratio < 0.7: state = "BOOSTED_HARD" 
                elif ratio < 0.9: state = "BOOSTED_SOFT" 
                else: state = "EQUAL"

                winrate = int((best_duo['wins']/g)*100)

                # --- CONFIGURATION AFFICHAGE ---
                # Default (Equal)
                header_color = "#00ff99"
                title_text = T["v_solid"]
                sub_text = T["s_solid"]
                role_me, role_duo = "r-solid", "r-solid"
                name_me, name_duo = T["role_solid"], T["role_solid"]

                if state == "BOOSTED_HARD":
                    header_color = "#ff4444"
                    title_text = T["v_passenger"] # Utilisez v_passenger (TOURISTE) pas verdict_boosted
                    sub_text = T["s_passenger"].format(target=target_name, duo=duo_name)
                    role_me, role_duo = "r-pass", "r-hyper"
                    name_me, name_duo = T["role_passenger"], T["role_hyper"]
                    if "http" in CLOWN_IMAGE_URL:
                        c1, c2, c3 = st.columns([1, 1, 1])
                        with c2: st.image(CLOWN_IMAGE_URL, use_column_width=True)

                elif state == "BOOSTED_SOFT":
                    header_color = "#FFA500"
                    title_text = T["v_protected"]
                    sub_text = T["s_protected"].format(target=target_name, duo=duo_name)
                    role_me, role_duo = "r-prot", "r-carry"
                    name_me, name_duo = T["role_protected"], T["role_carry"]

                elif state == "BOOSTER_HARD":
                    header_color = "#FFD700"
                    title_text = T["v_hyper"]
                    sub_text = T["s_hyper"].format(target=target_name)
                    role_me, role_duo = "r-hyper", "r-pass"
                    name_me, name_duo = T["role_hyper"], T["role_passenger"]

                elif state == "BOOSTER_SOFT":
                    header_color = "#00BFFF"
                    title_text = T["v_carry"]
                    sub_text = T["s_carry"].format(target=target_name, duo=duo_name)
                    role_me, role_duo = "r-carry", "r-prot"
                    name_me, name_duo = T["role_carry"], T["role_protected"]

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
                    st.markdown(f"""
                    <div class="player-panel">
                        <div class="panel-header" style="border-color:{header_color if 'BOOSTER' in state else '#333'}">
                            <div class="player-name">{target_name}</div>
                            <div class="player-role {role_me}">{name_me}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    top_champs = [c[0] for c in Counter(best_duo['my_champs']).most_common(3)]
                    html_champs = "<div class='champ-row' style='justify-content:center;'>"
                    for ch in top_champs: html_champs += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
                    html_champs += "</div>"
                    st.markdown(html_champs, unsafe_allow_html=True)
                    
                    st.markdown(f"<div style='text-align:center; color:#888; margin-bottom:15px'>{T['stats']} {target_name}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='color:#666; font-size:12px; font-weight:bold; margin-top:10px;'>{T['combat']}</div>", unsafe_allow_html=True)
                    render_stat_row("KDA", avg_f(s_me, 'kda'), avg_f(s_me, 'kda') - avg_f(s_duo, 'kda'))
                    render_stat_row("DPM", avg(s_me, 'dpm'), avg(s_me, 'dpm') - avg(s_duo, 'dpm'))
                    st.markdown(f"<div style='color:#666; font-size:12px; font-weight:bold; margin-top:15px;'>{T['eco']} / {T['vision']}</div>", unsafe_allow_html=True)
                    render_stat_row("Gold", avg(s_me, 'gold'), avg(s_me, 'gold') - avg(s_duo, 'gold'))
                    render_stat_row("Vision", avg(s_me, 'vis'), avg(s_me, 'vis') - avg(s_duo, 'vis'))
                    st.markdown(f"<div style='color:#666; font-size:12px; font-weight:bold; margin-top:15px;'>OBJECTIVES</div>", unsafe_allow_html=True)
                    render_stat_row("Obj Dmg", avg(s_me, 'obj'), avg(s_me, 'obj') - avg(s_duo, 'obj'))
                    render_stat_row("Towers", avg_f(s_me, 'towers'), avg_f(s_me, 'towers') - avg_f(s_duo, 'towers'))
                    st.markdown("</div>", unsafe_allow_html=True)

                with col_right:
                    st.markdown(f"""
                    <div class="player-panel">
                        <div class="panel-header" style="border-color:{header_color if 'BOOSTED' in state else '#333'}">
                            <div class="player-name">{duo_name}</div>
                            <div class="player-role {role_duo}">{name_duo}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    top_champs_duo = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                    html_champs_d = "<div class='champ-row' style='justify-content:center;'>"
                    for ch in top_champs_duo: html_champs_d += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
                    html_champs_d += "</div>"
                    st.markdown(html_champs_d, unsafe_allow_html=True)
                    
                    st.markdown(f"<div style='text-align:center; color:#888; margin-bottom:15px'>{T['stats']} {duo_name}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='color:#666; font-size:12px; font-weight:bold; margin-top:10px;'>{T['combat']}</div>", unsafe_allow_html=True)
                    render_stat_row("KDA", avg_f(s_duo, 'kda'), avg_f(s_duo, 'kda') - avg_f(s_me, 'kda'))
                    render_stat_row("DPM", avg(s_duo, 'dpm'), avg(s_duo, 'dpm') - avg(s_me, 'dpm'))
                    st.markdown(f"<div style='color:#666; font-size:12px; font-weight:bold; margin-top:15px;'>{T['eco']} / {T['vision']}</div>", unsafe_allow_html=True)
                    render_stat_row("Gold", avg(s_duo, 'gold'), avg(s_duo, 'gold') - avg(s_me, 'gold'))
                    render_stat_row("Vision", avg(s_duo, 'vis'), avg(s_duo, 'vis') - avg(s_me, 'vis'))
                    st.markdown(f"<div style='color:#666; font-size:12px; font-weight:bold; margin-top:15px;'>OBJECTIVES</div>", unsafe_allow_html=True)
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
