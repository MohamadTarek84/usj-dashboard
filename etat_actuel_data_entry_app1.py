#!/usr/bin/env python
# coding: utf-8

import sqlite3
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


APP_TITLE = "PLAN STRATÉGIQUE USJ 2032"
DB_PATH = Path("etat_actuel_responses.db")
LOGO_PATH = Path("LogoUAQ.png")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submitted_at TEXT NOT NULL,
            respondent_name TEXT,
            respondent_unit TEXT,
            respondent_email TEXT,
            data_json TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_response(metadata, data):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO responses (
            submitted_at,
            respondent_name,
            respondent_unit,
            respondent_email,
            data_json
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        metadata.get("responsable", ""),
        metadata.get("institution", ""),
        metadata.get("email", ""),
        json.dumps(data, ensure_ascii=False),
    ))
    conn.commit()
    conn.close()


def load_responses():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM responses ORDER BY id DESC", conn)
    conn.close()
    return df


def flatten_response(row):
    base = {
        "id": row["id"],
        "submitted_at": row["submitted_at"],
        "responsable": row["respondent_name"],
        "institution": row["respondent_unit"],
        "email": row["respondent_email"],
    }

    data = json.loads(row["data_json"])

    for section, values in data.items():
        if isinstance(values, dict):
            for key, value in values.items():
                if isinstance(value, list):
                    base[f"{section}_{key}"] = json.dumps(value, ensure_ascii=False)
                else:
                    base[f"{section}_{key}"] = value
        else:
            base[section] = values

    return base


def section_header(title, description=None):
    st.markdown(f"## {title}")
    if description:
        st.info(description)


def text_area(label, key, height=120, placeholder=None):
    return st.text_area(label, key=key, height=height, placeholder=placeholder)


def render_first_page_header():
    col_left, col_right = st.columns([2.2, 1])

    with col_left:
        st.markdown(
            """
            <div style="padding-top:20px;">
                <h1 style="font-size:42px; margin-bottom:0px; color:#001f5b;">
                    PLAN STRATÉGIQUE USJ 2032
                </h1>
                <h3 style="color:#1f3c88; margin-top:8px; margin-bottom:0px;">
                    Analyse de l’état actuel et propositions
                </h3>
                <h5 style="margin-top:4px; color:#333333;">
                    (pré-planification stratégique USJ)
                </h5>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=420)
        else:
            st.warning("LogoUAQ.png non trouvé. Placez le logo dans le même dossier que le script.")

    st.markdown("---")


def render_document_structure():
    st.markdown("## Structure du document")

    st.markdown(
        """
        <div style="line-height:2; font-size:17px;">
            <b>I - Introduction</b><br>
            <b>II - Identification des parties prenantes</b><br>
            <b>III - Analyse interne de l’État actuel de l’Université</b><br>
            <b>IV - Analyse externe de l’environnement actuel de l’Université</b><br>
            <b>V - Analyse SWOT – Niveau USJ</b><br>
            <b>VI - Priorités stratégiques et initiatives proposées – Niveau USJ</b><br>
            <b>VII - Annexes</b><br>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")


def main():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📋",
        layout="wide"
    )

    st.markdown("""
    <style>
    html, body, [class*="css"], [class*="st-"], .stApp {
        font-family: Candara, Calibri, Arial, sans-serif !important;
    }

    h1, h2, h3, h4, h5, h6, p, div, span, label, button, input, textarea, select {
        font-family: Candara, Calibri, Arial, sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

    init_db()

    st.session_state.setdefault("n_stakeholders", 5)
    st.session_state.setdefault("n_peer_rows", 5)
    st.session_state.setdefault("n_strategic_priorities", 3)

    render_first_page_header()

    mode = st.sidebar.radio(
        "Navigation",
        ["Saisir une réponse", "Consulter / exporter les réponses"],
    )

    if mode == "Saisir une réponse":
        with st.form("etat_actuel_form", clear_on_submit=False):

            st.markdown("## Informations générales")

            col1, col2, col3 = st.columns(3)

            with col1:
                institution = st.text_input("Institution")

            with col2:
                responsable = st.text_input("Responsable")

            with col3:
                response_date = st.date_input("Date")

            email = st.text_input("Email du responsable")

            st.markdown("---")

            render_document_structure()

            section_header("I - Introduction")

            introduction = text_area(
                "Introduction générale",
                key="introduction",
                height=220,
                placeholder="Saisir les éléments introductifs ou les constats généraux..."
            )

            st.divider()

            section_header("II - Identification des parties prenantes")
            st.write("Indiquez les parties prenantes consultées.")

            stakeholder_rows = []

            for i in range(1, st.session_state.n_stakeholders + 1):
                st.markdown(f"### Partie prenante {i}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    stakeholder_name = st.text_input(
                        "Nom",
                        key=f"stakeholder_name_{i}",
                    )

                with col2:
                    stakeholder_position = st.text_input(
                        "Poste",
                        key=f"stakeholder_position_{i}",
                    )

                with col3:
                    stakeholder_affiliation = st.text_input(
                        "Organisme d’affiliation",
                        key=f"stakeholder_affiliation_{i}",
                    )

                if any(x.strip() for x in [stakeholder_name, stakeholder_position, stakeholder_affiliation]):
                    stakeholder_rows.append({
                        "nom": stakeholder_name,
                        "poste": stakeholder_position,
                        "organisme_affiliation": stakeholder_affiliation,
                    })

            add_stakeholder = st.form_submit_button("Ajouter une autre partie prenante")

            if add_stakeholder:
                st.session_state.n_stakeholders += 1
                st.rerun()

            st.divider()

            section_header(
                "III - Analyse interne de l’État actuel de l’Université",
                "Cette section permet d’identifier les forces et les faiblesses à l’échelle de l’Université."
            )

            internal_themes = [
                "Soutenabilité financière",
                "Gouvernance et Leadership",
                "Stratégie académique",
                "Recherche et Innovation",
                "Environnement digital",
                "Succès des étudiants",
                "Ressources humaines",
                "Stratégie internationale",
                "Mission sociétale",
                "Espace et infrastructures",
                "Environnement de travail",
                "Diversité et inclusion",
                "Développement Durable",
                "Autre",
            ]

            internal_analysis = {}

            for theme in internal_themes:
                internal_analysis[theme] = text_area(
                    theme,
                    key=f"internal_{theme}",
                    height=120,
                    placeholder=f"Saisir les constats relatifs à : {theme}"
                )

            st.divider()

            section_header(
                "IV - Analyse externe de l’environnement actuel de l’Université",
                "Cette section permet d’identifier les opportunités et les menaces issues de l’environnement externe."
            )

            external_themes = [
                "Exigences ministérielles et Environnement réglementaire",
                "Marché du travail et Associations professionnelles",
                "Institutions paires : Concurrence et Benchmarking",
                "L’Intelligence artificielle",
                "Attractivité vis-à-vis des élèves des écoles",
                "Réputation et Image",
                "Autres Menaces ou Opportunités éventuelles",
                "Suggestions de meilleures pratiques ou de programmes innovants",
            ]

            external_analysis = {}

            for theme in external_themes:
                external_analysis[theme] = text_area(
                    theme,
                    key=f"external_{theme}",
                    height=120,
                    placeholder=f"Saisir les constats relatifs à : {theme}"
                )

            st.divider()

            section_header("V - Analyse SWOT – Niveau USJ")

            st.markdown("### Facteurs internes")

            swot_internal_rows = []

            for i in range(1, 6):
                col1, col2 = st.columns(2)

                with col1:
                    force = st.text_area(
                        f"Force {i}",
                        key=f"force_{i}",
                        height=80,
                    )

                with col2:
                    faiblesse = st.text_area(
                        f"Faiblesse {i}",
                        key=f"faiblesse_{i}",
                        height=80,
                    )

                if force.strip() or faiblesse.strip():
                    swot_internal_rows.append({
                        "force": force,
                        "faiblesse": faiblesse,
                    })

            st.markdown("### Facteurs externes")

            swot_external_rows = []

            for i in range(1, 6):
                col1, col2 = st.columns(2)

                with col1:
                    opportunite = st.text_area(
                        f"Opportunité {i}",
                        key=f"opportunite_{i}",
                        height=80,
                    )

                with col2:
                    menace = st.text_area(
                        f"Menace {i}",
                        key=f"menace_{i}",
                        height=80,
                    )

                if opportunite.strip() or menace.strip():
                    swot_external_rows.append({
                        "opportunite": opportunite,
                        "menace": menace,
                    })

            st.divider()

            section_header("VI - Priorités stratégiques et initiatives proposées – Niveau USJ")

            strategic_priorities = []

            for i in range(1, st.session_state.n_strategic_priorities + 1):
                st.markdown(f"### Priorité stratégique {i}")

                priority = st.text_area(
                    f"Priorité stratégique {i}",
                    key=f"priority_{i}",
                    height=80,
                    placeholder="Formuler la priorité stratégique..."
                )

                initiatives = st.text_area(
                    f"Initiatives liées à la priorité {i}",
                    key=f"initiatives_{i}",
                    height=120,
                    placeholder="Indiquer 1 à 3 initiatives, idéalement formulées avec un verbe d’action..."
                )

                if priority.strip() or initiatives.strip():
                    strategic_priorities.append({
                        "priorite_strategique": priority,
                        "initiatives": initiatives,
                    })

            st.divider()

            section_header("Pour finir")

            usj_reconnue = text_area(
                "Nous souhaitons que l’USJ soit reconnue pour ...",
                key="usj_reconnue",
                height=90,
            )

            etudiants_disent = text_area(
                "Nous souhaitons que nos étudiants disent que l’USJ ...",
                key="etudiants_disent",
                height=90,
            )

            excellent_lieu = text_area(
                "L’USJ est un excellent lieu de travail si ...",
                key="excellent_lieu",
                height=90,
            )

            submitted = st.form_submit_button("Enregistrer la réponse")

            if submitted:
                metadata = {
                    "institution": institution,
                    "responsable": responsable,
                    "email": email,
                    "response_date": str(response_date),
                }

                data = {
                    "metadata": metadata,
                    "introduction": {
                        "introduction": introduction,
                    },
                    "stakeholders": {
                        "rows": stakeholder_rows,
                    },
                    "internal_analysis": internal_analysis,
                    "external_analysis": external_analysis,
                    "swot_internal": {
                        "rows": swot_internal_rows,
                    },
                    "swot_external": {
                        "rows": swot_external_rows,
                    },
                    "strategic_priorities": {
                        "rows": strategic_priorities,
                    },
                    "final_statements": {
                        "usj_reconnue_pour": usj_reconnue,
                        "etudiants_disent_que_usj": etudiants_disent,
                        "excellent_lieu_de_travail_si": excellent_lieu,
                    },
                }

                save_response(metadata, data)
                st.success("Réponse enregistrée avec succès.")

    else:
        st.markdown("## Consulter / exporter les réponses")

        df = load_responses()

        if df.empty:
            st.warning("Aucune réponse enregistrée pour le moment.")
            return

        st.metric("Nombre total de réponses", len(df))

        st.markdown("### Réponses enregistrées")
        st.dataframe(
            df[["id", "submitted_at", "respondent_name", "respondent_unit", "respondent_email"]],
            use_container_width=True,
        )

        flat_df = pd.DataFrame([flatten_response(row) for _, row in df.iterrows()])

        csv_data = flat_df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="Télécharger les réponses en CSV",
            data=csv_data,
            file_name="etat_actuel_responses.csv",
            mime="text/csv",
        )

        excel_path = Path("etat_actuel_responses.xlsx")
        flat_df.to_excel(excel_path, index=False)

        with open(excel_path, "rb") as f:
            st.download_button(
                label="Télécharger les réponses en Excel",
                data=f,
                file_name="etat_actuel_responses.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        st.markdown("### Données complètes")
        st.dataframe(flat_df, use_container_width=True)


if __name__ == "__main__":
    main()
