import re
import html
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

APP_TITLE = "PLAN STRATÉGIQUE USJ 2032"
SHEET_NAME = "All answers 29-6-2026"

USJ_BLUE = "#001F5B"
USJ_BLUE_2 = "#1F3C88"
USJ_RED = "#8B1538"
USJ_LIGHT_BLUE = "#EAF2F8"
USJ_TEXT = "#1B2A41"


def clean(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize(value):
    value = clean(value).lower()
    replacements = {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a",
        "ù": "u", "û": "u",
        "ç": "c",
        "î": "i", "ï": "i",
        "ô": "o",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def esc(value):
    return html.escape(clean(value)).replace("\n", "<br>")


def safe_filename(value):
    value = clean(value)
    value = re.sub(r"[^A-Za-z0-9À-ÿ._-]+", "_", value)
    return value.strip("_") or "rapport"


def html_block(content):
    st.markdown(content, unsafe_allow_html=True)


PRINT_CSS = f"""
body {{
    font-family: Candara, Calibri, Arial, sans-serif;
    background:white;
    color:{USJ_TEXT};
    margin:0;
    padding:0;
}}

.print-report {{
    background:white;
    border:1px solid #D0D6E0;
    border-radius:12px;
    padding:28px 34px;
}}

.usj-main-header {{
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    border-bottom:2px solid #D0D6E0;
    padding-bottom:18px;
    margin-bottom:28px;
}}

.usj-main-header h1 {{
    font-size:42px;
    margin:0 0 16px 0;
    color:{USJ_BLUE};
    font-weight:800;
}}

.usj-main-header p {{
    font-size:26px;
    font-weight:700;
    color:{USJ_BLUE_2};
    margin:0;
}}

.participant-type {{
    font-size:22px;
    font-weight:800;
    color:{USJ_BLUE};
}}

.group-title {{
    text-align:center;
    font-size:28px;
    font-weight:800;
    color:{USJ_RED};
    margin:24px 0;
}}

.names {{
    text-align:center;
    font-size:21px;
    font-weight:700;
    color:#111;
    margin-bottom:32px;
}}

.section-header {{
    background-color:{USJ_LIGHT_BLUE};
    padding:12px 18px;
    border-radius:10px;
    border-left:7px solid {USJ_BLUE};
    margin-top:24px;
    margin-bottom:16px;
    page-break-inside:avoid;
}}

.section-header h2 {{
    font-size:28px;
    margin:0;
    color:{USJ_BLUE};
}}

.two-cols {{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:20px;
}}

.col-title {{
    background:{USJ_BLUE};
    color:white;
    padding:10px 14px;
    text-align:center;
    font-size:20px;
    font-weight:800;
    border-radius:6px;
    margin-bottom:10px;
}}

.answer-box {{
    background:#E3DED9;
    border:1.5px solid #595959;
    padding:12px 16px;
    margin-bottom:10px;
    font-size:18px;
    line-height:1.35;
    color:#000;
    page-break-inside:avoid;
    break-inside:avoid;
}}

.answer-number {{
    color:{USJ_RED};
    font-weight:800;
    margin-right:6px;
}}

.single-section .answer-box {{
    min-height:50px;
}}

.print-page-break {{
    page-break-before:always;
}}

.print-button {{
    background:#8B1538;
    color:white;
    border:1px solid #8B1538;
    border-radius:8px;
    padding:10px 22px;
    font-family:Candara,Calibri,Arial,sans-serif;
    font-size:18px;
    font-weight:800;
    cursor:pointer;
    margin-bottom:20px;
}}

@media print {{
    @page {{
        size:A4 portrait;
        margin:8mm 9mm;
    }}

    body {{
        margin:0;
    }}

    .print-button {{
        display:none;
    }}

    .print-report {{
        border:none;
        padding:0;
    }}

    .usj-main-header h1 {{
        font-size:22px;
        line-height:1.05;
        margin-bottom:2mm;
    }}

    .usj-main-header p {{
        font-size:13px;
    }}

    .participant-type {{
        font-size:12px;
    }}

    .group-title {{
        font-size:18px;
        margin:8mm 0 4mm 0;
    }}

    .names {{
        font-size:12px;
        margin-bottom:8mm;
    }}

    .section-header {{
        margin-top:5mm;
        margin-bottom:3mm;
        padding:7px 11px;
        box-shadow:none;
    }}

    .section-header h2 {{
        font-size:16px;
    }}

    .col-title {{
        font-size:12px;
        padding:6px;
    }}

    .answer-box {{
        font-size:10.5px;
        line-height:1.2;
        padding:6px;
        margin-bottom:2mm;
        page-break-inside:avoid;
        break-inside:avoid;
    }}
}}
"""


APP_CSS = f"""
<style>
html, body, .stApp {{
    font-family: Candara, Calibri, Arial, sans-serif !important;
    color:{USJ_TEXT};
}}

header, footer, #MainMenu {{
    display:none !important;
}}

.block-container {{
    max-width:100% !important;
    padding-left:3rem !important;
    padding-right:3rem !important;
}}

h1, h2, h3 {{
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
    font-size:18px !important;
}}

.stButton button p,
.stDownloadButton button p {{
    color:white !important;
}}
</style>
"""


def get_col(df, possible_names):
    cols = {normalize(c): c for c in df.columns}
    for name in possible_names:
        n = normalize(name)
        if n in cols:
            return cols[n]
    return None


def build_report_html(df_group, participant_type, subgroup, hide_names):
    names = sorted(set(clean(x) for x in df_group["participants"].dropna() if clean(x)))

    names_html = ""
    if not hide_names and names:
        names_html = f"""
        <div class="names">
            Nom des participants : {esc("; ".join(names))}
        </div>
        """

    def answers_for(section_contains=None, category_contains=None):
        temp = df_group.copy()

        if section_contains:
            temp = temp[temp["section_norm"].str.contains(section_contains, na=False)]

        if category_contains:
            temp = temp[temp["category_norm"].str.contains(category_contains, na=False)]

        answers = [clean(x) for x in temp["Final_Answer"].tolist() if clean(x)]

        if not answers:
            return '<div class="answer-box">Aucune réponse disponible.</div>'

        return "".join(
            f"""
            <div class="answer-box">
                <span class="answer-number">{i}.</span>{esc(answer)}
            </div>
            """
            for i, answer in enumerate(answers, start=1)
        )

    return f"""
<div class="print-report">

    <div class="usj-main-header">
        <div>
            <h1>PLAN STRATÉGIQUE USJ 2032</h1>
            <p>Focus groupe - Aperçu des réponses corrigées</p>
        </div>
        <div class="participant-type">{esc(participant_type)}</div>
    </div>

    <div class="group-title">{esc(subgroup)}</div>

    {names_html}

    <div class="section-header">
        <h2>I - Forces et faiblesses</h2>
    </div>

    <div class="two-cols">
        <div>
            <div class="col-title">Forces</div>
            {answers_for(section_contains="forces", category_contains="force")}
        </div>
        <div>
            <div class="col-title">Faiblesses</div>
            {answers_for(section_contains="forces", category_contains="faiblesse")}
        </div>
    </div>

    <div class="section-header">
        <h2>II - Opportunités et menaces</h2>
    </div>

    <div class="two-cols">
        <div>
            <div class="col-title">Opportunités</div>
            {answers_for(section_contains="opportunites", category_contains="opportun")}
        </div>
        <div>
            <div class="col-title">Menaces</div>
            {answers_for(section_contains="opportunites", category_contains="menace")}
        </div>
    </div>

    <div class="print-page-break"></div>

    <div class="section-header">
        <h2>III - Priorités</h2>
    </div>

    <div class="single-section">
        {answers_for(section_contains="prior")}
    </div>

    <div class="section-header">
        <h2>IV - Conclusion</h2>
    </div>

    <div class="single-section">
        {answers_for(section_contains="conclusion")}
    </div>

</div>
"""


def build_full_html(html_report, selected_type, selected_subgroup):
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{esc(selected_type)} - {esc(selected_subgroup)}</title>
<style>
{PRINT_CSS}
</style>
</head>
<body>
<button class="print-button" onclick="window.print()">Imprimer / Enregistrer en PDF</button>
{html_report}
</body>
</html>
"""


def main():
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    html_block(APP_CSS)

    html_block(f"""
    <div class="screen-only">
        <h1 style="margin-bottom:0;">{APP_TITLE}</h1>
        <h3 style="color:{USJ_RED} !important; margin-top:4px;">
            Lecture Excel - Print Preview des réponses corrigées
        </h3>
    </div>
    """)

    uploaded_file = st.file_uploader(
        "Uploader le fichier Excel corrigé",
        type=["xlsx", "xls"]
    )

    if uploaded_file is None:
        st.info(f"Veuillez uploader le fichier Excel contenant la feuille : {SHEET_NAME}")
        st.stop()

    try:
        df = pd.read_excel(uploaded_file, sheet_name=SHEET_NAME, engine="openpyxl")
    except Exception as e:
        st.error(f"Impossible de lire la feuille : {SHEET_NAME}")
        st.exception(e)
        st.stop()

    df = df.dropna(how="all")

    type_col = get_col(df, ["Respondent_Type", "Type participant", "Type de participants"])
    group_col = get_col(df, ["groupe", "Sous groupe", "Subgroup"])
    names_col = get_col(df, ["participants", "Participants", "Nom participants"])
    section_col = get_col(df, ["section"])
    category_col = get_col(df, ["category", "catégorie", "categorie"])
    answer_col = get_col(df, ["Final_Answer", "Final Answer", "Réponse finale", "Reponse finale"])

    missing = []
    if not type_col:
        missing.append("Respondent_Type")
    if not group_col:
        missing.append("groupe")
    if not names_col:
        missing.append("participants")
    if not section_col:
        missing.append("section")
    if not category_col:
        missing.append("category")
    if not answer_col:
        missing.append("Final_Answer")

    if missing:
        st.error("Colonnes manquantes : " + ", ".join(missing))
        st.stop()

    df = df.rename(columns={
        type_col: "Respondent_Type",
        group_col: "groupe",
        names_col: "participants",
        section_col: "section",
        category_col: "category",
        answer_col: "Final_Answer"
    })

    for col in ["Respondent_Type", "groupe", "participants", "section", "category", "Final_Answer"]:
        df[col] = df[col].apply(clean)

    df = df[(df["Respondent_Type"] != "") & (df["groupe"] != "")]

    df["section_norm"] = df["section"].apply(normalize)
    df["category_norm"] = df["category"].apply(normalize)

    participant_types = sorted(df["Respondent_Type"].dropna().unique().tolist())

    col1, col2, col3 = st.columns([1.2, 1.2, 1])

    with col1:
        selected_type = st.selectbox("Type de participants", participant_types)

    df_type = df[df["Respondent_Type"] == selected_type]
    subgroups = sorted(df_type["groupe"].dropna().unique().tolist())

    with col2:
        selected_subgroup = st.selectbox("Sous-groupe", subgroups)

    with col3:
        hide_names = st.checkbox("Hide participants names", value=False)

    df_group = df_type[df_type["groupe"] == selected_subgroup].copy()

    html_report = build_report_html(
        df_group=df_group,
        participant_type=selected_type,
        subgroup=selected_subgroup,
        hide_names=hide_names
    )

    full_html = build_full_html(
        html_report=html_report,
        selected_type=selected_type,
        selected_subgroup=selected_subgroup
    )

    components.html(
        full_html,
        height=1200,
        scrolling=True
    )

    file_name = (
        f"USJ2032_{safe_filename(selected_type)}_"
        f"{safe_filename(selected_subgroup)}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    )

    st.download_button(
        "Télécharger HTML",
        data=full_html.encode("utf-8"),
        file_name=file_name,
        mime="text/html"
    )


if __name__ == "__main__":
    main()
