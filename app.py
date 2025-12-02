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
st.set_page_config(page_title="LoL Duo Analyst V63", layout="wide")

# --- API KEY ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ API Key missing. Add RIOT_API_KEY to Streamlit secrets.")
    st.stop()

# --- ASSETS & CONSTANTS ---
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

# --- CSS MODERNE (HEXTECH DARK V3) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    
    .stApp {{
        background-image: url("{BACKGROUND_IMAGE_URL}");
        background-size: 150px; background-repeat: repeat; background-attachment: fixed;
    }}
    
    /* RECENTRAGE ET MARGES */
    .block-container {{
        max-width: 1400px !important; 
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        background: rgba(12, 12, 12, 0.96); backdrop-filter: blur(15px); /* Plus sombre */
        border-radius: 15px; border: 1px solid #333; box-shadow: 0 25px 60px rgba(0,0,0,0.95);
        margin-top: 20px !important;
    }}

    /* TITRE */
    .main-title {{
        font-size: 55px; font-weight: 900; text-align: center; margin-bottom: 30px; margin-top: 10px;
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 10px rgba(0, 114, 255, 0.5)); text-transform: uppercase;
    }}
    
    /* CARTE JOUEUR */
    .player-card {{
        background: rgba(30, 30, 30, 0.5); border-radius: 16px; padding: 25px; /* Plus sombre et aéré */
        border: 1px solid rgba(255,255,255,0.08); text-align: center; height: 100%;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.2);
    }}
    .player-name {{ font-size: 28px; font-weight: 800; color: white; margin-bottom: 5px; }}
    .player-sub {{ font-size: 14px; color: #aaa; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }}

    /* BADGES DE STYLE */
    .badge {{
        display: inline-block; padding: 4px 8px; border-radius: 4px; 
        font-size: 11px; font-weight: 700; margin: 2px; text-transform: uppercase;
    }}
    .b-green {{ background: rgba(0, 255, 153, 0.15); color: #00ff99; border: 1px solid #00ff99; }}
    .b-red {{ background: rgba(255, 68, 68, 0.15); color: #ff6666; border: 1px solid #ff4444; }}
    .b-blue {{ background: rgba(0, 191, 255, 0.15); color: #00BFFF; border: 1px solid #00BFFF; }}
    .b-gold {{ background: rgba(255, 215, 0, 0.15); color: #FFD700; border: 1px solid #FFD700; }}

    /* STATS GRID AVEC DIFF */
    .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px; margin-bottom: 0px; }}
    .stat-item {{ background: rgba(0,0,0,0.3); padding: 12px; border-radius: 10px; text-align: left; border: 1px solid rgba(255,255,255,0.05); }}
    .stat-val-container {{ display: flex; align-items: center; gap: 8px; }}
    .stat-val {{ font-size: 20px; font-weight: 700; color: white; }}
    .stat-lbl {{ font-size: 11px; color: #999; text-transform: uppercase; margin-top: 4px; font-weight: 600; letter-spacing: 0.5px; }}
    
    /* DIFFERENCES VERT/ROUGE */
    .stat-diff {{ font-size: 12px; font-weight: 700; padding: 2px 5px; border-radius: 4px; }}
    .pos {{ color: #00ff99; background: rgba(0,255,153,0.15); }} 
    .neg {{ color: #ff4444; background: rgba(255,68,68,0.15); }}
    .neutral {{ color: #888; }}

    /* VERDICT BANNER */
    .verdict-box {{
        text-align: center; padding: 30px; border-radius: 16px; margin: 20px 0 40px 0;
        background: rgba(20, 20, 20, 0.8); border: 2px solid #333; /* Plus sombre */
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
        text-transform: uppercase; transition: 0.3s; box-shadow: 0 0 15px rgba(255, 0, 85, 0.3);
    }}
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 25px rgba(255,0,60,0.5); }}
    
    /* HIDE INPUT LABEL */
    .stTextInput > label {{ display: none; }}
</style>
""", unsafe_allow_html=True)

# --- HEADER & LANGUAGE ---
c_title, c_lang = st.columns([5, 1])
with c_lang:
    selected_label = st.selectbox("Lang", list(LANG_MAP.keys()), label_visibility="collapsed")
    lang_code = LANG_MAP[selected_label]

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
        riot_id_input = st.text_input("HiddenLabel", placeholder="Ex: Kameto#EUW")
    with c2:
        st.markdown("<span style='font-size:14px; font-weight:700; color:#ddd;'>RÉGION</span>", unsafe_allow_html=True)
        region_select = st.selectbox("RegionLabel", ["EUW1", "NA1", "KR", "EUN1", "TR1"], label_visibility="collapsed")
    with c3:
        st.markdown("<span style='font-size:14px; font-weight:700; color:#ddd;'>MODE</span>", unsafe_allow_html=True)
        queue_label = st.selectbox("ModeLabel", list(QUEUE_MAP.keys()), label_visibility="collapsed")
    
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
    """Détermine des badges basés sur les stats par minute"""
    badges = []
    # Badges positifs
    if stats['kda'] >= 4.0: badges.append(("🛡️ KDA Player", "b-gold"))
    if stats['vis_min'] >= 2.0 or (role == "UTILITY" and stats['vis_min'] >= 2.5): badges.append(("👁️ Oracle", "b-blue")) 
    if stats['kp'] >= 0.65: badges.append(("🤝 Teamplayer", "b-green"))
    # Badges agressifs / Carry
    if stats['dmg_min'] >= 800: badges.append(("⚔️ 1v9 Machine", "b-red"))
    if stats['solokills'] >= 2.5: badges.append(("🩸 Duelist", "b-red"))
    if stats['obj'] >= 5000: badges.append(("🏰 Breacher", "b-gold"))
    # Badges négatifs
    if stats['kda'] < 1.5: badges.append(("👻 Grey Screen", "b-red"))
    if stats['vis_min'] < 0.4 and role != "ADC": badges.append(("🕶️ Blind", "b-red"))
    if stats['dmg_min'] < 300 and role not in ["UTILITY", "JUNGLE"]: badges.append(("💤 AFK Farm", "b-blue"))

    if not badges: badges.append(("⚖️ Standard", "b-blue"))
    return badges[:3] 

# --- FONCTION GRAPHIQUE AMÉLIORÉE ---
def create_radar(data_list, names, colors, title=None, height=400, show_legend=True):
    categories = ['Combat (DPM)', 'Gold', 'Vision', 'Objectifs', 'Survie (KDA)']
    fig = go.Figure()

    for i, data in enumerate(data_list):
        fig.add_trace(go.Scatterpolar(
            r=data,
            theta=categories,
            fill='toself',
            name=names[i],
            line_color=colors[i],
            opacity=0.7, # Plus vibrant
            marker=dict(size=5)
        ))

    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#555', gridcolor='#444', gridwidth=1), # Grille plus sombre et nette
            angularaxis=dict(linecolor='#555', gridcolor='#444', gridwidth=1, tickfont=dict(color='white', size=12, weight='bold')) # Labels plus clairs
        ),
        showlegend=show_legend,
        legend=dict(font=dict(color='white', size=12), orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
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
                        if duration_min < 5: continue 
                        
                        participants = info['participants']
                        me = next((p for p in participants if p['puuid'] == puuid), None)
                        if not me: continue
                        target_name = me['riotIdGameName']
                        
                        def extract_stats(p):
                            return {
                                'kills': p['kills'], 'deaths': p['deaths'], 'assists': p['assists'],
                                'dmg': p['totalDamageDealtToChampions'],
                                'gold': p['goldEarned'],
                                'vis': p['visionScore'],
                                'obj': p.get('damageDealtToObjectives', 0),
                                'towers': p.get('turretTakedowns', 0),
                                'kp': p.get('challenges', {}).get('killParticipation', 0),
                                'solokills': p.get('challenges', {}).get('soloKills', 0),
                                'champ': p['championName'],
                                'role': p.get('teamPosition', 'UNKNOWN'),
                                'win': p['win']
                            }
                        
                        my_s = extract_stats(me)
                        
                        with data_lock:
                            for p in participants:
                                if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                                    full_id = f"{p.get('riotIdGameName')}#{p.get('riotIdTagLine')}"
                                    if full_id not in duo_data:
                                        duo_data[full_id] = {
                                            'name': p.get('riotIdGameName'), 'games': 0, 'wins': 0,
                                            'champs': [], 'roles': [], 'stats_duo': [], 'stats_me': []
                                        }
                                    d = duo_data[full_id]
                                    d['games'] += 1
                                    if p['win']: d['wins'] += 1
                                    d['champs'].append(p['championName'])
                                    d['roles'].append(p.get('teamPosition', 'UNKNOWN'))
                                    
                                    # Normalisation minute
                                    duo_s = extract_stats(p)
                                    for s, norm in [(duo_s, d['stats_duo']), (my_s, d['stats_me'])]:
                                        n = s.copy()
                                        n['dmg_min'] = s['dmg'] / duration_min
                                        n['gold_min'] = s['gold'] / duration_min
                                        n['vis_min'] = s['vis'] / duration_min
                                        norm.append(n)
                    except Exception: pass

            # 4. ANALYSE DU MEILLEUR DUO
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
                winrate = int((best_duo['wins']/g)*100)
                
                try: role_duo = Counter(best_duo['roles']).most_common(1)[0][0]
                except: role_duo = "UNKNOWN"
                try: role_me = Counter([x['role'] for x in best_duo['stats_me']]).most_common(1)[0][0]
                except: role_me = "UNKNOWN"
                
                top_champs_duo = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                top_champs_me = [c[0] for c in Counter([x['champ'] for x in best_duo['stats_me']]).most_common(3)]
                
                # CALCUL MOYENNES
                def avg_stats(stat_list):
                    res = {}
                    keys = stat_list[0].keys()
                    for k in keys:
                        if isinstance(stat_list[0][k], (int, float)):
                            res[k] = sum(d[k] for d in stat_list) / len(stat_list)
                    return res

                avg_duo = avg_stats(best_duo['stats_duo'])
                avg_me = avg_stats(best_duo['stats_me'])
                
                def calc_kda(s): return round((s['kills'] + s['assists']) / max(1, s['deaths']), 2)
                avg_duo['kda'] = calc_kda(avg_duo)
                avg_me['kda'] = calc_kda(avg_me)

                # --- SCORE D'IMPACT V60 ---
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
                
                if ratio > 1.35: 
                    title, color, sub = "MVP TOTAL", "#FFD700", f"{target_name} est le carry indiscutable."
                elif ratio > 1.15: 
                    title, color, sub = "LEADER", "#00BFFF", f"{target_name} mène le jeu techniquement."
                elif ratio < 0.75: 
                    title, color, sub = "EN DIFFICULTÉ", "#ff4444", f"{target_name} a du mal à suivre {duo_name}."
                elif ratio < 0.9: 
                    title, color, sub = "SOUTIEN ACTIF", "#FFA500", f"{target_name} joue pour l'équipe."
                else: 
                    title, color, sub = "DUO FUSIONNEL", "#00ff99", "Synergie parfaite et impact équivalent."

                # AUTO SCROLL
                components.html(f"<script>window.parent.document.querySelector('.verdict-box').scrollIntoView({{behavior:'smooth'}});</script>", height=0)

                # UI VERDICT
                st.markdown(f"""
                <div class="verdict-box" style="border-color:{color}">
                    <div style="font-size:45px; font-weight:900; color:{color}; margin-bottom:10px;">{title}</div>
                    <div style="font-size:18px; color:#eee; font-style:italic;">"{sub}"</div>
                    <div style="margin-top:15px; color:#888; font-weight:600;">{g} Games ensemble • {winrate}% Winrate</div>
                </div>
                """, unsafe_allow_html=True)

                # PREPARATION DONNEES GRAPHIQUES
                def norm(val, max_v): return min(100, (val / max_v) * 100)
                data_me_norm = [norm(avg_me['dmg_min'], 1000), norm(avg_me['gold_min'], 600), norm(avg_me['vis_min'], 2.5), norm(avg_me['obj'], 8000), norm(avg_me['kda'], 5)]
                data_duo_norm = [norm(avg_duo['dmg_min'], 1000), norm(avg_duo['gold_min'], 600), norm(avg_duo['vis_min'], 2.5), norm(avg_duo['obj'], 8000), norm(avg_duo['kda'], 5)]

                # GRAPHIQUE CENTRAL COMPARATIF (AMÉLIORÉ & ASSOMBRI)
                fig_comp = create_radar([data_me_norm, data_duo_norm], [target_name, duo_name], ['#00c6ff', '#ff0055'], height=450)
                st.plotly_chart(fig_comp, use_container_width=True, config={'displayModeBar': False})
                
                # COLONNES JOUEURS
                col1, col2 = st.columns(2, gap="large")
                badges_me = determine_playstyle(avg_me, role_me)
                badges_duo = determine_playstyle(avg_duo, role_duo)
                
                def display_player_card(name, champs, stats, badges, role_icon, diff_stats, color_theme):
                    badges_html = "".join([f"<span class='badge {b[1]}'>{b[0]}</span>" for b in badges])
                    champs_html = "".join([f"<img src='{get_champ_url(c)}' style='width:55px; border-radius:50%; border:2px solid #333; margin:4px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);'>" for c in champs])
                    
                    # Fonction interne pour générer une ligne de stat avec diff
                    def stat_line(label, value, diff_val, is_percent=False, is_kda=False):
                        val_str = f"{int(value*100)}%" if is_percent else (f"{value:.2f}" if is_kda else (f"{int(value/1000)}k" if value > 1000 else f"{int(value)}"))
                        
                        diff_html = ""
                        if diff_val > 0: diff_html = f"<span class='stat-diff pos'>+{diff_val:.1f}</span>"
                        elif diff_val < 0: diff_html = f"<span class='stat-diff neg'>{diff_val:.1f}</span>"
                        else: diff_html = f"<span class='stat-diff neutral'>=</span>"

                        return f"""<div class="stat-item">
                            <div class="stat-val-container"><div class="stat-val">{val_str}</div>{diff_html}</div>
                            <div class="stat-lbl">{label}</div>
                        </div>"""

                    stat_grid_html = f"""<div class="stat-grid">
                        {stat_line("KDA", stats['kda'], diff_stats['kda'], is_kda=True)}
                        {stat_line("KP", stats['kp'], diff_stats['kp']*100, is_percent=True)}
                        {stat_line("DPM", stats['dmg_min'], diff_stats['dmg_min'])}
                        {stat_line("VIS/M", stats['vis_min'], diff_stats['vis_min'])}
                        {stat_line("OBJ DMG", stats['obj'], diff_stats['obj'])}
                        {stat_line("GOLD/M", stats['gold_min'], diff_stats['gold_min'])}
                    </div>"""

                    st.markdown(f"""
                    <div class="player-card" style="border-top: 4px solid {color_theme};">
                        <div class="player-name">{name}</div>
                        <div class="player-sub">{role_icon}</div>
                        <div style="margin:15px 0;">{badges_html}</div>
                        <div style="margin-bottom:20px;">{champs_html}</div>
                        {stat_grid_html}
                    </div>
                    """, unsafe_allow_html=True)
                    # PLUS DE PETIT GRAPHIQUE ICI

                # Calcul des différences pour l'affichage
                diff_me = {k: avg_me[k] - avg_duo[k] for k in avg_me if isinstance(avg_me[k], (int, float))}
                diff_duo = {k: avg_duo[k] - avg_me[k] for k in avg_duo if isinstance(avg_duo[k], (int, float))}

                with col1:
                    display_player_card(target_name, top_champs_me, avg_me, badges_me, ROLE_ICONS.get(role_me, "UNK"), diff_me, '#00c6ff')
                with col2:
                    display_player_card(duo_name, top_champs_duo, avg_duo, badges_duo, ROLE_ICONS.get(role_duo, "UNK"), diff_duo, '#ff0055')

            else:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="verdict-box" style="border-color:#888;">
                    <div style="font-size:32px; font-weight:900; color:#888;">LOUP SOLITAIRE</div>
                    <div style="font-size:16px; color:#aaa;">Aucun duo récurrent trouvé sur les 20 dernières parties.</div>
                </div>""", unsafe_allow_html=True)
