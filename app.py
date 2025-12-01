import streamlit as st
import requests
import time
from urllib.parse import quote
from collections import Counter

# --- CONFIGURATION ---
st.set_page_config(page_title="True Carry Detector", layout="wide")

# --- API KEY ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ API Key missing. Please add RIOT_API_KEY to Streamlit secrets.")
    st.stop()

# --- IMAGES ---
BACKGROUND_IMAGE_URL = "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123"
CLOWN_IMAGE_URL = "https://raw.githubusercontent.com/[YOUR_GITHUB_NAME]/[REPO_NAME]/main/clown.jpg"

# --- CSS STYLES ---
st.markdown(
    f"""
    <style>
    /* Background */
    .stApp {{
        background-image: url("{BACKGROUND_IMAGE_URL}");
        background-size: 150px;
        background-repeat: repeat;
        background-attachment: fixed;
    }}
    
    /* MAIN CONTAINER */
    .block-container {{
        max-width: 950px !important;
        padding: 3rem !important;
        margin: auto !important;
        background-color: rgba(10, 10, 10, 0.95);
        border-radius: 25px;
        border: 1px solid #444;
        box-shadow: 0 0 30px rgba(0,0,0,0.9);
    }}

    /* TITLE */
    .title-text {{
        font-family: 'Segoe UI', sans-serif; 
        font-size: 45px; font-weight: 900; color: #ffffff;
        text-shadow: 0 0 15px #ff0055; text-align: center; margin-bottom: 30px;
        text-transform: uppercase; letter-spacing: 2px;
    }}

    /* GLOWING BUTTON */
    @keyframes glowing {{
        0% {{ box-shadow: 0 0 5px #ff0055; }}
        50% {{ box-shadow: 0 0 25px #ff0055, 0 0 10px #ff4444; }}
        100% {{ box-shadow: 0 0 5px #ff0055; }}
    }}

    div.stButton > button {{
        width: 100%;
        background: linear-gradient(90deg, #ff0055, #ff2222);
        color: white;
        font-size: 26px;
        font-weight: 900;
        padding: 18px 0px;
        border: none;
        border-radius: 12px;
        text-transform: uppercase;
        animation: glowing 2s infinite;
        transition: 0.3s;
        margin-top: 20px;
        letter-spacing: 1px;
    }}
    div.stButton > button:hover {{
        background: linear-gradient(90deg, #ff2222, #ff0055);
        transform: scale(1.02);
        border: 1px solid white;
    }}

    /* DPM LINK */
    .dpm-link {{
        font-size: 12px; color: #888; text-decoration: none;
        transition: 0.3s; display: inline-block; margin-top: 5px; font-style: italic;
    }}
    .dpm-link:hover {{ color: #ff0055; text-decoration: underline; }}

    /* RESULTS BOXES */
    .result-box {{ 
        padding: 20px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; color: white; margin-top: 30px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.5);
    }}
    .boosted {{ background-color: rgba(220, 20, 60, 0.9); border: 3px solid #ff4444; }}
    .booster {{ background-color: rgba(255, 215, 0, 0.15); border: 3px solid #FFD700; color: #FFD700; }} 
    .clean {{ background-color: rgba(34, 139, 34, 0.9); border: 3px solid #00ff00; }}
    
    p, label, .stMarkdown, .stMetricLabel {{ color: #eee !important; }}
    div[data-testid="stMetricValue"] {{ font-size: 28px !important; color: #00ff00 !important; }}
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<div class="title-text">WHO IS CARRYING WHO?</div>', unsafe_allow_html=True)

# --- INPUTS ---
col1, col2 = st.columns([3, 1], gap="medium")

with col1:
    riot_id_input = st.text_input("Player Riot ID", placeholder="Name#TAG")
    st.markdown('<a href="https://dpm.lol" target="_blank" class="dpm-link">🔍 Can\'t find the ID? Search on dpm.lol</a>', unsafe_allow_html=True)

with col2:
    region_select = st.selectbox("Region", ["EUW1", "NA1", "KR", "EUN1", "TR1"])

# BUTTON
if st.button('🚀 LAUNCH TACTICAL ANALYSIS (20 GAMES)', type="primary"):
    
    # --- LOGIC ---
    def get_regions(region_code):
        if region_code in ["EUW1", "EUN1", "TR1", "RU"]: return "europe"
        elif region_code == "KR": return "asia"
        else: return "americas"

    if not riot_id_input or "#" not in riot_id_input:
        st.error("⚠️ Invalid format. Include the #TAG.")
    else:
        name_raw, tag = riot_id_input.split("#")
        name_encoded = quote(name_raw)
        routing_region = get_regions(region_select)
        
        # 1. PUUID
        url_puuid = f"https://{routing_region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name_encoded}/{tag}?api_key={API_KEY}"
        
        with st.spinner('Analyzing combat data...'):
            resp = requests.get(url_puuid)
            if resp.status_code != 200:
                st.error(f"API Error ({resp.status_code}). Check Riot ID.")
            else:
                puuid = resp.json().get("puuid")

                # 2. MATCHES
                url_matches = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=20&api_key={API_KEY}"
                match_ids = requests.get(url_matches).json()

                if not match_ids:
                    st.warning("No recent Ranked Solo games found.")
                else:
                    # 3. ANALYSIS
                    duo_data = {} 
                    progress_bar = st.progress(0)
                    target_display_name = riot_id_input 
                    
                    for i, match_id in enumerate(match_ids):
                        progress_bar.progress((i + 1) / len(match_ids))
                        
                        detail_url = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
                        data = requests.get(detail_url).json()
                        
                        if 'info' not in data: continue
                        
                        participants = data['info']['participants']
                        me = next((p for p in participants if p['puuid'] == puuid), None)
                        
                        if me:
                            target_display_name = me.get('riotIdGameName', name_raw)

                            # My Stats
                            my_k, my_d, my_a = me['kills'], me['deaths'], me['assists']
                            my_dmg = me['totalDamageDealtToChampions']
                            my_champ = me['championName']
                            # Objectives matter now!
                            my_towers = me.get('challenges', {}).get('turretTakedowns', 0)
                            my_obj_dmg = me.get('damageDealtToObjectives', 0)

                            for p in participants:
                                if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                                    r_name = p.get('riotIdGameName', p.get('summonerName', 'Unknown'))
                                    r_tag = p.get('riotIdTagLine', '')
                                    full_identity = f"{r_name}#{r_tag}" if r_tag else r_name
                                    
                                    if full_identity not in duo_data:
                                        duo_data[full_identity] = {
                                            'clean_name': r_name,
                                            'games': 0, 'wins': 0,
                                            'duo_k': 0, 'duo_d': 0, 'duo_a': 0, 'duo_dmg': 0,
                                            'duo_towers': 0, 'duo_obj_dmg': 0,
                                            'duo_champs': [],
                                            'my_k': 0, 'my_d': 0, 'my_a': 0, 'my_dmg': 0,
                                            'my_towers': 0, 'my_obj_dmg': 0,
                                            'my_champs': []
                                        }
                                    
                                    stats = duo_data[full_identity]
                                    stats['games'] += 1
                                    if p['win']: stats['wins'] += 1
                                    
                                    stats['duo_k'] += p['kills']
                                    stats['duo_d'] += p['deaths']
                                    stats['duo_a'] += p['assists']
                                    stats['duo_dmg'] += p['totalDamageDealtToChampions']
                                    stats['duo_towers'] += p.get('challenges', {}).get('turretTakedowns', 0)
                                    stats['duo_obj_dmg'] += p.get('damageDealtToObjectives', 0)
                                    stats['duo_champs'].append(p['championName'])
                                    
                                    stats['my_k'] += my_k
                                    stats['my_d'] += my_d
                                    stats['my_a'] += my_a
                                    stats['my_dmg'] += my_dmg
                                    stats['my_towers'] += my_towers
                                    stats['my_obj_dmg'] += my_obj_dmg
                                    stats['my_champs'].append(my_champ)

                        time.sleep(0.12) 

                    # 4. VERDICT
                    st.markdown("---")
                    
                    best_duo_key = None
                    best_duo_stats = None
                    max_games = 0

                    for identity, stats in duo_data.items():
                        if stats['games'] > max_games:
                            max_games = stats['games']
                            best_duo_key = identity
                            best_duo_stats = stats

                    if best_duo_stats and max_games >= 4:
                        s = best_duo_stats
                        duo_name_display = s['clean_name']
                        games = s['games']
                        
                        # --- RAW STATS ---
                        duo_deaths = s['duo_d'] if s['duo_d'] > 0 else 1
                        duo_kda = round((s['duo_k'] + s['duo_a']) / duo_deaths, 2)
                        my_deaths = s['my_d'] if s['my_d'] > 0 else 1
                        my_kda = round((s['my_k'] + s['my_a']) / my_deaths, 2)
                        
                        duo_avg_dmg = int(s['duo_dmg'] / games)
                        my_avg_dmg = int(s['my_dmg'] / games)
                        
                        duo_avg_towers = round(s['duo_towers'] / games, 1)
                        my_avg_towers = round(s['my_towers'] / games, 1)
                        
                        duo_avg_obj = int(s['duo_obj_dmg'] / games)
                        my_avg_obj = int(s['my_obj_dmg'] / games)
                        
                        winrate = int((s['wins'] / games) * 100)

                        my_top_champs = [c[0] for c in Counter(s['my_champs']).most_common(3)]
                        duo_top_champs = [c[0] for c in Counter(s['duo_champs']).most_common(3)]
                        
                        # --- SCORING SYSTEM (FAIRNESS LOGIC) ---
                        # Formula: (KDA * 3) + (Dmg/1000) + (ObjDmg/1000) + (Towers * 2)
                        
                        my_score = (my_kda * 3) + (my_avg_dmg / 1000) + (my_avg_obj / 1000) + (my_avg_towers * 2)
                        duo_score = (duo_kda * 3) + (duo_avg_dmg / 1000) + (duo_avg_obj / 1000) + (duo_avg_towers * 2)
                        
                        score_diff = duo_score - my_score
                        
                        # DETERMINE STATUS BASED ON SCORE GAP
                        # Needs a significant gap (> 15% diff approx) to be called "Boosted"
                        
                        if score_diff > 8: # Duo score is much higher
                            status = "BOOSTED"
                        elif score_diff < -8: # My score is much higher
                            status = "BOOSTER"
                        else:
                            status = "CLEAN"

                        # --- HEADER DISPLAY ---
                        if status == "BOOSTED":
                             st.markdown(f"""<div class="result-box boosted">🚨 VIP ESCORT DETECTED: {duo_name_display} 🚨</div>""", unsafe_allow_html=True)
                             if "http" in CLOWN_IMAGE_URL:
                                st.image(CLOWN_IMAGE_URL, caption=f"Tactical overview", width=500)
                             
                             col1_title = f"{target_display_name}<br><span style='font-size:18px'>(The Passenger)</span>"
                             col1_color = "white"
                             col2_title = f"{duo_name_display}<br><span style='font-size:18px'>(The Driver)</span>"
                             col2_color = "red"

                        elif status == "BOOSTER":
                             st.markdown(f"""<div class="result-box booster">👑 MERCENARY DETECTED: {target_display_name} 👑<br><span style='font-size:16px'>Your back must hurt...</span></div>""", unsafe_allow_html=True)
                             
                             col1_title = f"{target_display_name}<br><span style='font-size:18px'>(The Driver)</span>"
                             col1_color = "#FFD700"
                             col2_title = f"{duo_name_display}<br><span style='font-size:18px'>(The Backpack)</span>"
                             col2_color = "white"
                        
                        else:
                             st.markdown(f"""<div class="result-box clean">🤝 EQUAL SKILL DETECTED 🤝</div>""", unsafe_allow_html=True)
                             col1_title = target_display_name
                             col1_color = "white"
                             col2_title = duo_name_display
                             col2_color = "white"

                        st.markdown(f"<p style='text-align:center; font-size:18px;'>Seen <b>{games} times</b> (Winrate: {winrate}%).</p>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)

                        # --- STATS COLUMNS ---
                        c1, c2 = st.columns(2)
                        
                        # COLUMN 1 (TARGET)
                        with c1:
                            st.markdown(f"<h3 style='text-align:center; color:{col1_color};'>{col1_title}</h3>", unsafe_allow_html=True)
                            st.markdown(f"<div style='text-align:center; color:#888; margin-bottom:10px;'>Played: {', '.join(my_top_champs)}</div>", unsafe_allow_html=True)
                            
                            st.metric("KDA", my_kda)
                            st.metric("Damage/Game", my_avg_dmg)
                            st.metric("Towers/Game", my_avg_towers)
                            st.metric("Obj. Damage/Game", my_avg_obj)

                        # COLUMN 2 (DUO)
                        with c2:
                            st.markdown(f"<h3 style='text-align:center; color:{col2_color};'>{col2_title}</h3>", unsafe_allow_html=True)
                            st.markdown(f"<div style='text-align:center; color:#888; margin-bottom:10px;'>Played: {', '.join(duo_top_champs)}</div>", unsafe_allow_html=True)
                            
                            st.metric("KDA", duo_kda, delta=round(duo_kda - my_kda, 2))
                            st.metric("Damage/Game", duo_avg_dmg, delta=duo_avg_dmg - my_avg_dmg)
                            st.metric("Towers/Game", duo_avg_towers, delta=round(duo_avg_towers - my_avg_towers, 1))
                            st.metric("Obj. Damage/Game", duo_avg_obj, delta=duo_avg_obj - my_avg_obj)

                        # FINAL SENTENCE
                        st.markdown("<br>", unsafe_allow_html=True)
                        if status == "BOOSTED":
                            st.error(f"VERDICT: {duo_name_display} has a higher overall impact score ({int(duo_score)} vs {int(my_score)}).")
                        elif status == "BOOSTER":
                            st.warning(f"VERDICT: {target_display_name} has a higher overall impact score ({int(my_score)} vs {int(duo_score)}).")
                        else:
                            st.success(f"VERDICT: Scores are very close ({int(my_score)} vs {int(duo_score)}). Perfect synergy.")
                            
                    else:
                        st.markdown("""<div class="result-box clean">LONE WOLF OPERATOR</div>""", unsafe_allow_html=True)
                        st.markdown("<p style='text-align:center;'>No recurring duo detected.</p>", unsafe_allow_html=True)
