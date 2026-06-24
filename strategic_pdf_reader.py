#!/usr/bin/env python
# coding: utf-8

import sqlite3
import json
import base64
import html as html_lib
import re
from datetime import datetime
from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

APP_TITLE = "PLAN STRATÉGIQUE USJ 2032"
APP_SUBTITLE = "Strategic PDF Reader Platform"

if Path("/home/site").exists():
    DB_DIR = Path("/home/data")
else:
    DB_DIR = Path(".")

DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "strategic_pdf_reports.db"

LOGO_PATH = Path("LogoUAQ.png")

USJ_BLUE = "#001F5B"
USJ_BLUE_2 = "#1F3C88"
USJ_RED = "#8B1538"
USJ_GOLD = "#C9A227"
USJ_LIGHT_BLUE = "#EAF2F8"
USJ_TEXT = "#1B2A41"

ADMIN_CODE = "USJ-ADMIN-2032"
DIRECTOR_CODE = "USJ-DIRECTOR-2032"

RESPONDENT_TYPES = [
    "Anciens",
    "PSG",
    "Directors",
    "Students",
    "Teachers",
]

SUBGROUPS = [f"Sous groupe {i}" for i in range(1, 11)]

SECTION_LABELS = [
    "I - Forces et Faiblesses",
    "II - Opportunités et Menaces",
    "III - Priorités",
    "IV - Conclusion",
]

ADMIN_FIELDS = {
    "I - Forces et Faiblesses": ["Forces", "Faiblesses"],
    "II - Opportunités et Menaces": ["Opportunités", "Menaces"],
    "III - Priorités": ["Priorités"],
    "IV - Conclusion": ["Conclusion"],
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
.main .block-container, div[data-testid="stAppViewContainer"] .block-container {{
    padding-left:3rem !important;
    padding-right:3rem !important;
    max-width:100% !important;
}}
h1, h2, h3, h4, h5, h6 {{
    color:{USJ_BLUE} !important;
    font-family: Candara, Calibri, Arial, sans-serif !important;
    font-weight:800 !important;
}}
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
    background-color:#E3DED9 !important;
    color:#000000 !important;
    border:none !important;
    border-radius:6px !important;
}}
div[data-testid="stTextArea"] textarea {{
    border:1px solid #595959 !important;
    line-height:1.35 !important;
}}
.stButton button, .stDownloadButton button, div[data-testid="stFormSubmitButton"] button {{
    background-color:#0070C0 !important;
    color:white !important;
    border-radius:8px !important;
    border:1px solid #0070C0 !important;
    font-weight:800 !important;
    font-size:17px !important;
    padding:9px 18px !important;
}}
.stButton button p, .stDownloadButton button p, div[data-testid="stFormSubmitButton"] button p {{
    color:white !important;
}}
button[kind="primary"] {{
    background-color:{USJ_RED} !important;
    border-color:{USJ_RED} !important;
}}
.usj-card {{
    background:#ffffff;
    padding:20px 24px;
    border-radius:12px;
    border:1px solid #E2E8F0;
    box-shadow:0 2px 10px rgba(0,0,0,0.06);
    margin-bottom:18px;
}}
.usj-small-card {{
    background:{USJ_LIGHT_BLUE};
    padding:14px 18px;
    border-radius:10px;
    border-left:7px solid {USJ_BLUE};
    margin-top:6px;
    margin-bottom:12px;
}}
.readonly-answer {{
    background:#F7FAFD;
    border:1px solid #D6DEE8;
    border-left:6px solid {USJ_BLUE};
    padding:12px 16px;
    border-radius:8px;
    margin:8px 0;
    font-size:17px;
    line-height:1.4;
}}
.meta-badge {{
    display:inline-block;
    background:{USJ_BLUE};
    color:white;
    border-radius:999px;
    padding:6px 12px;
    margin-right:8px;
    font-weight:800;
}}

/* Clean file uploader. Hide Streamlit native duplicated text and draw one label. */
div[data-testid="stFileUploader"] section {{
    padding: 12px 14px !important;
    background-color: #F1F4F8 !important;
    border: none !important;
    border-radius: 8px !important;
}}
div[data-testid="stFileUploader"] section button {{
    min-width: 150px !important;
    width: 150px !important;
    height: 42px !important;
    position: relative !important;
    overflow: hidden !important;
    color: transparent !important;
    font-size: 0 !important;
    line-height: 0 !important;
    background-color: #ffffff !important;
    border: 1px solid #D0D6E0 !important;
    border-radius: 8px !important;
}}
div[data-testid="stFileUploader"] section button * {{
    display: none !important;
    visibility: hidden !important;
    color: transparent !important;
    font-size: 0 !important;
}}
div[data-testid="stFileUploader"] section button::after {{
    content: "Choisir un PDF";
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #001F5B !important;
    font-size: 15px !important;
    line-height: 1 !important;
    font-weight: 800 !important;
    font-family: Candara, Calibri, Arial, sans-serif !important;
}}
div[data-testid="stFileUploader"] small {{
    font-size: 14px !important;
}}


/* FINAL uploader override: remove Streamlit duplicated upload text completely. */
div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button,
div[data-testid="stFileUploader"] button,
div[data-testid="stFileUploader"] button[kind],
div[data-testid="stFileUploader"] button[data-testid] {{
    width: 165px !important;
    min-width: 165px !important;
    max-width: 165px !important;
    height: 44px !important;
    min-height: 44px !important;
    max-height: 44px !important;
    padding: 0 !important;
    margin: 0 !important;
    position: relative !important;
    overflow: hidden !important;
    text-indent: -9999px !important;
    font-size: 0 !important;
    line-height: 0 !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    background: #ffffff !important;
    border: 1px solid #D0D6E0 !important;
    border-radius: 8px !important;
}}

div[data-testid="stFileUploader"] button *,
div[data-testid="stFileUploader"] button p,
div[data-testid="stFileUploader"] button span,
div[data-testid="stFileUploader"] button svg {{
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    font-size: 0 !important;
    line-height: 0 !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
}}

div[data-testid="stFileUploader"] button::before {{
    content: "Choisir un PDF" !important;
    position: absolute !important;
    inset: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-indent: 0 !important;
    font-family: Candara, Calibri, Arial, sans-serif !important;
    font-size: 15px !important;
    line-height: 1 !important;
    font-weight: 800 !important;
    color: #001F5B !important;
    -webkit-text-fill-color: #001F5B !important;
    white-space: nowrap !important;
}}

</style>
""")


def render_header():
    logo_src = image_to_base64(LOGO_PATH)
    logo_html = f'<img src="{logo_src}" style="width:330px; max-width:100%; height:auto;">' if logo_src else ""
    html_block(f"""
<div style="display:flex; align-items:flex-start; justify-content:space-between; gap:28px; margin-bottom:22px;">
    <div style="flex:1;">
        <h1 style="font-size:42px; margin:0 0 10px 0; line-height:1.1;">{APP_TITLE}</h1>
        <p style="font-size:23px; color:{USJ_BLUE_2}; font-weight:800; margin:0;">{APP_SUBTITLE}</p>
        <p style="font-size:17px; color:#4F5B6B; font-weight:600; margin-top:8px;">PDF Upload → Extraction → Admin Correction → Director Browse</p>
    </div>
    <div style="width:340px; text-align:right;">{logo_html}</div>
</div>
<hr style="border:none; height:3px; background:#D0D6E0; margin:10px 0 22px 0;">
""")


def section_header(title):
    html_block(f"""
<div class="usj-small-card">
    <h2 style="font-size:25px; margin:0;">{html_lib.escape(title)}</h2>
</div>
""")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pdf_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uploaded_at TEXT,
            respondent_type TEXT,
            subgroup TEXT,
            filename TEXT,
            raw_text TEXT,
            parsed_json TEXT,
            admin_json TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS extracted_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            respondent_type TEXT,
            subgroup TEXT,
            section TEXT,
            category TEXT,
            answer_text TEXT,
            FOREIGN KEY(report_id) REFERENCES pdf_reports(id)
        )
    """)
    conn.commit()
    conn.close()


def extract_text_from_pdf(uploaded_pdf):
    if fitz is None:
        raise ImportError("PyMuPDF is not installed. Add pymupdf to requirements.txt.")

    pdf_bytes = uploaded_pdf.getvalue()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []

    for page in doc:
        pages_text.append(page.get_text("text"))

    return "\n".join(pages_text)



def _block_text(value):
    text = str(value or "")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def extract_pdf_blocks_with_layout(uploaded_pdf):
    """Return PDF text blocks with coordinates. A filled answer box is usually one block."""
    if fitz is None:
        raise ImportError("PyMuPDF is not installed. Add pymupdf to requirements.txt.")

    pdf_bytes = uploaded_pdf.getvalue()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    blocks = []

    for page_index, page in enumerate(doc):
        page_width = float(page.rect.width)
        raw_blocks = page.get_text("blocks")
        for b in raw_blocks:
            if len(b) < 5:
                continue
            x0, y0, x1, y1, text = b[:5]
            text = _block_text(text)
            if not text:
                continue
            blocks.append({
                "page": page_index,
                "page_width": page_width,
                "x0": float(x0),
                "x1": float(x1),
                "y0": float(y0),
                "y1": float(y1),
                "text": text,
                "norm": normalize_for_match(text),
            })

    blocks.sort(key=lambda d: (d["page"], d["y0"], d["x0"]))
    return blocks


def _is_section_heading(norm_text, section_no=None):
    norm_text = normalize_for_match(norm_text)
    if section_no == 1:
        return bool(re.search(r"\bi\s*[-–—.]?\s*forces\s+et\s+faiblesses", norm_text))
    if section_no == 2:
        return bool(re.search(r"\bii\s*[-–—.]?\s*opportunites\s+et\s+menaces", norm_text))
    if section_no == 3:
        return bool(re.search(r"\biii\s*[-–—.]?\s*prior", norm_text))
    if section_no == 4:
        return bool(re.search(r"\biv\s*[-–—.]?\s*conclusion", norm_text))
    return bool(re.search(r"\b(i|ii|iii|iv)\s*[-–—.]?", norm_text))


def _clean_answer_line_for_layout(text):
    line = clean_text(text)
    line = re.sub(r"^[\u2022\-*–—\d\.\)\s]+", "", line).strip()
    line = re.sub(r"\s+", " ", line)
    norm = normalize_for_match(line)

    blocked_exact = {
        "", "et", "forces", "faiblesses", "opportunites", "menaces",
        "priorites", "priorite", "conclusion", "niveau usj"
    }
    if norm in blocked_exact:
        return ""

    blocked_fragments = [
        "i - forces et faiblesses", "ii - opportunites et menaces",
        "iii - priorites", "iv - conclusion", "maximum cinq", "merci de",
        "quels sont", "thematique", "importer le rapport", "plan strategique",
        "verification et correction", "ajouter une ligne"
    ]
    if any(fragment in norm for fragment in blocked_fragments):
        return ""
    return line


def _split_possible_combined_answers(text):
    """Split a PDF block when several answer boxes were merged by PDF extraction."""
    text = _block_text(text)
    if not text:
        return []

    # Remove category headings accidentally included inside the block.
    text = re.sub(r"(?i)^\s*(forces|faiblesses|opportunit[eé]s|menaces|priorit[eé]s|conclusion)\s*[:：]?\s*", "", text).strip()
    text = re.sub(r"(?i)\b(faiblesses|opportunit[eé]s|menaces|priorit[eé]s|conclusion)\s*[:：]?\s*", "\n", text)

    raw_parts = []
    for line in text.splitlines():
        line = _clean_answer_line_for_layout(line)
        if not line:
            continue
        raw_parts.append(line)

    if not raw_parts:
        return []

    parts = []
    starters = (
        "Les ", "Le ", "La ", "L’", "L'", "Il ", "On ", "Manque ", "Trop ",
        "Matériel ", "Materiel ", "Insuffisance ", "Formation ", "Corps ",
        "Clarté ", "Clarte ", "Instabilité ", "Instabilite ", "Possibilités ",
        "Possibilites ", "La vague ", "Au ouvre ", "Le marché ", "Les universités ",
        "L’évolution ", "L'evolution "
    )

    for part in raw_parts:
        # Split only when a long paragraph clearly contains several short answers.
        if len(part) > 130:
            pattern = r"(?<=[\.?!])\s+(?=(?:" + "|".join(re.escape(x) for x in starters) + r"))"
            subparts = re.split(pattern, part)
        else:
            subparts = [part]
        for sp in subparts:
            sp = _clean_answer_line_for_layout(sp)
            if sp:
                parts.append(sp)

    cleaned = []
    seen = set()
    for part in parts:
        key = normalize_for_match(part)
        if key not in seen:
            cleaned.append(part)
            seen.add(key)
    return cleaned


def _slice_section_blocks(blocks, section_no, next_section_no):
    start_idx = None
    end_idx = len(blocks)
    for i, block in enumerate(blocks):
        if _is_section_heading(block["norm"], section_no):
            start_idx = i
            break
    if start_idx is None:
        return []
    for j in range(start_idx + 1, len(blocks)):
        if next_section_no and _is_section_heading(blocks[j]["norm"], next_section_no):
            end_idx = j
            break
    return blocks[start_idx:end_idx]


def _extract_two_column_section(blocks, section_no, left_header, right_header, next_section_no):
    section_blocks = _slice_section_blocks(blocks, section_no, next_section_no)
    if not section_blocks:
        return [], []

    left_norm = normalize_for_match(left_header)
    right_norm = normalize_for_match(right_header)

    header_y = None
    for block in section_blocks:
        norm = normalize_for_match(block["text"])
        if norm in {left_norm, right_norm}:
            header_y = block["y0"] if header_y is None else min(header_y, block["y0"])

    if header_y is None:
        # Use the first occurrence of either header as the table header line.
        for block in section_blocks:
            if left_norm in block["norm"] or right_norm in block["norm"]:
                header_y = block["y0"]
                break

    left_items, right_items = [], []
    for block in section_blocks:
        if header_y is not None and block["y0"] <= header_y + 8:
            continue

        # Skip any block that is basically a heading.
        if not _clean_answer_line_for_layout(block["text"]):
            continue

        x_center = (block["x0"] + block["x1"]) / 2.0
        page_mid = block["page_width"] / 2.0
        target = left_items if x_center < page_mid else right_items
        target.extend(_split_possible_combined_answers(block["text"]))

    return _dedupe_answers(left_items), _dedupe_answers(right_items)


def _extract_single_column_section(blocks, section_no, next_section_no):
    section_blocks = _slice_section_blocks(blocks, section_no, next_section_no)
    if not section_blocks:
        return []
    items = []
    for block in section_blocks[1:]:
        if _clean_answer_line_for_layout(block["text"]):
            items.extend(_split_possible_combined_answers(block["text"]))
    return _dedupe_answers(items)


def _dedupe_answers(items):
    cleaned = []
    seen = set()
    for item in items:
        item = _clean_answer_line_for_layout(item)
        if not item:
            continue
        norm = normalize_for_match(item)
        if norm not in seen:
            cleaned.append(item)
            seen.add(norm)
    return cleaned


def parse_report_pdf_layout(uploaded_pdf, raw_text=None):
    """Primary parser: reads visual PDF blocks, preserving left/right answer boxes."""
    blocks = extract_pdf_blocks_with_layout(uploaded_pdf)

    forces, faiblesses = _extract_two_column_section(
        blocks, 1, "Forces", "Faiblesses", 2
    )
    opportunites, menaces = _extract_two_column_section(
        blocks, 2, "Opportunités", "Menaces", 3
    )
    priorites = _extract_single_column_section(blocks, 3, 4)
    conclusion = _extract_single_column_section(blocks, 4, None)

    parsed = {
        "I - Forces et Faiblesses": {
            "Forces": forces,
            "Faiblesses": faiblesses,
        },
        "II - Opportunités et Menaces": {
            "Opportunités": opportunites,
            "Menaces": menaces,
        },
        "III - Priorités": {
            "Priorités": priorites,
        },
        "IV - Conclusion": {
            "Conclusion": conclusion,
        },
        "_section_text": {}
    }

    has_values = any(parsed[s][c] for s in ADMIN_FIELDS for c in ADMIN_FIELDS[s])
    if raw_text and not has_values:
        parsed = parse_report_text(raw_text)

    return parsed


def clean_text(value):
    value = str(value or "")
    value = value.replace("\u00a0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def normalize_for_match(value):
    value = str(value or "").lower()
    replacements = {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a", "ù": "u", "û": "u",
        "î": "i", "ï": "i", "ô": "o", "ç": "c",
        "’": "'",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def split_items(text):
    text = clean_text(text)
    if not text:
        return []

    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        line = re.sub(r"^[\u2022\-*–—\d\.\)\s]+", "", line).strip()
        line = re.sub(r"\s+", " ", line)
        if not line:
            continue

        line_norm = normalize_for_match(line)
        blocked = [
            "maximum cinq", "merci de", "thematique", "niveau usj",
            "quels sont", "reponse", "annexe", "plan strategique",
        ]
        if any(fragment in line_norm for fragment in blocked) and len(line.split()) < 18:
            continue

        lines.append(line)

    if len(lines) <= 1 and ";" in text:
        lines = [part.strip() for part in text.split(";") if part.strip()]

    seen = set()
    cleaned = []
    for line in lines:
        key = normalize_for_match(line)
        if key not in seen:
            cleaned.append(line)
            seen.add(key)
    return cleaned


def extract_section(raw_text, start_keywords, end_keywords):
    text = clean_text(raw_text)
    norm = normalize_for_match(text)

    start_pos = None
    for keyword in start_keywords:
        m = re.search(keyword, norm, flags=re.IGNORECASE)
        if m:
            start_pos = m.start()
            break

    if start_pos is None:
        return ""

    end_pos = len(text)
    after = norm[start_pos + 10:]
    for keyword in end_keywords:
        m = re.search(keyword, after, flags=re.IGNORECASE)
        if m:
            end_pos = start_pos + 10 + m.start()
            break

    return clean_text(text[start_pos:end_pos])


def extract_category_text(section_text, category_keywords, next_category_keywords):
    section_text = clean_text(section_text)
    norm = normalize_for_match(section_text)

    start_pos = None
    for keyword in category_keywords:
        m = re.search(keyword, norm, flags=re.IGNORECASE)
        if m:
            start_pos = m.end()
            break

    if start_pos is None:
        return ""

    end_pos = len(section_text)
    after = norm[start_pos:]
    for keyword in next_category_keywords:
        m = re.search(keyword, after, flags=re.IGNORECASE)
        if m:
            end_pos = start_pos + m.start()
            break

    return clean_text(section_text[start_pos:end_pos])


def parse_report_text(raw_text):
    text = clean_text(raw_text)

    section_i = extract_section(
        text,
        [r"\bi\s*[-–—.]?\s*forces", r"forces\s+et\s+faiblesses"],
        [r"\bii\s*[-–—.]?\s*opportun", r"opportunites\s+et\s+menaces"]
    )
    section_ii = extract_section(
        text,
        [r"\bii\s*[-–—.]?\s*opportun", r"opportunites\s+et\s+menaces"],
        [r"\biii\s*[-–—.]?\s*prior", r"priorites"]
    )
    section_iii = extract_section(
        text,
        [r"\biii\s*[-–—.]?\s*prior", r"priorites"],
        [r"\biv\s*[-–—.]?\s*conclusion", r"conclusion"]
    )
    section_iv = extract_section(
        text,
        [r"\biv\s*[-–—.]?\s*conclusion", r"conclusion"],
        []
    )

    forces_text = extract_category_text(section_i, [r"forces?\s*:?"] , [r"faiblesses?\s*:?"])
    faiblesses_text = extract_category_text(section_i, [r"faiblesses?\s*:?"] , [])
    opportunites_text = extract_category_text(section_ii, [r"opportunites?\s*:?"] , [r"menaces?\s*:?"])
    menaces_text = extract_category_text(section_ii, [r"menaces?\s*:?"] , [])

    parsed = {
        "I - Forces et Faiblesses": {
            "Forces": split_items(forces_text) if forces_text else [],
            "Faiblesses": split_items(faiblesses_text) if faiblesses_text else [],
        },
        "II - Opportunités et Menaces": {
            "Opportunités": split_items(opportunites_text) if opportunites_text else [],
            "Menaces": split_items(menaces_text) if menaces_text else [],
        },
        "III - Priorités": {
            "Priorités": split_items(section_iii),
        },
        "IV - Conclusion": {
            "Conclusion": split_items(section_iv) if section_iv else [],
        },
        "_section_text": {
            "I - Forces et Faiblesses": section_i,
            "II - Opportunités et Menaces": section_ii,
            "III - Priorités": section_iii,
            "IV - Conclusion": section_iv,
        }
    }

    return parsed


def json_to_text_lines(data, section, category):
    values = data.get(section, {}).get(category, []) if isinstance(data, dict) else []
    if isinstance(values, list):
        return "\n".join(str(v).strip() for v in values if str(v).strip())
    return str(values or "")


def text_lines_to_list(value):
    return [line.strip() for line in str(value or "").splitlines() if line.strip()]


def save_report(respondent_type, subgroup, filename, raw_text, parsed_json, admin_json):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pdf_reports (
            uploaded_at, respondent_type, subgroup, filename,
            raw_text, parsed_json, admin_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        respondent_type,
        subgroup,
        filename,
        raw_text,
        json.dumps(parsed_json, ensure_ascii=False),
        json.dumps(admin_json, ensure_ascii=False),
    ))
    report_id = cur.lastrowid
    refresh_extracted_answers(cur, report_id, respondent_type, subgroup, admin_json)
    conn.commit()
    conn.close()
    return report_id


def update_report_admin_json(report_id, admin_json):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    row = cur.execute("SELECT respondent_type, subgroup FROM pdf_reports WHERE id = ?", (report_id,)).fetchone()
    if not row:
        conn.close()
        return
    respondent_type, subgroup = row
    cur.execute("UPDATE pdf_reports SET admin_json = ? WHERE id = ?", (
        json.dumps(admin_json, ensure_ascii=False), report_id
    ))
    refresh_extracted_answers(cur, report_id, respondent_type, subgroup, admin_json)
    conn.commit()
    conn.close()


def refresh_extracted_answers(cur, report_id, respondent_type, subgroup, admin_json):
    cur.execute("DELETE FROM extracted_answers WHERE report_id = ?", (report_id,))
    for section, fields in ADMIN_FIELDS.items():
        for category in fields:
            for answer in admin_json.get(section, {}).get(category, []):
                answer = str(answer or "").strip()
                if answer:
                    cur.execute("""
                        INSERT INTO extracted_answers (
                            report_id, respondent_type, subgroup, section, category, answer_text
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (report_id, respondent_type, subgroup, section, category, answer))


def load_reports():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM pdf_reports ORDER BY respondent_type, subgroup, uploaded_at DESC", conn)
    conn.close()
    return df


def load_report(report_id):
    conn = sqlite3.connect(DB_PATH)
    row = pd.read_sql_query("SELECT * FROM pdf_reports WHERE id = ?", conn, params=(report_id,))
    conn.close()
    if row.empty:
        return None
    return row.iloc[0]


def delete_report(report_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM extracted_answers WHERE report_id = ?", (report_id,))
    cur.execute("DELETE FROM pdf_reports WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()


def build_export_df():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT r.id AS report_id, r.uploaded_at, r.respondent_type, r.subgroup,
               r.filename, a.section, a.category, a.answer_text
        FROM pdf_reports r
        LEFT JOIN extracted_answers a ON r.id = a.report_id
        ORDER BY r.respondent_type, r.subgroup, r.id, a.section, a.category, a.id
    """, conn)
    conn.close()
    return df


def _get_base_list(base_json, section, category):
    if not isinstance(base_json, dict):
        return []
    values = base_json.get(section, {}).get(category, [])
    if isinstance(values, list):
        return [str(v).strip() for v in values if str(v).strip()]
    if isinstance(values, str):
        return text_lines_to_list(values)
    return []


def render_admin_json_editor(base_json, key_prefix):
    edited = {}

    for section in SECTION_LABELS:
        section_header(section)
        edited[section] = {}
        fields = ADMIN_FIELDS[section]

        if len(fields) == 2:
            left_field, right_field = fields
            left_values = _get_base_list(base_json, section, left_field)
            right_values = _get_base_list(base_json, section, right_field)

            rows_key = f"{key_prefix}_{section}_rows"
            if rows_key not in st.session_state:
                st.session_state[rows_key] = max(5, len(left_values), len(right_values))

            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown(f"### {left_field}")
            with col_right:
                st.markdown(f"### {right_field}")

            left_result = []
            right_result = []

            for i in range(st.session_state[rows_key]):
                col_left, col_right = st.columns(2)

                with col_left:
                    default = left_values[i] if i < len(left_values) else ""
                    session_key = f"{key_prefix}_{section}_{left_field}_{i}"
                    if session_key not in st.session_state:
                        st.session_state[session_key] = default
                    st.text_area(
                        f"{left_field} {i + 1}",
                        key=session_key,
                        height=92,
                        label_visibility="collapsed",
                    )
                    value = str(st.session_state.get(session_key, "")).strip()
                    if value:
                        left_result.append(value)

                with col_right:
                    default = right_values[i] if i < len(right_values) else ""
                    session_key = f"{key_prefix}_{section}_{right_field}_{i}"
                    if session_key not in st.session_state:
                        st.session_state[session_key] = default
                    st.text_area(
                        f"{right_field} {i + 1}",
                        key=session_key,
                        height=92,
                        label_visibility="collapsed",
                    )
                    value = str(st.session_state.get(session_key, "")).strip()
                    if value:
                        right_result.append(value)

            if st.button("+ Ajouter une ligne", key=f"{key_prefix}_{section}_add_row"):
                st.session_state[rows_key] += 1
                st.rerun()

            edited[section][left_field] = left_result
            edited[section][right_field] = right_result

        else:
            category = fields[0]
            values = _get_base_list(base_json, section, category)

            rows_key = f"{key_prefix}_{section}_{category}_rows"
            if rows_key not in st.session_state:
                st.session_state[rows_key] = max(3, len(values))

            st.markdown(f"### {category}")
            result = []

            for i in range(st.session_state[rows_key]):
                default = values[i] if i < len(values) else ""
                session_key = f"{key_prefix}_{section}_{category}_{i}"
                if session_key not in st.session_state:
                    st.session_state[session_key] = default
                st.text_area(
                    f"{category} {i + 1}",
                    key=session_key,
                    height=92,
                    label_visibility="collapsed",
                )
                value = str(st.session_state.get(session_key, "")).strip()
                if value:
                    result.append(value)

            if st.button("+ Ajouter une ligne", key=f"{key_prefix}_{section}_{category}_add_row"):
                st.session_state[rows_key] += 1
                st.rerun()

            edited[section][category] = result

    return edited


def render_import_pdf_admin():
    section_header("1. Import des PDFs corrigés")
    html_block("""
<div class="usj-card">
    <b>Objectif :</b> importer les rapports PDF finaux, extraire automatiquement le texte,
    organiser les réponses par type de répondant et sous-groupe, puis permettre une correction admin.
</div>
""")

    col_type, col_sg = st.columns(2)
    with col_type:
        respondent_type = st.selectbox("Type de répondant", RESPONDENT_TYPES, key="upload_respondent_type")
    with col_sg:
        subgroup = st.selectbox("Sous-groupe", SUBGROUPS, key="upload_subgroup")

    st.markdown("**Importer le rapport PDF corrigé**")
    uploaded_pdf = st.file_uploader("Choisir un PDF", type=["pdf"], key="pdf_upload", label_visibility="collapsed")

    if uploaded_pdf is not None:
        if st.button("Extraire le texte du PDF", type="primary", key="extract_pdf_button"):
            try:
                for key in list(st.session_state.keys()):
                    if key.startswith("new_import_admin") or key.startswith("new_pdf_"):
                        del st.session_state[key]

                raw_text = extract_text_from_pdf(uploaded_pdf)
                parsed = parse_report_pdf_layout(uploaded_pdf, raw_text=raw_text)

                st.session_state["new_pdf_raw_text"] = raw_text
                st.session_state["new_pdf_parsed"] = parsed
                st.session_state["new_pdf_filename"] = uploaded_pdf.name
                st.success("Texte extrait. Vérifiez et corrigez les réponses ci-dessous avant l’enregistrement.")
            except Exception as exc:
                st.error(f"Erreur pendant l’extraction du PDF : {exc}")

    if "new_pdf_parsed" in st.session_state:
        st.markdown("---")
        st.markdown("## Vérification et correction admin")
        edited = render_admin_json_editor(st.session_state["new_pdf_parsed"], "new_import_admin")

        with st.expander("Voir le texte brut extrait du PDF"):
            st.text_area(
                "Texte brut",
                value=st.session_state.get("new_pdf_raw_text", ""),
                height=360,
                disabled=True,
                label_visibility="collapsed",
            )

        col_save, col_clear = st.columns([1, 3])
        with col_save:
            if st.button("Enregistrer le rapport", type="primary", use_container_width=True, key="save_imported_pdf"):
                report_id = save_report(
                    respondent_type=respondent_type,
                    subgroup=subgroup,
                    filename=st.session_state.get("new_pdf_filename", ""),
                    raw_text=st.session_state.get("new_pdf_raw_text", ""),
                    parsed_json=st.session_state.get("new_pdf_parsed", {}),
                    admin_json=edited,
                )
                for key in list(st.session_state.keys()):
                    if key.startswith("new_import_admin") or key.startswith("new_pdf_"):
                        del st.session_state[key]
                st.success(f"Rapport enregistré avec succès. ID : {report_id}")
                st.rerun()
        with col_clear:
            if st.button("Annuler l’import", use_container_width=False, key="clear_import"):
                for key in list(st.session_state.keys()):
                    if key.startswith("new_import_admin") or key.startswith("new_pdf_"):
                        del st.session_state[key]
                st.rerun()


def render_manage_reports_admin():
    section_header("Rapports importés")
    df = load_reports()
    if df.empty:
        st.info("Aucun rapport PDF importé pour le moment.")
        return

    df = df.copy()
    df["label"] = (
        df["id"].astype(str) + " | " +
        df["respondent_type"].fillna("") + " | " +
        df["subgroup"].fillna("") + " | " +
        df["filename"].fillna("")
    )
    selected_label = st.selectbox("Choisir un rapport à modifier", df["label"].tolist(), key="manage_report_select")
    report_id = int(selected_label.split(" | ")[0])
    row = load_report(report_id)
    if row is None:
        st.error("Rapport introuvable.")
        return

    html_block(f"""
<div class="usj-card">
    <span class="meta-badge">{html_lib.escape(str(row['respondent_type']))}</span>
    <span class="meta-badge">{html_lib.escape(str(row['subgroup']))}</span>
    <b>Fichier :</b> {html_lib.escape(str(row['filename']))}<br>
    <b>Date d'import :</b> {html_lib.escape(str(row['uploaded_at']))}
</div>
""")

    admin_json = json.loads(row["admin_json"] or "{}")
    edited = render_admin_json_editor(admin_json, f"edit_report_{report_id}")

    col_save, col_delete, col_empty = st.columns([1.1, 1.1, 3])
    with col_save:
        if st.button("Enregistrer les corrections", type="primary", use_container_width=True, key=f"save_report_{report_id}"):
            update_report_admin_json(report_id, edited)
            st.success("Corrections enregistrées.")
            st.rerun()
    with col_delete:
        if st.button("Supprimer ce rapport", use_container_width=True, key=f"delete_report_{report_id}"):
            delete_report(report_id)
            st.success("Rapport supprimé.")
            st.rerun()

    with st.expander("Voir le texte brut extrait"):
        st.text_area("Texte brut", value=row["raw_text"] or "", height=360, disabled=True, label_visibility="collapsed")


def render_exports_admin():
    section_header("Export")
    export_df = build_export_df()
    if export_df.empty:
        st.info("Aucune donnée à exporter.")
        return

    csv_data = export_df.to_csv(index=False, encoding="utf-8-sig")
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Answers")

    col_csv, col_excel, col_empty = st.columns([1, 1, 3])
    with col_csv:
        st.download_button(
            "Télécharger CSV",
            data=csv_data,
            file_name="strategic_pdf_answers_export.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_csv_export",
        )
    with col_excel:
        st.download_button(
            "Télécharger Excel",
            data=excel_buffer.getvalue(),
            file_name="strategic_pdf_answers_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="download_excel_export",
        )

    st.dataframe(export_df, use_container_width=True, hide_index=True)


def render_admin_view():
    st.markdown("## Admin View")
    tabs = st.tabs(["Importer PDF", "Modifier rapports", "Exporter"])
    with tabs[0]:
        render_import_pdf_admin()
    with tabs[1]:
        render_manage_reports_admin()
    with tabs[2]:
        render_exports_admin()


def render_answers_readonly(admin_json):
    if not isinstance(admin_json, dict):
        return
    for section in SECTION_LABELS:
        section_header(section)
        for category in ADMIN_FIELDS[section]:
            st.markdown(f"### {category}")
            answers = admin_json.get(section, {}).get(category, [])
            if not answers:
                st.info("Aucune réponse enregistrée pour cette rubrique.")
            for answer in answers:
                safe_answer = html_lib.escape(str(answer or "")).replace("\n", "<br>")
                html_block(f'<div class="readonly-answer">{safe_answer}</div>')


def render_director_view():
    st.markdown("## Director View")
    df = load_reports()
    if df.empty:
        st.info("Aucun rapport PDF n’est disponible pour le moment.")
        return

    col_type, col_sg = st.columns(2)
    with col_type:
        available_types = sorted(df["respondent_type"].dropna().unique().tolist())
        selected_type = st.selectbox("Catégorie de répondants", available_types, key="director_type")
    filtered = df[df["respondent_type"] == selected_type]

    with col_sg:
        available_subgroups = sorted(filtered["subgroup"].dropna().unique().tolist())
        selected_subgroup = st.selectbox("Sous-groupe", available_subgroups, key="director_subgroup")

    subgroup_df = filtered[filtered["subgroup"] == selected_subgroup].copy()
    subgroup_df = subgroup_df.sort_values("uploaded_at", ascending=False)

    if subgroup_df.empty:
        st.warning("Aucun rapport disponible pour cette sélection.")
        return

    if len(subgroup_df) > 1:
        subgroup_df["label"] = subgroup_df["uploaded_at"].fillna("") + " | " + subgroup_df["filename"].fillna("")
        selected_report_label = st.selectbox("Rapport", subgroup_df["label"].tolist(), key="director_report")
        selected_idx = subgroup_df[subgroup_df["label"] == selected_report_label].index[0]
        row = subgroup_df.loc[selected_idx]
    else:
        row = subgroup_df.iloc[0]

    html_block(f"""
<div class="usj-card">
    <span class="meta-badge">{html_lib.escape(str(row['respondent_type']))}</span>
    <span class="meta-badge">{html_lib.escape(str(row['subgroup']))}</span>
    <b>Fichier :</b> {html_lib.escape(str(row['filename']))}<br>
    <b>Date d'import :</b> {html_lib.escape(str(row['uploaded_at']))}
</div>
""")

    admin_json = json.loads(row["admin_json"] or "{}")
    render_answers_readonly(admin_json)


def login_screen():
    st.markdown("## Accès")
    col_code, col_button, col_empty = st.columns([4, 1.3, 2])
    with col_code:
        code = st.text_input("Mot de passe", type="password", key="login_code")
    with col_button:
        st.markdown("<br>", unsafe_allow_html=True)
        clicked = st.button("Accéder", use_container_width=True, key="access_button")

    if clicked:
        cleaned = code.strip().upper()
        if cleaned == ADMIN_CODE:
            st.session_state["access_granted"] = True
            st.session_state["role"] = "admin"
            st.rerun()
        elif cleaned == DIRECTOR_CODE:
            st.session_state["access_granted"] = True
            st.session_state["role"] = "director"
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="📄", layout="wide", initial_sidebar_state="collapsed")
    apply_usj_style()
    init_db()
    render_header()

    st.session_state.setdefault("access_granted", False)
    st.session_state.setdefault("role", "")

    if not st.session_state["access_granted"]:
        login_screen()
        st.stop()

    col_role, col_logout = st.columns([5, 1])
    with col_role:
        st.caption(f"Mode connecté : {st.session_state.get('role', '').upper()}")
    with col_logout:
        if st.button("Déconnexion", use_container_width=True):
            st.session_state["access_granted"] = False
            st.session_state["role"] = ""
            st.rerun()

    if st.session_state.get("role") == "admin":
        render_admin_view()
    else:
        render_director_view()


if __name__ == "__main__":
    main()
