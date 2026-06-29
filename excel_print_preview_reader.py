import re
import html
import base64
from pathlib import Path
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
LOGO_PATH = "LogoUAQ.png"


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


def image_to_base64(image_path):
    image_path = Path(image_path)
    if not image_path.exists():
        return ""
    suffix = image_path.suffix.lower().replace(".", "")
    mime_type = "png" if suffix == "png" else suffix
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    return f"data:image/{mime_type};base64,{encoded}"


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
    margin:0 0 6px 0;
    color:{USJ_BLUE};
    font-weight:800;
}}

.usj-main-header p {{
    font-size:18px;
    font-weight:700;
    color:{USJ_BLUE_2};
    margin:0;
}}

.usj-logo-box {{
    display:flex;
    justify-content:flex-end;
    align-items:flex-start;
}}

.usj-logo {{
    width:170px;
    height:auto;
    object-fit:contain;
}}

.participant-type {{
    display:none;
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
    box-shadow:0 2px 10px rgba(0,0,0,0.06);
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

.conclusion-label {{
    color:{USJ_BLUE};
    font-size:19px;
    font-weight:800;
    margin:28px 0 10px 4px;
}}

.conclusion-box {{
    background:#E3DED9;
    border:1.5px solid #595959;
    padding:14px 18px;
    margin-bottom:18px;
    min-height:72px;
    font-size:20px;
    line-height:1.35;
    color:#000;
    page-break-inside:avoid;
    break-inside:avoid;
}}

.swot-grid {{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:18px;
    margin-top:14px;
    page-break-inside:avoid;
}}

.swot-card {{
    border-radius:14px;
    padding:16px;
    border:2px solid var(--accent);
    background:var(--bg);
    page-break-inside:avoid;
    break-inside:avoid;
}}

.swot-card h3 {{
    margin:0 0 10px 0;
    color:var(--accent);
    font-size:24px;
    font-weight:900;
    border-bottom:2px solid var(--accent);
    padding-bottom:8px;
}}

.swot-card ul {{
    margin:0;
    padding-left:22px;
}}

.swot-card li {{
    margin-bottom:8px;
    font-size:16px;
    line-height:1.3;
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
        margin-bottom:1mm;
    }}

    .usj-main-header p {{
        font-size:10px;
    }}

    .usj-logo {{
        width:36mm;
        max-width:36mm;
        height:auto;
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

    .answer-box,
    .conclusion-box {{
        font-size:10.5px;
        line-height:1.2;
        padding:6px;
        margin-bottom:2mm;
        page-break-inside:avoid;
        break-inside:avoid;
    }}

    .conclusion-label {{
        font-size:11px;
        margin:4mm 0 2mm 0;
    }}

    .swot-card h3 {{
        font-size:13px;
    }}

    .swot-card li {{
        font-size:9.5px;
        line-height:1.15;
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


def get_answers(df_group, section_contains=None, category_contains=None):
    temp = df_group.copy()

    if section_contains:
        temp = temp[temp["section_norm"].str.contains(section_contains, na=False)]

    if category_contains:
        temp = temp[temp["category_norm"].str.contains(category_contains, na=False)]

    return [clean(x) for x in temp["Final_Answer"].tolist() if clean(x)]


def answer_boxes(answers):
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


def swot_card(title, answers, accent, bg):
    if not answers:
        li = "<li>Aucune réponse disponible.</li>"
    else:
        li = "".join(f"<li>{esc(x)}</li>" for x in answers)

    return f"""
    <div class="swot-card" style="--accent:{accent}; --bg:{bg};">
        <h3>{title}</h3>
        <ul>{li}</ul>
    </div>
    """


def swot_matrix_html(forces, faiblesses, opportunites, menaces):
    return f"""
    <div class="section-header print-page-break">
        <h2>Matrice SWOT - Niveau USJ</h2>
    </div>

    <div class="swot-grid">
        {swot_card("FORCES", forces, USJ_BLUE, "#DDEFF7")}
        {swot_card("FAIBLESSES", faiblesses, USJ_RED, "#FBE3C3")}
        {swot_card("OPPORTUNITÉS", opportunites, "#2F6B2F", "#E2F2D3")}
        {swot_card("MENACES", menaces, USJ_RED, "#F4C6C4")}
    </div>
    """


def conclusion_html(df_group):
    conclusion_rows = df_group[
        df_group["section_norm"].str.contains("conclusion", na=False)
    ].copy()

    if conclusion_rows.empty:
        return '<div class="conclusion-box">Aucune réponse disponible.</div>'

    blocks = ""

    question_order = []
    for question in conclusion_rows["question"].tolist():
        question = clean(question)
        if question and question not in question_order:
            question_order.append(question)

    for question in question_order:
        temp = conclusion_rows[conclusion_rows["question"] == question]
        answers = [clean(x) for x in temp["Final_Answer"].tolist() if clean(x)]

        blocks += f"""
        <div class="conclusion-label">• {esc(question)}</div>
        """

        if not answers:
            blocks += '<div class="conclusion-box"></div>'
        else:
            for answer in answers:
                blocks += f"""
                <div class="conclusion-box">{esc(answer)}</div>
                """

    return blocks


def build_one_report_html(df_group, participant_type, title_label, hide_names):
    names = sorted(set(clean(x) for x in df_group["participants"].dropna() if clean(x)))

    names_html = ""
    if not hide_names and names:
        names_html = f"""
        <div class="names">
            Nom des participants : {esc("; ".join(names))}
        </div>
        """

    logo_src = image_to_base64(LOGO_PATH)
    logo_html = f'<img src="{logo_src}" class="usj-logo">' if logo_src else ""

    forces = get_answers(df_group, section_contains="forces", category_contains="force")
    faiblesses = get_answers(df_group, section_contains="forces", category_contains="faiblesse")
    opportunites = get_answers(df_group, section_contains="opportunites", category_contains="opportun")
    menaces = get_answers(df_group, section_contains="opportunites", category_contains="menace")
    priorites = get_answers(df_group, section_contains="prior")

    return f"""
<div class="print-report">

    <div class="usj-main-header">
        <div>
            <h1>PLAN STRATÉGIQUE USJ 2032</h1>
            <p>Focus groupe</p>
        </div>

        <div class="usj-logo-box">
            {logo_html}
        </div>
    </div>

    <div class="group-title">{esc(title_label)}</div>

    {names_html}

    <div class="section-header">
        <h2>I - Forces et faiblesses</h2>
    </div>

    <div class="two-cols">
        <div>
            <div class="col-title">Forces</div>
            {answer_boxes(forces)}
        </div>
        <div>
            <div class="col-title">Faiblesses</div>
            {answer_boxes(faiblesses)}
        </div>
    </div>

    <div class="section-header">
        <h2>II - Opportunités et menaces</h2>
    </div>

    <div class="two-cols">
        <div>
            <div class="col-title">Opportunités</div>
            {answer_boxes(opportunites)}
        </div>
        <div>
            <div class="col-title">Menaces</div>
            {answer_boxes(menaces)}
        </div>
    </div>

    {swot_matrix_html(forces, faiblesses, opportunites, menaces)}

    <div class="section-header print-page-break">
        <h2>III - Priorités</h2>
    </div>

    <div>
        {answer_boxes(priorites)}
    </div>

    <div class="section-header">
        <h2>IV - Conclusion</h2>
    </div>

    <div>
        {conclusion_html(df_group)}
    </div>

</div>
"""


def build_full_html(html_report, selected_type, selected_label):
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{esc(selected_type)} - {esc(selected_label)}</title>
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

    df["question"] = df["category"]

    for col in ["Respondent_Type", "groupe", "participants", "section", "category", "question", "Final_Answer"]:
        df[col] = df[col].apply(clean)

    df = df[(df["Respondent_Type"] != "") & (df["groupe"] != "")]
    df["section_norm"] = df["section"].apply(normalize)
    df["question_norm"] = df["question"].apply(normalize)
    df["category_norm"] = df["category"].apply(normalize)

    participant_types = sorted(df["Respondent_Type"].dropna().unique().tolist())

    c1, c2, c3, c4 = st.columns([1.2, 1.3, 1.2, 1])

    with c1:
        selected_type = st.selectbox("Type de participants", participant_types)

    df_type = df[df["Respondent_Type"] == selected_type].copy()

    with c2:
        report_mode = st.selectbox(
            "Mode d'affichage",
            [
                "Tous les sous-groupes du type sélectionné",
                "Un sous-groupe spécifique"
            ]
        )

    subgroups = sorted(df_type["groupe"].dropna().unique().tolist())

    with c3:
        if report_mode == "Un sous-groupe spécifique":
            selected_subgroup = st.selectbox("Sous-groupe", subgroups)
        else:
            selected_subgroup = "Tous les sous-groupes"

    with c4:
        hide_names = st.checkbox("Hide participants names", value=False)

    if report_mode == "Un sous-groupe spécifique":
        df_report = df_type[df_type["groupe"] == selected_subgroup].copy()
        title_label = selected_subgroup
    else:
        df_report = df_type.copy()
        title_label = f"{selected_type} - Tous les sous-groupes"

    html_report = build_one_report_html(
        df_group=df_report,
        participant_type=selected_type,
        title_label=title_label,
        hide_names=hide_names
    )

    full_html = build_full_html(
        html_report=html_report,
        selected_type=selected_type,
        selected_label=title_label
    )

    components.html(
        full_html,
        height=1300,
        scrolling=True
    )

    file_name = (
        f"USJ2032_{safe_filename(selected_type)}_"
        f"{safe_filename(title_label)}_"
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
