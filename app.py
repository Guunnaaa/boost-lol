import streamlit as st
import requests
import time
from urllib.parse import quote

# --- CONFIGURATION ---
st.set_page_config(page_title="Boost Detector ULTIMATE", layout="centered")

# --- RÉCUPÉRATION DE LA CLÉ SÉCURISÉE ---
# Le code va chercher la clé dans les réglages de Streamlit Cloud
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ ERREUR CONFIG : Tu dois ajouter la clé API dans les 'Secrets' sur Streamlit Cloud.")
    st.stop()

# --- URL DE TON IMAGE DE FOND ---
# Instructions :
# 1. Sur GitHub, upload ton image et appelle-la "bg.jpg".
# 2. Remplace [TON_NOM_GITHUB] et [NOM_REPO] ci-dessous par les tiens.
# Exemple : https://raw.githubusercontent.com/Pseudo/boost-lol/main/bg.jpg
BACKGROUND_IMAGE_URL = "https://raw.githubusercontent.com/[TON_NOM_GITHUB]/[NOM_REPO]/main/bg.jpg"

# Si tu n'as pas encore mis l'image, on utilise une image par défaut temporaire :
# (Tu peux supprimer cette ligne une fois que tu as mis la tienne)
BACKGROUND_IMAGE_URL = "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123"


# --- STYLE CSS (FOND TUILE) ---
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("{BACKGROUND_IMAGE_URL}");
        background-size: 150px; /* Taille des petites têtes */
        background-repeat: repeat; /* Répétition partout */
        background-attachment: fixed;
    }}
    /* Pour rendre le texte lisible par dessus l'image */
    .block-container {{
        background-color: rgba(0, 0, 0, 0.85); /* Fond noir semi-transparent au centre */
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #444;
    }}
    .title-text {{
        font-family: sans-serif; font-size: 50px; font-weight: 900; color: #ffffff;
        text-shadow: 0 0 10px #ff0055; text-align: center; margin-bottom: 20px; text-transform: uppercase;
    }}
    .result-box {{
        padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; color: white; margin-top: 20px;
    }}
    .boosted {{ background-color: rgba(220, 20, 60, 0.9); border: 4px solid red; }}
    .clean {{ background-color: rgba(34, 139, 34, 0.9); border: 2px solid #00ff00; }}
    .stat-box {{ background-color: rgba(50,50,50,0.9); padding: 15px; border-radius: 10px; margin-top: 10px; color: white; border: 1px solid white; }}
    label, .stMarkdown, p, .stMetricLabel {{ color: white !important; }}
    div[data-testid="stMetricValue"] {{ color: #00ff00 !important; }}
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<div class="title-text">WHO IS BOOSTING YOU?</div>', unsafe_allow_html=True)

# --- INPUT ---
col1, col2 = st.columns([3, 1])
with col1:
    riot_id_input = st.text_input("Riot ID", placeholder="Exemple: Faker#KR1")
with col2:
    region_select = st.selectbox("Région", ["EUW1", "NA1", "KR", "EUN1", "TR1"])

# --- FONCTIONS ---
def get_regions(region_code):
    if region_code in ["EUW1", "EUN1", "TR1", "RU"]: return "europe"
    elif region_code == "KR": return "asia"
    else: return "americas"

def analyze():
    if not riot_id_input or "#" not in riot_id_input:
        st.error("⚠️ Entre un pseudo valide (Nom#TAG).")
        return

    name_raw, tag = riot_id_input.split("#")
    name_encoded = quote(name_raw)
    routing_region = get_regions(region_select)
    
    with st.spinner('Inspection des dossiers confidentiels...'):
        # 1. PUUID
        url_puuid = f"https://{routing_region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name_encoded}/{tag}?api_key={API_KEY}"
        resp = requests.get(url_puuid)
        
        if resp.status_code == 403:
            st.error("⛔ La clé API est invalide. Vérifie tes 'Secrets' Streamlit.")
            return
        elif resp.status_code != 200:
            st.error(f"Erreur : Joueur introuvable ou erreur technique ({resp.status_code})")
            return
            
        puuid = resp.json().get("puuid")

        # 2. Matchs (Queue 420 = SoloQ)
        url_matches = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=10&api_key={API_KEY}"
        match_resp = requests.get(url_matches)
        match_ids = match_resp.json()

        if not match_ids or len(match_ids) == 0:
            st.warning("Pas de games classées récentes.")
            return

        # 3. Analyse détaillée
        duo_tracker = {}
        progress_bar = st.progress(0)
        
        # Pour comparer les stats
        my_stats_accumulator = {'kills': 0, 'deaths': 0, 'assists': 0}

        for i, match_id in enumerate(match_ids):
            progress_bar.progress((i + 1) / len(match_ids))
            detail_url = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
            data = requests.get(detail_url).json()
            
            if 'info' not in data: continue
            
            participants = data['info']['participants']
            me = next((p for p in participants if p['puuid'] == puuid), None)
            
            if me:
                my_stats_accumulator['kills'] += me['kills']
                my_stats_accumulator['deaths'] += me['deaths']
                my_stats_accumulator['assists'] += me['assists']

                for p in participants:
                    if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
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
        
        best_duo = None
        max_games = 0
        
        for identity, stats in duo_tracker.items():
            if stats['games'] > max_games:
                max_games = stats['games']
                best_duo = (identity, stats)

        # RÈGLE : Si croisé 2 fois ou plus
        if best_duo and max_games >= 2:
            identity, stats = best_duo
            
            duo_deaths = stats['deaths'] if stats['deaths'] > 0 else 1
            duo_kda = round((stats['kills'] + stats['assists']) / duo_deaths, 2)
            
            my_deaths = my_stats_accumulator['deaths'] if my_stats_accumulator['deaths'] > 0 else 1
            my_kda = round((my_stats_accumulator['kills'] + my_stats_accumulator['assists']) / my_deaths, 2)

            winrate = (stats['wins'] / stats['games']) * 100
            
            st.markdown(f"""<div class="result-box boosted">🚨 DUO DÉTECTÉ 🚨<br>{identity}</div>""", unsafe_allow_html=True)
            
            st.markdown(f"<div class='stat-box'>Vu <b>{stats['games']}</b> fois ensemble (Winrate: {winrate}%).<br>Comparatif des KDA :</div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Ton KDA", my_kda)
            with c2:
                st.metric(f"KDA de {identity.split('#')[0]}", duo_kda, delta=round(duo_kda - my_kda, 2))

            if duo_kda > my_kda + 1.0:
                st.error(f"VERDICT : Il joue beaucoup mieux que toi. C'est du boosting pur.")
            elif winrate < 50:
                st.warning("VERDICT : C'est ton Duo, mais vous perdez. Arrêtez le massacre.")
            else:
                st.success("VERDICT : Duo legit, niveaux équivalents.")
                
        else:
            st.markdown("""<div class="result-box clean">SOLO PLAYER</div>""", unsafe_allow_html=True)
            st.write("Aucun joueur croisé de façon récurrente sur les 10 dernières games.")

if st.button('LANCER L\'ANQUÊTE', type="primary"):
    analyze()
