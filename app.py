import streamlit as st
import requests
import time
from urllib.parse import quote

# --- CONFIGURATION ---
st.set_page_config(page_title="Boost Detector", layout="wide")

# --- CLÉ API ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ Clé API introuvable. Ajoute-la dans les secrets Streamlit.")
    st.stop()

# --- BACKGROUND ---
BACKGROUND_IMAGE_URL = "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123"

# --- STYLE CSS (DESIGN & ESPACEMENT) ---
st.markdown(
    f"""
    <style>
    /* Fond d'écran */
    .stApp {{
        background-image: url("{BACKGROUND_IMAGE_URL}");
        background-size: 150px;
        background-repeat: repeat;
        background-attachment: fixed;
    }}
    
    /* BLOC CENTRAL (Plus aéré) */
    .block-container {{
        max-width: 800px !important;
        padding-top: 3rem !important;
        padding-bottom: 5rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        margin: auto !important;
        background-color: rgba(10, 10, 10, 0.95); /* Plus sombre */
        border-radius: 25px;
        border: 1px solid #444;
        box-shadow: 0 0 30px rgba(0,0,0,0.9);
    }}

    /* TITRE */
    .title-text {{
        font-family: 'Segoe UI', sans-serif; 
        font-size: 45px; 
        font-weight: 900; 
        color: #ffffff;
        text-shadow: 0 0 15px #ff0055; 
        text-align: center; 
        margin-bottom: 40px; /* Plus d'espace sous le titre */
        text-transform: uppercase;
        letter-spacing: 2px;
    }}

    /* BOUTON DPM.LOL (STYLE HEXTECH) */
    .dpm-button {{
        display: inline-block;
        background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%); /* Dégradé stylé */
        color: white !important;
        padding: 12px 25px;
        border-radius: 50px; /* Arrondi */
        font-family: 'Verdana', sans-serif;
        font-weight: bold;
        font-size: 14px;
        text-transform: uppercase;
        text-decoration: none;
        box-shadow: 0 4px 15px rgba(37, 117, 252, 0.4);
        transition: all 0.3s ease;
        margin-top: 15px; /* Espace au dessus du bouton */
        border: 1px solid rgba(255,255,255,0.2);
    }}
    .dpm-button:hover {{
        transform: translateY(-3px); /* Le bouton monte un peu */
        box-shadow: 0 8px 25px rgba(37, 117, 252, 0.6);
        background: linear-gradient(90deg, #2575fc 0%, #6a11cb 100%);
    }}

    /* RESULTATS & STATS */
    .result-box {{ 
        padding: 30px; 
        border-radius: 15px; 
        text-align: center; 
        font-size: 26px; 
        font-weight: bold; 
        color: white; 
        margin-top: 40px; /* Espace avant le résultat */
        margin-bottom: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.5);
    }}
    .boosted {{ background-color: rgba(220, 20, 60, 0.9); border: 3px solid #ff4444; }}
    .clean {{ background-color: rgba(34, 139, 34, 0.9); border: 3px solid #00ff00; }}
    
    .stat-box {{ 
        background-color: rgba(40,40,40,0.8); 
        padding: 20px; 
        border-radius: 12px; 
        margin-top: 25px; 
        color: #eee; 
        font-size: 16px; 
        border-left: 4px solid #ff0055; 
    }}
    
    /* CUSTOMISATION STREAMLIT GENERALE */
    p, label, .stMarkdown, .stMetricLabel {{ color: #eee !important; font-size: 16px !important; }}
    div[data-testid="stMetricValue"] {{ font-size: 28px !important; color: #00ff00 !important; }}
    
    /* Espace entre les input et le bouton scanner */
    .stButton {{ margin-top: 20px; }}
    .stButton > button {{
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
        font-size: 20px;
        padding-top: 10px;
        padding-bottom: 10px;
    }}
    </style>
    """, unsafe_allow_html=True
)

# --- LE TITRE MODIFIÉ ---
st.markdown('<div class="title-text">Mérites-tu un vilan C ?</div>', unsafe_allow_html=True)

# --- INPUT & LIEN DPM ---
col1, col2 = st.columns([3, 1], gap="medium") # Gap medium pour espacer les colonnes

with col1:
    riot_id_input = st.text_input("Entre le Riot ID", placeholder="Nom#TAG")
    
    # LE NOUVEAU BOUTON JOLI
    st.markdown("""
        <div style="text-align: right;">
            <a href="https://dpm.lol" target="_blank" class="dpm-button">
                🔍 Trouver un pseudo sur dpm.lol
            </a>
        </div>
    """, unsafe_allow_html=True)

with col2:
    region_select = st.selectbox("Région", ["EUW1", "NA1", "KR", "EUN1", "TR1"])

st.markdown("<br>", unsafe_allow_html=True) # Un saut de ligne forcé pour aérer avant le bouton

# --- FONCTIONS ---
def get_regions(region_code):
    if region_code in ["EUW1", "EUN1", "TR1", "RU"]: return "europe"
    elif region_code == "KR": return "asia"
    else: return "americas"

def analyze():
    if not riot_id_input or "#" not in riot_id_input:
        st.error("⚠️ Format invalide. Il faut le #TAG.")
        return

    name_raw, tag = riot_id_input.split("#")
    name_encoded = quote(name_raw)
    routing_region = get_regions(region_select)
    
    # 1. PUUID
    url_puuid = f"https://{routing_region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name_encoded}/{tag}?api_key={API_KEY}"
    
    with st.spinner('Analyse des 20 dernières games en cours...'):
        resp = requests.get(url_puuid)
        if resp.status_code != 200:
            st.error(f"Erreur API ({resp.status_code}). Vérifie le pseudo.")
            return
        puuid = resp.json().get("puuid")

        # 2. MATCHS (20 Dernières SoloQ)
        url_matches = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=20&api_key={API_KEY}"
        match_ids = requests.get(url_matches).json()

        if not match_ids:
            st.warning("Pas de SoloQ trouvée.")
            return

        # 3. ANALYSE COMPARATIVE
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

        # SEUIL : 4 games sur 20
        if best_duo and max_games >= 4:
            identity, s = best_duo
            
            # Calculs
            duo_deaths = s['duo_d'] if s['duo_d'] > 0 else 1
            duo_kda = round((s['duo_k'] + s['duo_a']) / duo_deaths, 2)
            
            my_deaths = s['my_d'] if s['my_d'] > 0 else 1
            my_kda = round((s['my_k'] + s['my_a']) / my_deaths, 2)
            
            duo_avg_dmg = int(s['duo_dmg'] / s['games'])
            my_avg_dmg = int(s['my_dmg'] / s['games'])
            winrate = int((s['wins'] / s['games']) * 100)

            st.markdown(f"""<div class="result-box boosted">🚨 DUO SUSPECT : {identity} 🚨</div>""", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; font-size:18px;'>Vu <b>{s['games']} fois</b> sur les 20 dernières games.</p>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<h3 style='text-align:center; color:white;'>TOI<br><span style='font-size:16px'>(quand t'es avec lui)</span></h3>", unsafe_allow_html=True)
                st.metric("KDA", my_kda)
                st.metric("Dégâts/Game", my_avg_dmg)
            with c2:
                st.markdown(f"<h3 style='text-align:center; color:red;'>LUI<br><span style='font-size:16px'>(le booster?)</span></h3>", unsafe_allow_html=True)
                delta_kda = round(duo_kda - my_kda, 2)
                delta_dmg = duo_avg_dmg - my_avg_dmg
                st.metric("KDA", duo_kda, delta=delta_kda)
                st.metric("Dégâts/Game", duo_avg_dmg, delta=delta_dmg)

            st.markdown(f"<div class='stat-box'>Winrate ensemble : <b>{winrate}%</b></div>", unsafe_allow_html=True)

            if duo_kda > my_kda + 1.5 or duo_avg_dmg > my_avg_dmg + 5000:
                st.error(f"VERDICT : 100% BOOSTED. Il fait tout le taf, tu récoltes les LP.")
            elif winrate < 50:
                st.warning("VERDICT : C'est ton duo, mais vous perdez. Changez de stratégie.")
            else:
                st.success("VERDICT : Duo legit. Vous avez le même niveau.")
        else:
            st.markdown("""<div class="result-box clean">SOLO PLAYER</div>""", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center;'>Aucun duo récurrent détecté. Tu joues vraiment tout seul.</p>", unsafe_allow_html=True)

if st.button('SCANNER (20 DERNIÈRES GAMES)', type="primary"):
    analyze()

