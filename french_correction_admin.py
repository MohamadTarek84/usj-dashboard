# file: french_correction_admin.py

import streamlit as st
import pandas as pd
import language_tool_python
from io import BytesIO

EXCEL_FILE = "FGs All Answers 25-6-2026.xlsx"
SHEET_NAME = "All Answers"
ANSWER_COL = "F"
CORRECTED_COL = "G"
LANGUAGE = "fr-FR"

st.set_page_config(page_title="French Correction Admin", layout="wide")

st.title("Correction orthographique - Français France")
st.caption("Column F = original answers | Column G = suggested corrected answers")

@st.cache_resource
def load_tool():
    return language_tool_python.LanguageTool(LANGUAGE)

def correct_french_text(text, tool):
    if pd.isna(text) or str(text).strip() == "":
        return "", []

    text = str(text)
    matches = tool.check(text)
    corrected = language_tool_python.utils.correct(text, matches)

    notes = []
    for m in matches:
        if m.replacements:
            notes.append({
                "message": m.message,
                "error": text[m.offset:m.offset + m.errorLength],
                "suggestions": ", ".join(m.replacements[:5])
            })

    return corrected, notes

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
    return output.getvalue()

uploaded_file = st.file_uploader(
    "Upload Excel file",
    type=["xlsx"],
    help="Upload FGs All Answers 25-6-2026.xlsx"
)

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name=SHEET_NAME)

    if df.shape[1] < 6:
        st.error("Column F was not found. The sheet must contain at least 6 columns.")
        st.stop()

    answer_column = df.columns[5]

    st.success(f"Loaded sheet: {SHEET_NAME}")
    st.info(f"Answers detected in column F: {answer_column}")

    tool = load_tool()

    if "corrected_df" not in st.session_state:
        with st.spinner("Checking French spelling and grammar..."):
            corrected_values = []
            notes_values = []

            for text in df[answer_column]:
                corrected, notes = correct_french_text(text, tool)
                corrected_values.append(corrected)
                notes_values.append(notes)

            df["Suggested_Correction"] = corrected_values
            df["Admin_Decision"] = "Pending"
            df["Final_Answer"] = df[answer_column]
            df["Correction_Notes"] = [
                " | ".join(
                    f"{n['error']} → {n['suggestions']} ({n['message']})"
                    for n in notes
                )
                for notes in notes_values
            ]

            st.session_state.corrected_df = df

    df_edit = st.session_state.corrected_df

    st.markdown("## Admin validation")

    for i in range(len(df_edit)):
        original = str(df_edit.loc[i, answer_column])
        suggested = str(df_edit.loc[i, "Suggested_Correction"])

        if original.strip() == suggested.strip():
            continue

        with st.expander(f"Row {i + 2} - Correction suggested"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Original answer**")
                st.text_area(
                    "Original",
                    value=original,
                    height=160,
                    disabled=True,
                    key=f"orig_{i}",
                    label_visibility="collapsed"
                )

            with col2:
                st.markdown("**Suggested correction**")
                edited_suggestion = st.text_area(
                    "Suggested",
                    value=suggested,
                    height=160,
                    key=f"sugg_{i}",
                    label_visibility="collapsed"
                )

            st.markdown("**Detected issues**")
            st.caption(df_edit.loc[i, "Correction_Notes"])

            decision = st.radio(
                "Admin decision",
                ["Pending", "Accept correction", "Reject correction"],
                horizontal=True,
                key=f"decision_{i}"
            )

            df_edit.loc[i, "Admin_Decision"] = decision

            if decision == "Accept correction":
                df_edit.loc[i, "Final_Answer"] = edited_suggestion
                df_edit.loc[i, "Suggested_Correction"] = edited_suggestion
            elif decision == "Reject correction":
                df_edit.loc[i, "Final_Answer"] = original
            else:
                df_edit.loc[i, "Final_Answer"] = original

    st.markdown("## Preview")

    st.dataframe(
        df_edit[
            [
                answer_column,
                "Suggested_Correction",
                "Admin_Decision",
                "Final_Answer",
                "Correction_Notes"
            ]
        ],
        use_container_width=True,
        height=500
    )

    excel_bytes = to_excel(df_edit)

    st.download_button(
        "Download corrected Excel",
        data=excel_bytes,
        file_name="FGs_All_Answers_25-6-2026_Corrected_Admin.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
