import streamlit as st
import requests
import time
from urllib.parse import quote

# --- CONFIGURATION (MODE WIDE POUR CORRIGER L'AFFICHAGE COUPÉ) ---
st.set_page_config(page_title="Boost Detector V5", layout="wide")

# --- RÉCUPÉRATION CLÉ API ---
try:
    API_KEY = st.secrets["RIOT_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ Clé API introuvable dans les secrets.")
    st.stop()

# --- BACKGROUND IMAGE ---
BACKGROUND_IMAGE_URL = "https://media.discordapp.net/attachments/1065027576572518490/1179469739770630164/face_tiled.jpg?ex=657a90f2&is=65681bf2&hm=123"
# Si tu as mis ton image sur GitHub, remplace le lien ci-dessus.

# --- CSS ROBUSTE (POUR CENTRER SANS COUPER) ---
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
    
    /* On force le contenu à se centrer dans une boite de max 700px */
    .block-container {{
        max-width: 700px !important;
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
        margin: auto !important;
        background-color: rgba(0, 0, 0, 0.90); /* Fond très sombre */
        border-radius: 20px;
        border: 1px solid #333;
        box-shadow: 0 0 20px rgba(0,0,0,0.8);
    }}

    /* Textes et Titres */
    .title-text {{
        font-family: sans-serif; font-size: 40px; font-weight: 900; color: #ffffff;
        text-shadow: 0 0 10px #ff0055; text-align: center; margin-bottom: 20px; text-transform: uppercase;
        line-height: 1.2;
    }}
    .result-box {{
        padding: 20px; border-radius: 10px; text-align: center; font-size: 22px; font-weight: bold; color: white; margin-top: 20px;
    }}
    .boosted {{ background-color: rgba(220, 20, 60, 0.9); border: 4px solid red; }}
    .clean {{ background-color: rgba(34, 139, 34, 0.9); border: 2px solid #00ff00; }}
    .stat-box {{ 
        background-color: rgba(50,50,50,0.5); 
        padding: 15px; 
        border-radius: 10px; 
        margin-top: 15px; 
        color: #ddd; 
        font-size: 14px;
        border-left: 3px solid #ff0055;
    }}
    
    /* Force la couleur du texte Streamlit en blanc */
    p, label, .stMarkdown, .stMetricLabel {{ color: #eee !important; }}
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
        st.error("⚠️ Format invalide. Utilise Nom#TAG.")
        return

    name_raw, tag = riot_id_input.split("#")
    name_encoded = quote(name_raw)
    routing_region = get_regions(region_select)
    
    # 1. PUUID
    url_puuid = f"https://{routing_region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name_encoded}/{tag}?api_key={API_KEY}"
    
    with st.spinner('Analyse des 20 dernières games...'):
        resp = requests.get(url_puuid)
        if resp.status_code != 200:
            st.error(f"Erreur Riot API ({resp.status_code}). Vérifie le pseudo.")
            return
        puuid = resp.json().get("puuid")

        # 2. MATCHS (20 Dernières SoloQ)
        # count=20 ici
        url_matches = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=20&api_key={API_KEY}"
        match_ids = requests.get(url_matches).json()

        if not match_ids:
            st.warning("Pas de SoloQ trouvée.")
            return

        # 3. ANALYSE COMPARATIVE
        # On va stocker les stats DUO et MES stats uniquement quand je joue AVEC lui
        duo_data = {} 
        # Structure : {'Pseudo#Tag': {'games': 0, 'wins': 0, 'duo_kills':0..., 'my_kills_with_him':0...}}

        progress_bar = st.progress(0)
        
        for i, match_id in enumerate(match_ids):
            progress_bar.progress((i + 1) / len(match_ids))
            
            detail_url = f"https://{routing_region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
            data = requests.get(detail_url).json()
            
            if 'info' not in data: continue
            
            participants = data['info']['participants']
            me = next((p for p in participants if p['puuid'] == puuid), None)
            
            if me:
                # Je note mes stats pour cette game
                my_k = me['kills']
                my_d = me['deaths']
                my_a = me['assists']
                my_dmg = me['totalDamageDealtToChampions']

                # Je scanne les autres
                for p in participants:
                    if p['teamId'] == me['teamId'] and p['puuid'] != puuid:
                        # Identité
                        r_name = p.get('riotIdGameName', p.get('summonerName', 'Unknown'))
                        r_tag = p.get('riotIdTagLine', '')
                        identity = f"{r_name}#{r_tag}" if r_tag else r_name
                        
                        if identity not in duo_data:
                            duo_data[identity] = {
                                'games': 0, 'wins': 0,
                                'duo_k': 0, 'duo_d': 0, 'duo_a': 0, 'duo_dmg': 0,
                                'my_k': 0, 'my_d': 0, 'my_a': 0, 'my_dmg': 0
                            }
                        
                        # On incrémente les stats du DUO
                        stats = duo_data[identity]
                        stats['games'] += 1
                        if p['win']: stats['wins'] += 1
                        
                        stats['duo_k'] += p['kills']
                        stats['duo_d'] += p['deaths']
                        stats['duo_a'] += p['assists']
                        stats['duo_dmg'] += p['totalDamageDealtToChampions']
                        
                        # IMPORTANT : On incrémente MES stats (liées à ce duo)
                        stats['my_k'] += my_k
                        stats['my_d'] += my_d
                        stats['my_a'] += my_a
                        stats['my_dmg'] += my_dmg

            # Pause pour l'API Rate Limit (surtout avec 20 games)
            time.sleep(0.15) 

        # 4. VERDICT
        st.markdown("---")
        
        # Trouver le meilleur duo
        suspect_name = None
        suspect_stats = None
        max_games = 0

        for identity, stats in duo_data.items():
            if stats['games'] > max_games:
                max_games = stats['games']
                suspect_name = identity
                suspect_stats = stats

        # SEUIL : 4 games sur 20 pour être considéré comme un Duo régulier
        if suspect_stats and max_games >= 4:
            s = suspect_stats
            
            # Calcul des moyennes sur les games communes
            # KDA
            duo_deaths = s['duo_d'] if s['duo_d'] > 0 else 1
            duo_kda = round((s['duo_k'] + s['duo_a']) / duo_deaths, 2)
            
            my_deaths = s['my_d'] if s['my_d'] > 0 else 1
            my_kda = round((s['my_k'] + s['my_a']) / my_deaths, 2)
            
            # Dégâts moyens
            duo_avg_dmg = int(s['duo_dmg'] / s['games'])
            my_avg_dmg = int(s['my_dmg'] / s['games'])

            winrate = int((s['wins'] / s['games']) * 100)

            # AFFICHAGE
            st.markdown(f"""<div class="result-box boosted">🚨 DUO SUSPECT : {suspect_name} 🚨</div>""", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center;'>Vu <b>{s['games']} fois</b> sur les 20 dernières games.</p>", unsafe_allow_html=True)

            # Colonnes stats
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<h3 style='text-align:center; color:white;'>TOI<br>(avec lui)</h3>", unsafe_allow_html=True)
                st.metric("KDA", my_kda)
                st.metric("Dégâts/Game", my_avg_dmg)
            with c2:
                st.markdown(f"<h3 style='text-align:center; color:red;'>LUI<br>(le booster?)</h3>", unsafe_allow_html=True)
                delta_kda = round(duo_kda - my_kda, 2)
                delta_dmg = duo_avg_dmg - my_avg_dmg
                st.metric("KDA", duo_kda, delta=delta_kda)
                st.metric("Dégâts/Game", duo_avg_dmg, delta=delta_dmg)

            # Le Jugement Final
            st.markdown(f"<div class='stat-box'>Winrate ensemble : <b>{winrate}%</b></div>", unsafe_allow_html=True)

            if duo_kda > my_kda + 1.5 or duo_avg_dmg > my_avg_dmg + 5000:
                st.error(f"VERDICT : 100% BOOSTED. Il a de meilleures stats que toi sur VOS parties.")
            elif winrate < 50:
                st.warning("VERDICT : C'est bien ton duo, mais vous êtes nuls ensemble.")
            else:
                st.success("VERDICT : Duo legit. Vous contribuez tous les deux à la victoire.")

        else:
            st.markdown("""<div class="result-box clean">SOLO PLAYER</div>""", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center;'>Aucun joueur croisé plus de 3 fois sur les 20 dernières games.</p>", unsafe_allow_html=True)

if st.button('SCANNER LES 20 DERNIÈRES GAMES', type="primary"):
    analyze()
