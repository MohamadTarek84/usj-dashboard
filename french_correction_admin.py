import time
from io import BytesIO

import pandas as pd
import streamlit as st
import language_tool_python


SHEET_NAME = "All Answers"
LANGUAGE = "fr-FR"
ANSWER_COL_INDEX = 5  # Column F

SUGGESTED_COL = "Suggested_Correction"
ERROR_COL = "Detected_Error"
ACCEPT_COL = "Accept"
FINAL_COL = "Final_Answer"

PROTECTED_WORDS = ["USJ"]


st.set_page_config(
    page_title="French Correction Admin",
    layout="wide"
)

st.title("French Orthographic Correction")


@st.cache_resource
def load_tool():
    return language_tool_python.LanguageTool(LANGUAGE)


def get_error_length(match):
    return getattr(match, "errorLength", getattr(match, "error_length", 0))


def is_protected_error(text, match):
    error_length = get_error_length(match)
    error_text = text[match.offset:match.offset + error_length]
    return error_text.strip() in PROTECTED_WORDS


def correct_text(text, tool):
    if pd.isna(text) or str(text).strip() == "":
        return "", ""

    text = str(text)

    matches = tool.check(text)

    matches = [
        m for m in matches
        if not is_protected_error(text, m)
    ]

    corrected = language_tool_python.utils.correct(text, matches)

    errors = []

    for m in matches:
        if m.replacements:
            error_length = get_error_length(m)
            wrong = text[m.offset:m.offset + error_length]
            suggestions = ", ".join(m.replacements[:3])
            errors.append(f"{wrong} → {suggestions}")

    return corrected, " | ".join(errors)


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


def to_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

    return output.getvalue()


uploaded_file = st.file_uploader(
    "Upload Excel file",
    type=["xlsx"]
)

if uploaded_file is None:
    st.info("Upload the Excel file to start.")
    st.stop()


if "file_name" not in st.session_state or st.session_state["file_name"] != uploaded_file.name:
    df_raw = pd.read_excel(uploaded_file, sheet_name=SHEET_NAME)
    df, answer_col = prepare_df(df_raw.copy())

    st.session_state["file_name"] = uploaded_file.name
    st.session_state["df"] = df
    st.session_state["answer_col"] = answer_col
    st.session_state["processed"] = set()


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

batch_size = 10

if st.button("Check next 10 rows", type="primary"):
    rows_to_check = [
        i for i in answer_rows
        if i not in st.session_state["processed"]
    ][:batch_size]

    progress = st.progress(0)
    status = st.empty()

    for n, i in enumerate(rows_to_check, start=1):
        status.write(
            f"Checking answer {len(st.session_state['processed']) + 1} of {len(answer_rows)}"
        )

        original = str(df.loc[i, answer_col])
        corrected, errors = correct_text(original, tool)

        df.loc[i, SUGGESTED_COL] = corrected
        df.loc[i, ERROR_COL] = errors
        df.loc[i, FINAL_COL] = original
        df.loc[i, ACCEPT_COL] = False

        st.session_state["processed"].add(i)

        progress.progress(n / len(rows_to_check))
        time.sleep(0.05)

    st.session_state["df"] = df
    st.rerun()


st.markdown("## Excel table with suggested corrections")

edited_df = st.data_editor(
    df,
    use_container_width=True,
    height=650,
    num_rows="fixed",
    column_config={
        ACCEPT_COL: st.column_config.CheckboxColumn(
            "Accept correction",
            help="Check this box to accept the suggested correction.",
            default=False
        ),
        SUGGESTED_COL: st.column_config.TextColumn(
            "Suggested correction",
            width="large"
        ),
        ERROR_COL: st.column_config.TextColumn(
            "Detected error",
            width="large",
            disabled=True
        ),
        FINAL_COL: st.column_config.TextColumn(
            "Final answer",
            width="large"
        )
    },
    disabled=[
        col for col in df.columns
        if col not in [SUGGESTED_COL, ACCEPT_COL, FINAL_COL]
    ]
)

for i in range(len(edited_df)):
    original = str(edited_df.loc[i, answer_col])
    suggested = str(edited_df.loc[i, SUGGESTED_COL])

    if edited_df.loc[i, ACCEPT_COL] is True:
        edited_df.loc[i, FINAL_COL] = suggested
    else:
        edited_df.loc[i, FINAL_COL] = original

st.session_state["df"] = edited_df


excel_file = to_excel(st.session_state["df"])

st.download_button(
    "Download corrected Excel",
    data=excel_file,
    file_name="corrected_answers.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
