import time
import re
from io import BytesIO
import html
from copy import copy

import pandas as pd
import streamlit as st
import language_tool_python
from openpyxl import load_workbook
from openpyxl.styles import PatternFill


SHEET_NAME = "All Answers"
LANGUAGE = "fr-FR"
ANSWER_COL_INDEX = 5  # Column F

SUGGESTED_COL = "Suggested_Correction"
ERROR_COL = "Detected_Error"
ACCEPT_COL = "Accept_Correction"
FINAL_COL = "Final_Answer"

PROTECTED_WORDS = [
    "USJ",
    "A",
    "B",
    "C",
    "flows"
]

PROTECTED_PATTERNS = [
    r"\bUSJ\b",
    r"\bClasse\s+[A-Z]\b",
    r"\b[A-Z]\s+et\s+[A-Z]\b",
    r"\b[A-Z],\s*[A-Z]\s+et\s+[A-Z]\b",
    r"^[IVXLCDM]+[-–]\s*",
]


st.set_page_config(page_title="French Correction Admin", layout="wide")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }

        [data-testid="collapsedControl"] {
            display: none;
        }

        .main .block-container {
            padding-left: 3rem;
            padding-right: 3rem;
            max-width: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("French Orthographic Correction")


@st.cache_resource
def load_tool():
    return language_tool_python.LanguageTool(LANGUAGE)


def get_error_length(match):
    return getattr(match, "errorLength", getattr(match, "error_length", 0))


def get_error_text(text, match):
    return text[match.offset:match.offset + get_error_length(match)]


def overlaps(start1, end1, start2, end2):
    return start1 < end2 and end1 > start2


def is_protected_error(text, match):
    error_length = get_error_length(match)
    start = match.offset
    end = match.offset + error_length
    error_text = text[start:end].strip()

    protected_lower = [w.lower() for w in PROTECTED_WORDS]

    if error_text.lower() in protected_lower:
        return True

    for pattern in PROTECTED_PATTERNS:
        for found in re.finditer(pattern, text, flags=re.IGNORECASE):
            p_start, p_end = found.span()

            if overlaps(start, end, p_start, p_end):
                return True

    return False


def is_bad_replacement(match):
    replacements = match.replacements or []

    for replacement in replacements:
        rep = str(replacement).strip()

        if "(" in rep or ")" in rep:
            return True

        if "?" in rep:
            return True

        if rep == "":
            return True

    return False


def is_safe_match(text, match):
    if is_protected_error(text, match):
        return False

    if is_bad_replacement(match):
        return False

    error_text = get_error_text(text, match).strip()

    if len(error_text) == 1 and error_text.upper() == error_text:
        return False

    return True


def highlight_original(text, matches):
    if not matches:
        return html.escape(text)

    parts = []
    last = 0

    for m in sorted(matches, key=lambda x: x.offset):
        start = m.offset
        end = m.offset + get_error_length(m)

        parts.append(html.escape(text[last:start]))
        parts.append(
            f"<mark style='background:#ffcccc; padding:2px; border-radius:4px;'>"
            f"{html.escape(text[start:end])}</mark>"
        )
        last = end

    parts.append(html.escape(text[last:]))
    return "".join(parts)


def correct_text(text, tool):
    if pd.isna(text) or str(text).strip() == "":
        return "", "", ""

    text = str(text)

    raw_matches = tool.check(text)

    matches = [
        m for m in raw_matches
        if is_safe_match(text, m)
    ]

    corrected = language_tool_python.utils.correct(text, matches)

    errors = []

    for m in matches:
        if m.replacements:
            wrong = get_error_text(text, m)
            suggestion = ", ".join(m.replacements[:3])
            errors.append(f"{wrong} → {suggestion}")

    highlighted = highlight_original(text, matches)

    return corrected, " | ".join(errors), highlighted


def prepare_df(df):
    if df.shape[1] < 6:
        st.error("Column F was not found.")
        st.stop()

    answer_col = df.columns[ANSWER_COL_INDEX]

    if SUGGESTED_COL not in df.columns:
        df.insert(6, SUGGESTED_COL, "")

    if ERROR_COL not in df.columns:
        df.insert(7, ERROR_COL, "")

    if ACCEPT_COL not in df.columns:
        df.insert(8, ACCEPT_COL, False)

    if FINAL_COL not in df.columns:
        df.insert(9, FINAL_COL, df[answer_col])

    return df, answer_col


def save_with_original_format(original_file_bytes, df):
    wb = load_workbook(BytesIO(original_file_bytes))
    ws = wb[SHEET_NAME]

    headers = list(df.columns)

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.value = header

        if col_idx > 6:
            source = ws.cell(row=1, column=6)
            cell.font = copy(source.font)
            cell.fill = copy(source.fill)
            cell.border = copy(source.border)
            cell.alignment = copy(source.alignment)
            cell.number_format = source.number_format

    yellow_fill = PatternFill("solid", fgColor="FFF2CC")
    red_fill = PatternFill("solid", fgColor="F4CCCC")
    green_fill = PatternFill("solid", fgColor="D9EAD3")

    for row_idx in range(len(df)):
        excel_row = row_idx + 2

        for col_idx, col_name in enumerate(headers, start=1):
            value = df.iloc[row_idx][col_name]

            if pd.isna(value):
                value = ""

            cell = ws.cell(row=excel_row, column=col_idx)
            cell.value = value

            if col_idx > 6:
                source = ws.cell(row=excel_row, column=6)
                cell.font = copy(source.font)
                cell.border = copy(source.border)
                cell.alignment = copy(source.alignment)
                cell.number_format = source.number_format

        if str(df.iloc[row_idx][ERROR_COL]).strip():
            ws.cell(excel_row, 7).fill = yellow_fill
            ws.cell(excel_row, 8).fill = red_fill

        if bool(df.iloc[row_idx][ACCEPT_COL]):
            ws.cell(excel_row, 10).fill = green_fill

    ws.column_dimensions["G"].width = 70
    ws.column_dimensions["H"].width = 55
    ws.column_dimensions["I"].width = 22
    ws.column_dimensions["J"].width = 70

    output = BytesIO()
    wb.save(output)
    return output.getvalue()


uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file is None:
    st.info("Upload the Excel file to start.")
    st.stop()

original_file_bytes = uploaded_file.getvalue()

if "file_name" not in st.session_state or st.session_state["file_name"] != uploaded_file.name:
    df_raw = pd.read_excel(BytesIO(original_file_bytes), sheet_name=SHEET_NAME)
    df, answer_col = prepare_df(df_raw.copy())

    st.session_state["file_name"] = uploaded_file.name
    st.session_state["original_file_bytes"] = original_file_bytes
    st.session_state["df"] = df
    st.session_state["answer_col"] = answer_col
    st.session_state["processed"] = set()
    st.session_state["highlighted"] = {}

df = st.session_state["df"]
answer_col = st.session_state["answer_col"]

tool = load_tool()

answer_rows = [
    i for i in range(len(df))
    if str(df.loc[i, answer_col]).strip() not in ["", "nan", "None"]
]

st.markdown("## Correction")

c1, c2, c3 = st.columns(3)
c1.metric("Total rows", len(df))
c2.metric("Answers", len(answer_rows))
c3.metric("Checked", len(st.session_state["processed"]))

if st.button("Check all rows", type="primary"):
    rows_to_check = [
        i for i in answer_rows
        if i not in st.session_state["processed"]
    ]

    if not rows_to_check:
        st.success("All rows are already checked.")
    else:
        progress = st.progress(0)
        status = st.empty()

        for n, i in enumerate(rows_to_check, start=1):
            status.write(
                f"Checking answer {len(st.session_state['processed']) + 1} of {len(answer_rows)}"
            )

            original = str(df.loc[i, answer_col])
            corrected, errors, highlighted = correct_text(original, tool)

            df.loc[i, SUGGESTED_COL] = corrected
            df.loc[i, ERROR_COL] = errors
            df.loc[i, ACCEPT_COL] = False
            df.loc[i, FINAL_COL] = original

            st.session_state["highlighted"][i] = highlighted
            st.session_state["processed"].add(i)

            progress.progress(n / len(rows_to_check))
            time.sleep(0.01)

        st.session_state["df"] = df
        st.rerun()


st.markdown("## Review corrections")

pending_rows = [
    i for i in sorted(st.session_state["processed"])
    if str(df.loc[i, ERROR_COL]).strip()
]

if not pending_rows:
    st.info("No detected errors yet.")
else:
    for i in pending_rows:
        st.markdown("---")
        st.markdown(f"### Excel row {i + 2}")

        original = str(df.loc[i, answer_col])
        suggested = str(df.loc[i, SUGGESTED_COL])
        errors = str(df.loc[i, ERROR_COL])

        left, right = st.columns(2)

        with left:
            st.markdown("**Original answer with highlighted error**")
            st.markdown(
                f"""
                <div style="border:1px solid #ddd; padding:15px; border-radius:8px; line-height:1.7;">
                    {st.session_state["highlighted"].get(i, html.escape(original))}
                </div>
                """,
                unsafe_allow_html=True
            )

        with right:
            st.markdown("**Suggested correction**")
            edited = st.text_area(
                "Suggested correction",
                value=suggested,
                height=180,
                key=f"suggested_{i}",
                label_visibility="collapsed"
            )

        st.markdown(f"**Detected error:** {errors}")

        accept = st.checkbox(
            "Accept this correction",
            value=bool(df.loc[i, ACCEPT_COL]),
            key=f"accept_{i}"
        )

        df.loc[i, SUGGESTED_COL] = edited
        df.loc[i, ACCEPT_COL] = accept

        if accept:
            df.loc[i, FINAL_COL] = edited
        else:
            df.loc[i, FINAL_COL] = original

        st.session_state["df"] = df


st.markdown("## Final Excel preview")

st.dataframe(
    df,
    use_container_width=True,
    height=450
)

excel_file = save_with_original_format(
    st.session_state["original_file_bytes"],
    st.session_state["df"]
)

st.download_button(
    "Download corrected Excel with original format",
    data=excel_file,
    file_name="corrected_answers_with_format.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
