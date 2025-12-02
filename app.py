import streamlit as st
import requests
import time
from urllib.parse import quote
from collections import Counter
import concurrent.futures

# --- CONFIGURATION ---
st.set_page_config(page_title="LoL Duo Investigator V33", layout="wide")

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
        "title": "LoL Duo Analyst",
        "btn_scan": "LANCER L'ANALYSE",
        "placeholder": "Exemple: Sardoche#EUW",
        "dpm_btn": "🔗 Voir sur dpm.lol",
        
        "v_hyper": "CARRY SOLITAIRE",
        "s_hyper": "{target} doit tout faire tout seul",
        "v_lead": "LEADER TECHNIQUE",
        "s_lead": "{target} a un léger avantage statistique",
        "v_equal": "DUO FUSIONNEL",
        "s_equal": "Synergie Parfaite : Ils se complètent totalement",
        "v_supp": "SOUTIEN STRATÉGIQUE",
        "s_supp": "{target} joue pour l'équipe, {duo} finit le travail",
        "v_gap": "EN DIFFICULTÉ",
        "s_gap": "{target} peine à suivre le niveau de {duo}",

        "solo": "JOUEUR SOLO",
        "solo_sub": "Aucun duo récurrent sur 20 parties.",
        "loading": "Calcul de la synergie...",
        
        "role_hyper": "CARRY",
        "role_lead": "MENEUR",
        "role_equal": "PARTENAIRE",
        "role_supp": "SOUTIEN",
        "role_gap": "ROOKIE",
        
        # Titres de spécialité
        "spec_vis": "👁️ Maître de la Vision",
        "spec_dmg": "⚔️ Artilleur (Dégâts)",
        "spec_surv": "🛡️ L'Immortel (KDA)",
        "spec_obj": "🏰 Destructeur",
        "spec_rich": "💰 Magnat (Gold)",
        "spec_poly": "⚖️ Polyvalent",

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
        
        "v_hyper": "SOLO CARRY",
        "s_hyper": "{target} is doing everything alone",
        "v_lead": "TECHNICAL LEADER",
        "s_lead": "{target} has a slight statistical edge",
        "v_equal": "PERFECT SYNERGY",
        "s_equal": "Perfect Match: They complete each other",
        "v_supp": "STRATEGIC SUPPORT",
        "s_supp": "{target} sets up the plays, {duo} finishes them",
        "v_gap": "STRUGGLING",
        "s_gap": "{target} is having a hard time keeping up",

        "solo": "SOLO PLAYER",
        "solo_sub": "No recurring partner found.",
        "loading": "Analyzing synergy...",
        
        "role_hyper": "CARRY",
        "role_lead": "LEADER",
        "role_equal": "PARTNER",
        "role_supp": "SUPPORT",
        "role_gap": "ROOKIE",
        
        "spec_vis": "👁️ Vision Master",
        "spec_dmg": "⚔️ Heavy Hitter",
        "spec_surv": "🛡️ The Immortal",
        "spec_obj": "🏰 Destroyer",
        "spec_rich": "💰 Tycoon",
        "spec_poly": "⚖️ All-Rounder",

        "stats": "STATS FOR",
        "combat": "COMBAT",
        "eco": "ECONOMY",
        "vision": "VISION & MAP",
        "error_no_games": "No games found.",
        "error_hint": "Check Region."
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

    .player-panel {{ background: rgba(255, 255, 255, 0.03); border-radius: 16px; padding: 25px; height: 100%; border: 1px solid rgba(255,255,255,0.05); }}
    
    .player-name {{ font-size: 32px; font-weight: 900; color: white; text-align: center; margin-bottom: 5px; }}
    .player-role {{ font-size: 14px; font-weight: 700; text-align: center; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; padding: 5px; border-radius: 4px; background: rgba(255,255,255,0.05); }}
    .specialty-badge {{ font-size: 14px; font-weight: 600; text-align: center; color: #aaa; margin-bottom: 20px; font-style: italic; }}

    /* ROLE COLORS */
    .color-gold {{ color: #FFD700; border-color: #FFD700; }}
    .color-blue {{ color: #00BFFF; border-color: #00BFFF; }}
    .color-green {{ color: #00ff99; border-color: #00ff99; }}
    .color-orange {{ color: #FFA500; border-color: #FFA500; }}
    .color-red {{ color: #ff4444; border-color: #ff4444; }}

    .stat-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }}
    .stat-label {{ font-size: 13px; color: #888; font-weight: 600; text-transform: uppercase; }}
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
    
    .champ-img {{ width: 50px; height: 50px; border-radius: 50%; border: 2px solid #444; margin: 0 4px; }}
    p, label {{ color: #eee !important; font-weight: 600; font-size: 13px; }}
    </style>
    """, unsafe_allow_html=True
)

# --- HEADER ---
c_title, c_lang = st.columns([5, 1])
with c_lang:
    selected_lang = st.selectbox("Language", ["FR", "EN"], label_visibility="collapsed")
T = TRANSLATIONS.get(selected_lang, TRANSLATIONS["EN"])

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

def identify_specialty(stats, lang_dict):
    """Trouve la stat la plus impressionnante du joueur pour lui donner un titre"""
    # Normalisation pour comparer ce qui est comparable
    s_kda = stats['kda'] / 3.0
    s_dmg = stats['dpm'] / 700.0
    s_vis = stats['vis'] / 30.0 # Vision très valorisée
    s_obj = stats['obj'] / 5000.0
    s_gold = stats['gold'] / 400.0
    
    scores = {
        "spec_vis": s_vis,
        "spec_dmg": s_dmg,
        "spec_surv": s_kda,
        "spec_obj": s_obj,
        "spec_rich": s_gold
    }
    
    best_stat = max(scores, key=scores.get)
    return lang_dict[best_stat]

def render_stat_row(label, val, diff, unit=""):
    if diff > 0: diff_html = f"<span class='stat-diff pos'>+{round(diff, 1)}{unit}</span>"
    elif diff < 0: diff_html = f"<span class='stat-diff neg'>{round(diff, 1)}{unit}</span>"
    else: diff_html = f"<span class='stat-diff neutral'>=</span>"
    val_display = f"{val}{unit}"
    if isinstance(val, int) and val > 1000: val_display = f"{val/1000:.1f}k"
    st.markdown(f"""<div class="stat-row"><div class="stat-label">{label}</div><div style="display:flex; align-items:center;"><div class="stat-value">{val_display}</div>{diff_html}</div></div>""", unsafe_allow_html=True)

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
                
                # --- CALCUL V33 (ÉQUILIBRE PARFAIT) ---
                def calc_score(s):
                    kda = s['kda'] / g
                    dpm = s['dpm'] / g
                    obj = s['obj'] / g 
                    vis = s['vis'] / g
                    # Poids Équilibrés : Vision et KDA pèsent très lourd
                    score = (kda * 250) + (dpm * 0.5) + (obj * 0.15) + (vis * 25)
                    return score

                score_me = calc_score(s_me)
                score_duo = calc_score(s_duo)
                ratio = score_me / max(1, score_duo)
                
                # Seuils très larges pour favoriser l'égalité
                if ratio > 1.3: state = "BOOSTER_HARD"
                elif ratio > 1.15: state = "BOOSTER_SOFT"
                elif ratio < 0.7: state = "BOOSTED_HARD"
                elif ratio < 0.85: state = "BOOSTED_SOFT"
                else: state = "EQUAL"

                winrate = int((best_duo['wins']/g)*100)

                # --- AFFICHAGE ---
                header_color = "#00ff99"
                title_text = T["v_equal"]
                sub_text = T["s_equal"]
                
                role_me_key, role_me_color = "role_equal", "color-green"
                role_duo_key, role_duo_color = "role_equal", "color-green"

                if state == "BOOSTED_HARD":
                    header_color = "#ff4444"
                    title_text = T["v_gap"]
                    sub_text = T["s_gap"].format(target=target_name, duo=duo_name)
                    role_me_key, role_me_color = "role_gap", "color-red"
                    role_duo_key, role_duo_color = "role_hyper", "color-gold"
                    if "http" in CLOWN_IMAGE_URL:
                        c1, c2, c3 = st.columns([1, 1, 1])
                        with c2: st.image(CLOWN_IMAGE_URL, use_column_width=True)

                elif state == "BOOSTED_SOFT":
                    header_color = "#FFA500"
                    title_text = T["v_supp"]
                    sub_text = T["s_supp"].format(target=target_name, duo=duo_name)
                    role_me_key, role_me_color = "role_supp", "color-orange"
                    role_duo_key, role_duo_color = "role_lead", "color-blue"

                elif state == "BOOSTER_HARD":
                    header_color = "#FFD700"
                    title_text = T["v_hyper"]
                    sub_text = T["s_hyper"].format(target=target_name)
                    role_me_key, role_me_color = "role_hyper", "color-gold"
                    role_duo_key, role_duo_color = "role_gap", "color-red"

                elif state == "BOOSTER_SOFT":
                    header_color = "#00BFFF"
                    title_text = T["v_lead"]
                    sub_text = T["s_lead"].format(target=target_name, duo=duo_name)
                    role_me_key, role_me_color = "role_lead", "color-blue"
                    role_duo_key, role_duo_color = "role_supp", "color-orange"

                st.markdown(f"""
                <div class="verdict-banner" style="border-color:{header_color}">
                    <div style="font-size:42px; font-weight:900; color:{header_color}; margin-bottom:10px;">{title_text}</div>
                    <div style="font-size:18px; color:#ddd;">{sub_text}</div>
                    <div style="margin-top:15px; font-size:14px; color:#888;">{g} Games • {winrate}% Winrate</div>
                </div>
                """, unsafe_allow_html=True)

                # --- PANNEAUX ---
                col_left, col_right = st.columns(2, gap="large")
                
                # Data préparation pour badge spécialité
                stats_me = {'kda': avg_f(s_me, 'kda'), 'dpm': avg(s_me, 'dpm'), 'vis': avg(s_me, 'vis'), 'obj': avg(s_me, 'obj'), 'gold': avg(s_me, 'gold')}
                stats_duo = {'kda': avg_f(s_duo, 'kda'), 'dpm': avg(s_duo, 'dpm'), 'vis': avg(s_duo, 'vis'), 'obj': avg(s_duo, 'obj'), 'gold': avg(s_duo, 'gold')}
                
                spec_me = identify_specialty(stats_me, T)
                spec_duo = identify_specialty(stats_duo, T)

                with col_left:
                    st.markdown(f"""
                    <div class="player-panel">
                        <div class="player-name">{target_name}</div>
                        <div class="player-role {role_me_color}">{T[role_me_key]}</div>
                        <div class="specialty-badge">{spec_me}</div>
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
                        <div class="specialty-badge">{spec_duo}</div>
                    """, unsafe_allow_html=True)
                    top_champs_d = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                    html_champs_d = "<div class='champ-row' style='justify-content:center; margin-bottom:20px;'>"
                    for ch in top_champs_d: html_champs_d += f"<img src='{get_champ_url(ch)}' class='champ-img'>"
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
