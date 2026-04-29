#!/usr/bin/env python
# coding: utf-8

# # Analyse de l’état actuel - Data Entry App
# 
# This notebook creates a Streamlit data-entry app based on the Word template. Run the first cell to save the app as a `.py` file, then run the second cell to launch it.

# In[ ]:


# Install required packages if needed
# Run this cell once if Streamlit or openpyxl are not installed.

# !pip install streamlit pandas openpyxl


# In[1]:


import sqlite3
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


APP_TITLE = "Analyse de l’état actuel - Formulaire de collecte"
DB_PATH = Path("etat_actuel_responses.db")


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
        metadata.get("respondent_name", ""),
        metadata.get("respondent_unit", ""),
        metadata.get("respondent_email", ""),
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
        "respondent_name": row["respondent_name"],
        "respondent_unit": row["respondent_unit"],
        "respondent_email": row["respondent_email"],
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


def text_area(label, key, height=120):
    return st.text_area(label, key=key, height=height)


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="📋", layout="wide")
    init_db()

    st.session_state.setdefault("n_stakeholders", 5)
    st.session_state.setdefault("n_peer_rows", 5)

    st.title(APP_TITLE)
    st.caption(
        "Formulaire numérique inspiré du modèle Word d’analyse de l’état actuel "
        "pour collecter les réponses des unités ou parties prenantes."
    )

    mode = "Saisir une réponse"

    if mode == "Saisir une réponse":
        with st.form("etat_actuel_form", clear_on_submit=False):
            st.markdown("## Informations du répondant")

            col1, col2 = st.columns(2)

            with col1:
                respondent_name = st.text_input("Nom du répondant")
                respondent_unit = st.text_input("Unité / Faculté / Service")

            with col2:
                respondent_email = st.text_input("Email")
                response_date = st.date_input("Date de réponse")

            st.divider()

            section_header("I - Attentes des parties prenantes")
            st.write("Indiquez les parties prenantes concernées et leurs attentes principales.")

            stakeholder_rows = []

            for i in range(1, st.session_state.n_stakeholders + 1):
                col1, col2 = st.columns([1, 2])

                with col1:
                    stakeholder = st.text_input(
                        f"Partie prenante {i}",
                        key=f"stakeholder_{i}",
                    )

                with col2:
                    expectation = st.text_area(
                        f"Attentes de la partie prenante {i}",
                        key=f"expectation_{i}",
                        height=80,
                    )

                if stakeholder.strip() or expectation.strip():
                    stakeholder_rows.append({
                        "partie_prenante": stakeholder,
                        "attentes": expectation,
                    })

            add_stakeholder = st.form_submit_button("Ajouter une autre partie prenante")

            if add_stakeholder:
                st.session_state.n_stakeholders += 1
                st.rerun()

            st.divider()

            section_header(
                "II - Analyse de l’environnement externe et interne",
                "Cette section examine l’état actuel de l’institution, les tendances, les enjeux, les meilleures pratiques et les idées stratégiques."
            )

            sector_trends = text_area(
                "Informations générales sur le secteur et tendances",
                "sector_trends",
            )

            professional_associations = text_area(
                "Informations provenant des associations professionnelles",
                "professional_associations",
            )

            peer_institutions_info = text_area(
                "Informations provenant des institutions paires",
                "peer_institutions_info",
            )

            best_practices = text_area(
                "Meilleures pratiques et/ou programmes innovants",
                "best_practices",
            )

            ideas_suggestions = text_area(
                "Idées et suggestions",
                "ideas_suggestions",
            )

            st.divider()

            section_header("III - Analyse des Institutions Paires")

            peer_rows = []

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("**Critères de Sélection**")
            with col2:
                st.markdown("**Institutions Correspondantes**")
            with col3:
                st.markdown("**Types d'Informations Disponibles**")
            with col4:
                st.markdown("**Plan de Collecte (Qui, Quand, Comment)**")

            for i in range(1, st.session_state.n_peer_rows + 1):
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    criteria = st.text_area(
                        "Critères de Sélection",
                        key=f"criteria_{i}",
                        height=100,
                        label_visibility="collapsed",
                        placeholder="Exemple : Taille des effectifs, Statut Jésuite, Budget",
                    )

                with col2:
                    institution = st.text_area(
                        "Institutions Correspondantes",
                        key=f"institution_{i}",
                        height=100,
                        label_visibility="collapsed",
                        placeholder="Exemple : Université Georgetown",
                    )

                with col3:
                    info_available = st.text_area(
                        "Types d'Informations Disponibles",
                        key=f"info_available_{i}",
                        height=100,
                        label_visibility="collapsed",
                        placeholder="Exemple : Meilleures pratiques, données de référence",
                    )

                with col4:
                    collection_plan = st.text_area(
                        "Plan de Collecte",
                        key=f"collection_plan_{i}",
                        height=100,
                        label_visibility="collapsed",
                        placeholder="Exemple : Entretien avec le doyen via Zoom, Mai 2026",
                    )

                if any(x.strip() for x in [criteria, institution, info_available, collection_plan]):
                    peer_rows.append({
                        "criteres_selection": criteria,
                        "institutions_correspondantes": institution,
                        "types_informations_disponibles": info_available,
                        "plan_collecte": collection_plan,
                    })

            add_peer_row = st.form_submit_button("Ajouter une institution paire")

            if add_peer_row:
                st.session_state.n_peer_rows += 1
                st.rerun()

            st.divider()

            section_header(
                "IV - Ressources internes et opérations",
                "Cette section permet d’identifier les ressources critiques et les éléments internes nécessaires au soutien des plans futurs."
            )

            key_resources = text_area("Ressources clés", "key_resources")
            leadership = text_area("Leadership", "leadership")
            climate_communication = text_area("Climat et communication", "climate_communication")

            st.divider()

            section_header("V - Analyse FFOM")

            col1, col2 = st.columns(2)

            with col1:
                strengths = st.text_area(
                    "Forces",
                    key="strengths",
                    height=180,
                    placeholder=(
                        "Que faisons-nous exceptionnellement bien ?\n"
                        "Quelles connaissances, compétences ou ressources possédons-nous ?\n"
                        "De quoi êtes-vous fier ?"
                    ),
                )

                opportunities = st.text_area(
                    "Opportunités",
                    key="opportunities",
                    height=180,
                    placeholder=(
                        "Quelles tendances ou événements émergents pouvons-nous exploiter ?\n"
                        "Technologie, politiques publiques, profils démographiques, etc."
                    ),
                )

            with col2:
                weaknesses = st.text_area(
                    "Faiblesses",
                    key="weaknesses",
                    height=180,
                    placeholder=(
                        "Que pourrions-nous faire de mieux ?\n"
                        "De quoi se plaint-on à notre sujet ?\n"
                        "Quelles sont nos vulnérabilités ?"
                    ),
                )

                threats = st.text_area(
                    "Menaces",
                    key="threats",
                    height=180,
                    placeholder=(
                        "Quels obstacles externes bloquent notre progression ?\n"
                        "Y a-t-il des changements significatifs à venir ?\n"
                        "Que font les autres universités qui pourrait nous impacter ?"
                    ),
                )

            submitted = st.form_submit_button("Enregistrer la réponse")

            if submitted:
                metadata = {
                    "respondent_name": respondent_name,
                    "respondent_unit": respondent_unit,
                    "respondent_email": respondent_email,
                    "response_date": str(response_date),
                }

                data = {
                    "metadata": metadata,
                    "stakeholders": {
                        "rows": stakeholder_rows,
                    },
                    "environment_analysis": {
                        "sector_trends": sector_trends,
                        "professional_associations": professional_associations,
                        "peer_institutions_info": peer_institutions_info,
                        "best_practices": best_practices,
                        "ideas_suggestions": ideas_suggestions,
                    },
                    "peer_institutions": {
                        "rows": peer_rows,
                    },
                    "internal_resources_operations": {
                        "key_resources": key_resources,
                        "leadership": leadership,
                        "climate_communication": climate_communication,
                    },
                    "swot": {
                        "strengths": strengths,
                        "weaknesses": weaknesses,
                        "opportunities": opportunities,
                        "threats": threats,
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


# In[ ]:




