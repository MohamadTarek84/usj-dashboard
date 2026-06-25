import time
from io import BytesIO

import pandas as pd
import streamlit as st
import language_tool_python


SHEET_NAME = "All Answers"
LANGUAGE = "fr-FR"

ANSWER_COL_INDEX = 5  # Column F

SUGGESTED_COL = "Suggested_Correction"
DECISION_COL = "Admin_Decision"
FINAL_COL = "Final_Answer"
NOTES_COL = "Correction_Notes"

PROTECTED_WORDS = ["USJ"]


st.set_page_config(
    page_title="French Correction Admin",
    layout="wide"
)

st.title("French Orthographic Correction")
st.caption("This tool corrects French spelling and grammar without changing the original answer.")


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
        match for match in matches
        if not is_protected_error(text, match)
    ]

    corrected = language_tool_python.utils.correct(text, matches)

    notes = []

    for match in matches:
        if match.replacements:
            error_length = get_error_length(match)
            wrong_text = text[match.offset:match.offset + error_length]
            suggestions = ", ".join(match.replacements[:3])

            notes.append(f"{wrong_text} → {suggestions}")

    return corrected, " | ".join(notes)


def prepare_df(df):
    if df.shape[1] < 6:
        st.error("Column F was not found.")
        st.stop()

    answer_col = df.columns[ANSWER_COL_INDEX]

    if SUGGESTED_COL not in df.columns:
        df.insert(6, SUGGESTED_COL, "")

    if DECISION_COL not in df.columns:
        df.insert(7, DECISION_COL, "Pending")

    if FINAL_COL not in df.columns:
        df.insert(8, FINAL_COL, df[answer_col])

    if NOTES_COL not in df.columns:
        df.insert(9, NOTES_COL, "")

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
    st.info("Upload your Excel file to start.")
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


st.success(f"Loaded sheet: {SHEET_NAME}")
st.info(f"Answers are read from Column F: {answer_col}")


st.markdown("## Full Excel preview before correction")

st.dataframe(
    df,
    use_container_width=True,
    height=400
)


tool = load_tool()

answer_rows = [
    i for i in range(len(df))
    if str(df.loc[i, answer_col]).strip() not in ["", "nan", "None"]
]

st.markdown("## Correction")

col1, col2, col3 = st.columns(3)

col1.metric("Total rows", len(df))
col2.metric("Answers", len(answer_rows))
col3.metric("Checked", len(st.session_state["processed"]))


batch_size = st.selectbox(
    "Rows to check per click",
    [10, 25, 50]
)

if st.button("Check next rows", type="primary"):
    rows_to_check = [
        i for i in answer_rows
        if i not in st.session_state["processed"]
    ][:batch_size]

    progress = st.progress(0)
    status = st.empty()

    for n, i in enumerate(rows_to_check, start=1):
        status.write(f"Checking answer {len(st.session_state['processed']) + 1} of {len(answer_rows)}")

        original = str(df.loc[i, answer_col])

        corrected, notes = correct_text(original, tool)

        df.loc[i, SUGGESTED_COL] = corrected
        df.loc[i, NOTES_COL] = notes

        if corrected.strip() == original.strip():
            df.loc[i, DECISION_COL] = "No correction"
            df.loc[i, FINAL_COL] = original
        else:
            df.loc[i, DECISION_COL] = "Pending"
            df.loc[i, FINAL_COL] = original

        st.session_state["processed"].add(i)

        progress.progress(n / len(rows_to_check))
        time.sleep(0.05)

    st.session_state["df"] = df
    st.success("Batch completed.")


st.markdown("## Validate corrections")

pending_rows = [
    i for i in sorted(st.session_state["processed"])
    if df.loc[i, DECISION_COL] == "Pending"
]

if not pending_rows:
    st.info("No pending corrections. Check the next rows.")
else:
    for i in pending_rows:
        st.markdown("---")
        st.markdown(f"### Excel row {i + 2}")

        meta = []

        for col in ["Respondent_Type", "groupe", "subgroup", "section", "category"]:
            if col in df.columns:
                meta.append(f"**{col}:** {df.loc[i, col]}")

        if meta:
            st.markdown(" | ".join(meta))

        left, right = st.columns(2)

        original = str(df.loc[i, answer_col])
        suggested = str(df.loc[i, SUGGESTED_COL])

        with left:
            st.markdown("**Original answer**")
            st.text_area(
                "Original",
                value=original,
                height=180,
                disabled=True,
                key=f"original_{i}",
                label_visibility="collapsed"
            )

        with right:
            st.markdown("**Suggested correction**")
            edited = st.text_area(
                "Suggested",
                value=suggested,
                height=180,
                key=f"suggested_{i}",
                label_visibility="collapsed"
            )

        st.caption(f"Detected errors: {df.loc[i, NOTES_COL]}")

        c1, c2, c3 = st.columns(3)

        if c1.button("Accept", key=f"accept_{i}"):
            df.loc[i, SUGGESTED_COL] = edited
            df.loc[i, DECISION_COL] = "Accepted"
            df.loc[i, FINAL_COL] = edited
            st.session_state["df"] = df
            st.rerun()

        if c2.button("Reject", key=f"reject_{i}"):
            df.loc[i, DECISION_COL] = "Rejected"
            df.loc[i, FINAL_COL] = original
            st.session_state["df"] = df
            st.rerun()

        if c3.button("Keep pending", key=f"pending_{i}"):
            df.loc[i, SUGGESTED_COL] = edited
            df.loc[i, DECISION_COL] = "Pending"
            df.loc[i, FINAL_COL] = original
            st.session_state["df"] = df
            st.rerun()


st.markdown("## Final Excel preview")

st.dataframe(
    df,
    use_container_width=True,
    height=400
)


excel_file = to_excel(df)

st.download_button(
    "Download corrected Excel",
    data=excel_file,
    file_name="corrected_answers.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
