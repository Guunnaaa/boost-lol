import streamlit as st
import requests
import time
from urllib.parse import quote
from collections import Counter

# --- CONFIGURATION ---
st.set_page_config(page_title="LoL Analytics Pro", layout="wide")

# --- API KEY ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ API Key missing. Add RIOT_API_KEY to Streamlit secrets.")
    st.stop()

# --- CONSTANTES ---
BACKGROUND_IMAGE_URL = "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123"
CLOWN_IMAGE_URL = "https://raw.githubusercontent.com/[YOUR_GITHUB_NAME]/[REPO_NAME]/main/clown.jpg"
DD_VERSION = "13.24.1" # Version DataDragon pour les images

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
        max-width: 1100px !important;
        padding: 2rem !important;
        margin: auto !important;
        background-color: rgba(18, 18, 18, 0.96);
        border-radius: 20px;
        border: 1px solid #333;
        box-shadow: 0 0 50px rgba(0,0,0,0.9);
    }}
    .title-text {{
        font-family: 'Segoe UI', sans-serif; font-size: 40px; font-weight: 900; color: white;
        text-shadow: 0 0 20px #ff0055; text-align: center; margin-bottom: 30px; text-transform: uppercase;
    }}
    
    /* CHAMPION IMAGES */
    .champ-img {{
        border-radius: 50%;
        border: 2px solid #555;
        transition: transform 0.2s;
    }}
    .champ-img:hover {{ transform: scale(1.1); border-color: white; }}

    /* SCORE CIRCLE */
    .score-container {{
        background: linear-gradient(135deg, #1e1e1e, #2a2a2a);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid #444;
    }}
    .score-val {{ font-size: 42px; font-weight: 900; }}
    .score-label {{ font-size: 12px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }}
    
    /* BUTTON */
    div.stButton > button {{
        width: 100%;
        background: linear-gradient(90deg, #ff0055, #ff2222);
        color: white; font-size: 22px; font-weight: 800; padding: 15px;
        border: none; border-radius: 10px; text-transform: uppercase;
        margin-top: 10px;
    }}
    
    .stat-header {{ font-size: 16px; font-weight: bold; color: #888; margin-bottom: 10px; margin-top: 20px; border-bottom: 1px solid #333; }}
    
    /* RESULT BOXES */
    .result-box {{ padding: 20px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; color: white; margin-top: 30px; margin-bottom: 20px; }}
    .boosted {{ background-color: rgba(220, 20, 60, 0.2); border: 2px solid #ff4444; }}
    .booster {{ background-color: rgba(255, 215, 0, 0.1); border: 2px solid #FFD700; color: #FFD700; }} 
    .clean {{ background-color: rgba(34, 139, 34, 0.2); border: 2px solid #00ff00; }}

    p, label, .stMarkdown, .stMetricLabel {{ color: #eee !important; }}
    div[data-testid="stMetricValue"] {{ font-size: 24px !important; }}
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<div class="title-text">WHO IS CARRYING WHO?</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1], gap="medium")
with col1:
    riot_id_input = st.text_input("Riot ID", placeholder="Name#TAG")
with col2:
    region_select = st.selectbox("Region", ["EUW1", "NA1", "KR", "EUN1", "TR1"])

# HELPER: Get Champion Image URL
def get_champ_url(champ_name):
    # Fix odd names for DataDragon
    clean = champ_name.replace(" ", "").replace("'", "").replace(".", "")
    if clean == "Wukong": clean = "MonkeyKing"
    if clean == "RenataGlasc": clean = "Renata"
    return f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/img/champion/{clean}.png"

# HELPER: Calculate OP Score (0-100)
def calc_op_score(stats):
    # Base 50
    score = 50
    
    # KDA (Target: 3.0)
    kda = (stats['k'] + stats['a']) / max(1, stats['d'])
    if kda >= 3: score += 10
    elif kda < 1.5: score -= 10
    score += (kda * 2) # Bonus per point of KDA

    # CS/min (Target: 7.0)
    cs_min = stats['cs'] / (stats['duration'] / 60)
    if cs_min >= 7: score += 10
    score += (cs_min * 1.5)

    # KP (Target: 50%)
    if stats['kp'] >= 0.5: score += 10
    score += (stats['kp'] * 10)

    # Win Bonus
    if stats['win']: score += 15

    # Cap at 100
    return min(100, max(0, int(score)))

if st.button('🚀 ANALYZE PERFORMANCE (20 GAMES)', type="primary"):
    
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
        
        url_puuid = f"https://{routing_region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name_encoded}/{tag}?api_key={API_KEY}"
        
        with st.spinner('Calculating OP Scores...'):
            resp = requests.get(url_puuid)
            if resp.status_code != 200:
                st.error(f"API Error ({resp.status_code}).")
            else:
                puuid = resp.json().get("puuid")
                url_matches = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=20&api_key={API_KEY}"
                match_ids = requests.get(url_matches).json()

                if not match_ids:
                    st.warning("No Ranked Solo games found.")
                else:
                    duo_data = {} 
                    progress_bar = st.progress(0)
                    target_display_name = riot_id_input
                    
                    for i, match_id in enumerate(match_ids):
                        progress_bar.progress((i + 1) / len(match_ids))
                        
                        detail_url = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
                        data = requests.get(detail_url).json()
                        if 'info' not in data: continue
                        
                        game_duration = data['info']['gameDuration'] 
                        participants = data['info']['participants']
                        
                        me = next((p for p in participants if p['puuid'] == puuid), None)
                        
                        if me:
                            target_display_name = me.get('riotIdGameName', name_raw)

                            def extract_stats(p):
                                return {
                                    'k': p['kills'], 'd': p['deaths'], 'a': p['assists'],
                                    'dmg': p['totalDamageDealtToChampions'],
                                    'gold': p['goldEarned'],
                                    'cs': p['totalMinionsKilled'] + p['neutralMinionsKilled'],
                                    'vision': p['visionScore'],
                                    'kp': p.get('challenges', {}).get('killParticipation', 0),
                                    'obj_dmg': p.get('damageDealtToObjectives', 0),
                                    'champ': p['championName'],
                                    'duration': game_duration,
                                    'win': p['win']
                                }

                            my_s = extract_stats(me)
                            my_s['op_score'] = calc_op_score(my_s) # Calculate Score per game

                            for p in participants:
                                if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                                    r_name = p.get('riotIdGameName', p.get('summonerName', 'Unknown'))
                                    r_tag = p.get('riotIdTagLine', '')
                                    full_identity = f"{r_name}#{r_tag}" if r_tag else r_name
                                    
                                    if full_identity not in duo_data:
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
                                    duo_s['op_score'] = calc_op_score(duo_s)
                                    
                                    entry['my_stats'].append(my_s)
                                    entry['duo_stats'].append(duo_s)

                        time.sleep(0.1)

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
                        
                        def get_avg(stats_list, key): return sum(x[key] for x in stats_list) / games

                        # --- AVERAGES ---
                        my_kda = round((get_avg(s['my_stats'], 'k') + get_avg(s['my_stats'], 'a')) / max(1, get_avg(s['my_stats'], 'd')), 2)
                        duo_kda = round((get_avg(s['duo_stats'], 'k') + get_avg(s['duo_stats'], 'a')) / max(1, get_avg(s['duo_stats'], 'd')), 2)
                        
                        my_dmg, duo_dmg = int(get_avg(s['my_stats'], 'dmg')), int(get_avg(s['duo_stats'], 'dmg'))
                        my_gold, duo_gold = int(get_avg(s['my_stats'], 'gold')), int(get_avg(s['duo_stats'], 'gold'))
                        my_cs, duo_cs = round(get_avg(s['my_stats'], 'cs') / avg_duration_min, 1), round(get_avg(s['duo_stats'], 'cs') / avg_duration_min, 1)
                        my_vision, duo_vision = int(get_avg(s['my_stats'], 'vision')), int(get_avg(s['duo_stats'], 'vision'))
                        
                        # --- SCORES 0-100 ---
                        my_final_score = int(get_avg(s['my_stats'], 'op_score'))
                        duo_final_score = int(get_avg(s['duo_stats'], 'op_score'))

                        # Champs
                        my_top = [c[0] for c in Counter([x['champ'] for x in s['my_stats']]).most_common(3)]
                        duo_top = [c[0] for c in Counter([x['champ'] for x in s['duo_stats']]).most_common(3)]

                        # --- STATUS ---
                        score_diff = duo_final_score - my_final_score
                        status = "EQUAL"
                        if score_diff > 10: status = "BOOSTED"
                        elif score_diff < -10: status = "BOOSTER"

                        # HEADER
                        if status == "BOOSTED":
                            st.markdown(f"""<div class="result-box boosted">🚨 PASSENGER: {target_display_name} 🚨</div>""", unsafe_allow_html=True)
                            if "http" in CLOWN_IMAGE_URL: st.image(CLOWN_IMAGE_URL, width=400)
                            col1_t, col2_t = f"{target_display_name} (Passenger)", f"{s['clean_name']} (Driver)"
                        elif status == "BOOSTER":
                            st.markdown(f"""<div class="result-box booster">👑 DRIVER: {target_display_name} 👑</div>""", unsafe_allow_html=True)
                            col1_t, col2_t = f"{target_display_name} (Driver)", f"{s['clean_name']} (Backpack)"
                        else:
                            st.markdown(f"""<div class="result-box clean">🤝 BALANCED DUO 🤝</div>""", unsafe_allow_html=True)
                            col1_t, col2_t = target_display_name, s['clean_name']

                        # --- DISPLAY GRID ---
                        c1, c2 = st.columns(2)

                        # LEFT (YOU)
                        with c1:
                            st.markdown(f"<h3 style='text-align:center;'>{col1_t}</h3>", unsafe_allow_html=True)
                            
                            # SCORE CARD
                            score_color = "#ff4444" if my_final_score < 50 else ("#FFD700" if my_final_score > 80 else "#ffffff")
                            st.markdown(f"""
                                <div class="score-container">
                                    <div class="score-val" style="color:{score_color}">{my_final_score}</div>
                                    <div class="score-label">OP SCORE / 100</div>
                                </div>
                            """, unsafe_allow_html=True)

                            # CHAMPS IMAGES
                            img_cols = st.columns(3)
                            for idx, ch in enumerate(my_top):
                                with img_cols[idx]:
                                    st.image(get_champ_url(ch), use_column_width=True)

                            st.markdown("<div class='stat-header'>⚔️ COMBAT</div>", unsafe_allow_html=True)
                            col_a, col_b = st.columns(2)
                            col_a.metric("KDA", my_kda)
                            col_b.metric("Damage", f"{my_dmg//1000}k")
                            
                            st.markdown("<div class='stat-header'>💰 ECONOMY</div>", unsafe_allow_html=True)
                            col_c, col_d = st.columns(2)
                            col_c.metric("Gold", f"{my_gold//1000}k")
                            col_d.metric("CS/min", my_cs)
                            
                            st.markdown("<div class='stat-header'>👁️ UTILITY</div>", unsafe_allow_html=True)
                            st.metric("Vision Score", my_vision)

                        # RIGHT (THEM - WITH DELTAS)
                        with c2:
                            st.markdown(f"<h3 style='text-align:center;'>{col2_t}</h3>", unsafe_allow_html=True)
                            
                            # SCORE CARD
                            score_color_duo = "#ff4444" if duo_final_score < 50 else ("#FFD700" if duo_final_score > 80 else "#ffffff")
                            st.markdown(f"""
                                <div class="score-container">
                                    <div class="score-val" style="color:{score_color_duo}">{duo_final_score}</div>
                                    <div class="score-label">OP SCORE / 100</div>
                                </div>
                            """, unsafe_allow_html=True)

                            # CHAMPS IMAGES
                            img_cols_duo = st.columns(3)
                            for idx, ch in enumerate(duo_top):
                                with img_cols_duo[idx]:
                                    st.image(get_champ_url(ch), use_column_width=True)

                            st.markdown("<div class='stat-header'>⚔️ COMBAT</div>", unsafe_allow_html=True)
                            col_aa, col_bb = st.columns(2)
                            col_aa.metric("KDA", duo_kda, delta=round(duo_kda - my_kda, 2))
                            col_bb.metric("Damage", f"{duo_dmg//1000}k", delta=f"{(duo_dmg-my_dmg)//1000}k")
                            
                            st.markdown("<div class='stat-header'>💰 ECONOMY</div>", unsafe_allow_html=True)
                            col_cc, col_dd = st.columns(2)
                            col_cc.metric("Gold", f"{duo_gold//1000}k", delta=f"{(duo_gold-my_gold)//1000}k")
                            col_dd.metric("CS/min", duo_cs, delta=round(duo_cs - my_cs, 1))

                            st.markdown("<div class='stat-header'>👁️ UTILITY</div>", unsafe_allow_html=True)
                            st.metric("Vision Score", duo_vision, delta=duo_vision - my_vision)

                        st.markdown("<br>", unsafe_allow_html=True)
                        if status == "BOOSTED":
                            st.error(f"VERDICT: {s['clean_name']} is performing better overall (Score: {duo_final_score} vs {my_final_score}).")
                        elif status == "BOOSTER":
                            st.warning(f"VERDICT: You are outperforming them (Score: {my_final_score} vs {duo_final_score}).")
                        else:
                            st.success(f"VERDICT: Perfectly Balanced. Scores are close ({my_final_score} vs {duo_final_score}).")

                    else:
                        st.markdown("""<div class="result-box clean">SOLO PLAYER</div>""", unsafe_allow_html=True)
                        st.markdown("<p style='text-align:center;'>No recurring duo detected.</p>", unsafe_allow_html=True)
