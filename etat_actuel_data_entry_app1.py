#!/usr/bin/env python
# coding: utf-8

import sqlite3
import json
import base64
import html as html_lib
from datetime import datetime
from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


APP_TITLE = "PLAN STRATÉGIQUE USJ 2032"
DB_PATH = Path("etat_actuel_responses.db")
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
    "USJ-HS-2032": {
        "responsable": "Hadi Sawaya",
        "institution": "ESIB",
    },
    "USJ-IM-2032": {
        "responsable": "Irma Majdalani",
        "institution": "FSE",
    },
    "USJ-NRH-2032": {
        "responsable": "Nadine Riachi Haddad",
        "institution": "FDLT",
    },
    "USJ-UEH-2032": {
        "responsable": "Ursula El Hage",
        "institution": "FGM",
    },
    "USJ-LKG-2032": {
        "responsable": "Lina Koleilat Ghalayini",
        "institution": "FSE",
    },
    "USJ-TH-2032": {
        "responsable": "Tarek Halabi",
        "institution": "",
    },
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
            data_json TEXT NOT NULL
        )
    """)

    existing_cols = [row[1] for row in cur.execute("PRAGMA table_info(responses)").fetchall()]

    if "statut" not in existing_cols:
        cur.execute("ALTER TABLE responses ADD COLUMN statut TEXT DEFAULT 'Brouillon'")

    if "draft_code" not in existing_cols:
        cur.execute("ALTER TABLE responses ADD COLUMN draft_code TEXT")

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
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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

    for i, row in enumerate(data.get("priorities_initiatives", []), start=1):
        st.session_state[f"priority_{i}"] = row.get("priorite_strategique", "")
        st.session_state[f"initiative_{i}_1"] = row.get("initiative_1", "")
        st.session_state[f"initiative_{i}_2"] = row.get("initiative_2", "")
        st.session_state[f"initiative_{i}_3"] = row.get("initiative_3", "")

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
html, body, [class*="css"], [class*="st-"], .stApp {{
    font-family: Candara, Calibri, Arial, sans-serif !important;
    color: {USJ_TEXT};
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
    background-color: #EAF2F8 !important;
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

section[data-testid="stSidebar"] {{
    background-color: {USJ_LIGHT_BLUE};
    border-right: 4px solid {USJ_BLUE};
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
    margin-top: -6px !important;
}}

/* =========================
   CLEAN PRINT / PDF MODE
========================= */

.print-answer-text {{
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
<div style="background-color:{USJ_LIGHT_BLUE}; padding:12px 18px; border-radius:10px; border-left:7px solid {USJ_BLUE}; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-top:14px; margin-bottom:18px;">
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
                height:100px;
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
                    width:82px;
                    height:82px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                ">
                    <img src="{print_icon_src}" alt="Imprimer / Enregistrer en PDF" style="
                        width:150px;
                        height:150px;
                        object-fit:contain;
                        display:block;
                    ">
                </button>
            </div>
            """,
            height=110
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
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    L’enseignement supérieur est aujourd’hui confronté à des transformations rapides, à des contraintes économiques croissantes et à une intensification de la concurrence, tant nationale qu’internationale. Les évolutions technologiques, les attentes accrues des étudiants et des parties prenantes, ainsi que les exigences renforcées en matière de qualité et de performance, imposent une réflexion stratégique à la fois rigoureuse et collective. Les universités sont ainsi appelées à réinterroger en profondeur leurs modèles académiques, organisationnels et opérationnels.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    <strong>Le Plan stratégique USJ 2032</strong> s’inscrit dans cette dynamique. Il constitue une feuille de route institutionnelle visant à traduire la mission, la vision et les valeurs de l’USJ en priorités stratégiques claires, en objectifs cohérents et en initiatives concrètes, capables de renforcer durablement son positionnement, sa résilience ainsi que son impact académique et sociétal.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    L’élaboration de ce plan stratégique se décline en plusieurs étapes (voir le schéma ci-dessous), dont la première est consacrée à <strong>l’analyse de données relatives à l’état actuel de l’Université</strong>. L’ensemble des acteurs de l’Université, ainsi que les parties prenantes, sont invités à y contribuer. Ce rapport a pour objectif de vous accompagner dans la formulation de constats partagés, des pratiques existantes et des expériences vécues, afin d’identifier <strong>les forces à consolider, les fragilités à traiter, les opportunités de développement et les risques à maîtriser à l’échelle de l’Université</strong>.
    </p>

    {image_html}

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Ce rapport vise ainsi à produire <strong>deux résultats principaux</strong>. Le premier consiste en une <strong>analyse SWOT</strong> (Strengths, Weaknesses, Opportunities, Threats) <strong>de l’Université</strong>, fondée sur la réalité vécue au sein de votre institution. Sur la base de cette analyse, vous serez amenés à proposer <strong>des priorités stratégiques ainsi que des initiatives (ou projets), toujours à l’échelle de l’Université</strong>, constituant ainsi le second résultat attendu.
    </p>

    <p style="font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:5px;">
    Le document comprend 6 parties :
    </p>

<div style="font-size:17px; line-height:1.75; color:{USJ_BLUE}; margin-top:5px;">

    I. Introduction<br>

    II. Identification des parties prenantes à consulter pour écrire le rapport<br>

    III. Analyse interne : cette analyse mène à produire les éléments Forces et Faiblesses de l’analyse SWOT<br>

    IV. Analyse externe : cette analyse mène à produire les éléments Opportunités et Menaces de l’analyse SWOT<br>

    V. Analyse SWOT<br>

    VI. Propositions de Priorités stratégiques et Initiatives

</div>
    <p style="font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-top:22px; margin-bottom:8px;">
    Pour toute information supplémentaire ou support, contacter :
</p>

<p style="font-size:16px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:0;">
    <p style="font-size:17px; line-height:1.75; color:{USJ_BLUE}; margin-top:22px; margin-bottom:0;">
    M. Hadi Sawaya – Coordinateur de l’Unité Assurance Qualité : hadi.sawaya@usj.edu.lb<br>
    Mme Irma Majdalani – Expert qualité – Unité Assurance qualité : irma.majdalani@usj.edu.lb<br>
    Mme Nadine Riachi Haddad – Secrétaire général : secg@usj.edu.lb<br>
    Mme Ursula El Hage – Directeur du Service de l’insertion professionnelle : ursula.hage@usj.edu.lb<br>
    Mme Lina Koleilat Ghalayini – Chef de projets – Unité Assurance qualité : lina.koleilat@usj.edu.lb
</p>
</div>
""")


def render_stakeholder_intro():
    annexe_a_src = image_to_base64(ANNEXE_A_PATH)

    annexe_hover_html = f'<span class="annexe-a-hover">Annexe&nbsp;A<span class="annexe-a-popup"><img src="{annexe_a_src}" style="width:720px; height:auto;"></span></span>'

    html_block(f"""
<div style="background-color:#ffffff; padding:20px 34px 12px 34px; border-radius:12px; border-left:none; border-top:none; border-bottom:none; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:12px;">

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:16px;">
    Le rapport d’analyse des données existantes est le fruit d’une consultation menée auprès de l’ensemble des parties prenantes de l’institution. L’identification et la prise en compte de leurs attentes constituent un levier essentiel pour la réussite du processus de planification stratégique. En raison de la diversité de leurs rôles, de leurs intérêts et de leur degré d’influence, les parties prenantes apportent des perspectives complémentaires, qui enrichissent l’analyse stratégique et favorisent l’adhésion aux orientations retenues. L’analyse de leurs attentes vise à mieux comprendre leurs besoins, leurs priorités et leur niveau d’influence, afin d’éclairer les choix stratégiques de l’USJ. Cette démarche participative est essentielle pour garantir une vision partagée, réaliste et représentative de la diversité de la communauté universitaire.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:16px;">
    Il est proposé aux institutions de consulter notamment les parties prenantes suivantes : le conseil de l’institution, le conseil d’orientation stratégique, les employeurs, les étudiants, les enseignants, le PSG, les anciens, ainsi que toute autre partie jugée pertinente et engagée dans l’institution (Exemple de parties prenantes en {annexe_hover_html}).
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:16px;">
    L’institution est libre d’organiser, selon les modalités qu’elle juge les plus appropriées, une ou plusieurs réunions avec les parties prenantes, ou, dans certains cas, de recourir à des questionnaires.
    </p>

    <p style="font-size:17px; line-height:1.55; color:#0070C0; font-weight:700; font-style:italic; margin-bottom:16px;">
    Le tableau ci-dessous doit être dûment complété.
    </p>
</div>
""")

def render_stakeholder_table():
    read_only = st.session_state.get("read_only_submitted", False)

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

    if "stakeholder_row_types" not in st.session_state:
        st.session_state["stakeholder_row_types"] = ["standard"] * 8

    stakeholder_rows = []

    col0, col1, col2, col3 = st.columns([1.4, 1.6, 1.6, 1.8])

    headers = [
        "Parties prenantes consultées",
        "Nom",
        "Poste",
        "Organisme d’affiliation",
    ]

    for col, header in zip([col0, col1, col2, col3], headers):
        with col:
            html_block(f"""
<div style="background:{USJ_BLUE}; color:white; padding:10px 12px; height:40px; display:flex; align-items:center; font-weight:700; border-radius:6px;">
    {header}
</div>
""")

    for i, row_type in enumerate(st.session_state["stakeholder_row_types"], start=1):
        col0, col1, col2, col3 = st.columns([1.4, 1.6, 1.6, 1.8])

        with col0:
            if row_type == "autres":
                categorie = st.text_input(
                    "Autre partie prenante",
                    key=f"stakeholder_category_autre_{i}",
                    label_visibility="collapsed",
                    placeholder="Autre, préciser",
                    disabled=read_only
                )
            else:
                categorie = st.selectbox(
                    "Parties prenantes consultées",
                    options=stakeholder_options,
                    index=None,
                    placeholder="Choisir une catégorie",
                    key=f"stakeholder_category_{i}",
                    label_visibility="collapsed",
                    disabled=read_only
                )

        with col1:
            nom = st.text_input(
                "Nom",
                key=f"stakeholder_nom_{i}",
                label_visibility="collapsed",
                placeholder="",
                disabled=read_only
            )

        with col2:
            poste = st.text_input(
                "Poste",
                key=f"stakeholder_poste_{i}",
                label_visibility="collapsed",
                placeholder="",
                disabled=read_only
            )

        with col3:
            organisme = st.text_input(
                "Organisme d’affiliation",
                key=f"stakeholder_organisme_{i}",
                label_visibility="collapsed",
                placeholder="",
                disabled=read_only
            )

        if any([
            (categorie or "").strip(),
            nom.strip(),
            poste.strip(),
            organisme.strip()
        ]):
            stakeholder_rows.append({
                "categorie": (categorie or "").strip(),
                "nom": nom.strip(),
                "poste": poste.strip(),
                "organisme_affiliation": organisme.strip(),
            })

    if not read_only:
        col_add1, col_add2, _ = st.columns([1.3, 2.2, 3.3])

        with col_add1:
            if st.button("Ajouter une ligne", key="add_stakeholder_standard"):
                st.session_state["stakeholder_row_types"].append("standard")
                st.rerun()

        with col_add2:
            if st.button("Ajouter une ligne Autre", key="add_stakeholder_autres"):
                st.session_state["stakeholder_row_types"].append("autres")
                st.rerun()

    return stakeholder_rows
    
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

    value = st.text_area(
        label=label,
        key=key,
        height=height,
        placeholder=f"Merci de saisir votre réponse ici (au maximum {max_words} mots)",
        label_visibility="collapsed",
        disabled=read_only
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
<div style="min-height:24px; color:#8B1538; font-weight:700; font-size:14px; margin-top:-6px; margin-bottom:8px;">
    ⚠ Vous avez saisi {word_count} mots. Maximum autorisé : {max_words} mots.
</div>
""")
        else:
            html_block(f"""
<div style="min-height:24px; color:#595959; font-size:13px; margin-top:-6px; margin-bottom:8px;">
    {word_count}/{max_words} mots
</div>
""")

    return value


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
        html_block('<div class="print-answer-block">')

        html_block(f"""
<div style="padding:2px 0px; margin-top:2px; margin-bottom:4px;">
    <p style="font-size:17px; line-height:1.25; color:{USJ_RED}; font-weight:700; margin:0;">
        • {theme}
    </p>
</div>
""")

        internal_analysis[theme] = word_limited_text_area(
            label=theme,
            key=f"internal_{theme}",
            height=300,
            max_words=500
        )
        html_block('</div>')

    return internal_analysis
    
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
<div style="background-color:#ffffff; padding:24px 34px 10px 34px; border-radius:12px; border-left:none; border-top:none; border-bottom:none; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:6px;">
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:0;">
    L&apos;Analyse SWOT est un levier de planification stratégique qui permet de synthétiser les constats majeurs afin d&apos;améliorer les processus de planification et d&apos;optimiser la prise de décision au niveau de l&apos;Université.
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

    st.markdown(f"""
<div style="background:#ffffff; padding:8px 24px 8px 24px; border-radius:10px; border-left:none; margin-top:6px; margin-bottom:8px;">
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:6px;">
    <strong>1. Facteurs internes :</strong> Identification des <strong>forces</strong> et des <strong>faiblesses</strong> propres à l'Université (Exemples de Forces et Faiblesses en {annexe_b_hover_html}).
    </p>
    <p style="text-align:left; font-size:17px; line-height:1.55; color:#0070C0; font-weight:700; font-style:italic; margin-bottom:0;">
    Nous vous remercions de bien vouloir compléter le tableau ci-dessous en indiquant au maximum <span style="text-decoration:underline; font-weight:700; font-style:italic;">cinq forces et cinq faiblesses</span>. Vos réponses seront déduites de l’analyse de l’état actuel interne (<a href="#section-iii" style="text-decoration:underline; color:#0000FF; font-weight:700; font-style:italic;">section III</a> principalement).
    </p>
</div>
""", unsafe_allow_html=True)

    swot_data["facteurs_internes"] = render_swot_table(
        section_key="swot_internal",
        left_title="Forces (Saisir une force par case)",
        right_title="Faiblesses (Saisir une faiblesse par case)"
    )

    html_block(f"""
<div style="background:#ffffff; padding:8px 24px 8px 24px; border-radius:10px; border-left:none; margin-top:10px; margin-bottom:6px;">
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE}; margin-bottom:6px;">
    <strong>2. Facteurs externes :</strong> Identification des <strong>opportunités</strong> de développement et des <strong>menaces</strong> émanant de l'environnement extérieur (Exemples d’Opportunités et de Menaces en {annexe_c_hover_html}).
    </p>
    <p style="text-align:left; font-size:17px; line-height:1.55; color:#0070C0; font-weight:700; font-style:italic; margin-bottom:0;">
    Nous vous remercions de bien vouloir compléter le tableau ci-dessous en indiquant au maximum <span style="text-decoration:underline; font-weight:700; font-style:italic;">cinq opportunités et cinq menaces</span>. Vos réponses seront déduites de l’analyse de l’état actuel externe (<a href="#section-iv" style="text-decoration:underline; color:#0000FF; font-weight:700; font-style:italic;">section IV</a> principalement).
    </p>
</div>
""")

    swot_data["facteurs_externes"] = render_swot_table(
        section_key="swot_external",
        left_title="Opportunités (Saisir une opportunité par case)",
        right_title="Menaces (Saisir une menace par case)"
    )

    return swot_data
def render_priorities_intro():
    html_block(f"""
<div style="background-color:#ffffff; padding:24px 34px; border-radius:12px; border-left:none; border-top:none; border-bottom:none; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-bottom:25px;">
    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    Cette section a pour objectif de proposer, à l’échelle de l’USJ, <strong>des priorités stratégiques et des initiatives (projets)</strong>, en cohérence avec les constats issus de l’analyse des environnements interne et externe et de l’analyse SWOT. Les propositions attendues doivent refléter les enjeux majeurs identifiés, les capacités institutionnelles existantes et les orientations à privilégier pour les prochaines années.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    <strong>Les priorités stratégiques</strong> sont les enjeux sur lesquels l’Université doit porter ses efforts pour remédier aux faiblesses, capitaliser sur les forces, tirer avantage des opportunités et faire face aux menaces identifiées par l’analyse SWOT.
    </p>

    <p style="text-align:justify; font-size:17px; line-height:1.55; color:{USJ_BLUE};">
    <strong>L'initiative</strong> correspond plus concrètement, à un projet spécifique qui permet la mise en œuvre de la priorité correspondante. Elle peut être au niveau de l’Université ou bien au niveau de votre institution. Afin de clarifier les attentes et de faciliter le pilotage, chaque initiative doit impérativement être formulée par un verbe d'action.
    </p>

    <p style="text-align:left; font-size:17px; line-height:1.55; color:#0070C0; font-weight:700; font-style:italic; margin-bottom:0;">
    Nous vous remercions de bien vouloir compléter le tableau ci-dessous en indiquant au maximum <span style="text-decoration:underline; font-weight:700; font-style:italic;">trois priorités stratégiques et 1 à 3 initiatives par priorité</span>. Les initiatives peuvent être au niveau de l’Université et/ou au niveau de l’institution. Vos réponses seront déduites de l’analyse SWOT. Vous pouvez hiérarchiser les priorités en les numérotant de 1 à 3.
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

    for i in range(1, 4):
        col1, col2 = st.columns([1.2, 1.8], gap="small")

        with col1:
            priority_value = word_limited_text_area(
                label=f"Priorité stratégique {i}",
                key=f"priority_{i}",
                height=350,
                max_words=30
            )

        with col2:
            initiative_1 = word_limited_text_area(
                label=f"Initiative {i}.1",
                key=f"initiative_{i}_1",
                height=70,
                max_words=30
            )

            initiative_2 = word_limited_text_area(
                label=f"Initiative {i}.2",
                key=f"initiative_{i}_2",
                height=70,
                max_words=30
            )

            initiative_3 = word_limited_text_area(
                label=f"Initiative {i}.3",
                key=f"initiative_{i}_3",
                height=70,
                max_words=30
            )

        priorities_rows.append({
            "priorite_strategique": priority_value,
            "initiative_1": initiative_1,
            "initiative_2": initiative_2,
            "initiative_3": initiative_3,
        })

    return priorities_rows

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
<div style="font-size:17px; line-height:1.35; color:{USJ_BLUE}; font-weight:700; margin-top:8px; white-space:nowrap;">
    &bull; {phrase}
</div>
""")

        with col_boxes:
            r1 = st.text_input(
                f"{phrase} 1",
                key=f"pour_finir_{i}_1",
                label_visibility="collapsed",
                disabled=read_only
            )
            r2 = st.text_input(
                f"{phrase} 2",
                key=f"pour_finir_{i}_2",
                label_visibility="collapsed",
                disabled=read_only
            )
            r3 = st.text_input(
                f"{phrase} 3",
                key=f"pour_finir_{i}_3",
                label_visibility="collapsed",
                disabled=read_only
            )

        pour_finir[phrase] = {
            "reponse_1": r1,
            "reponse_2": r2,
            "reponse_3": r3,
        }

    return pour_finir

def render_quick_save_button(key):
    if st.session_state.get("read_only_submitted", False):
        return False

    return st.button(
        "Enregistrer et continuer plus tard",
        key=key
    )


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

def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="📋", layout="wide")

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

        col_unlock, col_delete = st.columns(2)

        with col_unlock:
            if st.button("Redonner accès à cette personne"):
                unlock_response_by_code(selected_draft_code)
                st.success(
                    f"L’accès a été redonné au code {selected_draft_code}. "
                    "La personne peut modifier et soumettre à nouveau."
                )
                st.rerun()

        with col_delete:
            if st.button("Supprimer les réponses de cette personne"):
                delete_response_by_code(selected_draft_code)
                st.success(
                    f"Les réponses associées au code {selected_draft_code} ont été supprimées."
                )
                st.rerun()

        st.markdown("### Raw responses table")
        st.dataframe(df, use_container_width=True)

        try:
            flat_df = pd.DataFrame([flatten_response(row) for _, row in df.iterrows()])
        except Exception as e:
            st.warning(f"Could not flatten JSON responses. Raw data is still available. Details: {e}")
            flat_df = df.copy()

        st.markdown("### Flattened responses table")
        st.dataframe(flat_df, use_container_width=True)

        raw_csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="Download raw CSV",
            data=raw_csv,
            file_name="etat_actuel_responses_raw.csv",
            mime="text/csv",
        )

        flat_csv = flat_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="Download flattened CSV",
            data=flat_csv,
            file_name="etat_actuel_responses_flattened.csv",
            mime="text/csv",
        )

        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Raw responses")
            flat_df.to_excel(writer, index=False, sheet_name="Flattened responses")

        st.download_button(
            label="Download Excel",
            data=excel_buffer.getvalue(),
            file_name="etat_actuel_responses.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        with open(DB_PATH, "rb") as f:
            st.download_button(
                label="Download SQLite DB",
                data=f,
                file_name="etat_actuel_responses.db",
                mime="application/octet-stream",
            )

        st.stop()

    if not st.session_state["access_granted"]:
        col_code, col_button = st.columns([2, 1])

        with col_code:
            login_code = st.text_input(
                "Mot de passe reçu par email",
                placeholder="",
                key="login_draft_code"
            )

        with col_button:
            st.markdown("<br>", unsafe_allow_html=True)
            enter_form = st.button("Accéder au rapport")

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
                st.error("Code non reconnu. Veuillez utiliser le code personnel qui vous a été communiqué.")
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
                st.text_input(
                    "Institution",
                    value=st.session_state.get("institution", ""),
                    disabled=True,
                    key="institution_display"
                )
                institution = st.session_state.get("institution", "")

            with col2:
                responsable = st.text_input(
                    "Responsable",
                    key="responsable",
                    disabled=True
                )

            with col3:
                st.text_input(
                    "Date",
                    value=datetime.now().strftime("%Y-%m-%d"),
                    disabled=True
                )
                response_date = datetime.now().date()

            st.markdown("---")

            section_header("I - Introduction")
            render_fixed_introduction()

            st.divider()

            st.markdown('<div class="print-page-break"></div>', unsafe_allow_html=True)

            section_header("II - Identification des parties prenantes")
            render_stakeholder_intro()
            stakeholder_rows = render_stakeholder_table()
            quick_save_after_stakeholders = render_quick_save_button("quick_save_after_stakeholders")

            st.divider()

            st.markdown(
                """
                <div id="section-iii" style="position:relative; top:-150px; height:0px;"></div>
                """,
                unsafe_allow_html=True
            )
            st.markdown('<div class="print-page-break"></div>', unsafe_allow_html=True)

            section_header("III - Analyse interne de l’état actuel de l’Université")
            render_internal_intro()
            internal_analysis = render_internal_analysis()
            quick_save_after_internal = render_quick_save_button("quick_save_after_internal")

            st.divider()

            st.markdown(
                """
                <div id="section-iv" style="position:relative; top:-150px; height:0px;"></div>
                """,
                unsafe_allow_html=True
            )
            st.markdown('<div class="print-page-break"></div>', unsafe_allow_html=True)

            section_header("IV - Analyse externe de l’environnement actuel de l’Université")
            render_external_intro()
            external_analysis = render_external_analysis()
            quick_save_after_external = render_quick_save_button("quick_save_after_external")

            st.divider()

            st.markdown('<div class="print-page-break"></div>', unsafe_allow_html=True)

            section_header("V - Analyse SWOT – Niveau USJ")
            render_swot_intro()
            swot_analysis = render_swot_analysis()
            quick_save_after_swot = render_quick_save_button("quick_save_after_swot")

            st.divider()

            st.markdown('<div class="print-page-break"></div>', unsafe_allow_html=True)

            section_header("VI - Priorités stratégiques et initiatives proposées – Niveau USJ")
            render_priorities_intro()
            priorities_initiatives = render_priorities_table()
            quick_save_after_priorities = render_quick_save_button("quick_save_after_priorities")

            st.divider()

            pour_finir = render_pour_finir()

            st.markdown("<br>", unsafe_allow_html=True)

            if st.session_state.get("read_only_submitted", False):
                st.info(
                    "Cette réponse a déjà été envoyée en version finale. "
                    "Vous pouvez la consulter, mais vous ne pouvez plus la modifier ni l’enregistrer à nouveau."
                )
                save_draft = False
                submit_final = False
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
                "internal_analysis": internal_analysis,
                "external_analysis": external_analysis,
                "swot_analysis": swot_analysis,
                "priorities_initiatives": priorities_initiatives,
                "pour_finir": pour_finir,
            }

            try:
                draft_code = save_response(metadata, data)
                st.session_state["current_draft_code"] = draft_code

                if save_draft:
                    st.success(
                        f"Vos réponses ont été enregistrées. Utilisez ce code pour reprendre plus tard : {draft_code}"
                    )

                if submit_final:
                    st.session_state["read_only_submitted"] = True
                    st.success("Merci.\nVos réponses ont été enregistrées.")
                    st.rerun()

            except ValueError as e:
                st.error(str(e))


if __name__ == "__main__":
    main()
