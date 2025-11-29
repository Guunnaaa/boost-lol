import streamlit as st
import requests
import time
from urllib.parse import quote

# --- CONFIGURATION ---
st.set_page_config(page_title="Boost Detector ULTIMATE", layout="centered")

# --- STYLE ---
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://images.contentstack.io/v3/assets/blt731acb42bb3d1659/blt2a81f802ca00115e/6532ae3858c70f0742d4a674/102423_TFT_Set10_Social_Header_TFT_Set10_Base_Key_Art_Full_Logo_4k.jpg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .title-text {
        font-family: sans-serif; font-size: 50px; font-weight: 900; color: #ffffff;
        text-shadow: 0 0 10px #ff0055; text-align: center; margin-bottom: 20px; text-transform: uppercase;
    }
    .result-box {
        padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; color: white; margin-top: 20px;
    }
    .boosted { background-color: rgba(220, 20, 60, 0.9); border: 4px solid red; }
    .clean { background-color: rgba(34, 139, 34, 0.9); border: 2px solid #00ff00; }
    .stat-box { background-color: rgba(0,0,0,0.7); padding: 15px; border-radius: 10px; margin-top: 10px; color: white;}
    label, .stMarkdown, p, .stMetricLabel { color: white !important; text-shadow: 1px 1px 2px black; }
    div[data-testid="stMetricValue"] { color: #00ff00 !important; }
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<div class="title-text">WHO IS BOOSTING YOU?</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("Config")
api_key = st.sidebar.text_input("1. Clé API Riot", type="password").strip()

# --- INPUT ---
col1, col2 = st.columns([3, 1])
with col1:
    riot_id_input = st.text_input("2. Riot ID", placeholder="Nom#TAG")
with col2:
    region_select = st.selectbox("3. Région", ["EUW1", "NA1", "KR", "EUN1"])

# --- FONCTIONS ---
def get_regions(region_code):
    if region_code in ["EUW1", "EUN1", "TR1", "RU"]: return "europe"
    elif region_code == "KR": return "asia"
    else: return "americas"

def analyze():
    if not api_key or "#" not in riot_id_input:
        st.error("Il manque la clé API ou le #TAG.")
        return

    name_raw, tag = riot_id_input.split("#")
    name_encoded = quote(name_raw)
    routing_region = get_regions(region_select)
    
    with st.spinner('Inspection des performances...'):
        # 1. PUUID
        url_puuid = f"https://{routing_region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name_encoded}/{tag}?api_key={api_key}"
        resp = requests.get(url_puuid)
        if resp.status_code != 200:
            st.error(f"Erreur API: {resp.status_code}")
            return
        puuid = resp.json().get("puuid")

        # 2. Matchs (Queue 420 = SoloQ)
        url_matches = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=10&api_key={api_key}"
        match_ids = requests.get(url_matches).json()

        if not match_ids:
            st.warning("Pas de games récentes.")
            return

        # 3. Analyse détaillée
        duo_tracker = {}
        progress_bar = st.progress(0)
        
        # Pour comparer les stats du joueur vs son duo
        my_stats_accumulator = {'kills': 0, 'deaths': 0, 'assists': 0}

        for i, match_id in enumerate(match_ids):
            progress_bar.progress((i + 1) / len(match_ids))
            detail_url = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={api_key}"
            data = requests.get(detail_url).json()
            
            if 'info' not in data: continue
            
            participants = data['info']['participants']
            me = next((p for p in participants if p['puuid'] == puuid), None)
            
            if me:
                # On cumule mes stats pour voir si je suis nul
                my_stats_accumulator['kills'] += me['kills']
                my_stats_accumulator['deaths'] += me['deaths']
                my_stats_accumulator['assists'] += me['assists']

                for p in participants:
                    if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                        # Récupération du nom sécurisée
                        r_name = p.get('riotIdGameName', p.get('summonerName', 'Unknown'))
                        r_tag = p.get('riotIdTagLine', '')
                        identity = f"{r_name}#{r_tag}" if r_tag else r_name

                        if identity not in duo_tracker:
                            duo_tracker[identity] = {'games': 0, 'wins': 0, 'kills': 0, 'deaths': 0, 'assists': 0}
                        
                        duo_tracker[identity]['games'] += 1
                        if p['win']: duo_tracker[identity]['wins'] += 1
                        duo_tracker[identity]['kills'] += p['kills']
                        duo_tracker[identity]['deaths'] += p['deaths']
                        duo_tracker[identity]['assists'] += p['assists']
            time.sleep(0.05)

        # 4. Verdict Sévère
        st.markdown("---")
        
        # On cherche le duo le plus fréquent
        best_duo = None
        max_games = 0
        
        for identity, stats in duo_tracker.items():
            if stats['games'] > max_games:
                max_games = stats['games']
                best_duo = (identity, stats)

        # RÈGLES DURCIES : Si un mec est là 2 fois ou plus
        if best_duo and max_games >= 2:
            identity, stats = best_duo
            
            # Calcul KDA Duo
            duo_deaths = stats['deaths'] if stats['deaths'] > 0 else 1
            duo_kda = round((stats['kills'] + stats['assists']) / duo_deaths, 2)
            
            # Calcul KDA Joueur (sur 10 games)
            my_deaths = my_stats_accumulator['deaths'] if my_stats_accumulator['deaths'] > 0 else 1
            my_kda = round((my_stats_accumulator['kills'] + my_stats_accumulator['assists']) / my_deaths, 2)

            winrate = (stats['wins'] / stats['games']) * 100
            
            st.markdown(f"""<div class="result-box boosted">🚨 DUO DÉTECTÉ 🚨<br>{identity}</div>""", unsafe_allow_html=True)
            
            # Affichage des stats comparatives
            st.markdown(f"<div class='stat-box'>Ils ont joué <b>{stats['games']}</b> parties ensemble (Winrate: {winrate}%).<br>Voici la vérité sur les stats :</div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Ton KDA (Moyen)", my_kda)
            with c2:
                st.metric(f"KDA de {identity.split('#')[0]}", duo_kda, delta=round(duo_kda - my_kda, 2))

            if duo_kda > my_kda + 1.0:
                st.error(f"VERDICT : Il joue 10x mieux que toi. C'est du boosting.")
            elif winrate < 50:
                st.warning("VERDICT : C'est ton Duo, mais vous perdez. C'est du 'Emotional Support', pas du boosting.")
            else:
                st.success("VERDICT : Duo solide, niveaux équivalents.")
                
        else:
            st.markdown("""<div class="result-box clean">SOLO PLAYER</div>""", unsafe_allow_html=True)
            st.write("Aucun joueur croisé plus d'une fois sur les 10 dernières games.")

if st.button('SCANNER (MODE STRICT)', type="primary"):
    analyze()