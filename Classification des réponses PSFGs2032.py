"""
PLAN STRATÉGIQUE USJ 2032 - Plateforme IA supervisée d'analyse thématique
==========================================================================
Cette version corrige un audit de code portant sur trois points :

1. CODE MORT SUPPRIMÉ
   L'ancien "moteur heuristique pur" (classify_heuristic / heuristic_score_candidates /
   heuristic_confidence) n'était plus jamais appelé par le dispatcher de classification
   (classify_answer) : toute réponse non traitée par le modèle entraîné passait déjà par
   le moteur sémantique institutionnel. Ce code mort a été supprimé.

2. MOTEUR IA EXTERNE (LLM) SUPPRIMÉ
   Le moteur "IA institutionnelle" (appel à l'API OpenAI) n'était jamais câblé dans
   l'interface (ENGINE_LLM n'apparaissait dans aucune option du sélecteur, et
   classify_answer ne l'appelait jamais). Du code mort qui contredit la documentation
   utilisateur du projet ("aucune réponse participant n'est transmise à un service IA
   externe") est un risque : quelqu'un pourrait le réactiver plus tard sans revoir cet
   engagement de confidentialité. Il a donc été retiré entièrement. Architecture actuelle :
   uniquement deux moteurs, tous deux 100% locaux.

   Architecture de classification (2 moteurs, clairement séparés) :
     1. MOTEUR SÉMANTIQUE INSTITUTIONNEL (démarrage à froid, aucune donnée requise)
        Taxonomie officielle + ontologie de domaine + embeddings locaux (si le modèle
        sentence-transformers est installé sur le serveur), avec repli sur TF-IDF sinon.
        Précision plafonnée par nature : ce moteur ne "comprend" pas le texte comme un
        modèle entraîné sur vos propres données, il reconnaît des motifs et de la
        similarité sémantique générique. Utile pour démarrer, pas pour la précision finale.
     2. MODÈLE SUPERVISÉ ENTRAÎNÉ (recommandé pour la précision réelle)
        TF-IDF + Régression logistique / SVM linéaire / SGD / Naive Bayes, entraîné sur les
        réponses que vous avez validées dans l'onglet de validation experte. C'est le seul
        moyen d'obtenir une précision mesurable par validation croisée sur vos propres
        données plutôt qu'une estimation. Le modèle peut être téléchargé et réutilisé.

3. BUG DE CONFIANCE CORRIGÉ POUR LA CLASSIFICATION BINAIRE
   Pour un modèle SVM linéaire (ou SGD) entraîné sur exactement 2 thèmes,
   `decision_function` renvoie un score signé unique (distance à l'hyperplan), pas un
   score par classe. L'ancien code appliquait un softmax multi-classes sur ce score
   unique, ce qui renvoyait systématiquement 100% de confiance quel que soit le cas réel.
   Corrigé via une transformation logistique (sigmoïde) du score de marge — voir
   `classify_with_trained_model`. Il s'agit toujours d'une approximation non calibrée
   (pas une probabilité au sens statistique du terme), ce qui est maintenant documenté
   explicitement dans le code et dans l'interface.

Par ailleurs, le score de pertinence produit par le moteur sémantique institutionnel
(non entraîné) est désormais étiqueté dans l'interface comme un "score de pertinence
heuristique, non calibré", et non plus comme une "confiance %", afin de ne pas laisser
croire à une précision statistique qu'il n'a pas. Seul le score du modèle supervisé,
mesuré par validation croisée, est présenté comme une confiance/précision au sens
statistique.

4. MODÈLE SUPERVISÉ ORGANISÉ PAR GROUPE D'ENTRAÎNEMENT (et non plus un modèle unique)
   Avec 312 réponses SWOT réparties sur 5 types de participants x 4 éléments SWOT, un
   unique modèle "global" diluerait ses données d'entraînement sur ~100 combinaisons
   distinctes de thèmes officiels, la plupart avec 1-2 exemples validés : statistiquement
   inexploitable. La taxonomie officielle (THEME_TAXONOMY) montre cependant que certains
   types de participants partagent EXACTEMENT la même liste de thèmes officiels pour un
   même élément SWOT. Regrouper l'entraînement uniquement là où la liste de thèmes est
   identique est donc une mutualisation valide, pas une approximation :
     - Interne (Forces/Faiblesses), 13 thèmes communs : PSG + Directeurs + Enseignants
     - Externe (Opportunités/Menaces), 5 thèmes communs : PSG + Anciens + Enseignants
     - Externe (Opportunités/Menaces), 5 thèmes communs : Directeurs + Étudiants
   Les thèmes internes d'Anciens (8 thèmes) et d'Étudiants (12 thèmes) ne sont partagés
   avec aucun autre type : ces deux combinaisons restent sur le moteur sémantique tant
   qu'un volume suffisant de données validées n'est pas atteint indépendamment pour
   chacune. Voir TRAINING_POOLS, get_training_group_key et resolve_effective_engine.
   Un modèle entraîné est donc désormais un dictionnaire {groupe: modèle}, pas un objet
   unique — et si le moteur "modèle entraîné" est sélectionné pour une combinaison sans
   groupe éligible ou sans modèle encore entraîné pour son groupe, la classification
   retombe automatiquement sur le moteur sémantique pour cette combinaison uniquement,
   de façon visible (colonne "Moteur utilisé"), jamais silencieuse.
"""
import re
import os
import html
import base64
import difflib
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
ENGINE_SEMANTIC = "Moteur sémantique institutionnel - taxonomie + ontologie + embeddings locaux"
ENGINE_TRAINED = "Modèle supervisé entraîné - recommandé pour la précision"
SWOT_ELEMENTS = ["Forces", "Faiblesses", "Opportunités", "Menaces"]
MIN_EXAMPLES_PER_THEME = 3
MIN_TOTAL_TRAINING_EXAMPLES = 15
# Pooled training groups: valid ONLY where the official theme taxonomy is
# identical across the listed participant types for the listed SWOT elements
# (verified against THEME_TAXONOMY below, not assumed). Pooling across types
# with different theme lists would silently corrupt the label space, so any
# (participant type, swot element) combination not covered by a pool here
# is never used for supervised training — see get_training_group_key.
TRAINING_POOLS = {
    "internal_psg_directeurs_enseignants": {
        "participant_types": ["PSG", "Directeurs", "Enseignants"],
        "swot_elements": ["Forces", "Faiblesses"],
        "label": "Interne : PSG + Directeurs + Enseignants (Forces / Faiblesses, 13 thèmes)",
    },
    "external_psg_anciens_enseignants": {
        "participant_types": ["PSG", "Anciens", "Enseignants"],
        "swot_elements": ["Opportunités", "Menaces"],
        "label": "Externe : PSG + Anciens + Enseignants (Opportunités / Menaces, 5 thèmes)",
    },
    "external_directeurs_etudiants": {
        "participant_types": ["Directeurs", "Étudiants"],
        "swot_elements": ["Opportunités", "Menaces"],
        "label": "Externe : Directeurs + Étudiants (Opportunités / Menaces, 5 thèmes)",
    },
}
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
def _strip_control_chars(text):
    """Remove characters (other than newline/tab) that can break ReportLab's
    paragraph parser, such as stray control bytes sometimes present in Excel
    exports (e.g. \\x0b vertical tab from a wrapped cell)."""
    return "".join(ch for ch in text if ch in ("\n", "\t") or ord(ch) >= 32)
def esc(value):
    text = html.escape(_strip_control_chars(clean(value)))
    # Self-closing <br/>, not <br>: this string is also fed into ReportLab's
    # Paragraph markup (a strict, XML-like parser) when building PDF reports.
    # An unclosed <br> there raises a ValueError and aborts the whole report;
    # <br/> is valid both in HTML (Streamlit) and in ReportLab's parser.
    return text.replace("\n", "<br/>")
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

/* Wrapped HTML tables — real <table> DOM, not st.dataframe's canvas grid,
   so long text wraps reliably instead of being clipped or ellipsized. */
.usj-table-wrap {{
    border: 1px solid #D0D6E0; border-radius: 14px; overflow: hidden;
    box-shadow: 0 8px 20px rgba(0,0,0,0.045); margin: 10px 0 18px 0;
}}
.usj-table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
.usj-table thead th {{
    background: {USJ_BLUE}; color: white; text-align: left; font-weight: 800;
    padding: 10px 14px; position: sticky; top: 0; z-index: 1;
}}
.usj-table tbody td {{
    padding: 10px 14px; vertical-align: top; white-space: normal;
    word-break: break-word; border-top: 1px solid #EEF1F6; color: {USJ_TEXT};
}}
.usj-table tbody tr:nth-child(even) {{ background: #F7FAFD; }}
.usj-table tbody tr:hover {{ background: {USJ_LIGHT_BLUE}; }}
.usj-table-scroll {{ max-height: 480px; overflow-y: auto; }}

/* Per-answer review cards, used in the expert validation screen instead of
   packing full answer text into a narrow spreadsheet cell. */
.review-card {{
    background: white; border: 1px solid #D0D6E0; border-radius: 14px;
    padding: 14px 18px; margin: 0 0 12px 0; box-shadow: 0 4px 14px rgba(0,0,0,0.04);
}}
.review-card-text {{
    font-size: 14.5px; line-height: 1.55; color: {USJ_TEXT}; margin: 6px 0 10px 0;
    white-space: normal; word-break: break-word;
}}
.review-badges {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }}
.usj-badge {{
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 11.5px; font-weight: 800; letter-spacing: 0.2px;
}}
.badge-trained {{ background: #E6F4EA; color: #1E7A46; }}
.badge-semantic {{ background: #EAF2FB; color: {USJ_BLUE}; }}
.badge-lowconf {{ background: #FDECEC; color: {USJ_RED}; }}
.badge-neutral {{ background: #EEF1F6; color: #64748B; }}
</style>
"""
def render_html_table(df, columns=None, rename=None, wrap_cols=None, max_height=480):
    """Render a dataframe as a real, wrapped HTML <table> instead of
    st.dataframe's canvas-rendered grid. Streamlit's grid (glide-data-grid)
    does not expose text wrapping or variable row height in its public API
    as of the current release — these remain open feature requests upstream
    — so long text is clipped there regardless of column width settings.
    A real <table> wraps naturally because each cell is an actual DOM
    element. Trade-off: no built-in column sort/resize/filter the way
    st.dataframe has; callers needing that should also offer st.dataframe
    in a companion expander (see calls to this function for the pattern).
    """
    if df is None or df.empty:
        st.caption("Aucune donnée à afficher.")
        return
    view = df.copy()
    if columns:
        view = view[[c for c in columns if c in view.columns]]
    if rename:
        view = view.rename(columns=rename)
    wrap_cols = set(rename.get(c, c) if rename else c for c in (wrap_cols or []))
    header_html = "".join(f"<th>{esc(c)}</th>" for c in view.columns)
    rows_html = []
    for _, row in view.iterrows():
        cells = []
        for col in view.columns:
            value = row[col]
            text = esc(value) if not isinstance(value, (int, float, np.floating, np.integer)) or pd.isna(value) else str(value)
            cells.append(f"<td>{text}</td>")
        rows_html.append(f"<tr>{''.join(cells)}</tr>")
    html_block(f"""
    <div class="usj-table-wrap">
      <div class="usj-table-scroll" style="max-height:{max_height}px;">
        <table class="usj-table">
          <thead><tr>{header_html}</tr></thead>
          <tbody>{''.join(rows_html)}</tbody>
        </table>
      </div>
    </div>
    """)
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
def get_training_group_key(participant_type, swot_element):
    """Return the pooled training-group key this (participant type, SWOT
    element) combination belongs to, or None if it has no valid pooling
    partner (its official theme list is not shared with any other type at
    this SWOT element). Rows with no group key are never used for
    supervised training — see resolve_effective_engine.
    """
    participant_type = canonical_participant_type(participant_type)
    for key, pool in TRAINING_POOLS.items():
        if participant_type in pool["participant_types"] and swot_element in pool["swot_elements"]:
            return key
    return None
def resolve_effective_engine(participant_type, swot_element, requested_engine, trained_models):
    """Determine which engine actually classifies this (participant type,
    SWOT element) combination, given the engine requested in the UI.

    The trained model is organized as one classifier per pooled training
    group (TRAINING_POOLS), not a single global model, because the official
    theme taxonomy differs across participant types and pooling is only
    valid where two or more types share an identical theme list. If the
    trained engine is requested but this combination has no eligible pool,
    or its pool has not been trained yet, falling back to an untrained /
    nonexistent model would be worse than falling back to the semantic
    engine — so that fallback is deliberate here, and it is always recorded
    (see the Engine_Used / Training_Group columns downstream), never silent.

    Returns (effective_engine, group_key). group_key is None when this
    combination has no pooling partner at all.
    """
    if requested_engine != ENGINE_TRAINED:
        return ENGINE_SEMANTIC, None
    group_key = get_training_group_key(participant_type, swot_element)
    model = (trained_models or {}).get(group_key) if group_key else None
    if model is not None:
        return ENGINE_TRAINED, group_key
    return ENGINE_SEMANTIC, group_key
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
# DOMAIN ONTOLOGY (shared guardrails used by the semantic engine)
# ============================================================
# Domain vocabularies. Each domain lists positive terms and which official
# themes it supports / actively contradicts. This gives a conservative
# guardrail so the semantic engine can't be pulled toward an unrelated theme
# purely by generic word overlap.
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
# ============================================================
# SEMANTIC INSTITUTIONAL ENGINE
# ------------------------------------------------------------
# Fully local, no external API call. Pipeline:
#   1. official taxonomy filtering
#   2. domain ontology guardrails
#   3. local sentence embeddings when available
#   4. TF-IDF fallback only if embeddings are not installed/cached
#   5. relevance score calibrated from score level + margin
#      (this is a heuristic ranking signal, not a statistical probability —
#       see semantic_confidence docstring)
# ============================================================
THEME_PROFILE_HINTS = {
    "soutenabilite financiere": "budget financement frais scolarite couts bourses viabilite ressources financieres soutenabilite economique",
    "gouvernance et leadership": "gouvernance leadership decision transparence pilotage direction representation procedures gestion institutionnelle",
    "strategie academique et qualite d enseignement": "qualite enseignement programmes cours formation curriculum pedagogie accreditation niveau academique apprentissage",
    "qualite de l enseignement": "qualite enseignement accompagnement orientation tutorat pedagogie cours formation apprentissage evaluation",
    "recherche et innovation": "recherche innovation publications laboratoires doctorat brevets valorisation production scientifique",
    "ressources documentaires et environnement digital": "bibliotheque ressources documentaires numerique digital informatique plateformes outils donnees logiciels",
    "ressources documentaires numeriques et informatiques": "bibliotheque ressources documentaires numerique digital informatique plateformes outils donnees logiciels",
    "succes des etudiants": "reussite etudiante recrutement accompagnement services support employabilite orientation parcours inscription insertion",
    "ressources humaines": "personnel enseignants administratifs professeurs competences recrutement charge conditions ressources humaines",
    "strategie et mobilite internationales": "international mobilite partenariats echanges etranger diaspora francophonie cooperation internationale",
    "mobilite internationale": "international mobilite partenariats echanges etranger diaspora francophonie cooperation internationale",
    "mission societale": "mission societale engagement social responsabilite sociale communaute citoyennete impact social service societe",
    "espace et infrastructures": "campus batiments locaux salles equipements infrastructures espaces maintenance amenagement",
    "espace et infrastructure": "campus batiments locaux salles equipements infrastructures espaces maintenance amenagement",
    "environnement de travail": "conditions de travail climat communication interne collaboration charge de travail bien etre processus administratif",
    "diversite et inclusion": "diversite inclusion equite egalite handicap genre discrimination accessibilite",
    "developpement durable odd": "developpement durable odd durabilite ecologie energie transition energetique environnement responsabilite environnementale",
    "vie universitaire": "vie etudiante sport clubs activites aide psychologique experience etudiante animation campus",
    "aide financiere": "bourses aide financiere frais paiement couts scolarite soutien financier",
    "insertion professionnelle": "emploi stage carriere employabilite marche du travail entreprises employeurs professionnalisation",
    "marche du travail et associations professionnelles": "marche du travail employeurs entreprises associations professionnelles metiers stages carrieres emploi",
    "marche du travail et relations avec les employeurs": "marche du travail employeurs entreprises relations professionnelles stages carrieres emploi",
    "concurrence avec les autres universites": "concurrence competition autres universites attractivite differenciation positionnement offre concurrentielle",
    "intelligence artificielle": "intelligence artificielle ia automatisation machine learning data science outils generatifs transformation ia",
    "reputation et image": "reputation image classement visibilite notoriete attractivite rayonnement perception reconnaissance",
    "environnement politique et economique emigration": "crise politique economique emigration instabilite inflation guerre securite contexte libanais",
}
def _theme_profile_text(theme):
    theme_n = normalize(theme)
    hints = []
    for key, value in THEME_PROFILE_HINTS.items():
        if key in theme_n or theme_n in key:
            hints.append(value)
    return clean(theme) + ". " + " ".join(hints)
@st.cache_resource(show_spinner=False)
def _load_local_sentence_model():
    """Load a local multilingual sentence-transformer if available.
    No download is required or forced. If the model is absent, the platform
    falls back to ontology + TF-IDF so the app keeps working on Azure.
    """
    try:
        from sentence_transformers import SentenceTransformer
        model_name = os.environ.get("LOCAL_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        try:
            return SentenceTransformer(model_name, local_files_only=True)
        except TypeError:
            return SentenceTransformer(model_name)
    except Exception:
        return None
def _cosine_scores_from_embeddings(answer, theme_profiles):
    model = _load_local_sentence_model()
    if model is None:
        return None
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        vectors = model.encode([answer] + theme_profiles, normalize_embeddings=True)
        return cosine_similarity([vectors[0]], vectors[1:]).flatten().tolist()
    except Exception:
        return None
def semantic_institutional_score_candidates(answer, participant_type, swot_element):
    themes = official_themes_for(participant_type, swot_element, include_autre=False)
    if not themes:
        return [], "no_themes"
    theme_profiles = [_theme_profile_text(t) for t in themes]
    embedding_scores = _cosine_scores_from_embeddings(answer, theme_profiles)
    if embedding_scores is not None:
        semantic_scores = [(s + 1) / 2 if s < 0 else s for s in embedding_scores]
        semantic_source = "embeddings locaux"
        semantic_weight = 0.50
        lexical_weight = 0.05
    else:
        semantic_scores = tfidf_scores_against_themes(answer, theme_profiles)
        semantic_source = "fallback TF-IDF"
        semantic_weight = 0.30
        lexical_weight = 0.20
    lexical_scores = tfidf_scores_against_themes(answer, themes)
    detected = detected_answer_domains(answer)
    ranked = []
    for i, theme in enumerate(themes):
        domain_pos, domain_neg, matched = domain_guardrail_score(answer, theme)
        ontology_score = max(0.0, domain_pos - 0.70 * domain_neg)
        score = (
            semantic_weight * semantic_scores[i]
            + 0.40 * ontology_score
            + lexical_weight * lexical_scores[i]
        )
        # Strong guardrail: when the answer clearly belongs to a domain and
        # the candidate theme is in a contradictory domain, suppress it.
        if detected and domain_pos == 0 and domain_neg > 0:
            score *= 0.35
        elif detected and domain_pos == 0:
            score *= 0.70
        score = max(0.0, min(1.0, score))
        ranked.append((theme, score, matched, semantic_scores[i], lexical_scores[i], ontology_score))
    return sorted(ranked, key=lambda x: x[1], reverse=True), semantic_source
def semantic_confidence(ranked, semantic_source):
    """Heuristic relevance score (0-100), NOT a calibrated statistical
    probability. It combines the top candidate's raw score with the margin
    over the runner-up. Displayed in the UI as "score de pertinence", kept
    deliberately distinct from the trained model's cross-validated accuracy,
    which is the only number in this app backed by a real statistical
    estimate.
    """
    if not ranked:
        return 0.0
    best = ranked[0][1]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    margin = max(best - second, 0.0)
    conf = 20 + best * 62 + margin * 120
    if semantic_source == "fallback TF-IDF":
        conf = min(conf, 78)
    if best < 0.30:
        conf = min(conf, 42)
    if margin < 0.04:
        conf = min(conf, 55)
    if margin >= 0.18 and best >= 0.55 and semantic_source != "fallback TF-IDF":
        conf = max(conf, 82)
    return round(max(5, min(conf, 95)), 1)
def classify_semantic_institutional(answer, participant_type, swot_element):
    ranked, source = semantic_institutional_score_candidates(answer, participant_type, swot_element)
    if not ranked:
        return "", 0.0, "", "Aucun thème officiel disponible"
    best_theme, best_score, matched, sem_score, lex_score, onto_score = ranked[0]
    conf = semantic_confidence(ranked, source)
    top3 = " | ".join([f"{t} ({round(s * 100, 1)})" for t, s, *_ in ranked[:3]])
    if source == "embeddings locaux":
        evidence = (
            "Moteur sémantique institutionnel : taxonomie officielle + ontologie de domaine "
            f"+ embeddings locaux. Domaines détectés : {', '.join(matched) if matched else 'aucun domaine dominant'}."
        )
    else:
        evidence = (
            "Moteur sémantique institutionnel : taxonomie officielle + ontologie de domaine. "
            "Embeddings locaux non disponibles sur ce serveur ; fallback lexical contrôlé utilisé."
        )
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
    out["training_group"] = [
        get_training_group_key(pt, se) for pt, se in zip(out["Respondent_Type"], out["swot_element"])
    ]
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
    """Classify one answer with the trained pipeline and return (theme, confidence).

    confidence handling by classifier type:
      - predict_proba available (LogisticRegression, MultinomialNB): use it directly,
        this is a genuine calibrated-ish probability from the algorithm itself.
      - decision_function only, >=3 classes (LinearSVC, SGDClassifier): softmax over
        the per-class margins. A reasonable ranking signal, not a calibrated probability.
      - decision_function only, exactly 2 classes: BUG FIX. scikit-learn's
        decision_function for a binary linear classifier returns a single signed
        margin (shape (1,)), not one score per class. The previous implementation
        ran the multi-class softmax on this single value, which always produced
        exp(0)/exp(0) = 100% confidence regardless of how close the answer was to
        the decision boundary. Fixed by applying a logistic (sigmoid) squashing to
        the margin and reporting the winning class's probability instead. This is
        still an approximation, not a statistically calibrated probability — true
        calibration would require CalibratedClassifierCV with an isotonic/Platt fit,
        which needs more validated data than this project currently has.
    """
    pred = model.predict([answer])[0]
    confidence = None
    try:
        clf = model.named_steps.get("clf")
        if hasattr(clf, "predict_proba"):
            proba = model.predict_proba([answer])[0]
            confidence = round(float(max(proba)) * 100, 1)
        elif hasattr(clf, "decision_function"):
            raw_scores = np.array(model.decision_function([answer])).reshape(-1)
            n_classes = len(getattr(clf, "classes_", []))
            if n_classes == 2 and raw_scores.shape[0] == 1:
                margin = float(raw_scores[0])
                prob_positive = 1.0 / (1.0 + np.exp(-margin))
                confidence = round(max(prob_positive, 1.0 - prob_positive) * 100, 1)
            elif raw_scores.shape[0] > 1:
                exp_scores = np.exp(raw_scores - raw_scores.max())
                confidence = round(float(exp_scores.max() / exp_scores.sum()) * 100, 1)
    except Exception:
        confidence = None
    return pred, confidence
# ============================================================
# UNIFIED CLASSIFICATION DISPATCH
# ============================================================
def classify_answer(answer, participant_type, swot_element, engine, trained_models=None):
    """Classify one answer, routing to the correct pooled trained model when
    eligible, or to the semantic engine otherwise. trained_models is a dict
    of {group_key: fitted pipeline}, one entry per TRAINING_POOLS group that
    has been trained and activated so far — see resolve_effective_engine for
    how the fallback is decided.
    """
    effective_engine, group_key = resolve_effective_engine(participant_type, swot_element, engine, trained_models)
    if effective_engine == ENGINE_TRAINED:
        model = trained_models[group_key]
        theme, conf = classify_with_trained_model(answer, model)
        pool_label = TRAINING_POOLS[group_key]["label"]
        return theme, (conf if conf is not None else 0.0), "", f"Modèle supervisé entraîné — groupe : {pool_label}"
    return classify_semantic_institutional(answer, participant_type, swot_element)
def build_classification_dataframe(df_scope, engine, trained_models=None):
    rows = []
    for idx, row in df_scope.iterrows():
        swot_element = row.get("swot_element", "")
        if swot_element not in SWOT_ELEMENTS:
            continue
        answer = clean(row.get("Final_Answer", ""))
        if not answer:
            continue
        participant_type = row.get("Respondent_Type", "")
        # Computed once here (rather than only inferred implicitly from the
        # classification call) so the UI can display, per row, which engine
        # actually produced the prediction — this never has to be guessed
        # back out downstream, and it can never silently drift from what
        # classify_answer actually did, since both call the same resolver.
        effective_engine, group_key = resolve_effective_engine(participant_type, swot_element, engine, trained_models)
        theme, conf, top3, evidence = classify_answer(answer, participant_type, swot_element, engine, trained_models)
        rows.append({
            "row_id": idx, "Respondent_Type": participant_type, "groupe": row.get("groupe", ""),
            "participants": row.get("participants", ""), "swot_element": swot_element,
            "question": row.get("question", ""), "Final_Answer": answer,
            "AI_Suggested_Theme": theme, "Confidence": conf, "Top_3_Themes": top3, "Evidence": evidence,
            "Engine_Used": effective_engine, "Training_Group": group_key,
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
# DATA EDITOR STATE HELPERS
# ------------------------------------------------------------
# st.data_editor's `edited_rows` dict is keyed by POSITION (row order in the
# displayed frame), not by the DataFrame's index label. `_resolve_row_id` is
# the single, shared way to turn one of those positional keys back into our
# real `row_id` (the original Excel row index), and every caller below goes
# through it so there is exactly one place this logic can go wrong.
#
# Persistence itself also has a single source of truth: a session_state
# "shadow store" (`_editor_value_store`) written by the `on_change` callback
# (`persist_editor_changes_callback`) *before* Streamlit rebuilds the
# selectbox options for newly typed themes. Reading straight from
# `st.session_state[editor_key]["edited_rows"]` a second time in a separate
# helper was redundant and could drift out of sync with the shadow store, so
# that path has been removed in favor of this one.
# ============================================================
def _resolve_row_id(raw_key, row_ids):
    """Resolve a data_editor `edited_rows` key to the underlying row_id.
    `raw_key` is positional (0-based row order in the displayed frame) in
    normal operation, so position is always checked first. The direct
    membership fallback only covers the unusual case where the key already
    equals a row_id (e.g. programmatic edits), and is intentionally tried
    last so it can never shadow a legitimate positional match.
    """
    try:
        pos = int(raw_key)
    except (TypeError, ValueError):
        pos = None
    if pos is not None and 0 <= pos < len(row_ids):
        return row_ids[pos]
    if raw_key in row_ids:
        return raw_key
    return None
def _editor_value_store():
    """Persistent cell-level storage for manual edits in st.data_editor.
    Streamlit keeps only deltas inside the data_editor widget state. When the
    dropdown options are rebuilt after adding a new theme, those deltas can be
    recalculated and the visual value of the text column may disappear. This
    store keeps the expert-entered value independently from the widget, so the
    column "Nouveau thème" remains visible and exportable.
    """
    return st.session_state.setdefault("editor_cell_values", {})
def _editor_store_for(editor_key):
    store = _editor_value_store()
    return store.setdefault(editor_key, {})
def apply_persistent_editor_values(edit_df, editor_key):
    values = _editor_store_for(editor_key)
    if not values:
        return edit_df
    out = edit_df.copy()
    for row_id, row_values in values.items():
        if row_id in out.index and isinstance(row_values, dict):
            for col_name, value in row_values.items():
                if col_name in out.columns:
                    out.at[row_id, col_name] = value
    return out
def save_persistent_editor_values(edited_df, editor_key):
    values = _editor_store_for(editor_key)
    for row_id, row in edited_df.iterrows():
        row_values = values.setdefault(row_id, {})
        if "Nouveau thème" in edited_df.columns:
            new_theme_value = clean(row.get("Nouveau thème", ""))
            if new_theme_value:
                row_values["Nouveau thème"] = new_theme_value
            elif row_values.get("Nouveau thème"):
                # Keep the previously typed theme visible unless the expert
                # explicitly edits this same cell to another non-empty value.
                pass
            else:
                row_values["Nouveau thème"] = ""
        if "Thème validé" in edited_df.columns:
            theme_value = clean(row.get("Thème validé", ""))
            if theme_value:
                row_values["Thème validé"] = theme_value
def sync_custom_themes_from_persistent_values(editor_key, participant_type, swot_element):
    values = _editor_store_for(editor_key)
    for row_values in values.values():
        if not isinstance(row_values, dict):
            continue
        new_theme = clean(row_values.get("Nouveau thème", ""))
        if new_theme:
            register_custom_theme(participant_type, swot_element, new_theme)
def persist_editor_changes_callback(editor_key, participant_type, swot_element, row_ids):
    """Save data_editor cell changes immediately when Streamlit triggers a rerun.
    This is necessary because changing the selectbox options after adding a new
    theme can reset the widget state. The callback captures the typed value
    before the widget is rebuilt, so the value remains visible in the
    "Nouveau thème" column and is also added to the dropdown list.
    """
    editor_state = st.session_state.get(editor_key, {})
    if not isinstance(editor_state, dict):
        return
    edited_rows = editor_state.get("edited_rows", {})
    if not isinstance(edited_rows, dict):
        return
    values = _editor_store_for(editor_key)
    for raw_key, changes in edited_rows.items():
        if not isinstance(changes, dict):
            continue
        row_id = _resolve_row_id(raw_key, row_ids)
        if row_id is None:
            continue
        row_values = values.setdefault(row_id, {})
        if "Nouveau thème" in changes:
            new_theme_value = clean(changes.get("Nouveau thème", ""))
            row_values["Nouveau thème"] = new_theme_value
            if new_theme_value:
                register_custom_theme(participant_type, swot_element, new_theme_value)
        if "Thème validé" in changes:
            theme_value = clean(changes.get("Thème validé", ""))
            if theme_value:
                row_values["Thème validé"] = theme_value
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
# THEMATIC PARAGRAPH SYNTHESIS PER SWOT ELEMENT
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
# DYNAMIC SWOT MATRIX VISUAL (HTML/CSS card grid)
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
# DOWNLOADABLE PDF REPORT (post-validation synthesis)
# ============================================================
def _find_existing_file(possible_paths):
    """Return the first existing path from a list of possible local paths."""
    for candidate in possible_paths:
        try:
            path = Path(candidate)
            if path.exists():
                return path
        except Exception:
            continue
    return None
def _register_pdf_fonts():
    """Use Candara in PDF reports when the font file is available on the server.
    If Candara is not installed or not included in the app folder, ReportLab falls
    back safely to Helvetica so the report generation does not fail.
    """
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        base_dir = Path(__file__).parent if "__file__" in globals() else Path(".")
        regular_candidates = [
            base_dir / "Candara.ttf",
            base_dir / "candara.ttf",
            Path("Candara.ttf"),
            Path("candara.ttf"),
            Path("/usr/share/fonts/truetype/msttcorefonts/Candara.ttf"),
            Path("/usr/share/fonts/truetype/msttcorefonts/candara.ttf"),
            Path("C:/Windows/Fonts/Candara.ttf"),
            Path("C:/Windows/Fonts/candara.ttf"),
        ]
        bold_candidates = [
            base_dir / "Candarab.ttf",
            base_dir / "Candara Bold.ttf",
            base_dir / "candarab.ttf",
            Path("Candarab.ttf"),
            Path("Candara Bold.ttf"),
            Path("candarab.ttf"),
            Path("/usr/share/fonts/truetype/msttcorefonts/Candarab.ttf"),
            Path("/usr/share/fonts/truetype/msttcorefonts/candarab.ttf"),
            Path("C:/Windows/Fonts/Candarab.ttf"),
            Path("C:/Windows/Fonts/candarab.ttf"),
        ]
        regular_path = _find_existing_file(regular_candidates)
        bold_path = _find_existing_file(bold_candidates)
        if regular_path:
            pdfmetrics.registerFont(TTFont("Candara", str(regular_path)))
            if bold_path:
                pdfmetrics.registerFont(TTFont("Candara-Bold", str(bold_path)))
            else:
                pdfmetrics.registerFont(TTFont("Candara-Bold", str(regular_path)))
            return "Candara", "Candara-Bold"
    except Exception:
        pass
    return "Helvetica", "Helvetica-Bold"
def _safe_paragraph(Paragraph, text, style):
    """Build a ReportLab Paragraph defensively.
    ReportLab's paragraph text is a small XML-like markup, so any unexpected
    character from source data that slips past `esc()` can make its parser
    raise and abort PDF generation entirely (this is what caused the
    'paragraph text ... caused exception' crash). If the escaped text still
    fails to parse, fall back to a fully tag-stripped plain-text version so
    the report is still produced instead of crashing the whole app.
    Callers should pass RAW (unescaped) text — this function calls esc()
    itself, so pre-escaping the argument would double-escape it.
    """
    safe_text = esc(text)
    try:
        return Paragraph(safe_text, style)
    except Exception:
        fallback = re.sub(r"<[^>]*>", " ", safe_text)
        try:
            return Paragraph(fallback, style)
        except Exception:
            return Paragraph("(contenu illisible)", style)
def _pdf_styles():
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib import colors
    body_font, bold_font = _register_pdf_fonts()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="USJTitle", fontSize=20, leading=24,
                               textColor=colors.HexColor(USJ_BLUE), fontName=bold_font, spaceAfter=6))
    styles.add(ParagraphStyle(name="USJSubtitle", fontSize=12, leading=16,
                               textColor=colors.HexColor("#64748B"), fontName=body_font, spaceAfter=14))
    styles.add(ParagraphStyle(name="USJElement", fontSize=15, leading=18,
                               textColor=colors.white, fontName=bold_font))
    styles.add(ParagraphStyle(name="USJTheme", fontSize=11.5, leading=15, textColor=colors.HexColor(USJ_BLUE),
                               fontName=bold_font, spaceBefore=10, spaceAfter=2))
    styles.add(ParagraphStyle(name="USJBody", fontSize=10, leading=14.5, textColor=colors.HexColor(USJ_TEXT),
                               fontName=body_font, alignment=TA_JUSTIFY, spaceAfter=8))
    styles.add(ParagraphStyle(name="USJConclusion", fontSize=10.5, leading=15,
                               textColor=colors.HexColor(USJ_TEXT), fontName=body_font, alignment=TA_JUSTIFY))
    return styles
def _pdf_page_decorator(canvas, doc):
    """Draw UAQ logo in the top-right corner and page number in the footer."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.lib.utils import ImageReader
        page_width, page_height = A4
        base_dir = Path(__file__).parent if "__file__" in globals() else Path(".")
        logo_path = _find_existing_file([
            base_dir / LOGO_PATH,
            Path(LOGO_PATH),
            base_dir / "LOGO NEW UAQ.png",
            Path("LOGO NEW UAQ.png"),
        ])
        if logo_path:
            try:
                logo = ImageReader(str(logo_path))
                img_w, img_h = logo.getSize()
                target_w = 5.0 * cm
                target_h = target_w * img_h / max(img_w, 1)
                max_h = 1.35 * cm
                if target_h > max_h:
                    target_h = max_h
                    target_w = target_h * img_w / max(img_h, 1)
                canvas.drawImage(
                    logo,
                    page_width - doc.rightMargin - target_w,
                    page_height - 1.55 * cm,
                    width=target_w,
                    height=target_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                pass
        body_font, _ = _register_pdf_fonts()
        canvas.setFont(body_font, 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawCentredString(page_width / 2, 1.05 * cm, f"Page {doc.page}")
    except Exception:
        pass
def build_pdf_swot_matrix(validated_df, participant_type_filter, groupe_filter, styles, colors, cm, Paragraph, Table, TableStyle, top_n=5):
    """Build a printable SWOT matrix for the PDF report using the same validated data
    and filters as the on-screen dynamic SWOT matrix."""
    scope = filter_validated(validated_df, participant_type_filter, groupe_filter)
    element_colors = {"Forces": USJ_BLUE, "Faiblesses": USJ_RED, "Opportunités": "#1E7A46", "Menaces": "#B23A22"}
    element_bgs = {"Forces": "#EAF2FB", "Faiblesses": "#FDEDEE", "Opportunités": "#EAF7EF", "Menaces": "#FDEFE9"}
    cell_data = []
    for element in SWOT_ELEMENTS:
        sub = scope[scope["swot_element"] == element]
        theme_counts = sub.groupby("Validated_Theme").size().sort_values(ascending=False).head(top_n)
        lines = [f"<b>{element.upper()}</b> ({len(sub)} éléments)"]
        if theme_counts.empty:
            lines.append("<font color='#64748B'>Aucune donnée validée pour ce filtre</font>")
        else:
            for i, (theme, count) in enumerate(theme_counts.items(), start=1):
                lines.append(f"{i}. {esc(theme)} ({count})")
        joined = "<br/>".join(lines)
        try:
            para = Paragraph(joined, styles["USJBody"])
        except Exception:
            # This cell intentionally carries <b>/<font> markup, so it can't
            # go through _safe_paragraph (which would escape those tags too).
            # If it still fails to parse, strip all tags as a last resort.
            para = Paragraph(re.sub(r"<[^>]*>", " ", joined), styles["USJBody"])
        cell_data.append(para)
    matrix = Table(
        [[cell_data[0], cell_data[1]], [cell_data[2], cell_data[3]]],
        colWidths=[8.25 * cm, 8.25 * cm],
        rowHeights=None,
    )
    matrix.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#D0D6E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D6E0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(element_bgs["Forces"])),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor(element_bgs["Faiblesses"])),
        ("BACKGROUND", (0, 1), (0, 1), colors.HexColor(element_bgs["Opportunités"])),
        ("BACKGROUND", (1, 1), (1, 1), colors.HexColor(element_bgs["Menaces"])),
        ("LINEABOVE", (0, 0), (0, 0), 3, colors.HexColor(element_colors["Forces"])),
        ("LINEABOVE", (1, 0), (1, 0), 3, colors.HexColor(element_colors["Faiblesses"])),
        ("LINEABOVE", (0, 1), (0, 1), 3, colors.HexColor(element_colors["Opportunités"])),
        ("LINEABOVE", (1, 1), (1, 1), 3, colors.HexColor(element_colors["Menaces"])),
    ]))
    return matrix
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
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2.4 * cm, bottomMargin=2.0 * cm,
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
            story.append(_safe_paragraph(
                Paragraph, f"{item['rank']}. {item['theme']} ({item['count']} réponses)", styles["USJTheme"]
            ))
            story.append(_safe_paragraph(Paragraph, item["paragraph"], styles["USJBody"]))
        story.append(Spacer(1, 10))
    story.append(PageBreak())
    story.append(Paragraph("Priorités par élément SWOT", styles["USJTitle"]))
    priorities, conclusion = build_priorities_and_conclusion(validated_df, participant_type_filter, groupe_filter)
    for element in SWOT_ELEMENTS:
        story.append(Paragraph(element, styles["USJTheme"]))
        items = priorities.get(element, [])
        if items:
            for i, (theme, count) in enumerate(items, start=1):
                story.append(_safe_paragraph(
                    Paragraph,
                    f"{i}. {theme} — {count} occurrences validées ({PRIORITY_LABELS.get(element, '')})",
                    styles["USJBody"],
                ))
        else:
            story.append(Paragraph("Aucune priorité identifiable pour ce filtre.", styles["USJBody"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Conclusion", styles["USJTitle"]))
    story.append(_safe_paragraph(Paragraph, conclusion, styles["USJConclusion"]))
    story.append(PageBreak())
    story.append(Paragraph("Matrice SWOT synthétique", styles["USJTitle"]))
    story.append(Paragraph("Vue consolidée des thèmes dominants selon les filtres du rapport.", styles["USJSubtitle"]))
    story.append(build_pdf_swot_matrix(
        validated_df, participant_type_filter, groupe_filter, styles, colors, cm, Paragraph, Table, TableStyle
    ))
    doc.build(story, onFirstPage=_pdf_page_decorator, onLaterPages=_pdf_page_decorator)
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
    """Single-table expert validation: one dropdown to pick the SWOT element,
    one flat table underneath for every participant type at once.

    Trade-off, stated explicitly rather than hidden: the official theme
    taxonomy (THEME_TAXONOMY) differs by participant type, but one table
    needs one shared dropdown per column. The "Thème validé" options here
    are the UNION of official themes across every participant type present
    for the selected SWOT element — not the strict per-type list. This is a
    deliberate simplicity/rigor trade-off for a single-table UI; it does not
    prevent picking a theme that isn't officially valid for a given row's
    participant type. If that matters for your final coding scheme, spot-
    check across participant types before treating a batch as final.
    """
    if classified_df.empty:
        st.warning("Aucune réponse SWOT à classifier.")
        return pd.DataFrame()
    st.markdown("### Validation experte des classifications")
    st.caption("Choisissez un élément SWOT, validez le tableau, passez au suivant. Les réponses à "
               "faible score de pertinence / confiance apparaissent en premier dans chaque tableau.")
    validated_store = st.session_state.setdefault("validated_by_swot", {})
    swot_choice = st.selectbox("Élément SWOT à valider", SWOT_ELEMENTS, key="validation_swot_choice")
    subset = classified_df[classified_df["swot_element"] == swot_choice].sort_values(
        "Confidence", ascending=True
    ).reset_index(drop=True)
    if subset.empty:
        st.caption("Aucune réponse pour cet élément SWOT.")
    else:
        present_types = subset["Respondent_Type"].unique().tolist()
        theme_union = []
        for pt in present_types:
            for t in official_themes_for(pt, swot_choice, include_autre=False):
                if t not in theme_union:
                    theme_union.append(t)
        custom_themes_all = set()
        for pt in present_types:
            custom_themes_all.update(get_custom_themes(pt, swot_choice))
        theme_options = theme_union + [t for t in sorted(custom_themes_all) if t not in theme_union] + ["Autre (nouveau thème)"]
        if len(present_types) > 1:
            st.caption(f"Types de participants dans ce tableau : {', '.join(present_types)}. La liste de "
                       "thèmes ci-dessous regroupe les thèmes officiels de tous ces types (voir docstring "
                       "de la fonction pour la justification) — vérifiez la cohérence type/thème au besoin.")
        editor_key = f"editor_swot_{safe_filename(swot_choice)}"
        edit_df = subset[["row_id", "Respondent_Type", "groupe", "Final_Answer", "AI_Suggested_Theme"]].copy()
        edit_df["Thème validé"] = edit_df["AI_Suggested_Theme"]
        edit_df = edit_df.rename(columns={
            "Respondent_Type": "Type", "groupe": "Sous-groupe", "Final_Answer": "Réponse",
            "AI_Suggested_Theme": "Proposé (IA)",
        }).set_index("row_id")
        edit_df = apply_persistent_editor_values(edit_df, editor_key)
        row_ids_for_editor = list(edit_df.index)
        edited = st.data_editor(
            edit_df,
            key=editor_key,
            use_container_width=True,
            hide_index=True,
            on_change=persist_editor_changes_callback,
            args=(editor_key, None, swot_choice, row_ids_for_editor),
            column_config={
                "Type": st.column_config.TextColumn(disabled=True, width="small"),
                "Sous-groupe": st.column_config.TextColumn(disabled=True, width="small"),
                "Réponse": st.column_config.TextColumn(disabled=True, width="large"),
                "Proposé (IA)": st.column_config.TextColumn(disabled=True, width="medium"),
                "Thème validé": st.column_config.SelectboxColumn(options=theme_options, required=True, width="medium"),
            },
        )
        save_persistent_editor_values(edited, editor_key)
        pending_new = edited[edited["Thème validé"] == "Autre (nouveau thème)"]
        if not pending_new.empty:
            st.markdown(f"**Nouveaux thèmes à préciser** ({len(pending_new)} réponse(s) marquée(s) « Autre ») :")
            for row_id, row in pending_new.iterrows():
                orig = subset[subset["row_id"] == row_id].iloc[0]
                preview = orig["Final_Answer"]
                preview = preview[:80] + "…" if len(preview) > 80 else preview
                stored_new = _editor_store_for(editor_key).get(row_id, {}).get("Nouveau thème", "")
                new_val = st.text_input(
                    f"« {preview} » — {orig['Respondent_Type']}",
                    value=stored_new, key=f"newtheme_{editor_key}_{row_id}",
                )
                row_values = _editor_store_for(editor_key).setdefault(row_id, {})
                row_values["Nouveau thème"] = new_val
                if new_val:
                    register_custom_theme(orig["Respondent_Type"], swot_choice, new_val)
        if st.button(f"✅ Confirmer les validations — {swot_choice}", key=f"confirm_{editor_key}"):
            store = _editor_store_for(editor_key)
            confirmed_rows = []
            for _, row in subset.iterrows():
                row_id = row["row_id"]
                out = row.to_dict()
                stored_values = store.get(row_id, {})
                selected_theme = stored_values.get("Thème validé", row["AI_Suggested_Theme"])
                new_theme_input = clean(stored_values.get("Nouveau thème", ""))
                final_theme = _resolve_validated_theme(selected_theme, new_theme_input)
                out["Validated_Theme"] = final_theme if final_theme else selected_theme
                out["New_Theme"] = new_theme_input
                confirmed_rows.append(out)
            validated_store[swot_choice] = pd.DataFrame(confirmed_rows)
            st.success(f"{len(confirmed_rows)} réponses validées pour « {swot_choice} ».")
    if validated_store:
        st.caption("Validations confirmées jusqu'ici : " +
                   " · ".join(f"{k} ({len(v)})" for k, v in validated_store.items()))
    return pd.concat(validated_store.values(), ignore_index=True) if validated_store else pd.DataFrame()

def render_engine_selector(df_scope):
    st.markdown("""
    <div class="ai-card">
        <h3>Moteur de classification actif</h3>
        <p>Le moteur sémantique institutionnel (100% local) filtre d'abord les thèmes officiels selon le
        type de participant et l'élément SWOT, applique une ontologie de domaine, puis utilise des
        embeddings locaux si disponibles — TF-IDF en repli sinon. Aucune donnée n'est jamais transmise à
        un service externe par ce moteur.</p>
        <p>Le modèle supervisé entraîné n'est pas un modèle unique : il est organisé en trois groupes
        d'entraînement mutualisés, définis uniquement là où plusieurs types de participants partagent
        exactement la même liste de thèmes officiels (voir onglet 2). Pour toute combinaison type de
        participant / élément SWOT dont le groupe n'a pas encore été entraîné — ou qui n'a aucun
        partenaire de regroupement — la classification retombe automatiquement sur le moteur sémantique,
        de façon visible (colonne « Moteur utilisé »), jamais silencieuse.</p>
    </div>
    """, unsafe_allow_html=True)
    trained_models = st.session_state.get("trained_models", {})
    n_pools = len(TRAINING_POOLS)
    n_trained = len(trained_models)
    options = [ENGINE_SEMANTIC]
    if n_trained > 0:
        options.append(f"{ENGINE_TRAINED} (pools entraînés : {n_trained}/{n_pools})")
    else:
        options.append(f"{ENGINE_TRAINED} (aucun pool entraîné pour le moment - voir onglet 2)")
    choice = st.radio("Choisir le moteur", options, key="engine_choice_radio")
    if choice.startswith(ENGINE_TRAINED):
        engine = ENGINE_TRAINED
        if n_trained == 0:
            st.markdown('<div class="ai-warning">Aucun pool n\'est encore entraîné. Toutes les réponses seront '
                        'classifiées par le moteur sémantique jusqu\'à ce qu\'au moins un pool soit entraîné '
                        'dans l\'onglet « 2. Entraîner le modèle ».</div>', unsafe_allow_html=True)
        elif n_trained < n_pools:
            missing = [p["label"] for k, p in TRAINING_POOLS.items() if k not in trained_models]
            st.markdown('<div class="ai-info-box">Pools encore non entraînés (moteur sémantique utilisé pour '
                        'eux en attendant) : ' + "; ".join(missing) + '</div>', unsafe_allow_html=True)
    else:
        engine = ENGINE_SEMANTIC
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
    st.markdown("""
    <div class="ai-info-box">
        Le modèle n'est pas entraîné globalement : il est entraîné séparément pour chacun des trois
        groupes ci-dessous, définis uniquement là où plusieurs types de participants partagent
        exactement la même liste de thèmes officiels. Entraîner un modèle unique sur l'ensemble des
        ~312 réponses SWOT diluerait les données sur une centaine de combinaisons (type × élément ×
        thème), la plupart avec 1-2 exemples : statistiquement inexploitable. Voir la documentation en
        tête de fichier pour le détail de ce regroupement.
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
    full_train_df = prepare_training_dataset(combined)
    if full_train_df.empty:
        st.markdown('<div class="ai-warning">Aucune donnée validée disponible pour l\'instant. Allez dans '
                    'l\'onglet 1, classifiez et validez quelques réponses, puis revenez ici.</div>', unsafe_allow_html=True)
        return
    trained_models = st.session_state.setdefault("trained_models", {})
    trained_accuracies = st.session_state.setdefault("trained_model_accuracies", {})
    for pool_key, pool in TRAINING_POOLS.items():
        st.markdown(f"---\n#### {pool['label']}")
        pool_train_df = full_train_df[full_train_df["training_group"] == pool_key].reset_index(drop=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Réponses validées", len(pool_train_df))
        c2.metric("Thèmes distincts", pool_train_df["label"].nunique() if not pool_train_df.empty else 0)
        c3.metric("Min. requis", MIN_TOTAL_TRAINING_EXAMPLES)
        if pool_train_df.empty:
            st.caption("Aucune donnée validée pour ce groupe pour le moment.")
            continue
        counts = pool_train_df["label"].value_counts().reset_index()
        counts.columns = ["Thème", "Nombre d'exemples validés"]
        st.dataframe(counts, use_container_width=True, hide_index=True,
                     column_config={
                         "Thème": st.column_config.TextColumn(width="large"),
                         "Nombre d'exemples validés": st.column_config.NumberColumn(width="small"),
                     })
        thin_themes = counts[counts["Nombre d'exemples validés"] < MIN_EXAMPLES_PER_THEME]
        if not thin_themes.empty:
            st.caption(f"Thèmes sous {MIN_EXAMPLES_PER_THEME} exemples validés (à renforcer en priorité) : "
                       + ", ".join(thin_themes["Thème"].tolist()))
        run_key = f"run_training_{pool_key}"
        if st.button(f"Lancer l'entraînement et l'évaluation — {pool['label']}", key=run_key):
            with st.spinner("Entraînement et validation croisée en cours..."):
                results_df, predictions_df, error = evaluate_theme_models(pool_train_df)
            st.session_state[f"training_results_{pool_key}"] = results_df
            st.session_state[f"training_predictions_{pool_key}"] = predictions_df
            st.session_state[f"training_error_{pool_key}"] = error
            st.session_state[f"training_snapshot_{pool_key}"] = pool_train_df
        results_df = st.session_state.get(f"training_results_{pool_key}", pd.DataFrame())
        error = st.session_state.get(f"training_error_{pool_key}", "")
        if error:
            st.markdown(f'<div class="ai-warning">{esc(error)}</div>', unsafe_allow_html=True)
            continue
        if results_df.empty:
            continue
        st.markdown("Résultats — précision réelle par algorithme (validation croisée) :")
        st.dataframe(results_df, use_container_width=True)
        best_row = results_df.iloc[0]
        best_algo = best_row["Algorithme"]
        best_acc = best_row["Accuracy (validation croisée)"]
        predictions_df = st.session_state.get(f"training_predictions_{pool_key}", pd.DataFrame())
        if not predictions_df.empty:
            errors_df = predictions_df[(predictions_df["Algorithme"] == best_algo) & (~predictions_df["Correct"])]
            if not errors_df.empty:
                with st.expander(f"Voir les erreurs du meilleur modèle ({len(errors_df)} cas) — {pool['label']}"):
                    render_html_table(errors_df, columns=["Réponse", "Thème réel", "Thème prédit"],
                                       wrap_cols=["Réponse"], max_height=360)
        st.markdown(f"""
        <div class="ai-info-box">
            Meilleur algorithme pour ce groupe : <b>{esc(best_algo)}</b> — précision estimée :
            <b>{round(best_acc * 100, 1)}%</b> sur {len(pool_train_df)} réponses validées.
            Pour les algorithmes à marge (SVM, SGD), la confiance affichée par réponse individuelle lors
            de la classification reste une approximation dérivée de la distance à la frontière de
            décision, non une probabilité calibrée — seule l'accuracy ci-dessus est une mesure
            statistique validée par validation croisée.
        </div>
        """, unsafe_allow_html=True)
        chosen_algo = st.selectbox("Algorithme à activer pour ce groupe",
                                    options=results_df["Algorithme"].tolist(), index=0,
                                    key=f"chosen_algo_{pool_key}")
        if st.button(f"Activer ce modèle — {pool['label']}", key=f"activate_{pool_key}"):
            snapshot = st.session_state.get(f"training_snapshot_{pool_key}", pool_train_df)
            model = train_final_model(snapshot, chosen_algo)
            trained_models[pool_key] = model
            chosen_acc = results_df[results_df["Algorithme"] == chosen_algo]["Accuracy (validation croisée)"].iloc[0]
            trained_accuracies[pool_key] = round(chosen_acc * 100, 1)
            st.session_state["trained_models"] = trained_models
            st.session_state["trained_model_accuracies"] = trained_accuracies
            st.success(f"Modèle activé pour « {pool['label']} » (précision validée : "
                       f"{round(chosen_acc * 100, 1)}%). Retournez à l'onglet 1 et sélectionnez "
                       f"« Modèle supervisé entraîné » pour l'utiliser sur ce groupe.")
            import pickle
            buf = BytesIO()
            pickle.dump(model, buf)
            st.download_button(f"Télécharger ce modèle ({pool['label']})", data=buf.getvalue(),
                                file_name=f"modele_{safe_filename(pool_key)}_{safe_filename(chosen_algo)}.pkl",
                                mime="application/octet-stream", key=f"dl_model_{pool_key}")
    st.markdown("---\n#### Groupes non éligibles au regroupement")
    st.caption("Ces combinaisons type de participant / élément SWOT n'ont pas de partenaire de "
               "regroupement — leur taxonomie officielle interne n'est partagée avec aucun autre type. "
               "Elles restent classifiées par le moteur sémantique tant qu'un volume de données validées "
               "suffisant n'est pas atteint indépendamment pour chacune. Ce n'est pas une limite du code, "
               "c'est une contrainte réelle de vos données : forcer un entraînement ici équivaudrait à "
               "ajuster un modèle sur trop peu d'exemples par thème pour être fiable.")
    non_pooled = full_train_df[full_train_df["training_group"].isna()]
    if not non_pooled.empty:
        summary = non_pooled.groupby(["Respondent_Type", "swot_element"]).size().reset_index(name="Réponses validées")
        st.dataframe(summary, use_container_width=True, hide_index=True)
    else:
        st.caption("Aucune donnée validée pour ces groupes pour le moment.")
    st.markdown("---\n#### Réutiliser un modèle déjà entraîné")
    pool_choice_for_upload = st.selectbox(
        "À quel groupe ce modèle correspond-il ?",
        options=list(TRAINING_POOLS.keys()),
        format_func=lambda k: TRAINING_POOLS[k]["label"],
        key="model_pkl_pool_choice",
    )
    model_upload = st.file_uploader("Charger un fichier de modèle (.pkl)", type=["pkl"], key="model_pkl_upload")
    if model_upload is not None:
        import pickle
        try:
            loaded_model = pickle.load(model_upload)
            trained_models[pool_choice_for_upload] = loaded_model
            trained_accuracies.pop(pool_choice_for_upload, None)
            st.session_state["trained_models"] = trained_models
            st.session_state["trained_model_accuracies"] = trained_accuracies
            st.success(f"Modèle chargé et activé pour « {TRAINING_POOLS[pool_choice_for_upload]['label']} ».")
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
    trained_models_kpi = st.session_state.get("trained_models", {})
    c4.markdown(f'<div class="ai-kpi"><div class="ai-kpi-number">{len(trained_models_kpi)}/{len(TRAINING_POOLS)}</div><div class="ai-kpi-label">Pools de thèmes entraînés</div></div>', unsafe_allow_html=True)
    tab_mapping, tab_training, tab_duplicates, tab_synthesis = st.tabs([
        "1. Classification et validation", "2. Entraîner le modèle", "3. Doublons", "4. Synthèse"
    ])
    with tab_mapping:
        st.subheader("1. Classification et validation experte")
        engine = render_engine_selector(df_scope)
        trained_models = st.session_state.get("trained_models", {})
        # No blocking gate here: resolve_effective_engine (used inside
        # build_classification_dataframe) automatically and visibly falls
        # back to the semantic engine, per (participant type, SWOT element),
        # for any combination whose pool isn't trained yet or has no pooling
        # partner at all. Classification is therefore always available.
        if st.button("Classifier les réponses SWOT", key="run_mapping"):
            with st.spinner("Classification en cours..."):
                st.session_state["classified_df"] = build_classification_dataframe(df_scope, engine, trained_models)
        classified_df = st.session_state.get("classified_df", pd.DataFrame())
        if not classified_df.empty:
            engine_counts = classified_df["Engine_Used"].value_counts().to_dict()
            engine_summary = " · ".join(f"{v} via {k.replace('Modèle supervisé entraîné - recommandé pour la précision', 'le modèle entraîné').replace('Moteur sémantique institutionnel - taxonomie + ontologie + embeddings locaux', 'le moteur sémantique')}" for k, v in engine_counts.items())
            st.caption(f"Moteur utilisé pour ces {len(classified_df)} réponses : {engine_summary}. "
                       "(Détail par réponse disponible dans l'export Excel et dans l'onglet de validation ci-dessous.)")
            preview_df = classified_df[
                ["Respondent_Type", "groupe", "swot_element", "Final_Answer", "AI_Suggested_Theme", "Confidence"]
            ].rename(columns={"Confidence": "Score / Confiance (%)"})
            render_html_table(preview_df, wrap_cols=["Final_Answer", "AI_Suggested_Theme"])
            with st.expander("Vue tableau triable (grille interactive)"):
                st.dataframe(preview_df, use_container_width=True)
            validated_df = render_mapping_validation(classified_df)
            if not validated_df.empty:
                st.session_state["validated_mapping_df"] = validated_df
                export_cols = ["Respondent_Type", "groupe", "participants", "swot_element", "question",
                                "Final_Answer", "AI_Suggested_Theme", "Confidence", "Engine_Used",
                                "Validated_Theme", "New_Theme"]
                export_df = validated_df[[c for c in export_cols if c in validated_df.columns]].copy()
                export_df = export_df.rename(columns={"Confidence": "Score / Confiance (%)", "Engine_Used": "Moteur utilisé"})
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
                   "similaire avec un sujet différent n'est pas retenue. Les seuils utilisés sont "
                   "heuristiques et n'ont pas été validés contre un jeu de doublons annotés manuellement : "
                   "traitez les paires détectées comme des suggestions à vérifier, pas comme un résultat "
                   "certain.")
        if st.button("Détecter les doublons", key="detect_duplicates"):
            st.session_state["duplicates_df"] = detect_duplicate_pairs(df_scope)
        dup_df = st.session_state.get("duplicates_df", pd.DataFrame())
        if not dup_df.empty:
            render_html_table(dup_df, wrap_cols=["Réponse 1", "Réponse 2"])
            with st.expander("Vue tableau triable (grille interactive)"):
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
