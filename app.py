import streamlit as st
import requests
import time
from urllib.parse import quote

# --- CONFIGURATION ---
st.set_page_config(page_title="Boost Detector V10 (EN)", layout="wide")

# --- API KEY ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ API Key not found. Please add it to Streamlit secrets.")
    st.stop()

# --- BACKGROUND ---
BACKGROUND_IMAGE_URL = "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123"

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
        max-width: 800px !important;
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

    /* --- THE BIG SCAN BUTTON --- */
    div.stButton > button {{
        width: 100%;
        background: linear-gradient(45deg, #ff0055, #ff4444);
        color: white;
        font-size: 26px;
        font-weight: 900;
        padding: 15px 0px;
        border: none;
        border-radius: 12px;
        text-transform: uppercase;
        box-shadow: 0 0 20px rgba(255, 0, 85, 0.4);
        transition: 0.3s;
        margin-top: 20px;
    }}
    div.stButton > button:hover {{
        background: linear-gradient(45deg, #ff4444, #ff0055);
        box-shadow: 0 0 40px rgba(255, 0, 85, 0.8);
        transform: scale(1.02);
        border: 1px solid white;
    }}
    div.stButton > button:active {{
        transform: scale(0.98);
    }}

    /* --- DISCRET DPM LINK --- */
    .dpm-link {{
        font-size: 12px;
        color: #888;
        text-decoration: none;
        transition: 0.3s;
        display: inline-block;
        margin-top: 5px;
        font-style: italic;
    }}
    .dpm-link:hover {{
        color: #ff0055;
        text-decoration: underline;
    }}

    /* RESULTS BOXES */
    .result-box {{ 
        padding: 30px; border-radius: 15px; text-align: center; font-size: 26px; font-weight: bold; color: white; margin-top: 40px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.5);
    }}
    .boosted {{ background-color: rgba(220, 20, 60, 0.9); border: 3px solid #ff4444; }}
    .clean {{ background-color: rgba(34, 139, 34, 0.9); border: 3px solid #00ff00; }}
    .stat-box {{ background-color: rgba(40,40,40,0.8); padding: 20px; border-radius: 12px; margin-top: 25px; color: #eee; font-size: 16px; border-left: 4px solid #ff0055; }}
    
    /* CUSTOM GENERIC */
    p, label, .stMarkdown, .stMetricLabel {{ color: #eee !important; }}
    div[data-testid="stMetricValue"] {{ font-size: 28px !important; color: #00ff00 !important; }}
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<div class="title-text">Are you a boosted piggy?</div>', unsafe_allow_html=True)

# --- INPUTS ---
col1, col2 = st.columns([3, 1], gap="medium")

with col1:
    riot_id_input = st.text_input("Enter Riot ID", placeholder="Name#TAG")
    # Link translated
    st.markdown('<a href="https://dpm.lol" target="_blank" class="dpm-link">🔍 Can\'t find the name? Search on dpm.lol</a>', unsafe_allow_html=True)

with col2:
    # Regions
    region_select = st.selectbox("Region", ["EUW1", "NA1", "KR", "EUN1", "TR1"])

# THE BIG BUTTON (Translated)
if st.button('START SCAN (20 GAMES)', type="primary"):
    
    # --- LOGIC ---
    def get_regions(region_code):
        if region_code in ["EUW1", "EUN1", "TR1", "RU"]: return "europe"
        elif region_code == "KR": return "asia"
        else: return "americas"

    if not riot_id_input or "#" not in riot_id_input:
        st.error("⚠️ Invalid format. You must include the #TAG.")
    else:
        name_raw, tag = riot_id_input.split("#")
        name_encoded = quote(name_raw)
        routing_region = get_regions(region_select)
        
        # 1. PUUID
        url_puuid = f"https://{routing_region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name_encoded}/{tag}?api_key={API_KEY}"
        
        with st.spinner('Scouring Riot servers for evidence...'):
            resp = requests.get(url_puuid)
            if resp.status_code != 200:
                st.error(f"API Error ({resp.status_code}). Check the Summoner Name.")
            else:
                puuid = resp.json().get("puuid")

                # 2. MATCHES
                url_matches = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=20&api_key={API_KEY}"
                match_ids = requests.get(url_matches).json()

                if not match_ids:
                    st.warning("No recent Ranked Solo/Duo games found.")
                else:
                    # 3. ANALYSIS
                    duo_data = {} 
                    progress_bar = st.progress(0)
                    
                    for i, match_id in enumerate(match_ids):
                        progress_bar.progress((i + 1) / len(match_ids))
                        
                        detail_url = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
                        data = requests.get(detail_url).json()
                        
                        if 'info' not in data: continue
                        
                        participants = data['info']['participants']
                        me = next((p for p in participants if p['puuid'] == puuid), None)
                        
                        if me:
                            my_k, my_d, my_a = me['kills'], me['deaths'], me['assists']
                            my_dmg = me['totalDamageDealtToChampions']

                            for p in participants:
                                if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                                    r_name = p.get('riotIdGameName', p.get('summonerName', 'Unknown'))
                                    r_tag = p.get('riotIdTagLine', '')
                                    identity = f"{r_name}#{r_tag}" if r_tag else r_name
                                    
                                    if identity not in duo_data:
                                        duo_data[identity] = {
                                            'games': 0, 'wins': 0,
                                            'duo_k': 0, 'duo_d': 0, 'duo_a': 0, 'duo_dmg': 0,
                                            'my_k': 0, 'my_d': 0, 'my_a': 0, 'my_dmg': 0
                                        }
                                    
                                    stats = duo_data[identity]
                                    stats['games'] += 1
                                    if p['win']: stats['wins'] += 1
                                    stats['duo_k'] += p['kills']
                                    stats['duo_d'] += p['deaths']
                                    stats['duo_a'] += p['assists']
                                    stats['duo_dmg'] += p['totalDamageDealtToChampions']
                                    
                                    stats['my_k'] += my_k
                                    stats['my_d'] += my_d
                                    stats['my_a'] += my_a
                                    stats['my_dmg'] += my_dmg

                        time.sleep(0.15) 

                    # 4. VERDICT
                    st.markdown("---")
                    
                    best_duo = None
                    max_games = 0

                    for identity, stats in duo_data.items():
                        if stats['games'] > max_games:
                            max_games = stats['games']
                            best_duo = (identity, stats)

                    if best_duo and max_games >= 4:
                        identity, s = best_duo
                        
                        # Calculations
                        duo_deaths = s['duo_d'] if s['duo_d'] > 0 else 1
                        duo_kda = round((s['duo_k'] + s['duo_a']) / duo_deaths, 2)
                        
                        my_deaths = s['my_d'] if s['my_d'] > 0 else 1
                        my_kda = round((s['my_k'] + s['my_a']) / my_deaths, 2)
                        
                        duo_avg_dmg = int(s['duo_dmg'] / s['games'])
                        my_avg_dmg = int(s['my_dmg'] / s['games'])
                        winrate = int((s['wins'] / s['games']) * 100)

                        st.markdown(f"""<div class="result-box boosted">🚨 SUSPECT DUO: {identity} 🚨</div>""", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align:center; font-size:18px;'>Seen <b>{s['games']} times</b> in the last 20 games.</p>", unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)

                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"<h3 style='text-align:center; color:white;'>YOU<br><span style='font-size:16px'>(when with them)</span></h3>", unsafe_allow_html=True)
                            st.metric("KDA", my_kda)
                            st.metric("Damage/Game", my_avg_dmg)
                        with c2:
                            st.markdown(f"<h3 style='text-align:center; color:red;'>THEM<br><span style='font-size:16px'>(the booster?)</span></h3>", unsafe_allow_html=True)
                            delta_kda = round(duo_kda - my_kda, 2)
                            delta_dmg = duo_avg_dmg - my_avg_dmg
                            st.metric("KDA", duo_kda, delta=delta_kda)
                            st.metric("Damage/Game", duo_avg_dmg, delta=delta_dmg)

                        st.markdown(f"<div class='stat-box'>Winrate together: <b>{winrate}%</b></div>", unsafe_allow_html=True)

                        if duo_kda > my_kda + 1.5 or duo_avg_dmg > my_avg_dmg + 5000:
                            st.error(f"VERDICT: 100% BOOSTED. They do the work, you steal the LP.")
                        elif winrate < 50:
                            st.warning("VERDICT: It's your duo, but you're losing. Change strategy.")
                        else:
                            st.success("VERDICT: Legit Duo. You have the same skill level.")
                    else:
                        st.markdown("""<div class="result-box clean">SOLO PLAYER</div>""", unsafe_allow_html=True)
                        st.markdown("<p style='text-align:center;'>No recurring duo detected. You are truly playing alone.</p>", unsafe_allow_html=True)
