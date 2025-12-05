import streamlit as st
import streamlit.components.v1 as components
import requests
import plotly.graph_objects as go
from urllib.parse import quote
from collections import Counter, defaultdict
import concurrent.futures
import html
import time
import os

# --- 1. CONFIGURATION & SESSION ---
st.set_page_config(page_title="LoL Duo Analyst V80 (Debug Mode)", layout="wide")

if 'api_session' not in st.session_state:
    st.session_state.api_session = requests.Session()

# --- 2. API KEY ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except (FileNotFoundError, KeyError):
    API_KEY = os.environ.get("RIOT_API_KEY")

if not API_KEY:
    st.error("⚠️ CLÉ API MANQUANTE. Ajoute RIOT_API_KEY dans les secrets ou variables d'env.")
    st.stop()

# --- 3. CONSTANTES ---
BACKGROUND_IMAGE_URL = "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123"
QUEUE_MAP = {"Ranked Solo/Duo": 420, "Ranked Flex": 440, "Draft Normal": 400, "ARAM": 450, "Arena": 1700}
ROLE_ICONS = {"TOP": "🛡️ TOP", "JUNGLE": "🌲 JUNGLE", "MIDDLE": "🧙 MID", "BOTTOM": "🏹 ADC", "UTILITY": "🩹 SUPP", "UNKNOWN": "❓ FILL"}
LANG_MAP = {"🇫🇷 FR": "FR", "🇺🇸 EN": "EN", "🇪🇸 ES": "ES", "🇰🇷 KR": "KR"}

TRANSLATIONS = {
    "FR": {
        "title": "LoL Duo Analyst", "btn_scan": "LANCER L'ANALYSE", "placeholder": "Exemple: Kameto#EUW",
        "label_id": "Riot ID", "lbl_region": "RÉGION", "lbl_mode": "MODE", "dpm_btn": "🔗 Voir sur dpm.lol", "btn_profile": "Voir Profil DPM",
        "lbl_duo_detected": "🚨 DUO DÉTECTÉ AVEC {duo} 🚨", "v_hyper": "CARRY MACHINE", "s_hyper": "{target} inflige des dégâts monstrueux comparé à {duo}",
        "v_survivor": "IMMORTEL", "s_survivor": "{target} survit et joue propre, {duo} meurt trop souvent", "v_tactician": "MASTERMIND", "s_tactician": "{target} gagne grâce à la vision et au map control",
        "v_breacher": "DESTRUCTEUR", "s_breacher": "{target} prend les tours, {duo} regarde", "v_solid": "DUO FUSIONNEL", "s_solid": "Synergie parfaite entre {target} et {duo}",
        "v_passenger": "PASSAGER", "s_passenger": "{target} se laisse porter par {duo} (Dégâts faibles)", "v_feeder": "ZONE DE DANGER", "s_feeder": "{target} passe trop de temps à l'écran gris vs {duo}",
        "v_struggle": "EN DIFFICULTÉ", "s_struggle": "{target} peine à suivre le rythme de {duo}", "solo": "LOUP SOLITAIRE", "solo_sub": "Aucun duo récurrent détecté sur 20 parties.",
        "loading": "Analyse tactique en cours...", "q_surv": "Injouable (KDA)", "q_dmg": "Gros Dégâts", "q_obj": "Destructeur", "q_vis": "Contrôle Map",
        "f_feed": "Meurt trop souvent", "f_blind": "Vision faible", "f_afk": "Dégâts faibles", "error_no_games": "Aucune partie trouvée."
    },
    "EN": {
        "title": "LoL Duo Analyst", "btn_scan": "START ANALYSIS", "placeholder": "Example: Faker#KR1",
        "label_id": "Riot ID", "lbl_region": "REGION", "lbl_mode": "MODE", "dpm_btn": "🔗 Check dpm.lol", "btn_profile": "DPM Profile",
        "lbl_duo_detected": "🚨 DUO DETECTED WITH {duo} 🚨", "v_hyper": "DMG CARRY", "s_hyper": "{target} is dealing massive damage compared to {duo}",
        "v_survivor": "IMMORTAL", "s_survivor": "{target} survives, {duo} dies too much", "v_tactician": "MASTERMIND", "s_tactician": "{target} wins via vision & macro",
        "v_breacher": "BREACHER", "s_breacher": "{target} takes towers, {duo} watches", "v_solid": "PERFECT DUO", "s_solid": "Perfect synergy between {target} and {duo}",
        "v_passenger": "PASSENGER", "s_passenger": "{target} is getting carried by {duo} (Low Dmg)", "v_feeder": "DANGER ZONE", "s_feeder": "{target} sees grey screen too often vs {duo}",
        "v_struggle": "STRUGGLING", "s_struggle": "{target} can't keep up with {duo}", "solo": "SOLO PLAYER", "solo_sub": "No recurring partner found.",
        "loading": "Analyzing...", "q_surv": "Unkillable", "q_dmg": "Heavy Hitter", "q_obj": "Destroyer", "q_vis": "Map Control",
        "f_feed": "Too fragile", "f_blind": "Blind", "f_afk": "Low Dmg", "error_no_games": "No games found."
    }
}
TRANSLATIONS["ES"] = TRANSLATIONS["EN"]
TRANSLATIONS["KR"] = TRANSLATIONS["EN"]

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-image: url("{BACKGROUND_IMAGE_URL}"); background-size: 150px; background-repeat: repeat; background-attachment: fixed; }}
    .block-container {{ max-width: 1400px !important; padding-top: 3rem !important; padding-bottom: 3rem !important; background: rgba(12, 12, 12, 0.95); backdrop-filter: blur(15px); border-radius: 15px; border: 1px solid #333; box-shadow: 0 20px 50px rgba(0,0,0,0.9); margin-top: 20px !important; }}
    .main-title {{ font-size: 55px; font-weight: 900; text-align: center; margin-bottom: 30px; margin-top: 10px; background: linear-gradient(90deg, #00c6ff, #0072ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0 0 10px rgba(0, 114, 255, 0.5)); text-transform: uppercase; }}
    .player-card {{ background: rgba(30, 30, 30, 0.5); border-radius: 16px; padding: 25px; border: 1px solid rgba(255,255,255,0.08); text-align: center; height: 100%; box-shadow: inset 0 0 20px rgba(0,0,0,0.2); }}
    .player-name {{ font-size: 28px; font-weight: 800; color: white; margin-bottom: 5px; word-break: break-all; }}
    .player-sub {{ font-size: 14px; color: #aaa; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }}
    .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; margin: 2px; text-transform: uppercase; }}
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
    .pos {{ color: #00ff99; background: rgba(0,255,153,0.15); }} .neg {{ color: #ff4444; background: rgba(255,68,68,0.15); }} .neutral {{ color: #888; }}
    .verdict-box {{ text-align: center; padding: 30px; border-radius: 16px; margin: 20px 0 40px 0; background: rgba(20, 20, 20, 0.8); border: 2px solid #333; }}
    .dpm-btn {{ background: #2563eb; color: white !important; padding: 6px 16px; border-radius: 20px; text-decoration: none; font-size: 12px; font-weight: 700; display: inline-block; margin-bottom: 8px; transition: 0.2s; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3); }}
    .dpm-btn:hover {{ background: #1d4ed8; transform: translateY(-2px); }}
    .dpm-btn-header {{ background: rgba(37, 99, 235, 0.2); color: #60a5fa !important; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-size: 12px; border: 1px solid #2563eb; }}
    .stButton > button {{ width: 100%; height: 55px; background: linear-gradient(135deg, #ff0055, #cc0044); color: white; font-size: 20px; font-weight: 800; border: none; border-radius: 10px; text-transform: uppercase; transition: 0.3s; }}
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 25px rgba(255,0,60,0.5); }}
    .stTextInput > label, .stForm > div[data-testid="stFormEnterToSubmit"] {{ display: none; }}
</style>
""", unsafe_allow_html=True)

# --- 5. COUCHE API DEBUGGÉE ---
def safe_request(url, retry=True):
    """Requête sécurisée avec gestion des erreurs explicites."""
    try:
        resp = st.session_state.api_session.get(url, timeout=5)
        
        if resp.status_code == 200:
            return resp
        elif resp.status_code == 403:
            st.error("🚨 CLÉ API RIOT EXPIRÉE OU INVALIDE (Erreur 403).")
            st.stop() # On arrête tout ici pour avertir l'user
        elif resp.status_code == 404:
            return None # Donnée pas trouvée, c'est normal
        elif resp.status_code == 429:
            if retry:
                time.sleep(1.5) # On attend un peu
                return safe_request(url, retry=False) # On réessaie une fois
            else:
                st.warning("⚠️ API Surchargée (Rate Limit). Réessaie dans quelques secondes.")
                return None
        return None
    except Exception as e:
        # st.error(f"Erreur connexion: {e}") # Décommenter pour debug profond
        return None

@st.cache_data(ttl=86400)
def get_dd_version():
    try: 
        r = requests.get("https://ddragon.leagueoflegends.com/api/versions.json", timeout=3)
        return r.json()[0] if r.status_code == 200 else "14.23.1"
    except: return "14.23.1"

DD_VERSION = get_dd_version()

# --- 6. LOGIQUE MÉTIER ---
def get_champ_url(name):
    if not name: return "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Poro_0.jpg"
    clean = str(name).replace(" ", "").replace("'", "").replace(".", "")
    mapping = {"wukong":"MonkeyKing", "renataglasc":"Renata", "nunu&willump":"Nunu", "kogmaw":"KogMaw", "reksai":"RekSai", "drmundo":"DrMundo", "belveth":"Belveth"}
    return f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/img/champion/{mapping.get(clean.lower(), clean)}.png"

def get_dpm_url(riot_id):
    if "#" in str(riot_id):
        n, t = riot_id.split("#")
        return f"https://dpm.lol/{quote(n)}-{quote(t)}"
    return "https://dpm.lol"

def extract_stats(p):
    c = p.get('challenges', {})
    return {
        'kills': p.get('kills',0), 'deaths': p.get('deaths',0), 'assists': p.get('assists',0),
        'dmg': p.get('totalDamageDealtToChampions',0), 'gold': p.get('goldEarned',0), 'vis': p.get('visionScore',0),
        'obj': p.get('damageDealtToObjectives',0), 'towers': p.get('turretTakedowns',0),
        'kp': c.get('killParticipation',0), 'solokills': c.get('soloKills',0),
        'champ': p.get('championName','Unknown'), 'role': p.get('teamPosition','UNKNOWN'), 'win': p.get('win',False),
        'puuid': p.get('puuid'), 'name': p.get('riotIdGameName'), 'tag': p.get('riotIdTagLine')
    }

def process_single_match(m_id, region, api_key, my_puuid):
    # Appel Match Detail
    data_raw = safe_request(f"https://{region}.api.riotgames.com/lol/match/v5/matches/{m_id}?api_key={api_key}")
    if not data_raw: return None
    
    data = data_raw.json()
    info = data.get('info', {})
    if info.get('gameDuration', 0) < 300: return None

    parts = info.get('participants', [])
    me = next((p for p in parts if p['puuid'] == my_puuid), None)
    if not me: return None

    duration_min = info['gameDuration'] / 60.0
    my_stats = extract_stats(me)
    duo_entries = []

    for p in parts:
        if p['teamId'] == me['teamId'] and p['puuid'] != my_puuid:
            d_stats = extract_stats(p)
            for s in [my_stats, d_stats]:
                s['dmg_min'] = s['dmg'] / duration_min
                s['gold_min'] = s['gold'] / duration_min
                s['vis_min'] = s['vis'] / duration_min
            
            duo_id = f"{p.get('riotIdGameName')}#{p.get('riotIdTagLine')}"
            duo_entries.append({
                'id': duo_id,
                'name': p.get('riotIdGameName'), 'tag': p.get('riotIdTagLine'), 'puuid': p.get('puuid'),
                'win': p.get('win'), 'champ': p.get('championName'), 'role': p.get('teamPosition'),
                'stats_duo': d_stats, 'stats_me': my_stats
            })
    return {'target_name': me.get('riotIdGameName'), 'entries': duo_entries}

def determine_badges(stats, role, lang_dict):
    badges = []
    if stats.get('kda', 0) >= 4.0: badges.append((lang_dict.get("q_surv", "Survival"), "b-gold"))
    if stats.get('vis_min', 0) >= 2.0 or (role == "UTILITY" and stats.get('vis_min', 0) >= 2.5): badges.append((lang_dict.get("q_vis", "Oracle"), "b-blue")) 
    if stats.get('kp', 0) >= 0.65: badges.append(("Teamplayer", "b-green"))
    if stats.get('dmg_min', 0) >= 800: badges.append((lang_dict.get("q_dmg", "Damage"), "b-red"))
    if stats.get('solokills', 0) >= 2.5: badges.append(("Duelist", "b-red"))
    if stats.get('obj', 0) >= 5000: badges.append((lang_dict.get("q_obj", "Breacher"), "b-gold"))
    
    if stats.get('kda', 0) < 1.5: badges.append((lang_dict.get("f_feed", "Grey Screen"), "b-red"))
    if stats.get('vis_min', 0) < 0.4 and role != "ADC": badges.append((lang_dict.get("f_blind", "Blind"), "b-red"))
    if stats.get('dmg_min', 0) < 300 and role not in ["UTILITY", "JUNGLE"]: badges.append((lang_dict.get("f_afk", "AFK"), "b-blue"))
    return badges[:3] if badges else [("Standard", "b-blue")]

# --- 7. UI INTERFACE ---
c_title, c_lang = st.columns([5, 1])
with c_lang:
    lang_code = LANG_MAP[st.selectbox("Lang", list(LANG_MAP.keys()), label_visibility="collapsed")]

T = TRANSLATIONS.get(lang_code, TRANSLATIONS["EN"])
st.markdown(f'<div class="main-title">{T["title"]}</div>', unsafe_allow_html=True)

with st.form("search_form"):
    c1, c2, c3 = st.columns([3, 1, 1], gap="small")
    with c1:
        st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;"><span style="font-size:14px; font-weight:700; color:#ddd;">{T['label_id']}</span><a href="https://dpm.lol" target="_blank" class="dpm-btn-header">{T['dpm_btn']}</a></div>""", unsafe_allow_html=True)
        riot_id_input = st.text_input("HL", placeholder=T["placeholder"], label_visibility="collapsed")
    with c2:
        st.markdown(f"<span style='font-size:14px; font-weight:700; color:#ddd;'>{T['lbl_region']}</span>", unsafe_allow_html=True)
        region = st.selectbox("RL", ["EUW1", "NA1", "KR", "EUN1", "TR1"], label_visibility="collapsed")
    with c3:
        st.markdown(f"<span style='font-size:14px; font-weight:700; color:#ddd;'>{T['lbl_mode']}</span>", unsafe_allow_html=True)
        queue_label = st.selectbox("ML", list(QUEUE_MAP.keys()), label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button(T["btn_scan"])

# --- 8. EXÉCUTION PRINCIPALE ---
if submitted:
    if "#" not in riot_id_input:
        st.error("⚠️ Format invalide. Utilise: Nom#TAG")
    else:
        name_raw, tag = map(str.strip, riot_id_input.split("#"))
        region_api = "europe" if region in ["EUW1", "EUN1", "TR1", "RU"] else ("asia" if region == "KR" else "americas")
        
        with st.spinner(T["loading"]):
            # 1. FETCH PUUID
            acc_req = safe_request(f"https://{region_api}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{quote(name_raw)}/{tag}?api_key={API_KEY}")
            
            if not acc_req:
                st.error(f"❌ Joueur introuvable ou erreur API. Vérifie le pseudo {name_raw}#{tag} et la région {region}.")
                st.stop()
            
            puuid = acc_req.json().get("puuid")
            
            # 2. FETCH MATCH LIST
            matches_req = safe_request(f"https://{region_api}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue={QUEUE_MAP[queue_label]}&start=0&count=15&api_key={API_KEY}")
            
            if not matches_req:
                st.warning(T["error_no_games"])
                st.stop()
                
            match_ids = matches_req.json()
            if not match_ids:
                st.warning(f"{T['error_no_games']} ({queue_label})")
                st.stop()

            # 3. PROCESS MATCHES
            agg_data = defaultdict(lambda: {'name': '', 'tag': '', 'puuid': '', 'games': 0, 'wins': 0, 'champs': [], 'roles': [], 's_duo': [], 's_me': []})
            target_display_name = riot_id_input

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(process_single_match, m, region_api, API_KEY, puuid) for m in match_ids]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        res = future.result()
                        if not res: continue
                        target_display_name = res['target_name']
                        for entry in res['entries']:
                            d = agg_data[entry['id']]
                            d['name'], d['tag'], d['puuid'] = entry['name'], entry['tag'], entry['puuid']
                            d['games'] += 1
                            if entry['win']: d['wins'] += 1
                            d['champs'].append(entry['champ'])
                            d['roles'].append(entry['role'])
                            d['s_duo'].append(entry['stats_duo'])
                            d['s_me'].append(entry['stats_me'])
                    except: pass

            if not agg_data:
                st.warning("Aucun duo trouvé dans les parties récentes.")
                st.stop()
                
            best_duo = max(agg_data.values(), key=lambda x: x['games'])

            if best_duo['games'] < 2:
                st.markdown(f"""<div class="verdict-box" style="border-color:#888;"><div style="font-size:32px; font-weight:900; color:#888;">{T["solo"]}</div><div style="font-size:16px; color:#aaa;">{T["solo_sub"]}</div></div>""", unsafe_allow_html=True)
            else:
                # 4. FIX TAG & DISPLAY
                real_name, real_tag = best_duo['name'], best_duo['tag']
                if not real_tag or real_tag == "None":
                    acc_check = safe_request(f"https://{region_api}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{best_duo['puuid']}?api_key={API_KEY}")
                    if acc_check:
                        d_json = acc_check.json()
                        real_name, real_tag = d_json.get('gameName', real_name), d_json.get('tagLine', real_tag)

                duo_display = html.escape(real_name)
                t_safe = html.escape(target_display_name)
                duo_full_id = f"{real_name}#{real_tag}"
                
                def avg(l): return {k: sum(d[k] for d in l)/len(l) for k in l[0] if isinstance(l[0][k], (int,float))} if l else {}
                avg_duo, avg_me = avg(best_duo['s_duo']), avg(best_duo['s_me'])
                for s in [avg_duo, avg_me]: s['kda'] = round((s.get('kills',0)+s.get('assists',0))/max(1,s.get('deaths',1)), 2)
                
                r_duo = Counter(best_duo['roles']).most_common(1)[0][0] if best_duo['roles'] else "UNKNOWN"
                r_me = Counter([x['role'] for x in best_duo['s_me']]).most_common(1)[0][0] if best_duo['s_me'] else "UNKNOWN"

                def get_score(s, r):
                    sc = min(5, s['kda']) + (s['kp']*4) + min(3, (s['vis_min']/(2.0 if r=="UTILITY" else 1.0))*2)
                    sc += min(4, s['dmg_min']/700) if r!="UTILITY" else 0
                    return sc + min(4, (s['obj']/5000) + (s['towers']*0.5))
                
                ratio = get_score(avg_me, r_me) / max(0.1, get_score(avg_duo, r_duo))
                
                d_kda = (avg_me['kda'] - avg_duo['kda']) / 1.5
                d_dmg = (avg_me['dmg_min'] - avg_duo['dmg_min']) / 400
                d_vis = (avg_me['vis_min'] - avg_duo['vis_min']) / 0.8
                d_obj = (avg_me['obj'] - avg_duo['obj']) / 3000

                title, color, sub = T["v_solid"], "#00ff99", safe_format(T["s_solid"], t_safe, duo_display)
                if ratio > 1.15:
                    m = max(d_kda, d_dmg, d_vis, d_obj)
                    if m == d_kda: title, color, sub = T["v_survivor"], "#FFD700", safe_format(T["s_survivor"], t_safe, duo_display)
                    elif m == d_vis: title, color, sub = T["v_tactician"], "#00BFFF", safe_format(T["s_tactician"], t_safe, duo_display)
                    elif m == d_obj: title, color, sub = T["v_breacher"], "#FFA500", safe_format(T["s_breacher"], t_safe, duo_display)
                    else: title, color, sub = T["v_hyper"], "#ff0055", safe_format(T["s_hyper"], t_safe, duo_display)
                elif ratio < 0.85:
                    m = min(d_kda, d_dmg, d_vis)
                    if m == d_kda: title, color, sub = T["v_feeder"], "#ff4444", safe_format(T["s_feeder"], t_safe, duo_display)
                    elif m == d_dmg: title, color, sub = T["v_passenger"], "#888888", safe_format(T["s_passenger"], t_safe, duo_display)
                    else: title, color, sub = T["v_struggle"], "#ff4444", safe_format(T["s_struggle"], t_safe, duo_display)

                components.html(f"<script>window.parent.document.querySelector('.verdict-box').scrollIntoView({{behavior:'smooth'}});</script>", height=0)
                st.markdown(f"""
                <div class="verdict-box" style="border-color:{color}">
                    <div style="font-size:14px; font-weight:700; color:#aaa; margin-bottom:5px; text-transform:uppercase;">{safe_format(T['lbl_duo_detected'], target=t_safe, duo=duo_display)}</div>
                    <div style="font-size:clamp(30px, 6vw, 45px); font-weight:900; color:{color}; margin-bottom:10px; line-height:1.1;">{title}</div>
                    <div style="font-size:18px; color:#eee; font-style:italic;">"{sub}"</div>
                    <div style="margin-top:15px; color:#888; font-weight:600;">{best_duo['games']} Games • {int((best_duo['wins']/best_duo['games'])*100)}% Winrate</div>
                </div>""", unsafe_allow_html=True)

                def norm(v, m): return min(100, (v/m)*100)
                r_cats = ['dmg_min', 'gold_min', 'vis_min', 'obj', 'kda']
                r_maxs = [1000, 600, 2.5, 8000, 5]
                d1 = [norm(avg_me.get(c,0), m) for c, m in zip(r_cats, r_maxs)]
                d2 = [norm(avg_duo.get(c,0), m) for c, m in zip(r_cats, r_maxs)]
                
                fig = go.Figure()
                for d, n, c in [(d1, t_safe, '#00c6ff'), (d2, duo_display, '#ff0055')]:
                    fig.add_trace(go.Scatterpolar(r=d, theta=['Combat', 'Gold', 'Vision', 'Obj', 'Survie'], fill='toself', name=n, line_color=c, opacity=0.7))
                fig.update_layout(polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#555', gridcolor='#444'), angularaxis=dict(linecolor='#555')),
                    showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=60, r=60, t=20, b=60), height=400,
                    legend=dict(font=dict(color='white'), orientation="h", y=-0.15, x=0.5, xanchor="center", bgcolor='rgba(0,0,0,0)'))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                def render_card(col, name, champ_list, stats, role, diff_stats, color, full_id):
                    badges = determine_badges(stats, role, T)
                    badges_html = "".join([f"<span class='badge {b[1]}'>{b[0]}</span>" for b in badges])
                    champs_html = "".join([f"<img src='{get_champ_url(x)}' style='width:55px; border-radius:50%; border:2px solid #333; margin:4px;'>" for x in champ_list])
                    rows = ""
                    labels = [("KDA", 'kda', 1, False), ("KP", 'kp', 100, True), ("DPM", 'dmg_min', 1, False), ("VIS/M", 'vis_min', 1, False), ("OBJ", 'obj', 1, False), ("GOLD/M", 'gold_min', 1, False)]
                    
                    for lbl, key, mult, is_pct in labels:
                        val = stats.get(key, 0)
                        d_val = diff_stats.get(key, 0)
                        v_str = f"{int(val*100)}%" if is_pct else (f"{val:.2f}" if key=='kda' else (f"{int(val/1000)}k" if val>1000 else f"{int(val)}"))
                        if is_pct: pct = d_val
                        else:
                            base = val - d_val
                            pct = (d_val / abs(base)) * 100 if abs(base) > 0.01 else (100 if val > base else 0)
                        cls = "pos" if pct > 0 else ("neg" if pct < 0 else "neutral")
                        sign = "+" if pct > 0 else ""
                        rows += f"""<div class="stat-item"><div class="stat-val-container"><div class="stat-val">{v_str}</div><span class='stat-diff {cls}'>{sign}{int(pct)}%</span></div><div class="stat-lbl">{lbl}</div></div>"""

                    col.markdown(f"""
                    <div class="player-card" style="border-top: 4px solid {color};">
                        <div class="player-name">{name}</div>
                        <a href="{get_dpm_url(full_id)}" target="_blank" class="dpm-btn">{T['btn_profile']}</a>
                        <div class="player-sub">{ROLE_ICONS.get(role, "FILL")}</div>
                        <div style="margin:10px 0;">{badges_html}</div>
                        <div style="margin-bottom:15px;">{champs_html}</div>
                        <div class="stat-grid">{rows}</div>
                    </div>""", unsafe_allow_html=True)

                d_me = {k: avg_me.get(k,0)-avg_duo.get(k,0) for k in avg_me if isinstance(avg_me[k],(int,float))}
                d_duo = {k: avg_duo.get(k,0)-avg_me.get(k,0) for k in avg_duo if isinstance(avg_duo[k],(int,float))}

                c1, c2 = st.columns(2, gap="large")
                render_card(c1, t_safe, [c[0] for c in Counter([x['champ'] for x in best_duo['s_me']]).most_common(3)], avg_me, r_me, d_me, '#00c6ff', riot_id_input)
                render_card(c2, duo_display, [c[0] for c in Counter(best_duo['champs']).most_common(3)], avg_duo, r_duo, d_duo, '#ff0055', duo_full_id)
