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

# --- TRADUCTIONS (STANDARDISÉES - PLUS D'ERREUR) ---
TRANSLATIONS = {
    "FR": {
        "title": "LoL Duo Analyst",
        "btn_scan": "LANCER L'ANALYSE",
        "placeholder": "Exemple: Sardoche#EUW",
        "dpm_btn": "🔗 Voir sur dpm.lol",
        
        # Verdicts
        "verdict_boosted": "PASSAGER DÉTECTÉ",
        "sub_boosted": "{target} se fait carry par {duo}",
        "verdict_protected": "SOUTIEN TACTIQUE",
        "sub_protected": "{target} aide, mais {duo} fait le gros du travail",
        "verdict_booster": "CHAUFFEUR DÉTECTÉ",
        "sub_booster": "{target} booste {duo}",
        "verdict_hyper": "CHEF DE GUERRE",
        "sub_hyper": "{target} porte la game (1v9)",
        "verdict_clean": "DUO D'ÉLITE",
        "sub_clean": "Synergie et contribution égales",

        "solo": "LOUP SOLITAIRE",
        "solo_sub": "Aucun duo récurrent sur 20 parties.",
        "loading": "Analyse tactique en cours...",
        
        # Rôles (clés strictes)
        "role_mvp": "MVP",
        "role_leader": "LEADER",
        "role_equal": "PARTENAIRE",
        "role_supp": "SOUTIEN",
        "role_diff": "VIP",

        "stats": "PERF DE",
        "combat": "COMBAT",
        "eco": "ÉCONOMIE",
        "vision": "VISION & MAP",
        "error_no_games": "Aucune partie trouvée.",
        "error_hint": "Vérifie la région."
    },
    "EN": {
        "title": "LoL Duo Analyst",
        "btn_scan": "START ANALYSIS",
        "placeholder": "Example: Faker#KR1",
        "dpm_btn": "🔗 Check dpm.lol",
        
        "verdict_boosted": "PASSENGER DETECTED",
        "sub_boosted": "{target} is carried by {duo}",
        "verdict_protected": "TACTICAL SUPPORT",
        "sub_protected": "{target} helps, but {duo} leads",
        "verdict_booster": "DRIVER DETECTED",
        "sub_booster": "{target} is boosting {duo}",
        "verdict_hyper": "WARLORD",
        "sub_hyper": "{target} is 1v9 hard carrying",
        "verdict_clean": "ELITE DUO",
        "sub_clean": "Perfect Synergy",

        "solo": "LONE WOLF",
        "solo_sub": "No recurring partner found.",
        "loading": "Tactical analysis in progress...",
        
        "role_mvp": "MVP",
        "role_leader": "LEADER",
        "role_equal": "PARTNER",
        "role_supp": "SUPPORT",
        "role_diff": "VIP",
        
        "stats": "STATS FOR",
        "combat": "COMBAT",
        "eco": "ECONOMY",
        "vision": "VISION & MAP",
        "error_no_games": "No games found.",
        "error_hint": "Check Region."
    },
    "ES": {
        "title": "Analista LoL",
        "btn_scan": "ANALIZAR",
        "placeholder": "Ejemplo: Ibai#EUW",
        "dpm_btn": "Ver dpm.lol",
        
        "verdict_boosted": "PASAJERO",
        "sub_boosted": "{target} es carrileado por {duo}",
        "verdict_protected": "ESCUDERO",
        "sub_protected": "{target} ayuda, {duo} domina",
        "verdict_booster": "CONDUCTOR",
        "sub_booster": "{target} carrilea a {duo}",
        "verdict_hyper": "JEFIO",
        "sub_hyper": "{target} hace 1v9",
        "verdict_clean": "DUO DE ELITE",
        "sub_clean": "Sinergia perfecta",

        "solo": "SOLO",
        "solo_sub": "Sin duo recurrente",
        "loading": "Cargando...",
        
        "role_mvp": "MVP",
        "role_leader": "LIDER",
        "role_equal": "SOCIO",
        "role_supp": "APOYO",
        "role_diff": "VIP",
        
        "stats": "ESTADISTICAS",
        "combat": "COMBATE",
        "eco": "ECONOMIA",
        "vision": "VISION",
        "error_no_games": "Sin partidas",
        "error_hint": "Region?"
    },
    "KR": {
        "title": "LoL 듀오 분석",
        "btn_scan": "분석 시작",
        "placeholder": "예: Hide on bush#KR1",
        "dpm_btn": "dpm.lol 확인",
        
        "verdict_boosted": "버스 승객",
        "sub_boosted": "{target} 님이 업혀갑니다",
        "verdict_protected": "서포터",
        "sub_protected": "{target} 님은 조력자입니다",
        "verdict_booster": "버스 기사",
        "sub_booster": "{target} 님이 캐리 중입니다",
        "verdict_hyper": "하드 캐리",
        "sub_hyper": "{target} 님이 지배 중입니다",
        "verdict_clean": "완벽한 듀오",
        "sub_clean": "동등한 실력",

        "solo": "솔로",
        "solo_sub": "듀오 없음",
        "loading": "분석 중...",
        
        "role_mvp": "MVP",
        "role_leader": "리더",
        "role_equal": "파트너",
        "role_supp": "서포터",
        "role_diff": "승객",
        
        "stats": "통계",
        "combat": "전투",
        "eco": "경제",
        "vision": "시야",
        "error_no_games": "게임 없음",
        "error_hint": "지역 확인"
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
        background-color: rgba(37, 99, 235, 0.2); color: #60a5fa !important;
        height: 46px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px;
        border: 1px solid #2563eb; margin-top: 28px; transition: 0.2s;
    }}
    .dpm-button-small:hover {{ background-color: #2563eb; color: white !important; }}

    .player-panel {{ background: rgba(255, 255, 255, 0.03); border-radius: 16px; padding: 20px; height: 100%; border: 1px solid rgba(255,255,255,0.05); }}
    
    .player-name {{ font-size: 28px; font-weight: 900; color: white; text-align: center; margin-bottom: 5px; }}
    .player-role {{ font-size: 14px; font-weight: 700; text-align: center; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; padding: 5px; border-radius: 4px; background: rgba(255,255,255,0.05); }}
    
    /* ROLE COLORS */
    .color-gold {{ color: #FFD700; border-color: #FFD700; }}
    .color-blue {{ color: #00BFFF; border-color: #00BFFF; }}
    .color-green {{ color: #00ff99; border-color: #00ff99; }}
    .color-orange {{ color: #FFA500; border-color: #FFA500; }}
    .color-red {{ color: #ff4444; border-color: #ff4444; }}

    /* STATS LIST */
    .stat-section-title {{ font-size: 11px; color: #666; font-weight: 800; letter-spacing: 1px; margin-top: 15px; margin-bottom: 5px; }}
    
    .stat-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }}
    .stat-label {{ font-size: 13px; color: #aaa; font-weight: 600; }}
    .stat-value {{ font-size: 18px; color: white; font-weight: 700; }}
    .stat-diff {{ font-size: 11px; font-weight: 600; margin-left: 6px; padding: 2px 4px; border-radius: 3px; }}
    
    .pos {{ color: #00ff99; background: rgba(0,255,153,0.1); }}
    .neg {{ color: #ff4444; background: rgba(255,68,68,0.1); }}
    .neutral {{ color: #666; }}

    .verdict-banner {{ text-align: center; padding: 30px; margin-bottom: 40px; border-radius: 16px; background: rgba(0,0,0,0.4); border: 1px solid #333; }}

    .stButton > button {{
        width: 100%; height: 50px; background: linear-gradient(90deg, #ff0055, #ff2222);
        color: white; font-size: 18px; font-weight: 700; border: none; border-radius: 8px;
        text-transform: uppercase; transition: 0.2s;
    }}
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 20px rgba(255,0,85,0.3); }}
    
    .champ-img {{ width: 50px; height: 50px; border-radius: 50%; border: 2px solid #333; margin: 0 4px; }}
    p, label {{ color: #eee !important; font-weight: 600; font-size: 13px; }}
    </style>
    """, unsafe_allow_html=True
)

# --- HEADER & LANGUAGE ---
c_title, c_lang = st.columns([5, 1])
with c_lang:
    selected_lang = st.selectbox("Lang", ["FR", "EN", "ES", "KR"], label_visibility="collapsed")
T = TRANSLATIONS[selected_lang]

st.markdown(f'<div class="main-title">{T["title"]}</div>', unsafe_allow_html=True)

# --- FORMULAIRE ---
with st.form("search_form"):
    c1, c2, c3, c4 = st.columns([4, 1.2, 1.2, 1.2], gap="small")
    with c1:
        riot_id_input = st.text_input("Riot ID", placeholder=T["placeholder"])
    with c2:
        st.markdown(f'<a href="https://dpm.lol" target="_blank" class="dpm-button-small">{T["dpm_btn"]}</a>', unsafe_allow_html=True)
    with c3:
        region_select = st.selectbox("Region", ["EUW1", "NA1", "KR", "EUN1", "TR1"])
    with c4:
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
    
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-label">{label}</div>
        <div style="display:flex; align-items:center;">
            <div class="stat-value">{val_display}</div>
            {diff_html}
        </div>
    </div>""", unsafe_allow_html=True)

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
        st.error("⚠️ Format invalide: Name#TAG")
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
                
                # SCORE V29 (Fair-Play)
                def calc_score(s):
                    kda = s['kda'] / g
                    dpm = s['dpm'] / g
                    obj = s['obj'] / g 
                    vis = s['vis'] / g
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

                # AFFICHAGE
                header_color = "#00ff99"
                title_text = T["verdict_clean"]
                sub_text = T["sub_clean"]
                role_me_key, role_me_color = "role_equal", "color-green"
                role_duo_key, role_duo_color = "role_equal", "color-green"

                if state == "BOOSTED_HARD":
                    header_color = "#ff4444"
                    title_text = T["verdict_boosted"]
                    sub_text = T["sub_boosted"].format(target=target_name, duo=duo_name)
                    role_me_key, role_me_color = "role_diff", "color-red"
                    role_duo_key, role_duo_color = "role_mvp", "color-gold"
                    if "http" in CLOWN_IMAGE_URL:
                        c1, c2, c3 = st.columns([1, 1, 1])
                        with c2: st.image(CLOWN_IMAGE_URL, use_column_width=True)

                elif state == "BOOSTED_SOFT":
                    header_color = "#FFA500"
                    title_text = T["verdict_protected"]
                    sub_text = T["sub_protected"].format(target=target_name, duo=duo_name)
                    role_me_key, role_me_color = "role_supp", "color-orange"
                    role_duo_key, role_duo_color = "role_leader", "color-blue"

                elif state == "BOOSTER_HARD":
                    header_color = "#FFD700"
                    title_text = T["verdict_hyper"]
                    sub_text = T["sub_hyper"].format(target=target_name)
                    role_me_key, role_me_color = "role_mvp", "color-gold"
                    role_duo_key, role_duo_color = "role_diff", "color-red"

                elif state == "BOOSTER_SOFT":
                    header_color = "#00BFFF"
                    title_text = T["verdict_booster"]
                    sub_text = T["sub_booster"].format(target=target_name, duo=duo_name)
                    role_me_key, role_me_color = "role_leader", "color-blue"
                    role_duo_key, role_duo_color = "role_supp", "color-orange"

                st.markdown(f"""
                <div class="verdict-banner" style="border-color:{header_color}">
                    <div style="font-size:42px; font-weight:900; color:{header_color}; margin-bottom:10px;">{title_text}</div>
                    <div style="font-size:18px; color:#ddd;">{sub_text}</div>
                    <div style="margin-top:15px; font-size:14px; color:#888;">{g} Games • {winrate}% Winrate</div>
                </div>
                """, unsafe_allow_html=True)

                # PANNEAUX
                col_left, col_right = st.columns(2, gap="large")
                
                with col_left:
                    st.markdown(f"""
                    <div class="player-panel">
                        <div class="player-name">{target_name}</div>
                        <div class="player-role {role_me_color}">{T[role_me_key]}</div>
                    """, unsafe_allow_html=True)
                    top_champs = [c[0] for c in Counter(best_duo['my_champs']).most_common(3)]
                    html_champs = "<div class='champ-row' style='justify-content:center; margin-bottom:20px;'>"
                    for ch in top_champs: html_champs += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
                    html_champs += "</div>"
                    st.markdown(html_champs, unsafe_allow_html=True)
                    st.markdown(f"<div class='stat-section-title'>{T['combat']}</div>", unsafe_allow_html=True)
                    render_stat_row("KDA", avg_f(s_me, 'kda'), avg_f(s_me, 'kda') - avg_f(s_duo, 'kda'))
                    render_stat_row("DPM", avg(s_me, 'dpm'), avg(s_me, 'dpm') - avg(s_duo, 'dpm'))
                    st.markdown(f"<div class='stat-section-title'>{T['eco']} / {T['vision']}</div>", unsafe_allow_html=True)
                    render_stat_row("GOLD", avg(s_me, 'gold'), avg(s_me, 'gold') - avg(s_duo, 'gold'))
                    render_stat_row("VISION", avg(s_me, 'vis'), avg(s_me, 'vis') - avg(s_duo, 'vis'))
                    st.markdown(f"<div class='stat-section-title'>OBJECTIVES</div>", unsafe_allow_html=True)
                    render_stat_row("OBJ DMG", avg(s_me, 'obj'), avg(s_me, 'obj') - avg(s_duo, 'obj'))
                    render_stat_row("TOWERS", avg_f(s_me, 'towers'), avg_f(s_me, 'towers') - avg_f(s_duo, 'towers'))
                    st.markdown("</div>", unsafe_allow_html=True)

                with col_right:
                    st.markdown(f"""
                    <div class="player-panel">
                        <div class="player-name">{duo_name}</div>
                        <div class="player-role {role_duo_color}">{T[role_duo_key]}</div>
                    """, unsafe_allow_html=True)
                    top_champs_duo = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                    html_champs_d = "<div class='champ-row' style='justify-content:center; margin-bottom:20px;'>"
                    for ch in top_champs_duo: html_champs_d += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
                    html_champs_d += "</div>"
                    st.markdown(html_champs_d, unsafe_allow_html=True)
                    st.markdown(f"<div class='stat-section-title'>{T['combat']}</div>", unsafe_allow_html=True)
                    render_stat_row("KDA", avg_f(s_duo, 'kda'), avg_f(s_duo, 'kda') - avg_f(s_me, 'kda'))
                    render_stat_row("DPM", avg(s_duo, 'dpm'), avg(s_duo, 'dpm') - avg(s_me, 'dpm'))
                    st.markdown(f"<div class='stat-section-title'>{T['eco']} / {T['vision']}</div>", unsafe_allow_html=True)
                    render_stat_row("GOLD", avg(s_duo, 'gold'), avg(s_duo, 'gold') - avg(s_me, 'gold'))
                    render_stat_row("VISION", avg(s_duo, 'vis'), avg(s_duo, 'vis') - avg(s_me, 'vis'))
                    st.markdown(f"<div class='stat-section-title'>OBJECTIVES</div>", unsafe_allow_html=True)
                    render_stat_row("OBJ DMG", avg(s_duo, 'obj'), avg(s_duo, 'obj') - avg(s_me, 'obj'))
                    render_stat_row("TOWERS", avg_f(s_duo, 'towers'), avg_f(s_duo, 'towers') - avg_f(s_me, 'towers'))
                    st.markdown("</div>", unsafe_allow_html=True)

            else:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="verdict-banner" style="border-color:#00ff99">
                    <div style="font-size:32px; font-weight:900; color:#00ff99;">{T["solo"]}</div>
                    <div style="font-size:18px; color:#ddd; margin-top:10px;">{T["solo_sub"]}</div>
                </div>
                """, unsafe_allow_html=True)
