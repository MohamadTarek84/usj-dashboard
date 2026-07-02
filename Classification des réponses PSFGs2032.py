"""
PLAN STRATÉGIQUE USJ 2032 - Plateforme IA supervisée d'analyse thématique
==========================================================================

Ce fichier remplace la version précédente, qui contenait quatre générations
successives du même pipeline de classification empilées les unes sur les
autres (chaque nouvelle définition de fonction écrasant silencieusement la
précédente). Cette version ne garde qu'UNE implémentation propre de chaque
fonction, et ajoute un véritable moteur de classification supervisée
(entraîné sur vos réponses validées) plutôt que de se reposer uniquement
sur des règles de mots-clés.

Architecture de classification (3 moteurs, clairement séparés) :

  1. HEURISTIQUE (démarrage à froid, aucune donnée requise)
     Règles de domaine + TF-IDF. Sert à pré-remplir des suggestions
     avant qu'un modèle entraîné existe. Précision plafonnée par nature :
     un système à base de règles ne "comprend" pas le texte, il reconnaît
     des motifs. Utile pour démarrer, pas pour la précision finale.

  2. MODÈLE SUPERVISÉ ENTRAÎNÉ (recommandé pour la précision réelle)
     TF-IDF + Régression logistique / SVM linéaire, entraîné sur les
     réponses que vous avez validées dans l'onglet de validation experte.
     C'est le seul moyen d'obtenir une "haute précision" mesurable :
     la précision annoncée est calculée par validation croisée sur vos
     propres données, pas une estimation. Plus vous validez de réponses,
     plus ce modèle s'améliore. Le modèle peut être téléchargé et réutilisé.

  3. IA INSTITUTIONNELLE (optionnel, désactivé par défaut)
     Appel à une API externe (OpenAI). Envoie le texte des réponses à un
     service tiers : à activer uniquement si cela est acceptable pour la
     confidentialité de vos données. Isolé et clairement signalé dans
     l'interface, jamais activé silencieusement.
"""

import re
import os
import html
import base64
import difflib
import json
import urllib.request
from pathlib import Path
from io import BytesIO
from collections import Counter

import numpy as np
import pandas as pd
import streamlit as st

# ============================================================
# CONSTANTS
# ============================================================

APP_TITLE = "PLAN STRATÉGIQUE USJ 2032"
SHEET_NAME = "All answers 29-6-2026"

USJ_BLUE = "#001F5B"
USJ_BLUE_2 = "#1F3C88"
USJ_RED = "#8B1538"
USJ_LIGHT_BLUE = "#EAF2F8"
USJ_TEXT = "#1B2A41"
LOGO_PATH = "LOGO NEW UAQ.png"

ENGINE_HEURISTIC = "Heuristique (règles + TF-IDF) - démarrage à froid"
ENGINE_TRAINED = "Modèle supervisé entraîné - recommandé pour la précision"
ENGINE_LLM = "IA institutionnelle (API externe) - optionnel"

SWOT_ELEMENTS = ["Forces", "Faiblesses", "Opportunités", "Menaces"]

MIN_EXAMPLES_PER_THEME = 3
MIN_TOTAL_TRAINING_EXAMPLES = 15


# ============================================================
# BASIC UTILITIES
# ============================================================

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


def get_col(df, possible_names):
    cols = {normalize(c): c for c in df.columns}
    for name in possible_names:
        n = normalize(name)
        if n in cols:
            return cols[n]
    return None


APP_CSS = f"""
<style>
html, body, .stApp {{
    font-family: Candara, Calibri, Arial, sans-serif !important;
    color:{USJ_TEXT};
}}
header, footer, #MainMenu {{ display:none !important; }}
.block-container {{ max-width:100% !important; padding-left:3rem !important; padding-right:3rem !important; }}
h1, h2, h3 {{ color:{USJ_BLUE} !important; font-weight:800 !important; }}
.stButton button, .stDownloadButton button {{
    background-color:#0070C0 !important; color:white !important; border-radius:8px !important;
    border:1px solid #0070C0 !important; font-weight:800 !important; font-size:18px !important;
}}
.stButton button p, .stDownloadButton button p {{ color:white !important; }}
.ai-hero {{
    background: linear-gradient(135deg, #001F5B 0%, #123C7C 55%, #8B1538 100%);
    color: white; border-radius: 22px; padding: 30px 34px; margin: 8px 0 24px 0;
    box-shadow: 0 16px 38px rgba(0,31,91,0.22);
}}
.ai-hero h2 {{ color: white !important; margin: 0 0 8px 0; font-size: 32px; font-weight: 900; }}
.ai-hero p {{ color: #EAF2F8; margin: 0; font-size: 16px; line-height: 1.5; }}
.ai-card {{
    background: white; border: 1px solid #D0D6E0; border-radius: 18px; padding: 18px 22px;
    margin: 14px 0 18px 0; box-shadow: 0 8px 24px rgba(0,0,0,0.055);
}}
.ai-info-box {{
    background: #EAF2F8; color: #003B7A; border-left: 6px solid {USJ_BLUE}; border-radius: 12px;
    padding: 14px 18px; margin: 14px 0; font-size: 15px;
}}
.ai-warning {{
    background: #FFF7E6; border-left: 6px solid #F59F00; border-radius: 12px; padding: 14px 18px;
    color: #7A4B00; font-weight: 700; margin: 12px 0;
}}
.ai-danger {{
    background: #FDECEC; border-left: 6px solid {USJ_RED}; border-radius: 12px; padding: 14px 18px;
    color: #7A1B2B; font-weight: 700; margin: 12px 0;
}}
.ai-kpi {{
    background: white; border: 1px solid #D0D6E0; border-radius: 16px; padding: 16px 18px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.045); min-height: 92px;
}}
.ai-kpi-number {{ color: {USJ_RED}; font-size: 28px; font-weight: 900; }}
.ai-kpi-label {{ color: #64748B; font-size: 13px; font-weight: 700; margin-top: 3px; }}
</style>
"""


# ============================================================
# OFFICIAL THEME TAXONOMY (unchanged from your source of truth)
# ============================================================

THEME_TAXONOMY = {
    "PSG": {
        "internal": [
            "Soutenabilité financière",
            "Gouvernance et Leadership (gestion, relation, représentation, etc.)",
            "Stratégie académique et qualité d’enseignement",
            "Recherche et Innovation",
            "Ressources documentaires et Environnement digital",
            "Succès des étudiants (recrutement, accompagnement, services de support, employabilité, etc.)",
            "Ressources humaines",
            "Stratégie et mobilité internationales",
            "Mission sociétale",
            "Espace et infrastructures",
            "Environnement de travail",
            "Diversité et inclusion",
            "Développement Durable (ODD)",
            "Autre",
        ],
        "external": [
            "Marché du travail et Associations professionnelles",
            "Concurrence avec les autres universités",
            "Intelligence artificielle",
            "Réputation et image",
            "Environnement politique et économique, émigration",
            "Autres",
        ],
    },
    "Anciens": {
        "internal": [
            "Soutenabilité financière",
            "Gouvernance et Leadership (Gestion, relation, représentation, etc.)",
            "Stratégie académique et qualité d’enseignement",
            "Recherche et Innovation",
            "Succès des étudiants (recrutement, accompagnement, services de support, employabilité, etc.)",
            "Ressources humaines",
            "Mission sociétale",
            "Espace et infrastructures",
            "Autre",
        ],
        "external": [
            "Marché du travail et Associations professionnelles",
            "Concurrence avec les autres universités",
            "Intelligence artificielle",
            "Réputation et image",
            "Environnement politique et économique, émigration",
            "Autres",
        ],
    },
    "Directeurs": {
        "internal": [
            "Soutenabilité financière",
            "Gouvernance et Leadership (gestion, relation, représentation, etc.)",
            "Stratégie académique et qualité d’enseignement",
            "Recherche et Innovation",
            "Ressources documentaires et Environnement digital",
            "Succès des étudiants (recrutement, accompagnement, services de support, employabilité, etc.)",
            "Ressources humaines",
            "Stratégie et mobilité internationales",
            "Mission sociétale",
            "Espace et infrastructures",
            "Environnement de travail",
            "Diversité et inclusion",
            "Développement Durable (ODD)",
            "Autre",
        ],
        "external": [
            "Marché du travail et relations avec les employeurs",
            "Concurrence avec les autres universités",
            "Intelligence artificielle",
            "Réputation et image",
            "Environnement politique et économique, émigration",
            "Autres",
        ],
    },
    "Étudiants": {
        "internal": [
            "Qualité de l’enseignement (Accompagnement, Orientation, Tutorat, etc.)",
            "Relation avec l’administration et les enseignants",
            "Représentation des étudiants",
            "Ressources documentaires, numériques et informatiques",
            "Espace et infrastructure",
            "Vie universitaire (Vie étudiante, Sport, Aide psychologique, etc.)",
            "Diversité et inclusion",
            "Développement durable (ODD)",
            "Mission sociétale",
            "Mobilité internationale",
            "Aide financière",
            "Insertion professionnelle",
            "Autres",
        ],
        "external": [
            "Marché du travail et relations avec les employeurs",
            "Concurrence avec les autres universités",
            "Intelligence artificielle",
            "Réputation et image",
            "Environnement politique et économique, émigration",
            "Autres",
        ],
    },
    "Enseignants": {
        "internal": [
            "Soutenabilité financière",
            "Gouvernance et Leadership (gestion, relation, représentation, etc.)",
            "Stratégie académique et qualité d’enseignement",
            "Recherche et Innovation",
            "Ressources documentaires et Environnement digital",
            "Succès des étudiants (recrutement, accompagnement, services de support, employabilité, etc.)",
            "Ressources humaines",
            "Stratégie et mobilité internationales",
            "Mission sociétale",
            "Espace et infrastructures",
            "Environnement de travail",
            "Diversité et inclusion",
            "Développement Durable (ODD)",
            "Autre",
        ],
        "external": [
            "Marché du travail et Associations professionnelles",
            "Concurrence avec les autres universités",
            "Intelligence artificielle",
            "Réputation et image",
            "Environnement politique et économique, émigration",
            "Autres",
        ],
    },
}

PARTICIPANT_TYPE_ALIASES = {
    "psg": "PSG",
    "anciens": "Anciens",
    "directeurs": "Directeurs",
    "directors": "Directeurs",
    "etudiants": "Étudiants",
    "étudiants": "Étudiants",
    "students": "Étudiants",
    "enseignants": "Enseignants",
    "teachers": "Enseignants",
}


def canonical_participant_type(value):
    raw = clean(value)
    norm = normalize(raw)
    return PARTICIPANT_TYPE_ALIASES.get(norm, raw)


def official_themes_for(participant_type, swot_element, include_autre=False):
    participant_type = canonical_participant_type(participant_type)
    family = "internal" if swot_element in ["Forces", "Faiblesses"] else "external"
    themes = THEME_TAXONOMY.get(participant_type, {}).get(family, [])
    if include_autre:
        return themes
    return [t for t in themes if normalize(t) not in ["autre", "autres"]]


def _detect_swot_from_text(value):
    """Detect one SWOT element from a single field.
    This is intentionally applied field by field so that an exact category
    like "Forces" cannot be overridden by another field containing
    "Faiblesses".
    """
    text_n = normalize(value)
    if not text_n:
        return ""

    force_terms = [
        "force", "forces", "strength", "strengths",
        "atout", "atouts", "point fort", "points forts"
    ]
    faiblesse_terms = [
        "faiblesse", "faiblesses", "weakness", "weaknesses",
        "point faible", "points faibles"
    ]
    opportunite_terms = [
        "opportunite", "opportunites", "opportunity", "opportunities",
        "levier externe", "leviers externes"
    ]
    menace_terms = [
        "menace", "menaces", "threat", "threats",
        "risque externe", "risques externes"
    ]

    if any(_contains_term(text_n, term) for term in force_terms):
        return "Forces"
    if any(_contains_term(text_n, term) for term in faiblesse_terms):
        return "Faiblesses"
    if any(_contains_term(text_n, term) for term in opportunite_terms):
        return "Opportunités"
    if any(_contains_term(text_n, term) for term in menace_terms):
        return "Menaces"
    return ""


def detect_swot_element(row):
    """Detect SWOT from structured Excel fields.
    Priority order is category -> question -> section.
    The category column is the source of truth when it explicitly contains
    Forces / Faiblesses / Opportunités / Menaces.
    """
    for field in ["category", "question", "section"]:
        detected = _detect_swot_from_text(row.get(field, ""))
        if detected:
            return detected
    return ""



# ============================================================
# TEXT PROCESSING
# ============================================================

STOPWORDS_FR = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l", "et", "ou", "en",
    "au", "aux", "avec", "sans", "pour", "par", "dans", "sur", "ce", "cet", "cette",
    "ces", "qui", "que", "quoi", "dont", "est", "sont", "etre", "avoir", "plus",
    "moins", "tres", "comme", "nous", "vous", "ils", "elles", "il", "elle",
    "ne", "pas", "se", "sa", "son", "ses", "leur", "leurs", "a", "of", "the",
    "and", "or", "to", "in", "for", "with", "by", "on",
    "renforce", "renforcee", "renforcer", "davantage", "ameliorer", "meilleur",
    "meilleure", "systeme", "niveau", "mise", "jour", "usj", "universite",
}


def tokenize_for_similarity(text):
    text = normalize(text)
    tokens = re.findall(r"[a-z0-9]{3,}", text)
    return [t for t in tokens if t not in STOPWORDS_FR]


def _contains_term(text_norm, term):
    term_norm = normalize(term)
    if not term_norm:
        return False
    if " " in term_norm:
        return term_norm in text_norm
    return re.search(r"(^|[^a-z0-9])" + re.escape(term_norm) + r"([^a-z0-9]|$)", text_norm) is not None


# ============================================================
# HEURISTIC ENGINE (cold-start only, no training data required)
# ============================================================
# Domain vocabularies. Each domain lists positive terms and which official
# themes it supports / actively contradicts. This gives a conservative
# starting point for classification before any labeled data exists.

DOMAIN_RULES = {
    "academic_teaching": {
        "terms": ["cours", "programme", "programmes", "formation", "formations", "enseignement",
                  "pedagogie", "pedagogique", "curriculum", "credit", "credits", "ects", "diplome",
                  "diplomes", "evaluation", "apprentissage", "matiere", "matieres", "langue", "langues",
                  "anglais", "francais", "trilinguisme", "accreditation", "accreditations", "academique"],
        "themes": ["strategie academique et qualite d enseignement", "qualite de l enseignement"],
        "negative_themes": ["mission societale", "developpement durable odd", "ressources humaines",
                             "gouvernance et leadership"],
    },
    "student_success": {
        "terms": ["etudiant", "etudiants", "recrutement", "inscription", "inscriptions", "accompagnement",
                  "orientation", "support", "service", "services", "reussite", "parcours", "employabilite"],
        "themes": ["succes des etudiants", "qualite de l enseignement"],
        "negative_themes": ["mission societale", "ressources humaines"],
    },
    "research": {
        "terms": ["recherche", "innovation", "publication", "publications", "laboratoire", "laboratoires",
                  "doctorat", "these", "scientifique", "scientifiques", "brevet", "brevets", "valorisation"],
        "themes": ["recherche et innovation"],
        "negative_themes": ["mission societale", "vie universitaire", "relation avec l administration et les enseignants"],
    },
    "digital_resources": {
        "terms": ["bibliotheque", "documentaire", "documentaires", "numerique", "numeriques", "digital",
                  "digitale", "informatique", "informatiques", "technologie", "technologique", "plateforme",
                  "plateformes", "logiciel", "logiciels", "outils", "donnees", "data"],
        "themes": ["ressources documentaires et environnement digital", "ressources documentaires numeriques et informatiques"],
        "negative_themes": ["mission societale", "soutenabilite financiere"],
    },
    "hr": {
        "terms": ["personnel", "personnels", "enseignant", "enseignants", "professeur", "professeurs",
                  "administratif", "administratifs", "rh", "ressources humaines", "recrutement", "charge",
                  "charges", "competence", "competences"],
        "themes": ["ressources humaines"],
        "negative_themes": ["mission societale", "strategie academique et qualite d enseignement"],
    },
    "governance": {
        "terms": ["gouvernance", "leadership", "direction", "doyen", "doyens", "directeur", "directeurs",
                  "decision", "decisions", "procedure", "procedures", "transparence", "responsabilisation",
                  "accountability", "autonomie", "centralisation", "decentralisation", "pilotage", "administration"],
        "themes": ["gouvernance et leadership", "relation avec l administration et les enseignants"],
        "negative_themes": ["mission societale", "recherche et innovation"],
    },
    "finance": {
        "terms": ["budget", "financement", "financier", "financiere", "finance", "frais", "scolarite",
                  "bourse", "bourses", "cout", "couts", "paiement", "soutenabilite", "viabilite"],
        "themes": ["soutenabilite financiere", "aide financiere"],
        "negative_themes": ["mission societale", "qualite de l enseignement"],
    },
    "infrastructure": {
        "terms": ["campus", "batiment", "batiments", "salle", "salles", "locaux", "infrastructure",
                  "infrastructures", "espace", "espaces", "equipement", "equipements", "maintenance"],
        "themes": ["espace et infrastructures", "espace et infrastructure"],
        "negative_themes": ["mission societale", "strategie academique et qualite d enseignement"],
    },
    "international": {
        "terms": ["international", "internationale", "internationales", "mobilite", "echange", "echanges",
                  "partenariat", "partenariats", "etranger", "etrangers", "diaspora", "francophonie"],
        "themes": ["strategie et mobilite internationales", "mobilite internationale"],
        "negative_themes": ["mission societale", "environnement politique et economique emigration"],
    },
    "social_mission": {
        "terms": ["mission societale", "mission sociale", "engagement social", "responsabilite sociale",
                  "societe", "societal", "societale", "communautaire", "communaute", "citoyen", "citoyenne",
                  "impact social", "reconstruction", "liban", "territoire"],
        "themes": ["mission societale"],
        "negative_themes": ["strategie academique et qualite d enseignement", "ressources documentaires et environnement digital"],
    },
    "work_environment": {
        "terms": ["environnement de travail", "conditions de travail", "climat", "bien etre", "collaboration",
                  "communication interne", "charge de travail", "horaires", "processus administratif"],
        "themes": ["environnement de travail"],
        "negative_themes": ["mission societale", "reputation et image"],
    },
    "student_life": {
        "terms": ["vie universitaire", "vie etudiante", "sport", "activites", "clubs", "animation",
                  "aide psychologique", "psychologique", "experience etudiante"],
        "themes": ["vie universitaire"],
        "negative_themes": ["mission societale", "ressources humaines"],
    },
    "diversity": {
        "terms": ["diversite", "inclusion", "inclusive", "egalite", "equite", "handicap", "genre", "discrimination"],
        "themes": ["diversite et inclusion"],
        "negative_themes": ["mission societale"],
    },
    "sustainability": {
        "terms": ["developpement durable", "odd", "durable", "durabilite", "ecologie", "energie",
                  "transition energetique"],
        "themes": ["developpement durable odd"],
        "negative_themes": ["mission societale", "soutenabilite financiere"],
    },
    "employment_market": {
        "terms": ["marche du travail", "emploi", "employeur", "employeurs", "entreprise", "entreprises",
                  "association professionnelle", "associations professionnelles", "metier", "metiers",
                  "stage", "stages", "carriere", "professionnel"],
        "themes": ["marche du travail et associations professionnelles",
                   "marche du travail et relations avec les employeurs", "insertion professionnelle"],
        "negative_themes": ["mission societale", "soutenabilite financiere"],
    },
    "competition": {
        "terms": ["concurrence", "concurrent", "concurrentes", "competition", "autres universites",
                  "universites americaines", "classe a", "programmes flexibles"],
        "themes": ["concurrence avec les autres universites"],
        "negative_themes": ["mission societale", "strategie academique et qualite d enseignement"],
    },
    "ai": {
        "terms": ["intelligence artificielle", "ia", "ai", "agent conversationnel ia", "automatisation",
                  "generative", "data science", "machine learning"],
        "themes": ["intelligence artificielle"],
        "negative_themes": ["ressources documentaires et environnement digital", "mission societale"],
    },
    "reputation": {
        "terms": ["reputation", "image", "classement", "classements", "visibilite", "notoriete",
                  "attractivite", "perception", "rayonnement", "recruteurs"],
        "themes": ["reputation et image"],
        "negative_themes": ["mission societale", "gouvernance et leadership"],
    },
    "political_economic": {
        "terms": ["politique", "economique", "economie", "crise", "emigration", "emigrer", "instabilite",
                  "instabilites", "inflation", "securite", "guerre", "banque", "bancaire", "immobilier"],
        "themes": ["environnement politique et economique emigration"],
        "negative_themes": ["mission societale", "reputation et image"],
    },
}


def _theme_in_list(theme_norm, theme_patterns):
    return any((pat in theme_norm or theme_norm in pat) for pat in theme_patterns)


def detected_answer_domains(answer):
    answer_norm = normalize(answer)
    domains = {}
    for domain, profile in DOMAIN_RULES.items():
        hits = [t for t in profile["terms"] if _contains_term(answer_norm, t)]
        if hits:
            domains[domain] = min(1.0, 0.35 + 0.18 * len(hits))
    return domains


def domain_guardrail_score(answer, theme):
    theme_norm = normalize(theme)
    domains = detected_answer_domains(answer)
    positive, negative, matched = 0.0, 0.0, []
    for domain, strength in domains.items():
        profile = DOMAIN_RULES[domain]
        if _theme_in_list(theme_norm, profile["themes"]):
            positive += strength
            matched.append(domain)
        if _theme_in_list(theme_norm, profile.get("negative_themes", [])):
            negative += strength
    return min(1.0, positive), min(1.0, negative), matched


def tfidf_scores_against_themes(answer, themes):
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        from sklearn.pipeline import FeatureUnion
    except Exception:
        return [0.0 for _ in themes]

    corpus = [clean(answer)] + [clean(t) for t in themes]
    try:
        features = FeatureUnion([
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=1, strip_accents="unicode")),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, strip_accents="unicode")),
        ])
        matrix = features.fit_transform(corpus)
        return cosine_similarity(matrix[0:1], matrix[1:]).flatten().tolist()
    except Exception:
        return [0.0 for _ in themes]


def heuristic_score_candidates(answer, participant_type, swot_element):
    """Score every official theme for this row using domain rules + TF-IDF.
    Returns a list of (theme, score, matched_domains) sorted best-first.
    """
    themes = official_themes_for(participant_type, swot_element, include_autre=False)
    if not themes:
        return []

    tfidf = tfidf_scores_against_themes(answer, themes)
    detected = detected_answer_domains(answer)

    ranked = []
    for i, theme in enumerate(themes):
        domain_pos, domain_neg, matched = domain_guardrail_score(answer, theme)
        score = (0.60 * domain_pos) + (0.40 * tfidf[i]) - (0.65 * domain_neg)
        # If a clear domain was detected in the answer but this theme is outside
        # that domain entirely, suppress it so generic word overlap can't win.
        if detected and domain_pos == 0:
            score *= 0.5
        score = max(0.0, min(1.0, score))
        ranked.append((theme, score, matched))

    return sorted(ranked, key=lambda x: x[1], reverse=True)


def heuristic_confidence(ranked):
    if not ranked:
        return 0.0
    best, second = ranked[0][1], (ranked[1][1] if len(ranked) > 1 else 0)
    margin = max(best - second, 0)
    conf = 25 + best * 55 + margin * 90
    if best < 0.20:
        conf = min(conf, 40)
    if margin < 0.04:
        conf = min(conf, 55)
    return round(max(5, min(conf, 90)), 1)  # heuristic engine is capped below 90: it is not a trained model


def classify_heuristic(answer, participant_type, swot_element):
    ranked = heuristic_score_candidates(answer, participant_type, swot_element)
    if not ranked:
        return "", 0.0, "", "Aucun thème officiel disponible"
    best_theme, best_score, matched = ranked[0]
    conf = heuristic_confidence(ranked)
    top3 = " | ".join([f"{t} ({round(s * 100, 1)})" for t, s, _ in ranked[:3]])
    evidence = f"domaine détecté: {', '.join(matched)}" if matched else "évidence lexicale faible"
    return best_theme, conf, top3, evidence


# ============================================================
# EXCEL I/O
# ============================================================

def read_corrected_excel(uploaded_file):
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
    question_col = get_col(df, ["Question", "question", "Questions"])
    answer_col = get_col(df, ["Final_Answer", "Final Answer", "Réponse finale", "Reponse finale"])

    missing = []
    for label, col in [("Respondent_Type", type_col), ("groupe", group_col), ("participants", names_col),
                        ("section", section_col), ("category", category_col), ("Final_Answer", answer_col)]:
        if not col:
            missing.append(label)
    if missing:
        st.error("Colonnes manquantes : " + ", ".join(missing))
        st.stop()

    rename_map = {
        type_col: "Respondent_Type",
        group_col: "groupe",
        names_col: "participants",
        section_col: "section",
        category_col: "category",
        answer_col: "Final_Answer",
    }
    if question_col:
        rename_map[question_col] = "question"

    df = df.rename(columns=rename_map)

    if "question" not in df.columns:
        df["question"] = df["category"]

    for col in ["Respondent_Type", "groupe", "participants", "section", "category", "question", "Final_Answer"]:
        if col in df.columns:
            df[col] = df[col].apply(clean)

    df = df[(df["Respondent_Type"] != "") & (df["groupe"] != "")]
    df["swot_element"] = df.apply(detect_swot_element, axis=1)
    return df.reset_index(drop=True)


# ============================================================
# DUPLICATE DETECTION
# ============================================================

DUPLICATE_SYNONYMS = {
    "alumni": "anciens", "ancien": "anciens", "anciens": "anciens",
    "diplome": "diplomes", "diplomes": "diplomes",
    "enseignant": "enseignants", "enseignants": "enseignants",
    "professeur": "enseignants", "professeurs": "enseignants",
    "personnel": "personnel", "personnels": "personnel",
    "administratif": "administratifs", "administratifs": "administratifs",
    "ia": "intelligence_artificielle", "ai": "intelligence_artificielle",
    "intelligence": "intelligence_artificielle", "artificielle": "intelligence_artificielle",
    "emploi": "emploi", "employabilite": "emploi",
    "stage": "stage", "stages": "stage",
}


def canonical_duplicate_tokens(text):
    tokens = tokenize_for_similarity(text)
    canonical = [DUPLICATE_SYNONYMS.get(t, t) for t in tokens]
    return [t for t in canonical if t not in STOPWORDS_FR]


def strict_duplicate_score(answer_a, answer_b):
    a_norm, b_norm = normalize(answer_a), normalize(answer_b)
    if not a_norm or not b_norm:
        return 0.0, "Vide"
    if a_norm == b_norm:
        return 1.0, "Doublon exact"

    seq_ratio = difflib.SequenceMatcher(None, a_norm, b_norm).ratio()
    tokens_a, tokens_b = set(canonical_duplicate_tokens(answer_a)), set(canonical_duplicate_tokens(answer_b))
    if not tokens_a or not tokens_b:
        return seq_ratio, "Texte trop court"

    shared = tokens_a & tokens_b
    union = tokens_a | tokens_b
    jaccard = len(shared) / max(len(union), 1)
    containment = len(shared) / max(min(len(tokens_a), len(tokens_b)), 1)

    has_core_overlap = len(shared) >= 2 or (len(shared) == 1 and min(len(tokens_a), len(tokens_b)) <= 3)
    if not has_core_overlap:
        return max(seq_ratio * 0.35, jaccard), "Même structure possible, mais sujet différent"

    # Three or more shared concept words (after synonym canonicalization) is a strong
    # signal the two answers express the same idea, even if containment/jaccard alone
    # fall just under their individual thresholds (e.g. "anciens" vs "alumni" phrasing).
    if len(shared) >= 3 and containment >= 0.65:
        return max(0.85, containment), "Même idée avec formulation différente"

    if containment >= 0.80 and seq_ratio >= 0.55:
        return max(containment, seq_ratio), "Même idée avec formulation différente"
    if jaccard >= 0.62 and seq_ratio >= 0.50:
        return max(jaccard, seq_ratio), "Doublon probable"
    if seq_ratio >= 0.88 and containment >= 0.55:
        return seq_ratio, "Très proche lexicalement"
    return max(jaccard, containment * 0.75, seq_ratio * 0.50), "Non retenu"


def detect_duplicate_pairs(df):
    rows = df[df["Final_Answer"].apply(clean) != ""].copy()
    rows = rows[rows["swot_element"].isin(SWOT_ELEMENTS)].reset_index(drop=True)
    pairs = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if rows.loc[i, "swot_element"] != rows.loc[j, "swot_element"]:
                continue
            score, reason = strict_duplicate_score(rows.loc[i, "Final_Answer"], rows.loc[j, "Final_Answer"])
            if score >= 0.80:
                pairs.append({
                    "Élément SWOT": rows.loc[i, "swot_element"],
                    "Sous-groupe 1": rows.loc[i, "groupe"], "Réponse 1": rows.loc[i, "Final_Answer"],
                    "Sous-groupe 2": rows.loc[j, "groupe"], "Réponse 2": rows.loc[j, "Final_Answer"],
                    "Score doublon": round(score * 100, 1), "Raison": reason,
                    "Validation expert": "À vérifier",
                })
    return pd.DataFrame(pairs)


# ============================================================
# SUPERVISED MODEL (this is the real path to high accuracy)
# ============================================================

def prepare_training_dataset(validated_df):
    """Build a (text, label) training set from expert-validated rows."""
    if validated_df is None or validated_df.empty:
        return pd.DataFrame()
    text_col = get_col(validated_df, ["Final_Answer", "answer", "text"])
    label_col = get_col(validated_df, ["Validated_Theme", "Theme valide", "theme", "label"])
    swot_col = get_col(validated_df, ["swot_element", "Element SWOT", "SWOT"])
    type_col = get_col(validated_df, ["Respondent_Type", "Type de participants"])
    if not text_col or not label_col:
        return pd.DataFrame()

    out = pd.DataFrame({
        "text": validated_df[text_col].apply(clean),
        "label": validated_df[label_col].apply(clean),
    })
    out["swot_element"] = validated_df[swot_col].apply(clean) if swot_col else ""
    out["Respondent_Type"] = validated_df[type_col].apply(clean) if type_col else ""
    return out[(out["text"] != "") & (out["label"] != "")].reset_index(drop=True)


def _build_pipeline(clf):
    from sklearn.pipeline import Pipeline, FeatureUnion
    from sklearn.feature_extraction.text import TfidfVectorizer
    features = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, strip_accents="unicode")),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, strip_accents="unicode")),
    ])
    return Pipeline([("features", features), ("clf", clf)])


def evaluate_theme_models(train_df, random_state=42):
    """Compare candidate algorithms using stratified k-fold cross-validation.
    Cross-validation (rather than one train/test split) gives a much more
    reliable accuracy estimate on small datasets like this one.
    """
    try:
        from sklearn.model_selection import StratifiedKFold, cross_val_predict
        from sklearn.linear_model import LogisticRegression, SGDClassifier
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.svm import LinearSVC
        from sklearn.metrics import accuracy_score, f1_score
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), f"scikit-learn n'est pas installé. Détail : {e}"

    if train_df.empty:
        return pd.DataFrame(), pd.DataFrame(), "Aucune donnée validée disponible."

    counts = train_df["label"].value_counts()
    n_classes = train_df["label"].nunique()
    if n_classes < 2:
        return pd.DataFrame(), pd.DataFrame(), "Il faut au moins deux thèmes différents dans les données validées."
    if len(train_df) < MIN_TOTAL_TRAINING_EXAMPLES:
        return pd.DataFrame(), pd.DataFrame(), (
            f"Données insuffisantes pour un entraînement fiable : {len(train_df)} réponses validées, "
            f"minimum recommandé {MIN_TOTAL_TRAINING_EXAMPLES}. Continuez à valider des réponses dans "
            f"l'onglet de classification, puis relancez l'entraînement."
        )

    # Cross-validation folds cannot exceed the smallest class size.
    n_splits = max(2, min(5, int(counts.min())))
    if counts.min() < 2:
        thin = counts[counts < 2].index.tolist()
        return pd.DataFrame(), pd.DataFrame(), (
            "Les thèmes suivants n'ont qu'un seul exemple validé, ce qui empêche une évaluation fiable : "
            + ", ".join(thin) + ". Validez au moins 2-3 réponses par thème avant d'entraîner."
        )

    X = train_df["text"].astype(str)
    y = train_df["label"].astype(str)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    algorithms = {
        "TF-IDF + Régression logistique": LogisticRegression(max_iter=2000, class_weight="balanced"),
        "TF-IDF + SVM linéaire": LinearSVC(class_weight="balanced"),
        "TF-IDF + SGD (SVM en ligne)": SGDClassifier(loss="hinge", class_weight="balanced", random_state=random_state),
        "TF-IDF + Naive Bayes": MultinomialNB(),
    }

    summary_rows, all_predictions = [], []
    for name, clf in algorithms.items():
        try:
            model = _build_pipeline(clf)
            preds = cross_val_predict(model, X, y, cv=skf)
            acc = accuracy_score(y, preds)
            f1 = f1_score(y, preds, average="macro", zero_division=0)
            summary_rows.append({
                "Algorithme": name, "Accuracy (validation croisée)": round(acc, 3),
                "Macro F1 (validation croisée)": round(f1, 3),
                "N validé": len(X), "Nb de thèmes": n_classes, "Folds": n_splits,
            })
            for text, true_label, pred_label in zip(X, y, preds):
                all_predictions.append({
                    "Algorithme": name, "Réponse": text, "Thème réel": true_label,
                    "Thème prédit": pred_label, "Correct": true_label == pred_label,
                })
        except Exception as e:
            summary_rows.append({
                "Algorithme": name, "Accuracy (validation croisée)": None, "Macro F1 (validation croisée)": None,
                "N validé": len(X), "Nb de thèmes": n_classes, "Folds": n_splits, "Erreur": str(e),
            })

    results = pd.DataFrame(summary_rows).sort_values(
        ["Macro F1 (validation croisée)", "Accuracy (validation croisée)"], ascending=False, na_position="last"
    )
    return results, pd.DataFrame(all_predictions), ""


def train_final_model(train_df, algorithm_name, random_state=42):
    from sklearn.linear_model import LogisticRegression, SGDClassifier
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.svm import LinearSVC

    algorithms = {
        "TF-IDF + Régression logistique": LogisticRegression(max_iter=2000, class_weight="balanced"),
        "TF-IDF + SVM linéaire": LinearSVC(class_weight="balanced"),
        "TF-IDF + SGD (SVM en ligne)": SGDClassifier(loss="hinge", class_weight="balanced", random_state=random_state),
        "TF-IDF + Naive Bayes": MultinomialNB(),
    }
    clf = algorithms.get(algorithm_name, LinearSVC(class_weight="balanced"))
    model = _build_pipeline(clf)
    model.fit(train_df["text"].astype(str), train_df["label"].astype(str))
    return model


def classify_with_trained_model(answer, model):
    pred = model.predict([answer])[0]
    confidence = None
    try:
        clf = model.named_steps.get("clf")
        if hasattr(clf, "predict_proba"):
            proba = model.predict_proba([answer])[0]
            confidence = round(float(max(proba)) * 100, 1)
        elif hasattr(clf, "decision_function"):
            scores = np.array(model.decision_function([answer])).reshape(-1)
            if len(scores) > 0:
                exp_scores = np.exp(scores - scores.max())
                confidence = round(float(exp_scores.max() / exp_scores.sum()) * 100, 1)
    except Exception:
        confidence = None
    return pred, confidence


# ============================================================
# OPTIONAL EXTERNAL LLM ENGINE (opt-in, isolated, never silent)
# ============================================================

def get_institutional_ai_key():
    key = st.session_state.get("institutional_ai_key", "")
    if key:
        return key
    try:
        key = st.secrets.get("AI_ENGINE_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("AI_ENGINE_API_KEY", "")


def get_institutional_ai_model_name():
    try:
        model_name = st.secrets.get("AI_ENGINE_MODEL", "")
        if model_name:
            return model_name
    except Exception:
        pass
    return os.environ.get("AI_ENGINE_MODEL", "gpt-4o-mini")


def call_institutional_ai_json(messages, temperature=0):
    api_key = get_institutional_ai_key()
    if not api_key:
        raise RuntimeError("Clé du moteur IA manquante")
    payload = {
        "model": get_institutional_ai_model_name(), "messages": messages,
        "temperature": temperature, "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        data = json.loads(response.read().decode("utf-8"))
    return json.loads(data["choices"][0]["message"]["content"])


def classify_with_llm(answer, participant_type, swot_element):
    themes = [clean(t) for t in official_themes_for(participant_type, swot_element, include_autre=True) if clean(t)]
    if not themes:
        return "", 0.0, "", "Aucun thème officiel disponible"
    official_list = "\n".join([f"- {t}" for t in themes])

    system_prompt = """Tu es un expert senior en analyse qualitative institutionnelle universitaire.
Classifie une réponse de focus group USJ dans UN SEUL thème de la liste officielle fournie.
Respecte strictement les noms de thèmes, ne les modifie jamais.
Base-toi sur le sens et l'objet principal de la réponse, pas sur la structure de la phrase.
Si aucun thème ne correspond clairement, choisis Autres/Autre si disponible et indique une confiance faible.
Réponds uniquement en JSON valide : {"theme": "...", "confidence": 0-100, "explanation": "...", "alternatives": ["...", "..."]}"""

    user_prompt = f"Type de participants : {participant_type}\nÉlément SWOT : {swot_element}\n\nThèmes officiels autorisés :\n{official_list}\n\nRéponse à classifier :\n{answer}"

    try:
        result = call_institutional_ai_json([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])
        theme = clean(result.get("theme", ""))
        if theme not in themes:
            fallback = "Autres" if "Autres" in themes else ("Autre" if "Autre" in themes else themes[0])
            return fallback, 25.0, "", "Réponse hors liste officielle ; correction défensive appliquée."
        conf = round(max(0, min(float(result.get("confidence", 0) or 0), 100)), 1)
        explanation = clean(result.get("explanation", "Classification par le moteur IA institutionnel."))
        alts = result.get("alternatives", [])
        alt_txt = " | ".join([clean(x) for x in alts if clean(x) in themes][:3]) if isinstance(alts, list) else ""
        return theme, conf, alt_txt, explanation
    except Exception as e:
        fallback = "Autres" if "Autres" in themes else ("Autre" if "Autre" in themes else themes[0])
        return fallback, 10.0, "", f"Erreur moteur IA / fallback conservateur : {e}"


# ============================================================
# UNIFIED CLASSIFICATION DISPATCH
# ============================================================

def classify_answer(answer, participant_type, swot_element, engine, trained_model=None):
    if engine == ENGINE_TRAINED and trained_model is not None:
        theme, conf = classify_with_trained_model(answer, trained_model)
        return theme, (conf if conf is not None else 0.0), "", "Modèle supervisé entraîné sur vos données validées"
    if engine == ENGINE_LLM:
        return classify_with_llm(answer, participant_type, swot_element)
    return classify_heuristic(answer, participant_type, swot_element)


def build_classification_dataframe(df_scope, engine, trained_model=None):
    rows = []
    for idx, row in df_scope.iterrows():
        swot_element = row.get("swot_element", "")
        if swot_element not in SWOT_ELEMENTS:
            continue
        answer = clean(row.get("Final_Answer", ""))
        if not answer:
            continue
        theme, conf, top3, evidence = classify_answer(
            answer, row.get("Respondent_Type", ""), swot_element, engine, trained_model
        )
        rows.append({
            "row_id": idx, "Respondent_Type": row.get("Respondent_Type", ""), "groupe": row.get("groupe", ""),
            "participants": row.get("participants", ""), "swot_element": swot_element,
            "question": row.get("question", ""), "Final_Answer": answer,
            "AI_Suggested_Theme": theme, "Confidence": conf, "Top_3_Themes": top3, "Evidence": evidence,
            "Validated_Theme": theme, "New_Theme": "",
        })
    return pd.DataFrame(rows)


# ============================================================
# CUSTOM THEMES ADDED BY EXPERTS (auto-saved, reused across rows)
# ============================================================

def _custom_theme_key(participant_type, swot_element):
    return f"{normalize(participant_type)}||{normalize(swot_element)}"


def get_custom_themes(participant_type, swot_element):
    """Themes that experts have typed in as 'Nouveau thème' for this
    participant type / SWOT element combination, in the order they were added.
    Stored in session_state so they are immediately proposed for every
    subsequent row of the same group, without the expert retyping them."""
    store = st.session_state.setdefault("custom_themes", {})
    return store.get(_custom_theme_key(participant_type, swot_element), [])


def register_custom_theme(participant_type, swot_element, theme):
    theme = clean(theme)
    if not theme:
        return
    store = st.session_state.setdefault("custom_themes", {})
    key = _custom_theme_key(participant_type, swot_element)
    existing = store.setdefault(key, [])
    if theme not in existing:
        existing.append(theme)


# ============================================================
# ACADEMIC SYNTHESIS TEXT (rule-based, no external API required)
# ============================================================

SWOT_ACADEMIC_FRAMING = {
    "Forces": "constitue une force structurante clairement mise en évidence par les répondants",
    "Faiblesses": "constitue une faiblesse récurrente qui appelle une action correctrice prioritaire",
    "Opportunités": "représente une opportunité stratégique que l'institution gagnerait à saisir",
    "Menaces": "constitue une menace potentielle dont les effets doivent être anticipés",
}

PRIORITY_LABELS = {
    "Forces": "à consolider",
    "Faiblesses": "à corriger en priorité",
    "Opportunités": "à saisir stratégiquement",
    "Menaces": "à anticiper et atténuer",
}


def extract_top_keywords(answers, top_n=6):
    counter = Counter()
    for answer in answers:
        counter.update(tokenize_for_similarity(answer))
    return [word for word, _ in counter.most_common(top_n)]


def build_academic_synthesis(participant_type, swot_element, theme, groupes, answers):
    """Produce a clear, structured, academically-toned synthesis paragraph.
    This is deliberately rule-based (keyword extraction + templated framing)
    rather than a literal concatenation of answers, so it complements —
    and does not replace — the raw data table."""
    n = len(answers)
    if n == 0:
        return ""

    groupe_list = sorted({clean(g) for g in groupes if clean(g)})
    groupe_str = ", ".join(groupe_list) if groupe_list else participant_type
    framing = SWOT_ACADEMIC_FRAMING.get(swot_element, "présente une pertinence notable")
    keywords = extract_top_keywords(answers)
    keyword_str = ", ".join(keywords) if keywords else "des préoccupations convergentes"

    plural_reponse = "réponses" if n > 1 else "réponse"
    plural_groupe = "sous-groupes" if len(groupe_list) > 1 else "sous-groupe"

    return (
        f"Sur la base de {n} {plural_reponse} recueillie{'s' if n > 1 else ''} auprès des répondants "
        f"de la catégorie « {participant_type} » (issue{'s' if len(groupe_list) > 1 else ''} du "
        f"{plural_groupe} : {groupe_str}), le thème « {theme} » {framing} au sein de l'analyse SWOT. "
        f"L'examen du corpus révèle une convergence des contributions autour des dimensions suivantes : "
        f"{keyword_str}. Cette récurrence traduit une perception partagée qu'il conviendra de documenter "
        f"avec attention dans le cadre de l'élaboration du Plan Stratégique USJ 2032."
    )


def build_theme_synthesis(validated_df):
    if validated_df.empty:
        return pd.DataFrame()
    rows = []
    grouped = validated_df.groupby(["Respondent_Type", "swot_element", "Validated_Theme"], dropna=False)
    for (ptype, swot_element, theme), group in grouped:
        answers = [clean(x) for x in group["Final_Answer"].tolist() if clean(x)]
        groupes = group["groupe"].tolist() if "groupe" in group.columns else []
        rows.append({
            "Type de participants": ptype,
            "Élément SWOT": swot_element,
            "Thème": theme,
            "Sous-groupe(s)": ", ".join(sorted({clean(g) for g in groupes if clean(g)})),
            "Nombre de réponses": len(answers),
            "Synthèse automatique courte": " | ".join(answers[:3]),
            "Synthèse académique": build_academic_synthesis(ptype, swot_element, theme, groupes, answers),
        })
    return pd.DataFrame(rows).sort_values(
        ["Type de participants", "Élément SWOT", "Nombre de réponses"], ascending=[True, True, False]
    )


# ============================================================
# NEW: THEMATIC PARAGRAPH SYNTHESIS PER SWOT ELEMENT
# (separate prose per theme, real quotes as illustrative evidence,
#  filterable by participant type / subgroup — replaces the flat table
#  as the primary view in the Synthèse tab)
# ============================================================

def _select_illustrative_quotes(answers, max_quotes=2, max_len=220):
    """Pick up to max_quotes representative real answers (verbatim, since
    these are the institution's own primary survey data, not third-party
    copyrighted text), shortened only if very long, to illustrate a theme
    without turning the paragraph into a raw data dump."""
    quotes, seen = [], set()
    for a in sorted(answers, key=len, reverse=True):
        a_clean = clean(a)
        key = a_clean.lower()
        if not a_clean or key in seen:
            continue
        seen.add(key)
        if len(a_clean) > max_len:
            a_clean = a_clean[:max_len].rsplit(" ", 1)[0] + "…"
        quotes.append(a_clean)
        if len(quotes) >= max_quotes:
            break
    return quotes


def build_theme_paragraph(participant_label, swot_element, theme, groupes, answers):
    n = len(answers)
    if n == 0:
        return ""
    groupe_list = sorted({clean(g) for g in groupes if clean(g)})
    groupe_str = ", ".join(groupe_list) if groupe_list else participant_label
    framing = SWOT_ACADEMIC_FRAMING.get(swot_element, "présente une pertinence notable")
    keywords = extract_top_keywords(answers)
    keyword_str = ", ".join(keywords) if keywords else "des préoccupations convergentes"
    quotes = _select_illustrative_quotes(answers)
    plural_reponse = "réponses" if n > 1 else "réponse"
    intensity = ("un poids significatif" if n >= 5 else
                 "un poids modéré" if n >= 2 else "une occurrence isolée mais notable")

    paragraph = (
        f"Ce thème {framing}, avec {n} {plural_reponse} recensée{'s' if n > 1 else ''} parmi les "
        f"contributions {('de la catégorie « ' + participant_label + ' »') if participant_label else ''} "
        f"({groupe_str}), ce qui lui confère {intensity} au sein de cet axe de l'analyse SWOT. Les "
        f"contributions convergent notamment autour de : {keyword_str}."
    )
    if quotes:
        quoted = " ; ".join([f"« {q} »" for q in quotes])
        paragraph += f" À titre d'illustration, les répondants s'expriment ainsi : {quoted}."
    return paragraph.strip()


def filter_validated(validated_df, participant_type_filter, groupe_filter):
    scope = validated_df.copy()
    if participant_type_filter and participant_type_filter != "Tous les types confondus":
        scope = scope[scope["Respondent_Type"] == participant_type_filter]
    if groupe_filter and groupe_filter != "Tous les sous-groupes":
        scope = scope[scope["groupe"] == groupe_filter]
    return scope


def build_swot_element_synthesis(validated_df, participant_type_filter, groupe_filter, swot_element):
    """Returns a ranked list of {theme, count, paragraph} dicts for one SWOT
    element, restricted to the requested participant type / subgroup."""
    scope = filter_validated(validated_df, participant_type_filter, groupe_filter)
    scope = scope[scope["swot_element"] == swot_element]
    if scope.empty:
        return [], 0

    participant_label = participant_type_filter if participant_type_filter != "Tous les types confondus" else ""
    grouped = scope.groupby("Validated_Theme")
    ranked_themes = grouped.size().sort_values(ascending=False)

    paragraphs = []
    for rank, (theme, count) in enumerate(ranked_themes.items(), start=1):
        group = grouped.get_group(theme)
        answers = [clean(x) for x in group["Final_Answer"].tolist() if clean(x)]
        groupes = group["groupe"].tolist()
        para = build_theme_paragraph(participant_label, swot_element, theme, groupes, answers)
        paragraphs.append({"theme": theme, "count": int(count), "paragraph": para, "rank": rank})
    return paragraphs, len(scope)


def build_priorities_and_conclusion(validated_df, participant_type_filter, groupe_filter):
    scope = filter_validated(validated_df, participant_type_filter, groupe_filter)
    priorities = {}
    for element in SWOT_ELEMENTS:
        sub = scope[scope["swot_element"] == element]
        top = sub.groupby("Validated_Theme").size().sort_values(ascending=False).head(3)
        priorities[element] = list(top.items())

    total = len(scope)
    label = participant_type_filter if participant_type_filter != "Tous les types confondus" else "l'ensemble des parties prenantes consultées"
    conclusion = (
        f"L'analyse thématique conduite auprès de {label} ({total} contributions validées) met en évidence "
        f"des dynamiques internes et externes structurantes pour la trajectoire du Plan Stratégique USJ 2032. "
        f"Les forces recensées offrent des leviers de consolidation immédiats, tandis que les faiblesses "
        f"identifiées appellent des plans d'action correctifs ciblés. Sur le plan externe, les opportunités "
        f"relevées gagneraient à être intégrées dans la feuille de route stratégique, en parallèle d'une "
        f"vigilance soutenue à l'égard des menaces signalées par les répondants. La priorisation qui suit, "
        f"établie sur la base de la fréquence des occurrences validées par les experts, est proposée comme "
        f"point de départ pour les arbitrages à venir."
    )
    return priorities, conclusion


# ============================================================
# NEW: DYNAMIC SWOT MATRIX VISUAL (HTML/CSS card grid)
# ============================================================

SWOT_QUADRANT_META = {
    "Forces": {"icon": "✓", "color": USJ_BLUE, "bg": "#EAF2FB", "subtitle": "Atouts internes à consolider"},
    "Faiblesses": {"icon": "!", "color": USJ_RED, "bg": "#FDEDEE", "subtitle": "Points internes à améliorer"},
    "Opportunités": {"icon": "↗", "color": "#1E7A46", "bg": "#EAF7EF", "subtitle": "Leviers externes à saisir"},
    "Menaces": {"icon": "⚠", "color": "#B23A22", "bg": "#FDEFE9", "subtitle": "Risques externes à anticiper"},
}


def _swot_quadrant_html(element, scope, top_n=5):
    meta = SWOT_QUADRANT_META[element]
    sub = scope[scope["swot_element"] == element]
    theme_counts = sub.groupby("Validated_Theme").size().sort_values(ascending=False).head(top_n)
    items_html = ""
    for i, (theme, count) in enumerate(theme_counts.items(), start=1):
        items_html += f"""
        <div class="swot-item">
            <span class="swot-item-num" style="background:{meta['color']}">{i}</span>
            <span class="swot-item-text">{esc(theme)}<span class="swot-item-count">({count})</span></span>
        </div>"""
    if not items_html:
        items_html = '<div class="swot-item-empty">Aucune donnée validée pour ce filtre</div>'
    return f"""
    <div class="swot-quadrant" style="background:{meta['bg']}; border-top:5px solid {meta['color']}">
        <div class="swot-quadrant-header">
            <span class="swot-icon" style="background:{meta['color']}">{meta['icon']}</span>
            <div>
                <div class="swot-title" style="color:{meta['color']}">{element.upper()}</div>
                <div class="swot-subtitle">{meta['subtitle']}</div>
            </div>
            <span class="swot-badge" style="color:{meta['color']}">{len(sub)} éléments</span>
        </div>
        <div class="swot-items">{items_html}</div>
    </div>"""


def render_swot_matrix_html(validated_df, participant_type_filter, groupe_filter, top_n=5):
    scope = filter_validated(validated_df, participant_type_filter, groupe_filter)
    cards = {element: _swot_quadrant_html(element, scope, top_n) for element in SWOT_ELEMENTS}

    html_block(f"""
    <style>
    .swot-matrix-wrap {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin: 10px 0 26px 0; }}
    .swot-quadrant {{ border-radius:18px; padding:20px 22px; box-shadow:0 10px 26px rgba(0,0,0,0.06); }}
    .swot-quadrant-header {{ display:flex; align-items:center; gap:12px; margin-bottom:14px; }}
    .swot-icon {{ width:34px; height:34px; border-radius:10px; color:white; display:flex; align-items:center;
                  justify-content:center; font-weight:900; font-size:18px; flex-shrink:0; }}
    .swot-title {{ font-weight:900; font-size:17px; letter-spacing:0.5px; }}
    .swot-subtitle {{ font-size:12px; color:#64748B; font-weight:600; }}
    .swot-badge {{ margin-left:auto; font-size:12px; font-weight:800; background:white; padding:4px 10px;
                   border-radius:20px; }}
    .swot-item {{ display:flex; align-items:flex-start; gap:10px; background:white; border-radius:12px;
                  padding:10px 14px; margin-bottom:8px; box-shadow:0 2px 6px rgba(0,0,0,0.04); }}
    .swot-item-num {{ width:20px; height:20px; border-radius:50%; color:white; font-size:11px; font-weight:800;
                       display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:1px; }}
    .swot-item-text {{ font-size:13.5px; font-weight:600; color:{USJ_TEXT}; }}
    .swot-item-count {{ color:#94A3B8; font-weight:700; margin-left:6px; font-size:12px; }}
    .swot-item-empty {{ font-size:13px; color:#94A3B8; font-style:italic; padding:6px 0; }}
    @media (max-width: 900px) {{ .swot-matrix-wrap {{ grid-template-columns: 1fr; }} }}
    </style>
    <div class="swot-matrix-wrap">
        {cards['Forces']}{cards['Faiblesses']}{cards['Opportunités']}{cards['Menaces']}
    </div>
    """)


# ============================================================
# NEW: DOWNLOADABLE PDF REPORT (post-validation synthesis)
# ============================================================

def _pdf_styles():
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib import colors
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="USJTitle", fontSize=20, leading=24,
                               textColor=colors.HexColor(USJ_BLUE), fontName="Helvetica-Bold", spaceAfter=6))
    styles.add(ParagraphStyle(name="USJSubtitle", fontSize=12, leading=16,
                               textColor=colors.HexColor("#64748B"), spaceAfter=14))
    styles.add(ParagraphStyle(name="USJElement", fontSize=15, leading=18,
                               textColor=colors.white, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="USJTheme", fontSize=11.5, leading=15, textColor=colors.HexColor(USJ_BLUE),
                               fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=2))
    styles.add(ParagraphStyle(name="USJBody", fontSize=10, leading=14.5, textColor=colors.HexColor(USJ_TEXT),
                               alignment=TA_JUSTIFY, spaceAfter=8))
    styles.add(ParagraphStyle(name="USJConclusion", fontSize=10.5, leading=15,
                               textColor=colors.HexColor(USJ_TEXT), alignment=TA_JUSTIFY))
    return styles


def generate_pdf_report(validated_df, participant_type_filter, groupe_filter, report_label):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    except Exception as e:
        return None, f"reportlab n'est pas installé sur ce serveur : {e}"

    styles = _pdf_styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    story = []

    story.append(Paragraph(APP_TITLE, styles["USJTitle"]))
    story.append(Paragraph(f"Rapport de synthèse thématique — {report_label}", styles["USJSubtitle"]))
    story.append(Spacer(1, 6))

    element_colors = {"Forces": USJ_BLUE, "Faiblesses": USJ_RED, "Opportunités": "#1E7A46", "Menaces": "#B23A22"}

    for element in SWOT_ELEMENTS:
        paragraphs, n = build_swot_element_synthesis(validated_df, participant_type_filter, groupe_filter, element)
        header_tbl = Table([[Paragraph(f"{element.upper()} ({n} réponses)", styles["USJElement"])]], colWidths=[17 * cm])
        header_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(element_colors[element])),
            ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(header_tbl)
        story.append(Spacer(1, 8))
        if not paragraphs:
            story.append(Paragraph("Aucune donnée validée pour cet élément avec les filtres sélectionnés.", styles["USJBody"]))
        for item in paragraphs:
            story.append(Paragraph(f"{item['rank']}. {esc(item['theme'])} ({item['count']} réponses)", styles["USJTheme"]))
            story.append(Paragraph(esc(item["paragraph"]).replace("&#x27;", "'"), styles["USJBody"]))
        story.append(Spacer(1, 10))

    story.append(PageBreak())
    story.append(Paragraph("Priorités par élément SWOT", styles["USJTitle"]))
    priorities, conclusion = build_priorities_and_conclusion(validated_df, participant_type_filter, groupe_filter)
    for element in SWOT_ELEMENTS:
        story.append(Paragraph(element, styles["USJTheme"]))
        items = priorities.get(element, [])
        if items:
            for i, (theme, count) in enumerate(items, start=1):
                story.append(Paragraph(
                    f"{i}. {esc(theme)} — {count} occurrences validées ({PRIORITY_LABELS.get(element, '')})",
                    styles["USJBody"]))
        else:
            story.append(Paragraph("Aucune priorité identifiable pour ce filtre.", styles["USJBody"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Conclusion", styles["USJTitle"]))
    story.append(Paragraph(esc(conclusion), styles["USJConclusion"]))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue(), ""


# ============================================================
# STREAMLIT UI
# ============================================================

def _resolve_validated_theme(selected, new_theme):
    new_theme = clean(new_theme)
    if new_theme:
        return new_theme
    if selected == "Autre (nouveau thème)":
        return ""
    return selected


def render_mapping_validation(classified_df):
    if classified_df.empty:
        st.warning("Aucune réponse SWOT à classifier.")
        return classified_df

    st.markdown("### Validation experte des classifications")
    st.caption("Groupé par type de participant et élément SWOT, pour que la liste de thèmes proposée "
               "reste toujours la bonne. Triez : les groupes avec le plus de réponses à faible confiance "
               "apparaissent en premier et sont ouverts par défaut. Tout nouveau thème saisi dans la colonne "
               "« Nouveau thème » est automatiquement enregistré et proposé dans la liste déroulante "
               "« Thème validé » pour toutes les réponses suivantes du même groupe.")

    group_order = (
        classified_df.groupby(["Respondent_Type", "swot_element"])["Confidence"]
        .mean().sort_values().index.tolist()
    )

    validated_rows = []
    for ptype, swot_element in group_order:
        subset = classified_df[
            (classified_df["Respondent_Type"] == ptype) & (classified_df["swot_element"] == swot_element)
        ].sort_values("Confidence", ascending=True)
        if subset.empty:
            continue

        themes = official_themes_for(ptype, swot_element, include_autre=False)
        custom_themes = get_custom_themes(ptype, swot_element)
        theme_options = themes + [t for t in custom_themes if t not in themes] + ["Autre (nouveau thème)"]
        low_conf_count = int((subset["Confidence"] < 50).sum())

        header = f"{ptype} · {swot_element} — {len(subset)} réponses"
        if low_conf_count:
            header += f" · 🔴 {low_conf_count} à valider en priorité"
        if custom_themes:
            header += f" · ➕ {len(custom_themes)} thème(s) ajouté(s) par les experts"

        with st.expander(header, expanded=(low_conf_count > 0)):
            edit_df = subset[["row_id", "groupe", "Final_Answer", "Confidence", "AI_Suggested_Theme"]].copy()
            edit_df["Thème validé"] = edit_df["AI_Suggested_Theme"]
            edit_df["Nouveau thème"] = ""
            edit_df = edit_df.rename(columns={
                "groupe": "Sous-groupe", "Final_Answer": "Réponse", "Confidence": "Confiance %",
                "AI_Suggested_Theme": "Proposé (IA)",
            }).set_index("row_id")

            edited = st.data_editor(
                edit_df,
                key=f"editor_{safe_filename(ptype)}_{safe_filename(swot_element)}",
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Sous-groupe": st.column_config.TextColumn(disabled=True, width="small"),
                    "Réponse": st.column_config.TextColumn(disabled=True, width="large"),
                    "Confiance %": st.column_config.NumberColumn(disabled=True, width="small", format="%.1f"),
                    "Proposé (IA)": st.column_config.TextColumn(disabled=True, width="medium"),
                    "Thème validé": st.column_config.SelectboxColumn(options=theme_options, required=True, width="medium"),
                    "Nouveau thème": st.column_config.TextColumn(
                        width="medium", help="Un thème saisi ici est automatiquement enregistré et "
                        "apparaîtra dans la liste déroulante « Thème validé » pour les réponses suivantes "
                        "de ce même groupe."
                    ),
                },
            )

            for row_id, edited_row in edited.iterrows():
                original = subset[subset["row_id"] == row_id]
                if original.empty:
                    continue
                out = original.iloc[0].to_dict()
                new_theme_input = clean(edited_row["Nouveau thème"])
                final_theme = _resolve_validated_theme(edited_row["Thème validé"], new_theme_input)
                out["Validated_Theme"] = final_theme if final_theme else edited_row["Thème validé"]
                out["New_Theme"] = new_theme_input
                if new_theme_input:
                    register_custom_theme(ptype, swot_element, new_theme_input)
                validated_rows.append(out)

    return pd.DataFrame(validated_rows)


def render_engine_selector(df_scope):
    st.markdown("""
    <div class="ai-card">
        <h3>Moteur de classification actif</h3>
        <p>Commencez avec l'heuristique pour obtenir des suggestions de départ. Validez des réponses dans
        l'onglet suivant, puis entraînez le modèle supervisé : c'est lui qui donnera une précision réelle
        et mesurable, calculée sur vos propres données par validation croisée.</p>
    </div>
    """, unsafe_allow_html=True)

    trained_model = st.session_state.get("trained_model")
    trained_acc = st.session_state.get("trained_model_accuracy")

    options = [ENGINE_HEURISTIC]
    if trained_model is not None:
        label = f"{ENGINE_TRAINED} (précision validée : {trained_acc}%)" if trained_acc is not None else ENGINE_TRAINED
        options.append(label)
    else:
        options.append(f"{ENGINE_TRAINED} (pas encore entraîné - voir onglet 2)")
    options.append(ENGINE_LLM)

    choice = st.radio("Choisir le moteur", options, key="engine_choice_radio")
    if choice.startswith(ENGINE_HEURISTIC):
        engine = ENGINE_HEURISTIC
    elif choice.startswith(ENGINE_TRAINED):
        engine = ENGINE_TRAINED
        if trained_model is None:
            st.markdown('<div class="ai-warning">Aucun modèle entraîné pour le moment. Rendez-vous dans l\'onglet '
                        '« 2. Entraîner le modèle » après avoir validé quelques réponses.</div>', unsafe_allow_html=True)
    else:
        engine = ENGINE_LLM
        with st.expander("Configuration de l'IA institutionnelle (API externe)", expanded=True):
            st.markdown('<div class="ai-danger">Ce moteur envoie le texte des réponses à une API externe '
                        '(OpenAI). N\'activez ce moteur que si cela est acceptable pour la confidentialité '
                        'de vos données.</div>', unsafe_allow_html=True)
            api_key_input = st.text_input("Clé API", value="", type="password", key="institutional_ai_key_input")
            if api_key_input:
                st.session_state["institutional_ai_key"] = api_key_input
            if get_institutional_ai_key():
                st.success("Clé API configurée.")
            else:
                st.warning("Aucune clé API configurée : ce moteur renverra un résultat de repli conservateur.")

    st.session_state["active_engine"] = engine
    return engine


def render_training_tab(df_scope):
    st.subheader("2. Entraîner le modèle supervisé sur vos données validées")
    st.markdown("""
    <div class="ai-info-box">
        C'est ici que la précision réelle se construit. Le modèle apprend directement de vos réponses
        validées dans l'onglet 1 — pas de règles écrites à la main. La précision affichée est mesurée
        par validation croisée : les données sont divisées en plusieurs groupes, le modèle s'entraîne
        sur certains et est testé sur les autres, plusieurs fois, pour donner une estimation fiable
        plutôt qu'optimiste.
    </div>
    """, unsafe_allow_html=True)

    validated_df = st.session_state.get("validated_mapping_df", pd.DataFrame())

    st.markdown("#### Source des données d'entraînement")
    upload_extra = st.file_uploader(
        "Optionnel : ajouter un fichier de réponses déjà validées (Excel ou CSV, colonnes Final_Answer et Validated_Theme)",
        type=["xlsx", "csv"], key="extra_training_upload"
    )
    extra_df = pd.DataFrame()
    if upload_extra is not None:
        try:
            extra_df = pd.read_excel(upload_extra) if upload_extra.name.lower().endswith(("xlsx", "xls")) else pd.read_csv(upload_extra)
        except Exception as e:
            st.error("Impossible de lire ce fichier.")
            st.exception(e)

    combined = pd.concat([validated_df, extra_df], ignore_index=True) if not extra_df.empty else validated_df
    train_df = prepare_training_dataset(combined)

    if train_df.empty:
        st.markdown('<div class="ai-warning">Aucune donnée validée disponible pour l\'instant. Allez dans '
                    'l\'onglet 1, classifiez et validez quelques réponses, puis revenez ici.</div>', unsafe_allow_html=True)
        return

    st.markdown("#### Aperçu des données d'entraînement")
    st.caption("Ce tableau se met à jour automatiquement : tout nouveau thème ajouté par un expert dans "
               "l'onglet 1 apparaît ici comme une nouvelle ligne dès qu'au moins une réponse lui est validée.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Réponses validées", len(train_df))
    c2.metric("Thèmes distincts", train_df["label"].nunique())
    c3.metric("Min. requis", MIN_TOTAL_TRAINING_EXAMPLES)

    counts = train_df["label"].value_counts().reset_index()
    counts.columns = ["Thème", "Nombre d'exemples validés"]
    st.dataframe(
        counts,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Thème": st.column_config.TextColumn(width="large"),
            "Nombre d'exemples validés": st.column_config.NumberColumn(width="small"),
        },
    )
    thin_themes = counts[counts["Nombre d'exemples validés"] < MIN_EXAMPLES_PER_THEME]
    if not thin_themes.empty:
        st.caption(f"Thèmes avec moins de {MIN_EXAMPLES_PER_THEME} exemples validés (à renforcer en priorité) : "
                   + ", ".join(thin_themes["Thème"].tolist()))

    if st.button("Lancer l'entraînement et l'évaluation", key="run_training"):
        with st.spinner("Entraînement et validation croisée en cours..."):
            results_df, predictions_df, error = evaluate_theme_models(train_df)
        st.session_state["training_results_df"] = results_df
        st.session_state["training_predictions_df"] = predictions_df
        st.session_state["training_error"] = error
        st.session_state["training_data_snapshot"] = train_df

    results_df = st.session_state.get("training_results_df", pd.DataFrame())
    error = st.session_state.get("training_error", "")

    if error:
        st.markdown(f'<div class="ai-warning">{esc(error)}</div>', unsafe_allow_html=True)
        return

    if not results_df.empty:
        st.markdown("#### Résultats — précision réelle par algorithme (validation croisée)")
        st.dataframe(results_df, use_container_width=True)

        best_row = results_df.iloc[0]
        best_algo = best_row["Algorithme"]
        best_acc = best_row["Accuracy (validation croisée)"]

        predictions_df = st.session_state.get("training_predictions_df", pd.DataFrame())
        if not predictions_df.empty:
            errors_df = predictions_df[(predictions_df["Algorithme"] == best_algo) & (~predictions_df["Correct"])]
            if not errors_df.empty:
                with st.expander(f"Voir les erreurs de classification du meilleur modèle ({len(errors_df)} cas)"):
                    st.dataframe(errors_df[["Réponse", "Thème réel", "Thème prédit"]], use_container_width=True)

        st.markdown(f"""
        <div class="ai-info-box">
            Meilleur algorithme : <b>{esc(best_algo)}</b> — précision estimée : <b>{round(best_acc * 100, 1)}%</b>
            sur {len(st.session_state.get("training_data_snapshot", pd.DataFrame()))} réponses validées.
            Cette précision reflète vos données réelles : plus vous validez de réponses (en particulier pour
            les thèmes peu représentés ci-dessus), plus ce chiffre montera lors du prochain entraînement.
        </div>
        """, unsafe_allow_html=True)

        chosen_algo = st.selectbox("Algorithme à activer", options=results_df["Algorithme"].tolist(),
                                    index=0, key="chosen_training_algo")
        if st.button("Activer ce modèle pour la classification", key="activate_trained_model"):
            snapshot = st.session_state.get("training_data_snapshot", train_df)
            model = train_final_model(snapshot, chosen_algo)
            st.session_state["trained_model"] = model
            chosen_acc = results_df[results_df["Algorithme"] == chosen_algo]["Accuracy (validation croisée)"].iloc[0]
            st.session_state["trained_model_accuracy"] = round(chosen_acc * 100, 1)
            st.success(f"Modèle activé : {chosen_algo} (précision validée : {round(chosen_acc * 100, 1)}%). "
                       f"Retournez à l'onglet 1 et sélectionnez « Modèle supervisé entraîné » pour l'utiliser.")

            import pickle
            buf = BytesIO()
            pickle.dump(model, buf)
            st.download_button("Télécharger ce modèle entraîné (.pkl)", data=buf.getvalue(),
                                file_name=f"modele_theme_{safe_filename(chosen_algo)}.pkl",
                                mime="application/octet-stream")

    st.markdown("#### Réutiliser un modèle déjà entraîné")
    model_upload = st.file_uploader("Charger un fichier de modèle (.pkl)", type=["pkl"], key="model_pkl_upload")
    if model_upload is not None:
        import pickle
        try:
            loaded_model = pickle.load(model_upload)
            st.session_state["trained_model"] = loaded_model
            st.session_state["trained_model_accuracy"] = None
            st.success("Modèle chargé et activé. Sélectionnez « Modèle supervisé entraîné » dans l'onglet 1.")
        except Exception as e:
            st.error("Impossible de charger ce fichier de modèle.")
            st.exception(e)


def render_synthesis_tab():
    st.subheader("4. Synthèse thématique académique")
    st.caption("Analyse thématique rédigée par élément SWOT, avec extraits réels des réponses validées "
               "par les experts. Utilisez les filtres pour cibler un type de participants et/ou un "
               "sous-groupe, ou conservez la vue globale pour une synthèse consolidée.")
    validated_df = st.session_state.get("validated_mapping_df", pd.DataFrame())
    if validated_df.empty:
        st.warning("Veuillez d'abord produire et valider le mapping SWOT dans l'onglet 1.")
        return

    col_a, col_b = st.columns(2)
    type_options = ["Tous les types confondus"] + sorted(validated_df["Respondent_Type"].dropna().unique().tolist())
    selected_type = col_a.selectbox("Type de participants", type_options, key="synthesis_type_filter")

    if selected_type == "Tous les types confondus":
        groupe_pool = validated_df["groupe"].dropna().unique().tolist()
    else:
        groupe_pool = validated_df[validated_df["Respondent_Type"] == selected_type]["groupe"].dropna().unique().tolist()
    groupe_options = ["Tous les sous-groupes"] + sorted(groupe_pool)
    selected_groupe = col_b.selectbox("Sous-groupe", groupe_options, key="synthesis_groupe_filter")

    st.markdown("#### Matrice SWOT dynamique")
    render_swot_matrix_html(validated_df, selected_type, selected_groupe)

    st.markdown("#### Analyse thématique par élément SWOT")
    for element in SWOT_ELEMENTS:
        paragraphs, n = build_swot_element_synthesis(validated_df, selected_type, selected_groupe, element)
        meta = SWOT_QUADRANT_META[element]
        st.markdown(
            f'<h5 style="color:{meta["color"]};margin-top:22px;">{element} <span style="color:#94A3B8;'
            f'font-size:13px;font-weight:600;">({n} réponses)</span></h5>', unsafe_allow_html=True
        )
        if not paragraphs:
            st.caption("Aucune donnée validée pour ce filtre.")
            continue
        for item in paragraphs:
            st.markdown(
                f'<div class="ai-card"><b style="color:{USJ_BLUE};">{item["rank"]}. {esc(item["theme"])}'
                f' <span style="color:#94A3B8;font-weight:600;font-size:12.5px;">({item["count"]} réponses)</span>'
                f'</b><p style="margin-top:8px;line-height:1.55;">{item["paragraph"]}</p></div>',
                unsafe_allow_html=True,
            )

    st.markdown("#### Priorités et conclusion")
    priorities, conclusion = build_priorities_and_conclusion(validated_df, selected_type, selected_groupe)
    for element in SWOT_ELEMENTS:
        items = priorities.get(element, [])
        if items:
            st.markdown(f"**{element}** : " + " · ".join([f"{t} ({c})" for t, c in items]))
    st.markdown(f'<div class="ai-info-box">{esc(conclusion)}</div>', unsafe_allow_html=True)

    st.markdown("#### Rapport PDF téléchargeable")
    report_scope = st.radio(
        "Portée du rapport",
        ["Vue actuelle (filtres ci-dessus)",
         "Un rapport par type de participants (tous sous-groupes fusionnés)",
         "Un rapport par sous-groupe"],
        key="pdf_report_scope",
    )

    def _offer_pdf(ptype_filter, groupe_filter, label, key_suffix):
        pdf_bytes, error = generate_pdf_report(validated_df, ptype_filter, groupe_filter, label)
        if error:
            st.markdown(f'<div class="ai-warning">{esc(error)}</div>', unsafe_allow_html=True)
            return
        st.download_button(f"Télécharger le rapport PDF — {label}", data=pdf_bytes,
                            file_name=f"rapport_{safe_filename(label)}.pdf", mime="application/pdf",
                            key=f"pdf_dl_{key_suffix}")

    if report_scope.startswith("Vue actuelle"):
        if st.button("Générer le rapport PDF de la vue actuelle", key="gen_pdf_current"):
            label = f"{selected_type} - {selected_groupe}" if selected_groupe != "Tous les sous-groupes" else selected_type
            _offer_pdf(selected_type, selected_groupe, label, "current")
    elif report_scope.startswith("Un rapport par type"):
        if st.button("Générer un rapport PDF par type de participants", key="gen_pdf_by_type"):
            for ptype in sorted(validated_df["Respondent_Type"].dropna().unique().tolist()):
                _offer_pdf(ptype, "Tous les sous-groupes", ptype, safe_filename(ptype))
    else:
        if st.button("Générer un rapport PDF par sous-groupe", key="gen_pdf_by_groupe"):
            for _, row in validated_df[["Respondent_Type", "groupe"]].drop_duplicates().iterrows():
                label = f"{row['Respondent_Type']} - {row['groupe']}"
                _offer_pdf(row["Respondent_Type"], row["groupe"], label, safe_filename(label))

    st.markdown("#### Tableau de synthèse complet (export)")
    st.caption("Toujours disponible en complément des paragraphes ci-dessus, pour la traçabilité et le travail en Excel.")
    synthesis_df = build_theme_synthesis(validated_df)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        synthesis_df.to_excel(writer, index=False, sheet_name="Synthese")
    output.seek(0)
    st.download_button("Télécharger le tableau de synthèse (Excel)", data=output.getvalue(),
                        file_name="synthese_theme_SWOT.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def ai_platform_page(df):
    html_block(APP_CSS)
    html_block("""
    <div class="ai-hero">
        <h2>Plateforme IA supervisée - Analyse thématique stratégique</h2>
        <p>Classification, validation experte, entraînement d'un modèle supervisé sur vos données,
        détection de doublons et synthèse par thème.</p>
    </div>
    """)

    df_scope = df.copy()
    swot_df = df_scope[df_scope["swot_element"].isin(SWOT_ELEMENTS)]

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="ai-kpi"><div class="ai-kpi-number">{len(df_scope)}</div><div class="ai-kpi-label">Réponses importées</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="ai-kpi"><div class="ai-kpi-number">{len(swot_df)}</div><div class="ai-kpi-label">Réponses SWOT</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="ai-kpi"><div class="ai-kpi-number">{df_scope["Respondent_Type"].nunique()}</div><div class="ai-kpi-label">Types de participants</div></div>', unsafe_allow_html=True)
    trained_acc = st.session_state.get("trained_model_accuracy")
    c4.markdown(f'<div class="ai-kpi"><div class="ai-kpi-number">{trained_acc if trained_acc is not None else "—"}%</div><div class="ai-kpi-label">Précision du modèle entraîné</div></div>', unsafe_allow_html=True)

    tab_mapping, tab_training, tab_duplicates, tab_synthesis = st.tabs([
        "1. Classification et validation", "2. Entraîner le modèle", "3. Doublons", "4. Synthèse"
    ])

    with tab_mapping:
        st.subheader("1. Classification et validation experte")
        engine = render_engine_selector(df_scope)
        trained_model = st.session_state.get("trained_model") if engine == ENGINE_TRAINED else None

        if engine == ENGINE_TRAINED and trained_model is None:
            st.stop()

        if st.button("Classifier les réponses SWOT", key="run_mapping"):
            with st.spinner("Classification en cours..."):
                st.session_state["classified_df"] = build_classification_dataframe(df_scope, engine, trained_model)

        classified_df = st.session_state.get("classified_df", pd.DataFrame())
        if not classified_df.empty:
            preview_cols = ["Respondent_Type", "groupe", "swot_element", "Final_Answer", "AI_Suggested_Theme", "Confidence"]
            st.dataframe(classified_df[preview_cols], use_container_width=True)

            validated_df = render_mapping_validation(classified_df)
            st.session_state["validated_mapping_df"] = validated_df

            if not validated_df.empty:
                export_cols = ["Respondent_Type", "groupe", "participants", "swot_element", "question",
                                "Final_Answer", "AI_Suggested_Theme", "Confidence", "Validated_Theme", "New_Theme"]
                export_df = validated_df[[c for c in export_cols if c in validated_df.columns]].copy()
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    export_df.to_excel(writer, index=False, sheet_name="Mapping valide")
                output.seek(0)
                st.download_button("Télécharger le mapping validé", data=output.getvalue(),
                                    file_name="mapping_SWOT_valide.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.caption("Cliquez sur « Classifier les réponses SWOT » pour lancer la classification.")

    with tab_training:
        render_training_tab(df_scope)

    with tab_duplicates:
        st.subheader("3. Détection stricte des doublons")
        st.caption("Règle stricte : même élément SWOT + même sujet central. Une structure grammaticale "
                   "similaire avec un sujet différent n'est pas retenue.")
        if st.button("Détecter les doublons", key="detect_duplicates"):
            st.session_state["duplicates_df"] = detect_duplicate_pairs(df_scope)
        dup_df = st.session_state.get("duplicates_df", pd.DataFrame())
        if not dup_df.empty:
            st.dataframe(dup_df, use_container_width=True)
            st.download_button("Télécharger les doublons détectés", data=dup_df.to_csv(index=False).encode("utf-8-sig"),
                                file_name="doublons_detectes.csv", mime="text/csv")
        else:
            st.caption("Aucun doublon affiché pour le moment.")

    with tab_synthesis:
        render_synthesis_tab()


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="collapsed")
    html_block(APP_CSS)
    html_block(f"""
    <style>
    .usj-dashboard-header {{
        background: linear-gradient(135deg, #001F5B 0%, #1F3C88 70%, #8B1538 100%);
        border-radius: 22px; padding: 28px 34px; margin-bottom: 24px;
        box-shadow: 0 14px 34px rgba(0,31,91,0.20);
    }}
    .usj-dashboard-header h1 {{ margin: 0; color: white !important; font-size: 36px; font-weight: 900; }}
    .usj-dashboard-header h3 {{ margin: 8px 0 0 0; color: #EAF2F8 !important; font-weight: 800; font-size: 20px; }}
    .usj-step-card {{
        background: #ffffff; border: 1px solid #D0D6E0; border-radius: 16px; padding: 18px 20px;
        margin: 14px 0 18px 0; box-shadow: 0 8px 22px rgba(0,0,0,0.045);
    }}
    .usj-status-box {{
        background: #F0F7FF; border: 1px solid #CFE4FF; border-left: 6px solid {USJ_BLUE}; border-radius: 14px;
        padding: 14px 18px; margin: 10px 0 18px 0; color: {USJ_TEXT}; font-weight: 800;
    }}
    </style>
    <div class="usj-dashboard-header">
        <h1>{APP_TITLE}</h1>
        <h3>Plateforme IA supervisée - Classification, doublons et synthèse</h3>
    </div>
    """)

    html_block("""
    <div class="usj-step-card">
        <div class="usj-step-title" style="color:#001F5B;font-size:19px;font-weight:900;">Uploader le fichier Excel corrigé</div>
        <div style="color:#667085;font-size:14px;">Le fichier sera utilisé pour la classification, la validation, les doublons et la synthèse.</div>
    </div>
    """)

    uploaded_file = st.file_uploader("Uploader le fichier Excel corrigé", type=["xlsx", "xls"], key="main_excel_upload")
    if uploaded_file is None:
        st.info(f"Veuillez uploader le fichier Excel contenant la feuille : {SHEET_NAME}")
        st.stop()

    df = read_corrected_excel(uploaded_file)
    html_block(f"""
    <div class="usj-status-box">
        Fichier chargé avec succès : {len(df)} réponses, {df["Respondent_Type"].nunique()} types de participants,
        {df["groupe"].nunique()} sous-groupes.
    </div>
    """)

    ai_platform_page(df)


if __name__ == "__main__":
    main()
