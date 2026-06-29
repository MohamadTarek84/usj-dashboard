#!/usr/bin/env python
# coding: utf-8

import re
import html as html_lib
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


APP_TITLE = "PLAN STRATÉGIQUE USJ 2032 - Aperçu par groupe"

SHEET_NAME = "All answers 29-6-2026"

USJ_BLUE = "#001F5B"
USJ_BLUE_2 = "#1F3C88"
USJ_RED = "#8B1538"
USJ_LIGHT_BLUE = "#EAF2F8"
USJ_TEXT = "#1B2A41"

LOGO_PATH = Path("LogoUAQ.png")


# =====================================================
# BASIC HELPERS
# =====================================================

def html_block(content):
    if hasattr(st, "html"):
        st.html(content)
    else:
        st.markdown(content, unsafe_allow_html=True)


def normalize_col(col):
    return str(col).strip().lower().replace("\n", " ")


def clean_text(value):
    if pd.isna(value):
        return ""
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def find_column(df, possible_names, fallback_index=None):
    normalized = {normalize_col(c): c for c in df.columns}

    for name in possible_names:
        key = normalize_col(name)
        if key in normalized:
            return normalized[key]

    if fallback_index is not None and fallback_index < len(df.columns):
        return df.columns[fallback_index]

    return None


def extract_answer_columns(df):
    excluded_keywords = [
        "type",
        "participant",
        "participants",
        "groupe",
        "group",
        "sous groupe",
        "subgroup",
        "nom",
        "name",
        "date",
        "id",
        "code",
    ]

    answer_cols = []
    for col in df.columns:
        col_norm = normalize_col(col)
        if not any(k in col_norm for k in excluded_keywords):
            answer_cols.append(col)

    return answer_cols


# =====================================================
# STYLE
# =====================================================

def apply_usj_style():
    html_block(f"""
<style>
#MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{
    display:none !important;
    visibility:hidden !important;
}}

html, body, [class*="css"], [class*="st-"], .stApp {{
    font-family: Candara, Calibri, Arial, sans-serif !important;
    color:{USJ_TEXT};
}}

.main .block-container,
div[data-testid="stAppViewContainer"] .block-container {{
    padding-left:3rem !important;
    padding-right:3rem !important;
    max-width:100% !important;
}}

h1, h2, h3, h4 {{
    color:{USJ_BLUE} !important;
    font-weight:800 !important;
}}

.stButton button,
.stDownloadButton button {{
    background-color:#0070C0 !important;
    color:white !important;
    border-radius:8px !important;
    border:1px solid #0070C0 !important;
    font-weight:800 !important;
}}

button[kind="primary"] {{
    background-color:{USJ_RED} !important;
    border-color:{USJ_RED} !important;
    color:white !important;
}}

.print-wrapper {{
    background:white;
    padding:20px 26px;
    border:1px solid #D0D6E0;
    border-radius:12px;
    margin-top:16px;
}}

.print-header {{
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    border-bottom:2px solid #D0D6E0;
    padding-bottom:10px;
    margin-bottom:18px;
}}

.print-title {{
    font-size:34px;
    font-weight:900;
    color:{USJ_BLUE};
    margin:0;
    line-height:1.1;
}}

.print-subtitle {{
    font-size:22px;
    font-weight:800;
    color:{USJ_BLUE_2};
    margin-top:8px;
}}

.print-group {{
    text-align:center;
    font-size:24px;
    font-weight:900;
    color:{USJ_RED};
    margin:18px 0 8px 0;
}}

.print-participants {{
    text-align:center;
    font-size:18px;
    font-weight:700;
    color:#333;
    margin-bottom:22px;
}}

.section-title {{
    background:{USJ_LIGHT_BLUE};
    border-left:7px solid {USJ_BLUE};
    color:{USJ_BLUE};
    font-size:24px;
    font-weight:900;
    padding:12px 18px;
    border-radius:8px;
    margin-top:24px;
    margin-bottom:14px;
}}

.answer-block {{
    border:1.5px solid #595959;
    background:#E3DED9;
    padding:12px 14px;
    margin-bottom:12px;
    min-height:48px;
    font-size:17px;
    line-height:1.35;
    color:#000;
    white-space:pre-wrap;
    break-inside:avoid;
    page-break-inside:avoid;
}}

.answer-label {{
    font-size:17px;
    font-weight:900;
    color:{USJ_RED};
    margin-bottom:5px;
}}

.two-col {{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:16px;
}}

.col-title {{
    background:{USJ_BLUE};
    color:white;
    text-align:center;
    font-size:18px;
    font-weight:900;
    padding:10px;
    border-radius:6px;
    margin-bottom:8px;
}}

@media print {{
    @page {{
        size:A4 portrait;
        margin:10mm 9mm 10mm 9mm;
    }}

    header, footer, #MainMenu, .stButton, .stDownloadButton,
    div[data-testid="stToolbar"], div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"], .screen-only {{
        display:none !important;
        height:0 !important;
        visibility:hidden !important;
    }}

    .block-container {{
        max-width:190mm !important;
        width:190mm !important;
        padding:0 !important;
        margin:0 auto !important;
    }}

    .print-wrapper {{
        border:none !important;
        padding:0 !important;
        margin:0 !important;
    }}

    .print-title {{
        font-size:24px !important;
    }}

    .print-subtitle {{
        font-size:14px !important;
    }}

    .print-group {{
        font-size:20px !important;
        margin-top:8px !important;
    }}

    .section-title {{
        font-size:17px !important;
        padding:8px 12px !important;
        margin-top:12px !important;
        margin-bottom:8px !important;
        break-after:avoid !important;
        page-break-after:avoid !important;
    }}

    .answer-block {{
        font-size:10.5px !important;
        line-height:1.2 !important;
        padding:6px !important;
        margin-bottom:5px !important;
        break-inside:avoid !important;
        page-break-inside:avoid !important;
    }}

    .answer-label {{
        font-size:11px !important;
    }}

    .col-title {{
        font-size:12px !important;
        padding:6px !important;
    }}

    .two-col {{
        gap:8px !important;
    }}
}}
</style>
""")


# =====================================================
# DATA PROCESSING
# =====================================================

def load_excel(uploaded_file):
    return pd.read_excel(uploaded_file, sheet_name=SHEET_NAME)


def prepare_dataframe(df):
    type_col = find_column(
        df,
        ["Type", "Type de participant", "Respondent type", "Participant type"],
        fallback_index=0
    )

    subgroup_col = find_column(
        df,
        ["Sous groupe", "Subgroup", "Groupe", "Group", "Numéro du groupe"],
        fallback_index=1
    )

    name_col = find_column(
        df,
        ["Nom des participants", "Participants", "Nom", "Name", "Responsable"],
        fallback_index=2
    )

    answer_cols = extract_answer_columns(df)

    if type_col in answer_cols:
        answer_cols.remove(type_col)
    if subgroup_col in answer_cols:
        answer_cols.remove(subgroup_col)
    if name_col in answer_cols:
        answer_cols.remove(name_col)

    return type_col, subgroup_col, name_col, answer_cols


def group_answers(df, type_col, subgroup_col, name_col, answer_cols):
    rows = []

    for _, row in df.iterrows():
        respondent_type = clean_text(row.get(type_col, ""))
        subgroup = clean_text(row.get(subgroup_col, ""))
        participants = clean_text(row.get(name_col, "")) if name_col else ""

        answers = {}
        for col in answer_cols:
            value = clean_text(row.get(col, ""))
            if value:
                answers[str(col)] = value

        if respondent_type and subgroup:
            rows.append({
                "respondent_type": respondent_type,
                "subgroup": subgroup,
                "participants": participants,
                "answers": answers
            })

    return rows


# =====================================================
# PRINT PREVIEW
# =====================================================

def classify_section(question):
    q = normalize_col(question)

    if "force" in q:
        return "I - Forces et faiblesses", "Forces"
    if "faiblesse" in q:
        return "I - Forces et faiblesses", "Faiblesses"
    if "opportun" in q:
        return "II - Opportunités et menaces", "Opportunités"
    if "menace" in q:
        return "II - Opportunités et menaces", "Menaces"
    if "prior" in q:
        return "III - Priorités", "Priorités"
    if "conclusion" in q or "pour finir" in q or "souhaitons" in q:
        return "IV - Conclusion", "Conclusion"

    return "Autres réponses", "Autres"


def build_print_html(record, hide_participants=False):
    respondent_type = html_lib.escape(record["respondent_type"])
    subgroup = html_lib.escape(record["subgroup"])
    participants = html_lib.escape(record["participants"])

    sections = {}

    for question, answer in record["answers"].items():
        section, family = classify_section(question)
        sections.setdefault(section, {})
        sections[section].setdefault(family, [])
        sections[section][family].append((question, answer))

    participants_html = ""
    if not hide_participants and participants:
        participants_html = f"""
        <div class="print-participants">
            Nom des participants : {participants}
        </div>
        """

    html = f"""
<div class="print-wrapper">

    <div class="print-header">
        <div>
            <div class="print-title">PLAN STRATÉGIQUE USJ 2032</div>
            <div class="print-subtitle">Focus groupe - Aperçu des réponses corrigées</div>
        </div>
        <div style="font-weight:900; color:{USJ_BLUE}; font-size:18px;">
            {respondent_type}
        </div>
    </div>

    <div class="print-group">{subgroup}</div>
    {participants_html}
"""

    # SWOT two-column format
    swot_1 = sections.get("I - Forces et faiblesses", {})
    if swot_1:
        html += """
        <div class="section-title">I - Forces et faiblesses</div>
        <div class="two-col">
            <div>
                <div class="col-title">Forces</div>
        """
        for question, answer in swot_1.get("Forces", []):
            html += answer_html(question, answer)

        html += """
            </div>
            <div>
                <div class="col-title">Faiblesses</div>
        """
        for question, answer in swot_1.get("Faiblesses", []):
            html += answer_html(question, answer)

        html += """
            </div>
        </div>
        """

    swot_2 = sections.get("II - Opportunités et menaces", {})
    if swot_2:
        html += """
        <div class="section-title">II - Opportunités et menaces</div>
        <div class="two-col">
            <div>
                <div class="col-title">Opportunités</div>
        """
        for question, answer in swot_2.get("Opportunités", []):
            html += answer_html(question, answer)

        html += """
            </div>
            <div>
                <div class="col-title">Menaces</div>
        """
        for question, answer in swot_2.get("Menaces", []):
            html += answer_html(question, answer)

        html += """
            </div>
        </div>
        """

    # Other sections
    for section_name in ["III - Priorités", "IV - Conclusion", "Autres réponses"]:
        if section_name in sections:
            html += f'<div class="section-title">{html_lib.escape(section_name)}</div>'

            for family, items in sections[section_name].items():
                for question, answer in items:
                    html += answer_html(question, answer)

    html += "</div>"
    return html


def answer_html(question, answer):
    safe_q = html_lib.escape(str(question))
    safe_a = html_lib.escape(str(answer)).replace("\n", "<br>")

    return f"""
<div>
    <div class="answer-label">{safe_q}</div>
    <div class="answer-block">{safe_a}</div>
</div>
"""


def render_print_button():
    components.html(
        """
        <button onclick="window.parent.print()" style="
            background-color:#8B1538;
            color:white;
            border:1px solid #8B1538;
            border-radius:8px;
            padding:10px 22px;
            font-family:Candara, Calibri, Arial, sans-serif;
            font-size:18px;
            font-weight:800;
            cursor:pointer;
            width:260px;
        ">
            Imprimer / Enregistrer en PDF
        </button>
        """,
        height=55
    )


# =====================================================
# MAIN
# =====================================================

def main():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    apply_usj_style()

    st.title("PLAN STRATÉGIQUE USJ 2032")
    st.markdown("### Aperçu imprimable des réponses corrigées depuis Excel")

    uploaded_file = st.file_uploader(
        "Uploader le fichier Excel corrigé",
        type=["xlsx"]
    )

    if not uploaded_file:
        st.info("Veuillez uploader le fichier Excel contenant la feuille : All answers 29-6-2026.")
        st.stop()

    try:
        df = load_excel(uploaded_file)
    except Exception as e:
        st.error(f"Impossible de lire la feuille '{SHEET_NAME}'. Détail : {e}")
        st.stop()

    type_col, subgroup_col, name_col, answer_cols = prepare_dataframe(df)

    if not type_col or not subgroup_col:
        st.error("Impossible d’identifier la colonne Type de participant ou Sous groupe.")
        st.stop()

    records = group_answers(df, type_col, subgroup_col, name_col, answer_cols)

    if not records:
        st.warning("Aucune réponse exploitable trouvée.")
        st.stop()

    st.markdown("### Colonnes détectées")
    st.write({
        "Type participant": type_col,
        "Sous groupe": subgroup_col,
        "Nom participants": name_col,
        "Colonnes réponses": len(answer_cols)
    })

    respondent_types = sorted(set(r["respondent_type"] for r in records))
    selected_type = st.selectbox(
        "Type de participants",
        respondent_types
    )

    subgroups = sorted(
        set(r["subgroup"] for r in records if r["respondent_type"] == selected_type)
    )

    selected_subgroup = st.selectbox(
        "Sous groupe",
        subgroups
    )

    matching = [
        r for r in records
        if r["respondent_type"] == selected_type
        and r["subgroup"] == selected_subgroup
    ]

    if not matching:
        st.warning("Aucune donnée pour cette sélection.")
        st.stop()

    record = matching[0]

    hide_participants = st.checkbox(
        "Masquer le nom des participants",
        value=False
    )

    st.markdown("---")

    col_print, col_info = st.columns([1, 3])
    with col_print:
        render_print_button()

    with col_info:
        st.info("L’aperçu ci-dessous reprend le format imprimable utilisé dans la plateforme Focus Group.")

    print_html = build_print_html(
        record,
        hide_participants=hide_participants
    )

    html_block(print_html)

    export_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{selected_type} - {selected_subgroup}</title>
</head>
<body>
{print_html}
</body>
</html>
"""

    st.download_button(
        "Télécharger cet aperçu en HTML",
        data=export_html.encode("utf-8"),
        file_name=f"print_preview_{selected_type}_{selected_subgroup}.html".replace(" ", "_"),
        mime="text/html"
    )


if __name__ == "__main__":
    main()
