import streamlit as st
import requests
import time
from urllib.parse import quote
from collections import Counter

# --- CONFIGURATION ---
st.set_page_config(page_title="LoL Duo Investigator V22", layout="wide")

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

# --- CSS STYLES ---
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    .stApp {{
        background-image: url("{BACKGROUND_IMAGE_URL}");
        background-size: 150px;
        background-repeat: repeat;
        background-attachment: fixed;
    }}
    
    /* CONTAINER */
    .block-container {{
        max-width: 1100px !important;
        padding: 2rem !important;
        margin: auto !important;
        background: rgba(15, 15, 15, 0.95);
        backdrop-filter: blur(15px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 20px 50px rgba(0,0,0,0.8);
    }}
    
    /* TITLES */
    .main-title {{
        font-size: 50px; font-weight: 900; color: white;
        text-align: center; margin-bottom: 5px; text-transform: uppercase;
        text-shadow: 0 0 25px rgba(255, 0, 85, 0.5);
    }}
    
    /* VERDICT BOXES (Huge Header) */
    .verdict-container {{
        text-align: center;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        margin-top: 20px;
        border: 2px solid transparent;
    }}
    .v-boosted {{ background: rgba(220, 20, 60, 0.15); border-color: #ff4444; }}
    .v-booster {{ background: rgba(255, 215, 0, 0.1); border-color: #ffd700; }}
    .v-clean {{ background: rgba(0, 255, 153, 0.1); border-color: #00ff99; }}
    
    .verdict-title {{ font-size: 40px; font-weight: 900; margin-bottom: 10px; letter-spacing: -1px; }}
    .verdict-sub {{ font-size: 18px; color: #ddd; font-style: italic; }}

    /* STAT CARDS */
    .stat-card {{
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 3px solid #333;
    }}
    .card-label {{ font-size: 12px; color: #888; text-transform: uppercase; font-weight: 700; }}
    .card-val {{ font-size: 24px; color: white; font-weight: 800; }}
    .card-diff {{ font-size: 14px; font-weight: 600; margin-top: 2px; }}
    
    .pos {{ color: #00ff99; }}
    .neg {{ color: #ff4444; }}

    /* IMAGES */
    .champ-row {{ display: flex; justify-content: center; gap: 15px; margin-bottom: 20px; }}
    .champ-img {{ border-radius: 50%; border: 2px solid #444; width: 60px; height: 60px; transition: 0.3s; }}
    .champ-img:hover {{ transform: scale(1.1); border-color: white; }}
    
    /* FORM BUTTON */
    .stButton > button {{
        width: 100%;
        background: linear-gradient(135deg, #ff0055 0%, #ff2244 100%);
        color: white; font-weight: 800; padding: 12px; font-size: 18px;
        border: none; border-radius: 8px; text-transform: uppercase;
        margin-top: 10px; transition: 0.2s;
    }}
    .stButton > button:hover {{ transform: scale(1.01); box-shadow: 0 0 15px rgba(255,0,85,0.4); }}
    
    /* UTILS */
    p, label {{ color: #eee !important; }}
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<div class="main-title">LoL Duo Investigator</div>', unsafe_allow_html=True)

# --- FORMULAIRE (POUR QUE "ENTRÉE" MARCHE) ---
with st.form("search_form"):
    c1, c2 = st.columns([3, 1], gap="medium")
    with c1:
        riot_id_input = st.text_input("Riot ID", placeholder="Exemple: Sardoche#EUW")
    with c2:
        region_select = st.selectbox("Region", ["EUW1", "NA1", "KR", "EUN1", "TR1"])
    
    # Le bouton est maintenant dans le formulaire = Touche Entrée active
    submitted = st.form_submit_button("🚀 LANCER L'ANALYSE")


# --- FONCTIONS ---
def get_champ_url(champ_name):
    clean = champ_name.replace(" ", "").replace("'", "").replace(".", "")
    if clean == "Wukong": clean = "MonkeyKing"
    if clean == "RenataGlasc": clean = "Renata"
    return f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/img/champion/{clean}.png"

def render_comparison(title, val_a, val_b, unit=""):
    """Affiche une carte de stat avec la différence A vs B"""
    diff = val_a - val_b
    diff_display = round(diff, 1)
    if isinstance(val_a, int): diff_display = int(diff)
    
    color_class = "pos" if diff >= 0 else "neg"
    sign = "+" if diff > 0 else ""
    
    st.markdown(f"""
    <div class="stat-card" style="border-left-color: {'#00ff99' if diff>=0 else '#ff4444'};">
        <div class="card-label">{title}</div>
        <div class="card-val">{val_a}{unit}</div>
        <div class="card-diff {color_class}">{sign}{diff_display}{unit} vs Mate</div>
    </div>
    """, unsafe_allow_html=True)

# --- LOGIQUE ---
if submitted:
    
    def get_regions(region_code):
        if region_code in ["EUW1", "EUN1", "TR1", "RU"]: return "europe"
        elif region_code == "KR": return "asia"
        else: return "americas"

    if not riot_id_input or "#" not in riot_id_input:
        st.error("⚠️ Format invalide. Il faut le #TAG (Ex: Pseudo#EUW)")
    else:
        name_raw, tag = riot_id_input.split("#")
        name_encoded = quote(name_raw)
        region = get_regions(region_select)
        
        # 1. API CALLS
        with st.spinner('Connexion aux serveurs Riot...'):
            try:
                # PUUID
                url_acc = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name_encoded}/{tag}?api_key={API_KEY}"
                resp_acc = requests.get(url_acc)
                if resp_acc.status_code != 200:
                    st.error(f"Joueur introuvable (Erreur {resp_acc.status_code})")
                    st.stop()
                puuid = resp_acc.json().get("puuid")

                # MATCHES
                url_match = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=20&api_key={API_KEY}"
                match_ids = requests.get(url_match).json()
                
                if not match_ids:
                    st.warning("Aucune partie classée récente trouvée.")
                    st.stop()
            except Exception as e:
                st.error(f"Erreur API: {e}")
                st.stop()

            # 2. ANALYSIS LOOP
            duo_data = {} 
            progress_bar = st.progress(0)
            target_name = riot_id_input # Fallback name
            
            for i, match_id in enumerate(match_ids):
                progress_bar.progress((i + 1) / len(match_ids))
                
                url_det = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
                data = requests.get(url_det).json()
                if 'info' not in data: continue
                
                game_duration = data['info']['gameDuration'] 
                participants = data['info']['participants']
                
                me = next((p for p in participants if p['puuid'] == puuid), None)
                if me:
                    target_name = me.get('riotIdGameName', name_raw)
                    
                    # My Stats Wrapper
                    my_s = {
                        'kda': (me['kills'] + me['assists']) / max(1, me['deaths']),
                        'dmg': me['totalDamageDealtToChampions'],
                        'gold': me['goldEarned'],
                        'vis': me['visionScore'],
                        'obj': me.get('damageDealtToObjectives', 0),
                        'champ': me['championName'],
                        'win': me['win']
                    }

                    for p in participants:
                        if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                            full_id = f"{p.get('riotIdGameName')}#{p.get('riotIdTagLine')}"
                            
                            if full_id not in duo_data:
                                duo_data[full_id] = {
                                    'name': p.get('riotIdGameName'),
                                    'games': 0, 'wins': 0,
                                    'stats': {'kda':0, 'dmg':0, 'gold':0, 'vis':0, 'obj':0},
                                    'my_stats_vs': {'kda':0, 'dmg':0, 'gold':0, 'vis':0, 'obj':0},
                                    'champs': [],      # Duo champs
                                    'my_champs': []    # My champs with this duo
                                }
                            
                            d = duo_data[full_id]
                            d['games'] += 1
                            if p['win']: d['wins'] += 1
                            d['champs'].append(p['championName'])
                            d['my_champs'].append(my_s['champ'])
                            
                            # Accumulate Duo Stats
                            d['stats']['kda'] += (p['kills'] + p['assists']) / max(1, p['deaths'])
                            d['stats']['dmg'] += p['totalDamageDealtToChampions']
                            d['stats']['gold'] += p['goldEarned']
                            d['stats']['vis'] += p['visionScore']
                            d['stats']['obj'] += p.get('damageDealtToObjectives', 0)
                            
                            # Accumulate My Stats (vs this Duo)
                            d['my_stats_vs']['kda'] += my_s['kda']
                            d['my_stats_vs']['dmg'] += my_s['dmg']
                            d['my_stats_vs']['gold'] += my_s['gold']
                            d['my_stats_vs']['vis'] += my_s['vis']
                            d['my_stats_vs']['obj'] += my_s['obj']
                            
                time.sleep(0.05)

            # 3. FINAL PROCESSING
            progress_bar.empty()
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
                
                # Averages
                def avg(d, key): return int(d[key] / g)
                def avg_f(d, key): return round(d[key] / g, 2)
                
                s_me = best_duo['my_stats_vs']
                s_duo = best_duo['stats']
                
                # --- PILLAR LOGIC ---
                score_combat_me = (s_me['kda'] * 2) + (s_me['dmg'] / 1000)
                score_combat_duo = (s_duo['kda'] * 2) + (s_duo['dmg'] / 1000)
                
                score_eco_me = s_me['gold']
                score_eco_duo = s_duo['gold']
                
                score_vis_me = s_me['vis']
                score_vis_duo = s_duo['vis']
                
                score_obj_me = s_me['obj']
                score_obj_duo = s_duo['obj']
                
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

                # --- 1. DISPLAY VERDICT (BIG HEADER) ---
                if status == "BOOSTED":
                    st.markdown(f"""
                    <div class="verdict-container v-boosted">
                        <div class="verdict-title" style="color:#ff4444">🚨 PASSENGER DETECTED 🚨</div>
                        <div class="verdict-sub">{target_name} is being carried by {duo_name}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if "http" in CLOWN_IMAGE_URL: 
                        col_img1, col_img2, col_img3 = st.columns([1,2,1])
                        with col_img2: st.image(CLOWN_IMAGE_URL, use_column_width=True)

                elif status == "BOOSTER":
                    st.markdown(f"""
                    <div class="verdict-container v-booster">
                        <div class="verdict-title" style="color:#ffd700">👑 DRIVER DETECTED 👑</div>
                        <div class="verdict-sub">{target_name} is boosting {duo_name}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="verdict-container v-clean">
                        <div class="verdict-title" style="color:#00ff99">🤝 SOLID PARTNERSHIP 🤝</div>
                        <div class="verdict-sub">Equal contribution between {target_name} and {duo_name}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # --- 2. CHAMPIONS ROW ---
                st.markdown("<br>", unsafe_allow_html=True)
                c_row1, c_row2 = st.columns(2)
                
                # Get Top 3 Champs for ME
                my_top = [c[0] for c in Counter(best_duo['my_champs']).most_common(3)]
                # Get Top 3 Champs for DUO
                duo_top = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                
                with c_row1:
                    st.markdown(f"<h3 style='text-align:center'>{target_name}</h3>", unsafe_allow_html=True)
                    cols = st.columns(3)
                    for idx, ch in enumerate(my_top):
                        with cols[idx]: st.image(get_champ_url(ch), use_column_width=True)
                        
                with c_row2:
                    st.markdown(f"<h3 style='text-align:center'>{duo_name}</h3>", unsafe_allow_html=True)
                    cols = st.columns(3)
                    for idx, ch in enumerate(duo_top):
                        with cols[idx]: st.image(get_champ_url(ch), use_column_width=True)

                # --- 3. DETAILED STATS COLUMNS ---
                st.markdown("<br><hr><br>", unsafe_allow_html=True)
                col_stats1, col_stats2 = st.columns(2)
                
                with col_stats1:
                    st.markdown(f"<div style='text-align:center; color:#888; margin-bottom:10px'>STATS DE {target_name}</div>", unsafe_allow_html=True)
                    render_comparison("Combat (KDA)", avg_f(s_me, 'kda'), avg_f(s_duo, 'kda'))
                    render_comparison("Damage/Game", avg(s_me, 'dmg')//1000, avg(s_duo, 'dmg')//1000, unit="k")
                    render_comparison("Gold/Game", avg(s_me, 'gold')//1000, avg(s_duo, 'gold')//1000, unit="k")
                    render_comparison("Vision Score", avg(s_me, 'vis'), avg(s_duo, 'vis'))
                    render_comparison("Obj. Damage", avg(s_me, 'obj')//1000, avg(s_duo, 'obj')//1000, unit="k")

                with col_stats2:
                    st.markdown(f"<div style='text-align:center; color:#888; margin-bottom:10px'>STATS DE {duo_name}</div>", unsafe_allow_html=True)
                    # We render stats from Duo perspective
                    render_comparison("Combat (KDA)", avg_f(s_duo, 'kda'), avg_f(s_me, 'kda'))
                    render_comparison("Damage/Game", avg(s_duo, 'dmg')//1000, avg(s_me, 'dmg')//1000, unit="k")
                    render_comparison("Gold/Game", avg(s_duo, 'gold')//1000, avg(s_me, 'gold')//1000, unit="k")
                    render_comparison("Vision Score", avg(s_duo, 'vis'), avg(s_me, 'vis'))
                    render_comparison("Obj. Damage", avg(s_duo, 'obj')//1000, avg(s_me, 'obj')//1000, unit="k")

                # Recap Pilliers
                st.info(f"📊 **Analyse des Piliers :** {target_name} gagne sur **{my_wins}** aspects / {duo_name} gagne sur **{duo_wins}** aspects.")

            else:
                st.markdown("""<div class="verdict-container v-clean"><div class="verdict-title">SOLO PLAYER</div></div>""", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center;'>Aucun duo récurrent détecté sur les 20 dernières parties.</p>", unsafe_allow_html=True)
