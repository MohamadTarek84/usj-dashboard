import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import json
from datetime import datetime
import pandas as pd
import os
import base64
import textwrap

DB_NAME = "tna_demo.db"

USJ_BLUE = "#001F5B"
USJ_RED = "#8B1538"
USJ_GOLD = "#C9A227"
USJ_TEXT = "#1B2A41"
USJ_LIGHT_BLUE = "#EAF2F8"
DEMO_DATA_VERSION = "varied_scenarios_v2"

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
    "PSG001": {"role": "psg", "name": "Nour Haddad", "faculty": "Faculté des Sciences", "institution": "USJ", "department": "Service des Études", "director_code": "DD001"},
    "PSG002": {"role": "psg", "name": "Karim Mansour", "faculty": "Faculté des Sciences", "institution": "USJ", "department": "Service des Études", "director_code": "DD001"},
    "PSG003": {"role": "psg", "name": "Maya Khoury", "faculty": "Faculté des Sciences", "institution": "USJ", "department": "Service Informatique", "director_code": "DD001"},
    "PSG004": {"role": "psg", "name": "Elias Saad", "faculty": "Faculté des Sciences", "institution": "USJ", "department": "Service Informatique", "director_code": "DD001"},
    "PSG005": {"role": "psg", "name": "Rita Nader", "faculty": "Faculté des Sciences", "institution": "USJ", "department": "Service Administratif", "director_code": "DD001"},

    "PSG006": {"role": "psg", "name": "Paul Tannous", "faculty": "Faculté de Médecine", "institution": "USJ", "department": "Secrétariat académique", "director_code": "DD002"},
    "PSG007": {"role": "psg", "name": "Nadine Abi Rached", "faculty": "Faculté de Médecine", "institution": "USJ", "department": "Laboratoire", "director_code": "DD002"},
    "PSG008": {"role": "psg", "name": "Georges Saliba", "faculty": "Faculté de Médecine", "institution": "USJ", "department": "Accueil étudiants", "director_code": "DD002"},
    "PSG009": {"role": "psg", "name": "Sarah Karam", "faculty": "Faculté de Médecine", "institution": "USJ", "department": "Coordination administrative", "director_code": "DD002"},
    "PSG010": {"role": "psg", "name": "Fadi Younes", "faculty": "Faculté de Médecine", "institution": "USJ", "department": "Support pédagogique", "director_code": "DD002"},

    "PSG011": {"role": "psg", "name": "Lina Farah", "faculty": "Faculté de Gestion et de Management", "institution": "USJ", "department": "Scolarité", "director_code": "DD003"},
    "PSG012": {"role": "psg", "name": "Marc Azar", "faculty": "Faculté de Gestion et de Management", "institution": "USJ", "department": "Relations entreprises", "director_code": "DD003"},
    "PSG013": {"role": "psg", "name": "Hala Daher", "faculty": "Faculté de Gestion et de Management", "institution": "USJ", "department": "Communication", "director_code": "DD003"},
    "PSG014": {"role": "psg", "name": "Joe Sfeir", "faculty": "Faculté de Gestion et de Management", "institution": "USJ", "department": "Administration", "director_code": "DD003"},
    "PSG015": {"role": "psg", "name": "Mona Raad", "faculty": "Faculté de Gestion et de Management", "institution": "USJ", "department": "Assurance qualité", "director_code": "DD003"},

    "PSG016": {"role": "psg", "name": "Tania Helou", "faculty": "Faculté des Lettres et des Sciences Humaines", "institution": "USJ", "department": "Bibliothèque", "director_code": "DD004"},
    "PSG017": {"role": "psg", "name": "Rami Chidiac", "faculty": "Faculté des Lettres et des Sciences Humaines", "institution": "USJ", "department": "Secrétariat", "director_code": "DD004"},
    "PSG018": {"role": "psg", "name": "Dina Aoun", "faculty": "Faculté des Lettres et des Sciences Humaines", "institution": "USJ", "department": "Vie étudiante", "director_code": "DD004"},
    "PSG019": {"role": "psg", "name": "Michel Najjar", "faculty": "Faculté des Lettres et des Sciences Humaines", "institution": "USJ", "department": "Support académique", "director_code": "DD004"},
    "PSG020": {"role": "psg", "name": "Carla Haddad", "faculty": "Faculté des Lettres et des Sciences Humaines", "institution": "USJ", "department": "Communication", "director_code": "DD004"},

    "PSG021": {"role": "psg", "name": "Sami Bassil", "faculty": "Faculté d’Ingénierie", "institution": "USJ", "department": "Laboratoires", "director_code": "DD005"},
    "PSG022": {"role": "psg", "name": "Layal Matar", "faculty": "Faculté d’Ingénierie", "institution": "USJ", "department": "Support technique", "director_code": "DD005"},
    "PSG023": {"role": "psg", "name": "Anthony Ghosn", "faculty": "Faculté d’Ingénierie", "institution": "USJ", "department": "Scolarité", "director_code": "DD005"},
    "PSG024": {"role": "psg", "name": "Mireille Daher", "faculty": "Faculté d’Ingénierie", "institution": "USJ", "department": "Coordination administrative", "director_code": "DD005"},
    "PSG025": {"role": "psg", "name": "Patrick Bou Saab", "faculty": "Faculté d’Ingénierie", "institution": "USJ", "department": "Innovation et projets", "director_code": "DD005"},

    "DD001": {"role": "director", "name": "Dr. Rami Haddad", "faculty": "Faculté des Sciences", "institution": "USJ", "department": "Direction"},
    "DD002": {"role": "director", "name": "Dr. Carla Mansour", "faculty": "Faculté de Médecine", "institution": "USJ", "department": "Direction"},
    "DD003": {"role": "director", "name": "Dr. Joseph Khoury", "faculty": "Faculté de Gestion et de Management", "institution": "USJ", "department": "Direction"},
    "DD004": {"role": "director", "name": "Dr. Nadine Farhat", "faculty": "Faculté des Lettres et des Sciences Humaines", "institution": "USJ", "department": "Direction"},
    "DD005": {"role": "director", "name": "Dr. Marc Saad", "faculty": "Faculté d’Ingénierie", "institution": "USJ", "department": "Direction"},

    "ADMIN2032": {"role": "admin", "name": "Administrateur TNA", "faculty": "USJ", "institution": "USJ", "department": "Administration Centrale"}
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
    .pill-gold {{ background:#FFF8DF; color:#735C00; }}
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
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

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


def trial_data_is_complete():
    expected_codes = set(TRIAL_PSG_RESPONSES.keys()) | set(TRIAL_DIRECTOR_RESPONSES.keys())

    conn = sqlite3.connect(DB_NAME)

    existing_codes = {
        row[0]
        for row in conn.execute("SELECT DISTINCT respondent_code FROM responses").fetchall()
    }

    version_row = conn.execute(
        "SELECT value FROM app_meta WHERE key = ?",
        ("demo_data_version",)
    ).fetchone()

    conn.close()

    version_ok = version_row is not None and version_row[0] == DEMO_DATA_VERSION

    return expected_codes.issubset(existing_codes) and version_ok


def seed_trial_data(force=False):
    if not force and trial_data_is_complete():
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM responses")
    c.execute("DELETE FROM admin_theme_overrides")

    base_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for employee_code, ranked_themes in TRIAL_PSG_RESPONSES.items():
        user = DEMO_USERS[employee_code]

        data = {
            "ranked_themes": ranked_themes,
            "selected_themes": ranked_themes,
            "other_themes": "Donnée d’essai générée automatiquement.",
            "director_code": user.get("director_code", "")
        }

        c.execute("""
            INSERT INTO responses (
                respondent_code, role, name, faculty, institution, department, data_json, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_code,
            user["role"],
            user["name"],
            user["faculty"],
            user["institution"],
            user["department"],
            json.dumps(data, ensure_ascii=False),
            base_time
        ))

    for director_code, response in TRIAL_DIRECTOR_RESPONSES.items():
        user = DEMO_USERS[director_code]

        employees_training_needs = []

        for employee_code, ranked_themes in response["employees"].items():
            emp = DEMO_USERS[employee_code]

            employees_training_needs.append({
                "employee_code": employee_code,
                "employee_name": emp["name"],
                "employee_department": emp["department"],
                "ranked_themes_by_director": ranked_themes,
                "selected_themes": ranked_themes,
                "other_themes": "Donnée d’essai générée automatiquement par le directeur."
            })

        data = {
            "leader_ranked_themes": response["leader"],
            "leader_selected_themes": response["leader"],
            "leader_other_themes": "Donnée d’essai générée automatiquement.",
            "employees_training_needs": employees_training_needs
        }

        c.execute("""
            INSERT INTO responses (
                respondent_code, role, name, faculty, institution, department, data_json, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            director_code,
            user["role"],
            user["name"],
            user["faculty"],
            user["institution"],
            user["department"],
            json.dumps(data, ensure_ascii=False),
            base_time
        ))

    c.execute("""
        INSERT INTO app_meta (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, ("demo_data_version", DEMO_DATA_VERSION))

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

    records = []

    for row in rows:
        code, role, name, faculty, institution, department, data_json, submitted_at = row

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
            "Département": department,
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

    for code, info in DEMO_USERS.items():
        if info.get("role") == "psg" and info.get("director_code") == director_code:
            emp = info.copy()
            emp["code"] = code
            employees.append(emp)

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
    1. Check common themes first, regardless of priority position.
    2. If Employee P1 and Director P1 are the same, select it automatically.
    3. If Employee P1 and Director P1 are different, select both first.
    4. If two themes are already selected from Priority 1 and Priority 2 is different,
       the next decision goes to the Director, not to the employee.
    5. Complete until 3 themes are selected.
    """
    employee_ranked = employee_ranked or []
    director_ranked = director_ranked or []

    final = []
    matched = []

    employee_set = set(employee_ranked)
    director_set = set(director_ranked)

    def add_theme(theme, is_common=False):
        if theme and theme not in final and len(final) < 3:
            final.append(theme)
            if is_common and theme not in matched:
                matched.append(theme)

    # Case A: same Priority 1.
    if len(employee_ranked) >= 1 and len(director_ranked) >= 1:
        if employee_ranked[0] == director_ranked[0]:
            add_theme(employee_ranked[0], is_common=True)
        else:
            # Case B: two different Priority 1 themes are both retained.
            add_theme(employee_ranked[0], is_common=employee_ranked[0] in director_set)
            add_theme(director_ranked[0], is_common=director_ranked[0] in employee_set)

    # Prioritize common themes appearing anywhere in both lists.
    # This preserves the idea that shared needs are stronger, even if priorities differ.
    for theme in employee_ranked:
        if len(final) >= 3:
            break
        if theme in director_set:
            add_theme(theme, is_common=True)

    # If two themes were already retained from P1 conflict, and P2 differs,
    # the next choice is the director's Priority 2.
    if len(final) == 2:
        director_p2 = director_ranked[1] if len(director_ranked) > 1 else ""
        employee_p2 = employee_ranked[1] if len(employee_ranked) > 1 else ""

        if director_p2 and director_p2 != employee_p2:
            add_theme(director_p2, is_common=director_p2 in employee_set)

    # Continue rank by rank with director priority first, then employee.
    # This respects the requested rule when arbitration is needed.
    for rank_index in range(1, 3):
        if len(final) >= 3:
            break

        director_theme = director_ranked[rank_index] if len(director_ranked) > rank_index else ""
        employee_theme = employee_ranked[rank_index] if len(employee_ranked) > rank_index else ""

        add_theme(director_theme, is_common=director_theme in employee_set)

        if len(final) >= 3:
            break

        add_theme(employee_theme, is_common=employee_theme in director_set)

    # Final fallback, still director first then employee.
    fallback_candidates = []
    for rank_index in range(3):
        if len(director_ranked) > rank_index:
            fallback_candidates.append(director_ranked[rank_index])
        if len(employee_ranked) > rank_index:
            fallback_candidates.append(employee_ranked[rank_index])

    for theme in fallback_candidates:
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
            <div class="identity-label">Faculté / Institution</div>
            <div class="identity-value">{user['faculty']}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="identity-card">
            <div class="identity-label">Département</div>
            <div class="identity-value">{user['department']}</div>
        </div>
        """, unsafe_allow_html=True)


def render_ranked_section_header(title, help_text, color_class="blue"):
    st.markdown(f"""
    <div class="section-card {color_class}">
        <div class="step-title">{title}</div>
        <div class="step-help">{help_text}</div>
    </div>
    """, unsafe_allow_html=True)


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
            "Code d’accès",
            type="default",
            placeholder="Exemple : PSG001, DD001 ou ADMIN2032",
            autocomplete="off",
            key="access_code"
        )

        if st.button("Accéder au questionnaire", use_container_width=True):
            cleaned_code = code.strip().upper()

            if cleaned_code in DEMO_USERS:
                st.session_state["logged_in"] = True
                st.session_state["code"] = cleaned_code
                st.session_state["user"] = DEMO_USERS[cleaned_code]
                st.rerun()
            else:
                st.error("Code non reconnu.")

        st.caption("Codes demo : PSG001 à PSG025, DD001 à DD005, ADMIN2032")


def render_psg_form(user):
    render_form_hero(
        "Personnel de soutien et de gestion",
        "Questionnaire d’analyse des besoins en formation - PSG",
        "Ce court questionnaire nous aide à comprendre vos besoins en formation. Les résultats seront utilisés pour concevoir des programmes de formation qui soutiennent votre travail, améliorent vos compétences et favorisent votre développement professionnel.<br><br><b>Il vous faudra environ 5 à 10 minutes pour le compléter. Vos réponses resteront confidentielles.</b>"
    )

    render_identity_cards(user)

    st.markdown("<br>", unsafe_allow_html=True)

    render_ranked_section_header(
        "Classement des thèmes prioritaires",
        "Veuillez choisir exactement 3 thèmes, dans l’ordre d’importance. La priorité 1 correspond au besoin le plus important.",
        "blue"
    )

    ranked_themes = unique_ranked_select(
        "Vos 3 thèmes de formation prioritaires :",
        PSG_THEMES,
        "psg_ranked"
    )

    other_themes = st.text_area(
        "Autre(s) thème(s) ou sujet(s) de formation proposés",
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
        "Ce questionnaire vise à identifier vos besoins en formation en tant que leader ainsi que les besoins de développement de votre département. Les résultats nous aideront à concevoir des programmes de formation qui soutiennent le leadership, améliorent la performance des équipes et s’alignent sur les objectifs de l’université.<br><br><b>Il vous faudra environ 10 minutes pour le compléter. Vos réponses resteront confidentielles.</b>"
    )

    render_identity_cards(user)

    st.markdown("<br>", unsafe_allow_html=True)

    render_ranked_section_header(
        "A. Vos besoins de formation en tant que leader",
        "Veuillez choisir exactement 3 thématiques, dans l’ordre d’importance pour votre rôle de direction.",
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
        f"{len(employees)} employé(s) lié(s) à votre compte. Pour chaque employé, veuillez classer exactement 3 thèmes prioritaires.",
        "gold"
    )

    employee_training_needs = []

    for emp in employees:
        with st.expander(f"{emp['name']} | {emp['department']}", expanded=True):
            st.markdown(
                f"<span class='pill'>Code : {emp['code']}</span><span class='pill pill-gold'>{emp['department']}</span>",
                unsafe_allow_html=True
            )

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
                "employee_department": emp["department"],
                "ranked_themes_by_director": emp_ranked,
                "selected_themes": emp_ranked,
                "other_themes": emp_other
            })

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Soumettre mes réponses", use_container_width=True):
        if len(leader_ranked) != 3:
            st.warning("Veuillez sélectionner exactement 3 thèmes pour vous-même.")
            return

        incomplete = [
            emp["employee_name"]
            for emp in employee_training_needs
            if len(emp["ranked_themes_by_director"]) != 3
        ]

        if incomplete:
            st.warning("Veuillez sélectionner exactement 3 thèmes pour chaque employé : " + ", ".join(incomplete))
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
    employee_cards = ""
    director_cards = ""
    final_cards = ""

    for i, theme in enumerate(employee_ranked, start=1):
        employee_cards += textwrap.dedent(f"""
        <div class="priority-card employee-card">
            <div class="priority-rank">Priorité {i}</div>
            <div class="priority-theme">{theme}</div>
        </div>
        """).strip()

    if not employee_ranked:
        employee_cards = "<div class='empty-choice'>Aucun choix employé.</div>"

    for i, theme in enumerate(director_ranked, start=1):
        director_cards += textwrap.dedent(f"""
        <div class="priority-card director-card">
            <div class="priority-rank">Priorité {i}</div>
            <div class="priority-theme">{theme}</div>
        </div>
        """).strip()

    if not director_ranked:
        director_cards = "<div class='empty-choice'>Aucun choix directeur.</div>"

    for i, theme in enumerate(final_themes, start=1):
        badge = "Thème commun" if theme in matched else "Décision / complément"
        final_cards += textwrap.dedent(f"""
        <div class="priority-card final-card">
            <div class="priority-rank">Priorité finale {i}</div>
            <div class="priority-theme">{theme}</div>
            <div class="priority-badge">{badge}</div>
        </div>
        """).strip()

    if not final_themes:
        final_cards = "<div class='empty-choice'>Aucun thème final.</div>"

    html = textwrap.dedent(f"""
    <section class="employee-print-page">
        <div class="card blue-card employee-main-card">
            <h3 style="margin-top:0;">{employee_name}</h3>
            <span class="pill">Code : {employee_code}</span>
            <span class="pill pill-gold">{employee_department}</span>
        </div>

        <div class="card gold-card employee-summary-card">
            <h3 style="margin-top:0; color:#001F5B;">Synthèse visuelle</h3>
            <div style="color:#5D697A; font-weight:600;">
                Comparaison des priorités classées par l’employé, par le Doyen / Directeur, puis sélection finale proposée.
            </div>
        </div>

        <div class="employee-grid-print">
            <div class="visual-column visual-employee">
                <div class="visual-column-title">Choix de l’employé</div>
                {employee_cards}
            </div>

            <div class="visual-column visual-director">
                <div class="visual-column-title">Choix du Doyen / Directeur</div>
                {director_cards}
            </div>

            <div class="visual-column visual-final">
                <div class="visual-column-title">Thèmes finaux proposés</div>
                {final_cards}
            </div>
        </div>
    </section>
    """).strip()

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
            "Département": row["Département"],
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
                    "Département": row["Département"],
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
                    "Département": row["Département"],
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
                        "Département": emp.get("employee_department", ""),
                        "Source": "Choix directeur pour employé",
                        "Priorité": i,
                        "Thème": theme
                    })

    for code, user in DEMO_USERS.items():
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
                "Department": user.get("department", ""),
                "Final priority": i,
                "Final theme": theme,
                "Decision type": "Thème commun" if theme in matched else "Décision / complément selon priorité"
            })

    return (
        pd.DataFrame(respondent_rows),
        pd.DataFrame(theme_rows),
        pd.DataFrame(final_rows)
    )


def build_director_report_html(selected_director, df, overrides):
    director_user = DEMO_USERS[selected_director]
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
            <p class="meta">Code : {emp['code']} | Département : {emp['department']}</p>
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
                min-height: 88vh;
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
            @media print {{
                body {{
                    margin: 14mm;
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

    </style>
    </head>
    <body>
        <div class="header">
            <div class="kicker">Training Needs Assessment - TNA 2026</div>
            <h1>Rapport par Doyen / Directeur</h1>
            <p class="meta">{director_user['name']} | {director_user['faculty']} | {director_user['department']}</p>
            <p class="meta">Date de génération : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
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
                font-family: "Source Sans Pro", Arial, sans-serif;
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
                font-size: 15px;
                line-height: 1.2;
                cursor: pointer;
                box-shadow: 0 6px 16px rgba(0,31,91,0.16);
                display: flex;
                align-items: center;
                justify-content: center;
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

    if df.empty:
        st.info("Aucune réponse enregistrée pour le moment.")
        return

    st.markdown("<div class='no-print' style='color:#6B7688; font-size:0.95rem; line-height:1.6;'>Données d’essai intégrées : 5 Doyens / Directeurs et 25 employés PSG. Les scénarios sont volontairement variés : plusieurs cas sans thème commun, quelques cas avec 1 thème commun, quelques cas avec 2 thèmes communs, et un cas avec 3 thèmes communs.</div>", unsafe_allow_html=True)

    with st.sidebar:
        st.header("Filtres administrateur")

        if st.button("Charger / réinitialiser les données d’essai", use_container_width=True):
            seed_trial_data(force=True)
            st.success("Données d’essai chargées.")
            st.rerun()

        view = st.selectbox(
            "Vue à afficher",
            [
                "Synthèse directeur-employés",
                "Modifier les priorités",
                "Réponses PSG",
                "Réponses Doyens / Directeurs",
                "Départements",
                "Base de données"
            ]
        )

        profiles = ["Tous"] + sorted(df["Profil"].unique().tolist())
        selected_profile = st.selectbox("Profil", profiles)

        faculties = ["Toutes"] + sorted(df["Faculté"].unique().tolist())
        selected_faculty = st.selectbox("Faculté / institution", faculties)

        departments = ["Tous"] + sorted(df["Département"].unique().tolist())
        selected_department = st.selectbox("Département", departments)

    filtered = df.copy()

    if selected_profile != "Tous":
        filtered = filtered[filtered["Profil"] == selected_profile]

    if selected_faculty != "Toutes":
        filtered = filtered[filtered["Faculté"] == selected_faculty]

    if selected_department != "Tous":
        filtered = filtered[filtered["Département"] == selected_department]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Réponses", len(filtered))
    k2.metric("PSG", len(filtered[filtered["Profil"] == "psg"]))
    k3.metric("Doyens / Directeurs", len(filtered[filtered["Profil"] == "director"]))
    k4.metric("Départements", filtered["Département"].nunique())

    st.divider()

    respondents_export, themes_export, final_export = build_admin_flat_exports(df, overrides)

    with st.expander("Exports administrateur", expanded=False):
        ex1, ex2, ex3 = st.columns(3)

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

    directors = [
        code for code, user in DEMO_USERS.items()
        if user.get("role") == "director"
    ]

    director_labels = {
        code: f"{DEMO_USERS[code]['name']} | {DEMO_USERS[code]['faculty']}"
        for code in directors
    }

    if view in ["Synthèse directeur-employés", "Modifier les priorités"]:
        selected_director = st.selectbox(
            "Sélectionner un Doyen / Directeur",
            directors,
            format_func=lambda x: director_labels[x],
            key=f"admin_director_selector_{view}"
        )

        director_user = DEMO_USERS[selected_director]
        director_response = latest_by_code(df, selected_director)

        report_html = build_director_report_html(selected_director, df, overrides)

        report_col1, report_col2 = st.columns(2)

        with report_col1:
            st.download_button(
                "Télécharger le rapport du directeur",
                report_html.encode("utf-8"),
                f"rapport_TNA_2026_{selected_director}.html",
                "text/html",
                use_container_width=True
            )

        with report_col2:
            render_save_pdf_button()

        st.markdown("### 1. Besoins sélectionnés par le Doyen / Directeur pour lui-même")

        st.markdown(f"""
        <div class='card red-card'>
            <h3 style='margin-top:0;'>{director_user['name']}</h3>
            <span class='pill pill-red'>{director_user['faculty']}</span>
            <span class='pill pill-gold'>{director_user['department']}</span>
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
                "L’administrateur peut modifier les trois thèmes classés par l’employé "
                "et les trois thèmes classés par le Doyen / Directeur. Ces modifications sont enregistrées "
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
                    if len(admin_employee_ranked) != 3 or len(admin_director_ranked) != 3:
                        st.warning("Veuillez sélectionner exactement 3 thèmes pour l’employé et 3 thèmes pour le directeur.")
                    else:
                        save_admin_theme_override(emp["code"], admin_employee_ranked, admin_director_ranked)
                        st.success(f"Priorités modifiées pour {emp['name']}.")
                        st.rerun()

                st.divider()

            else:
                render_employee_visual_cards(emp["name"], emp["code"], emp["department"], employee_ranked, director_ranked, final, matched)
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
                    {row['Faculté']} | {row['Département']} | {row['Date']}
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
                    {row['Faculté']} | {row['Département']} | {row['Date']}
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
                        <b>{emp.get('employee_name')}</b> | {emp.get('employee_department')}
                    </div>
                    """, unsafe_allow_html=True)

                    render_theme_pills(
                        emp.get("ranked_themes_by_director", emp.get("selected_themes", [])),
                        "pill"
                    )

    elif view == "Départements":
        st.markdown("### Analyse par département")

        theme_rows = []

        for _, row in filtered.iterrows():
            data = row["Données"]

            if row["Profil"] == "psg":
                for theme in data.get("ranked_themes", data.get("selected_themes", [])):
                    theme_rows.append({
                        "Département": row["Département"],
                        "Source": "PSG",
                        "Thème": theme
                    })

            elif row["Profil"] == "director":
                for emp in data.get("employees_training_needs", []):
                    for theme in emp.get("ranked_themes_by_director", emp.get("selected_themes", [])):
                        theme_rows.append({
                            "Département": emp.get("employee_department"),
                            "Source": "Directeur pour employé",
                            "Thème": theme
                        })

        if not theme_rows:
            st.info("Aucune donnée disponible.")
        else:
            theme_df = pd.DataFrame(theme_rows)

            dept = st.selectbox(
                "Choisir un département",
                sorted(theme_df["Département"].dropna().unique())
            )

            sub = theme_df[theme_df["Département"] == dept]

            counts = sub["Thème"].value_counts().reset_index()
            counts.columns = ["Thème", "Nombre"]

            st.bar_chart(counts.set_index("Thème"), use_container_width=True)
            st.dataframe(sub, use_container_width=True, hide_index=True)

    elif view == "Base de données":
        st.markdown("### Base de données filtrée")

        display_df = filtered.drop(columns=["Données"])

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
    seed_trial_data(force=False)
    render_platform_header()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
        return

    user = st.session_state["user"]

    if user["role"] == "psg":
        render_psg_form(user)

    elif user["role"] == "director":
        render_director_form(user)

    elif user["role"] == "admin":
        render_admin_dashboard()


if __name__ == "__main__":
    main()
