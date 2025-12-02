import streamlit as st
import requests
from urllib.parse import quote
from collections import Counter
import concurrent.futures

# --- 1. CONFIGURATION & CONSTANTES ---
st.set_page_config(page_title="LoL Duo Analyst V35", layout="wide")

try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ API Key missing. Add RIOT_API_KEY to Streamlit secrets.")
    st.stop()

ASSETS = {
    "bg": "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123",
    "clown": "https://raw.githubusercontent.com/[YOUR_GITHUB_NAME]/[REPO_NAME]/main/clown.jpg"
}

# --- 2. GESTION DES RESSOURCES & CACHE ---
@st.cache_data(ttl=3600)
def get_dd_version():
    """Récupère la dernière version de LoL pour les images"""
    try: return requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
    except: return "14.23.1"

DD_VERSION = get_dd_version()

def get_champ_url(champ_name):
    """Génère le lien d'image propre pour un champion"""
    if not champ_name: return "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Poro_0.jpg"
    clean = champ_name.replace(" ", "").replace("'", "").replace(".", "")
    mapping = {
        "wukong": "MonkeyKing", "renataglasc": "Renata", "nunu&willump": "Nunu",
        "kogmaw": "KogMaw", "reksai": "RekSai", "drmundo": "DrMundo", "belveth": "Belveth"
    }
    return f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/img/champion/{mapping.get(clean.lower(), clean)}.png"

# --- 3. TRADUCTIONS & TEXTES ---
TRANSLATIONS = {
    "FR": {
        "title": "LoL Duo Analyst", "btn_scan": "LANCER L'ANALYSE", "placeholder": "Exemple: Sardoche#EUW", "dpm_btn": "🔗 Voir sur dpm.lol", "label_id": "Riot ID",
        "v_hyper": "MVP TOTAL", "s_hyper": "{target} domine la faille (Combat & Objectifs)",
        "v_tactician": "MASTERMIND", "s_tactician": "{target} gagne grâce à la macro",
        "v_fighter": "GLADIATEUR", "s_fighter": "{target} fait les dégâts, {duo} prend les objectifs",
        "v_solid": "DUO FUSIONNEL", "s_solid": "Contribution parfaitement équilibrée",
        "v_passive": "EN RETRAIT", "s_passive": "{target} joue safe, {duo} mène le jeu",
        "v_struggle": "EN DIFFICULTÉ", "s_struggle": "{target} peine à suivre le rythme de {duo}",
        "solo": "LOUP SOLITAIRE", "solo_sub": "Aucun duo récurrent sur 20 parties.",
        "loading": "Analyse tactique en cours...", "stats": "PERF DE", "combat": "COMBAT", "eco": "ÉCONOMIE", "vision": "VISION & MAP",
        "error_no_games": "Aucune partie trouvée.", "error_hint": "Vérifie la région.",
        "q_surv": "Injouable (KDA)", "q_dmg": "Gros Dégâts", "q_obj": "Destructeur", "q_vis": "Contrôle Map", "q_bal": "Polyvalent",
        "f_feed": "Meurt trop", "f_afk": "Pas de dégâts", "f_no_obj": "Ignore objectifs", "f_blind": "Joue dans le noir", "f_ok": "Aucun défaut"
    },
    "EN": {
        "title": "LoL Duo Analyst", "btn_scan": "START ANALYSIS", "placeholder": "Example: Faker#KR1", "dpm_btn": "🔗 Check dpm.lol", "label_id": "Riot ID",
        "v_hyper": "TOTAL MVP", "s_hyper": "{target} dominates the rift",
        "v_tactician": "MASTERMIND", "s_tactician": "{target} wins through macro",
        "v_fighter": "GLADIATOR", "s_fighter": "{target} deals dmg, {duo} takes objs",
        "v_solid": "PERFECT DUO", "s_solid": "Balanced contribution",
        "v_passive": "PASSIVE", "s_passive": "{target} plays safe, {duo} leads",
        "v_struggle": "STRUGGLING", "s_struggle": "{target} can't keep up with {duo}",
        "solo": "SOLO PLAYER", "solo_sub": "No recurring partner found.",
        "loading": "Analyzing...", "stats": "STATS FOR", "combat": "COMBAT", "eco": "ECONOMY", "vision": "VISION",
        "error_no_games": "No games found.", "error_hint": "Check Region.",
        "q_surv": "Unkillable", "q_dmg": "Heavy Hitter", "q_obj": "Destroyer", "q_vis": "Map Control", "q_bal": "Balanced",
        "f_feed": "Feeder", "f_afk": "Low Dmg", "f_no_obj": "No Objs", "f_blind": "Blind", "f_ok": "Solid"
    },
    "ES": {"title":"Analista LoL","btn_scan":"ANALIZAR","dpm_btn":"Ver dpm.lol","label_id":"Riot ID","v_solid":"DUO SOLIDO","solo":"SOLO","solo_sub":"Sin duo","loading":"Cargando...","stats":"STATS","combat":"COMBATE","eco":"ECONOMIA","vision":"VISION","error_no_games":"Sin partidas","error_hint":"Region?","placeholder":"Nombre#TAG","s_solid":"Equilibrio","v_hyper":"MVP","s_hyper":"Domina","q_surv":"Inmortal","q_dmg":"Daño","f_feed":"Muere mucho","f_ok":"Bien"},
    "KR": {"title":"LoL 듀오 분석","btn_scan":"분석 시작","dpm_btn":"dpm.lol 확인","label_id":"Riot ID","v_solid":"완벽 듀오","solo":"솔로","solo_sub":"듀오 없음","loading":"분석 중...","stats":"통계","combat":"전투","eco":"경제","vision":"시야","error_no_games":"게임 없음","error_hint":"지역 확인","placeholder":"이름#태그","s_solid":"동등함","v_hyper":"MVP","s_hyper":"캐리","q_surv":"생존","q_dmg":"딜량","f_feed":"데스","f_ok":"굿"}
}

# --- 4. CSS INJECTOR ---
def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-image: url("{ASSETS['bg']}"); background-size: 150px; background-repeat: repeat; background-attachment: fixed; }}
    .block-container {{ max-width: 1400px !important; padding: 2rem !important; margin: auto !important; background: rgba(12, 12, 12, 0.96); backdrop-filter: blur(20px); border-radius: 0px; border-bottom: 2px solid #333; box-shadow: 0 20px 50px rgba(0,0,0,0.9); }}
    .main-title {{ font-size: 60px; font-weight: 900; color: white; text-align: center; margin-bottom: 20px; text-transform: uppercase; letter-spacing: -2px; background: -webkit-linear-gradient(#eee, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    
    /* UI ELEMENTS */
    .dpm-button-small {{ display: flex; align-items: center; justify-content: center; background-color: rgba(37, 99, 235, 0.2); color: #60a5fa !important; height: 46px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 14px; border: 1px solid #2563eb; margin-top: 28px; transition: 0.2s; }}
    .dpm-button-small:hover {{ background-color: #2563eb; color: white !important; }}
    .stButton > button {{ width: 100%; height: 50px; background: linear-gradient(90deg, #ff0055, #ff2222); color: white; font-size: 18px; font-weight: 800; border: none; border-radius: 8px; text-transform: uppercase; transition: 0.2s; }}
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 20px rgba(255,0,85,0.3); }}
    .input-label-row {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 5px; }}
    .custom-label {{ font-size: 14px; font-weight: 700; color: #ddd; text-transform: uppercase; }}
    
    /* PANELS & STATS */
    .player-panel {{ background: rgba(255, 255, 255, 0.03); border-radius: 16px; padding: 25px; height: 100%; border: 1px solid rgba(255,255,255,0.05); }}
    .player-name {{ font-size: 32px; font-weight: 900; color: white; text-align: center; margin-bottom: 5px; }}
    .player-role {{ font-size: 14px; font-weight: 700; text-align: center; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; padding: 5px; border-radius: 4px; background: rgba(255,255,255,0.05); }}
    
    .color-gold {{ color: #FFD700; border-color: #FFD700; }}
    .color-blue {{ color: #00BFFF; border-color: #00BFFF; }}
    .color-green {{ color: #00ff99; border-color: #00ff99; }}
    .color-orange {{ color: #FFA500; border-color: #FFA500; }}
    .color-red {{ color: #ff4444; border-color: #ff4444; }}

    .stat-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }}
    .stat-label {{ font-size: 13px; color: #888; font-weight: 600; text-transform: uppercase; }}
    .stat-value {{ font-size: 18px; color: white; font-weight: 700; }}
    .stat-diff {{ font-size: 11px; font-weight: 600; margin-left: 6px; padding: 2px 4px; border-radius: 3px; }}
    .pos {{ color: #00ff99; background: rgba(0,255,153,0.1); }} .neg {{ color: #ff4444; background: rgba(255,68,68,0.1); }} .neutral {{ color: #666; }}
    
    .feedback-row {{ display: flex; gap: 8px; justify-content: center; margin-bottom: 15px; }}
    .fb-box {{ padding: 6px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase; }}
    .fb-good {{ background: rgba(0, 255, 153, 0.1); color: #00ff99; border: 1px solid #00ff99; }}
    .fb-bad {{ background: rgba(255, 68, 68, 0.1); color: #ff6666; border: 1px solid #ff4444; }}
    
    .verdict-banner {{ text-align: center; padding: 30px; margin-bottom: 40px; border-radius: 16px; background: rgba(0,0,0,0.4); border: 1px solid #333; }}
    .champ-img {{ width: 50px; height: 50px; border-radius: 50%; border: 2px solid #444; margin: 0 4px; }}
    p, label {{ color: #eee !important; font-weight: 600; font-size: 13px; }}
    </style>
    """, unsafe_allow_html=True)

inject_css()

# --- 5. LOGIQUE API & ANALYSE ---

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

def analyze_qualities(stats, lang_dict):
    """Détermine Points Forts et Faibles"""
    qualities, flaws = [], []
    if stats['kda'] > 3.5: qualities.append(lang_dict["q_surv"])
    elif stats['kda'] < 1.8: flaws.append(lang_dict["f_feed"])
    if stats['obj'] > 5000: qualities.append(lang_dict["q_obj"])
    elif stats['obj'] < 1000: flaws.append(lang_dict["f_no_obj"])
    if stats['dpm'] > 750: qualities.append(lang_dict["q_dmg"])
    elif stats['dpm'] < 300: flaws.append(lang_dict["f_afk"])
    if stats['vis'] > 30: qualities.append(lang_dict["q_vis"])
    elif stats['vis'] < 10: flaws.append(lang_dict["f_blind"])
    
    q = qualities[0] if qualities else lang_dict["q_bal"]
    f = flaws[0] if flaws else lang_dict["f_ok"]
    return q, f

def render_stat_row(label, val, diff, unit=""):
    """Composant visuel pour une ligne de stat"""
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

# --- 6. INTERFACE PRINCIPALE ---

c_title, c_lang = st.columns([5, 1])
with c_lang:
    selected_lang = st.selectbox("Lang", ["FR", "EN", "ES", "KR"], label_visibility="collapsed")
T = TRANSLATIONS.get(selected_lang, TRANSLATIONS["EN"])

st.markdown(f'<div class="main-title">{T["title"]}</div>', unsafe_allow_html=True)

with st.form("search_form"):
    c1, c2, c3, c4 = st.columns([4, 1.2, 1.2, 1.2], gap="small")
    with c1:
        st.markdown(f"""<div class="input-label-row"><span class="custom-label">{T['label_id']}</span><a href="https://dpm.lol" target="_blank" class="dpm-badge">{T['dpm_btn']}</a></div>""", unsafe_allow_html=True)
        riot_id_input = st.text_input("HiddenLabel", placeholder=T["placeholder"], label_visibility="collapsed")
    with c2:
        st.markdown(f"<div style='margin-bottom:5px'><span class='custom-label'>Region</span></div>", unsafe_allow_html=True)
        region_select = st.selectbox("Region", ["EUW1", "NA1", "KR", "EUN1", "TR1"], label_visibility="collapsed")
    with c3:
        st.markdown(f"<div style='margin-bottom:5px'><span class='custom-label'>Mode</span></div>", unsafe_allow_html=True)
        queue_type = st.selectbox("Mode", ["Solo/Duo", "Flex"], label_visibility="collapsed")
    submitted = st.form_submit_button(T["btn_scan"])

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

            # ANALYSIS CORE
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
                                    'gold': p['goldEarned'] / duration_min,
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

            # VERDICT PROCESSING
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
                
                # --- CALCUL DU SCORE (FAIR-PLAY) ---
                def calc_score(s):
                    kda = s['kda'] / g
                    dpm = s['dpm'] / g
                    obj = s['obj'] / g 
                    vis = s['vis'] / g
                    score = (kda * 150) + (dpm * 0.4) + (obj * 0.3) + (vis * 15)
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

                # UI Setup
                header_color, title_text, sub_text = "#00ff99", T["v_solid"], T["s_solid"]
                role_me_key, role_me_color = "role_equal", "color-green"
                role_duo_key, role_duo_color = "role_equal", "color-green"

                if state == "BOOSTED_HARD":
                    header_color, title_text, sub_text = "#ff4444", T["v_struggle"], T["s_struggle"].format(target=target_name, duo=duo_name)
                    role_me_key, role_me_color = "role_gap", "color-red"
                    role_duo_key, role_duo_color = "role_hyper", "color-gold"
                elif state == "BOOSTED_SOFT":
                    header_color, title_text, sub_text = "#FFA500", T["v_passive"], T["s_passive"].format(target=target_name, duo=duo_name)
                    role_me_key, role_me_color = "role_supp", "color-orange"
                    role_duo_key, role_duo_color = "role_lead", "color-blue"
                elif state == "BOOSTER_HARD":
                    header_color, title_text, sub_text = "#FFD700", T["v_hyper"], T["s_hyper"].format(target=target_name)
                    role_me_key, role_me_color = "role_hyper", "color-gold"
                    role_duo_key, role_duo_color = "role_gap", "color-red"
                elif state == "BOOSTER_SOFT":
                    header_color, title_text, sub_text = "#00BFFF", T["v_tactician"], T["s_tactician"].format(target=target_name)
                    role_me_key, role_me_color = "role_lead", "color-blue"
                    role_duo_key, role_duo_color = "role_supp", "color-orange"

                # DISPLAY
                st.markdown(f"""
                <div class="verdict-banner" style="border-color:{header_color}">
                    <div style="font-size:42px; font-weight:900; color:{header_color}; margin-bottom:10px;">{title_text}</div>
                    <div style="font-size:18px; color:#ddd;">{sub_text}</div>
                    <div style="margin-top:15px; font-size:14px; color:#888;">{g} Games • {winrate}% Winrate</div>
                </div>""", unsafe_allow_html=True)

                col_left, col_right = st.columns(2, gap="large")
                
                stats_me = {'kda': avg_f(s_me, 'kda'), 'dpm': avg(s_me, 'dpm'), 'vis': avg(s_me, 'vis'), 'obj': avg(s_me, 'obj')}
                qual, flaw = analyze_qualities(stats_me, T)
                stats_duo = {'kda': avg_f(s_duo, 'kda'), 'dpm': avg(s_duo, 'dpm'), 'vis': avg(s_duo, 'vis'), 'obj': avg(s_duo, 'obj')}
                qual_d, flaw_d = analyze_qualities(stats_duo, T)

                # LEFT PANEL
                with col_left:
                    st.markdown(f"""<div class="player-panel"><div class="player-name">{target_name}</div><div class="player-role {role_me_color}">{T[role_me_key]}</div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="feedback-row"><div class="fb-box fb-good">{qual}</div><div class="fb-box fb-bad">{flaw}</div></div>""", unsafe_allow_html=True)
                    
                    top_champs = [c[0] for c in Counter(best_duo['my_champs']).most_common(3)]
                    html_champs = "<div class='champ-row' style='justify-content:center; margin-bottom:20px;'>"
                    for ch in top_champs: html_champs += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
                    html_champs += "</div>"
                    st.markdown(html_champs, unsafe_allow_html=True)
                    
                    st.markdown(f"<div class='stat-section-title'>{T['combat']}</div>", unsafe_allow_html=True)
                    render_stat_row("KDA", stats_me['kda'], stats_me['kda'] - stats_duo['kda'])
                    render_stat_row("DPM", stats_me['dpm'], stats_me['dpm'] - stats_duo['dpm'])
                    st.markdown(f"<div class='stat-section-title'>{T['eco']} / {T['vision']}</div>", unsafe_allow_html=True)
                    render_stat_row("GOLD", int(avg(s_me, 'gold')), int(avg(s_me, 'gold')) - int(avg(s_duo, 'gold')))
                    render_stat_row("VISION", stats_me['vis'], stats_me['vis'] - stats_duo['vis'])
                    st.markdown(f"<div class='stat-section-title'>OBJECTIVES</div>", unsafe_allow_html=True)
                    render_stat_row("OBJ DMG", stats_me['obj'], stats_me['obj'] - stats_duo['obj'])
                    render_stat_row("TOWERS", avg_f(s_me, 'towers'), avg_f(s_me, 'towers') - avg_f(s_duo, 'towers'))
                    st.markdown("</div>", unsafe_allow_html=True)

                # RIGHT PANEL
                with col_right:
                    st.markdown(f"""<div class="player-panel"><div class="player-name">{duo_name}</div><div class="player-role {role_duo_color}">{T[role_duo_key]}</div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="feedback-row"><div class="fb-box fb-good">{qual_d}</div><div class="fb-box fb-bad">{flaw_d}</div></div>""", unsafe_allow_html=True)
                    
                    top_champs_d = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                    html_champs_d = "<div class='champ-row' style='justify-content:center; margin-bottom:20px;'>"
                    for ch in top_champs_d: html_champs_d += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
                    html_champs_d += "</div>"
                    st.markdown(html_champs_d, unsafe_allow_html=True)
                    
                    st.markdown(f"<div class='stat-section-title'>{T['combat']}</div>", unsafe_allow_html=True)
                    render_stat_row("KDA", stats_duo['kda'], stats_duo['kda'] - stats_me['kda'])
                    render_stat_row("DPM", stats_duo['dpm'], stats_duo['dpm'] - stats_me['dpm'])
                    st.markdown(f"<div class='stat-section-title'>{T['eco']} / {T['vision']}</div>", unsafe_allow_html=True)
                    render_stat_row("GOLD", int(avg(s_duo, 'gold')), int(avg(s_duo, 'gold')) - int(avg(s_me, 'gold')))
                    render_stat_row("VISION", stats_duo['vis'], stats_duo['vis'] - stats_me['vis'])
                    st.markdown(f"<div class='stat-section-title'>OBJECTIVES</div>", unsafe_allow_html=True)
                    render_stat_row("OBJ DMG", stats_duo['obj'], stats_duo['obj'] - stats_me['obj'])
                    render_stat_row("TOWERS", avg_f(s_duo, 'towers'), avg_f(s_duo, 'towers') - avg_f(s_me, 'towers'))
                    st.markdown("</div>", unsafe_allow_html=True)

            else:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.markdown(f"""<div class="verdict-banner" style="border-color:#00ff99"><div style="font-size:32px; font-weight:900; color:#00ff99;">{T["solo"]}</div><div style="font-size:18px; color:#ddd; margin-top:10px;">{T["solo_sub"]}</div></div>""", unsafe_allow_html=True)
