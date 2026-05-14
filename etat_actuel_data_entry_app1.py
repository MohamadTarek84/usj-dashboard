#!/usr/bin/env python
# coding: utf-8

import sqlite3
import json
import base64
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


APP_TITLE = "PLAN STRATÉGIQUE USJ 2032"
DB_PATH = Path("etat_actuel_responses.db")
LOGO_PATH = Path("LogoUAQ.png")
INTRO_IMAGE_PATH = Path("Intro_schema.png")

USJ_BLUE = "#001F5B"
USJ_BLUE_2 = "#1F3C88"
USJ_RED = "#8B1538"
USJ_GOLD = "#C9A227"
USJ_LIGHT_BLUE = "#EAF2F8"
USJ_TEXT = "#1B2A41"


def html_block(content):
    if hasattr(st, "html"):
        st.html(content)
    else:
        st.markdown(content, unsafe_allow_html=True)


def image_to_base64(image_path):
    if not image_path.exists():
        return None
    suffix = image_path.suffix.lower().replace(".", "")
    mime_type = "png" if suffix == "png" else suffix
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    return f"data:image/{mime_type};base64,{encoded}"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submitted_at TEXT NOT NULL,
            respondent_name TEXT,
            respondent_unit TEXT,
            respondent_email TEXT,
            data_json TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_response(metadata, data):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO responses (
            submitted_at,
            respondent_name,
            respondent_unit,
            respondent_email,
            data_json
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        metadata.get("responsable", ""),
        metadata.get("institution", ""),
        metadata.get("email", ""),
        json.dumps(data, ensure_ascii=False),
    ))
    conn.commit()
    conn.close()


def load_responses():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM responses ORDER BY id DESC", conn)
    conn.close()
    return df


def flatten_response(row):
    base = {
        "id": row["id"],
        "submitted_at": row["submitted_at"],
        "responsable": row["respondent_name"],
        "institution": row["respondent_unit"],
        "email": row["respondent_email"],
    }

    data = json.loads(row["data_json"])

    for section, values in data.items():
        if isinstance(values, dict):
            for key, value in values.items():
                if isinstance(value, list):
                    base[f"{section}_{key}"] = json.dumps(value, ensure_ascii=False)
                else:
                    base[f"{section}_{key}"] = value
        else:
            base[section] = values

    return base


def apply_usj_style():
    html_block(f"""
<style>
html, body, [class*="css"], [class*="st-"], .stApp {{
    font-family: Candara, Calibri, Arial, sans-serif !important;
    color: {USJ_TEXT};
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: Candara, Calibri, Arial, sans-serif !important;
    color: {USJ_BLUE} !important;
    font-weight: 700 !important;
}}

p, div, span, label, button, input, textarea, select {{
    font-family: Candara, Calibri, Arial, sans-serif !important;
}}

.stTextInput input, .stTextArea textarea, .stDateInput input {{
    border: 1.5px solid {USJ_BLUE_2} !important;
    border-radius: 8px !important;
    background-color: #F8FBFF !important;
    color: {USJ_TEXT} !important;
}}

.stTextArea textarea {{
    resize: vertical !important;
    overflow-y: auto !important;
}}

.stTextArea textarea:focus, .stTextInput input:focus {{
    border: 2px solid {USJ_RED} !important;
    box-shadow: 0 0 0 1px {USJ_GOLD} !important;
}}

div[data-testid="stForm"] {{
    border: 1px solid {USJ_BLUE_2};
    border-radius: 14px;
    padding: 20px;
    background-color: #FFFFFF;
}}

section[data-testid="stSidebar"] {{
    background-color: {USJ_LIGHT_BLUE};
    border-right: 4px solid {USJ_BLUE};
}}

.stButton button, .stDownloadButton button, div[data-testid="stFormSubmitButton"] button {{
    background-color: {USJ_BLUE} !important;
    color: white !important;
    border-radius: 8px !important;
    border: 1px solid {USJ_BLUE} !important;
    font-weight: 600 !important;
}}

.stButton button p, .stDownloadButton button p, div[data-testid="stFormSubmitButton"] button p {{
    color: white !important;
}}
</style>
""")


def section_header(title, description=None):
    html_block(f"""
<div style="border-left:6px solid {USJ_BLUE}; border-bottom:2px solid {USJ_GOLD}; padding:10px 14px; margin-top:20px; margin-bottom:18px; background-color:{USJ_LIGHT_BLUE}; border-radius:8px;">
    <h2 style="margin:0; color:{USJ_BLUE};">{title}</h2>
</div>
""")


def text_area(label, key, height=500, placeholder=None):
    return st.text_area(
        label,
        key=key,
        height=height,
        placeholder=placeholder
    )

def render_first_page_header():
    col_left, col_right = st.columns([2.2, 1])

    with col_left:
        html_block(f"""
<div style="padding-top:20px;">
    <h1 style="font-size:42px; margin-bottom:0px; color:{USJ_BLUE};">PLAN STRATÉGIQUE USJ 2032</h1>
    <h3 style="color:{USJ_BLUE_2}; margin-top:8px; margin-bottom:0px;">Analyse de l’état actuel et propositions</h3>
    <h5 style="margin-top:4px; color:{USJ_TEXT};">(pré-planification stratégique USJ)</h5>
</div>
""")

    with col_right:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=420)
        else:
            st.warning("LogoUAQ.png non trouvé. Placez le logo dans le même dossier que le script.")

    st.markdown("---")


def render_fixed_introduction():
    intro_image_src = image_to_base64(INTRO_IMAGE_PATH)

    image_html = ""
    if intro_image_src:
        image_html = f"""
        <div style="text-align:center; margin:18px 0;">
            <img src="{intro_image_src}" style="max-width:100%; height:auto; border-radius:8px;">
        </div>
        """

    html_block(f"""
<div style="background-color:#ffffff; padding:24px 34px; border-radius:12px; border-left:7px solid {USJ_BLUE}; border-top:2px solid {USJ_GOLD}; border-bottom:2px solid {USJ_RED}; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:25px;">
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    L’enseignement supérieur est aujourd’hui confronté à des transformations rapides, à des contraintes économiques croissantes et à une intensification de la concurrence, tant nationale qu’internationale. Les évolutions technologiques, les attentes accrues des étudiants et des parties prenantes, ainsi que les exigences renforcées en matière de qualité et de performance, imposent une réflexion stratégique à la fois rigoureuse et collective. Les universités sont ainsi appelées à réinterroger en profondeur leurs modèles académiques, organisationnels et opérationnels.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Le Plan stratégique USJ 2032 s’inscrit dans cette dynamique. Il constitue une feuille de route institutionnelle visant à traduire la mission, la vision et les valeurs de l’USJ en priorités stratégiques claires, en objectifs cohérents et en initiatives concrètes, capables de renforcer durablement son positionnement, sa résilience ainsi que son impact académique et sociétal.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    L’élaboration de ce plan stratégique se décline en plusieurs étapes (voir le schéma ci-dessous), dont la première est consacrée à l’analyse de données relatives à l’état actuel de l’Université. L’ensemble des acteurs de l’Université, ainsi que les parties prenantes, sont invités à y contribuer. Ce rapport a pour objectif de vous accompagner dans la formulation de constats partagés, des pratiques existantes et des expériences vécues, afin d’identifier les forces à consolider, les fragilités à traiter, les opportunités de développement et les risques à maîtriser à l’échelle de l’Université<sup>1</sup>.
    </p>

    {image_html}

    <p style="font-size:14px; line-height:1.45; color:{USJ_TEXT}; margin-top:8px; margin-bottom:20px;">
    <sup>1</sup> D’autres outils sont aussi mis à votre disposition pour recueillir l’opinion des parties prenantes, en particulier des questionnaires adressés aux employeurs, aux diplômés, ou aux étudiants. Ils sont joints à ce courrier. Leur utilisation est facultative.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Ce rapport vise ainsi à produire deux résultats principaux. Le premier consiste en une analyse SWOT (Strengths, Weaknesses, Opportunities, Threats) de l’Université, fondée sur la réalité vécue au sein de votre institution. Sur la base de cette analyse, vous serez amenés à proposer des priorités stratégiques ainsi que des initiatives (ou projets), toujours à l’échelle de l’Université, constituant ainsi le second résultat attendu.
    </p>

    <p style="font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:5px;">
    Le document comprend 6 parties :
    </p>

    <ol style="font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-top:5px;">
        <li>Introduction</li>
        <li>Identification des parties prenantes à consulter pour écrire le rapport</li>
        <li>Analyse interne : cette analyse mène à produire les éléments Forces et Faiblesses de l’analyse SWOT</li>
        <li>Analyse externe : cette analyse mène à produire les éléments Opportunités et Menaces de l’analyse SWOT</li>
        <li>Analyse SWOT</li>
        <li>Propositions de Priorités stratégiques et Initiatives</li>
    </ol>

    <p style="font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:5px;">
    Pour toute information supplémentaire ou support, contacter :
    </p>

    <p style="font-size:16px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:0;">
    M. Hadi Sawaya – Coordinateur de l’Unité Assurance Qualité : hadi.sawaya@usj.edu.lb<br>
    Mme Irma Majdalani – Expert qualité – Unité Assurance qualité : irma.majdalani@usj.edu.lb<br>
    Mme Nadine Riachi Haddad – Secrétaire général : secg@usj.edu.lb<br>
    Mme Ursula El Hage – Directeur du Service de l’insertion professionnelle : ursula.hage@usj.edu.lb<br>
    Mme Lina Koleilat Ghalayini – Chef de projets – Unité Assurance qualité : lina.koleilat@usj.edu.lb
    </p>
</div>
""")


def render_stakeholder_intro():
    html_block(f"""
<div style="background-color:#ffffff; padding:24px 34px; border-radius:12px; border-left:7px solid {USJ_BLUE}; border-top:2px solid {USJ_GOLD}; border-bottom:2px solid {USJ_RED}; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:25px;">
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Le rapport d’analyse des données existantes est le fruit d’une consultation menée auprès de l’ensemble des parties prenantes de l’institution. L’identification et la prise en compte de leurs attentes constituent un levier essentiel pour la réussite du processus de planification stratégique. En raison de la diversité de leurs rôles, de leurs intérêts et de leur degré d’influence, les parties prenantes apportent des perspectives complémentaires, qui enrichissent l’analyse stratégique et favorisent l’adhésion aux orientations retenues. L’analyse de leurs attentes vise à mieux comprendre leurs besoins, leurs priorités et leur niveau d’influence, afin d’éclairer les choix stratégiques de l’USJ. Cette démarche participative est essentielle pour garantir une vision partagée, réaliste et représentative de la diversité de la communauté universitaire.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:4px;">
    Il est proposé aux institutions de consulter notamment les parties prenantes suivantes : le conseil de l’institution, le conseil d’orientation stratégique, les employeurs, les étudiants, les enseignants, le PSG, les anciens, ainsi que toute autre partie jugée pertinente et engagée dans l’institution<sup>2</sup>.
    </p>

    <p style="font-size:13.5px; line-height:1.35; color:{USJ_TEXT}; margin-top:0; margin-bottom:16px;">
    <sup>2</sup> Exemple de parties prenantes en Annexe A.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    L’institution est libre d’organiser, selon les modalités qu’elle juge les plus appropriées, une ou plusieurs réunions avec les parties prenantes, ou, dans certains cas, de recourir à des questionnaires (voir la note de bas de page de l’introduction).
    </p>

    <p style="font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:0;">
    Le tableau ci-dessous doit être dûment complété.
    </p>
</div>
""")


def render_stakeholder_table():
    stakeholder_categories = [
        "Responsables institution",
        "Enseignants cadrés",
        "Enseignants non-cadrés",
        "PSG",
        "Étudiants",
        "Anciens",
        "Employeurs / Conseil d’orientation stratégique",
    ]

    stakeholder_rows = []

    col0, col1, col2, col3 = st.columns([1.4, 1.6, 1.6, 1.8])

    with col0:
        html_block(f"""
<div style="background:{USJ_BLUE}; color:white; padding:10px 12px; height:40px; display:flex; align-items:center; font-weight:700; border-radius:6px;">
    Parties prenantes consultées
</div>
""")

    with col1:
        html_block(f"""
<div style="background:{USJ_BLUE}; color:white; padding:10px 12px; height:40px; display:flex; align-items:center; font-weight:700; border-radius:6px;">
    Nom
</div>
""")

    with col2:
        html_block(f"""
<div style="background:{USJ_BLUE}; color:white; padding:10px 12px; height:40px; display:flex; align-items:center; font-weight:700; border-radius:6px;">
    Poste
</div>
""")

    with col3:
        html_block(f"""
<div style="background:{USJ_BLUE}; color:white; padding:10px 12px; height:40px; display:flex; align-items:center; font-weight:700; border-radius:6px;">
    Organisme d’affiliation
</div>
""")

    for category in stakeholder_categories:
        col0, col1, col2, col3 = st.columns([1.4, 1.6, 1.6, 1.8])

        with col0:
            html_block(f"""
<div style="background:{USJ_LIGHT_BLUE}; border-left:5px solid {USJ_BLUE}; padding:8px 10px; height:38px; display:flex; align-items:center; font-weight:700; color:{USJ_BLUE}; border-radius:6px;">
    {category}
</div>
""")

        with col1:
            nom = st.text_input("Nom", key=f"{category}_nom", label_visibility="collapsed")

        with col2:
            poste = st.text_input("Poste", key=f"{category}_poste", label_visibility="collapsed")

        with col3:
            organisme = st.text_input(
                "Organisme d’affiliation",
                key=f"{category}_organisme",
                label_visibility="collapsed"
            )

        if any([nom.strip(), poste.strip(), organisme.strip()]):
            stakeholder_rows.append({
                "categorie": category,
                "nom": nom,
                "poste": poste,
                "organisme_affiliation": organisme,
            })

    st.session_state.setdefault("n_autres_rows", 1)

    for i in range(1, st.session_state.n_autres_rows + 1):
        col0, col1, col2, col3 = st.columns([1.4, 1.6, 1.6, 1.8])

        with col0:
            html_block(f"""
<div style="background:#FFF7E6; border-left:5px solid {USJ_RED}; padding:8px 10px; height:38px; display:flex; align-items:center; font-weight:700; color:{USJ_RED}; border-radius:6px;">
    Autres
</div>
""")

        with col1:
            autre_nom = st.text_input("Nom", key=f"autre_nom_{i}", label_visibility="collapsed")

        with col2:
            autre_poste = st.text_input("Poste", key=f"autre_poste_{i}", label_visibility="collapsed")

        with col3:
            autre_org = st.text_input(
                "Organisme d’affiliation",
                key=f"autre_org_{i}",
                label_visibility="collapsed"
            )

        if any([autre_nom.strip(), autre_poste.strip(), autre_org.strip()]):
            stakeholder_rows.append({
                "categorie": "Autres",
                "nom": autre_nom,
                "poste": autre_poste,
                "organisme_affiliation": autre_org,
            })

    add_autre = st.form_submit_button("Ajouter une ligne Autres")

    if add_autre:
        st.session_state.n_autres_rows += 1
        st.rerun()

    return stakeholder_rows

def render_internal_intro():
    html_block(f"""
<div style="background-color:#ffffff; padding:24px 34px; border-radius:12px; border-left:7px solid {USJ_BLUE}; border-top:2px solid {USJ_GOLD}; border-bottom:2px solid {USJ_RED}; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:25px;">
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    L’analyse interne vise à apprécier dans quelle mesure l’USJ dispose des ressources nécessaires pour soutenir sa mission et mettre en œuvre ses orientations stratégiques. Elle porte également sur l’évaluation des modes d’organisation et des pratiques de gestion qui influencent directement la performance et l’efficacité de l’Université.
    </p>
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Cette analyse permet d’identifier les forces et les faiblesses<sup>3</sup>. Elle constitue un élément central du diagnostic institutionnel et contribue à éclairer les choix stratégiques, en assurant la cohérence entre les ambitions, les moyens disponibles et les capacités opérationnelles à l’échelle de l’USJ.
    </p>
    <p style="font-size:14px; line-height:1.45; color:{USJ_TEXT}; margin-top:8px; margin-bottom:18px;">
    <sup>3</sup> Exemples de Forces et Faiblesses en Annexe B.
    </p>
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:0;">
    Nous vous remercions de bien vouloir compléter les tableaux ci-dessous en vous appuyant sur les données disponibles et sur l’avis de votre institution et de ses parties prenantes, en traitant au moins six des thèmes proposés, dans une perspective globale à l’échelle de l’Université. Il convient de garder à l’esprit qu’il s’agit d’analyser l’état actuel afin de détecter les points forts et les points faibles de l’Université.
    </p>
</div>
""")


def render_internal_analysis():
    internal_themes = [
        "Soutenabilité financière",
        "Gouvernance et Leadership",
        "Stratégie académique",
        "Recherche et Innovation",
        "Environnement digital",
        "Succès des étudiants",
        "Ressources humaines",
        "Stratégie internationale",
        "Mission sociétale",
        "Espace et infrastructures",
        "Environnement de travail",
        "Diversité et inclusion",
        "Développement Durable",
        "Autre",
    ]

    internal_analysis = {}

    for theme in internal_themes:
        html_block(f"""
<div style="background:{USJ_LIGHT_BLUE}; border-left:5px solid {USJ_RED}; padding:10px 14px 10px 28px; border-radius:6px; margin-top:20px; margin-bottom:8px; font-weight:700; color:{USJ_RED}; font-size:17px;">
    <span style="font-size:22px; margin-right:10px; color:{USJ_RED};">•</span>{theme}
</div>
""")

        internal_analysis[theme] = st.text_area(
            label=theme,
            key=f"internal_{theme}",
            height=300,
            placeholder="Merci de saisir votre réponse ici",
            label_visibility="collapsed"
        )

    return internal_analysis

def render_external_intro():
    html_block(f"""
<div style="background-color:#ffffff; padding:24px 34px; border-radius:12px; border-left:7px solid {USJ_BLUE}; border-top:2px solid {USJ_GOLD}; border-bottom:2px solid {USJ_RED}; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:25px;">

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    L’analyse de l’environnement externe constitue une étape essentielle du processus de planification stratégique. Elle vise à situer l’USJ dans son écosystème institutionnel, académique, économique et réglementaire, afin d’identifier les facteurs externes susceptibles d’influencer ses orientations, ses performances et sa soutenabilité à moyen et à long terme.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:4px;">
    Cette analyse permet d’identifier les Opportunités et les Menaces<sup>4</sup> auxquelles l’Université est confrontée, en examinant les tendances clés, les enjeux critiques, les exigences réglementaires et les normes du secteur, ainsi que les pratiques et références observées auprès d’institutions ou d’organisations comparables (benchmarking).
    </p>

    <p style="font-size:14px; line-height:1.45; color:{USJ_TEXT}; margin-top:0; margin-bottom:18px;">
    <sup>4</sup> Exemples d’Opportunités et de Menaces en Annexe C.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Au-delà des opinions recueillies auprès de certaines parties prenantes, cette analyse repose également sur l’exploitation de données issues de sources externes variées. Chaque institution est ainsi invitée à s’appuyer sur des recherches documentaires, des ressources provenant d’associations professionnelles ou de rapports sectoriels, ainsi que sur des entretiens menés avec des institutions ou organisations pertinentes.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:0;">
    Nous vous remercions de bien vouloir compléter les tableaux ci-dessous en traitant, dans la mesure du possible, les thèmes proposés, dans une perspective globale à l’échelle de l’Université. Il convient de garder à l’esprit qu’il s’agit d’analyser l’état actuel afin d’identifier les Menaces et les Opportunités pour l’Université.
    </p>

</div>
""")


def render_external_analysis():
    external_themes = [
        "Exigences ministérielles et Environnement réglementaire",
        "Marché du travail et Associations professionnelles",
        "Institutions paires : Concurrence et Benchmarking (si des informations précises sont disponibles prière de les fournir avec un document à part si nécessaire)",
        "L’Intelligence artificielle",
        "Attractivité vis-à-vis des élèves des écoles",
        "Réputation et Image",
        "Autres Menaces ou Opportunités éventuelles",
        "Suggestions de meilleures pratiques ou de programmes innovants",
    ]

    external_analysis = {}

    for theme in external_themes:

        if theme.startswith("Institutions paires"):
            title_html = f"""
            <span style="font-weight:700;">
                • Institutions paires : Concurrence et Benchmarking
            </span>
            <span style="font-weight:400;">
                (si des informations précises sont disponibles prière de les fournir avec un document à part si nécessaire)
            </span>
            """
        else:
            title_html = f"""
            <span style="font-weight:700;">
                • {theme}
            </span>
            """

        html_block(f"""
<div style="background:{USJ_LIGHT_BLUE}; border-left:5px solid {USJ_RED}; padding:10px 14px 10px 28px; border-radius:6px; margin-top:20px; margin-bottom:8px; color:{USJ_RED}; font-size:17px;">
    {title_html}
</div>
""")

        external_analysis[theme] = st.text_area(
            label=theme,
            key=f"external_{theme}",
            height=300,
            placeholder="Merci de saisir votre réponse ici",
            label_visibility="collapsed"
        )

    return external_analysis

def render_swot_intro():
    html_block(f"""
<div style="background-color:#ffffff; padding:24px 34px; border-radius:12px; border-left:7px solid {USJ_BLUE}; border-top:2px solid {USJ_GOLD}; border-bottom:2px solid {USJ_RED}; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:25px;">
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    L'Analyse SWOT est un levier de planification stratégique qui permet de synthétiser les constats majeurs afin d’améliorer les processus de planification et d'optimiser la prise de décision au niveau de l’Université.
    </p>
</div>
""")


def render_swot_table(section_key, left_title, right_title):
    rows = []

    col1, col2 = st.columns(2)

    with col1:
        html_block(f"""
<div style="background:{USJ_BLUE}; color:white; padding:10px 12px; min-height:42px; display:flex; align-items:center; justify-content:center; font-weight:700; border-radius:6px;">
    {left_title}
</div>
""")

    with col2:
        html_block(f"""
<div style="background:{USJ_BLUE}; color:white; padding:10px 12px; min-height:42px; display:flex; align-items:center; justify-content:center; font-weight:700; border-radius:6px;">
    {right_title}
</div>
""")

    for i in range(1, 6):
        col1, col2 = st.columns(2)

        with col1:
            left_value = st.text_area(
                label=f"{left_title} {i}",
                key=f"{section_key}_{left_title}_{i}",
                height=120,
                placeholder="Merci de saisir votre réponse ici",
                label_visibility="collapsed"
            )

        with col2:
            right_value = st.text_area(
                label=f"{right_title} {i}",
                key=f"{section_key}_{right_title}_{i}",
                height=120,
                placeholder="Merci de saisir votre réponse ici",
                label_visibility="collapsed"
            )

        rows.append({
            left_title: left_value,
            right_title: right_value,
        })

    return rows


def render_swot_analysis():
    swot_data = {}

    html_block(f"""
<div style="background:#ffffff; padding:18px 24px; border-radius:10px; border-left:5px solid {USJ_RED}; margin-top:15px; margin-bottom:15px;">
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:6px;">
    <strong>1. Facteurs internes :</strong> Identification des forces et des faiblesses propres à l'Université.
    </p>
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:0;">
    Nous vous remercions de bien vouloir compléter le tableau ci-dessous en indiquant au maximum cinq forces et cinq faiblesses. Vos réponses seront déduites de l’analyse de l’état actuel interne (section III principalement).
    </p>
</div>
""")

    swot_data["facteurs_internes"] = render_swot_table(
        section_key="swot_internal",
        left_title="Forces",
        right_title="Faiblesses"
    )

    html_block(f"""
<div style="background:#ffffff; padding:18px 24px; border-radius:10px; border-left:5px solid {USJ_RED}; margin-top:28px; margin-bottom:15px;">
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:6px;">
    <strong>2. Facteurs externes :</strong> Identification des opportunités de développement et des menaces émanant de l'environnement extérieur.
    </p>
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:0;">
    Nous vous remercions de bien vouloir compléter le tableau ci-dessous en indiquant au maximum cinq opportunités et cinq menaces. Vos réponses seront déduites de l’analyse de l’état actuel externe (section IV principalement).
    </p>
</div>
""")

    swot_data["facteurs_externes"] = render_swot_table(
        section_key="swot_external",
        left_title="Opportunités",
        right_title="Menaces"
    )

    return swot_data

def render_priorities_intro():
    html_block(f"""
<div style="background-color:#ffffff; padding:24px 34px; border-radius:12px; border-left:7px solid {USJ_BLUE}; border-top:2px solid {USJ_GOLD}; border-bottom:2px solid {USJ_RED}; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:25px;">
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Cette section a pour objectif de proposer, à l’échelle de l’USJ, des priorités stratégiques et des initiatives (projets), en cohérence avec les constats issus de l’analyse des environnements interne et externe et de l’analyse SWOT. Les propositions attendues doivent refléter les enjeux majeurs identifiés, les capacités institutionnelles existantes et les orientations à privilégier pour les prochaines années.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Les priorités stratégiques sont les enjeux sur lesquels l’Université doit porter ses efforts pour remédier aux faiblesses, capitaliser sur les forces, tirer avantage des opportunités et faire face aux menaces identifiées par l’analyse SWOT.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    L'initiative correspond plus concrètement, à un projet spécifique qui permet la mise en œuvre de la priorité correspondante. Elle peut être au niveau de l’Université ou bien au niveau de votre institution. Afin de clarifier les attentes et de faciliter le pilotage, chaque initiative doit impérativement être formulée par un verbe d'action.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:0;">
    Nous vous remercions de bien vouloir compléter le tableau ci-dessous en indiquant au maximum trois priorités stratégiques et 1 à 3 initiatives par priorité. Les initiatives peuvent être au niveau de l’Université et/ou au niveau de l’institution. Vos réponses seront déduites de l’analyse SWOT. Vous pouvez hiérarchiser les priorités en les numérotant de 1 à 3.
    </p>
</div>
""")


def render_priorities_table():
    priorities_rows = []

    col1, col2 = st.columns([1.2, 1.8])

    with col1:
        html_block(f"""
<div style="background:{USJ_BLUE}; color:white; padding:10px 12px; min-height:42px; display:flex; align-items:center; justify-content:center; font-weight:700; border-radius:6px;">
    Priorités stratégiques au niveau de l’USJ
</div>
""")

    with col2:
        html_block(f"""
<div style="background:{USJ_BLUE}; color:white; padding:10px 12px; min-height:42px; display:flex; align-items:center; justify-content:center; font-weight:700; border-radius:6px;">
    Initiatives
</div>
""")

    for i in range(1, 7):
        col1, col2 = st.columns([1.2, 1.8])

        with col1:
            priority_value = st.text_area(
                label=f"Priorité stratégique {i}",
                key=f"priority_{i}",
                height=140,
                placeholder="Merci de saisir votre réponse ici",
                label_visibility="collapsed"
            )

        with col2:
            initiative_value = st.text_area(
                label=f"Initiatives {i}",
                key=f"initiative_{i}",
                height=140,
                placeholder="Merci de saisir votre réponse ici",
                label_visibility="collapsed"
            )

        priorities_rows.append({
            "priorite_strategique": priority_value,
            "initiatives": initiative_value,
        })

    return priorities_rows

def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="📋", layout="wide")

    apply_usj_style()
    init_db()

    st.session_state.setdefault("n_autres_rows", 1)

    render_first_page_header()

    mode = st.sidebar.radio(
        "Navigation",
        ["Saisir une réponse", "Consulter / exporter les réponses"],
    )

    if mode == "Saisir une réponse":
        with st.form("etat_actuel_form", clear_on_submit=False):

            st.markdown("## Informations générales")

            col1, col2, col3 = st.columns(3)

            with col1:
                institution = st.text_input("Institution")

            with col2:
                responsable = st.text_input("Responsable")

            with col3:
                response_date = st.date_input("Date")

            email = st.text_input("Email du responsable")

            st.markdown("---")

            section_header("I - Introduction")
            render_fixed_introduction()

            st.divider()

            section_header("II - Identification des parties prenantes")
            render_stakeholder_intro()
            stakeholder_rows = render_stakeholder_table()

            html_block(f"""
<div style="font-size:14px; line-height:1.45; color:{USJ_TEXT}; margin-top:8px; margin-bottom:20px;">
    <sup>2</sup> Exemple de parties prenantes en Annexe A.
</div>
""")

            st.divider()

            section_header("III - Analyse interne de l’État actuel de l’Université")
            render_internal_intro()
            internal_analysis = render_internal_analysis()

            st.divider()

            section_header("IV - Analyse externe de l’environnement actuel de l’Université")
            render_external_intro()
            external_analysis = render_external_analysis()

            st.divider()

            section_header("V - Analyse SWOT – Niveau USJ")
            render_swot_intro()
            swot_analysis = render_swot_analysis()

            st.divider()

            section_header("VI - Priorités stratégiques et initiatives proposées – Niveau USJ")
            render_priorities_intro()
            priorities_initiatives = render_priorities_table()

            submitted = st.form_submit_button("Enregistrer la réponse")

            if submitted:
                metadata = {
                    "institution": institution,
                    "responsable": responsable,
                    "email": email,
                    "response_date": str(response_date),
                }

                data = {
                    "metadata": metadata,
                    "introduction": {},
                    "stakeholders": {
                        "rows": stakeholder_rows,
                    },
                    "internal_analysis": internal_analysis,
                    "external_analysis": external_analysis,
                    "swot_analysis": swot_analysis,
                    "priorities_initiatives": priorities_initiatives,
                }

                save_response(metadata, data)
                st.success("Réponse enregistrée avec succès.")

    else:
        st.markdown("## Consulter / exporter les réponses")

        df = load_responses()

        if df.empty:
            st.warning("Aucune réponse enregistrée pour le moment.")
            return

        st.metric("Nombre total de réponses", len(df))

        st.markdown("### Réponses enregistrées")
        st.dataframe(
            df[["id", "submitted_at", "respondent_name", "respondent_unit", "respondent_email"]],
            use_container_width=True,
        )

        flat_df = pd.DataFrame([flatten_response(row) for _, row in df.iterrows()])

        csv_data = flat_df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="Télécharger les réponses en CSV",
            data=csv_data,
            file_name="etat_actuel_responses.csv",
            mime="text/csv",
        )

        excel_path = Path("etat_actuel_responses.xlsx")
        flat_df.to_excel(excel_path, index=False)

        with open(excel_path, "rb") as f:
            st.download_button(
                label="Télécharger les réponses en Excel",
                data=f,
                file_name="etat_actuel_responses.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        st.markdown("### Données complètes")
        st.dataframe(flat_df, use_container_width=True)


if __name__ == "__main__":
    main()
