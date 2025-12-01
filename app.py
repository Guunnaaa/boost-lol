import streamlit as st
import requests
import time
from urllib.parse import quote
from collections import Counter

# --- CONFIGURATION ---
st.set_page_config(page_title="LoL Performance Analyzer", layout="wide")

# --- API KEY ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ API Key missing. Add RIOT_API_KEY to Streamlit secrets.")
    st.stop()

# --- IMAGES ---
BACKGROUND_IMAGE_URL = "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123"
CLOWN_IMAGE_URL = "https://raw.githubusercontent.com/[YOUR_GITHUB_NAME]/[REPO_NAME]/main/clown.jpg"

# --- CSS STYLES ---
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("{BACKGROUND_IMAGE_URL}");
        background-size: 150px;
        background-repeat: repeat;
        background-attachment: fixed;
    }}
    .block-container {{
        max-width: 1200px !important; /* LARGEUR MAXIMALE */
        padding: 2rem !important;
        margin: auto !important;
        background-color: rgba(15, 15, 15, 0.96);
        border-radius: 20px;
        border: 1px solid #333;
        box-shadow: 0 0 40px rgba(0,0,0,0.8);
    }}
    .title-text {{
        font-family: 'Segoe UI', sans-serif; font-size: 40px; font-weight: 900; color: white;
        text-shadow: 0 0 20px #ff0055; text-align: center; margin-bottom: 30px; text-transform: uppercase;
    }}
    
    /* SCAN BUTTON */
    @keyframes glowing {{
        0% {{ box-shadow: 0 0 5px #ff0055; }}
        50% {{ box-shadow: 0 0 25px #ff0055, 0 0 10px #ff4444; }}
        100% {{ box-shadow: 0 0 5px #ff0055; }}
    }}
    div.stButton > button {{
        width: 100%;
        background: linear-gradient(90deg, #ff0055, #ff2222);
        color: white; font-size: 22px; font-weight: 800; padding: 15px;
        border: none; border-radius: 10px; text-transform: uppercase;
        animation: glowing 2s infinite; transition: 0.3s; margin-top: 10px;
    }}
    div.stButton > button:hover {{ transform: scale(1.01); border: 1px solid white; }}

    /* STATS CARDS */
    .stat-header {{ font-size: 18px; font-weight: bold; color: #aaa; margin-bottom: 5px; border-bottom: 1px solid #444; padding-bottom: 5px; }}
    .big-metric {{ font-size: 24px; font-weight: 900; color: white; }}
    .sub-metric {{ font-size: 14px; color: #888; }}
    
    .result-box {{ 
        padding: 20px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; color: white; margin-top: 30px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.5);
    }}
    .boosted {{ background-color: rgba(220, 20, 60, 0.2); border: 2px solid #ff4444; }}
    .booster {{ background-color: rgba(255, 215, 0, 0.1); border: 2px solid #FFD700; color: #FFD700; }} 
    .clean {{ background-color: rgba(34, 139, 34, 0.2); border: 2px solid #00ff00; }}

    /* CUSTOM PROGRESS BARS */
    .stProgress > div > div > div > div {{ background-color: #ff0055; }}
    
    p, label, .stMarkdown, .stMetricLabel {{ color: #eee !important; }}
    div[data-testid="stMetricValue"] {{ font-size: 24px !important; color: #00ff00 !important; }}
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<div class="title-text">WHO IS CARRYING WHO?</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1], gap="medium")
with col1:
    riot_id_input = st.text_input("Riot ID", placeholder="Name#TAG")
with col2:
    region_select = st.selectbox("Region", ["EUW1", "NA1", "KR", "EUN1", "TR1"])

if st.button('🚀 RUN FULL OP.GG ANALYSIS (20 GAMES)', type="primary"):
    
    def get_regions(region_code):
        if region_code in ["EUW1", "EUN1", "TR1", "RU"]: return "europe"
        elif region_code == "KR": return "asia"
        else: return "americas"

    if not riot_id_input or "#" not in riot_id_input:
        st.error("⚠️ Invalid format. Need Name#TAG")
    else:
        name_raw, tag = riot_id_input.split("#")
        name_encoded = quote(name_raw)
        routing_region = get_regions(region_select)
        
        # 1. PUUID
        url_puuid = f"https://{routing_region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name_encoded}/{tag}?api_key={API_KEY}"
        
        with st.spinner('Extracting detailed telemetry...'):
            resp = requests.get(url_puuid)
            if resp.status_code != 200:
                st.error(f"API Error ({resp.status_code}).")
            else:
                puuid = resp.json().get("puuid")

                # 2. MATCHES
                url_matches = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=20&api_key={API_KEY}"
                match_ids = requests.get(url_matches).json()

                if not match_ids:
                    st.warning("No Ranked Solo games found.")
                else:
                    # 3. ANALYSIS LOOP
                    duo_data = {} 
                    progress_bar = st.progress(0)
                    target_display_name = riot_id_input
                    
                    for i, match_id in enumerate(match_ids):
                        progress_bar.progress((i + 1) / len(match_ids))
                        
                        detail_url = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
                        data = requests.get(detail_url).json()
                        if 'info' not in data: continue
                        
                        game_duration = data['info']['gameDuration'] # in seconds
                        participants = data['info']['participants']
                        
                        # Find ME
                        me = next((p for p in participants if p['puuid'] == puuid), None)
                        
                        if me:
                            target_display_name = me.get('riotIdGameName', name_raw)

                            # --- COLLECT MY STATS FOR THIS GAME ---
                            def extract_stats(p):
                                return {
                                    'k': p['kills'], 'd': p['deaths'], 'a': p['assists'],
                                    'dmg': p['totalDamageDealtToChampions'],
                                    'gold': p['goldEarned'],
                                    'cs': p['totalMinionsKilled'] + p['neutralMinionsKilled'],
                                    'vision': p['visionScore'],
                                    'wards': p['visionWardsBoughtInGame'],
                                    'kp': p.get('challenges', {}).get('killParticipation', 0),
                                    'towers': p.get('challenges', {}).get('turretTakedowns', 0),
                                    'obj_dmg': p.get('damageDealtToObjectives', 0),
                                    'champ': p['championName']
                                }

                            my_s = extract_stats(me)

                            # Find DUO
                            for p in participants:
                                if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                                    r_name = p.get('riotIdGameName', p.get('summonerName', 'Unknown'))
                                    r_tag = p.get('riotIdTagLine', '')
                                    full_identity = f"{r_name}#{r_tag}" if r_tag else r_name
                                    
                                    if full_identity not in duo_data:
                                        # Initialize structure with lists to calculate averages later
                                        duo_data[full_identity] = {
                                            'clean_name': r_name,
                                            'games': 0, 'wins': 0, 'duration_sum': 0,
                                            'my_stats': [], 'duo_stats': []
                                        }
                                    
                                    entry = duo_data[full_identity]
                                    entry['games'] += 1
                                    entry['duration_sum'] += game_duration
                                    if p['win']: entry['wins'] += 1
                                    
                                    duo_s = extract_stats(p)
                                    
                                    entry['my_stats'].append(my_s)
                                    entry['duo_stats'].append(duo_s)

                        time.sleep(0.1)

                    # 4. FIND BEST DUO & CALCULATE AVERAGES
                    st.markdown("---")
                    
                    best_duo_stats = None
                    max_games = 0

                    for identity, data in duo_data.items():
                        if data['games'] > max_games:
                            max_games = data['games']
                            best_duo_stats = data

                    if best_duo_stats and max_games >= 4:
                        s = best_duo_stats
                        games = s['games']
                        avg_duration_min = (s['duration_sum'] / games) / 60
                        
                        # Helper to avg a list of dicts
                        def get_avg(stats_list, key):
                            return sum(x[key] for x in stats_list) / games

                        # --- CALCULATE METRICS (YOU vs DUO) ---
                        
                        # Combat
                        my_kda = round((get_avg(s['my_stats'], 'k') + get_avg(s['my_stats'], 'a')) / max(1, get_avg(s['my_stats'], 'd')), 2)
                        duo_kda = round((get_avg(s['duo_stats'], 'k') + get_avg(s['duo_stats'], 'a')) / max(1, get_avg(s['duo_stats'], 'd')), 2)
                        
                        my_dmg = int(get_avg(s['my_stats'], 'dmg'))
                        duo_dmg = int(get_avg(s['duo_stats'], 'dmg'))
                        
                        my_kp = int(get_avg(s['my_stats'], 'kp') * 100)
                        duo_kp = int(get_avg(s['duo_stats'], 'kp') * 100)

                        # Economy
                        my_cs_min = round(get_avg(s['my_stats'], 'cs') / avg_duration_min, 1)
                        duo_cs_min = round(get_avg(s['duo_stats'], 'cs') / avg_duration_min, 1)
                        
                        my_gold = int(get_avg(s['my_stats'], 'gold'))
                        duo_gold = int(get_avg(s['duo_stats'], 'gold'))

                        # Vision & Macro
                        my_vision = int(get_avg(s['my_stats'], 'vision'))
                        duo_vision = int(get_avg(s['duo_stats'], 'vision'))
                        
                        my_obj = int(get_avg(s['my_stats'], 'obj_dmg'))
                        duo_obj = int(get_avg(s['duo_stats'], 'obj_dmg'))

                        # Champs
                        my_champs = [x['champ'] for x in s['my_stats']]
                        duo_champs = [x['champ'] for x in s['duo_stats']]
                        my_top = [c[0] for c in Counter(my_champs).most_common(3)]
                        duo_top = [c[0] for c in Counter(duo_champs).most_common(3)]

                        # --- IMPACT SCORE V2 (The Fair Formula) ---
                        # Score = (KDA*4) + (Dmg/800) + (KP*20) + (Vision*1.5) + (CS_min*5) + (Obj/1000)
                        
                        def calc_score(kda, dmg, kp, vis, cs, obj):
                            return (kda * 4) + (dmg / 800) + (kp * 0.2) + (vis * 1.5) + (cs * 5) + (obj / 1000)

                        my_score = calc_score(my_kda, my_dmg, my_kp, my_vision, my_cs_min, my_obj)
                        duo_score = calc_score(duo_kda, duo_dmg, duo_kp, duo_vision, duo_cs_min, duo_obj)
                        
                        score_diff = duo_score - my_score
                        
                        # Thresholds
                        status = "EQUAL"
                        if score_diff > 15: status = "BOOSTED"
                        elif score_diff < -15: status = "BOOSTER"

                        # --- HEADER ---
                        winrate = int((s['wins'] / games) * 100)
                        
                        if status == "BOOSTED":
                            st.markdown(f"""<div class="result-box boosted">🚨 PASSENGER DETECTED: {target_display_name} 🚨</div>""", unsafe_allow_html=True)
                            if "http" in CLOWN_IMAGE_URL: st.image(CLOWN_IMAGE_URL, width=400)
                            col1_t, col2_t = f"{target_display_name} (Passenger)", f"{s['clean_name']} (Driver)"
                        elif status == "BOOSTER":
                            st.markdown(f"""<div class="result-box booster">👑 DRIVER DETECTED: {target_display_name} 👑</div>""", unsafe_allow_html=True)
                            col1_t, col2_t = f"{target_display_name} (Driver)", f"{s['clean_name']} (Backpack)"
                        else:
                            st.markdown(f"""<div class="result-box clean">🤝 BALANCED DUO 🤝</div>""", unsafe_allow_html=True)
                            col1_t, col2_t = target_display_name, s['clean_name']

                        st.markdown(f"<p style='text-align:center;'>Played {games} games • {winrate}% Winrate</p><br>", unsafe_allow_html=True)

                        # --- DATA GRID ---
                        c1, c2 = st.columns(2)

                        # LEFT (YOU)
                        with c1:
                            st.markdown(f"<h3 style='text-align:center; color:#ddd'>{col1_t}</h3>", unsafe_allow_html=True)
                            st.markdown(f"<p style='text-align:center; color:#888'>Plays: {', '.join(my_top)}</p>", unsafe_allow_html=True)
                            
                            st.markdown("<div class='stat-header'>⚔️ COMBAT</div>", unsafe_allow_html=True)
                            cc1, cc2 = st.columns(2)
                            cc1.metric("KDA", my_kda)
                            cc2.metric("Kill Part.", f"{my_kp}%")
                            st.metric("Dmg/Game", my_dmg)
                            st.progress(min(1.0, my_dmg / 40000))

                            st.markdown("<div class='stat-header'>💰 FARM & GOLD</div>", unsafe_allow_html=True)
                            cc3, cc4 = st.columns(2)
                            cc3.metric("CS/min", my_cs_min)
                            cc4.metric("Gold", f"{my_gold // 1000}k")
                            
                            st.markdown("<div class='stat-header'>👁️ VISION & MACRO</div>", unsafe_allow_html=True)
                            cc5, cc6 = st.columns(2)
                            cc5.metric("Vis. Score", my_vision)
                            cc6.metric("Obj. Dmg", f"{my_obj // 1000}k")

                        # RIGHT (THEM)
                        with c2:
                            st.markdown(f"<h3 style='text-align:center; color:#ddd'>{col2_t}</h3>", unsafe_allow_html=True)
                            st.markdown(f"<p style='text-align:center; color:#888'>Plays: {', '.join(duo_top)}</p>", unsafe_allow_html=True)

                            st.markdown("<div class='stat-header'>⚔️ COMBAT</div>", unsafe_allow_html=True)
                            dd1, dd2 = st.columns(2)
                            dd1.metric("KDA", duo_kda, delta=round(duo_kda-my_kda, 2))
                            dd2.metric("Kill Part.", f"{duo_kp}%", delta=duo_kp-my_kp)
                            st.metric("Dmg/Game", duo_dmg, delta=duo_dmg-my_dmg)
                            st.progress(min(1.0, duo_dmg / 40000))

                            st.markdown("<div class='stat-header'>💰 FARM & GOLD</div>", unsafe_allow_html=True)
                            dd3, dd4 = st.columns(2)
                            dd3.metric("CS/min", duo_cs_min, delta=round(duo_cs_min-my_cs_min, 1))
                            dd4.metric("Gold", f"{duo_gold // 1000}k", delta=f"{(duo_gold-my_gold)//1000}k")

                            st.markdown("<div class='stat-header'>👁️ VISION & MACRO</div>", unsafe_allow_html=True)
                            dd5, dd6 = st.columns(2)
                            dd5.metric("Vis. Score", duo_vision, delta=duo_vision-my_vision)
                            dd6.metric("Obj. Dmg", f"{duo_obj // 1000}k", delta=f"{(duo_obj-my_obj)//1000}k")
                        
                        # VERDICT
                        st.markdown("<br><hr>", unsafe_allow_html=True)
                        impact_diff = int(abs(score_diff))
                        if status == "BOOSTED":
                            st.error(f"VERDICT: {s['clean_name']} has a massive impact lead (Score diff: {impact_diff}). They carry the economy, combat, or map.")
                        elif status == "BOOSTER":
                            st.warning(f"VERDICT: You are the engine of this duo (Score diff: {impact_diff}). You outperform in resources or pressure.")
                        else:
                            st.success(f"VERDICT: Perfect Synergy. You excel in different areas, but overall contribution is equal.")

                    else:
                        st.markdown("""<div class="result-box clean">SOLO PLAYER</div>""", unsafe_allow_html=True)
                        st.markdown("<p style='text-align:center;'>No recurring duo detected.</p>", unsafe_allow_html=True)
