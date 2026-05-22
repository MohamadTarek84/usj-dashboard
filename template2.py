#!/usr/bin/env python
# coding: utf-8

import sqlite3
import json
import base64
import html as html_lib
import re
import textwrap
from datetime import datetime
from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle


APP_TITLE = "PLAN STRATÉGIQUE USJ 2032"
DB_PATH = Path("focus_group_responsesT2.db")
LOGO_PATH = Path("LogoUAQ.png")
INTRO_IMAGE_PATH = Path("Intro_schema.png")
ANNEXE_A_PATH = Path("Annexe_A.png")
ANNEXE_B_PATH = Path("Annexe_B.png")
ANNEXE_C_PATH = Path("Annexe_C.png")
PRINT_ICON_PATH = Path("Print.png")

USJ_BLUE = "#001F5B"
USJ_BLUE_2 = "#1F3C88"
USJ_RED = "#8B1538"
USJ_GOLD = "#C9A227"
USJ_LIGHT_BLUE = "#EAF2F8"
USJ_TEXT = "#1B2A41"

AUTHORIZED_TEST_CODES = {
    # Old test codes
    "USJ-HS-2032": {"responsable": "Hadi Sawaya", "institution": "ESIB"},
    "USJ-IM-2032": {"responsable": "Irma Majdalani", "institution": "FSE"},
    "USJ-NRH-2032": {"responsable": "Nadine Riachi Haddad", "institution": "FDLT"},
    "USJ-UEH-2032": {"responsable": "Ursula El Hage", "institution": "FGM"},
    "USJ-LKG-2032": {"responsable": "Lina Koleilat Ghalayini", "institution": "FSE"},
    "USJ-TH-2032": {"responsable": "Tarek Halabi", "institution": ""},

    # Final respondent codes
    "USJ-ESMOD-7KQ4-2032": {"responsable": "Nicole MASSOUD", "institution": "ESMOD"},
    "USJ-ESTS-M9X2-2032": {"responsable": "Rima MAWAD", "institution": "ESTS"},
    "USJ-ETIB-P4L8-2032": {"responsable": "Mary YAZBECK", "institution": "ETIB"},
    "USJ-FDLT-R6N3-2032": {"responsable": "Gina ABOU FADEL SAAD", "institution": "FDLT"},
    "USJ-FLSH-T8B5-2032": {"responsable": "Myrna GANNAGÉ", "institution": "FLSH"},
    "USJ-FSEDU-C2V7-2032": {"responsable": "Patricia FATA RACHED", "institution": "FSEDU"},
    "USJ-FSR-H5D9-2032": {"responsable": "Salah ABOU JAOUDE s.j.", "institution": "FSR"},
    "USJ-IEIC-J3W6-2032": {"responsable": "Roula TALHOUK", "institution": "IEIC"},
    "USJ-IESAV-F8K1-2032": {"responsable": "Toufic EL-KHOURY", "institution": "IESAV"},
    "USJ-ILE-Q2M4-2032": {"responsable": "Rock EL-ACHY", "institution": "ILE"},
    "USJ-ILO-Y7P5-2032": {"responsable": "Tony El-KHAWAJI", "institution": "ILO"},
    "USJ-ISSR-L9T2-2032": {"responsable": "Yara MATTA", "institution": "ISSR"},
    "USJ-FDSP-X4A8-2032": {"responsable": "Marie-Claude NAJEM KOBEH", "institution": "FDSP"},
    "USJ-ISP-N6E3-2032": {"responsable": "Sami NADER", "institution": "ISP"},
    "USJ-FGM-U1R7-2032": {"responsable": "Fouad ZMOKHOL", "institution": "FGM"},
    "USJ-FSE-B8C5-2032": {"responsable": "Jean-François VERNE", "institution": "FSE"},
    "USJ-IGE-Z3H9-2032": {"responsable": "Céline BOUTROS SAAB", "institution": "IGE"},
    "USJ-ISSA-K7V2-2032": {"responsable": "Irma Majdalani", "institution": "ISSA"},
    "USJ-ESAR-M4Q6-2032": {"responsable": "Richard MITRI", "institution": "ESAR"},
    "USJ-ESIA-P9L1-2032": {"responsable": "Wadih SKAFF", "institution": "ESIA"},
    "USJ-ESIAM-T5X8-2032": {"responsable": "Wadih SKAFF", "institution": "ESIAM"},
    "USJ-ESIB-W2N4-2032": {"responsable": "Wassim RAPHAËL", "institution": "ESIB"},
    "USJ-FS-D7K3-2032": {"responsable": "Maher ABBOUD", "institution": "FS"},
    "USJ-INCI-R8M6-2032": {"responsable": "Marc IBRAHIM", "institution": "INCI"},
    "USJ-ESF-H1P9-2032": {"responsable": "Salimé SALAMEH SAAD", "institution": "ESF"},
    "USJ-ETLAM-C6Y2-2032": {"responsable": "Marianne ABI FADEL", "institution": "ETLAM"},
    "USJ-FM-V4T7-2032": {"responsable": "Elie NEMER", "institution": "FM"},
    "USJ-FMD-L8Q5-2032": {"responsable": "Nada FARHAT MCHAYLEH", "institution": "FMD"},
    "USJ-FP-J2R4-2032": {"responsable": "Hayat AZOURY TANNOUS", "institution": "FP"},
    "USJ-FSI-X7B1-2032": {"responsable": "Rima SASSINE KAZAN", "institution": "FSI"},
    "USJ-IET-N5K8-2032": {"responsable": "Carla MATTA-ABI ZEID", "institution": "IET"},
    "USJ-IPHY-P3D6-2032": {"responsable": "Pascal BREIDY", "institution": "IPHY"},
    "USJ-IPM-T9W2-2032": {"responsable": "Céleste YOUNES HARB", "institution": "IPM"},
    "USJ-ISO-F6M7-2032": {"responsable": "Guillemette HENRY", "institution": "ISO"},
    "USJ-ISSP-Q1H4-2032": {"responsable": "Michèle KOSREMELLI-ASMAR", "institution": "ISSP"},
    "USJ-CDB-R5X9-2032": {"responsable": "Nathalie SABBAGH", "institution": "CDB"},
    "USJ-CLN-B2V6-2032": {"responsable": "Fadia ALAM GEMAYEL", "institution": "CLN"},
    "USJ-CLS-Y8P3-2032": {"responsable": "Dina SIDANI", "institution": "CLS"},
    "USJ-CZB-K4N1-2032": {"responsable": "Alain AJAMI EL", "institution": "CZB"},
    "USJ-CFP-M7T5-2032": {"responsable": "Fadi EL-HAGE", "institution": "CFP"},
    "USJ-CPM-L3Q8-2032": {"responsable": "Johanna HAWARI-BOURJEILY", "institution": "CPM"},
    "USJ-UPT-H9C2-2032": {"responsable": "Roland TOMB", "institution": "UPT"},
}

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
            statut TEXT DEFAULT 'Brouillon',
            draft_code TEXT,
            data_json TEXT NOT NULL,
            admin_data_json TEXT
        )
    """)

    existing_cols = [row[1] for row in cur.execute("PRAGMA table_info(responses)").fetchall()]

    if "statut" not in existing_cols:
        cur.execute("ALTER TABLE responses ADD COLUMN statut TEXT DEFAULT 'Brouillon'")

    if "draft_code" not in existing_cols:
        cur.execute("ALTER TABLE responses ADD COLUMN draft_code TEXT")

    if "admin_data_json" not in existing_cols:
        cur.execute("ALTER TABLE responses ADD COLUMN admin_data_json TEXT")

    conn.commit()
    conn.close()

def save_response(metadata, data):
    institution = metadata.get("institution", "").strip()
    responsable = metadata.get("responsable", "").strip()
    email = metadata.get("email", "").strip()
    statut = metadata.get("statut", "Brouillon")
    draft_code = metadata.get("draft_code", "").strip().upper()

    if not draft_code:
        raise ValueError("Un code de reprise est obligatoire pour enregistrer la réponse.")

    data["draft_code"] = draft_code
    data["metadata"]["draft_code"] = draft_code

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    existing = cur.execute("""
        SELECT id FROM responses
        WHERE draft_code = ?
        ORDER BY id DESC
        LIMIT 1
    """, (draft_code,)).fetchone()

    if existing:
        cur.execute("""
            UPDATE responses
            SET submitted_at = ?,
                respondent_name = ?,
                respondent_unit = ?,
                respondent_email = ?,
                statut = ?,
                data_json = ?
            WHERE id = ?
        """, (
            "2026-06-04",
            responsable,
            institution,
            email,
            statut,
            json.dumps(data, ensure_ascii=False),
            existing[0],
        ))
    else:
        cur.execute("""
            INSERT INTO responses (
                submitted_at,
                respondent_name,
                respondent_unit,
                respondent_email,
                statut,
                draft_code,
                data_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            responsable,
            institution,
            email,
            statut,
            draft_code,
            json.dumps(data, ensure_ascii=False),
        ))

    conn.commit()
    conn.close()

    return draft_code


def load_responses():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM responses ORDER BY id DESC", conn)
    conn.close()
    return df


def load_existing_draft_by_code(draft_code):
    draft_code = draft_code.strip().upper()

    if not draft_code:
        return None

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    row = cur.execute("""
        SELECT data_json, statut
        FROM responses
        WHERE draft_code = ?
        ORDER BY id DESC
        LIMIT 1
    """, (draft_code,)).fetchone()

    conn.close()

    if row is None:
        return None

    data = json.loads(row[0])
    data["loaded_statut"] = row[1]
    data["draft_code"] = draft_code
    return data


def preload_draft_into_session(data):
    if not data:
        return

    st.session_state["current_draft_code"] = data.get("draft_code", "")

    metadata = data.get("metadata", {})
    st.session_state["institution"] = metadata.get("institution", "")
    st.session_state["responsable"] = metadata.get("responsable", "")

    stakeholder_rows = data.get("stakeholders", {}).get("rows", [])

    stakeholder_options = [
        "Responsables institution",
        "Enseignants cadrés",
        "Enseignants non-cadrés",
        "PSG",
        "Étudiants",
        "Anciens",
        "Employeurs",
        "Conseil d’orientation stratégique",
    ]

    row_types = []
    number_of_rows_to_load = max(8, len(stakeholder_rows))

    for i in range(1, number_of_rows_to_load + 1):
        row = stakeholder_rows[i - 1] if i <= len(stakeholder_rows) else {}

        categorie = row.get("categorie", "")

        if categorie and categorie not in stakeholder_options:
            row_types.append("autres")
            st.session_state[f"stakeholder_category_autre_{i}"] = categorie
        else:
            row_types.append("standard")
            st.session_state[f"stakeholder_category_{i}"] = categorie if categorie in stakeholder_options else None

        st.session_state[f"stakeholder_nom_{i}"] = row.get("nom", "")
        st.session_state[f"stakeholder_poste_{i}"] = row.get("poste", "")
        st.session_state[f"stakeholder_organisme_{i}"] = row.get("organisme_affiliation", "")

    st.session_state["stakeholder_row_types"] = row_types

    for theme, value in data.get("internal_analysis", {}).items():
        st.session_state[f"internal_{theme}"] = value

    for theme, value in data.get("external_analysis", {}).items():
        st.session_state[f"external_{theme}"] = value

    for section_key, rows in data.get("swot_analysis", {}).items():
        prefix = "swot_internal" if section_key == "facteurs_internes" else "swot_external"

        for i, row in enumerate(rows, start=1):
            for col_name, value in row.items():
                st.session_state[f"{prefix}_{col_name}_{i}"] = value


    priorities_data = data.get("priorities_initiatives", {})

    for i in range(1, 6):
        st.session_state[f"priority_only_{i}"] = priorities_data.get(f"priorite_{i}", "")

    phrases = [
        "Nous souhaitons que l’USJ soit reconnue pour …",
        "Nous souhaitons que nos étudiants disent que l’USJ …",
        "L’USJ serait un excellent lieu de travail si …",
    ]

    pour_finir = data.get("pour_finir", {})

    for i, phrase in enumerate(phrases, start=1):
        saved_phrase = pour_finir.get(phrase, {})

        if isinstance(saved_phrase, dict):
            st.session_state[f"pour_finir_{i}_1"] = saved_phrase.get("reponse_1", "")
            st.session_state[f"pour_finir_{i}_2"] = saved_phrase.get("reponse_2", "")
            st.session_state[f"pour_finir_{i}_3"] = saved_phrase.get("reponse_3", "")
        else:
            st.session_state[f"pour_finir_{i}_1"] = saved_phrase
            st.session_state[f"pour_finir_{i}_2"] = ""
            st.session_state[f"pour_finir_{i}_3"] = ""


def flatten_response(row):
    base = {
        "id": row["id"],
        "submitted_at": row["submitted_at"],
        "responsable": row["respondent_name"],
        "institution": row["respondent_unit"],
        "email": row["respondent_email"],
    }

    if "statut" in row.index:
        base["statut"] = row["statut"]

    if "draft_code" in row.index:
        base["draft_code"] = row["draft_code"]

    data = json.loads(row["data_json"])

    for section, values in data.items():
        if isinstance(values, dict):
            for key, value in values.items():
                if isinstance(value, list):
                    base[f"{section}_{key}"] = json.dumps(value, ensure_ascii=False)
                elif isinstance(value, dict):
                    base[f"{section}_{key}"] = json.dumps(value, ensure_ascii=False)
                else:
                    base[f"{section}_{key}"] = value
        else:
            base[section] = values

    return base

def apply_usj_style():
    html_block(f"""
<style>

#MainMenu {{
    display: none !important;
    visibility: hidden !important;
}}

header {{
    display: none !important;
    visibility: hidden !important;
}}

[data-testid="stToolbar"] {{
    display: none !important;
    visibility: hidden !important;
}}

[data-testid="stDecoration"] {{
    display: none !important;
    visibility: hidden !important;
}}

[data-testid="stStatusWidget"] {{
    display: none !important;
    visibility: hidden !important;
}}

button[data-testid="stBaseButton-header"] {{
    display: none !important;
    visibility: hidden !important;
}}

[data-testid="stBaseButton-header"] {{
    display: none !important;
    visibility: hidden !important;
}}

html, body, [class*="css"], [class*="st-"], .stApp {{
    font-family: Candara, Calibri, Arial, sans-serif !important;
    color: {USJ_TEXT};
}}

/* =====================================================
   AZURE / STREAMLIT FIX
   Hide Streamlit multipage/sidebar elements and the
   broken keyboard_double_arrow_right text in Azure.
===================================================== */
section[data-testid="stSidebar"] {{
    display: none !important;
    visibility: hidden !important;
    width: 0px !important;
    min-width: 0px !important;
    max-width: 0px !important;
}}

[data-testid="stSidebarNav"] {{
    display: none !important;
    visibility: hidden !important;
}}

[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
button[kind="header"] {{
    display: none !important;
    visibility: hidden !important;
}}

div[data-testid="stAppViewContainer"] {{
    margin-left: 0px !important;
    padding-left: 0px !important;
}}

.main .block-container,
div[data-testid="stAppViewContainer"] .block-container {{
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    max-width: 100% !important;
}}

div[data-testid="stTextInput"] label,
div[data-testid="stTextInput"] label *,
div[data-testid="stDateInput"] label,
div[data-testid="stDateInput"] label * {{
    font-weight: 700 !important;
    color: #000000 !important;
}}

div[data-testid="stTextInput"] input,
div[data-testid="stDateInput"] input {{
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    opacity: 1 !important;
    background-color: #E3DED9 !important;
    border: none !important;
    border-radius: 6px !important;
    box-shadow: none !important;
    outline: none !important;
}}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stDateInput"] input:focus {{
    background-color: #E3DED9 !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}}

div[data-testid="stTextInput"] input:disabled,
div[data-testid="stDateInput"] input:disabled {{
    background-color: #E3DED9 !important;
    border: none !important;
    border-radius: 6px !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    opacity: 1 !important;
}}

div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stDateInput"] input::placeholder {{
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    opacity: 1 !important;
}}

.annexe-a-hover {{
    position: relative;
    color: #0000FF;
    text-decoration: underline;
    font-weight: 700;
    cursor: help;
}}

.annexe-a-popup {{
    display: none;
    position: fixed;
    z-index: 99999;
    left: 50%;
    top: 90px;
    transform: translateX(-50%);
    background: white;
    padding: 8px;
    border: 1px solid #595959;
    box-shadow: 0 4px 16px rgba(0,0,0,0.20);
    max-width: 95vw;
}}

.annexe-a-popup img {{
    width: 900px !important;
    max-width: 92vw !important;
    height: auto !important;
}}

.annexe-a-hover:hover .annexe-a-popup {{
    display: block;
}}

div[data-testid="stTextArea"] {{
    border: 0.75px solid #595959 !important;
    border-radius: 0px !important;
    background-color: #E3DED9 !important;
}}

div[data-testid="stTextArea"] > div {{
    border: none !important;
    box-shadow: none !important;
}}

div[data-testid="stTextArea"] textarea {{
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    opacity: 1 !important;
    border: 1.5px solid #595959 !important;
    border-radius: 0px !important;
    background-color: #E3DED9 !important;
    box-shadow: none !important;
}}

div[data-testid="stTextArea"] textarea:focus {{
    border: 2px solid #595959 !important;
    box-shadow: none !important;
    outline: none !important;
}}

div[data-testid="stTextArea"] textarea::placeholder {{
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    opacity: 1 !important;
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: Candara, Calibri, Arial, sans-serif !important;
    color: {USJ_BLUE} !important;
    font-weight: 700 !important;
}}

p, div, span, label, button, input, textarea, select {{
    font-family: Candara, Calibri, Arial, sans-serif !important;
}}

.stTextArea textarea {{
    resize: vertical !important;
    overflow-y: auto !important;
}}

div[data-testid="stForm"] {{
    border: none !important;
    border-radius: 0px !important;
    padding: 0px !important;
    background-color: #FFFFFF;
    box-shadow: none !important;
}}


/* Normal buttons */
.stButton button,
.stDownloadButton button,
div[data-testid="stFormSubmitButton"] button {{
    background-color: #0070C0 !important;
    color: white !important;
    border-radius: 8px !important;
    border: 1px solid #0070C0 !important;
    font-weight: 800 !important;
    font-size: 18px !important;
    padding: 10px 22px !important;
    white-space: nowrap !important;
}}

.stButton button p,
.stDownloadButton button p,
div[data-testid="stFormSubmitButton"] button p {{
    color: white !important;
    white-space: nowrap !important;
}}

/* ONLY these two stakeholder add-row buttons */
.st-key-add_stakeholder_standard button,
.st-key-add_stakeholder_autres button {{
    background-color: #001F5B !important;
    border: 1px solid #001F5B !important;
    color: white !important;
}}

.st-key-add_stakeholder_standard button:hover,
.st-key-add_stakeholder_autres button:hover {{
    background-color: #001352 !important;
    border: 1px solid #001352 !important;
    color: white !important;
}}

.st-key-add_stakeholder_standard button p,
.st-key-add_stakeholder_autres button p {{
    color: white !important;
    white-space: nowrap !important;
}}


/* Action buttons: same size for save and final buttons */
.st-key-quick_save_after_stakeholders,
.st-key-quick_save_after_internal,
.st-key-quick_save_after_external,
.st-key-quick_save_after_swot,
.st-key-quick_save_after_priorities,
.st-key-save_draft_button,
.st-key-submit_final_button {{
    display: flex !important;
    justify-content: flex-start !important;
}}

.st-key-quick_save_after_stakeholders button,
.st-key-quick_save_after_internal button,
.st-key-quick_save_after_external button,
.st-key-quick_save_after_swot button,
.st-key-quick_save_after_priorities button,
.st-key-save_draft_button button,
.st-key-submit_final_button button {{
    width: 360px !important;
    min-width: 360px !important;
    max-width: 360px !important;
    height: 58px !important;
    min-height: 58px !important;
    padding: 10px 22px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}}

/* Final submit button only */
button[kind="primary"] {{
    background-color: #8B1538 !important;
    border: 1px solid #8B1538 !important;
    color: white !important;
}}

button[kind="primary"] p {{
    color: white !important;
    white-space: nowrap !important;
}}

div[data-testid="InputInstructions"] {{
    display: none !important;
}}

[data-testid="stTextInput"] [data-testid="InputInstructions"],
[data-testid="stSelectbox"] [data-testid="InputInstructions"],
[data-testid="stTextArea"] [data-testid="InputInstructions"] {{
    display: none !important;
    visibility: hidden !important;
    height: 0px !important;
}}

textarea + div {{
    display: none !important;
}}

hr {{
    border: none !important;
    height: 3px !important;
    background-color: #D0D6E0 !important;
    margin-top: 14px !important;
    margin-bottom: 14px !important;
}}

.final-action-line {{
    border: none !important;
    height: 3px !important;
    background-color: #D0D6E0 !important;
    margin-top: 14px !important;
    margin-bottom: 14px !important;
}}

/* Move the print icon iframe upward while keeping enough height so the image is not cut */
div[data-testid="stIFrame"] {{
    margin-top: 0px !important;
}}

/* =========================
   CLEAN PRINT / PDF MODE
========================= */

.print-answer-text {{
    display: none;
}}

.pour-finir-print-row {{
    display: none;
}}

@media print {{

    @page {{
        size: A4 portrait;
        margin: 10mm 9mm 10mm 9mm;
    }}

    html, body, .stApp {{
        background: white !important;
        overflow: visible !important;
        width: 100% !important;
    }}

    .block-container {{
        max-width: 190mm !important;
        width: 190mm !important;
        padding: 0 !important;
        margin: 0 auto !important;
    }}

    header,
    footer,
    #MainMenu,
    .stDeployButton,
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"],
    .print-button-wrapper,
    div[data-testid="stButton"],
    div[data-testid="stDownloadButton"],
    iframe {{
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    .print-page-break {{
        break-before: page !important;
        page-break-before: always !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    .print-answer-block {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        margin-bottom: 3px !important;
    }}

    div[data-testid="stHorizontalBlock"] {{
        width: 100% !important;
    }}

    h1 {{
        font-size: 28px !important;
        line-height: 1.15 !important;
        margin-top: 0 !important;
        margin-bottom: 6px !important;
    }}

    h2 {{
        font-size: 18px !important;
        line-height: 1.2 !important;
    }}

    h3, h4, p, div, span, label {{
        font-size: 11px !important;
        line-height: 1.3 !important;
    }}

    div[style*="border-left:7px"] {{
        break-after: avoid !important;
        page-break-after: avoid !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        margin-top: 6px !important;
        margin-bottom: 8px !important;
        padding: 8px 12px !important;
    }}

    div[data-testid="stTextArea"] {{
        display: none !important;
    }}

    .print-answer-text {{
        display: block !important;
        width: 100% !important;
        margin-top: 2px !important;
        margin-bottom: 3px !important;
        break-inside: auto !important;
        page-break-inside: auto !important;
    }}

    .print-answer-content {{
        display: block !important;
        width: 100% !important;
        box-sizing: border-box !important;
        border: 1px solid #595959 !important;
        background-color: #E3DED9 !important;
        color: #000000 !important;
        font-size: 10.5px !important;
        line-height: 1.2 !important;
        padding: 6px !important;
        white-space: pre-wrap !important;
        overflow: visible !important;
    }}

    .print-answer-content-empty {{
        min-height: 34px !important;
        height: 34px !important;
    }}

    .print-answer-content-filled {{
        min-height: 40px !important;
        height: auto !important;
    }}

    div[style*="min-height:24px"] {{
        min-height: 10px !important;
        margin-top: -2px !important;
        margin-bottom: 2px !important;
        font-size: 9px !important;
        line-height: 1.1 !important;
    }}

    div[data-testid="stTextInput"] input {{
        height: 30px !important;
        min-height: 30px !important;
        border: none !important;
        background-color: #E3DED9 !important;
        font-size: 10px !important;
    }}

    div[data-testid="stSelectbox"] {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
    }}

    div[data-testid="stSelectbox"] > div {{
        min-height: 30px !important;
        height: auto !important;
        overflow: visible !important;
        font-size: 10px !important;
    }}

    div[data-testid="InputInstructions"] {{
        display: none !important;
    }}

    .intro-parts-print-block {{
        break-before: page !important;
        page-break-before: always !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        margin-top: 0 !important;
    }}

    .print-answer-block,
    .print-answer-text,
    .print-answer-content {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
    }}

    .print-answer-content {{
        overflow: hidden !important;
    }}

    .word-counter-status {{
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    .st-key-pour_finir_1_1,
    .st-key-pour_finir_1_2,
    .st-key-pour_finir_1_3,
    .st-key-pour_finir_2_1,
    .st-key-pour_finir_2_2,
    .st-key-pour_finir_2_3,
    .st-key-pour_finir_3_1,
    .st-key-pour_finir_3_2,
    .st-key-pour_finir_3_3 {{
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    .pour-finir-screen-label {{
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    .pour-finir-print-row {{
        display: block !important;
        width: 100% !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        margin: 8px 0 12px 0 !important;
        clear: both !important;
    }}

    .pour-finir-print-label {{
        display: block !important;
        width: 100% !important;
        color: #001F5B !important;
        font-weight: 700 !important;
        font-size: 11px !important;
        line-height: 1.25 !important;
        margin-bottom: 5px !important;
        white-space: normal !important;
    }}

    .pour-finir-print-box {{
        display: block !important;
        width: 100% !important;
        box-sizing: border-box !important;
        min-height: 28px !important;
        border: 1px solid #595959 !important;
        background-color: #E3DED9 !important;
        color: #000000 !important;
        font-size: 10.5px !important;
        line-height: 1.2 !important;
        padding: 6px !important;
        margin: 0 0 5px 0 !important;
        white-space: pre-wrap !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
    }}

    hr {{
        margin-top: 6px !important;
        margin-bottom: 6px !important;
        height: 1px !important;
    }}
}}


</style>
""")
def section_header(title):
    html_block(f"""
<div style="background-color:{USJ_LIGHT_BLUE}; padding:12px 18px; border-radius:10px; border-left:7px solid {USJ_BLUE}; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-top:0px; margin-bottom:8px;">
    <h2 style="font-size:26px; color:{USJ_BLUE}; margin:0; font-weight:700;">
        {title}
    </h2>
</div>
""")


def text_area(label, key, height=920, placeholder=None):
    return st.text_area(
        label,
        key=key,
        height=height,
        placeholder=placeholder
    )

def render_print_icon_button():
    print_icon_src = image_to_base64(PRINT_ICON_PATH)

    if print_icon_src:
        components.html(
            f"""
            <div class="print-button-wrapper" style="
                height:150px;
                display:flex;
                align-items:center;
                justify-content:center;
                overflow:visible;
                padding:0;
                margin:0;
            ">
                <button onclick="window.parent.print()" title="Imprimer / Enregistrer en PDF" style="
                    background-color:transparent;
                    border:none;
                    cursor:pointer;
                    padding:0;
                    margin:0;
                    width:130px;
                    height:130px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                ">
                    <img src="{print_icon_src}" alt="Imprimer / Enregistrer en PDF" style="
                        width:130px;
                        height:130px;
                        object-fit:contain;
                        display:block;
                    ">
                </button>
            </div>
            """,
            height=155
        )
    else:
        st.warning("Print.png non trouvé. Placez Print.png dans le même dossier que le script.")

def render_first_page_header():
    col_left, col_right = st.columns([2.2, 1])

    with col_left:
        html_block(f"""
<div style="padding-top:0px;">
    <h1 style="font-size:42px; margin-bottom:18px; color:{USJ_BLUE}; line-height:1.1;">
        PLAN STRATÉGIQUE USJ 2032
    </h1>

    <p style="font-size:18px; font-weight:700; color:{USJ_BLUE_2}; margin-top:0px; margin-bottom:0px; line-height:1.4;">
        Analyse de l’état actuel et propositions <span style="font-size:18px; font-weight:700; color:{USJ_BLUE_2};">(pré-planification stratégique USJ)</span>
    </p>
</div>
""")

    with col_right:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=350)
        else:
            st.warning("LogoUAQ.png non trouvé. Placez le logo dans le même dossier que le script.")

    st.markdown(
        """
        <style>
        [data-testid="stImage"] {
            margin-bottom: -30px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

def render_fixed_introduction():
    intro_image_src = image_to_base64(INTRO_IMAGE_PATH)

    image_html = ""
    if intro_image_src:
        image_html = f"""
        <div style="text-align:center; margin:18px 0;">
            <img src="{intro_image_src}" style="width:650px; max-width:100%; height:auto; border-radius:8px;">
        </div>
        """

    html_block(f"""
    <div style="background-color:#ffffff; padding:24px 34px; border-radius:12px; border-left:none; border-top:none; border-bottom:none; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:25px;">
        <p style="text-align:justify; font-size:19px; line-height:1.55; color:{USJ_BLUE};">
        L’enseignement supérieur est aujourd’hui confronté à des transformations rapides, à des contraintes économiques croissantes et à une intensification de la concurrence, tant nationale qu’internationale. Les évolutions technologiques, les attentes accrues des étudiants et des parties prenantes, ainsi que les exigences renforcées en matière de qualité et de performance, imposent une réflexion stratégique à la fois rigoureuse et collective. Les universités sont ainsi appelées à réinterroger en profondeur leurs modèles académiques, organisationnels et opérationnels.
        </p>

        <p style="text-align:justify; font-size:19px; line-height:1.55; color:{USJ_BLUE};">
        <strong>Le Plan stratégique USJ 2032</strong> s’inscrit dans cette dynamique. Il constitue une feuille de route institutionnelle visant à traduire la mission, la vision et les valeurs de l’USJ en priorités stratégiques claires, en objectifs cohérents et en initiatives concrètes, capables de renforcer durablement son positionnement, sa résilience ainsi que son impact académique et sociétal.
        </p>

        <p style="text-align:justify; font-size:19px; line-height:1.55; color:{USJ_BLUE};">
        L’élaboration de ce plan stratégique se décline en plusieurs étapes (voir le schéma ci-dessous), dont la première est consacrée à <strong>l’analyse de données relatives à l’état actuel de l’Université</strong>. L’ensemble des acteurs de l’Université, ainsi que les parties prenantes, sont invités à y contribuer. Ce rapport a pour objectif de vous accompagner dans la formulation de constats partagés, des pratiques existantes et des expériences vécues, afin d’identifier <strong>les forces à consolider, les fragilités à traiter, les opportunités de développement et les risques à maîtriser à l’échelle de l’Université</strong>.
        </p>

        {image_html}
    </div>
""")


    
def render_internal_intro():
    html_block(f"""
<div style="background-color:#ffffff; padding:24px 34px 10px 34px; border-radius:12px; border-left:none; border-top:none; border-bottom:none; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:6px;">
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    L’analyse interne vise à apprécier dans quelle mesure l’USJ dispose des ressources nécessaires pour soutenir sa mission et mettre en œuvre ses orientations stratégiques. Elle porte également sur l’évaluation des modes d’organisation et des pratiques de gestion qui influencent directement la performance et l’efficacité de l’Université. Cette analyse permettra d’identifier dans une étape ultérieure les forces et les faiblesses de l’Université. Elle constitue un élément central du diagnostic institutionnel et contribue à éclairer les choix stratégiques, en assurant la cohérence entre les ambitions, les moyens disponibles et les capacités opérationnelles à l’échelle de l’USJ.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Dans cette première étape, vous êtes appelés donc à analyser et évaluer, d’après votre expérience, l’état actuel des volets suivants (6 au minimum) au niveau de l’Université.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:#0070C0; font-weight:700; font-style:italic; margin-bottom:2px;">
    Nous vous remercions de bien vouloir compléter les tableaux ci-dessous en vous appuyant sur les données disponibles et sur l’avis de votre institution et de ses parties prenantes, en traitant <span style="text-decoration:underline;">au moins six</span> des thèmes proposés, dans une perspective globale à l’échelle de l’Université.
    </p>
</div>
""")


def count_words(text):
    if text is None:
        return 0
    return len(str(text).split())


def word_limited_text_area(label, key, height=300, max_words=500):
    read_only = st.session_state.get("read_only_submitted", False)

    # ADDED
    # max_chars = 3500 if max_words == 500 else 250
    
    value = st.text_area(
        label=label,
        key=key,
        height=height,
        placeholder=f"Merci de saisir votre réponse ici (au maximum {max_words} mots)",
        label_visibility="collapsed",
        disabled=read_only,

        # ADDED
        # max_chars=max_chars
    )

    word_count = count_words(value)

    printable_value = html_lib.escape(value or "")
    printable_value = printable_value.replace("\n", "<br>")
    print_answer_class = "print-answer-content-filled"

    if not printable_value.strip():
        printable_value = "&nbsp;"
        print_answer_class = "print-answer-content-empty"

    html_block(f"""
<div class="print-answer-text">
    <div class="print-answer-content {print_answer_class}">{printable_value}</div>
</div>
""")

    if not read_only:
        if word_count > max_words:
            html_block(f"""
<div class="word-counter-status" style="min-height:24px; color:#8B1538; font-weight:700; font-size:14px; margin-top:-6px; margin-bottom:8px;">
    ⚠ Vous avez saisi {word_count} mots. Maximum autorisé : {max_words} mots.
</div>
""")
        else:
            html_block(f"""
<div class="word-counter-status" style="min-height:24px; color:#595959; font-size:13px; margin-top:-6px; margin-bottom:8px;">
    {word_count}/{max_words} mots
</div>
""")

    return value


def render_internal_analysis():
    return {}
    
def render_external_intro():
    html_block(f"""
<div style="background-color:#ffffff; padding:24px 34px 10px 34px; border-radius:12px; border-left:none; border-top:none; border-bottom:none; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:6px;">

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    L’analyse de l’environnement externe constitue une étape essentielle du processus de planification stratégique. Elle vise à situer l’USJ dans son écosystème institutionnel, académique, économique et réglementaire, afin d’identifier les facteurs externes susceptibles d’influencer ses orientations, ses performances et sa soutenabilité à moyen et à long terme.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Cette analyse permettra d’identifier dans une étape ultérieure, les Opportunités et les Menaces auxquelles l’Université est confrontée, en examinant les tendances clés, les enjeux critiques, les exigences réglementaires et les normes du secteur, ainsi que les pratiques et références observées auprès d’institutions ou d’organisations comparables (benchmarking).
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Au-delà des opinions recueillies auprès de certaines parties prenantes, cette analyse repose également sur l’exploitation de données issues de sources externes variées. Chaque institution est ainsi invitée à s’appuyer sur des recherches documentaires, des ressources provenant d’associations professionnelles ou de rapports sectoriels, ainsi que sur des entretiens menés avec des institutions ou organisations pertinentes.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Dans cette deuxième étape, vous êtes appelés donc à analyser et évaluer, d’après votre expérience, l’état actuel des dimensions suivantes au niveau de l’Université.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:#0070C0; font-weight:700; font-style:italic; margin-bottom:2px;">
    Nous vous remercions de bien vouloir compléter les tableaux ci-dessous, dans une perspective globale à l’échelle de l’Université.
    </p>

</div>
""")


def render_external_analysis():
    external_themes = [
        "Exigences ministérielles et Environnement réglementaire",
        "Marché du travail et Associations professionnelles",
        "Institutions paires : Concurrence et Benchmarking (si des informations précises sont disponibles prière de les fournir dans un document à part si nécessaire)",
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
                &bull; Institutions paires : Concurrence et Benchmarking
            </span>
            <span style="font-weight:400; font-style:italic;">
                (si des informations précises sont disponibles prière de les fournir dans un document à part si nécessaire)
            </span>
            """
        else:
            title_html = f"""
            <span style="font-weight:700;">
                &bull; {theme}
            </span>
            """

        html_block('<div class="print-answer-block">')

        html_block(f"""
<div style="padding:2px 0px; margin-top:2px; margin-bottom:4px;">
    <p style="font-size:17px; line-height:1.25; color:{USJ_RED}; font-weight:700; margin:0;">
        {title_html}
    </p>
</div>
""")

        external_analysis[theme] = word_limited_text_area(
            label=theme,
            key=f"external_{theme}",
            height=300,
            max_words=500
        )
        html_block('</div>')

    return external_analysis

def render_swot_intro():
    html_block(f"""
<div style="background-color:#ffffff; padding:24px 34px 10px 34px; border-radius:12px; border:1px solid #E0E0E0; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:6px;">

    <p style="font-size:19px; line-height:1.45; color:{USJ_BLUE}; font-weight:700; margin-bottom:10px;">
    Thématiques à prendre en considération pour répondre aux questions 1 et 2 :
    </p>

    <ul style="font-size:19px; line-height:1.45; color:{USJ_BLUE}; margin-top:0; margin-bottom:18px;">
        <li>Soutenabilité financière</li>
        <li>Gouvernance et Leadership (Gestion, relation, représentation, etc.)</li>
        <li>Stratégie académique et qualité d’enseignement</li>
        <li>Recherche et Innovation</li>
        <li>Ressources documentaires et Environnement digital</li>
        <li>Succès des étudiants (recrutement, accompagnement, services de support, employabilité, etc.)</li>
        <li>Ressources humaines</li>
        <li>Stratégie et mobilité internationales</li>
        <li>Mission sociétale</li>
        <li>Espace et infrastructures</li>
        <li>Environnement de travail</li>
        <li>Diversité et inclusion</li>
        <li>Développement Durable (ODD)</li>
        <li>Autre</li>
    </ul>

    <p style="font-size:19px; line-height:1.5; color:{USJ_BLUE}; font-weight:700; margin-bottom:12px;">
    1. <span style="color:#C00000; font-style:italic;">Éléments de réussite – Forces :</span>
    Quels sont les initiatives, processus ou projets universitaires actuels que vous appréciez le plus ?
    </p>

    <p style="font-size:19px; line-height:1.5; color:{USJ_BLUE}; font-weight:700; margin-bottom:12px;">
    2. <span style="color:#C00000; font-style:italic;">Initiatives à abandonner – Faiblesses :</span>
    Quels sont les initiatives, processus ou projets universitaires actuels qui devraient être améliorés ou abandonnés ?
    </p>

    <p style="font-size:19px; line-height:1.5; color:#0070C0; font-style:italic; margin-bottom:0;">
    Nous vous remercions de bien vouloir compléter le tableau ci-dessous en indiquant au 
    <strong>maximum cinq forces et cinq faiblesses</strong>, avec un 
    <strong>maximum de 30 mots par ligne.</strong>
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
            left_value = word_limited_text_area(
                label=f"{left_title} {i}",
                key=f"{section_key}_{left_title}_{i}",
                height=95,
                max_words=30
            )

        with col2:
            right_value = word_limited_text_area(
                label=f"{right_title} {i}",
                key=f"{section_key}_{right_title}_{i}",
                height=95,
                max_words=30
            )

        rows.append({
            left_title: left_value,
            right_title: right_value,
        })

    return rows


def render_swot_analysis():
    swot_data = {}

    annexe_b_src = image_to_base64(ANNEXE_B_PATH)

    annexe_b_hover_html = "Annexe&nbsp;B"
    if annexe_b_src:
        annexe_b_hover_html = f'<span class="annexe-a-hover">Annexe&nbsp;B<span class="annexe-a-popup"><img src="{annexe_b_src}" style="width:900px; height:auto; text-decoration:none; border-bottom:none;"></span></span>'

    annexe_c_src = image_to_base64(ANNEXE_C_PATH)

    annexe_c_hover_html = "Annexe&nbsp;C"
    if annexe_c_src:
        annexe_c_hover_html = f'<span class="annexe-a-hover">Annexe&nbsp;C<span class="annexe-a-popup"><img src="{annexe_c_src}" style="width:900px; height:auto; text-decoration:none; border-bottom:none;"></span></span>'



    swot_data["facteurs_internes"] = render_swot_table(
        section_key="swot_internal",
        left_title="Forces",
        right_title="Faiblesses"
    )

    st.session_state["quick_save_after_section_i_clicked"] = render_quick_save_button("quick_save_after_section_i")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    section_header("II- OPPORTUNITES ET MENACES – NIVEAU USJ")

    html_block(f"""
<div style="background-color:#ffffff; padding:24px 34px 10px 34px; border-radius:12px; border:1px solid #E0E0E0; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:6px;">
    <p style="font-size:19px; line-height:1.4; color:{USJ_BLUE}; font-weight:700; margin-bottom:10px;">
    Thématiques à prendre en considération pour répondre aux questions 3 et 4 :
    </p>

    <ul style="font-size:19px; line-height:1.45; color:{USJ_BLUE}; margin-top:0; margin-bottom:18px;">
        <li>Marché du travail et Associations professionnelles</li>
        <li>Concurrence avec les autres universités</li>
        <li>Intelligence artificielle</li>
        <li>Réputation et image</li>
        <li>Environnement politique et économique, émigration</li>
        <li>Autres</li>
    </ul>

    <p style="font-size:19px; line-height:1.5; color:{USJ_BLUE}; font-weight:700; margin-bottom:12px;">
    3. <span style="color:#C00000; font-style:italic;">Opportunités :</span>
    Quels sont les éléments, facteurs, tendances, pratiques externes qui pourraient améliorer votre expérience à l’université et contribuer à votre succès ?
    </p>

    <p style="font-size:22px; line-height:1.5; color:{USJ_BLUE}; font-weight:700; margin-bottom:12px;">
    4. <span style="color:#C00000; font-style:italic;">Menaces :</span>
    Quels sont les éléments, facteurs, tendances, pratiques externes qui pourraient menacer l’évolution de l’université ?
    </p>

    <p style="font-size:22px; line-height:1.5; color:#0070C0; font-style:italic; margin-bottom:0;">
    Nous vous remercions de bien vouloir compléter le tableau ci-dessous en indiquant au 
    <strong>maximum cinq opportunités et cinq menaces</strong>, avec un 
    <strong>maximum de 30 mots par ligne.</strong>
    </p>

</div>
""")

    swot_data["facteurs_externes"] = render_swot_table(
        section_key="swot_external",
        left_title="Opportunités",
        right_title="Menaces"
    )

    st.session_state["quick_save_after_section_ii_clicked"] = render_quick_save_button("quick_save_after_section_ii")

    return swot_data
    
def render_priorities_intro():
    
    html_block(f"""
<div style="background-color:#ffffff; padding:24px 34px 10px 34px; border-radius:12px; border:1px solid #E0E0E0; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:6px;">

    <p style="font-size:19px; line-height:1.5; color:{USJ_BLUE}; font-weight:700; margin-bottom:16px;">
    <span style="color:#C00000; font-style:italic;">Priorités :</span>
    Suite à l’analyse précédente, quelles sont les priorités qu’il faudrait intégrer au prochain plan stratégique ?
    </p>

    <p style="font-size:19px; line-height:1.5; color:#0070C0; font-style:italic; margin-bottom:0;">
    Nous vous remercions de bien vouloir compléter le tableau ci-dessous en indiquant au 
    <strong>maximum cinq priorités</strong>, avec un 
    <strong>maximum de 30 mots par ligne.</strong>
    </p>

</div>
""")

def render_priorities_table():
    priorities_initiatives = {}

    html_block(f"""
<div style="margin-top:10px; margin-bottom:0;">
    <div style="background-color:{USJ_BLUE}; color:white; padding:10px 14px; font-size:18px; font-weight:700; border:1px solid #595959;">
        PRIORITÉS – NIVEAU USJ
    </div>
</div>
""")

    for i in range(1, 6):
        priorities_initiatives[f"priorite_{i}"] = word_limited_text_area(
            label=f"Priorité {i}",
            key=f"priority_only_{i}",
            height=75,
            max_words=30
        )

    return priorities_initiatives

def render_pour_finir():
    pour_finir = {}
    read_only = st.session_state.get("read_only_submitted", False)

    html_block(f"""
<div style="background-color:#ffffff; padding:4px 0 2px 0; margin-bottom:2px;">
    <p style="font-size:18px; line-height:1.25; color:{USJ_RED}; font-weight:700; font-style:italic; margin-bottom:2px;">
    POUR FINIR. Nous vous remercions de compléter les phrases suivantes :
    </p>
</div>
""")

    phrases = [
        "Nous souhaitons que l’USJ soit reconnue pour …",
        "Nous souhaitons que nos étudiants disent que l’USJ …",
        "L’USJ serait un excellent lieu de travail si …",
    ]

    for i, phrase in enumerate(phrases, start=1):
        col_label, col_boxes, col_empty = st.columns([260, 520, 1], gap="small")

        with col_label:
            html_block(f"""
<div class="pour-finir-screen-label" style="font-size:17px; line-height:1.35; color:{USJ_BLUE}; font-weight:700; margin-top:8px; white-space:nowrap;">
    &bull; {phrase}
</div>
""")

        with col_boxes:
           
            for j in range(2):
                key = f"pour_finir_{i}_{j}"

                pour_finir[key] = st.text_input(
                    label=key,
                    key=key,
                    label_visibility="collapsed",
                    disabled=read_only
                )

    return pour_finir


def render_quick_save_button(key):
    if st.session_state.get("read_only_submitted", False):
        return False

    clicked = st.button(
        "Enregistrer et continuer plus tard",
        key=key
    )

    if clicked:
        st.session_state["last_quick_save_key"] = key

    if st.session_state.get("quick_save_success_key") == key:
        st.success(
            f"Vos réponses ont été enregistrées. Votre code pour reprendre plus tard : "
            f"{st.session_state.get('current_draft_code', '')}"
        )

    return clicked


def find_word_limit_errors(section_data, section_label, max_words):
    errors = []

    def check_value(value, path):
        if isinstance(value, dict):
            for key, sub_value in value.items():
                check_value(sub_value, f"{path} - {key}")
        elif isinstance(value, list):
            for index, item in enumerate(value, start=1):
                check_value(item, f"{path} - Ligne {index}")
        else:
            word_count = count_words(value)
            if word_count > max_words:
                errors.append(
                    f"{path} : {word_count} mots / maximum {max_words}"
                )

    check_value(section_data, section_label)
    return errors

def unlock_response_by_code(draft_code):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        UPDATE responses
        SET statut = 'Brouillon'
        WHERE draft_code = ?
    """, (draft_code.strip().upper(),))

    conn.commit()
    conn.close()


def delete_response_by_code(draft_code):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM responses
        WHERE draft_code = ?
    """, (draft_code.strip().upper(),))

    conn.commit()
    conn.close()

def save_admin_version_by_code(draft_code, admin_data):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE responses
        SET admin_data_json = ?
        WHERE draft_code = ?
        """,
        (
            json.dumps(admin_data, ensure_ascii=False),
            draft_code
        )
    )

    conn.commit()
    conn.close()



def safe_filename(value):
    value = str(value or "").strip()
    value = re.sub(r"[^A-Za-z0-9À-ÿ._-]+", "_", value)
    value = value.strip("_")
    return value or "groupe"


def _normalize_text_for_match(value):
    value = str(value or "").strip().lower()
    replacements = {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a",
        "ù": "u", "û": "u",
        "î": "i", "ï": "i",
        "ô": "o",
        "ç": "c",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def _clean_swot_answer(value):
    value = str(value or "").strip()
    value = re.sub(r"\s+", " ", value)
    value = value.strip("•*-–— ")
    return value


def _get_row_value_exact_or_safe(row, wanted_field):
    """
    Reads only the expected admin-edited answer field.
    This prevents the old long question labels from being placed under the wrong SWOT box.
    """
    if not isinstance(row, dict):
        return ""

    if wanted_field in row:
        return _clean_swot_answer(row.get(wanted_field, ""))

    wanted_norm = _normalize_text_for_match(wanted_field)

    # Safe fallback only for the same field family.
    for key, value in row.items():
        key_norm = _normalize_text_for_match(key)

        if wanted_norm == "forces" and key_norm in ["force", "forces"]:
            return _clean_swot_answer(value)

        if wanted_norm == "faiblesses" and key_norm in ["faiblesse", "faiblesses"]:
            return _clean_swot_answer(value)

        if wanted_norm == "opportunites" and ("opportunite" in key_norm or "opportunites" in key_norm):
            return _clean_swot_answer(value)

        if wanted_norm == "menaces" and ("menace" in key_norm or "menaces" in key_norm):
            return _clean_swot_answer(value)

    return ""


def _deduplicate_keep_order(values):
    cleaned = []
    seen = set()

    for value in values:
        value = _clean_swot_answer(value)

        if not value:
            continue

        # Do not inject old instruction/question text into the image.
        value_norm = _normalize_text_for_match(value)
        blocked_fragments = [
            "quels sont les elements",
            "maximum cinq",
            "merci de bien vouloir",
            "thematique",
            "opportunites : quels",
            "menaces : quels",
            "forces : quels",
            "faiblesses : quels",
        ]

        if any(fragment in value_norm for fragment in blocked_fragments):
            continue

        key = value_norm
        if key not in seen:
            cleaned.append(value)
            seen.add(key)

    return cleaned[:5]


def extract_admin_swot_values(admin_data):
    """
    Reads the live admin-edited answers only:
    - I - Forces et faiblesses: Forces, Faiblesses
    - II - Opportunités et menaces: Opportunités, Menaces
    """
    if not isinstance(admin_data, dict):
        admin_data = {}

    section_internal = admin_data.get("I - Forces et faiblesses", [])
    section_external = admin_data.get("II - Opportunités et menaces", [])

    def collect(section, field):
        values = []
        if isinstance(section, list):
            for row in section:
                values.append(_get_row_value_exact_or_safe(row, field))
        elif isinstance(section, dict):
            values.append(_get_row_value_exact_or_safe(section, field))
        return _deduplicate_keep_order(values)

    return {
        "forces": collect(section_internal, "Forces"),
        "faiblesses": collect(section_internal, "Faiblesses"),
        "opportunites": collect(section_external, "Opportunités"),
        "menaces": collect(section_external, "Menaces"),
    }


def _wrap_lines_for_box(text, max_chars=42, max_lines=3):
    text = _clean_swot_answer(text)
    wrapped = textwrap.wrap(
        text,
        width=max_chars,
        break_long_words=False,
        break_on_hyphens=False
    )

    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        wrapped[-1] = wrapped[-1].rstrip(" .,;:") + "…"

    return wrapped


def _draw_swot_box(ax, x, y, w, h, title, items, facecolor, edgecolor):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.035,rounding_size=0.18",
        linewidth=2.2,
        edgecolor=edgecolor,
        facecolor=facecolor,
        alpha=0.98,
        zorder=1
    )
    ax.add_patch(box)

    ax.text(
        x + 0.32,
        y + h - 0.35,
        title,
        fontsize=27,
        fontweight="bold",
        color=edgecolor,
        ha="left",
        va="center",
        zorder=2
    )

    ax.plot(
        [x + 0.32, x + w - 0.32],
        [y + h - 0.72, y + h - 0.72],
        color=edgecolor,
        linewidth=2.0,
        zorder=2
    )

    text_y = y + h - 1.05
    min_y = y + 0.34

    for item in _deduplicate_keep_order(items):
        lines = _wrap_lines_for_box(item, max_chars=45, max_lines=3)
        needed_height = 0.29 * len(lines) + 0.22

        if text_y - needed_height < min_y:
            break

        ax.text(
            x + 0.42,
            text_y,
            "•",
            fontsize=23,
            fontweight="bold",
            color=edgecolor,
            ha="left",
            va="top",
            zorder=2
        )

        line_y = text_y
        for line in lines:
            ax.text(
                x + 0.68,
                line_y,
                line,
                fontsize=17,
                color="#2B2B2B",
                ha="left",
                va="top",
                zorder=2
            )
            line_y -= 0.29

        text_y = line_y - 0.13


def create_swot_image_bytes(swot_values, group_name="groupe"):
    """
    Creates a clean SWOT image from the admin-modified answers.
    The title and group name are inside the image.
    """
    fig, ax = plt.subplots(figsize=(13.2, 8.0), dpi=180)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7.25)
    ax.axis("off")

    ax.text(
        5,
        7.05,
        "Matrice SWOT - Niveau USJ",
        fontsize=22,
        fontweight="bold",
        color=USJ_BLUE,
        ha="center",
        va="center"
    )

    ax.text(
        5,
        6.78,
        f"Groupe : {group_name}",
        fontsize=12,
        color="#4F4F4F",
        ha="center",
        va="center"
    )

    boxes = [
        (0.35, 3.75, 4.25, 2.70, "FORCES", swot_values.get("forces", []), "#DDEFF7", USJ_BLUE),
        (5.40, 3.75, 4.25, 2.70, "FAIBLESSES", swot_values.get("faiblesses", []), "#FBE3C3", USJ_RED),
        (0.35, 0.45, 4.25, 2.70, "OPPORTUNITÉS", swot_values.get("opportunites", []), "#E2F2D3", "#2F6B2F"),
        (5.40, 0.45, 4.25, 2.70, "MENACES", swot_values.get("menaces", []), "#F4C6C4", USJ_RED),
    ]

    for box_args in boxes:
        _draw_swot_box(ax, *box_args)

    center_circle = Circle(
        (5.0, 3.42),
        0.52,
        facecolor="white",
        edgecolor="#C7CDD6",
        linewidth=2.0,
        zorder=10
    )
    ax.add_patch(center_circle)

    ax.text(
        5.0,
        3.42,
        "SWOT",
        fontsize=19,
        fontweight="bold",
        color=USJ_BLUE,
        ha="center",
        va="center",
        zorder=11
    )

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=180, bbox_inches="tight", facecolor="white", pad_inches=0.08)
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()


def render_swot_image_download_block(updated_admin_data, selected_row):
    swot_values = extract_admin_swot_values(updated_admin_data)

    group_name = selected_row.get("respondent_name", "") if hasattr(selected_row, "get") else ""
    group_unit = selected_row.get("respondent_unit", "") if hasattr(selected_row, "get") else ""
    draft_code = selected_row.get("draft_code", "") if hasattr(selected_row, "get") else ""

    display_group_name = " - ".join(
        [part for part in [str(group_name).strip(), str(group_unit).strip()] if part]
    )

    if not display_group_name:
        display_group_name = str(draft_code).strip() or "groupe"

    file_name = f"SWOT_{safe_filename(display_group_name)}.png"
    has_values = any(swot_values[key] for key in swot_values)

    safe_code = safe_filename(str(draft_code))
    button_key = f"generate_swot_image_{safe_code}"
    state_key = f"show_swot_image_{safe_code}"

    st.markdown("---")

    if state_key not in st.session_state:
        st.session_state[state_key] = False

    if st.button("Générer l’image SWOT", key=button_key):
        st.session_state[state_key] = True

    # Nothing appears before the admin clicks the button.
    if not st.session_state[state_key]:
        return

    if not has_values:
        st.warning("Aucune réponse admin n’est disponible pour générer l’image SWOT.")
        return

    image_bytes = create_swot_image_bytes(
        swot_values=swot_values,
        group_name=display_group_name
    )

    # Reduced display size inside the admin page.
    st.image(image_bytes, width=1050)

    st.download_button(
        label="Télécharger l’image SWOT",
        data=image_bytes,
        file_name=file_name,
        mime="image/png",
        key=f"download_swot_image_{safe_code}"
    )


def main():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    apply_usj_style()
    init_db()

    st.session_state.setdefault("n_autres_rows", 1)
    st.session_state.setdefault("access_granted", False)
    st.session_state.setdefault("current_draft_code", "")
    st.session_state.setdefault("admin_mode", False)
    st.session_state.setdefault("read_only_submitted", False)

    render_first_page_header()

    ADMIN_CODE = "USJ-ADMIN-2032"

    if st.session_state.get("current_draft_code", "").strip().upper() == ADMIN_CODE:
        st.session_state["access_granted"] = True
        st.session_state["admin_mode"] = True

    if st.session_state.get("admin_mode", False):
        st.markdown("## Admin download")

        st.write("DB path:", DB_PATH.resolve())
        st.write("DB exists:", DB_PATH.exists())

        if not DB_PATH.exists():
            st.error("Database not found in this app environment.")
            st.stop()

        df = load_responses()

        if df.empty:
            st.warning("Database exists, but no responses are saved.")
            st.stop()

        st.success(f"{len(df)} response(s) found.")

        st.markdown("### Gestion des réponses")

        admin_df = df.copy()
        admin_df["display_label"] = (
            admin_df["draft_code"].fillna("") + " | " +
            admin_df["respondent_name"].fillna("") + " | " +
            admin_df["respondent_unit"].fillna("") + " | " +
            admin_df["statut"].fillna("")
        )

        selected_response = st.selectbox(
            "Choisir une réponse",
            options=admin_df["display_label"].tolist()
        )

        selected_draft_code = selected_response.split(" | ")[0].strip()

        selected_row = admin_df[admin_df["draft_code"] == selected_draft_code].iloc[0]

        original_data = json.loads(selected_row["data_json"]) if selected_row["data_json"] else {}

        if pd.notna(selected_row.get("admin_data_json", None)) and selected_row.get("admin_data_json"):
            admin_data = json.loads(selected_row["admin_data_json"])
        else:
            admin_data = {}

        col_group_title, col_admin_title = st.columns(2)

        with col_group_title:
            html_block(f"""
<div style="
background-color:{USJ_LIGHT_BLUE};
padding:14px 22px;
border-radius:10px;
border-left:7px solid {USJ_BLUE};
box-shadow:0 2px 10px rgba(0,0,0,0.08);
margin-top:12px;
margin-bottom:18px;
">
<h2 style="font-size:26px; color:{USJ_BLUE}; margin:0; font-weight:700;">
    Réponse des groupes
</h2>
</div>
""")

        with col_admin_title:
            html_block(f"""
<div style="
background-color:#F8F3F5;
padding:14px 22px;
border-radius:10px;
border-left:7px solid {USJ_RED};
box-shadow:0 2px 10px rgba(0,0,0,0.08);
margin-top:12px;
margin-bottom:18px;
">
<h2 style="font-size:26px; color:{USJ_RED}; margin:0; font-weight:700;">
    Version modifiée après présentation des réponses
</h2>
</div>
""")

        section_map = {
            "I - Forces et faiblesses": ("swot_analysis", "facteurs_internes"),
            "II - Opportunités et menaces": ("swot_analysis", "facteurs_externes"),
            "III - Priorités": ("priorities_initiatives", None),
            "IV - Conclusion": ("pour_finir", None),
        }

        updated_all_admin_data = dict(admin_data) if isinstance(admin_data, dict) else {}

        def render_admin_title_bar(title, color):
            st.markdown(
                f'''
<div style="
background-color:{color};
color:white;
padding:10px 14px;
font-size:18px;
font-weight:700;
text-align:center;
border-radius:6px;
margin-top:8px;
margin-bottom:12px;
box-shadow:0 2px 6px rgba(0,0,0,0.05);
">
{title}
</div>
''',
                unsafe_allow_html=True
            )

        def render_original_answer_box(value):
            safe_value = html_lib.escape(str(value or "")).replace("\n", "<br>")
            if not safe_value.strip():
                safe_value = "&nbsp;"

            st.markdown(
                f'''
<div style="
background-color:#E3DED9;
padding:12px 16px;
border-radius:0px;
border:1.5px solid #595959;
margin-bottom:12px;
min-height:95px;
font-size:16px;
line-height:1.35;
color:#000000;
box-sizing:border-box;
">
{safe_value}
</div>
''',
                unsafe_allow_html=True
            )

        def render_admin_edit_box(label, value, key, height=95):
            return st.text_area(
                label=label,
                value=str(value) if value else "",
                height=height,
                key=key,
                label_visibility="collapsed"
            )

        def get_existing_admin_section(section_label, original_section):
            existing = updated_all_admin_data.get(section_label)
            if existing in [None, "", [], {}]:
                return original_section
            return existing

        def render_list_section(section_label, original_section):
            existing_admin_section = get_existing_admin_section(section_label, original_section)
            updated_admin_section = []

            if not isinstance(original_section, list):
                original_section = []

            # Use the real expected fields for the SWOT sections.
            # This avoids showing old long question labels or wrong keys from older saved drafts.
            if section_label == "I - Forces et faiblesses":
                field_names = ["Forces", "Faiblesses"]
            elif section_label == "II - Opportunités et menaces":
                field_names = ["Opportunités", "Menaces"]
            else:
                field_names = []
                for row in original_section:
                    if isinstance(row, dict):
                        for key in row.keys():
                            if key not in field_names:
                                field_names.append(key)

            def get_value_from_row(row, expected_field):
                if not isinstance(row, dict):
                    return ""

                # Exact match first.
                if expected_field in row:
                    return row.get(expected_field, "")

                expected_lower = expected_field.lower()

                # Robust match for older keys such as long question labels.
                for key, value in row.items():
                    key_lower = str(key).lower()
                    if expected_lower in key_lower:
                        return value

                # Accent-safe fallback for Opportunités / Menaces.
                if expected_field == "Opportunités":
                    for key, value in row.items():
                        if "opportun" in str(key).lower():
                            return value

                if expected_field == "Menaces":
                    for key, value in row.items():
                        if "menace" in str(key).lower():
                            return value

                return ""

            def get_admin_value(saved_admin_row, expected_field, original_value):
                if not isinstance(saved_admin_row, dict):
                    return original_value

                if expected_field in saved_admin_row:
                    return saved_admin_row.get(expected_field, original_value)

                expected_lower = expected_field.lower()

                for key, value in saved_admin_row.items():
                    key_lower = str(key).lower()
                    if expected_lower in key_lower:
                        return value

                if expected_field == "Opportunités":
                    for key, value in saved_admin_row.items():
                        if "opportun" in str(key).lower():
                            return value

                if expected_field == "Menaces":
                    for key, value in saved_admin_row.items():
                        if "menace" in str(key).lower():
                            return value

                return original_value

            number_of_rows = 5
            if original_section:
                number_of_rows = max(5, len(original_section))

            for field_name in field_names:
                col_original_section, col_admin_section = st.columns(2)

                with col_original_section:
                    render_admin_title_bar(field_name, USJ_BLUE)

                with col_admin_section:
                    render_admin_title_bar(field_name, USJ_RED)

                for i in range(1, number_of_rows + 1):
                    row = original_section[i - 1] if i <= len(original_section) else {}
                    original_value = get_value_from_row(row, field_name)

                    saved_admin_row = {}
                    if (
                        isinstance(existing_admin_section, list)
                        and len(existing_admin_section) >= i
                        and isinstance(existing_admin_section[i - 1], dict)
                    ):
                        saved_admin_row = existing_admin_section[i - 1]

                    admin_value = get_admin_value(saved_admin_row, field_name, original_value)

                    while len(updated_admin_section) < i:
                        updated_admin_section.append({})

                    col_original_answer, col_admin_answer = st.columns(2)

                    with col_original_answer:
                        st.markdown(
                            f'<div style="font-size:18px; font-weight:700; color:{USJ_BLUE}; margin:4px 0 6px 0;">Réponse {i}</div>',
                            unsafe_allow_html=True
                        )
                        render_original_answer_box(original_value)

                    with col_admin_answer:
                        st.markdown(
                            f'<div style="font-size:18px; font-weight:700; color:{USJ_RED}; margin:4px 0 6px 0;">Réponse {i}</div>',
                            unsafe_allow_html=True
                        )
                        updated_admin_section[i - 1][field_name] = render_admin_edit_box(
                            label=f"{section_label}_{field_name}_{i}",
                            value=admin_value,
                            key=f"admin_edit_{selected_draft_code}_{section_label}_{field_name}_{i}",
                            height=95
                        )

                st.markdown("<br>", unsafe_allow_html=True)

            return updated_admin_section

        def render_dict_section(section_label, original_section):
            existing_admin_section = get_existing_admin_section(section_label, original_section)
            updated_admin_section = {}

            if not isinstance(original_section, dict) or not original_section:
                st.info("Aucune réponse saisie pour cette section.")
                return original_section

            for key, original_value in original_section.items():
                if isinstance(existing_admin_section, dict):
                    admin_value = existing_admin_section.get(key, original_value)
                else:
                    admin_value = original_value

                col_original_answer, col_admin_answer = st.columns(2)

                with col_original_answer:
                    render_admin_title_bar(key, USJ_BLUE)
                    render_original_answer_box(original_value)

                with col_admin_answer:
                    render_admin_title_bar(key, USJ_RED)
                    updated_admin_section[key] = render_admin_edit_box(
                        label=f"{section_label}_{key}",
                        value=admin_value,
                        key=f"admin_edit_{selected_draft_code}_{section_label}_{key}",
                        height=95
                    )

            return updated_admin_section

        def render_conclusion_section(section_label, original_section):
            existing_admin_section = get_existing_admin_section(section_label, original_section)
            updated_admin_section = {}

            if not isinstance(original_section, dict):
                original_section = {}

            if not isinstance(existing_admin_section, dict):
                existing_admin_section = {}

            phrases = [
                "Nous souhaitons que l’USJ soit reconnue pour …",
                "Nous souhaitons que nos étudiants disent que l’USJ …",
                "L’USJ serait un excellent lieu de travail si …",
            ]

            for i, phrase in enumerate(phrases, start=1):
                st.markdown(
                    f"""
<div style="
font-size:18px;
font-weight:700;
color:{USJ_BLUE};
margin-top:12px;
margin-bottom:8px;
">
&bull; {phrase}
</div>
""",
                    unsafe_allow_html=True
                )

                for j in range(2):
                    key = f"pour_finir_{i}_{j}"
                    original_value = original_section.get(key, "")
                    admin_value = existing_admin_section.get(key, original_value)

                    col_original_answer, col_admin_answer = st.columns(2)

                    with col_original_answer:
                        render_admin_title_bar(f"Réponse {j + 1}", USJ_BLUE)
                        render_original_answer_box(original_value)

                    with col_admin_answer:
                        render_admin_title_bar(f"Réponse admin {j + 1}", USJ_RED)
                        updated_admin_section[key] = render_admin_edit_box(
                            label=f"{section_label}_{key}",
                            value=admin_value,
                            key=f"admin_edit_{selected_draft_code}_{section_label}_{key}",
                            height=95
                        )

            return updated_admin_section

        for section_label, (main_key, sub_key) in section_map.items():
            st.markdown("---")
            section_header(section_label)

            if sub_key:
                original_section = original_data.get(main_key, {}).get(sub_key, [])
            else:
                original_section = original_data.get(main_key, {})

            if section_label == "IV - Conclusion":
                updated_all_admin_data[section_label] = render_conclusion_section(section_label, original_section)
            elif isinstance(original_section, list):
                updated_all_admin_data[section_label] = render_list_section(section_label, original_section)
            elif isinstance(original_section, dict):
                updated_all_admin_data[section_label] = render_dict_section(section_label, original_section)
            else:
                col_original_answer, col_admin_answer = st.columns(2)

                existing_admin_section = get_existing_admin_section(section_label, original_section)

                with col_original_answer:
                    render_admin_title_bar("Réponse originale", USJ_BLUE)
                    render_original_answer_box(original_section)

                with col_admin_answer:
                    render_admin_title_bar("Version admin", USJ_RED)
                    updated_all_admin_data[section_label] = render_admin_edit_box(
                        label=section_label,
                        value=existing_admin_section,
                        key=f"admin_edit_{selected_draft_code}_{section_label}",
                        height=95
                    )

            if section_label == "II - Opportunités et menaces":
                render_swot_image_download_block(updated_all_admin_data, selected_row)

        st.markdown("---")

        if st.button(
            "Enregistrer toutes les versions admin",
            key=f"save_admin_all_{selected_draft_code}"
        ):
            save_admin_version_by_code(selected_draft_code, updated_all_admin_data)
            st.success("Versions admin enregistrées sans modifier les réponses originales du groupe.")
            st.rerun()

        st.stop()

    if not st.session_state["access_granted"]:
        col_code, col_button = st.columns([2, 1])

        def submit_login_code():
            st.session_state["enter_form_clicked"] = True


        with col_code:
            login_code = st.text_input(
                "Mot de passe reçu par email",
                placeholder="",
                key="login_draft_code",
                on_change=submit_login_code
            )

        with col_button:
            st.markdown("<br>", unsafe_allow_html=True)

            enter_form = (
                st.button("Accéder au rapport")
                or st.session_state.pop("enter_form_clicked", False)
            )

        if enter_form:
            cleaned_code = login_code.strip().upper()
            
            if not cleaned_code:
                st.warning("Veuillez saisir un code personnel de reprise avant d’accéder au formulaire.")
                return

            if cleaned_code == ADMIN_CODE:
                st.session_state["access_granted"] = True
                st.session_state["admin_mode"] = True
                st.session_state["current_draft_code"] = cleaned_code
                st.rerun()

            if cleaned_code not in AUTHORIZED_TEST_CODES:
                st.error("Merci d'utiliser le mot de passe reçu par email.")
                return

            draft = load_existing_draft_by_code(cleaned_code)

            if draft:
                preload_draft_into_session(draft)
                st.session_state["current_draft_code"] = cleaned_code
                st.session_state["access_granted"] = True

                if draft.get("loaded_statut") == "Soumis":
                    st.session_state["read_only_submitted"] = True
                else:
                    st.session_state["read_only_submitted"] = False

                st.success("Vos réponses enregistrées ont été chargées.")
                st.rerun()
            else:
                st.session_state["current_draft_code"] = cleaned_code
                st.session_state["access_granted"] = True
                st.session_state["read_only_submitted"] = False
                st.session_state["responsable"] = AUTHORIZED_TEST_CODES[cleaned_code]["responsable"]
                st.session_state["institution"] = AUTHORIZED_TEST_CODES[cleaned_code]["institution"]
                st.info("Nouveau formulaire ouvert. Vous pouvez commencer à remplir vos réponses.")
                st.rerun()

        st.stop()
    mode = "Saisir une réponse"

if mode == "Saisir une réponse":
    with st.container():

        st.markdown("## Informations générales")

        col1, col2, col3 = st.columns(3)

        with col1:
            focus_group_options = [
                "Focus groupe 1",
                "Focus groupe 2",
                "Focus groupe 3",
                "Focus groupe 4",
                "Focus groupe 5",
            ]

            institution = st.selectbox(
                "Focus groupe",
                options=focus_group_options,
                key="institution"
            )

        with col2:
            responsable = st.text_input(
                "Responsable",
                key="responsable",
                disabled=True
            )

        with col3:
            st.text_input(
                "Date",
                value="2026-06-04",
                disabled=True
            )
            response_date = "2026-06-04"

        st.markdown("---")

        section_header("Introduction")
        render_fixed_introduction()

        st.divider()
    
       
    # Section II removed for Focus Group version
    stakeholder_rows = []
    quick_save_after_stakeholders = False

    # Section III removed for Focus Group version
    internal_analysis = {}
    quick_save_after_internal = False

    # Section IV removed for Focus Group version
    external_analysis = {}
    quick_save_after_external = False

    section_header("I- FORCES ET FAIBLESSES – NIVEAU USJ")
    render_swot_intro()
    swot_analysis = render_swot_analysis()
    quick_save_after_swot = False

    st.divider()

    section_header("III - PRIORITES – Niveau USJ")
    render_priorities_intro()
    priorities_initiatives = render_priorities_table()
    quick_save_after_priorities = render_quick_save_button("quick_save_after_priorities")

    st.divider()

    section_header("IV- CONCLUSION")
    pour_finir = render_pour_finir()

    st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state.get("read_only_submitted", False):
        st.info(
            "Le rapport de votre institution a déjà été envoyé. "
            "Les modifications ne sont plus possibles."
        )
        save_draft = False
        submit_final = False

        st.markdown("<br>", unsafe_allow_html=True)
        render_print_icon_button()

    else:
        col_save_final, col_save_empty = st.columns(
            [1.25, 2.75],
            vertical_alignment="center"
        )
                with col_save_final:
                    save_draft = st.button(
                        "Enregistrer et continuer plus tard",
                        key="save_draft_button",
                        use_container_width=True
                    )

                st.markdown('<hr class="final-action-line">', unsafe_allow_html=True)

                col_submit_final, col_print_final, col_right_final = st.columns(
                    [1.25, 1.25, 1.50],
                    vertical_alignment="center"
                )

                with col_submit_final:
                    submit_final = st.button(
                        "Envoyer la version finale\u00A0uniquement",
                        key="submit_final_button",
                        type="primary",
                        use_container_width=True
                    )

                with col_print_final:
                    print_icon_src = image_to_base64(PRINT_ICON_PATH)

                    if print_icon_src:
                        components.html(
                            f"""
                            <div style="
                                height:150px;
                                display:flex;
                                align-items:center;
                                justify-content:center;
                                overflow:visible;
                                padding:0;
                                margin:0;
                            ">
                                <button onclick="window.parent.print()" title="Imprimer / Enregistrer en PDF" style="
                                    background-color:transparent;
                                    border:none;
                                    cursor:pointer;
                                    padding:0;
                                    margin:0;
                                    width:130px;
                                    height:130px;
                                    display:flex;
                                    align-items:center;
                                    justify-content:center;
                                ">
                                    <img src="{print_icon_src}" alt="Imprimer / Enregistrer en PDF" style="
                                        width:130px;
                                        height:130px;
                                        object-fit:contain;
                                        display:block;
                                    ">
                                </button>
                            </div>
                            """,
                            height=155
                        )

        quick_save_clicked = any([
            quick_save_after_stakeholders,
            quick_save_after_internal,
            quick_save_after_external,
            quick_save_after_swot,
            quick_save_after_priorities,
            st.session_state.get("quick_save_after_section_i_clicked", False),
            st.session_state.get("quick_save_after_section_ii_clicked", False),
        ])

        if save_draft or submit_final or quick_save_clicked:
            word_limit_errors = []

            word_limit_errors.extend(
                find_word_limit_errors(
                    internal_analysis,
                    "Section III - Analyse interne",
                    max_words=500
                )
            )

            word_limit_errors.extend(
                find_word_limit_errors(
                    external_analysis,
                    "Section IV - Analyse externe",
                    max_words=500
                )
            )

            word_limit_errors.extend(
                find_word_limit_errors(
                    swot_analysis,
                    "Section V - Analyse SWOT",
                    max_words=30
                )
            )

            word_limit_errors.extend(
                find_word_limit_errors(
                    priorities_initiatives,
                    "Section VI - Priorités stratégiques et initiatives",
                    max_words=30
                )
            )

            if word_limit_errors:
                st.error(
                    "Certaines réponses dépassent la limite autorisée. "
                    "Merci de les réduire avant l’enregistrement."
                )

                for error in word_limit_errors:
                    st.warning(error)

                st.stop()

            statut = "Soumis" if submit_final else "Brouillon"

            metadata = {
                "institution": institution,
                "responsable": responsable,
                "email": "",
                "response_date": str(response_date),
                "statut": statut,
                "draft_code": st.session_state.get("current_draft_code", ""),
            }

            data = {
                "metadata": metadata,
                "introduction": {},
                "stakeholders": {
                    "rows": stakeholder_rows,
                },
                "internal_analysis": {},
                "external_analysis": {},
                "swot_analysis": swot_analysis,
                "priorities_initiatives": priorities_initiatives,
                "pour_finir": pour_finir,
            }

            try:
                draft_code = save_response(metadata, data)
                st.session_state["current_draft_code"] = draft_code

                if quick_save_clicked:
                    st.session_state["quick_save_success_key"] = st.session_state.get("last_quick_save_key", "")
                    st.rerun()

                if save_draft or quick_save_clicked:
                    st.success(
                        f"Vos réponses ont été enregistrées. Votre code pour reprendre plus tard : {draft_code}"
                    )

                if submit_final:
                    st.session_state["read_only_submitted"] = True
                    st.success("Merci.\nVos réponses ont été enregistrées.")
                    st.rerun()

            except ValueError as e:
                st.error(str(e))


if __name__ == "__main__":
    main()
