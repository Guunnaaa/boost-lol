import streamlit as st
import requests
import time
from urllib.parse import quote
from collections import Counter

# --- CONFIGURATION ---
st.set_page_config(page_title="Duo Synergy V20", layout="wide")

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

# --- MODERN CSS & DESIGN SYSTEM ---
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
    
    /* GLASSMORPHISM CONTAINER */
    .block-container {{
        max-width: 1000px !important;
        padding: 3rem !important;
        margin: auto !important;
        background: rgba(18, 18, 18, 0.85);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }}
    
    /* TYPOGRAPHY */
    .main-title {{
        font-size: 48px; font-weight: 900; color: white;
        text-align: center; margin-bottom: 10px; text-transform: uppercase;
        letter-spacing: -1px;
        text-shadow: 0 0 20px rgba(255, 0, 85, 0.6);
    }}
    .subtitle {{
        font-size: 16px; color: #888; text-align: center; margin-bottom: 40px; font-weight: 400;
    }}
    
    /* CUSTOM CARDS */
    .stat-card {{
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        transition: transform 0.2s;
    }}
    .stat-card:hover {{ transform: translateY(-2px); border-color: rgba(255, 255, 255, 0.2); }}
    
    .card-title {{ font-size: 12px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; font-weight: 600; }}
    .card-value {{ font-size: 28px; font-weight: 800; color: white; margin-bottom: 5px; }}
    .diff-pos {{ color: #00ff99; font-size: 14px; font-weight: 600; }}
    .diff-neg {{ color: #ff4444; font-size: 14px; font-weight: 600; }}
    
    /* CHAMPION CIRCLES */
    .champ-container {{ display: flex; gap: 10px; justify-content: center; margin-bottom: 20px; }}
    .champ-img {{ width: 50px; height: 50px; border-radius: 50%; border: 2px solid #333; }}
    
    /* VERDICT BADGES */
    .verdict-badge {{
        padding: 15px 30px; border-radius: 12px; font-weight: 800; font-size: 20px; text-align: center; text-transform: uppercase; margin-top: 20px;
    }}
    .v-boosted {{ background: rgba(255, 68, 68, 0.2); border: 1px solid #ff4444; color: #ff4444; }}
    .v-booster {{ background: rgba(255, 215, 0, 0.2); border: 1px solid #ffd700; color: #ffd700; }}
    .v-clean {{ background: rgba(0, 255, 153, 0.2); border: 1px solid #00ff99; color: #00ff99; }}

    /* BUTTON */
    div.stButton > button {{
        width: 100%;
        background: linear-gradient(135deg, #ff0055 0%, #ff2244 100%);
        color: white; font-weight: 800; padding: 16px; font-size: 18px;
        border: none; border-radius: 12px;
        box-shadow: 0 4px 15px rgba(255, 0, 85, 0.3);
        transition: 0.3s;
    }}
    div.stButton > button:hover {{ transform: scale(1.02); box-shadow: 0 6px 20px rgba(255, 0, 85, 0.5); }}

    /* UTILS */
    p, label, .stMarkdown {{ color: #eee !important; }}
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<div class="main-title">Who is Carrying Who?</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Advanced Tactical Analysis • 20 Games Sample</div>', unsafe_allow_html=True)

# --- INPUT SECTION ---
c1, c2 = st.columns([3, 1], gap="medium")
with c1:
    riot_id_input = st.text_input("Riot ID", placeholder="Example: Faker#KR1")
with c2:
    region_select = st.selectbox("Region", ["EUW1", "NA1", "KR", "EUN1", "TR1"])

# --- HELPER FUNCTIONS ---
def get_champ_url(champ_name):
    clean = champ_name.replace(" ", "").replace("'", "").replace(".", "")
    if clean == "Wukong": clean = "MonkeyKing"
    if clean == "RenataGlasc": clean = "Renata"
    return f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/img/champion/{clean}.png"

def render_stat_card(title, my_val, duo_val, unit="", inverse=False):
    """Renders a nice HTML card comparing two values"""
    diff = my_val - duo_val
    if inverse: diff = -diff # Lower is better for deaths (not used here but ready)
    
    color_class = "diff-pos" if diff >= 0 else "diff-neg"
    sign = "+" if diff > 0 else ""
    
    html = f"""
    <div class="stat-card">
        <div class="card-title">{title}</div>
        <div class="card-value">{my_val}{unit}</div>
        <div class="{color_class}">{sign}{round(diff, 1)}{unit} vs Duo</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- MAIN LOGIC ---
if st.button('🚀 RUN ANALYSIS', type="primary"):
    
    def get_regions(region_code):
        if region_code in ["EUW1", "EUN1", "TR1", "RU"]: return "europe"
        elif region_code == "KR": return "asia"
        else: return "americas"

    if not riot_id_input or "#" not in riot_id_input:
        st.error("⚠️ Invalid format. Name#TAG required.")
    else:
        name_raw, tag = riot_id_input.split("#")
        name_encoded = quote(name_raw)
        region = get_regions(region_select)
        
        # 1. API CALLS
        with st.spinner('Connecting to Riot Neural Network...'):
            try:
                # PUUID
                url_acc = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name_encoded}/{tag}?api_key={API_KEY}"
                resp_acc = requests.get(url_acc)
                if resp_acc.status_code != 200:
                    st.error(f"Player not found (Error {resp_acc.status_code})")
                    st.stop()
                puuid = resp_acc.json().get("puuid")

                # MATCHES
                url_match = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=20&api_key={API_KEY}"
                match_ids = requests.get(url_match).json()
                
                if not match_ids:
                    st.warning("No Ranked games found.")
                    st.stop()
            except Exception as e:
                st.error(f"API Error: {e}")
                st.stop()

            # 2. ANALYSIS LOOP
            duo_data = {} 
            progress_bar = st.progress(0)
            my_real_name = riot_id_input
            
            for i, match_id in enumerate(match_ids):
                progress_bar.progress((i + 1) / len(match_ids))
                
                url_det = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
                data = requests.get(url_det).json()
                if 'info' not in data: continue
                
                duration = data['info']['gameDuration'] / 60
                parts = data['info']['participants']
                
                me = next((p for p in parts if p['puuid'] == puuid), None)
                if me:
                    my_real_name = me.get('riotIdGameName', name_raw)
                    
                    # My Stats
                    m_stats = {
                        'kda': (me['kills'] + me['assists']) / max(1, me['deaths']),
                        'dmg': me['totalDamageDealtToChampions'],
                        'gold': me['goldEarned'],
                        'vis': me['visionScore'],
                        'obj': me.get('damageDealtToObjectives', 0),
                        'champ': me['championName']
                    }

                    for p in parts:
                        if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                            full_id = f"{p.get('riotIdGameName')}#{p.get('riotIdTagLine')}"
                            
                            if full_id not in duo_data:
                                duo_data[full_id] = {
                                    'name': p.get('riotIdGameName'),
                                    'games': 0, 'wins': 0,
                                    'stats': {'kda':0, 'dmg':0, 'gold':0, 'vis':0, 'obj':0},
                                    'my_stats_vs': {'kda':0, 'dmg':0, 'gold':0, 'vis':0, 'obj':0},
                                    'champs': []
                                }
                            
                            d = duo_data[full_id]
                            d['games'] += 1
                            if p['win']: d['wins'] += 1
                            d['champs'].append(p['championName'])
                            
                            # Accumulate
                            d['stats']['kda'] += (p['kills'] + p['assists']) / max(1, p['deaths'])
                            d['stats']['dmg'] += p['totalDamageDealtToChampions']
                            d['stats']['gold'] += p['goldEarned']
                            d['stats']['vis'] += p['visionScore']
                            d['stats']['obj'] += p.get('damageDealtToObjectives', 0)
                            
                            d['my_stats_vs']['kda'] += m_stats['kda']
                            d['my_stats_vs']['dmg'] += m_stats['dmg']
                            d['my_stats_vs']['gold'] += m_stats['gold']
                            d['my_stats_vs']['vis'] += m_stats['vis']
                            d['my_stats_vs']['obj'] += m_stats['obj']
                            
                time.sleep(0.05)

            # 3. VERDICT LOGIC
            st.markdown("---")
            best_duo = None
            max_g = 0
            
            for k, v in duo_data.items():
                if v['games'] > max_g:
                    max_g = v['games']
                    best_duo = v
            
            if best_duo and max_g >= 4:
                g = best_duo['games']
                
                # Averages
                def avg(d, key): return int(d[key] / g)
                def avg_f(d, key): return round(d[key] / g, 2)
                
                # Player A (You) vs Player B (Duo)
                s_me = best_duo['my_stats_vs']
                s_duo = best_duo['stats']
                
                # THE 4 PILLARS OF PERFORMANCE
                # We determine who wins each category
                
                # 1. Combat (KDA + Dmg)
                score_combat_me = (s_me['kda'] * 2) + (s_me['dmg'] / 1000)
                score_combat_duo = (s_duo['kda'] * 2) + (s_duo['dmg'] / 1000)
                
                # 2. Economy (Gold)
                score_eco_me = s_me['gold']
                score_eco_duo = s_duo['gold']
                
                # 3. Map Control (Vision)
                score_vis_me = s_me['vis']
                score_vis_duo = s_duo['vis']
                
                # 4. Objectives (Dmg Obj)
                score_obj_me = s_me['obj']
                score_obj_duo = s_duo['obj']
                
                # Counting "Wins"
                my_wins = 0
                duo_wins = 0
                
                # Threshold logic: Must beat by 10% to count as a "Win", otherwise it's a tie
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
                
                # FINAL VERDICT based on Pillars
                status = "EQUAL"
                if duo_wins >= my_wins + 2: status = "BOOSTED" # They won 2 more categories than you
                elif my_wins >= duo_wins + 2: status = "BOOSTER"
                
                # DISPLAY
                col_res1, col_res2 = st.columns(2)
                
                with col_res1:
                    st.markdown(f"<h2 style='text-align:center; color:white; margin:0;'>{my_real_name}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center; color:#888; margin-bottom:15px;'>YOU</div>", unsafe_allow_html=True)
                    render_stat_card("Combat (KDA)", avg_f(s_me, 'kda'), avg_f(s_duo, 'kda'))
                    render_stat_card("Damage/Game", f"{avg(s_me, 'dmg')//1000}k", f"{avg(s_duo, 'dmg')//1000}k")
                    render_stat_card("Gold/Game", f"{avg(s_me, 'gold')//1000}k", f"{avg(s_duo, 'gold')//1000}k")
                    render_stat_card("Vision Score", avg(s_me, 'vis'), avg(s_duo, 'vis'))
                    render_stat_card("Obj. Damage", f"{avg(s_me, 'obj')//1000}k", f"{avg(s_duo, 'obj')//1000}k")

                with col_res2:
                    st.markdown(f"<h2 style='text-align:center; color:white; margin:0;'>{best_duo['name']}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center; color:#888; margin-bottom:15px;'>THE DUO</div>", unsafe_allow_html=True)
                    
                    # Champ Icons
                    top_champs = [c[0] for c in Counter(best_duo['champs']).most_common(3)]
                    cols_img = st.columns(3)
                    for idx, c in enumerate(top_champs):
                        with cols_img[idx]:
                            st.image(get_champ_url(c), use_column_width=True)
                    
                    # Verdict Badge
                    if status == "BOOSTED":
                        st.markdown(f"""<div class="verdict-badge v-boosted">PASSENGER<br><span style="font-size:12px">Carried by {best_duo['name']}</span></div>""", unsafe_allow_html=True)
                        if "http" in CLOWN_IMAGE_URL: st.image(CLOWN_IMAGE_URL, use_column_width=True)
                    elif status == "BOOSTER":
                        st.markdown(f"""<div class="verdict-badge v-booster">DRIVER<br><span style="font-size:12px">Boosting {best_duo['name']}</span></div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""<div class="verdict-badge v-clean">SOLID DUO<br><span style="font-size:12px">Equal Contribution</span></div>""", unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; margin-top:20px; font-size:14px;">
                        <b>Performance Pillars:</b><br>
                        You lead in <b>{my_wins}</b> areas.<br>
                        They lead in <b>{duo_wins}</b> areas.<br>
                        (Based on Combat, Gold, Vision, Objectives)
                    </div>
                    """, unsafe_allow_html=True)

            else:
                st.markdown("""<div class="result-box v-clean">SOLO PLAYER DETECTED</div>""", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center;'>No recurring duo found in the last 20 games.</p>", unsafe_allow_html=True)
