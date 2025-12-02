import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import plotly.graph_objects as go
import concurrent.futures
import threading
from collections import Counter

# --- CONFIGURATION ---
st.set_page_config(page_title="LoL Duo Analyst V60", layout="wide")

# --- API KEY ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ API Key missing. Add RIOT_API_KEY to Streamlit secrets.")
    st.stop()

# --- ASSETS & CONSTANTS ---
BACKGROUND_IMAGE_URL = "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123"

# Mapping des Queues
QUEUE_MAP = {
    "Ranked Solo/Duo": 420,
    "Ranked Flex": 440,
    "Draft Normal": 400,
    "ARAM": 450,
    "Arena": 1700
}

# Icônes de Rôle
ROLE_ICONS = {
    "TOP": "🛡️ TOP", "JUNGLE": "🌲 JUNGLE", "MIDDLE": "🧙 MID", 
    "BOTTOM": "🏹 ADC", "UTILITY": "🩹 SUPP", "UNKNOWN": "❓ FILL"
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
        max-width: 1400px !important; padding: 2rem !important;
        background: rgba(12, 12, 12, 0.95); backdrop-filter: blur(15px);
        border-radius: 15px; border: 1px solid #333; box-shadow: 0 20px 50px rgba(0,0,0,0.9);
    }}

    /* TITRE */
    .main-title {{
        font-size: 55px; font-weight: 900; text-align: center; margin-bottom: 10px;
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 10px rgba(0, 114, 255, 0.5));
    }}
    
    /* CARTE JOUEUR */
    .player-card {{
        background: rgba(255, 255, 255, 0.03); border-radius: 16px; padding: 20px;
        border: 1px solid rgba(255,255,255,0.05); text-align: center;
    }}
    .player-name {{ font-size: 28px; font-weight: 800; color: white; margin-bottom: 5px; }}
    .player-sub {{ font-size: 14px; color: #aaa; font-weight: 600; letter-spacing: 1px; }}

    /* BADGES */
    .badge {{
        display: inline-block; padding: 4px 8px; border-radius: 4px; 
        font-size: 11px; font-weight: 700; margin: 2px;
    }}
    .b-green {{ background: rgba(0, 255, 153, 0.15); color: #00ff99; border: 1px solid #00ff99; }}
    .b-red {{ background: rgba(255, 68, 68, 0.15); color: #ff6666; border: 1px solid #ff4444; }}
    .b-blue {{ background: rgba(0, 191, 255, 0.15); color: #00BFFF; border: 1px solid #00BFFF; }}
    .b-gold {{ background: rgba(255, 215, 0, 0.15); color: #FFD700; border: 1px solid #FFD700; }}

    /* STATS GRID */
    .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }}
    .stat-item {{ background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; }}
    .stat-val {{ font-size: 18px; font-weight: 700; color: white; }}
    .stat-lbl {{ font-size: 11px; color: #888; text-transform: uppercase; }}
    
    /* VERDICT BANNER */
    .verdict-box {{
        text-align: center; padding: 30px; border-radius: 16px; margin: 20px 0;
        background: rgba(0,0,0,0.4); border: 2px solid #333;
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
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 20px rgba(255,0,60,0.4); }}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<div class="main-title">LoL Duo Analyst</div>', unsafe_allow_html=True)

# --- FORMULAIRE ---
with st.form("search_form"):
    c1, c2, c3 = st.columns([3, 1, 1], gap="small")
    with c1:
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
            <span style="font-size:14px; font-weight:700; color:#ddd;">RIOT ID</span>
            <a href="https://dpm.lol" target="_blank" class="dpm-btn">🔗 Check dpm.lol</a>
        </div>""", unsafe_allow_html=True)
        riot_id_input = st.text_input("HiddenLabel", placeholder="Ex: Kameto#EUW", label_visibility="collapsed")
    with c2:
        st.markdown("<span style='font-size:14px; font-weight:700; color:#ddd;'>RÉGION</span>", unsafe_allow_html=True)
        region_select = st.selectbox("Région", ["EUW1", "NA1", "KR", "EUN1", "TR1"], label_visibility="collapsed")
    with c3:
        st.markdown("<span style='font-size:14px; font-weight:700; color:#ddd;'>MODE</span>", unsafe_allow_html=True)
        queue_label = st.selectbox("Mode", list(QUEUE_MAP.keys()), label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("LANCER L'ANALYSE COMPLÈTE")

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

# --- LOGIQUE SCORE & STYLE ---
def determine_playstyle(stats, role):
    badges = []
    
    # Badges positifs
    if stats['kda'] >= 4.0: badges.append(("🛡️ KDA Player", "b-gold"))
    if stats['vis_min'] >= 2.0: badges.append(("👁️ Oracle", "b-blue")) # >2 vision/min c'est énorme
    if stats['kp'] >= 0.65: badges.append(("🤝 Teamplayer", "b-green"))
    
    # Badges agressifs
    if stats['dmg_min'] >= 800: badges.append(("⚔️ 1v9 Machine", "b-red"))
    if stats['solokills'] >= 3: badges.append(("🩸 Duelist", "b-red"))
    
    # Badges négatifs (subtils)
    if stats['kda'] < 1.5: badges.append(("👻 Grey Screen", "b-red"))
    if stats['vis_min'] < 0.5 and role == "UTILITY": badges.append(("🕶️ Blind Supp", "b-red"))
    if stats['dmg_min'] < 300 and role not in ["UTILITY", "JUNGLE"]: badges.append(("💤 AFK Farm", "b-blue"))

    # Fallback
    if not badges: badges.append(("⚖️ Standard", "b-blue"))
    
    return badges[:3] # Max 3 badges

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
        
        with st.spinner("Analyse tactique des données Riot..."):
            try:
                # 1. PUUID
                r_acc = get_puuid(quote(name_raw), tag, region, API_KEY)
                if r_acc.status_code != 200:
                    st.error("Joueur introuvable.")
                    st.stop()
                puuid = r_acc.json().get("puuid")
                
                # 2. MATCHS
                r_match = get_matches(puuid, region, API_KEY, q_id)
                match_ids = r_match.json()
                if not match_ids:
                    st.warning(f"Aucune partie trouvée en {queue_label}.")
                    st.stop()
            except Exception as e:
                st.error(f"Erreur API: {e}")
                st.stop()

            # 3. PROCESSING PARALLÈLE
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
                        if duration_min < 5: continue # Remake
                        
                        me = next((p for p in info['participants'] if p['puuid'] == puuid), None)
                        if not me: continue
                        target_name = me['riotIdGameName']
                        
                        # Helper extraction stats
                        def extract_stats(p):
                            return {
                                'kills': p['kills'], 'deaths': p['deaths'], 'assists': p['assists'],
                                'dmg': p['totalDamageDealtToChampions'],
                                'gold': p['goldEarned'],
                                'vis': p['visionScore'],
                                'obj': p.get('damageDealtToObjectives', 0),
                                'cc': p.get('timeCCingOthers', 0),
                                'towers': p.get('turretTakedowns', 0),
                                'kp': p.get('challenges', {}).get('killParticipation', 0),
                                'solokills': p.get('challenges', {}).get('soloKills', 0),
                                'champ': p['championName'],
                                'role': p.get('teamPosition', 'UNKNOWN'),
                                'win': p['win']
                            }
                        
                        my_s = extract_stats(me)
                        
                        with data_lock:
                            for p in info['participants']:
                                if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                                    full_id = f"{p.get('riotIdGameName')}#{p.get('riotIdTagLine')}"
                                    
                                    if full_id not in duo_data:
                                        duo_data[full_id] = {
                                            'name': p.get('riotIdGameName'),
                                            'games': 0, 'wins': 0,
                                            'champs': [], 'roles': [],
                                            'stats_duo': [], 'stats_me': []
                                        }
                                    
                                    d = duo_data[full_id]
                                    d['games'] += 1
                                    if p['win']: d['wins'] += 1
                                    d['champs'].append(p['championName'])
                                    d['roles'].append(p.get('teamPosition', 'UNKNOWN'))
                                    
                                    # On stocke les stats brutes normalisées par minute pour moyenne ultérieure
                                    duo_s = extract_stats(p)
                                    
                                    # Normalisation minute
                                    norm_duo = duo_s.copy()
                                    norm_duo['dmg_min'] = duo_s['dmg'] / duration_min
                                    norm_duo['gold_min'] = duo_s['gold'] / duration_min
                                    norm_duo['vis_min'] = duo_s['vis'] / duration_min
                                    
                                    norm_me = my_s.copy()
                                    norm_me['dmg_min'] = my_s['dmg'] / duration_min
                                    norm_me['gold_min'] = my_s['gold'] / duration_min
                                    norm_me['vis_min'] = my_s['vis'] / duration_min
                                    
                                    d['stats_duo'].append(norm_duo)
                                    d['stats_me'].append(norm_me)

                    except Exception: pass

            # 4. ANALYSE DU MEILLEUR DUO
            st.markdown("<div id='result'></div>", unsafe_allow_html=True)
            
            best_duo = None
            max_g = 0
            for k, v in duo_data.items():
                if v['games'] > max_g:
                    max_g = v['games']
                    best_duo = v
            
            # --- AFFICHAGE ---
            if best_duo and max_g >= 2:
                g = best_duo['games']
                duo_name = best_duo['name']
                winrate = int((best_duo['wins']/g)*100)
                
                # Rôle Principal
                try: role_duo = Counter(best_duo['roles']).most_common(1)[0][0]
                except: role_duo = "UNKNOWN"
                
                # Champs
                top_champs_duo = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                top_champs_me = [c[0] for c in Counter([x['champ'] for x in best_duo['stats_me']]).most_common(3)]
                
                # --- CALCUL MOYENNES ---
                def avg_stats(stat_list):
                    res = {}
                    keys = stat_list[0].keys()
                    for k in keys:
                        if isinstance(stat_list[0][k], (int, float)):
                            res[k] = sum(d[k] for d in stat_list) / len(stat_list)
                    return res

                avg_duo = avg_stats(best_duo['stats_duo'])
                avg_me = avg_stats(best_duo['stats_me'])
                
                # --- CALCUL KDA ---
                def calc_kda(s): return round((s['kills'] + s['assists']) / max(1, s['deaths']), 2)
                avg_duo['kda'] = calc_kda(avg_duo)
                avg_me['kda'] = calc_kda(avg_me)

                # --- SCORE D'IMPACT (V60 - ULTRA FAIR) ---
                # On compare selon le rôle du joueur
                def get_impact_score(s, role):
                    score = 0
                    # Base KDA (Max 4 pts)
                    score += min(4, s['kda']) 
                    # KP (Max 3 pts)
                    score += (s['kp'] * 3)
                    # Vision (Max 2 pts)
                    if role == "UTILITY": score += min(2, s['vis_min'] / 1.5) # Support doit avoir > 1.5 vis/min
                    else: score += min(1, s['vis_min'] / 0.8)
                    # Dégâts (Max 3 pts)
                    if role not in ["UTILITY"]: score += min(3, s['dmg_min'] / 800)
                    # Objectifs (Max 3 pts)
                    if role == "JUNGLE": score += min(3, s['obj'] / 6000)
                    else: score += min(2, s['towers'])
                    
                    return score

                score_me = get_impact_score(avg_me, avg_me.get('role', 'UNKNOWN')) # On prend le rôle moyen ? Non, simplifié
                score_duo = get_impact_score(avg_duo, role_duo)
                
                ratio = score_me / max(0.1, score_duo)
                
                # --- VERDICT ---
                if ratio > 1.3: 
                    title, color, sub = "MVP TOTAL", "#FFD700", f"{target_name} est bien meilleur que {duo_name}."
                elif ratio > 1.1: 
                    title, color, sub = "LEADER", "#00BFFF", f"{target_name} mène le jeu."
                elif ratio < 0.7: 
                    title, color, sub = "EN DIFFICULTÉ", "#ff4444", f"{target_name} se fait carry par {duo_name}."
                elif ratio < 0.9: 
                    title, color, sub = "SOUTIEN ACTIF", "#FFA500", f"{target_name} aide {duo_name} à gagner."
                else: 
                    title, color, sub = "DUO FUSIONNEL", "#00ff99", "Synergie parfaite et impact égal."

                # --- AUTO SCROLL ---
                components.html(f"<script>window.parent.document.querySelector('.verdict-box').scrollIntoView({{behavior:'smooth'}});</script>", height=0)

                # --- UI RESULTAT ---
                st.markdown(f"""
                <div class="verdict-box" style="border-color:{color}">
                    <div style="font-size:45px; font-weight:900; color:{color}; margin-bottom:10px;">{title}</div>
                    <div style="font-size:18px; color:#eee; font-style:italic;">"{sub}"</div>
                    <div style="margin-top:15px; color:#888; font-weight:600;">{g} Games ensemble • {winrate}% Winrate</div>
                </div>
                """, unsafe_allow_html=True)
                
                # --- COLONNES COMPARATIVES ---
                col1, col2 = st.columns(2, gap="large")
                
                # Badges
                badges_me = determine_playstyle(avg_me, "UNKNOWN") # Rôle moyen non calculé ici pour simplicité
                badges_duo = determine_playstyle(avg_duo, role_duo)
                
                def display_player(name, champs, stats, badges, is_left):
                    align = "left" if is_left else "right"
                    # Badges HTML
                    badges_html = "".join([f"<span class='badge {b[1]}'>{b[0]}</span>" for b in badges])
                    
                    # Champs HTML
                    champs_html = ""
                    for c in champs:
                        champs_html += f"<img src='{get_champ_url(c)}' style='width:50px; border-radius:50%; border:2px solid #333; margin:2px;'>"
                    
                    st.markdown(f"""
                    <div class="player-card">
                        <div class="player-name">{name}</div>
                        <div style="margin-bottom:10px;">{badges_html}</div>
                        <div style="margin-bottom:15px;">{champs_html}</div>
                        <div class="stat-grid">
                            <div class="stat-item"><div class="stat-val">{stats['kda']}</div><div class="stat-lbl">KDA</div></div>
                            <div class="stat-item"><div class="stat-val">{int(stats['kp']*100)}%</div><div class="stat-lbl">PARTICIPATION</div></div>
                            <div class="stat-item"><div class="stat-val">{int(stats['dmg_min'])}</div><div class="stat-lbl">DMG/MIN</div></div>
                            <div class="stat-item"><div class="stat-val">{int(stats['vis_min'])}</div><div class="stat-lbl">VISION/MIN</div></div>
                            <div class="stat-item"><div class="stat-val">{int(stats['gold_min'])}</div><div class="stat-lbl">GOLD/MIN</div></div>
                            <div class="stat-item"><div class="stat-val">{int(stats['obj'])}</div><div class="stat-lbl">OBJ DMG</div></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Radar Chart (Petit graph en dessous)
                    categories = ['Combat', 'Gold', 'Vision', 'Obj', 'Survie']
                    # Normalisation arbitraire pour le graph (0-100)
                    val_combat = min(100, (stats['dmg_min']/1000)*100)
                    val_gold = min(100, (stats['gold_min']/600)*100)
                    val_vis = min(100, (stats['vis_min']/2.5)*100)
                    val_obj = min(100, (stats['obj']/8000)*100)
                    val_surv = min(100, (stats['kda']/5)*100)
                    
                    fig = go.Figure(data=go.Scatterpolar(
                        r=[val_combat, val_gold, val_vis, val_obj, val_surv],
                        theta=categories,
                        fill='toself',
                        line_color='#00c6ff' if is_left else '#ff0055',
                        opacity=0.7
                    ))
                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=False, range=[0, 100])),
                        showlegend=False,
                        margin=dict(l=20, r=20, t=20, b=20),
                        height=200,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white')
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                with col1:
                    display_player(target_name, top_champs_me, avg_me, badges_me, True)
                with col2:
                    display_player(duo_name, top_champs_duo, avg_duo, badges_duo, False)

            else:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="verdict-box" style="border-color:#888;">
                    <div style="font-size:32px; font-weight:900; color:#888;">LOUP SOLITAIRE</div>
                    <div style="font-size:16px; color:#aaa;">Aucun duo récurrent trouvé sur les 20 dernières parties.</div>
                </div>""", unsafe_allow_html=True)
