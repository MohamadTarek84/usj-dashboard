#!/usr/bin/env python
# coding: utf-8

import json
import re
import sqlite3
import html
from io import BytesIO
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


APP_TITLE = "PLAN STRATÉGIQUE USJ 2032 - Analyse des résultats"

USJ_BLUE = "#001F5B"
USJ_BLUE_2 = "#1F3C88"
USJ_RED = "#8B1538"
USJ_GOLD = "#C9A227"
USJ_LIGHT_BLUE = "#EAF2F8"
USJ_TEXT = "#1B2A41"

if Path("/home/site").exists():
    DB_DIR = Path("/home/data")
else:
    DB_DIR = Path(".")

DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "strategic_report_analysis.db"

QUESTION_ORDER = [
    "Forces",
    "Faiblesses",
    "Opportunités",
    "Menaces",
    "Priorités",
    "Conclusion - USJ reconnue pour",
    "Conclusion - Nos étudiants disent que",
    "Conclusion - Meilleur lieu de travail",
]

FRENCH_STOPWORDS = [
    "le", "la", "les", "un", "une", "des", "de", "du", "d", "et", "ou", "à", "a",
    "au", "aux", "en", "dans", "pour", "par", "sur", "avec", "sans", "plus",
    "moins", "que", "qui", "quoi", "dont", "est", "sont", "être", "etre",
    "nous", "vous", "ils", "elles", "leur", "leurs", "notre", "nos", "votre",
    "vos", "ce", "cet", "cette", "ces", "se", "sa", "son", "ses", "comme",
    "afin", "ainsi", "très", "tres", "université", "universite", "usj", "niveau",
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS validated_groupings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT,
            draft_code TEXT,
            stakeholder_category TEXT,
            subgroup TEXT,
            question TEXT,
            answer_text TEXT,
            ai_theme TEXT,
            final_theme TEXT,
            edited_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_validated_groupings(df, source_file):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM validated_groupings WHERE source_file = ?", (source_file,))
    for _, row in df.iterrows():
        cur.execute('''
            INSERT INTO validated_groupings (
                source_file, draft_code, stakeholder_category, subgroup,
                question, answer_text, ai_theme, final_theme, edited_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            source_file,
            str(row.get("draft_code", "")),
            str(row.get("stakeholder_category", "")),
            str(row.get("subgroup", "")),
            str(row.get("question", "")),
            str(row.get("answer_text", "")),
            str(row.get("ai_theme", "")),
            str(row.get("final_theme", "")),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))
    conn.commit()
    conn.close()


def load_validated_groupings(source_file):
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(
            "SELECT * FROM validated_groupings WHERE source_file = ?",
            conn,
            params=(source_file,)
        )
    finally:
        conn.close()


def apply_style():
    st.markdown(f'''
<style>
html, body, [class*="css"], [class*="st-"], .stApp {{
    font-family: Candara, Calibri, Arial, sans-serif !important;
    color: {USJ_TEXT};
}}
.main .block-container {{
    padding-top: 1.1rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 100%;
}}
header, #MainMenu, footer {{ visibility: hidden; }}
.hero {{
    background: linear-gradient(135deg, {USJ_BLUE} 0%, {USJ_BLUE_2} 55%, {USJ_RED} 100%);
    padding: 26px 34px;
    border-radius: 22px;
    color: white;
    box-shadow: 0 18px 45px rgba(0,31,91,0.22);
    margin-bottom: 20px;
}}
.hero h1 {{
    margin: 0;
    font-size: 34px;
    line-height: 1.1;
    font-weight: 900;
    color: white !important;
}}
.hero p {{
    margin: 8px 0 0 0;
    font-size: 18px;
    opacity: 0.95;
    font-weight: 600;
}}
.metric-card {{
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 10px 24px rgba(0,31,91,0.08);
    min-height: 118px;
}}
.metric-label {{
    color: #5B6777;
    font-size: 15px;
    font-weight: 800;
    margin-bottom: 8px;
}}
.metric-value {{
    color: {USJ_BLUE};
    font-size: 34px;
    font-weight: 900;
    line-height: 1;
}}
.section-title {{
    background: {USJ_LIGHT_BLUE};
    border-left: 7px solid {USJ_BLUE};
    border-radius: 12px;
    padding: 13px 18px;
    color: {USJ_BLUE};
    font-size: 24px;
    font-weight: 900;
    margin: 20px 0 14px 0;
    box-shadow: 0 4px 16px rgba(0,31,91,0.08);
}}
.note-box {{
    background: #FFF8E6;
    border-left: 6px solid {USJ_GOLD};
    border-radius: 12px;
    padding: 14px 16px;
    color: #3E3E3E;
    font-weight: 700;
    margin-bottom: 16px;
}}
.swot-shell {{
    width: 100%;
    padding: 28px 30px 36px 30px;
    background: linear-gradient(135deg, #FFFFFF 0%, #F7FAFD 48%, #FFFFFF 100%);
    border: 1px solid #E2E8F0;
    border-radius: 22px;
    box-shadow: 0 16px 38px rgba(0,31,91,0.12);
}}
.swot-header {{
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    gap:18px;
    margin-bottom:20px;
}}
.swot-heading h1 {{
    margin:0;
    color:{USJ_BLUE};
    font-size:34px;
    line-height:1.05;
    font-weight:900;
}}
.swot-heading p {{
    margin:7px 0 0 0;
    color:#4F5B6B;
    font-size:17px;
    font-weight:700;
}}
.swot-badge {{
    background:{USJ_BLUE};
    color:white;
    border-radius:999px;
    padding:10px 18px;
    font-size:15px;
    font-weight:900;
    box-shadow:0 8px 18px rgba(0,31,91,0.18);
    white-space:nowrap;
}}
.swot-grid {{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:26px;
}}
.swot-card {{
    min-height:270px;
    background:var(--bg);
    border:2.5px solid var(--accent);
    border-radius:22px;
    padding:22px 24px 26px 24px;
    box-shadow:0 12px 24px rgba(0,0,0,0.08);
}}
.swot-title {{
    color:var(--accent);
    font-size:28px;
    font-weight:900;
    margin-bottom:12px;
    border-bottom:3px solid var(--accent);
    padding-bottom:10px;
}}
.swot-item {{
    display:grid;
    grid-template-columns:32px 1fr;
    gap:10px;
    align-items:start;
    background:rgba(255,255,255,0.70);
    border-radius:14px;
    padding:10px 12px;
    margin-bottom:10px;
    border:1px solid rgba(255,255,255,0.90);
}}
.swot-index {{
    width:26px;
    height:26px;
    color:white;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:14px;
    font-weight:900;
    background:var(--accent);
}}
.swot-text {{
    color:#202A35;
    font-size:17px;
    line-height:1.25;
    font-weight:700;
}}
.stButton button, .stDownloadButton button {{
    background-color: {USJ_BLUE} !important;
    color: white !important;
    border-radius: 9px !important;
    border: 1px solid {USJ_BLUE} !important;
    font-weight: 800 !important;
}}
button[kind="primary"] {{
    background-color: {USJ_RED} !important;
    border-color: {USJ_RED} !important;
    color:white !important;
}}
</style>
''', unsafe_allow_html=True)

div[data-testid="stFileUploader"] button {{
    height: auto !important;
    min-height: 42px !important;
    width: auto !important;
    min-width: 95px !important;
    padding: 8px 14px !important;
    font-size: 14px !important;
    white-space: nowrap !important;
    line-height: 1.2 !important;
}}

div[data-testid="stFileUploader"] button p {{
    margin: 0 !important;
    padding: 0 !important;
    white-space: nowrap !important;
    font-size: 14px !important;
    line-height: 1.2 !important;
}}


def hero():
    st.markdown(f'''
<div class="hero">
    <h1>{APP_TITLE}</h1>
    <p>Analyse thématique, regroupement automatique, validation admin et visualisations stratégiques.</p>
</div>
''', unsafe_allow_html=True)


def section_title(text):
    st.markdown(f'<div class="section-title">{html.escape(text)}</div>', unsafe_allow_html=True)


def metric_card(label, value):
    st.markdown(f'''
<div class="metric-card">
    <div class="metric-label">{html.escape(label)}</div>
    <div class="metric-value">{value}</div>
</div>
''', unsafe_allow_html=True)


def clean_text(value):
    value = str(value or "").strip()
    value = re.sub(r"\s+", " ", value)
    value = value.strip("•*-–— ")
    return value


def safe_json_loads(value):
    if pd.isna(value) or not str(value).strip():
        return {}
    try:
        return json.loads(value)
    except Exception:
        return {}


def detect_category(row):
    parts = " ".join([
        str(row.get("groupe", "")),
        str(row.get("participants", "")),
        str(row.get("draft_code", "")),
        str(row.get("respondent_unit", "")),
        str(row.get("respondent_name", "")),
    ]).lower()

    if "student" in parts or "étudiant" in parts or "etudiant" in parts or "fgstudents" in parts:
        return "STUDENTS"
    if "psg" in parts:
        return "PSG"
    if "director" in parts or "directeur" in parts or "doyen" in parts or "dir" in parts:
        return "DIRECTORS"
    if "alumni" in parts or "ancien" in parts:
        return "ALUMNI"
    if "employeur" in parts or "employer" in parts:
        return "EMPLOYERS"
    return "OTHER"


def extract_subgroup(row):
    draft_code = str(row.get("draft_code", "")).strip()
    group = str(row.get("groupe", "")).strip()

    m = re.search(r"FG\s*([0-9]+)", draft_code, flags=re.IGNORECASE)
    if m:
        return f"FG{m.group(1)}"

    m = re.search(r"sous\s*groupe\s*([0-9]+)", group, flags=re.IGNORECASE)
    if m:
        return f"FG{m.group(1)}"

    return group or draft_code or "Non spécifié"


def extract_from_list(rows, question):
    output = []
    if not isinstance(rows, list):
        return output

    for row in rows:
        if isinstance(row, dict):
            value = clean_text(row.get(question, ""))
            if value:
                output.append(value)

    return output


def extract_priorities(section):
    values = []
    if not isinstance(section, dict):
        return values

    for key, value in section.items():
        if str(key).startswith("priorite_") or str(key).startswith("priority_only_"):
            value = clean_text(value)
            if value:
                values.append(value)

    return values


def extract_conclusion(section):
    values = {
        "Conclusion - USJ reconnue pour": [],
        "Conclusion - Nos étudiants disent que": [],
        "Conclusion - Meilleur lieu de travail": [],
    }

    if not isinstance(section, dict):
        return values

    mapping = {
        "pour_finir_1_0": "Conclusion - USJ reconnue pour",
        "pour_finir_1_1": "Conclusion - USJ reconnue pour",
        "pour_finir_2_0": "Conclusion - Nos étudiants disent que",
        "pour_finir_2_1": "Conclusion - Nos étudiants disent que",
        "pour_finir_3_0": "Conclusion - Meilleur lieu de travail",
        "pour_finir_3_1": "Conclusion - Meilleur lieu de travail",
    }

    for key, question in mapping.items():
        value = clean_text(section.get(key, ""))
        if value:
            values[question].append(value)

    return values


def normalize_admin_data(data):
    extracted = {
        "Forces": [],
        "Faiblesses": [],
        "Opportunités": [],
        "Menaces": [],
        "Priorités": [],
        "Conclusion - USJ reconnue pour": [],
        "Conclusion - Nos étudiants disent que": [],
        "Conclusion - Meilleur lieu de travail": [],
    }

    if not isinstance(data, dict):
        return extracted

    if "I - Forces et faiblesses" in data:
        extracted["Forces"].extend(extract_from_list(data.get("I - Forces et faiblesses", []), "Forces"))
        extracted["Faiblesses"].extend(extract_from_list(data.get("I - Forces et faiblesses", []), "Faiblesses"))

    if "II - Opportunités et menaces" in data:
        extracted["Opportunités"].extend(extract_from_list(data.get("II - Opportunités et menaces", []), "Opportunités"))
        extracted["Menaces"].extend(extract_from_list(data.get("II - Opportunités et menaces", []), "Menaces"))

    if "III - Priorités" in data:
        extracted["Priorités"].extend(extract_priorities(data.get("III - Priorités", {})))

    if "IV - Conclusion" in data:
        conc = extract_conclusion(data.get("IV - Conclusion", {}))
        for k, v in conc.items():
            extracted[k].extend(v)

    swot = data.get("swot_analysis", {})
    if isinstance(swot, dict):
        internal = swot.get("facteurs_internes", [])
        external = swot.get("facteurs_externes", [])
        extracted["Forces"].extend(extract_from_list(internal, "Forces"))
        extracted["Faiblesses"].extend(extract_from_list(internal, "Faiblesses"))
        extracted["Opportunités"].extend(extract_from_list(external, "Opportunités"))
        extracted["Menaces"].extend(extract_from_list(external, "Menaces"))

    if "priorities_initiatives" in data:
        extracted["Priorités"].extend(extract_priorities(data.get("priorities_initiatives", {})))

    if "pour_finir" in data:
        conc = extract_conclusion(data.get("pour_finir", {}))
        for k, v in conc.items():
            extracted[k].extend(v)

    for question in extracted:
        seen = set()
        cleaned = []
        for item in extracted[question]:
            item = clean_text(item)
            key = item.lower()
            if item and key not in seen:
                cleaned.append(item)
                seen.add(key)
        extracted[question] = cleaned

    return extracted


def build_long_answers_df(raw_df, source_name):
    rows = []

    for _, row in raw_df.iterrows():
        admin_json = safe_json_loads(row.get("admin_modified_answers_json", ""))
        original_json = safe_json_loads(row.get("original_answers_json", ""))

        used_source = "admin"
        data = admin_json

        if not data:
            used_source = "original_fallback"
            data = original_json

        extracted = normalize_admin_data(data)

        base = {
            "source_file": source_name,
            "draft_code": str(row.get("draft_code", "")),
            "stakeholder_category": detect_category(row),
            "subgroup": extract_subgroup(row),
            "participants": str(row.get("participants", row.get("respondent_name", ""))),
            "groupe": str(row.get("groupe", row.get("respondent_unit", ""))),
            "used_source": used_source,
        }

        for question, answers in extracted.items():
            for answer in answers:
                answer = clean_text(answer)
                if answer:
                    rows.append({**base, "question": question, "answer_text": answer})

    return pd.DataFrame(rows)


def infer_cluster_label(texts):
    if not texts:
        return "Thème non défini"

    try:
        vectorizer = TfidfVectorizer(stop_words=FRENCH_STOPWORDS, ngram_range=(1, 2), max_features=80, min_df=1)
        X = vectorizer.fit_transform(texts)
        scores = np.asarray(X.sum(axis=0)).ravel()
        terms = np.array(vectorizer.get_feature_names_out())
        top_terms = terms[np.argsort(scores)[::-1][:4]]
        label = " / ".join([t.title() for t in top_terms if len(t.strip()) > 2])
        return label or "Thème non défini"
    except Exception:
        return "Thème non défini"


def auto_group_answers(df, max_clusters_per_question=7):
    if df.empty:
        return df

    df = df.copy()
    df["ai_theme"] = ""
    df["cluster_id"] = ""

    for question, qdf in df.groupby("question"):
        indices = qdf.index.tolist()
        texts = qdf["answer_text"].fillna("").astype(str).tolist()

        if len(texts) == 1:
            df.loc[indices, "ai_theme"] = infer_cluster_label(texts)
            df.loc[indices, "cluster_id"] = f"{question}_1"
            continue

        try:
            vectorizer = TfidfVectorizer(stop_words=FRENCH_STOPWORDS, ngram_range=(1, 2), min_df=1, max_features=500)
            X = vectorizer.fit_transform(texts)

            n_clusters = min(max_clusters_per_question, max(2, int(np.sqrt(len(texts)))))
            n_clusters = min(n_clusters, len(texts))

            model = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
            labels = model.fit_predict(X)

            for cluster in sorted(set(labels)):
                local = [i for i, lab in enumerate(labels) if lab == cluster]
                cluster_texts = [texts[i] for i in local]
                theme_label = infer_cluster_label(cluster_texts)

                for i in local:
                    df.loc[indices[i], "ai_theme"] = theme_label
                    df.loc[indices[i], "cluster_id"] = f"{question}_{cluster + 1}"

        except Exception:
            df.loc[indices, "ai_theme"] = infer_cluster_label(texts)
            df.loc[indices, "cluster_id"] = f"{question}_1"

    df["final_theme"] = df["ai_theme"]
    return df


def merge_previous_validation(current_df, previous_df):
    if current_df.empty or previous_df.empty:
        return current_df

    key_cols = ["draft_code", "question", "answer_text"]
    prev = previous_df[key_cols + ["final_theme"]].drop_duplicates()

    merged = current_df.merge(prev, on=key_cols, how="left", suffixes=("", "_previous"))
    merged["final_theme"] = merged["final_theme_previous"].fillna(merged["final_theme"])
    return merged.drop(columns=["final_theme_previous"], errors="ignore")


def theme_counts(df):
    if df.empty:
        return pd.DataFrame(columns=["question", "final_theme", "n"])
    return df.groupby(["question", "final_theme"]).size().reset_index(name="n").sort_values(["question", "n"], ascending=[True, False])


def plot_theme_bar(df, question):
    qdf = df[df["question"] == question]
    if qdf.empty:
        st.info("Aucune donnée disponible pour cette question.")
        return

    counts = qdf.groupby("final_theme").size().reset_index(name="Nombre de réponses").sort_values("Nombre de réponses", ascending=True)

    fig = px.bar(counts, x="Nombre de réponses", y="final_theme", orientation="h", text="Nombre de réponses", title=f"Thèmes validés - {question}")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=max(420, 42 * len(counts)), title_font_size=22, font=dict(family="Candara, Calibri, Arial", size=15), margin=dict(l=20, r=40, t=70, b=30), yaxis_title="", xaxis_title="Nombre de réponses")
    st.plotly_chart(fig, use_container_width=True)


def plot_grouped_by_category(df, question):
    qdf = df[df["question"] == question]
    if qdf.empty:
        st.info("Aucune donnée disponible pour cette question.")
        return

    counts = qdf.groupby(["final_theme", "stakeholder_category"]).size().reset_index(name="Nombre")

    fig = px.bar(counts, x="final_theme", y="Nombre", color="stakeholder_category", barmode="group", text="Nombre", title=f"Comparaison par catégorie - {question}")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=520, xaxis_tickangle=-35, title_font_size=22, font=dict(family="Candara, Calibri, Arial", size=14), margin=dict(l=20, r=20, t=70, b=120), xaxis_title="Thème validé", yaxis_title="Nombre de réponses", legend_title="Catégorie")
    st.plotly_chart(fig, use_container_width=True)


def plot_heatmap(df):
    if df.empty:
        st.info("Aucune donnée disponible.")
        return

    counts = df.groupby(["stakeholder_category", "question"]).size().reset_index(name="Nombre")
    pivot = counts.pivot_table(index="stakeholder_category", columns="question", values="Nombre", fill_value=0)
    ordered_cols = [q for q in QUESTION_ORDER if q in pivot.columns]
    pivot = pivot[ordered_cols]

    fig = px.imshow(pivot, text_auto=True, aspect="auto", title="Volume des réponses par catégorie et par question")
    fig.update_layout(height=420, font=dict(family="Candara, Calibri, Arial", size=14), title_font_size=22, margin=dict(l=20, r=20, t=70, b=30))
    st.plotly_chart(fig, use_container_width=True)


def create_swot_html(df):
    def top_items(question, n=5):
        qdf = df[df["question"] == question]
        if qdf.empty:
            return []
        counts = qdf.groupby("final_theme").size().reset_index(name="n").sort_values("n", ascending=False)
        return [f"{row['final_theme']} ({row['n']})" for _, row in counts.head(n).iterrows()]

    cards = [
        ("FORCES", "Forces", top_items("Forces"), "#001F5B", "#DDEFF7"),
        ("FAIBLESSES", "Faiblesses", top_items("Faiblesses"), "#8B1538", "#FBE3C3"),
        ("OPPORTUNITÉS", "Opportunités", top_items("Opportunités"), "#2F6B2F", "#E2F2D3"),
        ("MENACES", "Menaces", top_items("Menaces"), "#C00000", "#F4C6C4"),
    ]

    cards_html = ""
    total_items = 0

    for title, question, items, accent, bg in cards:
        total_items += len(items)
        if not items:
            items_html = '<div class="swot-item"><div class="swot-index">0</div><div class="swot-text">Aucun thème validé.</div></div>'
        else:
            items_html = ""
            for i, item in enumerate(items, start=1):
                items_html += f'''
<div class="swot-item">
    <div class="swot-index">{i}</div>
    <div class="swot-text">{html.escape(item)}</div>
</div>
'''
        cards_html += f'''
<div class="swot-card" style="--accent:{accent}; --bg:{bg};">
    <div class="swot-title">{title}</div>
    {items_html}
</div>
'''

    return f'''
<div class="swot-shell">
    <div class="swot-header">
        <div class="swot-heading">
            <h1>Matrice SWOT - Synthèse validée</h1>
            <p>Thèmes finaux validés à partir des réponses admin</p>
        </div>
        <div class="swot-badge">{total_items} thèmes affichés</div>
    </div>
    <div class="swot-grid">
        {cards_html}
    </div>
</div>
'''


def make_excel_export(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Answers_Validated")
        theme_counts(df).to_excel(writer, index=False, sheet_name="Theme_Counts")
        by_cat = df.groupby(["stakeholder_category", "question", "final_theme"]).size().reset_index(name="n").sort_values(["stakeholder_category", "question", "n"], ascending=[True, True, False])
        by_cat.to_excel(writer, index=False, sheet_name="By_Category")
    buffer.seek(0)
    return buffer.getvalue()


def generate_text_report(df):
    if df.empty:
        return "Aucune donnée disponible."

    lines = []
    lines.append("PLAN STRATÉGIQUE USJ 2032")
    lines.append("Rapport automatique d'analyse des focus groupes")
    lines.append("")
    lines.append(f"Nombre total de réponses analysées : {len(df)}")
    lines.append(f"Nombre de catégories de répondants : {df['stakeholder_category'].nunique()}")
    lines.append(f"Nombre de thèmes finaux : {df['final_theme'].nunique()}")
    lines.append("")

    for question in QUESTION_ORDER:
        qdf = df[df["question"] == question]
        if qdf.empty:
            continue

        lines.append("=" * 80)
        lines.append(question.upper())
        lines.append("=" * 80)

        counts = qdf.groupby("final_theme").size().reset_index(name="n").sort_values("n", ascending=False)
        for _, row in counts.iterrows():
            lines.append(f"- {row['final_theme']} : {row['n']} réponse(s)")

        lines.append("")
        lines.append("Exemples de réponses :")
        for answer in qdf["answer_text"].drop_duplicates().head(8):
            lines.append(f"  • {answer}")
        lines.append("")

    return "\n".join(lines)


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="📊", layout="wide", initial_sidebar_state="expanded")
    init_db()
    apply_style()
    hero()

    with st.sidebar:
        st.markdown("## Navigation")
        page = st.radio(
            "Choisir une page",
            [
                "1. Charger les données",
                "2. Dashboard global",
                "3. Validation admin des thèmes",
                "4. Visualisations",
                "5. Matrice SWOT",
                "6. Rapport et exports",
            ],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### Paramètres")
        max_clusters = st.slider("Nombre maximum de thèmes IA par question", min_value=3, max_value=12, value=7, step=1)

    if "answers_df" not in st.session_state:
        st.session_state["answers_df"] = pd.DataFrame()

    if "source_file" not in st.session_state:
        st.session_state["source_file"] = ""

    if page == "1. Charger les données":
        section_title("1. Charger l’export Excel")

        st.markdown('''
<div class="note-box">
Chargez l’export Excel contenant les colonnes <b>admin_modified_answers_json</b> et <b>original_answers_json</b>.
La plateforme analysera en priorité les réponses modifiées par l’admin.
</div>
''', unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Importer le fichier Excel", type=["xlsx", "xls"])

        if uploaded_file is not None:
            source_name = uploaded_file.name
            raw_df = pd.read_excel(uploaded_file)

            st.write("Aperçu du fichier importé")
            st.dataframe(raw_df.head(20), use_container_width=True)

            if not {"admin_modified_answers_json", "original_answers_json"}.intersection(set(raw_df.columns)):
                st.error("Le fichier ne contient pas les colonnes JSON attendues.")
                st.stop()

            if st.button("Extraire les réponses admin et générer les thèmes IA", type="primary"):
                long_df = build_long_answers_df(raw_df, source_name)

                if long_df.empty:
                    st.error("Aucune réponse exploitable n’a été trouvée.")
                    st.stop()

                grouped_df = auto_group_answers(long_df, max_clusters_per_question=max_clusters)
                previous = load_validated_groupings(source_name)
                grouped_df = merge_previous_validation(grouped_df, previous)

                st.session_state["answers_df"] = grouped_df
                st.session_state["source_file"] = source_name
                st.success(f"{len(grouped_df)} réponses extraites et regroupées automatiquement.")

        if not st.session_state["answers_df"].empty:
            section_title("Données actuellement chargées")
            st.dataframe(st.session_state["answers_df"].head(100), use_container_width=True)

            fallback_n = (st.session_state["answers_df"]["used_source"] == "original_fallback").sum()
            if fallback_n:
                st.warning(f"{fallback_n} réponse(s) utilisent original_answers_json car admin_modified_answers_json était vide.")

    elif page == "2. Dashboard global":
        df = st.session_state["answers_df"]
        if df.empty:
            st.warning("Veuillez d’abord charger un fichier Excel.")
            st.stop()

        section_title("2. Dashboard global")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Réponses analysées", len(df))
        with c2:
            metric_card("Catégories", df["stakeholder_category"].nunique())
        with c3:
            metric_card("Sous-groupes", df["subgroup"].nunique())
        with c4:
            metric_card("Thèmes finaux", df["final_theme"].nunique())

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            counts_q = df.groupby("question").size().reset_index(name="Nombre")
            fig = px.bar(counts_q, x="question", y="Nombre", text="Nombre", title="Nombre de réponses par question")
            fig.update_traces(textposition="outside")
            fig.update_layout(xaxis_tickangle=-35, height=460)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            counts_cat = df.groupby("stakeholder_category").size().reset_index(name="Nombre")
            fig = px.pie(counts_cat, values="Nombre", names="stakeholder_category", title="Répartition par catégorie")
            fig.update_layout(height=460)
            st.plotly_chart(fig, use_container_width=True)

        plot_heatmap(df)

    elif page == "3. Validation admin des thèmes":
        df = st.session_state["answers_df"]
        if df.empty:
            st.warning("Veuillez d’abord charger un fichier Excel.")
            st.stop()

        section_title("3. Validation admin des regroupements")
        st.markdown('''
<div class="note-box">
Modifiez la colonne <b>final_theme</b> si vous souhaitez corriger les thèmes proposés par l’algorithme.
La colonne <b>ai_theme</b> reste conservée.
</div>
''', unsafe_allow_html=True)

        selected_category = st.multiselect("Filtrer par catégorie", options=sorted(df["stakeholder_category"].dropna().unique()), default=sorted(df["stakeholder_category"].dropna().unique()))
        selected_question = st.multiselect("Filtrer par question", options=[q for q in QUESTION_ORDER if q in df["question"].unique()], default=[q for q in QUESTION_ORDER if q in df["question"].unique()])

        view_df = df[df["stakeholder_category"].isin(selected_category) & df["question"].isin(selected_question)].copy()

        editable_cols = ["draft_code", "stakeholder_category", "subgroup", "question", "answer_text", "ai_theme", "final_theme"]

        edited = st.data_editor(
            view_df[editable_cols],
            use_container_width=True,
            height=620,
            num_rows="fixed",
            column_config={
                "answer_text": st.column_config.TextColumn("Réponse admin", width="large"),
                "ai_theme": st.column_config.TextColumn("Thème IA", width="medium"),
                "final_theme": st.column_config.TextColumn("Thème final admin", width="medium"),
            },
            disabled=["draft_code", "stakeholder_category", "subgroup", "question", "answer_text", "ai_theme"],
            key="validation_editor"
        )

        if st.button("Enregistrer les thèmes validés", type="primary"):
            updated_df = df.copy()

            for _, row in edited.iterrows():
                mask = (
                    (updated_df["draft_code"] == row["draft_code"]) &
                    (updated_df["question"] == row["question"]) &
                    (updated_df["answer_text"] == row["answer_text"])
                )
                updated_df.loc[mask, "final_theme"] = row["final_theme"]

            st.session_state["answers_df"] = updated_df
            save_validated_groupings(updated_df, st.session_state["source_file"])
            st.success("Thèmes finaux enregistrés.")

    elif page == "4. Visualisations":
        df = st.session_state["answers_df"]
        if df.empty:
            st.warning("Veuillez d’abord charger un fichier Excel.")
            st.stop()

        section_title("4. Visualisations des résultats")
        question = st.selectbox("Choisir une question", options=[q for q in QUESTION_ORDER if q in df["question"].unique()])
        plot_theme_bar(df, question)
        plot_grouped_by_category(df, question)

        section_title("Table des thèmes")
        st.dataframe(theme_counts(df), use_container_width=True)

    elif page == "5. Matrice SWOT":
        df = st.session_state["answers_df"]
        if df.empty:
            st.warning("Veuillez d’abord charger un fichier Excel.")
            st.stop()

        section_title("5. Matrice SWOT interactive")
        category_filter = st.multiselect("Afficher certaines catégories", options=sorted(df["stakeholder_category"].dropna().unique()), default=sorted(df["stakeholder_category"].dropna().unique()))
        fdf = df[df["stakeholder_category"].isin(category_filter)].copy()

        st.markdown(create_swot_html(fdf), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            plot_theme_bar(fdf, "Forces")
        with col2:
            plot_theme_bar(fdf, "Faiblesses")

        col3, col4 = st.columns(2)
        with col3:
            plot_theme_bar(fdf, "Opportunités")
        with col4:
            plot_theme_bar(fdf, "Menaces")

    elif page == "6. Rapport et exports":
        df = st.session_state["answers_df"]
        if df.empty:
            st.warning("Veuillez d’abord charger un fichier Excel.")
            st.stop()

        section_title("6. Rapport automatique et exports")
        report_text = generate_text_report(df)

        st.text_area("Rapport généré automatiquement", value=report_text, height=520)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button("Télécharger le rapport TXT", data=report_text.encode("utf-8"), file_name="rapport_strategique_usj_2032.txt", mime="text/plain", use_container_width=True)

        with col2:
            excel_data = make_excel_export(df)
            st.download_button("Télécharger l’export Excel validé", data=excel_data, file_name="analyse_strategique_usj_2032.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


if __name__ == "__main__":
    main()
