import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import json
from datetime import datetime
import pandas as pd
import os
import base64
import textwrap
from io import BytesIO
import plotly.express as px

from pathlib import Path
import os

if os.path.exists("/home/site"):
    DB_DIR = Path("/home/data")   # Azure App Service
else:
    DB_DIR = Path(".")            # Streamlit Cloud / local

DB_DIR.mkdir(parents=True, exist_ok=True)

DB_NAME = str(DB_DIR / "tna_demo.db")

USJ_BLUE = "#001F5B"
USJ_RED = "#8B1538"
USJ_GOLD = "#C9A227"
USJ_TEXT = "#1B2A41"
USJ_LIGHT_BLUE = "#EAF2F8"

CFP_LOGO_PATH = "CFP LOGO.png"
USJ_LOGO_PATH = "USJ LOGO 150.png"


PSG_THEMES = [
    "Communication constructive",
    "Résolution de conflits",
    "Intelligence interpersonnelle",
    "Diversité culturelle",
    "Collaboration",
    "Communication écrite",
    "Communication orale",
    "Public speaking and Body language",
    "Santé mentale",
    "Bien-être au travail",
    "Intelligence émotionnelle",
    "Gestion du stress",
    "Gestion du temps",
    "Mindfulness",
    "Team building",
    "Inclusion",
    "Harcèlement",
    "Branding",
    "Création de contenu-Réseaux sociaux",
    "Outils intelligence artificielle",
    "Bureautique-Word",
    "Bureautique-Excel",
    "Bureautique-PowerPoint",
    "Gestion financière",
    "Esprit critique et résolution de problèmes",
    "Gestion du changement en milieu universitaire",
    "Gestion de projets",
    "Équilibre vie professionnelle vie personnelle",
    "Ergonomie",
    "Customer service"
]

DD_LEADER_THEMES = [
    "Outils intelligence artificielle-IA",
    "Agile management",
    "Strategic decision making",
    "Gestion budgétaire",
    "Gestion financière",
    "Digital marketing",
    "Change management in academic institutions",
    "Crisis management and institutional resilience",
    "Data-driven decision making"
]


DEMO_USERS = {
    # =========================
    # SRH - PSG
    # =========================
    "707619": {"role": "psg", "name": "Edgard BARADHY", "poste": "Préposé aux remboursements médicaux et à la SG", "faculty": "SRH", "institution": "SRH", "department": "", "email": "edgard...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "701304": {"role": "psg", "name": "Joëlle BAZ TRABOULSI", "poste": "Directeur-adjoint - Administration du personnel", "faculty": "SRH", "institution": "SRH", "department": "", "email": "joelle...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "711919": {"role": "psg", "name": "Pamela BERBERI FADDOUL", "poste": "Coordinateur - Bureau des assurances", "faculty": "SRH", "institution": "SRH", "department": "", "email": "pamela...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "717400": {"role": "psg", "name": "Michelle BITAR", "poste": "Chargée de support administratif", "faculty": "SRH", "institution": "SRH", "department": "", "email": "michelle...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "712197": {"role": "psg", "name": "Grace BOU DOUMIT DARGHAM", "poste": "Gestionnaire de paie", "faculty": "SRH", "institution": "SRH", "department": "", "email": "grace...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "701696": {"role": "psg", "name": "Rana CHAAYA MHAWEJ", "poste": "Directeur-adjoint - assurances", "faculty": "SRH", "institution": "SRH", "department": "", "email": "rana...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "701813": {"role": "psg", "name": "Yolla CHAMMAS (EL) ABI NASR", "poste": "Gestionnaire de projets et de communication RH", "faculty": "SRH", "institution": "SRH", "department": "", "email": "yolla...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "713286": {"role": "psg", "name": "Sara HAWHA", "poste": "Chargé de support administratif", "faculty": "SRH", "institution": "SRH", "department": "", "email": "sara...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "703865": {"role": "psg", "name": "Antoine ISHAK", "poste": "Représentant du personnel auprès de la CNSS et du ministère du travail", "faculty": "SRH", "institution": "SRH", "department": "", "email": "antoine...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "709975": {"role": "psg", "name": "Joseph KANAAN", "poste": "Agent administratif", "faculty": "SRH", "institution": "SRH", "department": "", "email": "joseph...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "715394": {"role": "psg", "name": "Angela KASSIS (EL)", "poste": "Assistant(e) RH", "faculty": "SRH", "institution": "SRH", "department": "", "email": "angela...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "704400": {"role": "psg", "name": "Marie KHAIRALLAH", "poste": "Chef d'unité - paie des vacataires", "faculty": "SRH", "institution": "SRH", "department": "", "email": "marie...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "709782": {"role": "psg", "name": "Claudine MOUBARAK COSTANTINE", "poste": "Coordinateur d'inclusion", "faculty": "SRH", "institution": "SRH", "department": "", "email": "claudine...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "712070": {"role": "psg", "name": "Hind NASTA MOUSSA", "poste": "Agent de numérisation", "faculty": "SRH", "institution": "SRH", "department": "", "email": "hind...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "706239": {"role": "psg", "name": "Hâla RISHA BALDO", "poste": "Assistant aux affaires administratives", "faculty": "SRH", "institution": "SRH", "department": "", "email": "hala...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "715995": {"role": "psg", "name": "Diala SEMAN CHALHOUB", "poste": "Chargé de recrutement", "faculty": "SRH", "institution": "SRH", "department": "", "email": "diala...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "716185": {"role": "psg", "name": "Sara Maria SOUEIDY (EL)", "poste": "Assistant de paie", "faculty": "SRH", "institution": "SRH", "department": "", "email": "sarah...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "716498": {"role": "psg", "name": "Ranine TABET", "poste": "Chargé de support administratif", "faculty": "SRH", "institution": "SRH", "department": "", "email": "ranine...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},
    "710743": {"role": "psg", "name": "Sarah ZAHREDDINE", "poste": "Gestionnaire RH", "faculty": "SRH", "institution": "SRH", "department": "", "email": "sarah...", "director_name": "Gladys GHRAICHY", "director_code": "703095", "director_email": "gladys..."},

    # =========================
    # CFP - PSG
    # =========================
    "717612": {"role": "psg", "name": "Angel BAHOUT MRAD", "poste": "Chef d'unité - formation continue", "faculty": "CFP", "institution": "CFP", "department": "", "email": "angel...", "director_name": "Fadi HAGE", "director_code": "703328", "director_email": "fadi..."},
    "715919": {"role": "psg", "name": "Josiane DIAB MAALOUF KHALAF", "poste": "Développeur d'affaires", "faculty": "CFP", "institution": "CFP", "department": "", "email": "josiane...", "director_name": "Fadi HAGE", "director_code": "703328", "director_email": "fadi..."},
    "719455": {"role": "psg", "name": "Elissa MAKHOUL", "poste": "Chargé de communication", "faculty": "CFP", "institution": "CFP", "department": "", "email": "elissa...", "director_name": "Fadi HAGE", "director_code": "703328", "director_email": "fadi..."},
    "718851": {"role": "psg", "name": "Elyse SAADEH DIBO", "poste": "Chargé de support administratif", "faculty": "CFP", "institution": "CFP", "department": "", "email": "elyse...", "director_name": "Fadi HAGE", "director_code": "703328", "director_email": "fadi..."},
    "718491": {"role": "psg", "name": "Albert YAMMINE", "poste": "Coordinateur de la formation continue", "faculty": "CFP", "institution": "CFP", "department": "", "email": "albert...", "director_name": "Fadi HAGE", "director_code": "703328", "director_email": "fadi..."},

    # =========================
    # DIRECTORS
    # =========================
    "703095": {
        "role": "director",
        "name": "Gladys GHRAICHY",
        "poste": "Directeur du service des ressources humaines",
        "faculty": "SRH",
        "institution": "SRH",
        "department": "",
        "email": "gladys..."
    },

    "703328": {
        "role": "director",
        "name": "Fadi HAGE",
        "poste": "Directeur",
        "faculty": "CFP",
        "institution": "CFP",
        "department": "",
        "email": "fadi..."
    },

    # =========================
    # ADMIN
    # =========================
    "ADMIN2032": {
        "role": "admin",
        "name": "Administrateur TNA",
        "poste": "Administrateur",
        "faculty": "USJ",
        "institution": "USJ",
        "department": "",
        "email": ""
    }
}

TRIAL_PSG_RESPONSES = {
    # DD001 - mixed cases
    "PSG001": ["Communication constructive", "Diversité culturelle", "Communication écrite"],          # 0 common with director
    "PSG002": ["Outils intelligence artificielle", "Gestion du temps", "Communication écrite"],         # 1 common
    "PSG003": ["Bureautique-Excel", "Outils intelligence artificielle", "Gestion de projets"],          # 2 common
    "PSG004": ["Résolution de conflits", "Communication orale", "Team building"],                      # 0 common
    "PSG005": ["Customer service", "Gestion du stress", "Communication constructive"],                  # 3 common

    # DD002 - mostly low/no agreement
    "PSG006": ["Santé mentale", "Gestion du stress", "Intelligence émotionnelle"],                     # 1 common
    "PSG007": ["Bureautique-Excel", "Ergonomie", "Gestion du temps"],                                  # 0 common
    "PSG008": ["Customer service", "Communication orale", "Diversité culturelle"],                      # 1 common
    "PSG009": ["Gestion de projets", "Collaboration", "Communication écrite"],                         # 0 common
    "PSG010": ["Outils intelligence artificielle", "Bureautique-PowerPoint", "Création de contenu-Réseaux sociaux"], # 2 common

    # DD003 - varied business/admin cases
    "PSG011": ["Gestion financière", "Bureautique-Excel", "Esprit critique et résolution de problèmes"], # 0 common
    "PSG012": ["Communication orale", "Public speaking and Body language", "Customer service"],          # 1 common
    "PSG013": ["Branding", "Création de contenu-Réseaux sociaux", "Customer service"],                  # 2 common
    "PSG014": ["Gestion du changement en milieu universitaire", "Gestion de projets", "Collaboration"], # 0 common
    "PSG015": ["Esprit critique et résolution de problèmes", "Bureautique-Excel", "Communication écrite"], # 1 common

    # DD004 - mostly no common themes
    "PSG016": ["Communication écrite", "Bureautique-Word", "Customer service"],                         # 0 common
    "PSG017": ["Gestion du temps", "Gestion du stress", "Collaboration"],                              # 1 common
    "PSG018": ["Inclusion", "Diversité culturelle", "Intelligence interpersonnelle"],                   # 0 common
    "PSG019": ["Outils intelligence artificielle", "Bureautique-PowerPoint", "Gestion de projets"],     # 2 common
    "PSG020": ["Branding", "Communication orale", "Création de contenu-Réseaux sociaux"],               # 0 common

    # DD005 - technical/project cases
    "PSG021": ["Ergonomie", "Gestion de projets", "Bureautique-Excel"],                                 # 1 common
    "PSG022": ["Outils intelligence artificielle", "Esprit critique et résolution de problèmes", "Communication constructive"], # 0 common
    "PSG023": ["Customer service", "Gestion du temps", "Communication écrite"],                          # 1 common
    "PSG024": ["Collaboration", "Gestion du changement en milieu universitaire", "Team building"],       # 2 common
    "PSG025": ["Outils intelligence artificielle", "Gestion de projets", "Esprit critique et résolution de problèmes"] # 0 common
}


TRIAL_DIRECTOR_RESPONSES = {
    "DD001": {
        "leader": ["Data-driven decision making", "Outils intelligence artificielle-IA", "Strategic decision making"],
        "employees": {
            "PSG001": ["Gestion financière", "Ergonomie", "Bureautique-PowerPoint"],                    # 0 common
            "PSG002": ["Collaboration", "Outils intelligence artificielle", "Customer service"],        # 1 common, not same priority
            "PSG003": ["Gestion de projets", "Bureautique-Excel", "Team building"],                     # 2 common
            "PSG004": ["Bureautique-Excel", "Bien-être au travail", "Gestion financière"],              # 0 common
            "PSG005": ["Customer service", "Gestion du stress", "Communication constructive"]           # 3 common
        }
    },
    "DD002": {
        "leader": ["Crisis management and institutional resilience", "Gestion budgétaire", "Change management in academic institutions"],
        "employees": {
            "PSG006": ["Bien-être au travail", "Santé mentale", "Mindfulness"],                         # 1 common
            "PSG007": ["Communication constructive", "Collaboration", "Bureautique-PowerPoint"],        # 0 common
            "PSG008": ["Gestion du temps", "Diversité culturelle", "Ergonomie"],                        # 1 common
            "PSG009": ["Customer service", "Gestion du stress", "Bureautique-Excel"],                   # 0 common
            "PSG010": ["Branding", "Bureautique-PowerPoint", "Outils intelligence artificielle"]        # 2 common
        }
    },
    "DD003": {
        "leader": ["Strategic decision making", "Digital marketing", "Gestion financière"],
        "employees": {
            "PSG011": ["Communication orale", "Gestion du temps", "Customer service"],                  # 0 common
            "PSG012": ["Gestion financière", "Customer service", "Bureautique-Excel"],                  # 1 common
            "PSG013": ["Branding", "Customer service", "Gestion de projets"],                           # 2 common
            "PSG014": ["Santé mentale", "Bureautique-Word", "Ergonomie"],                               # 0 common
            "PSG015": ["Communication écrite", "Team building", "Gestion du stress"]                    # 1 common
        }
    },
    "DD004": {
        "leader": ["Agile management", "Change management in academic institutions", "Data-driven decision making"],
        "employees": {
            "PSG016": ["Collaboration", "Gestion de projets", "Ergonomie"],                             # 0 common
            "PSG017": ["Branding", "Collaboration", "Bureautique-PowerPoint"],                          # 1 common
            "PSG018": ["Bureautique-Excel", "Customer service", "Gestion financière"],                   # 0 common
            "PSG019": ["Gestion de projets", "Outils intelligence artificielle", "Communication orale"], # 2 common
            "PSG020": ["Gestion du stress", "Bureautique-Word", "Customer service"]                     # 0 common
        }
    },
    "DD005": {
        "leader": ["Outils intelligence artificielle-IA", "Data-driven decision making", "Gestion budgétaire"],
        "employees": {
            "PSG021": ["Gestion du temps", "Ergonomie", "Customer service"],                            # 1 common
            "PSG022": ["Bureautique-Word", "Team building", "Gestion financière"],                      # 0 common
            "PSG023": ["Communication orale", "Customer service", "Gestion financière"],                # 1 common
            "PSG024": ["Team building", "Bureautique-Excel", "Collaboration"],                          # 2 common
            "PSG025": ["Customer service", "Communication orale", "Ergonomie"]                         # 0 common
        }
    }
}


def image_to_base64(image_path):
    if not os.path.exists(image_path):
        return ""

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def apply_style():
    st.markdown(f"""
    <style>

    section[data-testid="stSidebar"],
    div[data-testid="stSidebar"],
    [data-testid="stSidebar"] {{
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }}

    [data-testid="collapsedControl"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    header,
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stMainMenu"],
    [data-testid="stDeployButton"],
    .stDeployButton,
    #MainMenu {{
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }}
    
    .stApp {{
        background: linear-gradient(180deg, #F7FAFE 0%, #EEF3F9 100%);
        color: {USJ_TEXT};
    }}

    .block-container {{
        padding-top: 1.1rem;
        max-width: 1320px;
    }}

    h1, h2, h3 {{
        color: {USJ_BLUE};
        font-weight: 400;
    }}

    .platform-header {{
        background: #ffffff;
        border: 1px solid #DDE5F0;
        border-radius: 22px;
        padding: 16px 24px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 10px 30px rgba(27,42,65,0.07);
    }}

    .logo-side {{
        width: 180px;
        display: flex;
        align-items: center;
    }}

    .left-logo {{
        justify-content: flex-start;
    }}

    .right-logo {{
        justify-content: flex-end;
    }}

    .platform-logo {{
        max-height: 82px;
        max-width: 165px;
        object-fit: contain;
        display: block;
    }}

    .cfp-logo {{
        max-height: 86px;
    }}

    .usj-logo {{
        max-height: 78px;
    }}

    .header-center {{
        text-align: center;
        flex: 1;
        padding: 0 20px;
    }}

    .header-title {{
        color: {USJ_BLUE};
        font-weight: 400;
        font-size: 1.45rem;
        line-height: 1.2;
    }}

    .header-subtitle {{
        color: #6B7688;
        font-weight: 700;
        font-size: 0.96rem;
        margin-top: 4px;
    }}

    .logo-placeholder {{
        border: 2px solid {USJ_BLUE};
        color: {USJ_BLUE};
        border-radius: 14px;
        padding: 14px 20px;
        font-weight: 400;
        background: #F7FAFE;
    }}

    .main-hero {{
        background: linear-gradient(135deg, {USJ_BLUE} 0%, #123E7C 60%, {USJ_RED} 100%);
        border-radius: 24px;
        padding: 30px 34px;
        margin-bottom: 24px;
        color: white;
        box-shadow: 0 18px 45px rgba(0,31,91,0.18);
    }}

    .hero-kicker {{
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        opacity: 0.85;
        font-weight: 700;
        margin-bottom: 8px;
    }}

    .hero-title {{
        font-size: 2.15rem;
        line-height: 1.1;
        font-weight: 400;
        margin-bottom: 10px;
    }}

    .hero-subtitle {{
        font-size: 1.02rem;
        line-height: 1.55;
        opacity: 0.95;
    }}

    div[data-baseweb="input"],
    div[data-baseweb="select"],
    div[data-baseweb="textarea"] {{
        background-color: #ffffff !important;
        border: 2px solid {USJ_BLUE} !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 14px rgba(0,31,91,0.12) !important;
        min-height: 52px !important;
    }}

    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"]:focus-within,
    div[data-baseweb="textarea"]:focus-within {{
        border: 3px solid {USJ_RED} !important;
        box-shadow: 0 0 0 4px rgba(139,21,56,0.14) !important;
    }}

    div[data-baseweb="input"] input {{
        background-color: #ffffff !important;
        color: {USJ_BLUE} !important;
        font-weight: 750 !important;
        font-size: 17px !important;
        padding: 12px 14px !important;
    }}

    div[data-baseweb="select"] {{
        min-height: 58px !important;
        padding: 3px 6px !important;
        box-sizing: border-box !important;
        overflow: visible !important;
    }}

    div[data-baseweb="select"] > div {{
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        padding-left: 10px !important;
        padding-right: 10px !important;
        box-sizing: border-box !important;
    }}

    div[data-baseweb="select"] div,
    div[data-baseweb="select"] span {{
        color: {USJ_BLUE} !important;
        font-weight: 750 !important;
        font-size: 16px !important;
        opacity: 1 !important;
        line-height: 1.35 !important;
    }}

    div[data-baseweb="select"] svg {{
        color: {USJ_BLUE} !important;
        fill: {USJ_BLUE} !important;
    }}


    div[data-baseweb="textarea"] textarea {{
        background-color: #ffffff !important;
        color: {USJ_BLUE} !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        padding: 14px 16px !important;
        min-height: 120px !important;
        line-height: 1.5 !important;
    }}

    .stSelectbox,
    .stTextArea,
    .stTextInput {{
        margin-bottom: 12px !important;
        overflow: visible !important;
    }}

    label {{
        color: {USJ_BLUE} !important;
        font-weight: 800 !important;
        font-size: 16px !important;
    }}

    .identity-card {{
        background:#ffffff;
        border: 1px solid #DDE5F0;
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 10px 28px rgba(27,42,65,0.06);
        min-height: 112px;
    }}

    .identity-label {{
        color:#6B7688;
        font-size: 0.84rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 10px;
    }}

    .identity-value {{
        color:{USJ_TEXT};
        font-size: 1.35rem;
        font-weight: 750;
        line-height: 1.2;
    }}

    .section-card {{
        background:#ffffff;
        border:1px solid #DDE5F0;
        border-radius:20px;
        padding:20px 22px;
        margin: 18px 0;
        box-shadow: 0 12px 32px rgba(27,42,65,0.07);
    }}

    .blue {{ border-top: 5px solid {USJ_BLUE}; }}
    .red {{ border-top: 5px solid {USJ_RED}; }}
    .gold {{ border-top: 5px solid {USJ_GOLD}; }}

    .step-title {{
        color:{USJ_BLUE};
        font-weight: 820;
        font-size: 1.18rem;
        margin-bottom: 8px;
    }}

    .step-help {{
        color:#5D697A;
        font-size:0.94rem;
    }}

    .card {{
        background:#ffffff;
        border:1px solid #DDE5F0;
        border-radius:16px;
        padding:16px 18px;
        margin-bottom:12px;
        box-shadow:0 8px 22px rgba(27,42,65,0.06);
    }}

    .blue-card {{ border-left:6px solid {USJ_BLUE}; }}
    .red-card {{ border-left:6px solid {USJ_RED}; }}
    .gold-card {{ border-left:6px solid {USJ_GOLD}; }}

    .pill {{
        display:inline-block;
        padding:8px 12px;
        margin:4px 5px 4px 0;
        border-radius:999px;
        background:#EAF2F8;
        color:{USJ_BLUE};
        font-weight:750;
        font-size:14px;
    }}

    .pill-red {{ background:#F8EDEF; color:{USJ_RED}; }}
    .pill-green {{ background:#E9F7EF; color:#146C43; }}
    .pill-final {{ background:#FFF8DF; color:{USJ_BLUE}; border:1px solid #E6D58D; }}

    .visual-column {{
        background: #ffffff;
        border: 1px solid #DDE5F0;
        border-radius: 18px;
        padding: 14px;
        box-shadow: 0 10px 28px rgba(27,42,65,0.06);
        margin-bottom: 10px;
    }}

    .visual-column-title {{
        font-size: 1.08rem;
        font-weight: 400;
        color: #001F5B;
        margin-bottom: 10px;
        padding-bottom: 6px;
        border-bottom: 1px solid #DDE5F0;
    }}

    .visual-employee {{ border-top: 5px solid #001F5B; }}
    .visual-director {{ border-top: 5px solid #8B1538; }}
    .visual-final {{ border-top: 5px solid #C9A227; }}

    .priority-card {{
        border-radius: 16px;
        padding: 10px 12px;
        margin-bottom: 8px;
        border: 1px solid #DDE5F0;
    }}

    .employee-card {{
        background: #EAF2F8;
        border-left: 6px solid #001F5B;
    }}

    .director-card {{
        background: #F8EDEF;
        border-left: 6px solid #8B1538;
    }}

    .final-card {{
        background: #FFF8DF;
        border-left: 6px solid #C9A227;
    }}

    .priority-rank {{
        font-size: 0.78rem;
        font-weight: 400;
        color: #5D697A;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 5px;
    }}

    .priority-theme {{
        font-size: 0.98rem;
        font-weight: 400;
        color: #001F5B;
        line-height: 1.35;
    }}

    .priority-badge {{
        margin-top: 8px;
        display: inline-block;
        padding: 5px 9px;
        border-radius: 999px;
        background: #ffffff;
        color: #735C00;
        font-size: 0.76rem;
        font-weight: 500;
        border: 1px solid #E6D58D;
    }}

    div.stButton > button {{
        border-radius:12px;
        background:{USJ_BLUE};
        color:white;
        border:0;
        font-weight:500;
        min-height: 46px;
    }}

    div.stButton > button:hover {{
        background:#123E7C;
        color:white;
        border:0;
    }}

    @media (max-width: 760px) {{
        .platform-header {{
            padding: 14px 16px;
            gap: 10px;
        }}

        .logo-side {{
            width: 90px;
        }}

        .platform-logo {{
            max-height: 58px;
            max-width: 88px;
        }}

        .header-title {{
            font-size: 1.05rem;
        }}

        .header-subtitle {{
            font-size: 0.78rem;
        }}

        .hero-title {{
            font-size: 1.55rem;
        }}
    }}
    
    .admin-action-button {{
        width: 100%;
        min-height: 50px;
        background: #001F5B;
        color: #ffffff;
        border: 0;
        border-radius: 12px;
        padding: 13px 18px;
        font-weight: 400;
        font-size: 15px;
        cursor: pointer;
        box-shadow: 0 6px 16px rgba(0,31,91,0.16);
    }}

    .admin-action-button:hover {{
        background: #123E7C;
        color: #ffffff;
    }}

    div[data-testid="stDownloadButton"] > button {{
        width: 100% !important;
        min-height: 50px !important;
        background: #001F5B !important;
        color: #ffffff !important;
        border: 0 !important;
        border-radius: 12px !important;
        padding: 13px 18px !important;
        font-weight: 400 !important;
        font-size: 15px !important;
        box-shadow: 0 6px 16px rgba(0,31,91,0.16) !important;
    }}

    div[data-testid="stDownloadButton"] > button:hover {{
        background: #123E7C !important;
        color: #ffffff !important;
        border: 0 !important;
    }}

    @media print {{
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        button,
        .admin-action-button {{
            display: none !important;
        }}

        .main-hero {{
            box-shadow: none !important;
            border-radius: 0 !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}
    }}

    
    div[data-testid="stDownloadButton"] > button {{
        width: 100% !important;
        min-height: 50px !important;
        height: 50px !important;
        background: #001F5B !important;
        color: #ffffff !important;
        border: 0 !important;
        border-radius: 12px !important;
        padding: 13px 18px !important;
        font-weight: 400 !important;
        font-size: 15px !important;
        line-height: 1.2 !important;
        box-shadow: 0 6px 16px rgba(0,31,91,0.16) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    div[data-testid="stDownloadButton"] > button:hover {{
        background: #123E7C !important;
        color: #ffffff !important;
        border: 0 !important;
    }}

    @media print {{
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        .main-hero,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr {{
            display: none !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        .card.blue-card {{
            page-break-before: always !important;
            break-before: page !important;
            margin-top: 0 !important;
        }}

        .card.blue-card:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .visual-column {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            box-shadow: none !important;
        }}

        .priority-card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}

        h3 {{
            page-break-after: avoid !important;
        }}

        body {{
            background: white !important;
        }}
    }}

    
    .employee-grid-print {{
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 16px;
        align-items: start;
    }}

    .employee-print-page {{
        margin-bottom: 26px;
        page-break-inside: avoid;
        break-inside: avoid;
    }}

    .employee-main-card {{
        margin-bottom: 12px;
    }}

    .employee-summary-card {{
        margin-bottom: 14px;
    }}

    .empty-choice {{
        color: #6B7688;
        font-weight: 600;
        padding: 8px 0;
    }}

    @media print {{
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        .no-print,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr {{
            display: none !important;
        }}

        .platform-header {{
            display: flex !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
        }}

        .main-hero {{
            box-shadow: none !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        body,
        .stApp {{
            background: white !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 92vh !important;
            box-sizing: border-box !important;
            padding-top: 8px !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print {{
            display: grid !important;
            grid-template-columns: 1fr 1fr 1fr !important;
            gap: 12px !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}

        .visual-column,
        .priority-card,
        .card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            box-shadow: none !important;
        }}

        .visual-column {{
            min-height: auto !important;
        }}

        .priority-card {{
            margin-bottom: 7px !important;
        }}

        .employee-main-card,
        .employee-summary-card {{
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        h1, h2, h3 {{
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}
    }}

    
    @media print {{
        .no-print,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr {{
            display: none !important;
        }}

        .platform-header {{
            display: flex !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 92vh !important;
            box-sizing: border-box !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print,
        .visual-column,
        .priority-card,
        .card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}
    }}

    
    /* FINAL PRINT FIX */
    @media print {{
        .no-print,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr {{
            display: none !important;
        }}

        .platform-header {{
            display: flex !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .main-hero {{
            display: block !important;
            box-shadow: none !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        body,
        .stApp {{
            background: white !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 90vh !important;
            box-sizing: border-box !important;
            padding-top: 8px !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print {{
            display: grid !important;
            grid-template-columns: 1fr 1fr 1fr !important;
            gap: 12px !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}

        .visual-column,
        .priority-card,
        .card,
        .employee-main-card,
        .employee-summary-card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            box-shadow: none !important;
        }}

        h1, h2, h3 {{
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}
    }}

    
    /* FINAL PDF PRINT HEADER FIX */
    @media print {{
        .platform-header {{
            display: flex !important;
            visibility: visible !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            border-radius: 12px !important;
            margin-bottom: 16px !important;
            padding: 12px 18px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .platform-logo {{
            display: block !important;
            visibility: visible !important;
            max-height: 68px !important;
            max-width: 145px !important;
        }}

        .header-title,
        .header-subtitle {{
            display: block !important;
            visibility: visible !important;
        }}

        .no-print,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr,
        label,
        div[data-baseweb="select"],
        .stSelectbox {{
            display: none !important;
            visibility: hidden !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        body,
        .stApp {{
            background: white !important;
        }}

        .main-hero {{
            box-shadow: none !important;
            margin-bottom: 14px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 90vh !important;
            box-sizing: border-box !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print,
        .visual-column,
        .priority-card,
        .card,
        .employee-main-card,
        .employee-summary-card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            box-shadow: none !important;
        }}
    }}

    </style>
    """, unsafe_allow_html=True)


def render_platform_header():
    cfp_logo = image_to_base64(CFP_LOGO_PATH)
    usj_logo = image_to_base64(USJ_LOGO_PATH)

    cfp_html = (
        f"<img src='data:image/png;base64,{cfp_logo}' class='platform-logo cfp-logo'>"
        if cfp_logo else
        "<div class='logo-placeholder'>CFP</div>"
    )

    usj_html = (
        f"<img src='data:image/png;base64,{usj_logo}' class='platform-logo usj-logo'>"
        if usj_logo else
        "<div class='logo-placeholder'>USJ</div>"
    )

    st.markdown(f"""
    <div class="platform-header">
        <div class="logo-side left-logo">{cfp_html}</div>
        <div class="header-center">
            <div class="header-title">Centre de Formation Professionnelle</div>
            <div class="header-subtitle">Training Needs Assessment - TNA 2026</div>
        </div>
        <div class="logo-side right-logo">{usj_html}</div>
    </div>
    """, unsafe_allow_html=True)


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            respondent_code TEXT,
            role TEXT,
            name TEXT,
            faculty TEXT,
            institution TEXT,
            department TEXT,
            data_json TEXT,
            submitted_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS admin_theme_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT UNIQUE,
            employee_ranked_json TEXT,
            director_ranked_json TEXT,
            updated_by TEXT,
            updated_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS custom_users (
            code TEXT PRIMARY KEY,
            role TEXT,
            name TEXT,
            poste TEXT,
            faculty TEXT,
            institution TEXT,
            department TEXT,
            director_code TEXT,
            created_by TEXT,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()



def load_custom_users():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT code, role, name, poste, faculty, institution, department, director_code
        FROM custom_users
    """).fetchall()
    conn.close()

    users = {}

    for code, role, name, poste, faculty, institution, department, director_code in rows:
        users[code] = {
            "role": role,
            "name": name,
            "poste": poste or "",
            "faculty": faculty or "",
            "institution": institution or "USJ",
            "department": department or "",
            "director_code": director_code or ""
        }

    return users


def get_all_users():
    users = DEMO_USERS.copy()
    users.update(load_custom_users())
    return users


def get_user_by_code(code):
    code = str(code).strip().upper()

    if code in DEMO_USERS:
        return DEMO_USERS[code]

    custom_users = load_custom_users()
    return custom_users.get(code)


def custom_user_exists(code):
    code = str(code).strip().upper()

    if code in DEMO_USERS:
        return True

    conn = sqlite3.connect(DB_NAME)
    row = conn.execute(
        "SELECT code FROM custom_users WHERE code = ?",
        (code,)
    ).fetchone()
    conn.close()

    return row is not None


def add_custom_employee(code, name, poste, faculty, institution, department, director_code):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO custom_users (
            code, role, name, poste, faculty, institution, department, director_code, created_by, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(code).strip().upper(),
        "psg",
        str(name).strip(),
        str(poste).strip(),
        str(faculty).strip(),
        str(institution).strip() or "USJ",
        str(department).strip(),
        str(director_code).strip().upper(),
        st.session_state.get("code", ""),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()



def get_removed_employee_codes_for_director(director_code):
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT employee_code
        FROM director_employee_exclusions
        WHERE director_code = ?
    """, (str(director_code).strip().upper(),)).fetchall()
    conn.close()

    return {row[0] for row in rows}


def remove_employee_from_director(director_code, employee_code):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT OR IGNORE INTO director_employee_exclusions (
            director_code,
            employee_code,
            removed_by,
            removed_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        str(director_code).strip().upper(),
        str(employee_code).strip().upper(),
        st.session_state.get("code", ""),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def save_response(user, data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO responses (
            respondent_code, role, name, faculty, institution, department, data_json, submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        st.session_state["code"],
        user["role"],
        user["name"],
        user["faculty"],
        user["institution"],
        user["department"],
        json.dumps(data, ensure_ascii=False),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()




def load_responses():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT respondent_code, role, name, faculty, institution, department, data_json, submitted_at
        FROM responses
        ORDER BY submitted_at DESC
    """).fetchall()
    conn.close()

    current_codes = {
        str(code).strip().upper()
        for code, user in get_all_users().items()
        if user.get("role") in ["psg", "director"]
    }

    records = []

    for row in rows:
        code, role, name, faculty, institution, department, data_json, submitted_at = row
        code = str(code).strip().upper()

        # Ignore old trial/demo responses still stored in SQLite, without deleting any real data.
        if code not in current_codes:
            continue

        try:
            data = json.loads(data_json)
        except Exception:
            data = {}

        records.append({
            "Code": code,
            "Profil": role,
            "Nom": name,
            "Faculté": faculty,
            "Institution": institution,
            "Date": submitted_at,
            "Données": data
        })

    return pd.DataFrame(records)



def save_admin_theme_override(employee_code, employee_ranked, director_ranked):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO admin_theme_overrides (
            employee_code,
            employee_ranked_json,
            director_ranked_json,
            updated_by,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(employee_code) DO UPDATE SET
            employee_ranked_json = excluded.employee_ranked_json,
            director_ranked_json = excluded.director_ranked_json,
            updated_by = excluded.updated_by,
            updated_at = excluded.updated_at
    """, (
        employee_code,
        json.dumps(employee_ranked, ensure_ascii=False),
        json.dumps(director_ranked, ensure_ascii=False),
        st.session_state.get("code", "ADMIN"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def load_admin_theme_overrides():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT employee_code, employee_ranked_json, director_ranked_json, updated_by, updated_at
        FROM admin_theme_overrides
    """).fetchall()
    conn.close()

    overrides = {}

    for employee_code, employee_json, director_json, updated_by, updated_at in rows:
        try:
            employee_ranked = json.loads(employee_json or "[]")
        except Exception:
            employee_ranked = []

        try:
            director_ranked = json.loads(director_json or "[]")
        except Exception:
            director_ranked = []

        overrides[employee_code] = {
            "employee_ranked": employee_ranked,
            "director_ranked": director_ranked,
            "updated_by": updated_by,
            "updated_at": updated_at
        }

    return overrides


def get_employees_for_director(director_code):
    employees = []
    all_users = get_all_users()
    removed_codes = get_removed_employee_codes_for_director(director_code)

    for code, info in all_users.items():
        if (
            info.get("role") == "psg"
            and info.get("director_code") == director_code
            and code not in removed_codes
        ):
            emp = info.copy()
            emp["code"] = code
            emp["is_custom"] = code not in DEMO_USERS
            employees.append(emp)

    employees = sorted(
        employees,
        key=lambda x: (
            1 if x.get("is_custom") else 0,
            x.get("code", "")
        )
    )

    return employees


def latest_by_code(df, code):
    if df.empty:
        return None

    subset = df[df["Code"] == code].sort_values("Date", ascending=False)

    if subset.empty:
        return None

    return subset.iloc[0].to_dict()


def unique_ranked_select(label, options, key_prefix):
    st.markdown(f"**{label}**")

    c1, c2, c3 = st.columns(3)

    with c1:
        p1 = st.selectbox("Priorité 1", [""] + options, key=f"{key_prefix}_p1")

    with c2:
        remaining2 = [x for x in options if x != p1]
        p2 = st.selectbox("Priorité 2", [""] + remaining2, key=f"{key_prefix}_p2")

    with c3:
        remaining3 = [x for x in options if x not in [p1, p2]]
        p3 = st.selectbox("Priorité 3", [""] + remaining3, key=f"{key_prefix}_p3")

    return [x for x in [p1, p2, p3] if x]


def ranked_select_with_defaults(label, options, key_prefix, defaults=None):
    defaults = defaults or []
    defaults = [x for x in defaults if x in options]

    p1_default = defaults[0] if len(defaults) > 0 else ""
    p2_default = defaults[1] if len(defaults) > 1 else ""
    p3_default = defaults[2] if len(defaults) > 2 else ""

    st.markdown(f"**{label}**")

    c1, c2, c3 = st.columns(3)

    with c1:
        options_1 = [""] + options
        p1 = st.selectbox(
            "Priorité 1",
            options_1,
            index=options_1.index(p1_default) if p1_default in options_1 else 0,
            key=f"{key_prefix}_p1"
        )

    with c2:
        remaining_2 = [x for x in options if x != p1]
        options_2 = [""] + remaining_2
        p2 = st.selectbox(
            "Priorité 2",
            options_2,
            index=options_2.index(p2_default) if p2_default in options_2 else 0,
            key=f"{key_prefix}_p2"
        )

    with c3:
        remaining_3 = [x for x in options if x not in [p1, p2]]
        options_3 = [""] + remaining_3
        p3 = st.selectbox(
            "Priorité 3",
            options_3,
            index=options_3.index(p3_default) if p3_default in options_3 else 0,
            key=f"{key_prefix}_p3"
        )

    return [x for x in [p1, p2, p3] if x]


def calculate_final_themes(employee_ranked, director_ranked):
    """
    Final selection method:
    1. Common themes are always selected first.
    2. If there are 3 common themes, final = the 3 common themes.
    3. If there are 2 common themes, add 1 extra theme from the director.
    4. If there is 1 common theme, add 2 extra themes from the director.
    5. If there is no common theme, select 2 themes from the director and 1 theme from the employee.
    6. Final list always contains maximum 3 themes.
    """

    employee_ranked = employee_ranked or []
    director_ranked = director_ranked or []

    final = []
    matched = []

    employee_set = set(employee_ranked)
    director_set = set(director_ranked)

    common_themes = [
        theme for theme in employee_ranked
        if theme in director_set
    ]

    def add_theme(theme, is_common=False):
        if theme and theme not in final and len(final) < 3:
            final.append(theme)
            if is_common and theme not in matched:
                matched.append(theme)

    # 1. Add common themes first
    for theme in common_themes:
        add_theme(theme, is_common=True)

    # 2. Count how many non-common themes are needed
    remaining_slots = 3 - len(final)

    # Case A: 3 common themes
    if remaining_slots <= 0:
        return matched[:3], final[:3]

    # Case B: 2 common themes, director chooses 1 extra
    # Case C: 1 common theme, director chooses 2 extra
    # Case D: 0 common themes, director chooses 2 and employee chooses 1
    director_slots = min(2, remaining_slots)

    if len(common_themes) == 2:
        director_slots = 1

    elif len(common_themes) == 1:
        director_slots = 2

    elif len(common_themes) == 0:
        director_slots = 2

    # 3. Add director choices first
    added_director = 0

    for theme in director_ranked:
        if len(final) >= 3:
            break

        if theme not in common_themes and added_director < director_slots:
            before_count = len(final)
            add_theme(theme, is_common=False)

            if len(final) > before_count:
                added_director += 1

    # 4. Add employee choice only if needed
    for theme in employee_ranked:
        if len(final) >= 3:
            break

        if theme not in common_themes:
            add_theme(theme, is_common=False)

    # 5. Emergency fallback if still incomplete
    for theme in director_ranked + employee_ranked:
        if len(final) >= 3:
            break

        add_theme(theme, is_common=theme in employee_set and theme in director_set)

    return matched[:3], final[:3]


def render_theme_pills(themes, css_class="pill"):
    if not themes:
        st.caption("Aucun thème sélectionné.")
        return

    html = "".join([
        f"<span class='{css_class}'>{i}. {theme}</span>"
        for i, theme in enumerate(themes, start=1)
    ])

    st.markdown(html, unsafe_allow_html=True)


def render_form_hero(profile_label, title, objective):
    st.markdown(f"""
    <div class="main-hero">
        <div class="hero-kicker">TNA 2026 | {profile_label}</div>
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{objective}</div>
    </div>
    """, unsafe_allow_html=True)


def render_identity_cards(user):
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="identity-card">
            <div class="identity-label">Nom</div>
            <div class="identity-value">{user['name']}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="identity-card">
            <div class="identity-label">Poste</div>
            <div class="identity-value">{user.get('poste', '')}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="identity-card">
            <div class="identity-label">Faculté / Institution</div>
            <div class="identity-value">{user.get('institution', user.get('faculty', ''))}</div>
        </div>
        """, unsafe_allow_html=True)

def render_ranked_section_header(title, help_text, color_class="blue"):
    st.markdown(f"""
    <div class="section-card {color_class}">
        <div class="step-title">{title}</div>
        <div class="step-help">{help_text}</div>
    </div>
    """, unsafe_allow_html=True)

def submit_login_code():
    st.session_state["enter_login"] = True

def login_page():
    st.markdown("""
    <div class="main-hero">
        <div class="hero-kicker">TNA 2026</div>
        <div class="hero-title">Plateforme d’analyse des besoins en formation</div>
        <div class="hero-subtitle">Accès sécurisé par code au questionnaire PSG, au questionnaire Doyens / Directeurs et au tableau de bord administrateur.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        code = st.text_input(
            "Identifiant reçu par email",
            type="default",
            placeholder="",
            key="access_code",
            on_change=submit_login_code
        )


        enter_form = st.button(
            "Accéder au questionnaire",
            use_container_width=True
        ) or st.session_state.pop("enter_login", False)

        if enter_form:
            cleaned_code = code.strip().upper()

            user_info = get_user_by_code(cleaned_code)

            if user_info:
                st.session_state["logged_in"] = True
                st.session_state["code"] = cleaned_code
                st.session_state["user"] = user_info
                st.rerun()
            else:
                st.error("Code non reconnu.")

        st.caption("Utilisez l’identifiant reçu par email.")

def load_latest_response_for_code(code):
    conn = sqlite3.connect(DB_NAME)
    row = conn.execute("""
        SELECT data_json
        FROM responses
        WHERE respondent_code = ?
        ORDER BY submitted_at DESC
        LIMIT 1
    """, (str(code).strip().upper(),)).fetchone()
    conn.close()

    if not row:
        return {}

    try:
        return json.loads(row[0])
    except Exception:
        return {}
    
def render_psg_form(user):
    render_form_hero(
        "Personnel de soutien et de gestion",
        "Questionnaire d’analyse des besoins en formation - PSG",
        "Ce court questionnaire nous aide à comprendre vos besoins en formation. Les résultats seront utilisés pour concevoir des programmes de formation qui soutiennent votre travail, améliorent vos compétences et favorisent votre développement professionnel.<br><br><b>Il vous faudra environ 5 à 10 minutes pour le compléter. Vos réponses resteront confidentielles.</b>"
    )

    render_identity_cards(user)

    saved_data = load_latest_response_for_code(st.session_state["code"])
    saved_ranked = saved_data.get("ranked_themes", [])
    saved_other = saved_data.get("other_themes", "")

    st.markdown("<br>", unsafe_allow_html=True)

    render_ranked_section_header(
        "Classement des thèmes prioritaires",
        "Veuillez choisir exactement 3 thèmes, dans l’ordre d’importance. La priorité 1 correspond au besoin le plus important.",
        "blue"
    )

    ranked_themes = ranked_select_with_defaults(
        "Vos 3 thèmes de formation prioritaires :",
        PSG_THEMES,
        "psg_ranked",
        saved_ranked
    )

    other_themes = st.text_area(
        "Autre(s) thème(s) ou sujet(s) de formation proposés",
        value=saved_other,
        key="psg_other",
        placeholder="Indiquez ici un thème non présent dans la liste, si nécessaire."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Soumettre mes réponses", use_container_width=True):
        if len(ranked_themes) != 3:
            st.warning("Veuillez sélectionner exactement 3 thèmes classés par ordre de priorité.")
            return

        data = {
            "ranked_themes": ranked_themes,
            "selected_themes": ranked_themes,
            "other_themes": other_themes,
            "director_code": user.get("director_code", "")
        }

        save_response(user, data)
        st.success("Vos réponses ont été enregistrées avec succès.")


def render_director_form(user):
    render_form_hero(
        "Doyens et Directeurs",
        "Questionnaire d’analyse des besoins en formation - Doyens et Directeurs",
        "Ce questionnaire vise à identifier vos besoins en formation en tant que leader ainsi que les besoins de développement de vos employés. Les résultats nous aideront à concevoir des programmes de formation qui soutiennent le leadership, améliorent la performance des équipes et s’alignent sur les objectifs de l’université.<br><br><b>Il vous faudra environ 10 minutes pour le compléter. Vos réponses resteront confidentielles.</b>"
    )

    render_identity_cards(user)

    st.markdown("<br>", unsafe_allow_html=True)

    render_ranked_section_header(
        "A. Vos besoins de formation en tant que leader",
        "Veuillez choisir au moins 1 thématique, dans l’ordre d’importance pour votre rôle de direction.",
        "red"
    )

    leader_ranked = unique_ranked_select(
        "Vos 3 thématiques prioritaires :",
        DD_LEADER_THEMES,
        "leader_ranked"
    )

    leader_other = st.text_area(
        "Autre(s) thème(s) proposés pour vous-même",
        key="leader_other",
        placeholder="Indiquez ici un thème de leadership non présent dans la liste, si nécessaire."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    employees = get_employees_for_director(st.session_state["code"])

    render_ranked_section_header(
        "B. Besoins de formation de vos employés",
        f"{len(employees)} employé(s) lié(s) à votre compte. Pour chaque employé, vous pouvez classer jusqu’à 3 thèmes prioritaires.",
        "gold"
    )

    employee_training_needs = []
    director_visible_df = load_responses()

    for emp in employees:
        with st.expander(f"{emp['name']}", expanded=True):
            info_col, remove_col = st.columns([6, 1])

            with info_col:
                st.markdown(
                    f"<span class='pill'>Code : {emp['code']}</span>",
                    unsafe_allow_html=True
                )

            with remove_col:
                if st.button(
                    "Retirer",
                    key=f"remove_employee_{emp['code']}",
                    use_container_width=True
                ):
                    remove_employee_from_director(
                        st.session_state["code"],
                        emp["code"]
                    )
                    st.success(f"{emp['name']} a été retiré de votre liste.")
                    st.rerun()

            emp_response = latest_by_code(director_visible_df, emp["code"])

            if emp_response:
                emp_data = emp_response["Données"]
                employee_submitted_themes = emp_data.get(
                    "ranked_themes",
                    emp_data.get("selected_themes", [])
                )
                employee_other_themes = emp_data.get("other_themes", "")

                st.markdown("**Réponses déjà soumises par l’employé :**")
                render_theme_pills(employee_submitted_themes, "pill")

                if employee_other_themes:
                    st.markdown(f"""
                    <div class='card blue-card'>
                        <b>Autre(s) thème(s) proposé(s) par l’employé :</b><br>
                        {employee_other_themes}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Cet employé n’a pas encore soumis ses réponses.")

            emp_ranked = unique_ranked_select(
                f"Classement des 3 thèmes prioritaires pour {emp['name']} :",
                PSG_THEMES,
                f"director_emp_{emp['code']}"
            )

            emp_other = st.text_area(
                f"Autre(s) besoin(s) spécifique(s) pour {emp['name']}",
                key=f"other_{emp['code']}",
                placeholder="Indiquez ici un besoin particulier, si nécessaire."
            )

            employee_training_needs.append({
                "employee_code": emp["code"],
                "employee_name": emp["name"],
                "employee_department": "",
                "ranked_themes_by_director": emp_ranked,
                "selected_themes": emp_ranked,
                "other_themes": emp_other
            })

    
    with st.expander("+ Ajouter un employé", expanded=False):
        new_emp_code = st.text_input(
            "Code de l’employé",
            key="new_emp_code",
            placeholder="Exemple : PSG026"
        )

        new_emp_name = st.text_input(
            "Nom de l’employé",
            key="new_emp_name"
        )

        new_emp_poste = st.text_input(
            "Poste",
            key="new_emp_poste"
        )

        if st.button("Ajouter cet employé", use_container_width=True):
            cleaned_new_code = new_emp_code.strip().upper()

            if not cleaned_new_code or not new_emp_name.strip():
                st.warning("Veuillez saisir au minimum le code et le nom.")
            elif custom_user_exists(cleaned_new_code):
                st.warning("Ce code existe déjà. Veuillez utiliser un autre code.")
            else:
                add_custom_employee(
                    code=cleaned_new_code,
                    name=new_emp_name,
                    poste=new_emp_poste,
                    faculty=user.get("faculty", ""),
                    institution=user.get("institution", "USJ"),
                    department="",
                    director_code=st.session_state["code"]
                )

                st.success(
                    f"Employé ajouté avec le code {cleaned_new_code}. "
                    "Il peut maintenant accéder à sa page avec ce code."
                )
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Soumettre mes réponses", use_container_width=True):
        if len(leader_ranked) != 3:
            st.warning("Veuillez sélectionner exactement 3 thèmes pour vous-même.")
            return


        data = {
            "leader_ranked_themes": leader_ranked,
            "leader_selected_themes": leader_ranked,
            "leader_other_themes": leader_other,
            "employees_training_needs": employee_training_needs
        }

        save_response(user, data)
        st.success("Vos réponses ont été enregistrées avec succès.")


def render_employee_visual_cards(employee_name, employee_code, employee_department, employee_ranked, director_ranked, final_themes, matched):
    def priority_card(css_class, rank_label, theme, badge=None):
        badge_html = ""
        if badge:
            badge_html = f"<div class='priority-badge'>{badge}</div>"

        return (
            f"<div class='priority-card {css_class}'>"
            f"<div class='priority-rank'>{rank_label}</div>"
            f"<div class='priority-theme'>{theme}</div>"
            f"{badge_html}"
            f"</div>"
        )

    employee_cards = "".join([
        priority_card("employee-card", f"Priorité {i}", theme)
        for i, theme in enumerate(employee_ranked, start=1)
    ])

    director_cards = "".join([
        priority_card("director-card", f"Priorité {i}", theme)
        for i, theme in enumerate(director_ranked, start=1)
    ])

    final_cards = "".join([
        priority_card(
            "final-card",
            f"Priorité finale {i}",
            theme,
            "Thème commun" if theme in matched else "Décision / complément"
        )
        for i, theme in enumerate(final_themes, start=1)
    ])

    if not employee_cards:
        employee_cards = "<div class='empty-choice'>Aucun choix employé.</div>"

    if not director_cards:
        director_cards = "<div class='empty-choice'>Aucun choix directeur.</div>"

    if not final_cards:
        final_cards = "<div class='empty-choice'>Aucun thème final.</div>"

    html = (
        "<section class='employee-print-page'>"
        "<div class='card blue-card employee-main-card'>"
        f"<h3 style='margin-top:0;'>{employee_name}</h3>"
        f"<span class='pill'>Code : {employee_code}</span>"
        "</div>"
        "<div class='card gold-card employee-summary-card'>"
        "<h3 style='margin-top:0; color:#001F5B;'>Synthèse visuelle</h3>"
        "<div style='color:#5D697A; font-weight:600;'>"
        "Comparaison des priorités classées par l’employé, par le Doyen / Directeur, puis sélection finale proposée."
        "</div>"
        "</div>"
        "<div class='employee-grid-print'>"
        "<div class='visual-column visual-employee'>"
        "<div class='visual-column-title'>Choix de l’employé</div>"
        f"{employee_cards}"
        "</div>"
        "<div class='visual-column visual-director'>"
        "<div class='visual-column-title'>Choix du Doyen / Directeur</div>"
        f"{director_cards}"
        "</div>"
        "<div class='visual-column visual-final'>"
        "<div class='visual-column-title'>Thèmes finaux proposés</div>"
        f"{final_cards}"
        "</div>"
        "</div>"
        "</section>"
    )

    st.markdown(html, unsafe_allow_html=True)


def build_admin_flat_exports(df, overrides):
    respondent_rows = []
    theme_rows = []
    final_rows = []

    for _, row in df.iterrows():
        respondent_rows.append({
            "Code": row["Code"],
            "Profil": row["Profil"],
            "Nom": row["Nom"],
            "Faculté": row["Faculté"],
            "Institution": row["Institution"],
            "Département": "",
            "Date": row["Date"]
        })

        data = row["Données"]

        if row["Profil"] == "psg":
            themes = data.get("ranked_themes", data.get("selected_themes", []))
            for i, theme in enumerate(themes, start=1):
                theme_rows.append({
                    "Code": row["Code"],
                    "Nom": row["Nom"],
                    "Profil": "PSG",
                    "Faculté": row["Faculté"],
                    "Département": "",
                    "Source": "Choix employé",
                    "Priorité": i,
                    "Thème": theme
                })

        elif row["Profil"] == "director":
            leader_themes = data.get("leader_ranked_themes", data.get("leader_selected_themes", []))
            for i, theme in enumerate(leader_themes, start=1):
                theme_rows.append({
                    "Code": row["Code"],
                    "Nom": row["Nom"],
                    "Profil": "Doyen / Directeur",
                    "Faculté": row["Faculté"],
                    "Département": "",
                    "Source": "Choix leader",
                    "Priorité": i,
                    "Thème": theme
                })

            for emp in data.get("employees_training_needs", []):
                director_themes = emp.get("ranked_themes_by_director", emp.get("selected_themes", []))
                for i, theme in enumerate(director_themes, start=1):
                    theme_rows.append({
                        "Code": emp.get("employee_code", ""),
                        "Nom": emp.get("employee_name", ""),
                        "Profil": "PSG",
                        "Faculté": row["Faculté"],
                        "Département": "",
                        "Source": "Choix directeur pour employé",
                        "Priorité": i,
                        "Thème": theme
                    })

    for code, user in get_all_users().items():
        if user.get("role") != "psg":
            continue

        employee_response = latest_by_code(df, code)
        director_code = user.get("director_code", "")
        director_response = latest_by_code(df, director_code)

        employee_original = []
        if employee_response:
            employee_original = employee_response["Données"].get(
                "ranked_themes",
                employee_response["Données"].get("selected_themes", [])
            )

        director_original = []
        if director_response:
            for item in director_response["Données"].get("employees_training_needs", []):
                if item.get("employee_code") == code:
                    director_original = item.get(
                        "ranked_themes_by_director",
                        item.get("selected_themes", [])
                    )

        employee_ranked = overrides.get(code, {}).get("employee_ranked", employee_original)
        director_ranked = overrides.get(code, {}).get("director_ranked", director_original)

        matched, final = calculate_final_themes(employee_ranked, director_ranked)

        for i, theme in enumerate(final, start=1):
            final_rows.append({
                "Employee code": code,
                "Employee name": user.get("name", ""),
                "Director code": director_code,
                "Faculty": user.get("faculty", ""),
                "Department": "",
                "Final priority": i,
                "Final theme": theme,
                "Decision type": "Thème commun" if theme in matched else "Décision / complément selon priorité"
            })

    return (
        pd.DataFrame(respondent_rows),
        pd.DataFrame(theme_rows),
        pd.DataFrame(final_rows)
    )

def build_theme_frequency_excel_report(df):
    detail_rows = []

    for _, row in df.iterrows():
        data = row["Données"]

        if row["Profil"] == "psg":
            themes = data.get("ranked_themes", data.get("selected_themes", []))

            for priority, theme in enumerate(themes, start=1):
                detail_rows.append({
                    "Thème": theme,
                    "Source": "Employé",
                    "Priorité": priority,
                    "Code répondant": row["Code"],
                    "Nom": row["Nom"],
                    "Profil": "PSG",
                    "Faculté": row["Faculté"],
                    "Institution": row["Institution"],
                    "Département": "",
                    "Date": row["Date"]
                })

        elif row["Profil"] == "director":
            leader_themes = data.get("leader_ranked_themes", data.get("leader_selected_themes", []))

            for priority, theme in enumerate(leader_themes, start=1):
                detail_rows.append({
                    "Thème": theme,
                    "Source": "Doyen / Directeur pour lui-même",
                    "Priorité": priority,
                    "Code répondant": row["Code"],
                    "Nom": row["Nom"],
                    "Profil": "Doyen / Directeur",
                    "Faculté": row["Faculté"],
                    "Institution": row["Institution"],
                    "Département": "",
                    "Date": row["Date"]
                })

            for emp in data.get("employees_training_needs", []):
                director_themes = emp.get("ranked_themes_by_director", emp.get("selected_themes", []))

                for priority, theme in enumerate(director_themes, start=1):
                    detail_rows.append({
                        "Thème": theme,
                        "Source": "Doyen / Directeur pour employé",
                        "Priorité": priority,
                        "Code répondant": emp.get("employee_code", ""),
                        "Nom": emp.get("employee_name", ""),
                        "Profil": "PSG évalué par Doyen / Directeur",
                        "Faculté": row["Faculté"],
                        "Institution": row["Institution"],
                        "Département": "",
                        "Date": row["Date"]
                    })

    details_df = pd.DataFrame(detail_rows)

    if details_df.empty:
        summary_df = pd.DataFrame(columns=[
            "Thème",
            "Sélections employés",
            "Sélections Doyens / Directeurs pour eux-mêmes",
            "Sélections Doyens / Directeurs pour employés",
            "Total sélections Doyens / Directeurs",
            "Total général"
        ])
    else:
        summary_df = (
            details_df
            .pivot_table(
                index="Thème",
                columns="Source",
                values="Code répondant",
                aggfunc="count",
                fill_value=0
            )
            .reset_index()
        )

        for col in [
            "Employé",
            "Doyen / Directeur pour lui-même",
            "Doyen / Directeur pour employé"
        ]:
            if col not in summary_df.columns:
                summary_df[col] = 0

        summary_df["Total sélections Doyens / Directeurs"] = (
            summary_df["Doyen / Directeur pour lui-même"]
            + summary_df["Doyen / Directeur pour employé"]
        )

        summary_df["Total général"] = (
            summary_df["Employé"]
            + summary_df["Total sélections Doyens / Directeurs"]
        )

        summary_df = summary_df.rename(columns={
            "Employé": "Sélections employés",
            "Doyen / Directeur pour lui-même": "Sélections Doyens / Directeurs pour eux-mêmes",
            "Doyen / Directeur pour employé": "Sélections Doyens / Directeurs pour employés"
        })

        summary_df = summary_df[
            [
                "Thème",
                "Sélections employés",
                "Sélections Doyens / Directeurs pour eux-mêmes",
                "Sélections Doyens / Directeurs pour employés",
                "Total sélections Doyens / Directeurs",
                "Total général"
            ]
        ].sort_values("Total général", ascending=False)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Synthèse par thème", index=False)
        details_df.to_excel(writer, sheet_name="Détails par thème", index=False)

        if not details_df.empty:
            for theme in sorted(details_df["Thème"].dropna().unique()):
                safe_sheet_name = (
                    theme[:31]
                    .replace("/", "-")
                    .replace("\\", "-")
                    .replace("*", "")
                    .replace("?", "")
                    .replace(":", "")
                    .replace("[", "")
                    .replace("]", "")
                )

                theme_df = details_df[details_df["Thème"] == theme].copy()
                theme_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)

    output.seek(0)
    return output
    
def build_theme_frequency_dataframe(df):
    rows = []

    for _, row in df.iterrows():
        data = row["Données"]

        if row["Profil"] == "psg":
            themes = data.get("ranked_themes", data.get("selected_themes", []))

            for priority, theme in enumerate(themes, start=1):
                rows.append({
                    "Thème": theme,
                    "Source": "Employés",
                    "Priorité": priority,
                    "Nom": row["Nom"],
                    "Faculté": row["Faculté"],
                    "Département": ""
                })

        elif row["Profil"] == "director":
            leader_themes = data.get("leader_ranked_themes", data.get("leader_selected_themes", []))

            for priority, theme in enumerate(leader_themes, start=1):
                rows.append({
                    "Thème": theme,
                    "Source": "Doyens / Directeurs",
                    "Priorité": priority,
                    "Nom": row["Nom"],
                    "Faculté": row["Faculté"],
                    "Département": ""
                })

            for emp in data.get("employees_training_needs", []):
                director_themes = emp.get(
                    "ranked_themes_by_director",
                    emp.get("selected_themes", [])
                )

                for priority, theme in enumerate(director_themes, start=1):
                    rows.append({
                        "Thème": theme,
                        "Source": "Doyens / Directeurs pour employés",
                        "Priorité": priority,
                        "Nom": emp.get("employee_name", ""),
                        "Faculté": row["Faculté"],
                        "Département": ""
                    })

    return pd.DataFrame(rows)


def render_theme_visualization_dashboard(df):
    st.markdown("### Visualisation générale des thèmes")

    if st.button(
        "Générer les figures des thèmes sélectionnés",
        use_container_width=True,
        key="generate_theme_visuals_main"
    ):
        st.session_state["show_theme_visuals"] = True

    if not st.session_state.get("show_theme_visuals", False):
        return

    theme_visual_df = build_theme_frequency_dataframe(df)

    if theme_visual_df.empty:
        st.info("Aucune donnée disponible pour générer les figures.")
        return

    employee_related_df = theme_visual_df[
        theme_visual_df["Source"].isin([
            "Employés",
            "Doyens / Directeurs pour employés"
        ])
    ]

    employee_related_counts = (
        employee_related_df
        .groupby(["Thème", "Source"])
        .size()
        .reset_index(name="Fréquence")
    )

    st.markdown("#### 1. Thèmes liés aux employés")

    if employee_related_counts.empty:
        st.info("Aucune donnée disponible pour les thèmes liés aux employés.")
    else:
        fig_employee_related = px.bar(
            employee_related_counts,
            x="Fréquence",
            y="Thème",
            color="Source",
            orientation="h",
            barmode="group",
            text="Fréquence",
            title="Thèmes liés aux employés : choix des employés et choix des Doyens / Directeurs"
        )

        fig_employee_related.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        fig_employee_related.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=850,
            margin=dict(l=260, r=80, t=70, b=40),
            legend_title_text="Source"
        )

        st.plotly_chart(fig_employee_related, use_container_width=True)

    director_only_df = theme_visual_df[
        theme_visual_df["Source"] == "Doyens / Directeurs"
    ]

    director_only_counts = (
        director_only_df
        .groupby("Thème")
        .size()
        .reset_index(name="Fréquence")
        .sort_values("Fréquence", ascending=False)
    )

    st.markdown("#### 2. Thèmes liés uniquement aux Doyens / Directeurs")

    if director_only_counts.empty:
        st.info("Aucune donnée disponible pour les thèmes liés aux Doyens / Directeurs.")
    else:
        fig_director_only = px.bar(
            director_only_counts,
            x="Fréquence",
            y="Thème",
            orientation="h",
            text="Fréquence",
            title="Thèmes sélectionnés par les Doyens / Directeurs pour eux-mêmes"
        )

        fig_director_only.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        fig_director_only.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=600,
            margin=dict(l=260, r=80, t=70, b=40),
            showlegend=False
        )

        st.plotly_chart(fig_director_only, use_container_width=True)

    report_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Visualisation des thèmes TNA 2026</title>
    </head>
    <body>
        <h1>Visualisation générale des thèmes sélectionnés - TNA 2026</h1>
        <h2>1. Thèmes liés aux employés</h2>
        {fig_employee_related.to_html(full_html=False, include_plotlyjs="cdn") if not employee_related_counts.empty else "<p>Aucune donnée.</p>"}
        <br><br>
        <h2>2. Thèmes liés uniquement aux Doyens / Directeurs</h2>
        {fig_director_only.to_html(full_html=False, include_plotlyjs=False) if not director_only_counts.empty else "<p>Aucune donnée.</p>"}
    </body>
    </html>
    """

    d1, d2 = st.columns(2)

    with d1:
        st.download_button(
            "Télécharger la visualisation HTML",
            data=report_html.encode("utf-8"),
            file_name="tna_visualisation_themes.html",
            mime="text/html",
            use_container_width=True
        )

    with d2:
        st.download_button(
            "Télécharger les données de visualisation CSV",
            theme_visual_df.to_csv(index=False).encode("utf-8-sig"),
            "tna_visualisation_themes.csv",
            "text/csv",
            use_container_width=True
        )



def build_director_report_html(selected_director, df, overrides):
    all_users = get_all_users()
    director_user = all_users[selected_director]
    director_response = latest_by_code(df, selected_director)
    employees = get_employees_for_director(selected_director)

    leader_themes = []
    if director_response:
        leader_themes = director_response["Données"].get(
            "leader_ranked_themes",
            director_response["Données"].get("leader_selected_themes", [])
        )

    director_emp_map = {}
    if director_response:
        for item in director_response["Données"].get("employees_training_needs", []):
            director_emp_map[item.get("employee_code")] = item

    rows_html = ""

    for emp in employees:
        emp_response = latest_by_code(df, emp["code"])

        employee_original = []
        if emp_response:
            employee_original = emp_response["Données"].get(
                "ranked_themes",
                emp_response["Données"].get("selected_themes", [])
            )

        director_original = []
        if emp["code"] in director_emp_map:
            director_original = director_emp_map[emp["code"]].get(
                "ranked_themes_by_director",
                director_emp_map[emp["code"]].get("selected_themes", [])
            )

        employee_ranked = overrides.get(emp["code"], {}).get("employee_ranked", employee_original)
        director_ranked = overrides.get(emp["code"], {}).get("director_ranked", director_original)

        matched, final = calculate_final_themes(employee_ranked, director_ranked)

        employee_list = "".join([f"<li><b>P{i}</b> - {theme}</li>" for i, theme in enumerate(employee_ranked, start=1)])
        director_list = "".join([f"<li><b>P{i}</b> - {theme}</li>" for i, theme in enumerate(director_ranked, start=1)])
        final_list = "".join([
            f"<li><b>P{i}</b> - {theme} <span>{'Thème commun' if theme in matched else 'Décision / complément'}</span></li>"
            for i, theme in enumerate(final, start=1)
        ])

        rows_html += f"""
        <section class="employee-card">
            <h2>{emp['name']}</h2>
            <p class="meta">Code : {emp['code']}</p>
            <div class="three-cols">
                <div class="box employee">
                    <h3>Choix de l’employé</h3>
                    <ol>{employee_list}</ol>
                </div>
                <div class="box director">
                    <h3>Choix du Doyen / Directeur</h3>
                    <ol>{director_list}</ol>
                </div>
                <div class="box final">
                    <h3>Thèmes finaux proposés</h3>
                    <ol>{final_list}</ol>
                </div>
            </div>
        </section>
        """

    leader_html = "".join([f"<li><b>P{i}</b> - {theme}</li>" for i, theme in enumerate(leader_themes, start=1)])

    cfp_logo = image_to_base64(CFP_LOGO_PATH)
    usj_logo = image_to_base64(USJ_LOGO_PATH)

    cfp_logo_src = f"data:image/png;base64,{cfp_logo}" if cfp_logo else ""
    usj_logo_src = f"data:image/png;base64,{usj_logo}" if usj_logo else ""

    director_affiliation = director_user.get("institution", director_user.get("faculty", ""))

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Rapport TNA 2026 - {director_user['name']}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                color: #1B2A41;
                background: #ffffff;
                margin: 28px;
            }}

            .report-logo-header {{
                background: #ffffff;
                border: 1px solid #DDE5F0;
                border-radius: 18px;
                padding: 14px 22px;
                margin-bottom: 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}

            .report-logo {{
                max-height: 70px;
                max-width: 170px;
            }}

            .report-center {{
                text-align: center;
                color: #001F5B;
            }}

            .report-center-title {{
                font-size: 26px;
                font-weight: 500;
            }}

            .report-center-subtitle {{
                font-size: 16px;
                color: #5D697A;
                font-weight: 600;
            }}

            .header {{
                border-bottom: 4px solid #001F5B;
                padding-bottom: 16px;
                margin-bottom: 24px;
            }}
            .kicker {{
                color: #8B1538;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 12px;
            }}
            h1 {{
                color: #001F5B;
                margin: 8px 0 6px 0;
                font-size: 28px;
            }}
            h2 {{
                color: #001F5B;
                margin-bottom: 6px;
            }}
            h3 {{
                color: #001F5B;
                margin-top: 0;
            }}
            .meta {{
                color: #5D697A;
                font-weight: 600;
            }}
            .leader {{
                background: #F8EDEF;
                border-left: 6px solid #8B1538;
                border-radius: 12px;
                padding: 14px 18px;
                margin-bottom: 22px;
            }}
            .employee-card {{
                page-break-before: always;
                page-break-inside: avoid;
                break-before: page;
                break-inside: avoid;
                border: 1px solid #DDE5F0;
                border-radius: 14px;
                padding: 16px;
                margin-bottom: 18px;
                box-sizing: border-box;
            }}
            .employee-card:first-of-type {{
                page-break-before: auto;
                break-before: auto;
            }}
            .three-cols {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 14px;
            }}
            .box {{
                border-radius: 12px;
                padding: 12px;
                min-height: 120px;
            }}
            .employee {{
                background: #EAF2F8;
                border-left: 5px solid #001F5B;
            }}
            .director {{
                background: #F8EDEF;
                border-left: 5px solid #8B1538;
            }}
            .final {{
                background: #FFF8DF;
                border-left: 5px solid #C9A227;
            }}
            li {{
                margin-bottom: 8px;
                line-height: 1.35;
            }}
            span {{
                display: inline-block;
                margin-left: 6px;
                font-size: 11px;
                background: #ffffff;
                border: 1px solid #C9A227;
                border-radius: 999px;
                padding: 3px 7px;
                color: #735C00;
                font-weight: 700;
            }}

            .print-btn {{
                width: 100%;
                background: #001F5B;
                color: white;
                border: 0;
                border-radius: 12px;
                padding: 14px;
                font-size: 14px;
                cursor: pointer;
                margin-bottom: 20px;
                box-shadow: 0 6px 16px rgba(0,31,91,0.16);
            }}

            @media print {{
                body {{
                    margin: 14mm;
                }}

                .print-btn {{
                    display: none;
                }}

                .employee-card {{
                    page-break-before: always;
                    break-before: page;
                    page-break-inside: avoid;
                    break-inside: avoid;
                    min-height: 90vh;
                }}
                .employee-card:first-of-type {{
                    page-break-before: auto;
                    break-before: auto;
                }}
            }}
        </style>
    </head>

    <body>

        <button class="print-btn" onclick="window.print()">
            Enregistrer en PDF
        </button>

        <div class="report-logo-header">
            <img src="{cfp_logo_src}" class="report-logo">
            <div class="report-center">
                <div class="report-center-title">Centre de Formation Professionnelle</div>
                <div class="report-center-subtitle">Training Needs Assessment - TNA 2026</div>
            </div>
            <img src="{usj_logo_src}" class="report-logo">
        </div>

        <div class="header">
            <div class="kicker">Training Needs Assessment - TNA 2026</div>
            <h1>Rapport par Doyen / Directeur</h1>
            <p class="meta">{director_user['name']} | {director_affiliation}</p>
            <p class="meta">Date de génération : {datetime.now().strftime("%Y-%m-%d")}</p>
        </div>

        <section class="leader">
            <h2>Besoins de formation sélectionnés pour le leader</h2>
            <ol>{leader_html}</ol>
        </section>

        {rows_html}
    </body>
    </html>
    """

    return html



def render_save_pdf_button():
    components.html(
        """
        <style>
            html, body {
                margin: 0;
                padding: 0;
                background: transparent;
                font-family: inherit;
            }
            .pdf-button {
                width: 100%;
                min-height: 50px;
                background: #001F5B;
                color: #ffffff;
                border: 0;
                border-radius: 12px;
                padding: 13px 18px;
                font-weight: 400;
                font-size: 14px;
                line-height: 50px;
                cursor: pointer;
                box-shadow: 0 6px 16px rgba(0,31,91,0.16);
                display: block;
                text-align: center;
                padding: 0;
                box-sizing: border-box;
            }
            .pdf-button:hover {
                background: #123E7C;
            }
        
    @media print {{
        .no-print,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr {{
            display: none !important;
        }}

        .platform-header {{
            display: flex !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 92vh !important;
            box-sizing: border-box !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print,
        .visual-column,
        .priority-card,
        .card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}
    }}

    
    /* FINAL PRINT FIX */
    @media print {{
        .no-print,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr {{
            display: none !important;
        }}

        .platform-header {{
            display: flex !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .main-hero {{
            display: block !important;
            box-shadow: none !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        body,
        .stApp {{
            background: white !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 90vh !important;
            box-sizing: border-box !important;
            padding-top: 8px !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print {{
            display: grid !important;
            grid-template-columns: 1fr 1fr 1fr !important;
            gap: 12px !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}

        .visual-column,
        .priority-card,
        .card,
        .employee-main-card,
        .employee-summary-card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            box-shadow: none !important;
        }}

        h1, h2, h3 {{
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}
    }}

    
    /* FINAL PDF PRINT HEADER FIX */
    @media print {{
        .platform-header {{
            display: flex !important;
            visibility: visible !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            border-radius: 12px !important;
            margin-bottom: 16px !important;
            padding: 12px 18px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .platform-logo {{
            display: block !important;
            visibility: visible !important;
            max-height: 68px !important;
            max-width: 145px !important;
        }}

        .header-title,
        .header-subtitle {{
            display: block !important;
            visibility: visible !important;
        }}

        .no-print,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr,
        label,
        div[data-baseweb="select"],
        .stSelectbox {{
            display: none !important;
            visibility: hidden !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        body,
        .stApp {{
            background: white !important;
        }}

        .main-hero {{
            box-shadow: none !important;
            margin-bottom: 14px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 90vh !important;
            box-sizing: border-box !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print,
        .visual-column,
        .priority-card,
        .card,
        .employee-main-card,
        .employee-summary-card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            box-shadow: none !important;
        }}
    }}

    </style>
        <button class="pdf-button" onclick="window.parent.print();">
            Enregistrer le rapport en PDF
        </button>
        """,
        height=64
    )


def render_admin_dashboard():
    st.markdown("""
    <div class="main-hero">
        <div class="hero-kicker">Administration | TNA 2026</div>
        <div class="hero-title">Tableau de bord administrateur</div>
        <div class="hero-subtitle">Vue interactive des besoins de formation avec comparaison employé-directeur et modification administrative des priorités.</div>
    </div>
    """, unsafe_allow_html=True)

    df = load_responses()
    overrides = load_admin_theme_overrides()
    all_users = get_all_users()

    valid_user_codes = {
        str(code).strip().upper()
        for code, user in all_users.items()
        if user.get("role") in ["psg", "director"]
    }

    if not df.empty:
        df = df[df["Code"].astype(str).str.upper().isin(valid_user_codes)].copy()

    with st.sidebar:
        st.header("Filtres administrateur")

        view = st.selectbox(
            "Vue à afficher",
            [
                "Synthèse directeur-employés",
                "Modifier les priorités",
                "Visualisation des thèmes",
                "Réponses PSG",
                "Réponses Doyens / Directeurs",
                "Base de données"
            ]
        )

        profiles = ["Tous"]
        if not df.empty:
            profiles += sorted(df["Profil"].dropna().unique().tolist())
        selected_profile = st.selectbox("Profil", profiles)

        faculties = ["Toutes"]
        if not df.empty:
            faculties += sorted(df["Faculté"].dropna().unique().tolist())
        selected_faculty = st.selectbox("Faculté / institution", faculties)

    filtered = df.copy()

    if not filtered.empty and selected_profile != "Tous":
        filtered = filtered[filtered["Profil"] == selected_profile]

    if not filtered.empty and selected_faculty != "Toutes":
        filtered = filtered[filtered["Faculté"] == selected_faculty]

    total_psg_users = len([
        code for code, user in all_users.items()
        if user.get("role") == "psg"
    ])

    total_director_users = len([
        code for code, user in all_users.items()
        if user.get("role") == "director"
    ])

    unique_respondents = 0 if filtered.empty else filtered["Code"].nunique()
    unique_psg_responses = 0 if filtered.empty else filtered[filtered["Profil"] == "psg"]["Code"].nunique()
    unique_director_responses = 0 if filtered.empty else filtered[filtered["Profil"] == "director"]["Code"].nunique()

    valid_user_codes = set(DEMO_USERS.keys())
    
    filtered_valid = filtered[filtered["Code"].isin(valid_user_codes)]
    
    total_psg_users = len([
        code for code, user in DEMO_USERS.items()
        if user.get("role") == "psg"
    ])
    
    total_director_users = len([
        code for code, user in DEMO_USERS.items()
        if user.get("role") == "director"
    ])
    
    unique_psg_responses = filtered_valid[
        filtered_valid["Profil"] == "psg"
    ]["Code"].nunique()
    
    unique_director_responses = filtered_valid[
        filtered_valid["Profil"] == "director"
    ]["Code"].nunique()
    
    unique_respondents = unique_psg_responses + unique_director_responses
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Répondants uniques", unique_respondents)
    k2.metric("PSG", f"{unique_psg_responses} / {total_psg_users}")
    k3.metric("Doyens / Directeurs", f"{unique_director_responses} / {total_director_users}")

    if df.empty:
        st.info("Aucune réponse enregistrée pour le moment.")
        return

    st.divider()

    respondents_export, themes_export, final_export = build_admin_flat_exports(df, overrides)
    theme_frequency_excel = build_theme_frequency_excel_report(df)

    with st.expander("Exports administrateur", expanded=False):
        ex1, ex2, ex3, ex4 = st.columns(4)

        with ex1:
            st.download_button(
                "Télécharger les répondants CSV",
                respondents_export.to_csv(index=False).encode("utf-8-sig"),
                "tna_repondants.csv",
                "text/csv",
                use_container_width=True
            )

        with ex2:
            st.download_button(
                "Télécharger les thèmes CSV",
                themes_export.to_csv(index=False).encode("utf-8-sig"),
                "tna_themes_selectionnes.csv",
                "text/csv",
                use_container_width=True
            )

        with ex3:
            st.download_button(
                "Télécharger les thèmes finaux CSV",
                final_export.to_csv(index=False).encode("utf-8-sig"),
                "tna_themes_finaux.csv",
                "text/csv",
                use_container_width=True
            )

        with ex4:
            st.download_button(
                "Rapport Excel par thème",
                data=theme_frequency_excel,
                file_name="tna_rapport_frequence_par_theme.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    render_theme_visualization_dashboard(df)

    if view == "Visualisation des thèmes":
        return

    st.divider()

    directors = [
        code for code, user in all_users.items()
        if user.get("role") == "director"
    ]

    director_labels = {
        code: f"{all_users[code]['name']} | {all_users[code].get('institution', all_users[code].get('faculty', ''))}"
        for code in directors
    }

    if view in ["Synthèse directeur-employés", "Modifier les priorités"]:
        selected_director = st.selectbox(
            "Sélectionner un Doyen / Directeur",
            directors,
            format_func=lambda x: director_labels[x],
            key=f"admin_director_selector_{view}"
        )

        director_user = all_users[selected_director]
        director_response = latest_by_code(df, selected_director)

        report_html = build_director_report_html(selected_director, df, overrides)
        safe_report_html = json.dumps(report_html)

        components.html(
            f"""
            <button onclick="openReport()" style="
                width:100%;
                min-height:50px;
                background:#001F5B;
                color:white;
                border:0;
                border-radius:12px;
                font-size:14px;
                font-weight:400;
                cursor:pointer;
                box-shadow:0 6px 16px rgba(0,31,91,0.16);
            ">
                Ouvrir le rapport du directeur
            </button>

            <script>
            function openReport() {{
                const html = {safe_report_html};
                const win = window.open("", "_blank");
                win.document.open();
                win.document.write(html);
                win.document.close();
            }}
            </script>
            """,
            height=64
        )

        st.markdown("### 1. Besoins sélectionnés par le Doyen / Directeur pour lui-même")

        st.markdown(f"""
        <div class='card red-card'>
            <h3 style='margin-top:0;'>{director_user['name']}</h3>
            <span class='pill pill-red'>{director_user.get('institution', director_user.get('faculty', ''))}</span>
        </div>
        """, unsafe_allow_html=True)

        if director_response:
            leader_themes = director_response["Données"].get(
                "leader_ranked_themes",
                director_response["Données"].get("leader_selected_themes", [])
            )
            render_theme_pills(leader_themes, "pill pill-red")
        else:
            st.warning("Ce directeur n’a pas encore soumis ses réponses.")

        st.divider()

        employees = get_employees_for_director(selected_director)

        director_emp_map = {}

        if director_response:
            for item in director_response["Données"].get("employees_training_needs", []):
                director_emp_map[item.get("employee_code")] = item

        if view == "Modifier les priorités":
            st.markdown("### Modification administrative des priorités par employé")
            st.info(
                "L’administrateur peut modifier les thèmes classés par l’employé "
                "et les thèmes classés par le Doyen / Directeur. Ces modifications sont enregistrées "
                "dans une table administrative séparée."
            )
        else:
            st.markdown("### 2. Analyse visuelle par employé")

        for emp in employees:
            emp_response = latest_by_code(df, emp["code"])

            employee_original = []

            if emp_response:
                employee_original = emp_response["Données"].get(
                    "ranked_themes",
                    emp_response["Données"].get("selected_themes", [])
                )

            director_original = []

            if emp["code"] in director_emp_map:
                director_original = director_emp_map[emp["code"]].get(
                    "ranked_themes_by_director",
                    director_emp_map[emp["code"]].get("selected_themes", [])
                )

            employee_ranked = overrides.get(emp["code"], {}).get("employee_ranked", employee_original)
            director_ranked = overrides.get(emp["code"], {}).get("director_ranked", director_original)

            matched, final = calculate_final_themes(employee_ranked, director_ranked)

            if emp["code"] in overrides:
                st.caption(f"Priorités modifiées par l’administrateur le {overrides[emp['code']]['updated_at']}.")

            if view == "Modifier les priorités":
                c1, c2 = st.columns(2)

                with c1:
                    admin_employee_ranked = ranked_select_with_defaults(
                        "Modifier le classement de l’employé",
                        PSG_THEMES,
                        f"admin_edit_employee_{emp['code']}",
                        employee_ranked
                    )

                with c2:
                    admin_director_ranked = ranked_select_with_defaults(
                        "Modifier le classement du Doyen / Directeur",
                        PSG_THEMES,
                        f"admin_edit_director_{emp['code']}",
                        director_ranked
                    )

                if st.button(
                    f"Enregistrer les priorités modifiées pour {emp['name']}",
                    key=f"save_override_{emp['code']}",
                    use_container_width=True
                ):
                    if len(admin_employee_ranked) > 3 or len(admin_director_ranked) > 3:
                        st.warning("Veuillez sélectionner au maximum 3 thèmes pour chaque classement.")
                    else:
                        save_admin_theme_override(emp["code"], admin_employee_ranked, admin_director_ranked)
                        st.success(f"Priorités modifiées pour {emp['name']}.")
                        st.rerun()

                st.divider()

            else:
                render_employee_visual_cards(
                    emp["name"],
                    emp["code"],
                    "",
                    employee_ranked,
                    director_ranked,
                    final,
                    matched
                )
                st.divider()

    elif view == "Réponses PSG":
        st.markdown("### Réponses PSG")

        psg_df = filtered[filtered["Profil"] == "psg"].copy()

        if psg_df.empty:
            st.info("Aucune réponse PSG dans les filtres sélectionnés.")
        else:
            for _, row in psg_df.iterrows():
                themes = row["Données"].get("ranked_themes", row["Données"].get("selected_themes", []))

                st.markdown(f"""
                <div class='card blue-card'>
                    <b>{row['Nom']}</b><br>
                    {row['Faculté']} | {row['Date']}
                </div>
                """, unsafe_allow_html=True)

                render_theme_pills(themes, "pill")

    elif view == "Réponses Doyens / Directeurs":
        st.markdown("### Réponses Doyens / Directeurs")

        dd_df = filtered[filtered["Profil"] == "director"].copy()

        if dd_df.empty:
            st.info("Aucune réponse Doyen / Directeur dans les filtres sélectionnés.")
        else:
            for _, row in dd_df.iterrows():
                data = row["Données"]

                st.markdown(f"""
                <div class='card red-card'>
                    <b>{row['Nom']}</b><br>
                    {row['Faculté']} | {row['Date']}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("**Thèmes sélectionnés pour lui-même :**")
                render_theme_pills(
                    data.get("leader_ranked_themes", data.get("leader_selected_themes", [])),
                    "pill pill-red"
                )

                st.markdown("**Thèmes sélectionnés pour les employés :**")

                for emp in data.get("employees_training_needs", []):
                    st.markdown(f"""
                    <div class='card'>
                        <b>{emp.get('employee_name')}</b>
                    </div>
                    """, unsafe_allow_html=True)

                    render_theme_pills(
                        emp.get("ranked_themes_by_director", emp.get("selected_themes", [])),
                        "pill"
                    )

    elif view == "Base de données":
        st.markdown("### Base de données filtrée")

        display_df = filtered.drop(columns=["Données"]) if not filtered.empty else pd.DataFrame()

        if "Département" in display_df.columns:
            display_df = display_df.drop(columns=["Département"])

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Télécharger CSV",
            display_df.to_csv(index=False).encode("utf-8-sig"),
            "tna_reponses.csv",
            "text/csv"
        )



def main():
    st.set_page_config(
        page_title="TNA 2026",
        page_icon="📘",
        layout="wide"
    )

    apply_style()
    init_db()
    render_platform_header()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
        return

    user = st.session_state["user"]

    if user["role"] != "admin":
        st.markdown(
            """
            <style>
            section[data-testid="stSidebar"] {
                display: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    if user["role"] == "psg":
        render_psg_form(user)

    elif user["role"] == "director":
        render_director_form(user)

    elif user["role"] == "admin":
        render_admin_dashboard()


if __name__ == "__main__":
    main()
