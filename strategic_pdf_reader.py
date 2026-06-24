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

/* FIX: Streamlit file uploader icon appears as the word "upload" on some deployments */
div[data-testid="stFileUploader"] button {
    min-width: 145px !important;
    width: 145px !important;
    height: 42px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0 !important;
    overflow: hidden !important;
    white-space: nowrap !important;
}
div[data-testid="stFileUploader"] button svg,
div[data-testid="stFileUploader"] button [data-testid="stIconMaterial"],
div[data-testid="stFileUploader"] button span[aria-hidden="true"],
div[data-testid="stFileUploader"] button i {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    min-width: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stFileUploader"] section {
    background-color:#F1F4F8 !important;
    border-radius:8px !important;
}

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



def _words_to_lines(words):
    """
    Convert PyMuPDF word tuples into visual lines with coordinates.
    This is used to preserve the two-column PDF table layout.
    """
    grouped = {}
    for w in words:
        x0, y0, x1, y1, text, block_no, line_no, word_no = w[:8]
        key = (int(block_no), int(line_no), round(float(y0), 1))
        grouped.setdefault(key, []).append(w)

    lines = []
    for key, group in grouped.items():
        group = sorted(group, key=lambda t: (t[0], t[7]))
        text = " ".join(str(t[4]) for t in group).strip()
        if not text:
            continue
        lines.append({
            "text": text,
            "x0": min(float(t[0]) for t in group),
            "y0": min(float(t[1]) for t in group),
            "x1": max(float(t[2]) for t in group),
            "y1": max(float(t[3]) for t in group),
            "page": None,
        })
    return sorted(lines, key=lambda d: (d["y0"], d["x0"]))


def _line_is_heading(line_text, heading_key):
    n = normalize_for_match(line_text)
    if heading_key == "I":
        return ("forces et faiblesses" in n) or re.search(r"\bi\s*[-–—.]?\s*forces", n)
    if heading_key == "II":
        return ("opportunites et menaces" in n) or re.search(r"\bii\s*[-–—.]?\s*opportun", n)
    if heading_key == "III":
        return re.search(r"\biii\s*[-–—.]?\s*prior", n) or n.strip() == "priorites"
    if heading_key == "IV":
        return re.search(r"\biv\s*[-–—.]?\s*conclusion", n) or n.strip() == "conclusion"
    return False


def _is_exact_category(text, category):
    n = normalize_for_match(text).strip(" :-–—").lower()
    c = normalize_for_match(category).strip().lower()
    aliases = {
        "opportunités": ["opportunites", "opportunite"],
        "priorités": ["priorites", "priorite"],
    }
    allowed = [c] + aliases.get(category, [])
    return n in allowed


def _clean_layout_item(text):
    text = clean_text(text)
    text = re.sub(r"^[\u2022\-*–—\d\.\)\s]+", "", text).strip()
    return text


def _group_lines_into_items(lines):
    """
    Group visual lines into answer boxes.
    Wrapped lines inside one box have small vertical gaps.
    Separate boxes have larger gaps.
    """
    if not lines:
        return []

    lines = sorted(lines, key=lambda d: (d["y0"], d["x0"]))
    items = []
    current = []
    previous_y = None

    for line in lines:
        txt = _clean_layout_item(line["text"])
        if not txt:
            continue

        n = normalize_for_match(txt)
        if any(fragment in n for fragment in [
            "maximum cinq", "merci de", "thematique", "quels sont",
            "niveau usj", "plan strategique", "forces et faiblesses",
            "opportunites et menaces"
        ]):
            continue
        if _is_exact_category(txt, "Forces") or _is_exact_category(txt, "Faiblesses") or _is_exact_category(txt, "Opportunités") or _is_exact_category(txt, "Menaces"):
            continue

        if previous_y is not None and (line["y0"] - previous_y) > 18:
            joined = _clean_layout_item(" ".join(current))
            if joined:
                items.append(joined)
            current = []

        current.append(txt)
        previous_y = line["y0"]

    joined = _clean_layout_item(" ".join(current))
    if joined:
        items.append(joined)

    cleaned = []
    seen = set()
    for item in items:
        key = normalize_for_match(item)
        if key and key not in seen:
            cleaned.append(item)
            seen.add(key)
    return cleaned


def _extract_two_column_section_from_lines(lines, section_key, next_section_key, left_cat, right_cat):
    section_indices = [i for i, line in enumerate(lines) if _line_is_heading(line["text"], section_key)]
    if not section_indices:
        return None

    start_idx = section_indices[0]
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        if _line_is_heading(lines[i]["text"], next_section_key):
            end_idx = i
            break

    section_lines = lines[start_idx + 1:end_idx]
    if not section_lines:
        return None

    left_headers = [l for l in section_lines if _is_exact_category(l["text"], left_cat)]
    right_headers = [l for l in section_lines if _is_exact_category(l["text"], right_cat)]

    if not left_headers or not right_headers:
        return None

    left_header = sorted(left_headers, key=lambda d: (d["y0"], d["x0"]))[0]
    right_header = sorted(right_headers, key=lambda d: (d["y0"], d["x0"]))[0]
    header_y = min(left_header["y0"], right_header["y0"])
    split_x = (left_header["x1"] + right_header["x0"]) / 2

    left_lines = []
    right_lines = []

    for line in section_lines:
        if line["y0"] <= header_y + 4:
            continue

        txt = line["text"].strip()
        if not txt:
            continue
        if _line_is_heading(txt, section_key) or _line_is_heading(txt, next_section_key):
            continue

        mid_x = (line["x0"] + line["x1"]) / 2
        if mid_x < split_x:
            left_lines.append(line)
        else:
            right_lines.append(line)

    left_items = _group_lines_into_items(left_lines)
    right_items = _group_lines_into_items(right_lines)

    if not left_items and not right_items:
        return None

    return {left_cat: left_items, right_cat: right_items}


def _extract_single_column_section_from_lines(lines, section_key, next_section_key, category):
    section_indices = [i for i, line in enumerate(lines) if _line_is_heading(line["text"], section_key)]
    if not section_indices:
        return None

    start_idx = section_indices[0]
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        if next_section_key and _line_is_heading(lines[i]["text"], next_section_key):
            end_idx = i
            break

    section_lines = []
    for line in lines[start_idx + 1:end_idx]:
        txt = line["text"].strip()
        if not txt:
            continue
        if _line_is_heading(txt, section_key):
            continue
        if _is_exact_category(txt, category):
            continue
        section_lines.append(line)

    items = _group_lines_into_items(section_lines)
    return {category: items} if items else None


def extract_pdf_content(uploaded_pdf):
    """
    Reads the PDF once and returns:
    1) plain raw text for backup/debug
    2) layout-based parsed answers that preserve columns and answer boxes when possible
    """
    if fitz is None:
        raise ImportError("PyMuPDF is not installed. Add pymupdf to requirements.txt.")

    pdf_bytes = uploaded_pdf.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    pages_text = []
    all_lines = []

    for page_index, page in enumerate(doc):
        pages_text.append(page.get_text("text"))

        words = page.get_text("words")
        page_lines = _words_to_lines(words)
        for line in page_lines:
            line["page"] = page_index
            # Add a large page offset so sorting across pages is stable.
            line["y0"] = float(line["y0"]) + page_index * 10000
            line["y1"] = float(line["y1"]) + page_index * 10000
        all_lines.extend(page_lines)

    raw_text = "\n".join(pages_text)
    all_lines = sorted(all_lines, key=lambda d: (d["y0"], d["x0"]))

    layout_parsed = {
        "I - Forces et Faiblesses": _extract_two_column_section_from_lines(
            all_lines, "I", "II", "Forces", "Faiblesses"
        ),
        "II - Opportunités et Menaces": _extract_two_column_section_from_lines(
            all_lines, "II", "III", "Opportunités", "Menaces"
        ),
        "III - Priorités": _extract_single_column_section_from_lines(
            all_lines, "III", "IV", "Priorités"
        ),
        "IV - Conclusion": _extract_single_column_section_from_lines(
            all_lines, "IV", None, "Conclusion"
        ),
    }

    return raw_text, layout_parsed


def extract_text_from_pdf(uploaded_pdf):
    raw_text, _ = extract_pdf_content(uploaded_pdf)
    return raw_text

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



def _remove_section_title_lines(section_text):
    lines = []
    for raw in clean_text(section_text).splitlines():
        n = normalize_for_match(raw).strip()
        if not n:
            continue
        if "forces et faiblesses" in n:
            continue
        if "opportunites et menaces" in n:
            continue
        if re.search(r"\bi\s*[-–—.]?\s*forces", n):
            continue
        if re.search(r"\bii\s*[-–—.]?\s*opportun", n):
            continue
        if re.search(r"\biii\s*[-–—.]?\s*prior", n):
            continue
        if re.search(r"\biv\s*[-–—.]?\s*conclusion", n):
            continue
        lines.append(raw.strip())
    return "\n".join(lines)


def extract_category_text(section_text, category_keywords, next_category_keywords):
    """
    Fallback text parser.
    Important fix: it removes section titles before looking for category titles.
    This prevents 'Forces et Faiblesses' from being read as a Forces answer
    and prevents the full section from being dumped into Faiblesses.
    """
    cleaned_section = _remove_section_title_lines(section_text)
    lines = cleaned_section.splitlines()

    start_index = None
    for i, line in enumerate(lines):
        line_norm = normalize_for_match(line).strip(" :-–—").lower()
        for keyword in category_keywords:
            # Match only category headers as full lines, not inside section titles.
            if re.fullmatch(keyword.strip(".*?^$\\b") + r"s?", line_norm, flags=re.IGNORECASE):
                start_index = i + 1
                break
            if re.fullmatch(keyword, line_norm, flags=re.IGNORECASE):
                start_index = i + 1
                break
        if start_index is not None:
            break

    if start_index is None:
        return ""

    end_index = len(lines)
    for i in range(start_index, len(lines)):
        line_norm = normalize_for_match(lines[i]).strip(" :-–—").lower()
        for keyword in next_category_keywords:
            if re.fullmatch(keyword.strip(".*?^$\\b") + r"s?", line_norm, flags=re.IGNORECASE):
                end_index = i
                break
            if re.fullmatch(keyword, line_norm, flags=re.IGNORECASE):
                end_index = i
                break
        if end_index != len(lines):
            break

    return clean_text("\n".join(lines[start_index:end_index]))


def _merge_layout_with_text_parse(layout_parsed, text_parsed):
    """
    Prefer visual-layout parsing when available.
    Fall back to text parsing for any missing section/category.
    """
    merged = {}
    for section in SECTION_LABELS:
        merged[section] = {}
        for category in ADMIN_FIELDS[section]:
            layout_values = []
            if isinstance(layout_parsed, dict) and isinstance(layout_parsed.get(section), dict):
                layout_values = layout_parsed.get(section, {}).get(category, []) or []
            text_values = []
            if isinstance(text_parsed, dict) and isinstance(text_parsed.get(section), dict):
                text_values = text_parsed.get(section, {}).get(category, []) or []
            merged[section][category] = layout_values if layout_values else text_values
    return merged


def parse_report_text(raw_text, layout_parsed=None):
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

    forces_text = extract_category_text(section_i, [r"forces?"] , [r"faiblesses?"])
    faiblesses_text = extract_category_text(section_i, [r"faiblesses?"] , [])
    opportunites_text = extract_category_text(section_ii, [r"opportunites?"] , [r"menaces?"])
    menaces_text = extract_category_text(section_ii, [r"menaces?"] , [])

    text_parsed = {
        "I - Forces et Faiblesses": {
            "Forces": split_items(forces_text) if forces_text else [],
            "Faiblesses": split_items(faiblesses_text) if faiblesses_text else [],
        },
        "II - Opportunités et Menaces": {
            "Opportunités": split_items(opportunites_text) if opportunites_text else [],
            "Menaces": split_items(menaces_text) if menaces_text else [],
        },
        "III - Priorités": {
            "Priorités": split_items(_remove_section_title_lines(section_iii)),
        },
        "IV - Conclusion": {
            "Conclusion": split_items(_remove_section_title_lines(section_iv)) if section_iv else [],
        },
    }

    parsed = _merge_layout_with_text_parse(layout_parsed or {}, text_parsed)

    parsed["_section_text"] = {
        "I - Forces et Faiblesses": section_i,
        "II - Opportunités et Menaces": section_ii,
        "III - Priorités": section_iii,
        "IV - Conclusion": section_iv,
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



def _get_category_values(base_json, section, category):
    if not isinstance(base_json, dict):
        return []
    values = base_json.get(section, {}).get(category, [])
    if isinstance(values, list):
        return [str(v or "").strip() for v in values]
    if isinstance(values, str):
        return text_lines_to_list(values)
    return []


def _clean_editor_key(value):
    return re.sub(r"[^A-Za-z0-9_]+", "_", normalize_for_match(value)).strip("_")


def render_admin_json_editor(base_json, key_prefix):
    """
    Admin correction screen in the same box-by-box format as the original PDF/report:
    - Forces/Faiblesses are shown as two columns with aligned rows.
    - Opportunités/Menaces are shown as two columns with aligned rows.
    - Priorités and Conclusion are shown as stacked answer boxes.
    """
    edited = {}

    for section in SECTION_LABELS:
        section_header(section)
        edited[section] = {}
        fields = ADMIN_FIELDS[section]

        if len(fields) == 2:
            left_field, right_field = fields
            left_values = _get_category_values(base_json, section, left_field)
            right_values = _get_category_values(base_json, section, right_field)

            rows_key = f"{key_prefix}_{_clean_editor_key(section)}_rows"
            if rows_key not in st.session_state:
                st.session_state[rows_key] = max(5, len(left_values), len(right_values))

            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown(f"### {left_field}")
            with col_right:
                st.markdown(f"### {right_field}")

            left_edited = []
            right_edited = []

            for i in range(st.session_state[rows_key]):
                col_left, col_right = st.columns(2)

                with col_left:
                    left_key = f"{key_prefix}_{_clean_editor_key(section)}_{_clean_editor_key(left_field)}_{i+1}"
                    if left_key not in st.session_state:
                        st.session_state[left_key] = left_values[i] if i < len(left_values) else ""
                    value = st.text_area(
                        f"{left_field} {i+1}",
                        key=left_key,
                        height=95,
                        label_visibility="collapsed",
                    )
                    left_edited.append(value.strip())

                with col_right:
                    right_key = f"{key_prefix}_{_clean_editor_key(section)}_{_clean_editor_key(right_field)}_{i+1}"
                    if right_key not in st.session_state:
                        st.session_state[right_key] = right_values[i] if i < len(right_values) else ""
                    value = st.text_area(
                        f"{right_field} {i+1}",
                        key=right_key,
                        height=95,
                        label_visibility="collapsed",
                    )
                    right_edited.append(value.strip())

            col_add, col_spacer = st.columns([1, 5])
            with col_add:
                if st.button("+ Ajouter une ligne", key=f"{key_prefix}_{_clean_editor_key(section)}_add_row"):
                    st.session_state[rows_key] += 1
                    st.rerun()

            edited[section][left_field] = [v for v in left_edited if v]
            edited[section][right_field] = [v for v in right_edited if v]

        else:
            category = fields[0]
            values = _get_category_values(base_json, section, category)

            rows_key = f"{key_prefix}_{_clean_editor_key(section)}_{_clean_editor_key(category)}_rows"
            default_rows = 5 if section == "III - Priorités" else 3
            if rows_key not in st.session_state:
                st.session_state[rows_key] = max(default_rows, len(values))

            st.markdown(f"### {category}")

            collected = []
            for i in range(st.session_state[rows_key]):
                answer_key = f"{key_prefix}_{_clean_editor_key(section)}_{_clean_editor_key(category)}_{i+1}"
                if answer_key not in st.session_state:
                    st.session_state[answer_key] = values[i] if i < len(values) else ""

                value = st.text_area(
                    f"{category} {i+1}",
                    key=answer_key,
                    height=95,
                    label_visibility="collapsed",
                )
                collected.append(value.strip())

            col_add, col_spacer = st.columns([1, 5])
            with col_add:
                if st.button("+ Ajouter une ligne", key=f"{key_prefix}_{_clean_editor_key(section)}_{_clean_editor_key(category)}_add_row"):
                    st.session_state[rows_key] += 1
                    st.rerun()

            edited[section][category] = [v for v in collected if v]

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

    uploaded_pdf = st.file_uploader("Importer le rapport PDF corrigé", type=["pdf"], key="pdf_upload")

    if uploaded_pdf is not None:
        if st.button("Extraire le texte du PDF", type="primary", key="extract_pdf_button"):
            try:
                raw_text, layout_parsed = extract_pdf_content(uploaded_pdf)
                parsed = parse_report_text(raw_text, layout_parsed)
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
