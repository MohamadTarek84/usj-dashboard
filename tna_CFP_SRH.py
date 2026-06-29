import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import json
from datetime import datetime
import pandas as pd
import os
import base64
import textwrap
from io import BytesIO
import plotly.express as px

from pathlib import Path
import os

if os.path.exists("/home/site"):
    DB_DIR = Path("/home/data")   # Azure App Service
else:
    DB_DIR = Path(".")            # Streamlit Cloud / local

DB_DIR.mkdir(parents=True, exist_ok=True)

DB_NAME = str(DB_DIR / "tna_demo.db")

USJ_BLUE = "#001F5B"
USJ_RED = "#8B1538"
USJ_GOLD = "#C9A227"
USJ_TEXT = "#1B2A41"
USJ_LIGHT_BLUE = "#EAF2F8"

CFP_LOGO_PATH = "CFP LOGO.png"
USJ_LOGO_PATH = "USJ LOGO 150.png"


PSG_THEMES = [
    "Communication constructive",
    "Résolution de conflits",
    "Intelligence interpersonnelle",
    "Diversité culturelle",
    "Collaboration",
    "Communication écrite",
    "Communication orale",
    "Public speaking and Body language",
    "Santé mentale",
    "Bien-être au travail",
    "Intelligence émotionnelle",
    "Gestion du stress",
    "Gestion du temps",
    "Mindfulness",
    "Team building",
    "Inclusion",
    "Harcèlement",
    "Branding",
    "Création de contenu-Réseaux sociaux",
    "Outils intelligence artificielle",
    "Bureautique-Word",
    "Bureautique-Excel",
    "Bureautique-PowerPoint",
    "Gestion financière",
    "Gestion du changement en milieu universitaire",
    "Gestion de projets",
    "Équilibre vie professionnelle vie personnelle",
    "Ergonomie",
    "Customer service"
]

DD_LEADER_THEMES = [
    "Outils intelligence artificielle-IA",
    "Agile management",
    "Strategic decision making",
    "Gestion budgétaire",
    "Gestion financière",
    "Digital marketing",
    "Change management in academic institutions",
    "Crisis management and institutional resilience",
    "Data-driven decision making",
    "Résolution de conflits",
    "Public speaking and Body language",
    "Bien-être au travail",
    "Gestion du stress",
    "Team building",
    "Inclusion",
    "Harcèlement",
    "Branding",
    "Création de contenu-Réseaux sociaux",
    "Gestion financière",
    "Gestion du changement en milieu universitaire",
    "Gestion de projets (bases pour non-chefs de projet)",
    "Équilibre vie professionnelle vie personnelle",
    "Customer service (dealing with students/staff)"

]


# =====================================================
# USERS DEFINED DIRECTLY IN CODE
# =====================================================
# Source: users.xlsx converted into a Python dictionary.
# No Excel reading is required at runtime.


def clean_login_value(value):
    if value is None:
        return ""
    value = str(value).strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value.upper()


def login_variants(value):
    value = clean_login_value(value)
    values = {value}
    if "@" in value:
        values.add(value.split("@", 1)[0])
    elif value:
        values.add(value + "@USJ.EDU.LB")
        values.add(value + "@USJ.EDU")
    return {v for v in values if v}


DEMO_USERS = {'716920': {'ldap': '716920',
            'code': '716920',
            'role': 'psg',
            'name': 'Bilal CHEHAB',
            'poste': "Agent de propreté et d'hygiène",
            'faculty': 'CZB',
            'institution': 'CZB',
            'department': '',
            'email': 'bilal.chehab@usj.edu.lb',
            'director_name': 'Ali (Alain) AJAMI (EL)',
            'director_code': '711811',
            'director_ldap': '711811',
            'director_email': 'alain.ajami@usj.edu.lb'},
 '711811': {'ldap': '711811',
            'code': '711811',
            'role': 'director',
            'name': 'Ali (Alain) AJAMI (EL)',
            'poste': 'Directeur du Campus de Zahlé et de la Békaa',
            'faculty': 'CZB',
            'institution': 'CZB',
            'department': '',
            'email': 'alain.ajami@usj.edu.lb'},
 '703405': {'ldap': '703405',
            'code': '703405',
            'role': 'psg',
            'name': 'Souad HAJJAR',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'CZB',
            'institution': 'CZB',
            'department': '',
            'email': 'souad.hajjar@usj.edu.lb',
            'director_name': 'Ali (Alain) AJAMI (EL)',
            'director_code': '711811',
            'director_ldap': '711811',
            'director_email': 'alain.ajami@usj.edu.lb'},
 '719142': {'ldap': '719142',
            'code': '719142',
            'role': 'psg',
            'name': 'Zeina KARAKI DARWICH',
            'poste': 'Chargé de support administratif',
            'faculty': 'CZB',
            'institution': 'CZB',
            'department': '',
            'email': 'zeina.karaki2@usj.edu.lb',
            'director_name': 'Ali (Alain) AJAMI (EL)',
            'director_code': '711811',
            'director_ldap': '711811',
            'director_email': 'alain.ajami@usj.edu.lb'},
 '716598': {'ldap': '716598',
            'code': '716598',
            'role': 'psg',
            'name': 'Fadi NASSAR',
            'poste': "Agent de maintenance et d'entretien",
            'faculty': 'CZB',
            'institution': 'CZB',
            'department': '',
            'email': 'fadi.nassar@usj.edu.lb',
            'director_name': 'Ali (Alain) AJAMI (EL)',
            'director_code': '711811',
            'director_ldap': '711811',
            'director_email': 'alain.ajami@usj.edu.lb'},
 '706502': {'ldap': '706502',
            'code': '706502',
            'role': 'psg',
            'name': 'Talaat SAHLI (AL)',
            'poste': "Agent de propreté et d'hygiène",
            'faculty': 'CZB',
            'institution': 'CZB',
            'department': '',
            'email': 'talaat.sahli@usj.edu.lb',
            'director_name': 'Ali (Alain) AJAMI (EL)',
            'director_code': '711811',
            'director_ldap': '711811',
            'director_email': 'alain.ajami@usj.edu.lb'},
 '710303': {'ldap': '710303',
            'code': '710303',
            'role': 'psg',
            'name': 'Samir ABI WAKIM',
            'poste': 'Technicien',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'samir.abiwakim@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '716874': {'ldap': '716874',
            'code': '716874',
            'role': 'director',
            'name': 'Antoine NAHHAS (EL)',
            'poste': 'Administrateur du Campus des sciences et technologies',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'antoine.nahhas@usj.edu.lb'},
 '700291': {'ldap': '700291',
            'code': '700291',
            'role': 'psg',
            'name': 'Khaled ABOU ABBOUD',
            'poste': 'Technicien - plomberie',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'khaled.abouabboud@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '718033': {'ldap': '718033',
            'code': '718033',
            'role': 'psg',
            'name': 'Jad ABOU KHALIL',
            'poste': 'Surveillant de site',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'jad.aboukhalil@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '718028': {'ldap': '718028',
            'code': '718028',
            'role': 'psg',
            'name': 'Pierre BEJJANI',
            'poste': 'Surveillant de site',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'pierre.bejjani@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '717027': {'ldap': '717027',
            'code': '717027',
            'role': 'psg',
            'name': 'Elias BOU ABSI',
            'poste': 'Technicien',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'elias.bouabsi@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '711493': {'ldap': '711493',
            'code': '711493',
            'role': 'psg',
            'name': 'Georges DAOUD',
            'poste': 'Technicien spécialisé',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'georges.daoud@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '702939': {'ldap': '702939',
            'code': '702939',
            'role': 'psg',
            'name': 'Rita GERMANY GERMANY (EL)',
            'poste': 'Bibliothécaire spécialisé',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'rita.germany@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '710927': {'ldap': '710927',
            'code': '710927',
            'role': 'psg',
            'name': 'Dani HADCHITI',
            'poste': 'Agent de sécurité',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'dani.hadchiti@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '717113': {'ldap': '717113',
            'code': '717113',
            'role': 'psg',
            'name': 'Nabil HADCHITY',
            'poste': 'Agent de sécurité',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'nabil.hadchity@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '704164': {'ldap': '704164',
            'code': '704164',
            'role': 'psg',
            'name': 'Elias KARAA',
            'poste': 'Coursier-Chauffeur',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'elias.karaa@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '717087': {'ldap': '717087',
            'code': '717087',
            'role': 'psg',
            'name': 'Salim KAZAN',
            'poste': "Agent de maintenance et d'entretien",
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'salim.kazan@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '704356': {'ldap': '704356',
            'code': '704356',
            'role': 'psg',
            'name': 'Leila KEYROUZ',
            'poste': 'Bibliothécaire spécialisé',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'leila.keyrouz@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '704507': {'ldap': '704507',
            'code': '704507',
            'role': 'psg',
            'name': 'Gerges KHAWAND (EL)',
            'poste': 'Intendant de campus',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'gerges.khawand@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '718958': {'ldap': '718958',
            'code': '718958',
            'role': 'psg',
            'name': 'Johnny KHAWAND (EL)',
            'poste': 'Technicien spécialisé',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'jhonny.khawand@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '705156': {'ldap': '705156',
            'code': '705156',
            'role': 'psg',
            'name': 'Bachar MASSOUD',
            'poste': 'Technicien spécialisé',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'bachar.massoud@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '708843': {'ldap': '708843',
            'code': '708843',
            'role': 'psg',
            'name': 'Jean MONDALEK',
            'poste': 'Agent de sécurité',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'jean.mondalek@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '717345': {'ldap': '717345',
            'code': '717345',
            'role': 'psg',
            'name': 'Roudy MRAD',
            'poste': 'Agent administratif',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'roudy.mrad1@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '705753': {'ldap': '705753',
            'code': '705753',
            'role': 'psg',
            'name': 'Raghida NASR NAWFAL',
            'poste': 'Directeur de bibliothèque',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'raghida.nawfal@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '709907': {'ldap': '709907',
            'code': '709907',
            'role': 'psg',
            'name': 'Boulos RIZK',
            'poste': 'Technicien spécialisé',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'boulos.rizk@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '706507': {'ldap': '706507',
            'code': '706507',
            'role': 'psg',
            'name': 'Rita SAHYOUNI HENEINEH',
            'poste': 'Secrétaire de campus',
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'rita.honeine@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '717697': {'ldap': '717697',
            'code': '717697',
            'role': 'psg',
            'name': 'Youssef TANNOUS',
            'poste': "Agent de maintenance et d'entretien",
            'faculty': 'CST',
            'institution': 'CST',
            'department': '',
            'email': 'youssef.tannous@usj.edu.lb',
            'director_name': 'Antoine NAHHAS (EL)',
            'director_code': '716874',
            'director_ldap': '716874',
            'director_email': 'antoine.nahhas@usj.edu.lb'},
 '711238': {'ldap': '711238',
            'code': '711238',
            'role': 'psg',
            'name': 'Ralph AYOUB',
            'poste': "Assistant technique de recherche et d'imagerie médicale",
            'faculty': 'LBIM',
            'institution': 'LBIM',
            'department': '',
            'email': 'ralph.ayoub@usj.edu.lb',
            'director_name': 'Ayman ASSI',
            'director_code': '700780',
            'director_ldap': '700780',
            'director_email': 'ayman.assi@usj.edu.lb'},
 '700780': {'ldap': '700780',
            'code': '700780',
            'role': 'director',
            'name': 'Ayman ASSI',
            'poste': "Directeur du Laboratoire de Biomécanique et d'imagerie médicale",
            'faculty': 'LBIM',
            'institution': 'LBIM',
            'department': '',
            'email': 'ayman.assi@usj.edu.lb'},
 '703541': {'ldap': '703541',
            'code': '703541',
            'role': 'psg',
            'name': 'Aline HARFOUCHE ABI TAYEH',
            'poste': 'Chargé de la mobilité estudiantine et des conventions internationales',
            'faculty': 'VRRI',
            'institution': 'VRRI',
            'department': '',
            'email': 'aline.harfouche@usj.edu.lb',
            'director_name': 'Carla EDDE',
            'director_code': '702496',
            'director_ldap': '702496',
            'director_email': 'carla.edde@usj.edu.lb'},
 '702496': {'ldap': '702496',
            'code': '702496',
            'role': 'director',
            'name': 'Carla EDDE',
            'poste': 'Vice-Recteur aux Vice-rectorat aux relations internationales',
            'faculty': 'VRRI',
            'institution': 'VRRI',
            'department': '',
            'email': 'carla.edde@usj.edu.lb'},
 '715650': {'ldap': '715650',
            'code': '715650',
            'role': 'psg',
            'name': 'Elie HAYEK (EL)',
            'poste': 'Chargé du suivi des projets internationaux',
            'faculty': 'VRRI',
            'institution': 'VRRI',
            'department': '',
            'email': 'elie.hayek1@usj.edu.lb',
            'director_name': 'Carla EDDE',
            'director_code': '702496',
            'director_ldap': '702496',
            'director_email': 'carla.edde@usj.edu.lb'},
 '716931': {'ldap': '716931',
            'code': '716931',
            'role': 'psg',
            'name': 'Rana KANAAN SAFI',
            'poste': 'Chargé de la mobilité estudiantine et des projets internationaux',
            'faculty': 'VRRI',
            'institution': 'VRRI',
            'department': '',
            'email': 'rana.kanaan1@usj.edu.lb',
            'director_name': 'Carla EDDE',
            'director_code': '702496',
            'director_ldap': '702496',
            'director_email': 'carla.edde@usj.edu.lb'},
 '707528': {'ldap': '707528',
            'code': '707528',
            'role': 'psg',
            'name': 'Gladys ZEIN HAYEK (EL)',
            'poste': 'Coordinateur administratif des relations internationales',
            'faculty': 'VRRI',
            'institution': 'VRRI',
            'department': '',
            'email': 'gladys.zein@usj.edu.lb',
            'director_name': 'Carla EDDE',
            'director_code': '702496',
            'director_ldap': '702496',
            'director_email': 'carla.edde@usj.edu.lb'},
 '702953': {'ldap': '702953',
            'code': '702953',
            'role': 'psg',
            'name': 'Suzanne GHAFARY',
            'poste': 'Chargé de support académique',
            'faculty': 'IET',
            'institution': 'IET',
            'department': '',
            'email': 'suzanne.ghafary@usj.edu.lb',
            'director_name': 'Carla MATTA ABI ZEID',
            'director_code': '705197',
            'director_ldap': '705197',
            'director_email': 'carla.abizeid@usj.edu.lb'},
 '705197': {'ldap': '705197',
            'code': '705197',
            'role': 'director',
            'name': 'Carla MATTA ABI ZEID',
            'poste': "Directrice de l' Institut d'ergothérapie",
            'faculty': 'IET',
            'institution': 'IET',
            'department': '',
            'email': 'carla.abizeid@usj.edu.lb'},
 '718648': {'ldap': '718648',
            'code': '718648',
            'role': 'psg',
            'name': 'Ghada KHATER NAKHLE',
            'poste': 'Agent administratif',
            'faculty': 'IET',
            'institution': 'IET',
            'department': '',
            'email': 'ghada.khater@usj.edu.lb',
            'director_name': 'Carla MATTA ABI ZEID',
            'director_code': '705197',
            'director_ldap': '705197',
            'director_email': 'carla.abizeid@usj.edu.lb'},
 '702097': {'ldap': '702097',
            'code': '702097',
            'role': 'psg',
            'name': 'Rola COPTI GERMANOS',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'IPM',
            'institution': 'IPM',
            'department': '',
            'email': 'roula.germanos@usj.edu.lb',
            'director_name': 'Céleste YOUNES HARB',
            'director_code': '707429',
            'director_ldap': '707429',
            'director_email': 'celeste.younes@usj.edu.lb'},
 '707429': {'ldap': '707429',
            'code': '707429',
            'role': 'director',
            'name': 'Céleste YOUNES HARB',
            'poste': "Directrice de l' Institut de psychomotricité",
            'faculty': 'IPM',
            'institution': 'IPM',
            'department': '',
            'email': 'celeste.younes@usj.edu.lb'},
 '715008': {'ldap': '715008',
            'code': '715008',
            'role': 'psg',
            'name': 'Antoinette HATEM BEJJANI',
            'poste': 'Chargé de support académique',
            'faculty': 'IPM',
            'institution': 'IPM',
            'department': '',
            'email': 'antoinette.hatem1@usj.edu.lb',
            'director_name': 'Céleste YOUNES HARB',
            'director_code': '707429',
            'director_ldap': '707429',
            'director_email': 'celeste.younes@usj.edu.lb'},
 '710615': {'ldap': '710615',
            'code': '710615',
            'role': 'psg',
            'name': 'Renée KASSIS CHAMOUN',
            'poste': 'Chargé de support administratif - centre de soins',
            'faculty': 'IPM',
            'institution': 'IPM',
            'department': '',
            'email': 'renee.kassischamoun@usj.edu.lb',
            'director_name': 'Céleste YOUNES HARB',
            'director_code': '707429',
            'director_ldap': '707429',
            'director_email': 'celeste.younes@usj.edu.lb'},
 '714547': {'ldap': '714547',
            'code': '714547',
            'role': 'psg',
            'name': 'Hind FAYAD GERGES',
            'poste': 'Agent de stock',
            'faculty': 'IGE',
            'institution': 'IGE',
            'department': '',
            'email': 'hind.fayad1@usj.edu.lb',
            'director_name': 'Céline BOUTROS SAAB',
            'director_code': '709180',
            'director_ldap': '709180',
            'director_email': 'celine.boutrossaab@usj.edu.lb'},
 '709180': {'ldap': '709180',
            'code': '709180',
            'role': 'director',
            'name': 'Céline BOUTROS SAAB',
            'poste': "Directrice de l' Institut de gestion des entreprises",
            'faculty': 'IGE',
            'institution': 'IGE',
            'department': '',
            'email': 'celine.boutrossaab@usj.edu.lb'},
 '703874': {'ldap': '703874',
            'code': '703874',
            'role': 'psg',
            'name': 'Mony ISKANDAR DORO',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'IGE',
            'institution': 'IGE',
            'department': '',
            'email': 'mony.doro@usj.edu.lb',
            'director_name': 'Céline BOUTROS SAAB',
            'director_code': '709180',
            'director_ldap': '709180',
            'director_email': 'celine.boutrossaab@usj.edu.lb'},
 '707319': {'ldap': '707319',
            'code': '707319',
            'role': 'psg',
            'name': 'Maryam WEHBE KARATI',
            'poste': 'Agent administratif',
            'faculty': 'IGE',
            'institution': 'IGE',
            'department': '',
            'email': 'maryam.karati@usj.edu.lb',
            'director_name': 'Céline BOUTROS SAAB',
            'director_code': '709180',
            'director_ldap': '709180',
            'director_email': 'celine.boutrossaab@usj.edu.lb'},
 '700592': {'ldap': '700592',
            'code': '700592',
            'role': 'psg',
            'name': 'Maria-Pia AKIKI BOUTROS',
            'poste': 'Bibliothécaire',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'pia.akiki@usj.edu.lb',
            'director_name': 'Chantal HABIS (EL) SFEIR',
            'director_code': '712552',
            'director_ldap': '712552',
            'director_email': 'chantal.sfeir@usj.edu.lb'},
 '712552': {'ldap': '712552',
            'code': '712552',
            'role': 'director',
            'name': 'Chantal HABIS (EL) SFEIR',
            'poste': 'Directeur de la bibliothèque du  Campus des sciences humaines',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'chantal.sfeir@usj.edu.lb'},
 '701971': {'ldap': '701971',
            'code': '701971',
            'role': 'psg',
            'name': 'Jocelyne CHEMALY',
            'poste': 'Bibliothécaire spécialisé',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'jocelyne.chemaly@usj.edu.lb',
            'director_name': 'Chantal HABIS (EL) SFEIR',
            'director_code': '712552',
            'director_ldap': '712552',
            'director_email': 'chantal.sfeir@usj.edu.lb'},
 '702264': {'ldap': '702264',
            'code': '702264',
            'role': 'psg',
            'name': 'Pierre DAOU',
            'poste': 'Bibliothécaire-adjoint',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'pierre.daou@usj.edu.lb',
            'director_name': 'Chantal HABIS (EL) SFEIR',
            'director_code': '712552',
            'director_ldap': '712552',
            'director_email': 'chantal.sfeir@usj.edu.lb'},
 '703307': {'ldap': '703307',
            'code': '703307',
            'role': 'psg',
            'name': 'Gladys HADDAD SALIBA',
            'poste': 'Bibliothécaire',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'gladys.saliba@usj.edu.lb',
            'director_name': 'Chantal HABIS (EL) SFEIR',
            'director_code': '712552',
            'director_ldap': '712552',
            'director_email': 'chantal.sfeir@usj.edu.lb'},
 '704406': {'ldap': '704406',
            'code': '704406',
            'role': 'psg',
            'name': 'Nicole KHAIRALLAH',
            'poste': 'Bibliothécaire de référence',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'nicole.khairallah@usj.edu.lb',
            'director_name': 'Chantal HABIS (EL) SFEIR',
            'director_code': '712552',
            'director_ldap': '712552',
            'director_email': 'chantal.sfeir@usj.edu.lb'},
 '716735': {'ldap': '716735',
            'code': '716735',
            'role': 'psg',
            'name': 'Christine SABA CHOUEIRI (EL)',
            'poste': 'Bibliothécaire spécialisé',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'christine.saba@usj.edu.lb',
            'director_name': 'Chantal HABIS (EL) SFEIR',
            'director_code': '712552',
            'director_ldap': '712552',
            'director_email': 'chantal.sfeir@usj.edu.lb'},
 '702371': {'ldap': '702371',
            'code': '702371',
            'role': 'psg',
            'name': 'Virginia DERGASPARD EL KHOURY',
            'poste': 'Coordinateur administratif',
            'faculty': 'CUE',
            'institution': 'CUE',
            'department': '',
            'email': 'virginia.elkhoury@usj.edu.lb',
            'director_name': 'Charbel BATOUR s.j.',
            'director_code': '708659',
            'director_ldap': '708659',
            'director_email': 'charbel.batour@usj.edu.lb'},
 '708659': {'ldap': '708659',
            'code': '708659',
            'role': 'director',
            'name': 'Charbel BATOUR s.j.',
            'poste': "Directeur du Centre universitaire d'éthique",
            'faculty': 'CUE',
            'institution': 'CUE',
            'department': '',
            'email': 'charbel.batour@usj.edu.lb'},
 '716418': {'ldap': '716418',
            'code': '716418',
            'role': 'psg',
            'name': 'Sabine ALAMEH',
            'poste': 'Chargé (e) de communication rédactionnelle',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'sabine.alameh1@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '705970': {'ldap': '705970',
            'code': '705970',
            'role': 'director',
            'name': 'Christine OMEIRA WAZEN',
            'poste': 'Directeur du service des publications et de la communication',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'christine.omeira@usj.edu.lb'},
 '710971': {'ldap': '710971',
            'code': '710971',
            'role': 'psg',
            'name': 'Maria BASSILA HABCHI',
            'poste': "Coordinateur de l'évènementiel",
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'maria.habchi@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '710675': {'ldap': '710675',
            'code': '710675',
            'role': 'psg',
            'name': 'Murielle CHAHINE TOBY',
            'poste': 'Graphiste senior',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'murielle.chahine@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '716969': {'ldap': '716969',
            'code': '716969',
            'role': 'psg',
            'name': 'Christiane CHAMOUN',
            'poste': 'Correcteur - rédacteur',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'christiane.chamoun@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '702161': {'ldap': '702161',
            'code': '702161',
            'role': 'psg',
            'name': 'Aline DAGHER BACHIR',
            'poste': 'Directeur adjoint - communication numérique',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'aline.dagher@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '711182': {'ldap': '711182',
            'code': '711182',
            'role': 'psg',
            'name': 'Nada EID TAYARA (EL)',
            'poste': 'Coordinateur de communication rédactionnelle',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'nada.eid2@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '719543': {'ldap': '719543',
            'code': '719543',
            'role': 'psg',
            'name': 'Marc FAYAD',
            'poste': 'Vidéographe',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'marc.fayad1@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '715159': {'ldap': '715159',
            'code': '715159',
            'role': 'psg',
            'name': 'Marilyn FEGHALI',
            'poste': 'Rédacteur - Traducteur senior',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'marilyn.feghali1@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '707915': {'ldap': '707915',
            'code': '707915',
            'role': 'psg',
            'name': 'Roger HADDAD',
            'poste': 'Coordinateur de communication rédactionnelle',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'roger.haddad@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '717014': {'ldap': '717014',
            'code': '717014',
            'role': 'psg',
            'name': 'Nathaly HAWAWINI DIT KHOURY ASSAF',
            'poste': 'Community Manager',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'nathaly.assaf@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '718723': {'ldap': '718723',
            'code': '718723',
            'role': 'psg',
            'name': 'Yorgo KAAZAN',
            'poste': 'Développeur "Full Stack"',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'yorgo.kazan@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '704142': {'ldap': '704142',
            'code': '704142',
            'role': 'psg',
            'name': 'Cynthia KENAAN',
            'poste': 'Rédacteur - Traducteur',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'cynthia.kenaan1@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '717017': {'ldap': '717017',
            'code': '717017',
            'role': 'psg',
            'name': 'Rim KFOURY',
            'poste': 'Designer UX',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'rim.kfoury@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '718379': {'ldap': '718379',
            'code': '718379',
            'role': 'psg',
            'name': 'Elise KIWAN MASSOUD',
            'poste': 'Coordinateur de communication',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'elise.kiwan1@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '716966': {'ldap': '716966',
            'code': '716966',
            'role': 'psg',
            'name': 'Jenifer NASSAR',
            'poste': 'Concepteur et animateur vidéos',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'jennifer.nassar1@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '718440': {'ldap': '718440',
            'code': '718440',
            'role': 'psg',
            'name': 'Christy NEHME',
            'poste': 'Graphiste',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'christy.nehme@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '706692': {'ldap': '706692',
            'code': '706692',
            'role': 'psg',
            'name': 'Marianne SAMRA (EL) AOUAD',
            'poste': 'Graphiste senior',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'marianne.samra@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '706771': {'ldap': '706771',
            'code': '706771',
            'role': 'psg',
            'name': 'Christia SAYEGH',
            'poste': 'coordinateur des ressources numériques',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'christia.sayegh@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '707144': {'ldap': '707144',
            'code': '707144',
            'role': 'psg',
            'name': 'Carine TOHME HADDAD',
            'poste': 'Directeur adjoint - Design et Image',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'carine.tohme@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '716140': {'ldap': '716140',
            'code': '716140',
            'role': 'psg',
            'name': 'Hened ZADEH BARADHY',
            'poste': 'Concepteur et animateur vidéos',
            'faculty': 'SPCOM',
            'institution': 'SPCOM',
            'department': '',
            'email': 'hened.zadeh@usj.edu.lb',
            'director_name': 'Christine OMEIRA WAZEN',
            'director_code': '705970',
            'director_ldap': '705970',
            'director_email': 'christine.omeira@usj.edu.lb'},
 '711161': {'ldap': '711161',
            'code': '711161',
            'role': 'psg',
            'name': 'Katia BACHA (EL)',
            'poste': 'Responsable communication et relations donateurs',
            'faculty': 'FONDUSJ',
            'institution': 'FONDUSJ',
            'department': '',
            'email': 'katia.bacha@usj.edu.lb',
            'director_name': 'Cynthia-Maria GHOBRIL ANDREA',
            'director_code': '703029',
            'director_ldap': '703029',
            'director_email': 'cynthia.ghobril@usj.edu.lb'},
 '703029': {'ldap': '703029',
            'code': '703029',
            'role': 'director',
            'name': 'Cynthia-Maria GHOBRIL ANDREA',
            'poste': 'Directeur de la "Fondation USJ"',
            'faculty': 'FONDUSJ',
            'institution': 'FONDUSJ',
            'department': '',
            'email': 'cynthia.ghobril@usj.edu.lb'},
 '717185': {'ldap': '717185',
            'code': '717185',
            'role': 'psg',
            'name': 'Nayla BOU FADEL EL HELOU HADDAD',
            'poste': 'Analyste des donations et des bases de données',
            'faculty': 'FONDUSJ',
            'institution': 'FONDUSJ',
            'department': '',
            'email': 'nayla.boufadelelhelou@usj.edu.lb',
            'director_name': 'Cynthia-Maria GHOBRIL ANDREA',
            'director_code': '703029',
            'director_ldap': '703029',
            'director_email': 'cynthia.ghobril@usj.edu.lb'},
 '713033': {'ldap': '713033',
            'code': '713033',
            'role': 'psg',
            'name': 'Elise KHOURY YAMMINE',
            'poste': 'Gestionnaire des opérations',
            'faculty': 'FONDUSJ',
            'institution': 'FONDUSJ',
            'department': '',
            'email': 'elise.khoury@usj.edu.lb',
            'director_name': 'Cynthia-Maria GHOBRIL ANDREA',
            'director_code': '703029',
            'director_ldap': '703029',
            'director_email': 'cynthia.ghobril@usj.edu.lb'},
 '716344': {'ldap': '716344',
            'code': '716344',
            'role': 'psg',
            'name': 'Christina-Maria LOUCA',
            'poste': 'Coordinateur des projets et partenariat',
            'faculty': 'FONDUSJ',
            'institution': 'FONDUSJ',
            'department': '',
            'email': 'christina-maria.louca@usj.edu.lb',
            'director_name': 'Cynthia-Maria GHOBRIL ANDREA',
            'director_code': '703029',
            'director_ldap': '703029',
            'director_email': 'cynthia.ghobril@usj.edu.lb'},
 '717399': {'ldap': '717399',
            'code': '717399',
            'role': 'psg',
            'name': 'Marwan MINA',
            'poste': "Gestionnaire des donations et mécénat à l'HDF",
            'faculty': 'FONDUSJ',
            'institution': 'FONDUSJ',
            'department': '',
            'email': 'marwan.mina@usj.edu.lb',
            'director_name': 'Cynthia-Maria GHOBRIL ANDREA',
            'director_code': '703029',
            'director_ldap': '703029',
            'director_email': 'cynthia.ghobril@usj.edu.lb'},
 '715974': {'ldap': '715974',
            'code': '715974',
            'role': 'psg',
            'name': 'Arzé YAZBECK MNEIMNEH',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'FONDUSJ',
            'institution': 'FONDUSJ',
            'department': '',
            'email': 'arze.yazbeck@usj.edu.lb',
            'director_name': 'Cynthia-Maria GHOBRIL ANDREA',
            'director_code': '703029',
            'director_ldap': '703029',
            'director_email': 'cynthia.ghobril@usj.edu.lb'},
 '701067': {'ldap': '701067',
            'code': '701067',
            'role': 'psg',
            'name': 'Bassem AZIZ',
            'poste': 'Agent administratif',
            'faculty': 'CLS',
            'institution': 'CLS',
            'department': '',
            'email': 'bassem.aziz@usj.edu.lb',
            'director_name': 'Dina SIDANI',
            'director_code': '708919',
            'director_ldap': '708919',
            'director_email': 'dina.sidani@usj.edu.lb'},
 '708919': {'ldap': '708919',
            'code': '708919',
            'role': 'director',
            'name': 'Dina SIDANI',
            'poste': 'Directrice du Campus du Liban Sud - R.P. André Masse s.j.',
            'faculty': 'CLS',
            'institution': 'CLS',
            'department': '',
            'email': 'dina.sidani@usj.edu.lb'},
 '713931': {'ldap': '713931',
            'code': '713931',
            'role': 'psg',
            'name': 'Dania EZZEDDINE ABBAS',
            'poste': 'Chargé de support académique',
            'faculty': 'CLS',
            'institution': 'CLS',
            'department': '',
            'email': 'dania.ezzeddine@usj.edu.lb',
            'director_name': 'Dina SIDANI',
            'director_code': '708919',
            'director_ldap': '708919',
            'director_email': 'dina.sidani@usj.edu.lb'},
 '713386': {'ldap': '713386',
            'code': '713386',
            'role': 'psg',
            'name': 'Latifa HANNA AJRAM',
            'poste': 'Chargé de support académique',
            'faculty': 'CLS',
            'institution': 'CLS',
            'department': '',
            'email': 'latifa.hanna@usj.edu.lb',
            'director_name': 'Dina SIDANI',
            'director_code': '708919',
            'director_ldap': '708919',
            'director_email': 'dina.sidani@usj.edu.lb'},
 '719260': {'ldap': '719260',
            'code': '719260',
            'role': 'psg',
            'name': 'Mohammad ABDEL HADI',
            'poste': 'Agent de laboratoire',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'mohammad.abdelhadi@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '705889': {'ldap': '705889',
            'code': '705889',
            'role': 'director',
            'name': 'Elie NEMER',
            'poste': 'Doyen de la  Faculté de médecine',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'elie.nemer@usj.edu.lb'},
 '700238': {'ldap': '700238',
            'code': '700238',
            'role': 'psg',
            'name': 'Mireille ABI RACHED KASSIS HARB',
            'poste': 'Chargé de support académique',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'mireille.harb@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '711295': {'ldap': '711295',
            'code': '711295',
            'role': 'psg',
            'name': 'Bachir ATALLAH',
            'poste': 'Statisticien',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'bachir.atallah1@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '713817': {'ldap': '713817',
            'code': '713817',
            'role': 'psg',
            'name': 'Anna-Maria BARAMILI',
            'poste': 'Assistant de laboratoire',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'anna-maria.baramili1@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '718220': {'ldap': '718220',
            'code': '718220',
            'role': 'psg',
            'name': 'May BARK',
            'poste': 'Assistant de laboratoire',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'may.bark@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '716311': {'ldap': '716311',
            'code': '716311',
            'role': 'psg',
            'name': 'Carine BOU ABDO',
            'poste': 'Chargé de communication',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'carine.bouabdo1@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '718373': {'ldap': '718373',
            'code': '718373',
            'role': 'psg',
            'name': 'Mariana BOU SLEIMAN ABOU KHALIL',
            'poste': "Agent d'accueil",
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'mariana.bousleiman@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '707803': {'ldap': '707803',
            'code': '707803',
            'role': 'psg',
            'name': 'Camélia BOUALEG',
            'poste': 'Chargé de support administratif',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'camelia.boualeg@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '708368': {'ldap': '708368',
            'code': '708368',
            'role': 'psg',
            'name': 'Rania CHAAYA',
            'poste': 'Chargé de support administratif',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'rania.chaaya@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '717613': {'ldap': '717613',
            'code': '717613',
            'role': 'psg',
            'name': 'Thérèse CHALHOUB ABI AAD',
            'poste': 'Chargé de support administratif',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'therese.chalhoub@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '716670': {'ldap': '716670',
            'code': '716670',
            'role': 'psg',
            'name': 'Elizabeth CHARBACHI',
            'poste': 'Chargé de support administratif',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'elizabeth.charbachi@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '701946': {'ldap': '701946',
            'code': '701946',
            'role': 'psg',
            'name': 'Michel CHEHWAN',
            'poste': 'Technicien spécialisé',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'michel.chehwan@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '716143': {'ldap': '716143',
            'code': '716143',
            'role': 'psg',
            'name': 'Madonna CHREIM KMEID',
            'poste': 'Chargé de support académique',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'madonna.chreim@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '718096': {'ldap': '718096',
            'code': '718096',
            'role': 'psg',
            'name': 'Luna DIB',
            'poste': 'Technicien de laboratoire',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'luna.dib@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '703445': {'ldap': '703445',
            'code': '703445',
            'role': 'psg',
            'name': 'Fériale HALAWJI YAZBECK',
            'poste': 'Assistant du doyen',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'feriale.yazbeck@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '716042': {'ldap': '716042',
            'code': '716042',
            'role': 'psg',
            'name': 'Nancy HOBEIKA',
            'poste': 'Chargé de support académique',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'nancy.hobeika@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '710135': {'ldap': '710135',
            'code': '710135',
            'role': 'psg',
            'name': 'Mona KARAM',
            'poste': 'Chargé de support administratif',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'mona.karam@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '719344': {'ldap': '719344',
            'code': '719344',
            'role': 'psg',
            'name': 'Aline KHOURY (EL) ABOU SLEIMAN',
            'poste': 'Chargé de support académique',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'aline.khoury1@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '719459': {'ldap': '719459',
            'code': '719459',
            'role': 'psg',
            'name': 'Rachel KRAYEM MEZHER',
            'poste': 'Chargé de support académique',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'rachel.krayem@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '718304': {'ldap': '718304',
            'code': '718304',
            'role': 'psg',
            'name': 'Nancy LAHAD ABI NADER HADDAD',
            'poste': "Agent d'accueil",
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'nancy.lahadabinader@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '716023': {'ldap': '716023',
            'code': '716023',
            'role': 'psg',
            'name': 'Christina MAALOUF',
            'poste': 'Chargé de support académique',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'christina.maalouf@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '718026': {'ldap': '718026',
            'code': '718026',
            'role': 'psg',
            'name': 'Jessica RAHAL MEZHER',
            'poste': 'Chargé de support administratif',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'jessica.rahal1@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '718307': {'ldap': '718307',
            'code': '718307',
            'role': 'psg',
            'name': 'Nancy RIZK NOUAYDER',
            'poste': 'Chargé de support académique',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'nancy.rizk5@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '708859': {'ldap': '708859',
            'code': '708859',
            'role': 'psg',
            'name': 'Charbel YOUSSEF',
            'poste': 'Technicien de laboratoire',
            'faculty': 'FM',
            'institution': 'FM',
            'department': '',
            'email': 'charbel.youssef@usj.edu.lb',
            'director_name': 'Elie NEMER',
            'director_code': '705889',
            'director_ldap': '705889',
            'director_email': 'elie.nemer@usj.edu.lb'},
 '700380': {'ldap': '700380',
            'code': '700380',
            'role': 'psg',
            'name': 'Carla BOU JAOUDE ARIDA',
            'poste': 'Coordinateur administratif',
            'faculty': 'EDSHS',
            'institution': 'EDSHS',
            'department': '',
            'email': 'carla.arida@usj.edu.lb',
            'director_name': 'Elie YAZBEK',
            'director_code': '707404',
            'director_ldap': '707404',
            'director_email': 'elie.yazbek@usj.edu.lb'},
 '707404': {'ldap': '707404',
            'code': '707404',
            'role': 'director',
            'name': 'Elie YAZBEK',
            'poste': "Directeur de l' École doctorale sciences de l'homme et de la société",
            'faculty': 'EDSHS',
            'institution': 'EDSHS',
            'department': '',
            'email': 'elie.yazbek@usj.edu.lb'},
 '709136': {'ldap': '709136',
            'code': '709136',
            'role': 'psg',
            'name': 'Eliana SEMAAN HAGE(EL)',
            'poste': 'Coordinateur du bureau du VRA',
            'faculty': 'VRA',
            'institution': 'VRA',
            'department': '',
            'email': 'eliana.semaan@usj.edu.lb',
            'director_name': 'Fadi GEARA',
            'director_code': '702858',
            'director_ldap': '702858',
            'director_email': 'fadi.geara@usj.edu.lb'},
 '702858': {'ldap': '702858',
            'code': '702858',
            'role': 'director',
            'name': 'Fadi GEARA',
            'poste': "Vice-Recteur à Vice-rectorat à l'administration",
            'faculty': 'VRA',
            'institution': 'VRA',
            'department': '',
            'email': 'fadi.geara@usj.edu.lb'},
 '717612': {'ldap': '717612',
            'code': '717612',
            'role': 'psg',
            'name': 'Angel BAHOUT MRAD',
            'poste': "Chef d'unité - formation continue",
            'faculty': 'CFP',
            'institution': 'CFP',
            'department': '',
            'email': 'angel.bahout1@usj.edu.lb',
            'director_name': 'Fadi HAGE (EL)',
            'director_code': '703328',
            'director_ldap': '703328',
            'director_email': 'fadi.el-hage@usj.edu.lb'},
 '703328': {'ldap': '703328',
            'code': '703328',
            'role': 'director',
            'name': 'Fadi HAGE (EL)',
            'poste': 'Directeur du Centre de formation professionnelle',
            'faculty': 'CFP',
            'institution': 'CFP',
            'department': '',
            'email': 'fadi.el-hage@usj.edu.lb'},
 '715919': {'ldap': '715919',
            'code': '715919',
            'role': 'psg',
            'name': 'Josiane DIAB MAALOUF KHALAF',
            'poste': "Développeur d'affaires",
            'faculty': 'CFP',
            'institution': 'CFP',
            'department': '',
            'email': 'josiane.maalouf@usj.edu.lb',
            'director_name': 'Fadi HAGE (EL)',
            'director_code': '703328',
            'director_ldap': '703328',
            'director_email': 'fadi.el-hage@usj.edu.lb'},
 '719455': {'ldap': '719455',
            'code': '719455',
            'role': 'psg',
            'name': 'Elissa MAKHOUL',
            'poste': 'Chargé de communication',
            'faculty': 'CFP',
            'institution': 'CFP',
            'department': '',
            'email': 'elissa.makhoul1@usj.edu.lb',
            'director_name': 'Fadi HAGE (EL)',
            'director_code': '703328',
            'director_ldap': '703328',
            'director_email': 'fadi.el-hage@usj.edu.lb'},
 '718851': {'ldap': '718851',
            'code': '718851',
            'role': 'psg',
            'name': 'Elyse SAADEH DIBO',
            'poste': 'Chargé de support administratif',
            'faculty': 'CFP',
            'institution': 'CFP',
            'department': '',
            'email': 'elyse.saadeh@usj.edu.lb',
            'director_name': 'Fadi HAGE (EL)',
            'director_code': '703328',
            'director_ldap': '703328',
            'director_email': 'fadi.el-hage@usj.edu.lb'},
 '718491': {'ldap': '718491',
            'code': '718491',
            'role': 'psg',
            'name': 'Albert YAMMINE',
            'poste': 'Coordinateur de la formation continue',
            'faculty': 'CFP',
            'institution': 'CFP',
            'department': '',
            'email': 'albert.yammine2@usj.edu.lb',
            'director_name': 'Fadi HAGE (EL)',
            'director_code': '703328',
            'director_ldap': '703328',
            'director_email': 'fadi.el-hage@usj.edu.lb'},
 '706584': {'ldap': '706584',
            'code': '706584',
            'role': 'psg',
            'name': 'Layla AHMAD SALEH IBRAHIM',
            'poste': "Agent de propreté et d'hygiène",
            'faculty': 'CLN',
            'institution': 'CLN',
            'department': '',
            'email': 'layla.ibrahim@usj.edu.lb',
            'director_name': 'Fadia ALAM (EL) GEMAYEL',
            'director_code': '700634',
            'director_ldap': '700634',
            'director_email': 'fadia.alam@usj.edu.lb'},
 '700634': {'ldap': '700634',
            'code': '700634',
            'role': 'director',
            'name': 'Fadia ALAM (EL) GEMAYEL',
            'poste': 'Directeur du Campus du Liban Nord',
            'faculty': 'CLN',
            'institution': 'CLN',
            'department': '',
            'email': 'fadia.alam@usj.edu.lb'},
 '701881': {'ldap': '701881',
            'code': '701881',
            'role': 'psg',
            'name': 'Wassila CHATRY BREIR',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'CLN',
            'institution': 'CLN',
            'department': '',
            'email': 'wassila.chatry@usj.edu.lb',
            'director_name': 'Fadia ALAM (EL) GEMAYEL',
            'director_code': '700634',
            'director_ldap': '700634',
            'director_email': 'fadia.alam@usj.edu.lb'},
 '702373': {'ldap': '702373',
            'code': '702373',
            'role': 'psg',
            'name': 'Maha DERJANI',
            'poste': 'Assistant aux affaires académiques',
            'faculty': 'CLN',
            'institution': 'CLN',
            'department': '',
            'email': 'maha.derjani@usj.edu.lb',
            'director_name': 'Fadia ALAM (EL) GEMAYEL',
            'director_code': '700634',
            'director_ldap': '700634',
            'director_email': 'fadia.alam@usj.edu.lb'},
 '703714': {'ldap': '703714',
            'code': '703714',
            'role': 'psg',
            'name': 'Ziad HLAIS',
            'poste': 'Agent de sécurité',
            'faculty': 'CLN',
            'institution': 'CLN',
            'department': '',
            'email': 'ziad.hlais@usj.edu.lb',
            'director_name': 'Fadia ALAM (EL) GEMAYEL',
            'director_code': '700634',
            'director_ldap': '700634',
            'director_email': 'fadia.alam@usj.edu.lb'},
 '705106': {'ldap': '705106',
            'code': '705106',
            'role': 'psg',
            'name': 'Halimeh MARIAM YAGHI',
            'poste': "Agent de propreté et d'hygiène",
            'faculty': 'CLN',
            'institution': 'CLN',
            'department': '',
            'email': 'halimeh.yaghi@usj.edu.lb',
            'director_name': 'Fadia ALAM (EL) GEMAYEL',
            'director_code': '700634',
            'director_ldap': '700634',
            'director_email': 'fadia.alam@usj.edu.lb'},
 '705468': {'ldap': '705468',
            'code': '705468',
            'role': 'psg',
            'name': 'Samir MOUHAMAD (AL)',
            'poste': "Agent de maintenance et d'entretien",
            'faculty': 'CLN',
            'institution': 'CLN',
            'department': '',
            'email': 'samir.mouhamad@usj.edu.lb',
            'director_name': 'Fadia ALAM (EL) GEMAYEL',
            'director_code': '700634',
            'director_ldap': '700634',
            'director_email': 'fadia.alam@usj.edu.lb'},
 '712814': {'ldap': '712814',
            'code': '712814',
            'role': 'psg',
            'name': 'Nadia SALLOUM ARFOUL',
            'poste': 'Chargé de support académique',
            'faculty': 'CLN',
            'institution': 'CLN',
            'department': '',
            'email': 'nadia.salloum1@usj.edu.lb',
            'director_name': 'Fadia ALAM (EL) GEMAYEL',
            'director_code': '700634',
            'director_ldap': '700634',
            'director_email': 'fadia.alam@usj.edu.lb'},
 '713326': {'ldap': '713326',
            'code': '713326',
            'role': 'psg',
            'name': 'Salwa ABBOUD',
            'poste': 'Chargé de support académique',
            'faculty': 'FGM',
            'institution': 'FGM',
            'department': '',
            'email': 'salwa.abboud@usj.edu.lb',
            'director_name': 'Fouad ZMOKHOL',
            'director_code': '701198',
            'director_ldap': '701198',
            'director_email': 'fouad.zmokhol@usj.edu.lb'},
 '701198': {'ldap': '701198',
            'code': '701198',
            'role': 'director',
            'name': 'Fouad ZMOKHOL',
            'poste': 'Doyen de la Faculté de gestion et de management',
            'faculty': 'FGM',
            'institution': 'FGM',
            'department': '',
            'email': 'fouad.zmokhol@usj.edu.lb'},
 '700106': {'ldap': '700106',
            'code': '700106',
            'role': 'psg',
            'name': 'Nadine ABDEL NOUR BAZ',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'FGM',
            'institution': 'FGM',
            'department': '',
            'email': 'nadine.baz@usj.edu.lb',
            'director_name': 'Fouad ZMOKHOL',
            'director_code': '701198',
            'director_ldap': '701198',
            'director_email': 'fouad.zmokhol@usj.edu.lb'},
 '716208': {'ldap': '716208',
            'code': '716208',
            'role': 'psg',
            'name': 'Caroline HADDAD',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'FGM',
            'institution': 'FGM',
            'department': '',
            'email': 'caroline.haddad@usj.edu.lb',
            'director_name': 'Fouad ZMOKHOL',
            'director_code': '701198',
            'director_ldap': '701198',
            'director_email': 'fouad.zmokhol@usj.edu.lb'},
 '719405': {'ldap': '719405',
            'code': '719405',
            'role': 'psg',
            'name': 'Lama HALY (EL)',
            'poste': 'Chargé de support administratif',
            'faculty': 'FGM',
            'institution': 'FGM',
            'department': '',
            'email': 'lama.haly1@usj.edu.lb',
            'director_name': 'Fouad ZMOKHOL',
            'director_code': '701198',
            'director_ldap': '701198',
            'director_email': 'fouad.zmokhol@usj.edu.lb'},
 '719401': {'ldap': '719401',
            'code': '719401',
            'role': 'psg',
            'name': 'Mélanie KHALIL CHAHOUD',
            'poste': 'Chargé de support académique',
            'faculty': 'FGM',
            'institution': 'FGM',
            'department': '',
            'email': 'melanie.khalil@usj.edu.lb',
            'director_name': 'Fouad ZMOKHOL',
            'director_code': '701198',
            'director_ldap': '701198',
            'director_email': 'fouad.zmokhol@usj.edu.lb'},
 '703168': {'ldap': '703168',
            'code': '703168',
            'role': 'psg',
            'name': 'Cosette HABIB DANIEL',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'SREC',
            'institution': 'SREC',
            'department': '',
            'email': 'cosette.daniel@usj.edu.lb',
            'director_name': 'François BOËDEC s.j.',
            'director_code': '701440',
            'director_ldap': '701440',
            'director_email': 'francois.boedec@usj.edu.lb'},
 '701440': {'ldap': '701440',
            'code': '701440',
            'role': 'director',
            'name': 'François BOËDEC s.j.',
            'poste': 'Recteur',
            'faculty': 'SREC',
            'institution': 'SREC',
            'department': '',
            'email': 'francois.boedec@usj.edu.lb'},
 '700565': {'ldap': '700565',
            'code': '700565',
            'role': 'psg',
            'name': 'Patrick HAJJ',
            'poste': 'Responsable de la sécurité des systèmes d’information',
            'faculty': 'SREC',
            'institution': 'SREC',
            'department': '',
            'email': 'patrick.hajj@usj.edu.lb',
            'director_name': 'François BOËDEC s.j.',
            'director_code': '701440',
            'director_ldap': '701440',
            'director_email': 'francois.boedec@usj.edu.lb'},
 '707189': {'ldap': '707189',
            'code': '707189',
            'role': 'psg',
            'name': 'Rima TOUMA EL HAJJ',
            'poste': 'Coordinateur du bureau du Recteur',
            'faculty': 'SREC',
            'institution': 'SREC',
            'department': '',
            'email': 'rima.hajj@usj.edu.lb',
            'director_name': 'François BOËDEC s.j.',
            'director_code': '701440',
            'director_ldap': '701440',
            'director_email': 'francois.boedec@usj.edu.lb'},
 '717304': {'ldap': '717304',
            'code': '717304',
            'role': 'psg',
            'name': 'Abdo ABI RACHED',
            'poste': 'Administrateur - Réseaux',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'abdo.abirached@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '705697': {'ldap': '705697',
            'code': '705697',
            'role': 'director',
            'name': 'Georges NAKHLE',
            'poste': "Directeur du service de technologie de l'information",
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'georges.nakhle@usj.edu.lb'},
 '709114': {'ldap': '709114',
            'code': '709114',
            'role': 'psg',
            'name': 'Rony ABI SAAD',
            'poste': 'Business Analyst Senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'rony.abisaad@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '713927': {'ldap': '713927',
            'code': '713927',
            'role': 'psg',
            'name': 'Geryes ABI SALEH',
            'poste': 'Informaticien de support senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'geryes.abisaleh@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '717837': {'ldap': '717837',
            'code': '717837',
            'role': 'psg',
            'name': 'Georgio ABOU DIWAN',
            'poste': 'Développeur',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'georgio.aboudiwan@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '712219': {'ldap': '712219',
            'code': '712219',
            'role': 'psg',
            'name': 'Elie AKL',
            'poste': 'Administrateur - Systèmes Senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'elie.akl@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '714336': {'ldap': '714336',
            'code': '714336',
            'role': 'psg',
            'name': 'Joseph AKL',
            'poste': 'Développeur senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'joseph.akl1@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '700811': {'ldap': '700811',
            'code': '700811',
            'role': 'psg',
            'name': 'Fady ARBID',
            'poste': "Chef d'Unité - Systèmes et Réseaux",
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'fady.arbid@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '717381': {'ldap': '717381',
            'code': '717381',
            'role': 'psg',
            'name': 'Charbel ASSAF',
            'poste': 'Administrateur - Systèmes',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'charbel.assaf3@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '715119': {'ldap': '715119',
            'code': '715119',
            'role': 'psg',
            'name': 'Tania AWADIK ESTEPHAN',
            'poste': "Chef d'Unité - Développement",
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'tania.estephan@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '701007': {'ldap': '701007',
            'code': '701007',
            'role': 'psg',
            'name': 'Joseph AWWAD',
            'poste': 'Administrateur - Sécurité Senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'joseph.awwad@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '706273': {'ldap': '706273',
            'code': '706273',
            'role': 'psg',
            'name': 'Georges BACHIR',
            'poste': "Chef d'unité - production & Data - BI",
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'george.bachir@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '701171': {'ldap': '701171',
            'code': '701171',
            'role': 'psg',
            'name': 'Fady BAKHACHE',
            'poste': "Chef d'Unité - Business Analysis",
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'fady.bakhache@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '718750': {'ldap': '718750',
            'code': '718750',
            'role': 'psg',
            'name': 'Rebecca BEJJANI',
            'poste': 'Développeur web',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'rebecca.bejjani@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '719646': {'ldap': '719646',
            'code': '719646',
            'role': 'psg',
            'name': 'Serge BOU SAADA',
            'poste': 'Administrateur - Multimédias Senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'serge.bousaada@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '717348': {'ldap': '717348',
            'code': '717348',
            'role': 'psg',
            'name': 'Joe-Oliver CHAHOUD',
            'poste': 'Informaticien de support',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'joe-oliver.chahoud@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '710399': {'ldap': '710399',
            'code': '710399',
            'role': 'psg',
            'name': 'Johnny CHAMMAS',
            'poste': 'Informaticien de support senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'johnny.chammas@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '709252': {'ldap': '709252',
            'code': '709252',
            'role': 'psg',
            'name': 'Fadi CHEBLI',
            'poste': 'Directeur-adjoint - infrastructure & support',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'fadi.chebli@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '709335': {'ldap': '709335',
            'code': '709335',
            'role': 'psg',
            'name': 'Imad CHEDID',
            'poste': 'Agent Helpdesk - TL',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'imad.chedid@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '717762': {'ldap': '717762',
            'code': '717762',
            'role': 'psg',
            'name': 'Anthony CHOUCAIR',
            'poste': 'Administrateur - Réseaux',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'anthony.choucair@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '716346': {'ldap': '716346',
            'code': '716346',
            'role': 'psg',
            'name': 'Kevin CREIDI',
            'poste': 'Informaticien de support senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'kevin.creidi1@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '718850': {'ldap': '718850',
            'code': '718850',
            'role': 'psg',
            'name': 'Elias DEAIBESS',
            'poste': 'Administrateur - Réseaux',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'elias.deaibess@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '719115': {'ldap': '719115',
            'code': '719115',
            'role': 'psg',
            'name': 'Anais DEURDULIAN',
            'poste': 'Développeur web',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'anais.deurdulian@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '716973': {'ldap': '716973',
            'code': '716973',
            'role': 'psg',
            'name': 'Michel FADEL',
            'poste': 'Informaticien de support',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'michel.fadel@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '716844': {'ldap': '716844',
            'code': '716844',
            'role': 'psg',
            'name': 'Anthony FAHED',
            'poste': 'Administrateur - Multimédias',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'anthony.fahed@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '708811': {'ldap': '708811',
            'code': '708811',
            'role': 'psg',
            'name': 'Elias FARAH',
            'poste': 'Administrateur - Systèmes - Team leader',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'elias.farah@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '702715': {'ldap': '702715',
            'code': '702715',
            'role': 'psg',
            'name': 'Georges FAWAZ',
            'poste': 'Administrateur - Réseaux - Team leader',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'georges.fawaz@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '718749': {'ldap': '718749',
            'code': '718749',
            'role': 'psg',
            'name': 'Myriam GHANEM',
            'poste': 'Développeur Web',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'myriam.ghanem2@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '719554': {'ldap': '719554',
            'code': '719554',
            'role': 'psg',
            'name': 'Fawzy GHAZAWY',
            'poste': 'Développeur "Full Stack"',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'fawzy.ghazawy@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '718673': {'ldap': '718673',
            'code': '718673',
            'role': 'psg',
            'name': 'Walid GHOUL (EL)',
            'poste': 'Informaticien de support',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'walid.ghoul@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '704967': {'ldap': '704967',
            'code': '704967',
            'role': 'psg',
            'name': 'Antoine HAGE (EL)',
            'poste': 'Business Analyst Senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'antoine.elhage@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '718095': {'ldap': '718095',
            'code': '718095',
            'role': 'psg',
            'name': 'Rony HANNA',
            'poste': 'Informaticien de support',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'rony.hanna@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '703632': {'ldap': '703632',
            'code': '703632',
            'role': 'psg',
            'name': 'Georges HAYEK (EL)',
            'poste': "Chef d'Unité - support informatique",
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'georges.hayek@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '715420': {'ldap': '715420',
            'code': '715420',
            'role': 'psg',
            'name': 'Jack ISSA',
            'poste': 'Administrateur - Systèmes Senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'jack.issa@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '719114': {'ldap': '719114',
            'code': '719114',
            'role': 'psg',
            'name': 'Jason ISSA',
            'poste': 'Développeur "Full Stack"',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'jason.issa@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '703943': {'ldap': '703943',
            'code': '703943',
            'role': 'psg',
            'name': 'Tony JADAM',
            'poste': 'Administrateur - Multimédias - Team leader',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'tony.jadam@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '715808': {'ldap': '715808',
            'code': '715808',
            'role': 'psg',
            'name': 'Said KHALIL',
            'poste': 'Développeur senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'said.khalil1@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '719116': {'ldap': '719116',
            'code': '719116',
            'role': 'psg',
            'name': 'Edgard KHNEISSER',
            'poste': 'Développeur web',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'edgard.khneisser@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '708812': {'ldap': '708812',
            'code': '708812',
            'role': 'psg',
            'name': 'Rony KHOURY',
            'poste': 'Informaticien de support - Team leader',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'rony.khoury@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '719639': {'ldap': '719639',
            'code': '719639',
            'role': 'psg',
            'name': 'Charbel KHOURY (EL)',
            'poste': 'Administrateur - Multimédias',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'charbel.khoury16@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '715981': {'ldap': '715981',
            'code': '715981',
            'role': 'psg',
            'name': 'Elias KHOURY (EL)',
            'poste': 'Informaticien de support senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'elias.khoury9@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '716633': {'ldap': '716633',
            'code': '716633',
            'role': 'psg',
            'name': 'Pamela LOUBNAN',
            'poste': 'Informaticien de support senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'pamela.loubnan@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '710397': {'ldap': '710397',
            'code': '710397',
            'role': 'psg',
            'name': 'Robert MAROUN',
            'poste': 'Administrateur - Systèmes Senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'robert.maroun@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '716616': {'ldap': '716616',
            'code': '716616',
            'role': 'psg',
            'name': 'Jana NAJDI',
            'poste': 'Développeur web senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'jana.najdi1@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '716345': {'ldap': '716345',
            'code': '716345',
            'role': 'psg',
            'name': 'Joe NASSAR',
            'poste': 'Informaticien de support',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'joe.nassar1@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '716586': {'ldap': '716586',
            'code': '716586',
            'role': 'psg',
            'name': 'Marc RIZK',
            'poste': 'Informaticien de support',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'marc.rizk1@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '706506': {'ldap': '706506',
            'code': '706506',
            'role': 'psg',
            'name': 'Thérèse SAHYOUNI BAAKLINI',
            'poste': 'Gestionnaire des opérations',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'therese.baaklini@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '717385': {'ldap': '717385',
            'code': '717385',
            'role': 'psg',
            'name': 'Abdo SAKR',
            'poste': 'Informaticien de support',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'abdo.sakr@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '717523': {'ldap': '717523',
            'code': '717523',
            'role': 'psg',
            'name': 'Ibrahim SAMAHA',
            'poste': 'Administrateur - Systèmes',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'ibrahim.samaha@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '711694': {'ldap': '711694',
            'code': '711694',
            'role': 'psg',
            'name': 'Elie SLEIMAN',
            'poste': 'Helpdesk Agent - senior',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'elie.sleiman@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '711703': {'ldap': '711703',
            'code': '711703',
            'role': 'psg',
            'name': 'Ramy SLEIMAN',
            'poste': 'Administrateur - Réseaux - Team leader',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'ramy.sleiman@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '716603': {'ldap': '716603',
            'code': '716603',
            'role': 'psg',
            'name': 'Dany TAHCHY (EL)',
            'poste': 'Développeur - Team leader',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'dany.tahchy@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '707194': {'ldap': '707194',
            'code': '707194',
            'role': 'psg',
            'name': 'Elias TRABOULSI',
            'poste': "Chef d'Unité - Multimédia",
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'elie.traboulsi@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '708949': {'ldap': '708949',
            'code': '708949',
            'role': 'psg',
            'name': 'Mansour YOUSSEF',
            'poste': 'Administrateur - Sécurité - Team leader',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'mansour.youssef@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '715793': {'ldap': '715793',
            'code': '715793',
            'role': 'psg',
            'name': 'Ahmad ZEIN',
            'poste': 'Administrateur - Sécurité',
            'faculty': 'STI',
            'institution': 'STI',
            'department': '',
            'email': 'ahmad.zein3@usj.edu.lb',
            'director_name': 'Georges NAKHLE',
            'director_code': '705697',
            'director_ldap': '705697',
            'director_email': 'georges.nakhle@usj.edu.lb'},
 '700269': {'ldap': '700269',
            'code': '700269',
            'role': 'psg',
            'name': 'Naji ABI ZEID DAOU',
            'poste': 'Directeur du service des tests',
            'faculty': 'STA',
            'institution': 'STA',
            'department': '',
            'email': 'naji.abizeid@usj.edu.lb',
            'director_name': 'Gina ABOU FADEL SAAD',
            'director_code': '700335',
            'director_ldap': '700335',
            'director_email': 'gina.aboufadel@usj.edu.lb'},
 '700335': {'ldap': '700335',
            'code': '700335',
            'role': 'director',
            'name': 'Gina ABOU FADEL SAAD',
            'poste': 'Doyen de la Faculté de langues et de traduction',
            'faculty': 'STA',
            'institution': 'STA',
            'department': '',
            'email': 'gina.aboufadel@usj.edu.lb'},
 '700789': {'ldap': '700789',
            'code': '700789',
            'role': 'psg',
            'name': 'Carole AOUN CHACAR',
            'poste': 'Assistant aux affaires académiques',
            'faculty': 'STA',
            'institution': 'STA',
            'department': '',
            'email': 'carole.chacar@usj.edu.lb',
            'director_name': 'Gina ABOU FADEL SAAD',
            'director_code': '700335',
            'director_ldap': '700335',
            'director_email': 'gina.aboufadel@usj.edu.lb'},
 '704413': {'ldap': '704413',
            'code': '704413',
            'role': 'psg',
            'name': 'Liliane KHAIRALLAH TABET',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'FdLT',
            'institution': 'FdLT',
            'department': '',
            'email': 'liliane.tabet@usj.edu.lb',
            'director_name': 'Gina ABOU FADEL SAAD',
            'director_code': '700335',
            'director_ldap': '700335',
            'director_email': 'gina.aboufadel@usj.edu.lb'},
 '716884': {'ldap': '716884',
            'code': '716884',
            'role': 'psg',
            'name': 'Diana KOUYOUMJIAN BATHANI',
            'poste': 'Agent de service',
            'faculty': 'FdLT',
            'institution': 'FdLT',
            'department': '',
            'email': 'diana.kouyoumjian@usj.edu.lb',
            'director_name': 'Gina ABOU FADEL SAAD',
            'director_code': '700335',
            'director_ldap': '700335',
            'director_email': 'gina.aboufadel@usj.edu.lb'},
 '711072': {'ldap': '711072',
            'code': '711072',
            'role': 'psg',
            'name': 'Aziza TAHHAN YOUSSEF',
            'poste': 'Chargé de support académique',
            'faculty': 'FdLT',
            'institution': 'FdLT',
            'department': '',
            'email': 'aziza.youssef@usj.edu.lb',
            'director_name': 'Gina ABOU FADEL SAAD',
            'director_code': '700335',
            'director_ldap': '700335',
            'director_email': 'gina.aboufadel@usj.edu.lb'},
 '707420': {'ldap': '707420',
            'code': '707420',
            'role': 'psg',
            'name': 'Gladys YOUAKIM ABI RACHED',
            'poste': 'Chargé de support académique',
            'faculty': 'FdLT',
            'institution': 'FdLT',
            'department': '',
            'email': 'gladys.abirached@usj.edu.lb',
            'director_name': 'Gina ABOU FADEL SAAD',
            'director_code': '700335',
            'director_ldap': '700335',
            'director_email': 'gina.aboufadel@usj.edu.lb'},
 '707619': {'ldap': '707619',
            'code': '707619',
            'role': 'psg',
            'name': 'Edgard BARADHY',
            'poste': 'Préposé aux remboursements médicaux et à la SG',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'edgard.baradhy@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '703095': {'ldap': '703095',
            'code': '703095',
            'role': 'director',
            'name': 'Gladys GHRAICHY',
            'poste': 'Directeur du service des ressources humaines',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'gladys.ghraichy@usj.edu.lb'},
 '701304': {'ldap': '701304',
            'code': '701304',
            'role': 'psg',
            'name': 'Joëlle BAZ TRABOULSI',
            'poste': 'Directeur-adjoint - Administration du personnel',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'joelle.baz@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '711919': {'ldap': '711919',
            'code': '711919',
            'role': 'psg',
            'name': 'Pamela BERBERI FADDOUL',
            'poste': 'Coordinateur - Bureau des assurances',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'pamela.berberi@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '717400': {'ldap': '717400',
            'code': '717400',
            'role': 'psg',
            'name': 'Michelle BITAR',
            'poste': 'Chargé de support administratif',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'michelle.bitar@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '712197': {'ldap': '712197',
            'code': '712197',
            'role': 'psg',
            'name': 'Grace BOU DOUMIT DARGHAM',
            'poste': 'Gestionnaire de paie',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'grace.dargham@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '701696': {'ldap': '701696',
            'code': '701696',
            'role': 'psg',
            'name': 'Rana CHAAYA MHAWEJ',
            'poste': 'Directeur- adjoint - assurances',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'rana.mhawej@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '701813': {'ldap': '701813',
            'code': '701813',
            'role': 'psg',
            'name': 'Yolla CHAMMAS (EL) ABI NASR',
            'poste': 'Gestionnaire de projets et de communication RH',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'yolla.chammas@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '713286': {'ldap': '713286',
            'code': '713286',
            'role': 'psg',
            'name': 'Sara HAWWA',
            'poste': 'Chargé de support administratif',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'sara.hawwa@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '703865': {'ldap': '703865',
            'code': '703865',
            'role': 'psg',
            'name': 'Antoine ISHAK',
            'poste': 'Représentant du personnel auprès de la CNSS et du ministère du travail',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'antoine.ishak@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '709975': {'ldap': '709975',
            'code': '709975',
            'role': 'psg',
            'name': 'Joseph KANAAN',
            'poste': 'Agent administratif',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'joseph.kanaan@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '715394': {'ldap': '715394',
            'code': '715394',
            'role': 'psg',
            'name': 'Angela KASSIS (EL)',
            'poste': 'Assistant (e) RH',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'angela.kassis1@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '704400': {'ldap': '704400',
            'code': '704400',
            'role': 'psg',
            'name': 'Marie KHAIRALLAH',
            'poste': "Chef d'unité - paie des vacataires",
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'marie.khairallah@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '709782': {'ldap': '709782',
            'code': '709782',
            'role': 'psg',
            'name': 'Claudine MOUBARAK COSTANTINE',
            'poste': "Coordinateur d'inclusion",
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'claudine.moubarak1@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '712070': {'ldap': '712070',
            'code': '712070',
            'role': 'psg',
            'name': 'Hind NASTA MOUSSA',
            'poste': 'Agent de numérisation',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'hind.nastamoussa@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '706239': {'ldap': '706239',
            'code': '706239',
            'role': 'psg',
            'name': 'Hâla RISHA BALDO',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'hala.baldo@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '715995': {'ldap': '715995',
            'code': '715995',
            'role': 'psg',
            'name': 'Diala SEMAAN CHALHOUB',
            'poste': 'Chargé de recrutement',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'diala.chalhoub@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '716185': {'ldap': '716185',
            'code': '716185',
            'role': 'psg',
            'name': 'Sara Maria SOUEIDY (EL)',
            'poste': 'Assistant de paie',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'sarahmaria.soueidy@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '716498': {'ldap': '716498',
            'code': '716498',
            'role': 'psg',
            'name': 'Ranine TABET',
            'poste': 'Chargé de support administratif',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'ranine.tabet@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '710743': {'ldap': '710743',
            'code': '710743',
            'role': 'psg',
            'name': 'Sarah ZAHREDDINE',
            'poste': 'Gestionnaire RH',
            'faculty': 'SRH',
            'institution': 'SRH',
            'department': '',
            'email': 'sarah.zahreddine@usj.edu.lb',
            'director_name': 'Gladys GHRAICHY',
            'director_code': '703095',
            'director_ldap': '703095',
            'director_email': 'gladys.ghraichy@usj.edu.lb'},
 '719133': {'ldap': '719133',
            'code': '719133',
            'role': 'psg',
            'name': 'Zoya BARAKAT',
            'poste': 'chargé(e) des projets',
            'faculty': 'SVE',
            'institution': 'SVE',
            'department': '',
            'email': 'zoya.barakat1@usj.edu.lb',
            'director_name': 'Gloria ABDO',
            'director_code': '700118',
            'director_ldap': '700118',
            'director_email': 'gloria.abdo@usj.edu.lb'},
 '700118': {'ldap': '700118',
            'code': '700118',
            'role': 'director',
            'name': 'Gloria ABDO',
            'poste': 'Directeur du service de la vie étudiante',
            'faculty': 'SVE',
            'institution': 'SVE',
            'department': '',
            'email': 'gloria.abdo@usj.edu.lb'},
 '716219': {'ldap': '716219',
            'code': '716219',
            'role': 'psg',
            'name': 'Youssef CHAAYA',
            'poste': 'Coordinateur de projets',
            'faculty': 'SVE',
            'institution': 'SVE',
            'department': '',
            'email': 'youssef.chaaya1@usj.edu.lb',
            'director_name': 'Gloria ABDO',
            'director_code': '700118',
            'director_ldap': '700118',
            'director_email': 'gloria.abdo@usj.edu.lb'},
 '717291': {'ldap': '717291',
            'code': '717291',
            'role': 'psg',
            'name': 'Patrick CHEHADE',
            'poste': 'Chargé de communication et des réseaux sociaux',
            'faculty': 'SVE',
            'institution': 'SVE',
            'department': '',
            'email': 'patrick.chehade1@usj.edu.lb',
            'director_name': 'Gloria ABDO',
            'director_code': '700118',
            'director_ldap': '700118',
            'director_email': 'gloria.abdo@usj.edu.lb'},
 '713978': {'ldap': '713978',
            'code': '713978',
            'role': 'psg',
            'name': 'Joseph HATEM',
            'poste': 'Coordinateur des activités  - Opération 7e Jour',
            'faculty': 'O7',
            'institution': 'O7',
            'department': '',
            'email': 'joe.hatem@usj.edu.lb',
            'director_name': '',
            'director_code': '',
            'director_ldap': '',
            'director_email': ''},
 '716043': {'ldap': '716043',
            'code': '716043',
            'role': 'psg',
            'name': 'Christine JARJOUR',
            'poste': 'Chargé de support académique',
            'faculty': 'ISO',
            'institution': 'ISO',
            'department': '',
            'email': 'christine.jarjour@usj.edu.lb',
            'director_name': 'Guillemette HENRY',
            'director_code': '703687',
            'director_ldap': '703687',
            'director_email': 'guillemette.henry@usj.edu.lb'},
 '703687': {'ldap': '703687',
            'code': '703687',
            'role': 'director',
            'name': 'Guillemette HENRY',
            'poste': "Directrice de l' Institut supérieur d'orthophonie",
            'faculty': 'ISO',
            'institution': 'ISO',
            'department': '',
            'email': 'guillemette.henry@usj.edu.lb'},
 '716625': {'ldap': '716625',
            'code': '716625',
            'role': 'psg',
            'name': 'Mireille TOHME BAZ',
            'poste': 'Chargé de support académique',
            'faculty': 'ISO',
            'institution': 'ISO',
            'department': '',
            'email': 'mireille.tohme@usj.edu.lb',
            'director_name': 'Guillemette HENRY',
            'director_code': '703687',
            'director_ldap': '703687',
            'director_email': 'guillemette.henry@usj.edu.lb'},
 '719135': {'ldap': '719135',
            'code': '719135',
            'role': 'psg',
            'name': 'Mireille FRANCIS ABOU KHEIR',
            'poste': 'chargé (e ) de support administratif',
            'faculty': 'UAQ',
            'institution': 'UAQ',
            'department': '',
            'email': 'mireille.francis1@usj.edu.lb',
            'director_name': 'Hadi SAWAYA',
            'director_code': '706744',
            'director_ldap': '706744',
            'director_email': 'hadi.sawaya@usj.edu.lb'},
 '706744': {'ldap': '706744',
            'code': '706744',
            'role': 'director',
            'name': 'Hadi SAWAYA',
            'poste': "Directeur de l' Unité assurance qualité",
            'faculty': 'UAQ',
            'institution': 'UAQ',
            'department': '',
            'email': 'hadi.sawaya@usj.edu.lb'},
 '710584': {'ldap': '710584',
            'code': '710584',
            'role': 'psg',
            'name': 'Mohamad Tarek HALABI (EL)',
            'poste': 'Data Analyst',
            'faculty': 'UAQ',
            'institution': 'UAQ',
            'department': '',
            'email': 'tarek.halabi@usj.edu.lb',
            'director_name': 'Hadi SAWAYA',
            'director_code': '706744',
            'director_ldap': '706744',
            'director_email': 'hadi.sawaya@usj.edu.lb'},
 '704755': {'ldap': '704755',
            'code': '704755',
            'role': 'psg',
            'name': 'Lina KOLEILAT GHALAYINI',
            'poste': 'Chef de projets',
            'faculty': 'UAQ',
            'institution': 'UAQ',
            'department': '',
            'email': 'lina.koleilat@usj.edu.lb',
            'director_name': 'Hadi SAWAYA',
            'director_code': '706744',
            'director_ldap': '706744',
            'director_email': 'hadi.sawaya@usj.edu.lb'},
 '701196': {'ldap': '701196',
            'code': '701196',
            'role': 'psg',
            'name': 'Jacqueline BALLOUZ',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'jacqueline.ballouz@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '701075': {'ldap': '701075',
            'code': '701075',
            'role': 'director',
            'name': 'Hayat AZOURI TANNOUS',
            'poste': 'Doyen de la Faculté de pharmacie',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'hayat.azouri@usj.edu.lb'},
 '701903': {'ldap': '701903',
            'code': '701903',
            'role': 'psg',
            'name': 'Amale CHEBLI',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'amale.chebli@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '702418': {'ldap': '702418',
            'code': '702418',
            'role': 'psg',
            'name': 'Zeinab DIB MALLI',
            'poste': "Agent de propreté et d'hygiène",
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'zeinab.malli@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '703096': {'ldap': '703096',
            'code': '703096',
            'role': 'psg',
            'name': 'Amale GHRAICHY (EL) ABI EZZ',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'amale.abiezz@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '708948': {'ldap': '708948',
            'code': '708948',
            'role': 'psg',
            'name': 'Fabienne HAJJ (EL) MOUSSA LTEIF',
            'poste': 'Assistant de laboratoire',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'fabienne.hajjmoussa@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '718386': {'ldap': '718386',
            'code': '718386',
            'role': 'psg',
            'name': 'Tania HANANIA KERKOR',
            'poste': 'Chargé de support administratif',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'tania.hanania@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '710969': {'ldap': '710969',
            'code': '710969',
            'role': 'psg',
            'name': 'Charbel KARKAF',
            'poste': 'Assistant de laboratoire',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'charbel.karkaf@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '713696': {'ldap': '713696',
            'code': '713696',
            'role': 'psg',
            'name': 'Mireille KHOURY (EL)',
            'poste': 'Chargé de support administratif',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'mireille.khoury@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '710919': {'ldap': '710919',
            'code': '710919',
            'role': 'psg',
            'name': 'May MALLAH',
            'poste': 'Assistant de laboratoire',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'may.mallah@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '712076': {'ldap': '712076',
            'code': '712076',
            'role': 'psg',
            'name': 'Jihan MAWALI (AL)',
            'poste': 'Agent de laboratoire',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'jihan.mawali@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '716982': {'ldap': '716982',
            'code': '716982',
            'role': 'psg',
            'name': 'Pierre MOUBARAK',
            'poste': 'Technicien de laboratoire',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'pierre.moubarak@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '716549': {'ldap': '716549',
            'code': '716549',
            'role': 'psg',
            'name': 'Sabine SALAMEH',
            'poste': 'Chargé de support académique',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'sabine.salameh1@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '716841': {'ldap': '716841',
            'code': '716841',
            'role': 'psg',
            'name': 'Rita TABET',
            'poste': 'Technicien de laboratoire',
            'faculty': 'FP',
            'institution': 'FP',
            'department': '',
            'email': 'rita.tabet4@usj.edu.lb',
            'director_name': 'Hayat AZOURI TANNOUS',
            'director_code': '701075',
            'director_ldap': '701075',
            'director_email': 'hayat.azouri@usj.edu.lb'},
 '713787': {'ldap': '713787',
            'code': '713787',
            'role': 'psg',
            'name': 'Zeinab ABDALLAH',
            'poste': 'Rédacteur - Analyste',
            'faculty': 'BDA',
            'institution': 'BDA',
            'department': '',
            'email': 'zeinab.abdallah2@usj.edu.lb',
            'director_name': 'Helen ACHOU TAYAR',
            'director_code': '700523',
            'director_ldap': '700523',
            'director_email': 'helen.tayar@usj.edu.lb'},
 '700523': {'ldap': '700523',
            'code': '700523',
            'role': 'director',
            'name': 'Helen ACHOU TAYAR',
            'poste': "Directeur du Bureau des anciens étudiants de l'USJ",
            'faculty': 'BDA',
            'institution': 'BDA',
            'department': '',
            'email': 'helen.tayar@usj.edu.lb'},
 '711769': {'ldap': '711769',
            'code': '711769',
            'role': 'psg',
            'name': 'Yara NASRANY (EL) BARTAH MATAR',
            'poste': "Chargé d'analyse de données",
            'faculty': 'BDA',
            'institution': 'BDA',
            'department': '',
            'email': 'yara.nasrany@usj.edu.lb',
            'director_name': 'Helen ACHOU TAYAR',
            'director_code': '700523',
            'director_ldap': '700523',
            'director_email': 'helen.tayar@usj.edu.lb'},
 '700413': {'ldap': '700413',
            'code': '700413',
            'role': 'psg',
            'name': 'Elie ABOU NASR',
            'poste': 'Technicien',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'elie.abounasr@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '713010': {'ldap': '713010',
            'code': '713010',
            'role': 'director',
            'name': 'Jacques BAROUD',
            'poste': 'Administrateur du Campus François Debbané des sciences sociales',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'jacques.baroud@usj.edu.lb'},
 '711484': {'ldap': '711484',
            'code': '711484',
            'role': 'psg',
            'name': 'Colette AOUN MOUKHEIBER',
            'poste': "Agent d'accueil",
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'colette.aounmokheiber@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '714093': {'ldap': '714093',
            'code': '714093',
            'role': 'psg',
            'name': 'David BACHOUR',
            'poste': 'Intendant de campus',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'david.bachour@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '701428': {'ldap': '701428',
            'code': '701428',
            'role': 'psg',
            'name': 'Nouhad BITAR FAYAD',
            'poste': 'Agent administratif',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'nouhad.fayad@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '702009': {'ldap': '702009',
            'code': '702009',
            'role': 'psg',
            'name': 'Bachir CHIDIAC (EL)',
            'poste': 'Appariteur',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'bechir.chidiac@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '702296': {'ldap': '702296',
            'code': '702296',
            'role': 'psg',
            'name': 'Najwa DAOUD ZOUEIN',
            'poste': 'Secrétaire de campus',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'najwa.zouein@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '711503': {'ldap': '711503',
            'code': '711503',
            'role': 'psg',
            'name': 'Johnny FADEL',
            'poste': 'Appariteur',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'johnny.fadel@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '702609': {'ldap': '702609',
            'code': '702609',
            'role': 'psg',
            'name': 'Georges FAHL (EL)',
            'poste': 'Bibliothécaire-adjoint',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'georges.fahl@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '708677': {'ldap': '708677',
            'code': '708677',
            'role': 'psg',
            'name': 'Tony HABIB',
            'poste': 'Technicien',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'toni.habib@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '711983': {'ldap': '711983',
            'code': '711983',
            'role': 'psg',
            'name': 'Fadi HACHEM',
            'poste': 'Coursier-Chauffeur',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'fadi.hachem@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '710100': {'ldap': '710100',
            'code': '710100',
            'role': 'psg',
            'name': 'Hanady HTEIT HADDAD',
            'poste': 'Agent de service',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'hanady.hteithaddad@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '703816': {'ldap': '703816',
            'code': '703816',
            'role': 'psg',
            'name': 'Abdel-Wahab HUSSEIN',
            'poste': 'Appariteur',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'abdelwahab.hussein@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '704348': {'ldap': '704348',
            'code': '704348',
            'role': 'psg',
            'name': 'Marie KESROUANI (EL) SEMAAN',
            'poste': "Agent d'accueil",
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'marie.semaan@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '714659': {'ldap': '714659',
            'code': '714659',
            'role': 'psg',
            'name': 'Charbel KHALIFE',
            'poste': 'Technicien spécialisé',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'charbel.khalife@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '717347': {'ldap': '717347',
            'code': '717347',
            'role': 'psg',
            'name': 'Elie TAWK',
            'poste': 'Technicien',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'elie.tawk@usj.edu.lb',
            'director_name': 'Jacques BAROUD',
            'director_code': '713010',
            'director_ldap': '713010',
            'director_email': 'jacques.baroud@usj.edu.lb'},
 '714094': {'ldap': '714094',
            'code': '714094',
            'role': 'psg',
            'name': 'Joelle AHMARANI',
            'poste': 'Chargé de communication',
            'faculty': 'AUM',
            'institution': 'AUM',
            'department': '',
            'email': 'joelle.ahmarani@usj.edu.lb',
            'director_name': '',
            'director_code': '',
            'director_ldap': '',
            'director_email': ''},
 '717698': {'ldap': '717698',
            'code': '717698',
            'role': 'psg',
            'name': 'Hanane BOU DOUMIT MAALOUF',
            'poste': "Responsable d'orientation",
            'faculty': 'SIO',
            'institution': 'SIO',
            'department': '',
            'email': 'hanane.boudoumit@usj.edu.lb',
            'director_name': 'Jana AOUAD AWAD',
            'director_code': '709004',
            'director_ldap': '709004',
            'director_email': 'jana.aouad@usj.edu.lb'},
 '709004': {'ldap': '709004',
            'code': '709004',
            'role': 'director',
            'name': 'Jana AOUAD AWAD',
            'poste': "Directeur du service étudiant d'information et d'orientation",
            'faculty': 'SIO',
            'institution': 'SIO',
            'department': '',
            'email': 'jana.aouad@usj.edu.lb'},
 '717132': {'ldap': '717132',
            'code': '717132',
            'role': 'psg',
            'name': 'Omar CHEHAB',
            'poste': "Chargé d'information et de communication",
            'faculty': 'SIO',
            'institution': 'SIO',
            'department': '',
            'email': 'omar.chehab1@usj.edu.lb',
            'director_name': 'Jana AOUAD AWAD',
            'director_code': '709004',
            'director_ldap': '709004',
            'director_email': 'jana.aouad@usj.edu.lb'},
 '716839': {'ldap': '716839',
            'code': '716839',
            'role': 'psg',
            'name': 'Farah EID GHADDAR',
            'poste': 'Coordinateur communication interne et évènementiel',
            'faculty': 'SIO',
            'institution': 'SIO',
            'department': '',
            'email': 'farah.eid1@usj.edu.lb',
            'director_name': 'Jana AOUAD AWAD',
            'director_code': '709004',
            'director_ldap': '709004',
            'director_email': 'jana.aouad@usj.edu.lb'},
 '716287': {'ldap': '716287',
            'code': '716287',
            'role': 'psg',
            'name': 'Jessica KARAM MOUSSA',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'SIO',
            'institution': 'SIO',
            'department': '',
            'email': 'jessica.karam1@usj.edu.lb',
            'director_name': 'Jana AOUAD AWAD',
            'director_code': '709004',
            'director_ldap': '709004',
            'director_email': 'jana.aouad@usj.edu.lb'},
 '716024': {'ldap': '716024',
            'code': '716024',
            'role': 'psg',
            'name': 'Aline NASR',
            'poste': "Chargé d'information et de communication",
            'faculty': 'SIO',
            'institution': 'SIO',
            'department': '',
            'email': 'aline.nasr2@usj.edu.lb',
            'director_name': 'Jana AOUAD AWAD',
            'director_code': '709004',
            'director_ldap': '709004',
            'director_email': 'jana.aouad@usj.edu.lb'},
 '713729': {'ldap': '713729',
            'code': '713729',
            'role': 'psg',
            'name': 'Perla ABDEL NOUR GHAWITIAN',
            'poste': 'Chargé de support administratif',
            'faculty': 'FSE',
            'institution': 'FSE',
            'department': '',
            'email': 'perla.abdelnour@usj.edu.lb',
            'director_name': 'Jean-François VERNE',
            'director_code': '710677',
            'director_ldap': '710677',
            'director_email': 'jean-francois.verne@usj.edu.lb'},
 '710677': {'ldap': '710677',
            'code': '710677',
            'role': 'director',
            'name': 'Jean-François VERNE',
            'poste': 'Doyen de la Faculté de sciences économiques',
            'faculty': 'FSE',
            'institution': 'FSE',
            'department': '',
            'email': 'jean-francois.verne@usj.edu.lb'},
 '705276': {'ldap': '705276',
            'code': '705276',
            'role': 'psg',
            'name': 'Cynthia MENASSA MAALOUF',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'FSE',
            'institution': 'FSE',
            'department': '',
            'email': 'cynthia.maalouf@usj.edu.lb',
            'director_name': 'Jean-François VERNE',
            'director_code': '710677',
            'director_ldap': '710677',
            'director_email': 'jean-francois.verne@usj.edu.lb'},
 '716135': {'ldap': '716135',
            'code': '716135',
            'role': 'psg',
            'name': 'Lara NASR AKL',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'FSE',
            'institution': 'FSE',
            'department': '',
            'email': 'lara.nasr@usj.edu.lb',
            'director_name': 'Jean-François VERNE',
            'director_code': '710677',
            'director_ldap': '710677',
            'director_email': 'jean-francois.verne@usj.edu.lb'},
 '709742': {'ldap': '709742',
            'code': '709742',
            'role': 'psg',
            'name': 'Eliane BOU KHALIL MANSOUR',
            'poste': 'Directeur opérationnel',
            'faculty': 'CPM',
            'institution': 'CPM',
            'department': '',
            'email': 'eliane.boukhalilmansour@usj.edu.lb',
            'director_name': 'Johanna HAWARI BOURJELY',
            'director_code': '702829',
            'director_ldap': '702829',
            'director_email': 'johanna.hawari@usj.edu.lb'},
 '702829': {'ldap': '702829',
            'code': '702829',
            'role': 'director',
            'name': 'Johanna HAWARI BOURJELY',
            'poste': 'Directeur du centre professionnel de médiation',
            'faculty': 'CPM',
            'institution': 'CPM',
            'department': '',
            'email': 'johanna.hawari@usj.edu.lb'},
 '709050': {'ldap': '709050',
            'code': '709050',
            'role': 'psg',
            'name': 'Zalfa YOUNES KHATER',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'CPM',
            'institution': 'CPM',
            'department': '',
            'email': 'zalfa.khater@usj.edu.lb',
            'director_name': 'Johanna HAWARI BOURJELY',
            'director_code': '702829',
            'director_ldap': '702829',
            'director_email': 'johanna.hawari@usj.edu.lb'},
 '717764': {'ldap': '717764',
            'code': '717764',
            'role': 'psg',
            'name': 'Marie-Claire BADR',
            'poste': 'Magasinier',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'marie-claire.badr@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '706340': {'ldap': '706340',
            'code': '706340',
            'role': 'director',
            'name': 'Joseph RUSTOM',
            'poste': 'Directeur de la Bibliothèque Orientale',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'joseph.rustom@usj.edu.lb'},
 '714929': {'ldap': '714929',
            'code': '714929',
            'role': 'psg',
            'name': 'Cloé BARCHA',
            'poste': 'Médiateur culturel',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'cloe.barcha1@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '718380': {'ldap': '718380',
            'code': '718380',
            'role': 'psg',
            'name': 'Ghinwa CHELALA',
            'poste': 'Agent de numérisation',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'ghinwa.chelala@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '718305': {'ldap': '718305',
            'code': '718305',
            'role': 'psg',
            'name': 'Esber CHOUEIRI (EL)',
            'poste': 'Agent de numérisation',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'esber.choueiri@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '708428': {'ldap': '708428',
            'code': '708428',
            'role': 'psg',
            'name': 'Karam HOYEK (EL)',
            'poste': 'Gestionnaire des manuscrits et des espaces physiques',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'karam.hoyek@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '718431': {'ldap': '718431',
            'code': '718431',
            'role': 'psg',
            'name': 'Nadim KAMEL',
            'poste': 'Agent de numérisation',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'nadim.kamel@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '713510': {'ldap': '713510',
            'code': '713510',
            'role': 'psg',
            'name': 'Marina MATTAR',
            'poste': 'Chargé de gestion et de conservation',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'marina.mattar@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '705221': {'ldap': '705221',
            'code': '705221',
            'role': 'psg',
            'name': 'Daniella MAZRAANI (EL)',
            'poste': 'Bibliothécaire spécialisé',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'daniella.mazraani@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '718804': {'ldap': '718804',
            'code': '718804',
            'role': 'psg',
            'name': 'Adrien Henri NAFFAH',
            'poste': 'Bibliothécaire',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'adrienhenri.naffah1@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '717517': {'ldap': '717517',
            'code': '717517',
            'role': 'psg',
            'name': 'Maya NAZZAL HAROUNI (EL)',
            'poste': 'Bibliothécaire en chef',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'maya.nazzalharouni@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '716428': {'ldap': '716428',
            'code': '716428',
            'role': 'psg',
            'name': 'Rabih RACHED',
            'poste': 'Chargé de conservation préventive de photos',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'rabih.rached1@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '706913': {'ldap': '706913',
            'code': '706913',
            'role': 'psg',
            'name': 'Jessy SLEIMAN GHANEM',
            'poste': 'Bibliothécaire spécialisé',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'jessy.sleiman@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '719475': {'ldap': '719475',
            'code': '719475',
            'role': 'psg',
            'name': 'Elsa Maya ZAKHIA',
            'poste': 'Archiviste',
            'faculty': 'BO',
            'institution': 'BO',
            'department': '',
            'email': 'elsa.zakhia@usj.edu.lb',
            'director_name': 'Joseph RUSTOM',
            'director_code': '706340',
            'director_ldap': '706340',
            'director_email': 'joseph.rustom@usj.edu.lb'},
 '712071': {'ldap': '712071',
            'code': '712071',
            'role': 'psg',
            'name': 'Ahmad ABDEL HAMID',
            'poste': 'Technicien',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'ahmad.abdelhamid@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '713691': {'ldap': '713691',
            'code': '713691',
            'role': 'director',
            'name': 'Joseph YOUNES',
            'poste': 'Administrateur du Campus des sciences médicales',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'joseph.younes@usj.edu.lb'},
 '710935': {'ldap': '710935',
            'code': '710935',
            'role': 'psg',
            'name': 'Fady BASSILA',
            'poste': 'Appariteur',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'fady.bassila@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '710454': {'ldap': '710454',
            'code': '710454',
            'role': 'psg',
            'name': 'Wissam BOU MANSOUR',
            'poste': 'Bibliothécaire-adjoint',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'wissam.boumansour@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '714799': {'ldap': '714799',
            'code': '714799',
            'role': 'psg',
            'name': 'Alain BOU NAFEH',
            'poste': 'Surveillant de site',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'alain.bounafeh1@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '716713': {'ldap': '716713',
            'code': '716713',
            'role': 'psg',
            'name': 'Marlie BSAIBESS BOU KADDAHA',
            'poste': 'Bibliothécaire',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'marlie.bsaibess@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '714978': {'ldap': '714978',
            'code': '714978',
            'role': 'psg',
            'name': 'Elias CHAAYA',
            'poste': 'Technicien',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'elias.chaaya@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '702226': {'ldap': '702226',
            'code': '702226',
            'role': 'psg',
            'name': 'Hatem DALI (EL)',
            'poste': 'Agent de sécurité',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'hatem.dali@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '702227': {'ldap': '702227',
            'code': '702227',
            'role': 'psg',
            'name': 'Mahmoud DALI (EL)',
            'poste': 'Agent de sécurité',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'mahmoud.dali@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '716645': {'ldap': '716645',
            'code': '716645',
            'role': 'psg',
            'name': 'Georges DEBS',
            'poste': 'Agent de sécurité',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'georges.debs@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '702671': {'ldap': '702671',
            'code': '702671',
            'role': 'psg',
            'name': 'Eliane FARES ABOU HANNA',
            'poste': 'Secrétaire de campus',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'eliane.abouhanna@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '713972': {'ldap': '713972',
            'code': '713972',
            'role': 'psg',
            'name': 'Dany GERGES',
            'poste': 'Intendant de campus',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'dany.gerges@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '708343': {'ldap': '708343',
            'code': '708343',
            'role': 'psg',
            'name': 'Tony HADDAD',
            'poste': "Agent d'accueil",
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'tony.haddad1@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '717307': {'ldap': '717307',
            'code': '717307',
            'role': 'psg',
            'name': 'Myriame HILAL GERGES',
            'poste': "Agent d'accueil et caissier",
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'myriame.hilal@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '703815': {'ldap': '703815',
            'code': '703815',
            'role': 'psg',
            'name': 'Abdel llah HUSSEIN',
            'poste': "Agent de maintenance et d'entretien",
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'abdelllah.hussein@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '705128': {'ldap': '705128',
            'code': '705128',
            'role': 'psg',
            'name': 'Rania MAROUN',
            'poste': "Agent de propreté et d'hygiène",
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'rania.maroun@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '712085': {'ldap': '712085',
            'code': '712085',
            'role': 'psg',
            'name': 'Mélissa MEFLEH JABBOUR',
            'poste': 'Bibliothécaire spécialisé',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'melissa.mefleh@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '719286': {'ldap': '719286',
            'code': '719286',
            'role': 'psg',
            'name': 'Dani NEHME',
            'poste': 'Technicien',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'dani.nehme@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '710127': {'ldap': '710127',
            'code': '710127',
            'role': 'psg',
            'name': 'Maroun RAHAL',
            'poste': 'Appariteur',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'maroun.rahal@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '710789': {'ldap': '710789',
            'code': '710789',
            'role': 'psg',
            'name': 'Johnny ZEINOUN',
            'poste': 'Agent administratif',
            'faculty': 'CSM',
            'institution': 'CSM',
            'department': '',
            'email': 'johnny.zeinoun@usj.edu.lb',
            'director_name': 'Joseph YOUNES',
            'director_code': '713691',
            'director_ldap': '713691',
            'director_email': 'joseph.younes@usj.edu.lb'},
 '713339': {'ldap': '713339',
            'code': '713339',
            'role': 'psg',
            'name': 'Nour AOUN FARROUKH',
            'poste': 'bibliothécaire spécialisé',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'nour.aoun@usj.edu.lb',
            'director_name': 'Leila KASSATLY RIZK',
            'director_code': '704275',
            'director_ldap': '704275',
            'director_email': 'leila.rizk@usj.edu.lb'},
 '704275': {'ldap': '704275',
            'code': '704275',
            'role': 'director',
            'name': 'Leila KASSATLY RIZK',
            'poste': 'Directeur de bibliothèque',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'leila.rizk@usj.edu.lb'},
 '700862': {'ldap': '700862',
            'code': '700862',
            'role': 'psg',
            'name': 'Tanios ASMAR (EL)',
            'poste': 'Bibliothécaire-adjoint',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'tanios.asmar@usj.edu.lb',
            'director_name': 'Leila KASSATLY RIZK',
            'director_code': '704275',
            'director_ldap': '704275',
            'director_email': 'leila.rizk@usj.edu.lb'},
 '718025': {'ldap': '718025',
            'code': '718025',
            'role': 'psg',
            'name': 'Hala HADDAD (EL) IBRAHIM',
            'poste': 'Bibliothécaire',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'hala.haddad@usj.edu.lb',
            'director_name': 'Leila KASSATLY RIZK',
            'director_code': '704275',
            'director_ldap': '704275',
            'director_email': 'leila.rizk@usj.edu.lb'},
 '705057': {'ldap': '705057',
            'code': '705057',
            'role': 'psg',
            'name': 'Charifé MALLAH',
            'poste': 'Bibliothécaire de référence',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'charife.mallah@usj.edu.lb',
            'director_name': 'Leila KASSATLY RIZK',
            'director_code': '704275',
            'director_ldap': '704275',
            'director_email': 'leila.rizk@usj.edu.lb'},
 '705480': {'ldap': '705480',
            'code': '705480',
            'role': 'psg',
            'name': 'Mountaha MOUKANZAH YOUAKIM',
            'poste': 'Bibliothécaire de référence',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'mountaha.moukanzah@usj.edu.lb',
            'director_name': 'Leila KASSATLY RIZK',
            'director_code': '704275',
            'director_ldap': '704275',
            'director_email': 'leila.rizk@usj.edu.lb'},
 '718090': {'ldap': '718090',
            'code': '718090',
            'role': 'psg',
            'name': 'Krystel SAFI',
            'poste': 'Bibliothécaire',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'krystel.safi@usj.edu.lb',
            'director_name': 'Leila KASSATLY RIZK',
            'director_code': '704275',
            'director_ldap': '704275',
            'director_email': 'leila.rizk@usj.edu.lb'},
 '707061': {'ldap': '707061',
            'code': '707061',
            'role': 'psg',
            'name': 'Chady TANNOUS',
            'poste': 'Bibliothécaire-adjoint',
            'faculty': 'CFDSS',
            'institution': 'CFDSS',
            'department': '',
            'email': 'chadi.tannous@usj.edu.lb',
            'director_name': 'Leila KASSATLY RIZK',
            'director_code': '704275',
            'director_ldap': '704275',
            'director_email': 'leila.rizk@usj.edu.lb'},
 '712501': {'ldap': '712501',
            'code': '712501',
            'role': 'psg',
            'name': 'Hiba AHMADIE (EL)',
            'poste': 'Documentaliste',
            'faculty': 'CEDROMA',
            'institution': 'CEDROMA',
            'department': '',
            'email': 'hiba.ahmadie@usj.edu.lb',
            'director_name': 'Léna GANNAGE',
            'director_code': '702831',
            'director_ldap': '702831',
            'director_email': 'lena.gannage@usj.edu.lb'},
 '702831': {'ldap': '702831',
            'code': '702831',
            'role': 'director',
            'name': 'Léna GANNAGE',
            'poste': "Directeur du Centre d'études des droits du monde arabe",
            'faculty': 'CEDROMA',
            'institution': 'CEDROMA',
            'department': '',
            'email': 'lena.gannage@usj.edu.lb'},
 '706237': {'ldap': '706237',
            'code': '706237',
            'role': 'psg',
            'name': 'Zeina RISHA',
            'poste': 'Coordinateur administratif',
            'faculty': 'CEDROMA',
            'institution': 'CEDROMA',
            'department': '',
            'email': 'zeina.risha@usj.edu.lb',
            'director_name': 'Léna GANNAGE',
            'director_code': '702831',
            'director_ldap': '702831',
            'director_email': 'lena.gannage@usj.edu.lb'},
 '716041': {'ldap': '716041',
            'code': '716041',
            'role': 'psg',
            'name': 'Mirna ABI NAHED ISKANDAR',
            'poste': 'Chargé de support académique',
            'faculty': 'FS',
            'institution': 'FS',
            'department': '',
            'email': 'myrna.abinahed@usj.edu.lb',
            'director_name': 'Maher ABBOUD',
            'director_code': '700040',
            'director_ldap': '700040',
            'director_email': 'maher.abboud@usj.edu.lb'},
 '700040': {'ldap': '700040',
            'code': '700040',
            'role': 'director',
            'name': 'Maher ABBOUD',
            'poste': 'Doyen de la Faculté des sciences',
            'faculty': 'FS',
            'institution': 'FS',
            'department': '',
            'email': 'maher.abboud@usj.edu.lb'},
 '710788': {'ldap': '710788',
            'code': '710788',
            'role': 'psg',
            'name': 'Rita ABOU JAOUDE BRAX',
            'poste': 'coordinateur administratif des affaires académiques',
            'faculty': 'FS',
            'institution': 'FS',
            'department': '',
            'email': 'rita.brax@usj.edu.lb',
            'director_name': 'Maher ABBOUD',
            'director_code': '700040',
            'director_ldap': '700040',
            'director_email': 'maher.abboud@usj.edu.lb'},
 '703637': {'ldap': '703637',
            'code': '703637',
            'role': 'psg',
            'name': 'Gladys HAYKAL',
            'poste': 'Assistant aux affaires académiques',
            'faculty': 'FS',
            'institution': 'FS',
            'department': '',
            'email': 'gladys.haykal@usj.edu.lb',
            'director_name': 'Maher ABBOUD',
            'director_code': '700040',
            'director_ldap': '700040',
            'director_email': 'maher.abboud@usj.edu.lb'},
 '704283': {'ldap': '704283',
            'code': '704283',
            'role': 'psg',
            'name': 'Hilda HNEIN',
            'poste': 'Assistant de laboratoire',
            'faculty': 'FS',
            'institution': 'FS',
            'department': '',
            'email': 'hilda.hnein@usj.edu.lb',
            'director_name': 'Maher ABBOUD',
            'director_code': '700040',
            'director_ldap': '700040',
            'director_email': 'maher.abboud@usj.edu.lb'},
 '712102': {'ldap': '712102',
            'code': '712102',
            'role': 'psg',
            'name': 'Jeannette KHOURY (EL)',
            'poste': 'Chargé de support administratif',
            'faculty': 'FS',
            'institution': 'FS',
            'department': '',
            'email': 'jeannette.khoury@usj.edu.lb',
            'director_name': 'Maher ABBOUD',
            'director_code': '700040',
            'director_ldap': '700040',
            'director_email': 'maher.abboud@usj.edu.lb'},
 '705176': {'ldap': '705176',
            'code': '705176',
            'role': 'psg',
            'name': 'Rita MATAR MATAR',
            'poste': 'Assistant de laboratoire',
            'faculty': 'FS',
            'institution': 'FS',
            'department': '',
            'email': 'rita.matar@usj.edu.lb',
            'director_name': 'Maher ABBOUD',
            'director_code': '700040',
            'director_ldap': '700040',
            'director_email': 'maher.abboud@usj.edu.lb'},
 '706119': {'ldap': '706119',
            'code': '706119',
            'role': 'psg',
            'name': 'Gerges RAI (EL)',
            'poste': 'Chargé de support académique',
            'faculty': 'FS',
            'institution': 'FS',
            'department': '',
            'email': 'georges.rai@usj.edu.lb',
            'director_name': 'Maher ABBOUD',
            'director_code': '700040',
            'director_ldap': '700040',
            'director_email': 'maher.abboud@usj.edu.lb'},
 '703053': {'ldap': '703053',
            'code': '703053',
            'role': 'psg',
            'name': 'Salma GHORAYEB (EL) YAGHI',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'INCI',
            'institution': 'INCI',
            'department': '',
            'email': 'salma.ghorayeb@usj.edu.lb',
            'director_name': 'Marc IBRAHIM',
            'director_code': '703840',
            'director_ldap': '703840',
            'director_email': 'marc.Ibrahim@usj.edu.lb'},
 '703840': {'ldap': '703840',
            'code': '703840',
            'role': 'director',
            'name': 'Marc IBRAHIM',
            'poste': "Directeur de l' Institut national des télécommunications et de l'informatique",
            'faculty': 'INCI',
            'institution': 'INCI',
            'department': '',
            'email': 'marc.Ibrahim@usj.edu.lb'},
 '715855': {'ldap': '715855',
            'code': '715855',
            'role': 'psg',
            'name': 'Sirine ABOU ISMAIL',
            'poste': 'Technicien de laboratoire',
            'faculty': 'LRM',
            'institution': 'LRM',
            'department': '',
            'email': 'sirine.abouismail1@usj.edu.lb',
            'director_name': 'Marianne ABI FADEL',
            'director_code': '700162',
            'director_ldap': '700162',
            'director_email': 'marianne.abifadel@usj.edu.lb'},
 '700162': {'ldap': '700162',
            'code': '700162',
            'role': 'director',
            'name': 'Marianne ABI FADEL',
            'poste': 'Directeur du Laboratoire Rodolphe Mérieux-Liban',
            'faculty': 'LRM',
            'institution': 'LRM',
            'department': '',
            'email': 'marianne.abifadel@usj.edu.lb'},
 '709546': {'ldap': '709546',
            'code': '709546',
            'role': 'psg',
            'name': 'Danielle CHAAYA',
            'poste': 'Assistant de laboratoire',
            'faculty': 'LRM',
            'institution': 'LRM',
            'department': '',
            'email': 'danielle.chaaya@usj.edu.lb',
            'director_name': 'Marianne ABI FADEL',
            'director_code': '700162',
            'director_ldap': '700162',
            'director_email': 'marianne.abifadel@usj.edu.lb'},
 '717735': {'ldap': '717735',
            'code': '717735',
            'role': 'psg',
            'name': 'Dana MATTAR',
            'poste': 'Technicien de laboratoire',
            'faculty': 'LRM',
            'institution': 'LRM',
            'department': '',
            'email': 'dana.mattar1@usj.edu.lb',
            'director_name': 'Marianne ABI FADEL',
            'director_code': '700162',
            'director_ldap': '700162',
            'director_email': 'marianne.abifadel@usj.edu.lb'},
 '714696': {'ldap': '714696',
            'code': '714696',
            'role': 'psg',
            'name': 'Laurice TABET',
            'poste': 'Technicien de laboratoire',
            'faculty': 'LRM',
            'institution': 'LRM',
            'department': '',
            'email': 'laurice.tabet1@usj.edu.lb',
            'director_name': 'Marianne ABI FADEL',
            'director_code': '700162',
            'director_ldap': '700162',
            'director_email': 'marianne.abifadel@usj.edu.lb'},
 '700864': {'ldap': '700864',
            'code': '700864',
            'role': 'psg',
            'name': 'Sabine ASMAR (EL) SAAD',
            'poste': 'coordinateur de la formation pratique et des stages',
            'faculty': 'ETLAM',
            'institution': 'ETLAM',
            'department': '',
            'email': 'sabine.saad@usj.edu.lb',
            'director_name': 'Marianne ABI FADEL',
            'director_code': '700162',
            'director_ldap': '700162',
            'director_email': 'marianne.abifadel@usj.edu.lb'},
 '718301': {'ldap': '718301',
            'code': '718301',
            'role': 'psg',
            'name': 'Joy GHANEM',
            'poste': 'Technicien de laboratoire',
            'faculty': 'ETLAM',
            'institution': 'ETLAM',
            'department': '',
            'email': 'joy.ghanem1@usj.edu.lb',
            'director_name': 'Marianne ABI FADEL',
            'director_code': '700162',
            'director_ldap': '700162',
            'director_email': 'marianne.abifadel@usj.edu.lb'},
 '712077': {'ldap': '712077',
            'code': '712077',
            'role': 'psg',
            'name': 'Rabiha RAHBANY',
            'poste': 'Assistant de laboratoire',
            'faculty': 'ETLAM',
            'institution': 'ETLAM',
            'department': '',
            'email': 'rabiha.rahbany@usj.edu.lb',
            'director_name': 'Marianne ABI FADEL',
            'director_code': '700162',
            'director_ldap': '700162',
            'director_email': 'marianne.abifadel@usj.edu.lb'},
 '715810': {'ldap': '715810',
            'code': '715810',
            'role': 'psg',
            'name': 'Rana ABOU GHANTOUS MALEK',
            'poste': 'Chargé de communication',
            'faculty': 'FDSP',
            'institution': 'FDSP',
            'department': '',
            'email': 'rana.aboughantous@usj.edu.lb',
            'director_name': 'Marie-Claude NAJM KOBEH',
            'director_code': '705687',
            'director_ldap': '705687',
            'director_email': 'marieclaude.najm@usj.edu.lb'},
 '705687': {'ldap': '705687',
            'code': '705687',
            'role': 'director',
            'name': 'Marie-Claude NAJM KOBEH',
            'poste': 'Doyen de la Faculté de droit et des sciences politiques',
            'faculty': 'FDSP',
            'institution': 'FDSP',
            'department': '',
            'email': 'marieclaude.najm@usj.edu.lb'},
 '703425': {'ldap': '703425',
            'code': '703425',
            'role': 'psg',
            'name': 'Renée HAKIM GHOSN',
            'poste': 'Chargé de support académique',
            'faculty': 'FDSP',
            'institution': 'FDSP',
            'department': '',
            'email': 'renee.hakimghosn@usj.edu.lb',
            'director_name': 'Marie-Claude NAJM KOBEH',
            'director_code': '705687',
            'director_ldap': '705687',
            'director_email': 'marieclaude.najm@usj.edu.lb'},
 '704704': {'ldap': '704704',
            'code': '704704',
            'role': 'psg',
            'name': 'Salma KHOURY NOUJAIM',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'FDSP',
            'institution': 'FDSP',
            'department': '',
            'email': 'salma.noujaim@usj.edu.lb',
            'director_name': 'Marie-Claude NAJM KOBEH',
            'director_code': '705687',
            'director_ldap': '705687',
            'director_email': 'marieclaude.najm@usj.edu.lb'},
 '718023': {'ldap': '718023',
            'code': '718023',
            'role': 'psg',
            'name': 'Joyce TYAN HAROUN',
            'poste': 'Chargé de support administratif',
            'faculty': 'FDSP',
            'institution': 'FDSP',
            'department': '',
            'email': 'joyce.tyan@usj.edu.lb',
            'director_name': 'Marie-Claude NAJM KOBEH',
            'director_code': '705687',
            'director_ldap': '705687',
            'director_email': 'marieclaude.najm@usj.edu.lb'},
 '708773': {'ldap': '708773',
            'code': '708773',
            'role': 'psg',
            'name': 'Joel CHALHOUB',
            'poste': 'Gestionnaire du centre sportif',
            'faculty': 'SSPORT',
            'institution': 'SSPORT',
            'department': '',
            'email': 'joel.chalhoub@usj.edu.lb',
            'director_name': 'Maroun KHOURY (EL)',
            'director_code': '704446',
            'director_ldap': '704446',
            'director_email': 'maroun.khoury@usj.edu.lb'},
 '704446': {'ldap': '704446',
            'code': '704446',
            'role': 'director',
            'name': 'Maroun KHOURY (EL)',
            'poste': 'Directeur du Service de sport',
            'faculty': 'SSPORT',
            'institution': 'SSPORT',
            'department': '',
            'email': 'maroun.khoury@usj.edu.lb'},
 '713411': {'ldap': '713411',
            'code': '713411',
            'role': 'psg',
            'name': 'Mario MATTA',
            'poste': 'Animateur des activités sportives',
            'faculty': 'SSPORT',
            'institution': 'SSPORT',
            'department': '',
            'email': 'mario.matta@usj.edu.lb',
            'director_name': 'Maroun KHOURY (EL)',
            'director_code': '704446',
            'director_ldap': '704446',
            'director_email': 'maroun.khoury@usj.edu.lb'},
 '703245': {'ldap': '703245',
            'code': '703245',
            'role': 'psg',
            'name': 'Danielle RENNO KHOURY(EL)',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'SSPORT',
            'institution': 'SSPORT',
            'department': '',
            'email': 'danielle.elkhoury@usj.edu.lb',
            'director_name': 'Maroun KHOURY (EL)',
            'director_code': '704446',
            'director_ldap': '704446',
            'director_email': 'maroun.khoury@usj.edu.lb'},
 '707116': {'ldap': '707116',
            'code': '707116',
            'role': 'psg',
            'name': 'Chafic TAYEH',
            'poste': 'Animateur des activités sportives',
            'faculty': 'SSPORT',
            'institution': 'SSPORT',
            'department': '',
            'email': 'chafic.tayeh@usj.edu.lb',
            'director_name': 'Maroun KHOURY (EL)',
            'director_code': '704446',
            'director_ldap': '704446',
            'director_email': 'maroun.khoury@usj.edu.lb'},
 '719415': {'ldap': '719415',
            'code': '719415',
            'role': 'psg',
            'name': 'Sarah CHACCOUR',
            'poste': 'Chargé de support académique',
            'faculty': 'ETIB',
            'institution': 'ETIB',
            'department': '',
            'email': 'sarah.chaccour1@usj.edu.lb',
            'director_name': 'Mary YAZBECK',
            'director_code': '707394',
            'director_ldap': '707394',
            'director_email': 'mary.yazbeck@usj.edu.lb'},
 '707394': {'ldap': '707394',
            'code': '707394',
            'role': 'director',
            'name': 'Mary YAZBECK',
            'poste': "Directrice de l' École de traducteurs et d'interprètes de Beyrouth",
            'faculty': 'ETIB',
            'institution': 'ETIB',
            'department': '',
            'email': 'mary.yazbeck@usj.edu.lb'},
 '717030': {'ldap': '717030',
            'code': '717030',
            'role': 'psg',
            'name': 'Ralda SALAMOUN JABRE',
            'poste': 'Médiateur culturel',
            'faculty': 'MPL',
            'institution': 'MPL',
            'department': '',
            'email': 'ralda.salamoun@usj.edu.lb',
            'director_name': 'Maya HAIDAR BOUSTANI',
            'director_code': '703358',
            'director_ldap': '703358',
            'director_email': 'maya.boustani@usj.edu.lb'},
 '703358': {'ldap': '703358',
            'code': '703358',
            'role': 'director',
            'name': 'Maya HAIDAR BOUSTANI',
            'poste': 'Directeur du musée de préhistoire libanais',
            'faculty': 'MPL',
            'institution': 'MPL',
            'department': '',
            'email': 'maya.boustani@usj.edu.lb'},
 '716351': {'ldap': '716351',
            'code': '716351',
            'role': 'psg',
            'name': 'Ninar AZAR EL NACHMY',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'ISSP',
            'institution': 'ISSP',
            'department': '',
            'email': 'ninar.azar1@usj.edu.lb',
            'director_name': 'Michèle KOSREMELLI ASMAR',
            'director_code': '704773',
            'director_ldap': '704773',
            'director_email': 'michele.asmar@usj.edu.lb'},
 '704773': {'ldap': '704773',
            'code': '704773',
            'role': 'director',
            'name': 'Michèle KOSREMELLI ASMAR',
            'poste': "Directrice de l' Institut supérieur de santé publique",
            'faculty': 'ISSP',
            'institution': 'ISSP',
            'department': '',
            'email': 'michele.asmar@usj.edu.lb'},
 '715998': {'ldap': '715998',
            'code': '715998',
            'role': 'psg',
            'name': 'Aline BEHEIT MATTAR',
            'poste': 'Coordinateur administratif de recherche',
            'faculty': 'ISSP',
            'institution': 'ISSP',
            'department': '',
            'email': 'aline.beheit@usj.edu.lb',
            'director_name': 'Michèle KOSREMELLI ASMAR',
            'director_code': '704773',
            'director_ldap': '704773',
            'director_email': 'michele.asmar@usj.edu.lb'},
 '715592': {'ldap': '715592',
            'code': '715592',
            'role': 'psg',
            'name': 'Julia BOU DIB',
            'poste': 'Assistant de projet et de recherche',
            'faculty': 'ISSP',
            'institution': 'ISSP',
            'department': '',
            'email': 'julia.boudib1@usj.edu.lb',
            'director_name': 'Michèle KOSREMELLI ASMAR',
            'director_code': '704773',
            'director_ldap': '704773',
            'director_email': 'michele.asmar@usj.edu.lb'},
 '703885': {'ldap': '703885',
            'code': '703885',
            'role': 'psg',
            'name': 'Christiane ISSA BAKHACHE',
            'poste': 'Coordinateur administratif',
            'faculty': 'ISSP',
            'institution': 'ISSP',
            'department': '',
            'email': 'christiane.issa@usj.edu.lb',
            'director_name': 'Michèle KOSREMELLI ASMAR',
            'director_code': '704773',
            'director_ldap': '704773',
            'director_email': 'michele.asmar@usj.edu.lb'},
 '717235': {'ldap': '717235',
            'code': '717235',
            'role': 'psg',
            'name': 'Kawthar JABER FADLALLAH',
            'poste': 'Assistant de projet et de recherche',
            'faculty': 'ISSP',
            'institution': 'ISSP',
            'department': '',
            'email': 'kawthar.jaber@usj.edu.lb',
            'director_name': 'Michèle KOSREMELLI ASMAR',
            'director_code': '704773',
            'director_ldap': '704773',
            'director_email': 'michele.asmar@usj.edu.lb'},
 '715595': {'ldap': '715595',
            'code': '715595',
            'role': 'psg',
            'name': 'Ranim SAHILY (EL) HAIDAR',
            'poste': 'Assistant de projet et de recherche',
            'faculty': 'ISSP',
            'institution': 'ISSP',
            'department': '',
            'email': 'ranim.sahily@usj.edu.lb',
            'director_name': 'Michèle KOSREMELLI ASMAR',
            'director_code': '704773',
            'director_ldap': '704773',
            'director_email': 'michele.asmar@usj.edu.lb'},
 '710381': {'ldap': '710381',
            'code': '710381',
            'role': 'psg',
            'name': 'Elie ABI DAHER',
            'poste': 'Appariteur',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'elie.abidaher@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '705836': {'ldap': '705836',
            'code': '705836',
            'role': 'director',
            'name': 'Mireille NASSIF CHAMOUN',
            'poste': 'Administrateur p.i. du Campus des sciences humaines',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'mireille.chamoun@usj.edu.lb'},
 '700311': {'ldap': '700311',
            'code': '700311',
            'role': 'psg',
            'name': 'Marie ABOU CHAAYA AWAD',
            'poste': 'Agent administratif',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'marie.awad@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '700552': {'ldap': '700552',
            'code': '700552',
            'role': 'psg',
            'name': 'Badr AGHAJOUN',
            'poste': 'Technicien spécialisé',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'badr.aghajoun@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '714882': {'ldap': '714882',
            'code': '714882',
            'role': 'psg',
            'name': 'NALLUSAMY ALAGU',
            'poste': "Agent de maintenance et d'entretien",
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'nallusamy.alagu@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '700731': {'ldap': '700731',
            'code': '700731',
            'role': 'psg',
            'name': 'Aouad AOUAD',
            'poste': 'Agent de sécurité',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'aouad.aouad@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '701017': {'ldap': '701017',
            'code': '701017',
            'role': 'psg',
            'name': 'Elias AYOUB',
            'poste': 'Coursier-Chauffeur',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'elias.ayoub@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '710036': {'ldap': '710036',
            'code': '710036',
            'role': 'psg',
            'name': 'Elie CHAHINE',
            'poste': 'Technicien',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'elie.chahine4@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '702924': {'ldap': '702924',
            'code': '702924',
            'role': 'psg',
            'name': 'Roger GERGES',
            'poste': 'Intendant',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'roger.gerges@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '703832': {'ldap': '703832',
            'code': '703832',
            'role': 'psg',
            'name': 'Elias IBRAHIM',
            'poste': "Agent de maintenance et d'entretien",
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'elias.ibrahim@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '708382': {'ldap': '708382',
            'code': '708382',
            'role': 'psg',
            'name': 'Youssef KHALED',
            'poste': 'Technicien spécialisé',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'youssef.khaled@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '711132': {'ldap': '711132',
            'code': '711132',
            'role': 'psg',
            'name': 'Suzanne KHALIFE ISHAK',
            'poste': 'Secrétaire de campus',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'suzanne.ishak@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '704602': {'ldap': '704602',
            'code': '704602',
            'role': 'psg',
            'name': 'Karim KHOURY',
            'poste': "Agent d'accueil",
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'karim.khoury@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '705396': {'ldap': '705396',
            'code': '705396',
            'role': 'psg',
            'name': 'Badri MOGHAMES',
            'poste': 'Agent de sécurité',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'badri.moghames@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '705685': {'ldap': '705685',
            'code': '705685',
            'role': 'psg',
            'name': 'Antoine NAJM',
            'poste': 'Appariteur',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'antoine.najm@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '710599': {'ldap': '710599',
            'code': '710599',
            'role': 'psg',
            'name': 'Elian RAHAL',
            'poste': 'Technicien spécialisé',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'elian.rahal@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '707056': {'ldap': '707056',
            'code': '707056',
            'role': 'psg',
            'name': 'Tony TANNOURY',
            'poste': 'Technicien',
            'faculty': 'CSH',
            'institution': 'CSH',
            'department': '',
            'email': 'tony.tannoury@usj.edu.lb',
            'director_name': 'Mireille NASSIF CHAMOUN',
            'director_code': '705836',
            'director_ldap': '705836',
            'director_email': 'mireille.chamoun@usj.edu.lb'},
 '719141': {'ldap': '719141',
            'code': '719141',
            'role': 'psg',
            'name': 'Nadine AKL',
            'poste': 'Aide-éducatrice',
            'faculty': 'GSJ',
            'institution': 'GSJ',
            'department': '',
            'email': 'nadine.akl@usj.edu.lb',
            'director_name': 'Mirna OSSEIRAN',
            'director_code': '703285',
            'director_ldap': '703285',
            'director_email': 'mirna.osseiran@usj.edu.lb'},
 '703285': {'ldap': '703285',
            'code': '703285',
            'role': 'director',
            'name': 'Mirna OSSEIRAN',
            'poste': 'Directeur de la Garderie Saint-Joseph de Beyrouth',
            'faculty': 'GSJ',
            'institution': 'GSJ',
            'department': '',
            'email': 'mirna.osseiran@usj.edu.lb'},
 '714690': {'ldap': '714690',
            'code': '714690',
            'role': 'psg',
            'name': 'Samar AMMOUNI NASSER',
            'poste': 'Educatrice',
            'faculty': 'GSJ',
            'institution': 'GSJ',
            'department': '',
            'email': 'samar.ammouni1@usj.edu.lb',
            'director_name': 'Mirna OSSEIRAN',
            'director_code': '703285',
            'director_ldap': '703285',
            'director_email': 'mirna.osseiran@usj.edu.lb'},
 '719139': {'ldap': '719139',
            'code': '719139',
            'role': 'psg',
            'name': 'Vanessa ATALLAH',
            'poste': 'Educatrice',
            'faculty': 'GSJ',
            'institution': 'GSJ',
            'department': '',
            'email': 'vanessa.atallah2@usj.edu.lb',
            'director_name': 'Mirna OSSEIRAN',
            'director_code': '703285',
            'director_ldap': '703285',
            'director_email': 'mirna.osseiran@usj.edu.lb'},
 '702235': {'ldap': '702235',
            'code': '702235',
            'role': 'psg',
            'name': 'Georgina DAMIEN HAJJ(EL)',
            'poste': 'Educatrice',
            'faculty': 'GSJ',
            'institution': 'GSJ',
            'department': '',
            'email': 'georgina.damien@usj.edu.lb',
            'director_name': 'Mirna OSSEIRAN',
            'director_code': '703285',
            'director_ldap': '703285',
            'director_email': 'mirna.osseiran@usj.edu.lb'},
 '709835': {'ldap': '709835',
            'code': '709835',
            'role': 'psg',
            'name': 'Thérèse HADDAD (EL) DEBS',
            'poste': "Agent de propreté et d'hygiène",
            'faculty': 'GSJ',
            'institution': 'GSJ',
            'department': '',
            'email': 'therese.haddad@usj.edu.lb',
            'director_name': 'Mirna OSSEIRAN',
            'director_code': '703285',
            'director_ldap': '703285',
            'director_email': 'mirna.osseiran@usj.edu.lb'},
 '716950': {'ldap': '716950',
            'code': '716950',
            'role': 'psg',
            'name': 'Rachelle HANNA MAKHOUL',
            'poste': 'Infirmière puéricultrice',
            'faculty': 'GSJ',
            'institution': 'GSJ',
            'department': '',
            'email': 'rachelle.hanna1@usj.edu.lb',
            'director_name': 'Mirna OSSEIRAN',
            'director_code': '703285',
            'director_ldap': '703285',
            'director_email': 'mirna.osseiran@usj.edu.lb'},
 '718309': {'ldap': '718309',
            'code': '718309',
            'role': 'psg',
            'name': 'Rita HJAYLI BOGHOSSIAN',
            'poste': 'Aide-éducatrice',
            'faculty': 'GSJ',
            'institution': 'GSJ',
            'department': '',
            'email': 'rita.hjayli@usj.edu.lb',
            'director_name': 'Mirna OSSEIRAN',
            'director_code': '703285',
            'director_ldap': '703285',
            'director_email': 'mirna.osseiran@usj.edu.lb'},
 '704553': {'ldap': '704553',
            'code': '704553',
            'role': 'psg',
            'name': 'Noha KHOUEIRY (EL)',
            'poste': 'Educatrice',
            'faculty': 'GSJ',
            'institution': 'GSJ',
            'department': '',
            'email': 'noha.khoueiry@usj.edu.lb',
            'director_name': 'Mirna OSSEIRAN',
            'director_code': '703285',
            'director_ldap': '703285',
            'director_email': 'mirna.osseiran@usj.edu.lb'},
 '711618': {'ldap': '711618',
            'code': '711618',
            'role': 'psg',
            'name': 'Jacqueline MERHI NEMER',
            'poste': 'Aide-éducatrice',
            'faculty': 'GSJ',
            'institution': 'GSJ',
            'department': '',
            'email': 'jacqueline.merhinemer@usj.edu.lb',
            'director_name': 'Mirna OSSEIRAN',
            'director_code': '703285',
            'director_ldap': '703285',
            'director_email': 'mirna.osseiran@usj.edu.lb'},
 '718295': {'ldap': '718295',
            'code': '718295',
            'role': 'psg',
            'name': 'Josiane SLEIMAN ABI CHACRA',
            'poste': 'Educatrice',
            'faculty': 'GSJ',
            'institution': 'GSJ',
            'department': '',
            'email': 'josiane.sleiman@usj.edu.lb',
            'director_name': 'Mirna OSSEIRAN',
            'director_code': '703285',
            'director_ldap': '703285',
            'director_email': 'mirna.osseiran@usj.edu.lb'},
 '709163': {'ldap': '709163',
            'code': '709163',
            'role': 'psg',
            'name': 'Geaourgious BARADHY',
            'poste': 'Spécialiste achats',
            'faculty': 'SAA',
            'institution': 'SAA',
            'department': '',
            'email': 'georges.baradhy@usj.edu.lb',
            'director_name': 'Mona JARJOUR TABET',
            'director_code': '707765',
            'director_ldap': '707765',
            'director_email': 'mona.tabet@usj.edu.lb'},
 '707765': {'ldap': '707765',
            'code': '707765',
            'role': 'director',
            'name': 'Mona JARJOUR TABET',
            'poste': "Directeur du service des achats et de l'approvisionnement",
            'faculty': 'SAA',
            'institution': 'SAA',
            'department': '',
            'email': 'mona.tabet@usj.edu.lb'},
 '713213': {'ldap': '713213',
            'code': '713213',
            'role': 'psg',
            'name': 'Georges BATHANI (EL)',
            'poste': 'Agent de stock',
            'faculty': 'SAA',
            'institution': 'SAA',
            'department': '',
            'email': 'georges.bathani@usj.edu.lb',
            'director_name': 'Mona JARJOUR TABET',
            'director_code': '707765',
            'director_ldap': '707765',
            'director_email': 'mona.tabet@usj.edu.lb'},
 '717490': {'ldap': '717490',
            'code': '717490',
            'role': 'psg',
            'name': 'Mirella KHAIRALLAH MURR (EL)',
            'poste': 'Spécialiste achats',
            'faculty': 'SAA',
            'institution': 'SAA',
            'department': '',
            'email': 'mirella.khairallah@usj.edu.lb',
            'director_name': 'Mona JARJOUR TABET',
            'director_code': '707765',
            'director_ldap': '707765',
            'director_email': 'mona.tabet@usj.edu.lb'},
 '713048': {'ldap': '713048',
            'code': '713048',
            'role': 'psg',
            'name': 'Elsy KORKMAZ HACHEM (EL)',
            'poste': 'Spécialiste achats',
            'faculty': 'SAA',
            'institution': 'SAA',
            'department': '',
            'email': 'elsy.korkmaz@usj.edu.lb',
            'director_name': 'Mona JARJOUR TABET',
            'director_code': '707765',
            'director_ldap': '707765',
            'director_email': 'mona.tabet@usj.edu.lb'},
 '716712': {'ldap': '716712',
            'code': '716712',
            'role': 'psg',
            'name': 'Joêlle KREIDY MOUZAWAK',
            'poste': 'Chargé de support administratif',
            'faculty': 'SAA',
            'institution': 'SAA',
            'department': '',
            'email': 'joelle.kreidy@usj.edu.lb',
            'director_name': 'Mona JARJOUR TABET',
            'director_code': '707765',
            'director_ldap': '707765',
            'director_email': 'mona.tabet@usj.edu.lb'},
 '719798': {'ldap': '719798',
            'code': '719798',
            'role': 'psg',
            'name': 'Amine MRAD',
            'poste': 'Magasinier',
            'faculty': 'SAA',
            'institution': 'SAA',
            'department': '',
            'email': 'amine.mrad@usj.edu.lb',
            'director_name': 'Mona JARJOUR TABET',
            'director_code': '707765',
            'director_ldap': '707765',
            'director_email': 'mona.tabet@usj.edu.lb'},
 '716880': {'ldap': '716880',
            'code': '716880',
            'role': 'psg',
            'name': 'Ramona SEMAAN AYOUB',
            'poste': 'Agent de service',
            'faculty': 'SAA',
            'institution': 'SAA',
            'department': '',
            'email': 'ramona.semaan@usj.edu.lb',
            'director_name': 'Mona JARJOUR TABET',
            'director_code': '707765',
            'director_ldap': '707765',
            'director_email': 'mona.tabet@usj.edu.lb'},
 '700590': {'ldap': '700590',
            'code': '700590',
            'role': 'psg',
            'name': 'Joseph AKIKI',
            'poste': 'Appariteur',
            'faculty': 'FLSH',
            'institution': 'FLSH',
            'department': '',
            'email': 'joseph.akiki@usj.edu.lb',
            'director_name': 'Myrna GANNAGE',
            'director_code': '702832',
            'director_ldap': '702832',
            'director_email': 'myrna.gannage@usj.edu.lb'},
 '702832': {'ldap': '702832',
            'code': '702832',
            'role': 'director',
            'name': 'Myrna GANNAGE',
            'poste': 'Doyen de la Faculté des lettres et des sciences humaines Ramez G. Chagoury',
            'faculty': 'FLSH',
            'institution': 'FLSH',
            'department': '',
            'email': 'myrna.gannage@usj.edu.lb'},
 '701015': {'ldap': '701015',
            'code': '701015',
            'role': 'psg',
            'name': 'Darine AYOUB CHAAYA',
            'poste': 'Agent de service',
            'faculty': 'FLSH',
            'institution': 'FLSH',
            'department': '',
            'email': 'darine.ayoub@usj.edu.lb',
            'director_name': 'Myrna GANNAGE',
            'director_code': '702832',
            'director_ldap': '702832',
            'director_email': 'myrna.gannage@usj.edu.lb'},
 '701139': {'ldap': '701139',
            'code': '701139',
            'role': 'psg',
            'name': 'Nada BADARO SALIBA',
            'poste': 'Coordinateur du laboratoire de télédétection',
            'faculty': 'FLSH',
            'institution': 'FLSH',
            'department': '',
            'email': 'nada.saliba@usj.edu.lb',
            'director_name': 'Myrna GANNAGE',
            'director_code': '702832',
            'director_ldap': '702832',
            'director_email': 'myrna.gannage@usj.edu.lb'},
 '704510': {'ldap': '704510',
            'code': '704510',
            'role': 'psg',
            'name': 'Samia KHAWAND (EL)',
            'poste': 'Coordinateur administratif',
            'faculty': 'FLSH',
            'institution': 'FLSH',
            'department': '',
            'email': 'samia.khawand@usj.edu.lb',
            'director_name': 'Myrna GANNAGE',
            'director_code': '702832',
            'director_ldap': '702832',
            'director_email': 'myrna.gannage@usj.edu.lb'},
 '716873': {'ldap': '716873',
            'code': '716873',
            'role': 'psg',
            'name': 'Thérèse KHOURY (EL) BEJJANY (EL)',
            'poste': 'Chargé de support académique',
            'faculty': 'FLSH',
            'institution': 'FLSH',
            'department': '',
            'email': 'therese.khoury3@usj.edu.lb',
            'director_name': 'Myrna GANNAGE',
            'director_code': '702832',
            'director_ldap': '702832',
            'director_email': 'myrna.gannage@usj.edu.lb'},
 '705436': {'ldap': '705436',
            'code': '705436',
            'role': 'psg',
            'name': 'Wadiha MOUAWAD IBRAHIM',
            'poste': 'Chargé de support académique',
            'faculty': 'FLSH',
            'institution': 'FLSH',
            'department': '',
            'email': 'wadiha.mouawad@usj.edu.lb',
            'director_name': 'Myrna GANNAGE',
            'director_code': '702832',
            'director_ldap': '702832',
            'director_email': 'myrna.gannage@usj.edu.lb'},
 '706156': {'ldap': '706156',
            'code': '706156',
            'role': 'psg',
            'name': 'Michel RASSI (EL)',
            'poste': 'Appariteur',
            'faculty': 'FLSH',
            'institution': 'FLSH',
            'department': '',
            'email': 'michel.rassi@usj.edu.lb',
            'director_name': 'Myrna GANNAGE',
            'director_code': '702832',
            'director_ldap': '702832',
            'director_email': 'myrna.gannage@usj.edu.lb'},
 '706276': {'ldap': '706276',
            'code': '706276',
            'role': 'psg',
            'name': 'Eliane RIZKALLAH',
            'poste': 'Chargé de support académique',
            'faculty': 'FLSH',
            'institution': 'FLSH',
            'department': '',
            'email': 'eliane.rizcallah@usj.edu.lb',
            'director_name': 'Myrna GANNAGE',
            'director_code': '702832',
            'director_ldap': '702832',
            'director_email': 'myrna.gannage@usj.edu.lb'},
 '714258': {'ldap': '714258',
            'code': '714258',
            'role': 'psg',
            'name': 'Sandy TABRI',
            'poste': 'Chargé de support académique',
            'faculty': 'FLSH',
            'institution': 'FLSH',
            'department': '',
            'email': 'sandy.tabri@usj.edu.lb',
            'director_name': 'Myrna GANNAGE',
            'director_code': '702832',
            'director_ldap': '702832',
            'director_email': 'myrna.gannage@usj.edu.lb'},
 '714753': {'ldap': '714753',
            'code': '714753',
            'role': 'psg',
            'name': 'Rima WEHBE ABOU JAOUDE',
            'poste': 'Agent administratif',
            'faculty': 'SAP',
            'institution': 'SAP',
            'department': '',
            'email': 'rima.wehbe@usj.edu.lb',
            'director_name': 'Myrna GANNAGE',
            'director_code': '702832',
            'director_ldap': '702832',
            'director_email': 'myrna.gannage@usj.edu.lb'},
 '717678': {'ldap': '717678',
            'code': '717678',
            'role': 'psg',
            'name': 'Toufic BAAKLINI',
            'poste': 'Comptable',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'toufic.baaklini1@usj.edu.lb',
            'director_name': 'Nada AKL ALLAM',
            'director_code': '700616',
            'director_ldap': '700616',
            'director_email': 'nada.allam@usj.edu.lb'},
 '700616': {'ldap': '700616',
            'code': '700616',
            'role': 'director',
            'name': 'Nada AKL ALLAM',
            'poste': 'Directeur du service de la comptabilité',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'nada.allam@usj.edu.lb'},
 '716071': {'ldap': '716071',
            'code': '716071',
            'role': 'psg',
            'name': 'Nagham HADDAD',
            'poste': 'Comptable',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'nagham.haddad2@usj.edu.lb',
            'director_name': 'Nada AKL ALLAM',
            'director_code': '700616',
            'director_ldap': '700616',
            'director_email': 'nada.allam@usj.edu.lb'},
 '703292': {'ldap': '703292',
            'code': '703292',
            'role': 'psg',
            'name': 'Pascale HADDAD (EL) SALIBA',
            'poste': 'Coordinateur informatique des données comptables',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'pascale.saliba@usj.edu.lb',
            'director_name': 'Nada AKL ALLAM',
            'director_code': '700616',
            'director_ldap': '700616',
            'director_email': 'nada.allam@usj.edu.lb'},
 '703516': {'ldap': '703516',
            'code': '703516',
            'role': 'psg',
            'name': 'Widad HANNOUN NASSAR',
            'poste': 'Comptable',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'widad.nassar@usj.edu.lb',
            'director_name': 'Nada AKL ALLAM',
            'director_code': '700616',
            'director_ldap': '700616',
            'director_email': 'nada.allam@usj.edu.lb'},
 '709013': {'ldap': '709013',
            'code': '709013',
            'role': 'psg',
            'name': 'Chadi KHOURY (EL)',
            'poste': 'Comptable analyste',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'chadi.khoury1@usj.edu.lb',
            'director_name': 'Nada AKL ALLAM',
            'director_code': '700616',
            'director_ldap': '700616',
            'director_email': 'nada.allam@usj.edu.lb'},
 '705310': {'ldap': '705310',
            'code': '705310',
            'role': 'psg',
            'name': 'Nawal MERHEJ TANIOS',
            'poste': 'Comptable analyste',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'nawal.tanios@usj.edu.lb',
            'director_name': 'Nada AKL ALLAM',
            'director_code': '700616',
            'director_ldap': '700616',
            'director_email': 'nada.allam@usj.edu.lb'},
 '717724': {'ldap': '717724',
            'code': '717724',
            'role': 'psg',
            'name': 'Elise MEZHER SAIKALI (EL)',
            'poste': 'Comptable',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'elise.mezher1@usj.edu.lb',
            'director_name': 'Nada AKL ALLAM',
            'director_code': '700616',
            'director_ldap': '700616',
            'director_email': 'nada.allam@usj.edu.lb'},
 '705705': {'ldap': '705705',
            'code': '705705',
            'role': 'psg',
            'name': 'Fadia NAKHLE KAHWAGI',
            'poste': 'Directeur-adjoint - Reporting et analyse comptable',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'fadia.kahwaji@usj.edu.lb',
            'director_name': 'Nada AKL ALLAM',
            'director_code': '700616',
            'director_ldap': '700616',
            'director_email': 'nada.allam@usj.edu.lb'},
 '708684': {'ldap': '708684',
            'code': '708684',
            'role': 'psg',
            'name': 'Elias NEHME BHAMDOUNI',
            'poste': 'Comptable analyste',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'elias.nehmebhamdouni@usj.edu.lb',
            'director_name': 'Nada AKL ALLAM',
            'director_code': '700616',
            'director_ldap': '700616',
            'director_email': 'nada.allam@usj.edu.lb'},
 '716965': {'ldap': '716965',
            'code': '716965',
            'role': 'psg',
            'name': 'Maria NOHRA',
            'poste': 'Comptable',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'maria.nohra2@usj.edu.lb',
            'director_name': 'Nada AKL ALLAM',
            'director_code': '700616',
            'director_ldap': '700616',
            'director_email': 'nada.allam@usj.edu.lb'},
 '707336': {'ldap': '707336',
            'code': '707336',
            'role': 'psg',
            'name': 'Dany YACHOUH',
            'poste': 'Agent administratif',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'dany.yachouh@usj.edu.lb',
            'director_name': 'Nada AKL ALLAM',
            'director_code': '700616',
            'director_ldap': '700616',
            'director_email': 'nada.allam@usj.edu.lb'},
 '716338': {'ldap': '716338',
            'code': '716338',
            'role': 'psg',
            'name': 'Anthony ZAGHLOUL',
            'poste': 'Comptable',
            'faculty': 'SCO',
            'institution': 'SCO',
            'department': '',
            'email': 'anthony.zaghloul@usj.edu.lb',
            'director_name': 'Nada AKL ALLAM',
            'director_code': '700616',
            'director_ldap': '700616',
            'director_email': 'nada.allam@usj.edu.lb'},
 '708998': {'ldap': '708998',
            'code': '708998',
            'role': 'psg',
            'name': 'Mireille ABDALLAH',
            'poste': 'Chargé de support administratif - centre de soins',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'mireille.abdallah@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '702691': {'ldap': '702691',
            'code': '702691',
            'role': 'director',
            'name': 'Nada FARHAT MCHAYLEH',
            'poste': 'Doyen de la Faculté de médecine dentaire',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '700110': {'ldap': '700110',
            'code': '700110',
            'role': 'psg',
            'name': 'Elie ABDEL SALIB',
            'poste': 'Technicien spécialisé - Team leader',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'elie.abdelsalib@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '716426': {'ldap': '716426',
            'code': '716426',
            'role': 'psg',
            'name': 'Rachelle ABDEL-HADI',
            'poste': 'Chargé de support administratif - centre de soins',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'rachelle.abdel-hadi@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '700379': {'ldap': '700379',
            'code': '700379',
            'role': 'psg',
            'name': 'Aline ABOU JAOUDE AOUN',
            'poste': 'Chargé de support administratif - centre de soins',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'aline.aoun@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '719119': {'ldap': '719119',
            'code': '719119',
            'role': 'psg',
            'name': 'Mariana ABOU KHALIL KOSSAYFI',
            'poste': "Chargé d'accueil et de facturation",
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'mariana.aboukhalil@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '717633': {'ldap': '717633',
            'code': '717633',
            'role': 'psg',
            'name': 'Zaher ABOU SEIF',
            'poste': 'Technicien spécialisé',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'zaher.abouseif@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '718296': {'ldap': '718296',
            'code': '718296',
            'role': 'psg',
            'name': 'Carla ASSAAD DAOUD',
            'poste': "Agent de propreté et d'hygiène",
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'carla.assaaddaoud@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '714143': {'ldap': '714143',
            'code': '714143',
            'role': 'psg',
            'name': 'Vanessa ATALLAH',
            'poste': 'Chargé de support administratif',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'vanessa.atallah@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '713929': {'ldap': '713929',
            'code': '713929',
            'role': 'psg',
            'name': 'Gretta AZAR TAHAN',
            'poste': 'Agent de stock',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'gretta.azar@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '701087': {'ldap': '701087',
            'code': '701087',
            'role': 'psg',
            'name': 'Georges AZZI (AL)',
            'poste': 'Magasinier',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'georges.azzi@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '716555': {'ldap': '716555',
            'code': '716555',
            'role': 'psg',
            'name': 'Pamela BEAINO (EL)',
            'poste': 'Chargé de support académique',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'pamela.beaino@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '702401': {'ldap': '702401',
            'code': '702401',
            'role': 'psg',
            'name': 'Samira DIAB CHAHINE',
            'poste': 'Agent de stock',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'samira.diab@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '702673': {'ldap': '702673',
            'code': '702673',
            'role': 'psg',
            'name': 'Lamis FARES BADR',
            'poste': 'Chargé de support administratif - centre de soins',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'lamis.badr@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '702987': {'ldap': '702987',
            'code': '702987',
            'role': 'psg',
            'name': 'Hoda GHANEM NAMMOUR',
            'poste': 'Chargé de support administratif - centre de soins',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'hoda.nammour@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '712608': {'ldap': '712608',
            'code': '712608',
            'role': 'psg',
            'name': 'Marie HABCHI KEYROUZ',
            'poste': 'Agent de laboratoire',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'marie.habchi@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '716602': {'ldap': '716602',
            'code': '716602',
            'role': 'psg',
            'name': 'Souad HABCHI KEYROUZ',
            'poste': 'Agent de stock',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'souad.habchi@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '710375': {'ldap': '710375',
            'code': '710375',
            'role': 'psg',
            'name': 'Ghada HABIB',
            'poste': 'Chargé de support administratif - centre de soins',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'ghada.habib@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '710154': {'ldap': '710154',
            'code': '710154',
            'role': 'psg',
            'name': 'Marianne HADDAD HATEM',
            'poste': 'Technicien spécialisé - imagerie médicale',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'marianne.haddad@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '703383': {'ldap': '703383',
            'code': '703383',
            'role': 'psg',
            'name': 'Souad HAJJ (EL) MOUSSA FEGHALI(EL)',
            'poste': 'Chargé de support académique',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'souad.moussa@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '709838': {'ldap': '709838',
            'code': '709838',
            'role': 'psg',
            'name': 'Salwa HAJJ (EL) TANIOS',
            'poste': 'Agent de laboratoire',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'salwa.hajj@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '703583': {'ldap': '703583',
            'code': '703583',
            'role': 'psg',
            'name': 'Yacoub HASSOUN',
            'poste': 'Technicien spécialisé',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'yacoub.hassoun@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '703797': {'ldap': '703797',
            'code': '703797',
            'role': 'psg',
            'name': 'Hala HOYEK (AL) SLIM',
            'poste': 'Coordinateur des affaires comptables',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'hala.slim@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '717629': {'ldap': '717629',
            'code': '717629',
            'role': 'psg',
            'name': 'Perla KHATTAR',
            'poste': 'Technicien de laboratoire dentaire',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'perla.khattar@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '704527': {'ldap': '704527',
            'code': '704527',
            'role': 'psg',
            'name': 'Leyla KHAZEN MERHEJ',
            'poste': "Chargé d'accueil et de facturation",
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'leyla.merhej@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '704530': {'ldap': '704530',
            'code': '704530',
            'role': 'psg',
            'name': 'Rita KHEIR MOACDIEH',
            'poste': 'Assistant aux affaires académiques',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'rita.moacdieh@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '717526': {'ldap': '717526',
            'code': '717526',
            'role': 'psg',
            'name': 'Soha KHOURY (EL) HARROUZ',
            'poste': 'Caissier',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'soha.khouryelharrouz@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '717589': {'ldap': '717589',
            'code': '717589',
            'role': 'psg',
            'name': 'Mariana KHOURY (EL) NAWAR (EL)',
            'poste': 'Caissier',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'mariana.khoury@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '704688': {'ldap': '704688',
            'code': '704688',
            'role': 'psg',
            'name': 'Paulette KHOURY ABOU CHAAYA',
            'poste': 'Directeur opérationnel du Centre de soins dentaires',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'paulette.abouchaaya@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '712072': {'ldap': '712072',
            'code': '712072',
            'role': 'psg',
            'name': 'Laure KIZANA ABI SAMRA',
            'poste': 'Agent de laboratoire',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'laure.kizana@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '704730': {'ldap': '704730',
            'code': '704730',
            'role': 'psg',
            'name': 'Antoinette KLEIANY DAHER',
            'poste': 'Agent de laboratoire',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'antoinette.daher@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '705077': {'ldap': '705077',
            'code': '705077',
            'role': 'psg',
            'name': 'Charbel MANSOUR',
            'poste': 'Assistant de laboratoire',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'charbel.mansour@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '719117': {'ldap': '719117',
            'code': '719117',
            'role': 'psg',
            'name': 'Elvire NAKHLEH HARB',
            'poste': 'Chargé de support administratif',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'elvire.nakhleh@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '706194': {'ldap': '706194',
            'code': '706194',
            'role': 'psg',
            'name': 'Nabiha RHAYEM EL KHAWAND',
            'poste': 'Agent administratif',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'nabiha.elkhawand@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '714624': {'ldap': '714624',
            'code': '714624',
            'role': 'psg',
            'name': 'Liliane SAMAHA ATTAR',
            'poste': 'Agent de stock',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'liliane.samaha@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '716632': {'ldap': '716632',
            'code': '716632',
            'role': 'psg',
            'name': 'Pascale SAYAH (EL) FEGHALI (EL)',
            'poste': 'Agent de laboratoire',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'pascale.sayah@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '713329': {'ldap': '713329',
            'code': '713329',
            'role': 'psg',
            'name': 'Amale SKAFF',
            'poste': 'Agent de stock',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'amale.skaff@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '708888': {'ldap': '708888',
            'code': '708888',
            'role': 'psg',
            'name': 'Amal TABET GHOMEID',
            'poste': 'Agent de laboratoire',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'amal.tabet@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '707223': {'ldap': '707223',
            'code': '707223',
            'role': 'psg',
            'name': 'Nawal TURK (EL)',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'nawal.turk@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '716987': {'ldap': '716987',
            'code': '716987',
            'role': 'psg',
            'name': 'Roudaina WEHBE',
            'poste': 'Caissier',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'roudaina.wehbe@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '719121': {'ldap': '719121',
            'code': '719121',
            'role': 'psg',
            'name': 'Charbel ZGHEIB',
            'poste': 'Technicien de laboratoire dentaire',
            'faculty': 'FMD',
            'institution': 'FMD',
            'department': '',
            'email': 'charbel.zgheib5@usj.edu.lb',
            'director_name': 'Nada FARHAT MCHAYLEH',
            'director_code': '702691',
            'director_ldap': '702691',
            'director_email': 'nada.farhatmouchayleh@usj.edu.lb'},
 '717597': {'ldap': '717597',
            'code': '717597',
            'role': 'psg',
            'name': 'Antoinette KHOURY(EL) SAMAHA',
            'poste': 'Coordinateur administratif',
            'faculty': 'MPU',
            'institution': 'MPU',
            'department': '',
            'email': 'antoinette.samaha@usj.edu.lb',
            'director_name': 'Nada MOGHAIZEL NASR',
            'director_code': '705464',
            'director_ldap': '705464',
            'director_email': 'nada.moghaizel-nasr@usj.edu.lb'},
 '705464': {'ldap': '705464',
            'code': '705464',
            'role': 'director',
            'name': 'Nada MOGHAIZEL NASR',
            'poste': 'Délégué de la  Mission de pédagogie universitaire',
            'faculty': 'MPU',
            'institution': 'MPU',
            'department': '',
            'email': 'nada.moghaizel-nasr@usj.edu.lb'},
 '702885': {'ldap': '702885',
            'code': '702885',
            'role': 'psg',
            'name': 'Marie GEHA OHANESSIAN',
            'poste': 'Coordinateur de bureau',
            'faculty': 'SG',
            'institution': 'SG',
            'department': '',
            'email': 'marie.geha@usj.edu.lb',
            'director_name': 'Nadine RIACHI HADDAD',
            'director_code': '706200',
            'director_ldap': '706200',
            'director_email': 'nadine.riachi@usj.edu.lb'},
 '706200': {'ldap': '706200',
            'code': '706200',
            'role': 'director',
            'name': 'Nadine RIACHI HADDAD',
            'poste': 'Secrétaire Général au Secrétariat général',
            'faculty': 'SG',
            'institution': 'SG',
            'department': '',
            'email': 'nadine.riachi@usj.edu.lb'},
 '716928': {'ldap': '716928',
            'code': '716928',
            'role': 'psg',
            'name': 'Donna-Maria SFEILA (EL)',
            'poste': 'Chargé des dossiers',
            'faculty': 'SG',
            'institution': 'SG',
            'department': '',
            'email': 'donna-maria.sfeila1@usj.edu.lb',
            'director_name': 'Nadine RIACHI HADDAD',
            'director_code': '706200',
            'director_ldap': '706200',
            'director_email': 'nadine.riachi@usj.edu.lb'},
 '714138': {'ldap': '714138',
            'code': '714138',
            'role': 'psg',
            'name': 'Valérie ZGHEIB',
            'poste': 'Gestionnaire de projets',
            'faculty': 'SG',
            'institution': 'SG',
            'department': '',
            'email': 'valerie.zgheib1@usj.edu.lb',
            'director_name': 'Nadine RIACHI HADDAD',
            'director_code': '706200',
            'director_ldap': '706200',
            'director_email': 'nadine.riachi@usj.edu.lb'},
 '717303': {'ldap': '717303',
            'code': '717303',
            'role': 'psg',
            'name': 'Charbel ATTIEH',
            'poste': 'Assistant de laboratoire',
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'charbel.attieh@usj.edu.lb',
            'director_name': 'Nassim FARES',
            'director_code': '702663',
            'director_ldap': '702663',
            'director_email': 'nassim.fares@usj.edu.lb'},
 '702663': {'ldap': '702663',
            'code': '702663',
            'role': 'director',
            'name': 'Nassim FARES',
            'poste': 'Directeur du Centre Jacques Loiselet de génétique et de génomique médicales',
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'nassim.fares@usj.edu.lb'},
 '717074': {'ldap': '717074',
            'code': '717074',
            'role': 'psg',
            'name': 'Rita BASSILA MAKHOUL',
            'poste': 'Chargé de support administratif',
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'rita.bassila@usj.edu.lb',
            'director_name': 'Nassim FARES',
            'director_code': '702663',
            'director_ldap': '702663',
            'director_email': 'nassim.fares@usj.edu.lb'},
 '715948': {'ldap': '715948',
            'code': '715948',
            'role': 'psg',
            'name': 'Hala CHAKHTOURA',
            'poste': 'Assistant de laboratoire',
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'hala.chakhtoura1@usj.edu.lb',
            'director_name': 'Nassim FARES',
            'director_code': '702663',
            'director_ldap': '702663',
            'director_email': 'nassim.fares@usj.edu.lb'},
 '716032': {'ldap': '716032',
            'code': '716032',
            'role': 'psg',
            'name': 'Manal CHAMI HADDAD (EL) TANNOUS',
            'poste': 'Chargé de support administratif',
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'manal.chamihaddad@usj.edu.lb',
            'director_name': 'Nassim FARES',
            'director_code': '702663',
            'director_ldap': '702663',
            'director_email': 'nassim.fares@usj.edu.lb'},
 '718320': {'ldap': '718320',
            'code': '718320',
            'role': 'psg',
            'name': 'Riwa CHDID',
            'poste': 'Technicien de laboratoire',
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'riwa.chdid1@usj.edu.lb',
            'director_name': 'Nassim FARES',
            'director_code': '702663',
            'director_ldap': '702663',
            'director_email': 'nassim.fares@usj.edu.lb'},
 '717254': {'ldap': '717254',
            'code': '717254',
            'role': 'psg',
            'name': 'Ghina HIJAZI CHOKER',
            'poste': 'Assistant de laboratoire',
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'ghina.hijazi2@usj.edu.lb',
            'director_name': 'Nassim FARES',
            'director_code': '702663',
            'director_ldap': '702663',
            'director_email': 'nassim.fares@usj.edu.lb'},
 '717919': {'ldap': '717919',
            'code': '717919',
            'role': 'psg',
            'name': 'Ronald HOMSY (EL)',
            'poste': 'Technicien de laboratoire',
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'ronald.homsy@usj.edu.lb',
            'director_name': 'Nassim FARES',
            'director_code': '702663',
            'director_ldap': '702663',
            'director_email': 'nassim.fares@usj.edu.lb'},
 '704538': {'ldap': '704538',
            'code': '704538',
            'role': 'psg',
            'name': 'Issam KHNEISSER',
            'poste': "Chef d'unité de dépistage néonatal",
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'issam.khneisser@usj.edu.lb',
            'director_name': 'Nassim FARES',
            'director_code': '702663',
            'director_ldap': '702663',
            'director_email': 'nassim.fares@usj.edu.lb'},
 '717305': {'ldap': '717305',
            'code': '717305',
            'role': 'psg',
            'name': 'Zeinab MOUNAJJED (EL) KIBBI',
            'poste': 'Assistant de laboratoire',
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'zeinab.mounajjed@usj.edu.lb',
            'director_name': 'Nassim FARES',
            'director_code': '702663',
            'director_ldap': '702663',
            'director_email': 'nassim.fares@usj.edu.lb'},
 '715883': {'ldap': '715883',
            'code': '715883',
            'role': 'psg',
            'name': 'Romy MOUSSALEM',
            'poste': 'Technicien de laboratoire',
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'romy.moussalem1@usj.edu.lb',
            'director_name': 'Nassim FARES',
            'director_code': '702663',
            'director_ldap': '702663',
            'director_email': 'nassim.fares@usj.edu.lb'},
 '708561': {'ldap': '708561',
            'code': '708561',
            'role': 'psg',
            'name': 'Maya RIZKALLAH AZZI (AL)',
            'poste': 'Assistant de laboratoire',
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'maya.rizkallah@usj.edu.lb',
            'director_name': 'Nassim FARES',
            'director_code': '702663',
            'director_ldap': '702663',
            'director_email': 'nassim.fares@usj.edu.lb'},
 '712269': {'ldap': '712269',
            'code': '712269',
            'role': 'psg',
            'name': 'Wardé SEMAAN RAJHA',
            'poste': 'Assistant de laboratoire',
            'faculty': 'CGGM',
            'institution': 'CGGM',
            'department': '',
            'email': 'warde.semaan@usj.edu.lb',
            'director_name': 'Nassim FARES',
            'director_code': '702663',
            'director_ldap': '702663',
            'director_email': 'nassim.fares@usj.edu.lb'},
 '715715': {'ldap': '715715',
            'code': '715715',
            'role': 'psg',
            'name': 'Josiane HELOU (EL)',
            'poste': 'Coordinateur des opérations',
            'faculty': 'CONF',
            'institution': 'CONF',
            'department': '',
            'email': 'josiane.helou2@usj.edu.lb',
            'director_name': 'Nisrine ABDEL NOUR LATTOUF',
            'director_code': '700108',
            'director_ldap': '700108',
            'director_email': 'nisrine.lattouf@usj.edu.lb'},
 '700108': {'ldap': '700108',
            'code': '700108',
            'role': 'director',
            'name': 'Nisrine ABDEL NOUR LATTOUF',
            'poste': "Directrice de l' Institut Confucius",
            'faculty': 'CONF',
            'institution': 'CONF',
            'department': '',
            'email': 'nisrine.lattouf@usj.edu.lb'},
 '700666': {'ldap': '700666',
            'code': '700666',
            'role': 'psg',
            'name': 'Mountaha ALLAWY TANNOURY',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'IPHY',
            'institution': 'IPHY',
            'department': '',
            'email': 'mony.tannoury@usj.edu.lb',
            'director_name': 'Pascal BRAIDY (EL)',
            'director_code': '701630',
            'director_ldap': '701630',
            'director_email': 'pascal.breidy@usj.edu.lb'},
 '701630': {'ldap': '701630',
            'code': '701630',
            'role': 'director',
            'name': 'Pascal BRAIDY (EL)',
            'poste': "Directeur de l' Institut de physiothérapie",
            'faculty': 'IPHY',
            'institution': 'IPHY',
            'department': '',
            'email': 'pascal.breidy@usj.edu.lb'},
 '715419': {'ldap': '715419',
            'code': '715419',
            'role': 'psg',
            'name': 'Ghada AZZI (EL) SEMAAN',
            'poste': 'Chargé de support académique',
            'faculty': 'IPHY',
            'institution': 'IPHY',
            'department': '',
            'email': 'ghada.azzi@usj.edu.lb',
            'director_name': 'Pascal BRAIDY (EL)',
            'director_code': '701630',
            'director_ldap': '701630',
            'director_email': 'pascal.breidy@usj.edu.lb'},
 '716499': {'ldap': '716499',
            'code': '716499',
            'role': 'psg',
            'name': 'Joelle KHOUEIRY (EL) SAWMA',
            'poste': 'Chargé de support administratif',
            'faculty': 'OFP',
            'institution': 'OFP',
            'department': '',
            'email': 'joelle.khoueiry@usj.edu.lb',
            'director_name': 'Pascal MONIN',
            'director_code': '705412',
            'director_ldap': '705412',
            'director_email': 'pascal.monin@usj.edu.lb'},
 '705412': {'ldap': '705412',
            'code': '705412',
            'role': 'director',
            'name': 'Pascal MONIN',
            'poste': "Directeur de l' Observatoire de la fonction publique et de la bonne gouvernance",
            'faculty': 'OFP',
            'institution': 'OFP',
            'department': '',
            'email': 'pascal.monin@usj.edu.lb'},
 '710373': {'ldap': '710373',
            'code': '710373',
            'role': 'psg',
            'name': 'Samir ABI MOUSSA',
            'poste': 'Agent administratif',
            'faculty': 'FSEDU',
            'institution': 'FSEDU',
            'department': '',
            'email': 'samir.abimoussa@usj.edu.lb',
            'director_name': 'Patricia FATA (EL) RACHED',
            'director_code': '702702',
            'director_ldap': '702702',
            'director_email': 'patricia.rached@usj.edu.lb'},
 '702702': {'ldap': '702702',
            'code': '702702',
            'role': 'director',
            'name': 'Patricia FATA (EL) RACHED',
            'poste': "Doyen de la Faculté des sciences de l'éducation",
            'faculty': 'FSEDU',
            'institution': 'FSEDU',
            'department': '',
            'email': 'patricia.rached@usj.edu.lb'},
 '710292': {'ldap': '710292',
            'code': '710292',
            'role': 'psg',
            'name': 'Soha MOAWAD KARAM',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'FSEDU',
            'institution': 'FSEDU',
            'department': '',
            'email': 'soha.moawadkaram@usj.edu.lb',
            'director_name': 'Patricia FATA (EL) RACHED',
            'director_code': '702702',
            'director_ldap': '702702',
            'director_email': 'patricia.rached@usj.edu.lb'},
 '711510': {'ldap': '711510',
            'code': '711510',
            'role': 'psg',
            'name': 'Nicole YANKOVITCH TANNOUS',
            'poste': 'Assistant aux affaires académiques',
            'faculty': 'FSEDU',
            'institution': 'FSEDU',
            'department': '',
            'email': 'nicole.tannous@usj.edu.lb',
            'director_name': 'Patricia FATA (EL) RACHED',
            'director_code': '702702',
            'director_ldap': '702702',
            'director_email': 'patricia.rached@usj.edu.lb'},
 '709870': {'ldap': '709870',
            'code': '709870',
            'role': 'psg',
            'name': 'Alia YOUSSEF HOURANI',
            'poste': 'Agent de service',
            'faculty': 'FSEDU',
            'institution': 'FSEDU',
            'department': '',
            'email': 'alia.youssefhourani@usj.edu.lb',
            'director_name': 'Patricia FATA (EL) RACHED',
            'director_code': '702702',
            'director_ldap': '702702',
            'director_email': 'patricia.rached@usj.edu.lb'},
 '719399': {'ldap': '719399',
            'code': '719399',
            'role': 'psg',
            'name': 'Jessy BOU DAHER KASSIS (EL)',
            'poste': 'maquettiste',
            'faculty': 'CDRAC',
            'institution': 'CDRAC',
            'department': '',
            'email': 'jessy.boudaherkassisel@usj.edu.lb',
            'director_name': 'Pierre JABBOUR',
            'director_code': '715439',
            'director_ldap': '715439',
            'director_email': 'pierre.jabbour1@usj.edu.lb'},
 '715439': {'ldap': '715439',
            'code': '715439',
            'role': 'director',
            'name': 'Pierre JABBOUR',
            'poste': 'Directeur p.i du Centre de documentation et de recherches arabes chrétiennes',
            'faculty': 'CDRAC',
            'institution': 'CDRAC',
            'department': '',
            'email': 'pierre.jabbour1@usj.edu.lb'},
 '702143': {'ldap': '702143',
            'code': '702143',
            'role': 'psg',
            'name': 'Léna DABAHY',
            'poste': "Assistant(e) à l'édition et à la recherche",
            'faculty': 'CDRAC',
            'institution': 'CDRAC',
            'department': '',
            'email': 'lena.dabaghy@usj.edu.lb',
            'director_name': 'Pierre JABBOUR',
            'director_code': '715439',
            'director_ldap': '715439',
            'director_email': 'pierre.jabbour1@usj.edu.lb'},
 '702144': {'ldap': '702144',
            'code': '702144',
            'role': 'psg',
            'name': 'Mona DABAHY',
            'poste': "Gestionnaire de l'édition critique et des manuscrits",
            'faculty': 'CDRAC',
            'institution': 'CDRAC',
            'department': '',
            'email': 'mona.dabaghy@usj.edu.lb',
            'director_name': 'Pierre JABBOUR',
            'director_code': '715439',
            'director_ldap': '715439',
            'director_email': 'pierre.jabbour1@usj.edu.lb'},
 '713076': {'ldap': '713076',
            'code': '713076',
            'role': 'psg',
            'name': 'Rita GEMAYEL (EL) HELOU (EL)',
            'poste': 'Chargé de support administratif',
            'faculty': 'DDA',
            'institution': 'DDA',
            'department': '',
            'email': 'rita.gemayel1@usj.edu.lb',
            'director_name': 'Pierre NAJM',
            'director_code': '705669',
            'director_ldap': '705669',
            'director_email': 'pierre.najm@usj.edu.lb'},
 '705669': {'ldap': '705669',
            'code': '705669',
            'role': 'director',
            'name': 'Pierre NAJM',
            'poste': 'Directeur des admissions',
            'faculty': 'DDA',
            'institution': 'DDA',
            'department': '',
            'email': 'pierre.najm@usj.edu.lb'},
 '715568': {'ldap': '715568',
            'code': '715568',
            'role': 'psg',
            'name': 'Zeina NEMR DIMAS',
            'poste': 'Chargé de support administratif',
            'faculty': 'DDA',
            'institution': 'DDA',
            'department': '',
            'email': 'zeina.nemr@usj.edu.lb',
            'director_name': 'Pierre NAJM',
            'director_code': '705669',
            'director_ldap': '705669',
            'director_email': 'pierre.najm@usj.edu.lb'},
 '719457': {'ldap': '719457',
            'code': '719457',
            'role': 'psg',
            'name': 'Sandy GHOSSEIN (EL)',
            'poste': "Chargé d'études statistiques",
            'faculty': 'CDS',
            'institution': 'CDS',
            'department': '',
            'email': 'sandy.ghossein1@usj.edu.lb',
            'director_name': 'Rami HADDAD (EL)',
            'director_code': '708902',
            'director_ldap': '708902',
            'director_email': 'rami.haddad@usj.edu.lb'},
 '708902': {'ldap': '708902',
            'code': '708902',
            'role': 'director',
            'name': 'Rami HADDAD (EL)',
            'poste': 'Directeur du Centre de statistiques',
            'faculty': 'CDS',
            'institution': 'CDS',
            'department': '',
            'email': 'rami.haddad@usj.edu.lb'},
 '706391': {'ldap': '706391',
            'code': '706391',
            'role': 'psg',
            'name': 'Jacqueline SAAD HARFOUCHE',
            'poste': 'Directeur- adjoint',
            'faculty': 'CDS',
            'institution': 'CDS',
            'department': '',
            'email': 'jacqueline.harfouche@usj.edu.lb',
            'director_name': 'Rami HADDAD (EL)',
            'director_code': '708902',
            'director_ldap': '708902',
            'director_email': 'rami.haddad@usj.edu.lb'},
 '711223': {'ldap': '711223',
            'code': '711223',
            'role': 'psg',
            'name': 'Samar GABRIEL MRAD',
            'poste': 'Coordinateur des projets de recherche subventionnés',
            'faculty': 'VRR',
            'institution': 'VRR',
            'department': '',
            'email': 'samar.gabriel1@usj.edu.lb',
            'director_name': 'Richard MAROUN',
            'director_code': '705129',
            'director_ldap': '705129',
            'director_email': 'richard.maroun@usj.edu.lb'},
 '705129': {'ldap': '705129',
            'code': '705129',
            'role': 'director',
            'name': 'Richard MAROUN',
            'poste': 'Vice-Recteur à la Vice-rectorat à la recherche',
            'faculty': 'VRR',
            'institution': 'VRR',
            'department': '',
            'email': 'richard.maroun@usj.edu.lb'},
 '712480': {'ldap': '712480',
            'code': '712480',
            'role': 'psg',
            'name': 'Régina GEITANI (EL) DIB',
            'poste': 'Coordinateur administratif de recherche',
            'faculty': 'VRR',
            'institution': 'VRR',
            'department': '',
            'email': 'regina.geitani1@usj.edu.lb',
            'director_name': 'Richard MAROUN',
            'director_code': '705129',
            'director_ldap': '705129',
            'director_email': 'richard.maroun@usj.edu.lb'},
 '717010': {'ldap': '717010',
            'code': '717010',
            'role': 'psg',
            'name': 'Georges HAYEK (EL)',
            'poste': 'Développeur senior',
            'faculty': 'VRR',
            'institution': 'VRR',
            'department': '',
            'email': 'georges.hayek4@usj.edu.lb',
            'director_name': 'Richard MAROUN',
            'director_code': '705129',
            'director_ldap': '705129',
            'director_email': 'richard.maroun@usj.edu.lb'},
 '719113': {'ldap': '719113',
            'code': '719113',
            'role': 'psg',
            'name': 'Christelle KASSARGY',
            'poste': 'Chargé de subventions',
            'faculty': 'VRR',
            'institution': 'VRR',
            'department': '',
            'email': 'christelle.kassargy1@usj.edu.lb',
            'director_name': 'Richard MAROUN',
            'director_code': '705129',
            'director_ldap': '705129',
            'director_email': 'richard.maroun@usj.edu.lb'},
 '710453': {'ldap': '710453',
            'code': '710453',
            'role': 'psg',
            'name': 'Elias BOU ROUPHAEL',
            'poste': 'Assistant de laboratoire',
            'faculty': 'ESAR',
            'institution': 'ESAR',
            'department': '',
            'email': 'elias.bourouphael@usj.edu.lb',
            'director_name': 'Richard MITRI',
            'director_code': '716842',
            'director_ldap': '716842',
            'director_email': 'richard.mitri@usj.edu.lb'},
 '716842': {'ldap': '716842',
            'code': '716842',
            'role': 'director',
            'name': 'Richard MITRI',
            'poste': "Directeur de l'Ecole supérieure d'architecture",
            'faculty': 'ESAR',
            'institution': 'ESAR',
            'department': '',
            'email': 'richard.mitri@usj.edu.lb'},
 '704664': {'ldap': '704664',
            'code': '704664',
            'role': 'psg',
            'name': 'Rana KHOURY (EL)',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'ESAR',
            'institution': 'ESAR',
            'department': '',
            'email': 'rana.elkhoury@usj.edu.lb',
            'director_name': 'Richard MITRI',
            'director_code': '716842',
            'director_ldap': '716842',
            'director_email': 'richard.mitri@usj.edu.lb'},
 '703676': {'ldap': '703676',
            'code': '703676',
            'role': 'psg',
            'name': 'Julie HELOU (EL)',
            'poste': 'Chargé de support académique',
            'faculty': 'ESTS',
            'institution': 'ESTS',
            'department': '',
            'email': 'julie.helou@usj.edu.lb',
            'director_name': 'Rima MAWAD',
            'director_code': '705390',
            'director_ldap': '705390',
            'director_email': 'rima.moawad@usj.edu.lb'},
 '705390': {'ldap': '705390',
            'code': '705390',
            'role': 'director',
            'name': 'Rima MAWAD',
            'poste': "Directrice de l' École libanaise de formation sociale",
            'faculty': 'ESTS',
            'institution': 'ESTS',
            'department': '',
            'email': 'rima.moawad@usj.edu.lb'},
 '704471': {'ldap': '704471',
            'code': '704471',
            'role': 'psg',
            'name': 'Tania KHANATI',
            'poste': 'Gestionnaire des projets subventionnés',
            'faculty': 'ESTS',
            'institution': 'ESTS',
            'department': '',
            'email': 'tania.khanaty@usj.edu.lb',
            'director_name': 'Rima MAWAD',
            'director_code': '705390',
            'director_ldap': '705390',
            'director_email': 'rima.moawad@usj.edu.lb'},
 '704411': {'ldap': '704411',
            'code': '704411',
            'role': 'psg',
            'name': 'Thérèse KHAIRALLAH GHANEM',
            'poste': 'Chargé de support académique',
            'faculty': 'FSI',
            'institution': 'FSI',
            'department': '',
            'email': 'therese.khairallah@usj.edu.lb',
            'director_name': 'Rima SASSINE KAZAN',
            'director_code': '706737',
            'director_ldap': '706737',
            'director_email': 'rima.sassine@usj.edu.lb'},
 '706737': {'ldap': '706737',
            'code': '706737',
            'role': 'director',
            'name': 'Rima SASSINE KAZAN',
            'poste': 'Doyen de la Faculté des sciences infirmières',
            'faculty': 'FSI',
            'institution': 'FSI',
            'department': '',
            'email': 'rima.sassine@usj.edu.lb'},
 '704408': {'ldap': '704408',
            'code': '704408',
            'role': 'psg',
            'name': 'Thérèse KHAIRALLAH OBEID',
            'poste': 'Chargé de support académique',
            'faculty': 'FSI',
            'institution': 'FSI',
            'department': '',
            'email': 'therese.obeid@usj.edu.lb',
            'director_name': 'Rima SASSINE KAZAN',
            'director_code': '706737',
            'director_ldap': '706737',
            'director_email': 'rima.sassine@usj.edu.lb'},
 '705439': {'ldap': '705439',
            'code': '705439',
            'role': 'psg',
            'name': 'Wafa MOUAWAD MATTA',
            'poste': 'Chargé de support académique',
            'faculty': 'FSI',
            'institution': 'FSI',
            'department': '',
            'email': 'wafa.mouawad@usj.edu.lb',
            'director_name': 'Rima SASSINE KAZAN',
            'director_code': '706737',
            'director_ldap': '706737',
            'director_email': 'rima.sassine@usj.edu.lb'},
 '701602': {'ldap': '701602',
            'code': '701602',
            'role': 'psg',
            'name': 'Rita BOUSTANY',
            'poste': 'Chargé de support académique',
            'faculty': 'ILE',
            'institution': 'ILE',
            'department': '',
            'email': 'rita.boustany@usj.edu.lb',
            'director_name': 'Rock ACHY (EL)',
            'director_code': '709169',
            'director_ldap': '709169',
            'director_email': 'rock.achy@usj.edu.lb'},
 '709169': {'ldap': '709169',
            'code': '709169',
            'role': 'director',
            'name': 'Rock ACHY (EL)',
            'poste': "Directeur de l' Institut libanais d'éducateurs",
            'faculty': 'ILE',
            'institution': 'ILE',
            'department': '',
            'email': 'rock.achy@usj.edu.lb'},
 '718520': {'ldap': '718520',
            'code': '718520',
            'role': 'psg',
            'name': 'Yolla JARJOUR ABED SATER (EL)',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'ILE',
            'institution': 'ILE',
            'department': '',
            'email': 'yolla.jarjour1@usj.edu.lb',
            'director_name': 'Rock ACHY (EL)',
            'director_code': '709169',
            'director_ldap': '709169',
            'director_email': 'rock.achy@usj.edu.lb'},
 '702921': {'ldap': '702921',
            'code': '702921',
            'role': 'psg',
            'name': 'Marlène NAIM GERGES',
            'poste': 'Bibliothécaire-adjoint',
            'faculty': 'ILE',
            'institution': 'ILE',
            'department': '',
            'email': 'marlene.gerges@usj.edu.lb',
            'director_name': 'Rock ACHY (EL)',
            'director_code': '709169',
            'director_ldap': '709169',
            'director_email': 'rock.achy@usj.edu.lb'},
 '714484': {'ldap': '714484',
            'code': '714484',
            'role': 'psg',
            'name': 'Micha ABDEL NOUR ELIAS',
            'poste': 'Chargé de facutration et de paiement',
            'faculty': 'PTS',
            'institution': 'PTS',
            'department': '',
            'email': 'micha.abdelnour@usj.edu.lb',
            'director_name': 'Roger LTEIF',
            'director_code': '704928',
            'director_ldap': '704928',
            'director_email': 'roger.lteif@usj.edu.lb'},
 '704928': {'ldap': '704928',
            'code': '704928',
            'role': 'director',
            'name': 'Roger LTEIF',
            'poste': 'Directeur du Pôle technologie santé',
            'faculty': 'PTS',
            'institution': 'PTS',
            'department': '',
            'email': 'roger.lteif@usj.edu.lb'},
 '709292': {'ldap': '709292',
            'code': '709292',
            'role': 'psg',
            'name': 'Salwa LAHOUD',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'PTS',
            'institution': 'PTS',
            'department': '',
            'email': 'salwa.lahoud@usj.edu.lb',
            'director_name': 'Roger LTEIF',
            'director_code': '704928',
            'director_ldap': '704928',
            'director_email': 'roger.lteif@usj.edu.lb'},
 '717686': {'ldap': '717686',
            'code': '717686',
            'role': 'psg',
            'name': 'Michelle AOUN',
            'poste': 'Animateur spécialisé',
            'faculty': 'UPT',
            'institution': 'UPT',
            'department': '',
            'email': 'michelle.aoun@usj.edu.lb',
            'director_name': 'Roland TOMB',
            'director_code': '707163',
            'director_ldap': '707163',
            'director_email': 'roland.tomb@usj.edu.lb'},
 '707163': {'ldap': '707163',
            'code': '707163',
            'role': 'director',
            'name': 'Roland TOMB',
            'poste': "Directeur de l' Université pour tous",
            'faculty': 'UPT',
            'institution': 'UPT',
            'department': '',
            'email': 'roland.tomb@usj.edu.lb'},
 '710371': {'ldap': '710371',
            'code': '710371',
            'role': 'psg',
            'name': 'Pascale FARES',
            'poste': 'Chargé de support administratif',
            'faculty': 'UPT',
            'institution': 'UPT',
            'department': '',
            'email': 'pascale.fares@usj.edu.lb',
            'director_name': 'Roland TOMB',
            'director_code': '707163',
            'director_ldap': '707163',
            'director_email': 'roland.tomb@usj.edu.lb'},
 '705525': {'ldap': '705525',
            'code': '705525',
            'role': 'psg',
            'name': 'Bassam MOUSSA',
            'poste': "Agent de maintenance et d'entretien",
            'faculty': 'UPT',
            'institution': 'UPT',
            'department': '',
            'email': 'bassam.moussa@usj.edu.lb',
            'director_name': 'Roland TOMB',
            'director_code': '707163',
            'director_ldap': '707163',
            'director_email': 'roland.tomb@usj.edu.lb'},
 '710507': {'ldap': '710507',
            'code': '710507',
            'role': 'psg',
            'name': 'Nancy SAAB',
            'poste': 'Coordinateur de la communication et des affaires académiques',
            'faculty': 'UPT',
            'institution': 'UPT',
            'department': '',
            'email': 'nancy.saab1@usj.edu.lb',
            'director_name': 'Roland TOMB',
            'director_code': '707163',
            'director_ldap': '707163',
            'director_email': 'roland.tomb@usj.edu.lb'},
 '716357': {'ldap': '716357',
            'code': '716357',
            'role': 'psg',
            'name': 'Vanessa SAYDE',
            'poste': 'Orthopédagogue',
            'faculty': 'UPT',
            'institution': 'UPT',
            'department': '',
            'email': 'vanessa.sayde1@usj.edu.lb',
            'director_name': 'Roland TOMB',
            'director_code': '707163',
            'director_ldap': '707163',
            'director_email': 'roland.tomb@usj.edu.lb'},
 '716981': {'ldap': '716981',
            'code': '716981',
            'role': 'psg',
            'name': 'Stéphanie SLEIMAN KHOURY (EL)',
            'poste': 'Coordinateur académique de la formation inclusive',
            'faculty': 'UPT',
            'institution': 'UPT',
            'department': '',
            'email': 'stephanie.sleiman@usj.edu.lb',
            'director_name': 'Roland TOMB',
            'director_code': '707163',
            'director_ldap': '707163',
            'director_email': 'roland.tomb@usj.edu.lb'},
 '717685': {'ldap': '717685',
            'code': '717685',
            'role': 'psg',
            'name': 'Nour TANNOUS BOU GHOSN',
            'poste': 'Orthopédagogue',
            'faculty': 'UPT',
            'institution': 'UPT',
            'department': '',
            'email': 'nour.tannous2@usj.edu.lb',
            'director_name': 'Roland TOMB',
            'director_code': '707163',
            'director_ldap': '707163',
            'director_email': 'roland.tomb@usj.edu.lb'},
 '718312': {'ldap': '718312',
            'code': '718312',
            'role': 'psg',
            'name': 'Michelle BASSIL',
            'poste': 'Chargé de support administratif',
            'faculty': 'CEMAM',
            'institution': 'CEMAM',
            'department': '',
            'email': 'michelle.bassil1@usj.edu.lb',
            'director_name': 'Roula ABI HABIB KHOURY',
            'director_code': '700162',
            'director_ldap': '700162',
            'director_email': 'roula.khoury@usj.edu.lb'},
 '716843': {'ldap': '716843',
            'code': '716843',
            'role': 'psg',
            'name': 'Jimmy MALLAH (EL) ASSOUAD (EL)',
            'poste': 'Chargé de support administratif',
            'faculty': 'FSR',
            'institution': 'FSR',
            'department': '',
            'email': 'jimmy.mallah1@usj.edu.lb',
            'director_name': 'Salah ABOUJAOUDE s.j.',
            'director_code': '700373',
            'director_ldap': '700373',
            'director_email': 'salah.aboujaoude@usj.edu.lb'},
 '700373': {'ldap': '700373',
            'code': '700373',
            'role': 'director',
            'name': 'Salah ABOUJAOUDE s.j.',
            'poste': 'Doyen de la Faculté des sciences religieuses',
            'faculty': 'FSR',
            'institution': 'FSR',
            'department': '',
            'email': 'salah.aboujaoude@usj.edu.lb'},
 '716883': {'ldap': '716883',
            'code': '716883',
            'role': 'psg',
            'name': 'Josette MEHANNA BARHOUCHE',
            'poste': 'Documentaliste',
            'faculty': 'FSR',
            'institution': 'FSR',
            'department': '',
            'email': 'josette.mehanna@usj.edu.lb',
            'director_name': 'Salah ABOUJAOUDE s.j.',
            'director_code': '700373',
            'director_ldap': '700373',
            'director_email': 'salah.aboujaoude@usj.edu.lb'},
 '705773': {'ldap': '705773',
            'code': '705773',
            'role': 'psg',
            'name': 'Josette NASRALLAH FREM',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'FSR',
            'institution': 'FSR',
            'department': '',
            'email': 'josette.nasrallah@usj.edu.lb',
            'director_name': 'Salah ABOUJAOUDE s.j.',
            'director_code': '700373',
            'director_ldap': '700373',
            'director_email': 'salah.aboujaoude@usj.edu.lb'},
 '710521': {'ldap': '710521',
            'code': '710521',
            'role': 'psg',
            'name': 'Céline GHOBRIL DAGHER',
            'poste': 'Coordinateur administratif',
            'faculty': 'EDUSJ',
            'institution': 'EDUSJ',
            'department': '',
            'email': 'celine.dagher@usj.edu.lb',
            'director_name': 'Salim DACCACHE s.j.',
            'director_code': '702156',
            'director_ldap': '702156',
            'director_email': 'salim.daccache@usj.edu.lb'},
 '702156': {'ldap': '702156',
            'code': '702156',
            'role': 'director',
            'name': 'Salim DACCACHE s.j.',
            'poste': "Directeur des Éditions de l'Université Saint-Joseph de Beyrouth",
            'faculty': 'EDUSJ',
            'institution': 'EDUSJ',
            'department': '',
            'email': 'salim.daccache@usj.edu.lb'},
 '704054': {'ldap': '704054',
            'code': '704054',
            'role': 'psg',
            'name': 'Nada KABBOUCHE CHIDIAC',
            'poste': "Chargé d'édition",
            'faculty': 'EDUSJ',
            'institution': 'EDUSJ',
            'department': '',
            'email': 'nada.chidiac@usj.edu.lb',
            'director_name': 'Salim DACCACHE s.j.',
            'director_code': '702156',
            'director_ldap': '702156',
            'director_email': 'salim.daccache@usj.edu.lb'},
 '716501': {'ldap': '716501',
            'code': '716501',
            'role': 'psg',
            'name': 'Marie Rose HADDAD ZIADE',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'ESF',
            'institution': 'ESF',
            'department': '',
            'email': 'marierose.haddad@usj.edu.lb',
            'director_name': 'Salimé SALAMEH SAAD',
            'director_code': '714945',
            'director_ldap': '714945',
            'director_email': 'salime.salameh3@usj.edu.lb'},
 '714945': {'ldap': '714945',
            'code': '714945',
            'role': 'director',
            'name': 'Salimé SALAMEH SAAD',
            'poste': "Directrice p.i. de l' École de sages-femmes",
            'faculty': 'ESF',
            'institution': 'ESF',
            'department': '',
            'email': 'salime.salameh3@usj.edu.lb'},
 '708543': {'ldap': '708543',
            'code': '708543',
            'role': 'psg',
            'name': 'Michèle SALHA AFTIMOS',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'ISP',
            'institution': 'ISP',
            'department': '',
            'email': 'michele.salhaaftimos@usj.edu.lb',
            'director_name': 'Sami NADER',
            'director_code': '705626',
            'director_ldap': '705626',
            'director_email': 'sami.nader@usj.edu.lb'},
 '705626': {'ldap': '705626',
            'code': '705626',
            'role': 'director',
            'name': 'Sami NADER',
            'poste': "Directeur de l' Institut des sciences politiques",
            'faculty': 'ISP',
            'institution': 'ISP',
            'department': '',
            'email': 'sami.nader@usj.edu.lb'},
 '718277': {'ldap': '718277',
            'code': '718277',
            'role': 'psg',
            'name': 'Diana HADDAD KHAWAND (EL)',
            'poste': 'Chargé de support administratif',
            'faculty': 'MEDSIM',
            'institution': 'MEDSIM',
            'department': '',
            'email': 'diana.haddad3@usj.edu.lb',
            'director_name': 'Samia MADI JEBARA',
            'director_code': '704984',
            'director_ldap': '704984',
            'director_email': 'samia.jebara@usj.edu.lb'},
 '704984': {'ldap': '704984',
            'code': '704984',
            'role': 'director',
            'name': 'Samia MADI JEBARA',
            'poste': "Directeur du MEDSIM - Centre de simulation Ralph Audi - Faculté de médecine de l'USJ",
            'faculty': 'MEDSIM',
            'institution': 'MEDSIM',
            'department': '',
            'email': 'samia.jebara@usj.edu.lb'},
 '712697': {'ldap': '712697',
            'code': '712697',
            'role': 'psg',
            'name': 'Tony HAJJ MOUSSA',
            'poste': 'Technicien de simulation',
            'faculty': 'MEDSIM',
            'institution': 'MEDSIM',
            'department': '',
            'email': 'tony.hajjmoussa@usj.edu.lb',
            'director_name': 'Samia MADI JEBARA',
            'director_code': '704984',
            'director_ldap': '704984',
            'director_email': 'samia.jebara@usj.edu.lb'},
 '718442': {'ldap': '718442',
            'code': '718442',
            'role': 'psg',
            'name': 'Maroun NASSIF',
            'poste': 'Technicien de simulation',
            'faculty': 'MEDSIM',
            'institution': 'MEDSIM',
            'department': '',
            'email': 'maroun.nassif@usj.edu.lb',
            'director_name': 'Samia MADI JEBARA',
            'director_code': '704984',
            'director_ldap': '704984',
            'director_email': 'samia.jebara@usj.edu.lb'},
 '718449': {'ldap': '718449',
            'code': '718449',
            'role': 'psg',
            'name': 'Dany SEMRANY (AL)',
            'poste': 'Technicien de simulation',
            'faculty': 'MEDSIM',
            'institution': 'MEDSIM',
            'department': '',
            'email': 'dany.semrany1@usj.edu.lb',
            'director_name': 'Samia MADI JEBARA',
            'director_code': '704984',
            'director_ldap': '704984',
            'director_email': 'samia.jebara@usj.edu.lb'},
 '702954': {'ldap': '702954',
            'code': '702954',
            'role': 'psg',
            'name': 'Joe EID',
            'poste': 'Agent administratif',
            'faculty': 'RUSJ',
            'institution': 'RUSJ',
            'department': '',
            'email': 'joe.eid@usj.edu.lb',
            'director_name': 'Samir BECHARA s.j.',
            'director_code': '700634',
            'director_ldap': '700634',
            'director_email': 'samir.bechara@usj.edu.lb'},
 '711529': {'ldap': '711529',
            'code': '711529',
            'role': 'psg',
            'name': 'Youssef GHALEB',
            'poste': "Agent d'accueil et de sécurité",
            'faculty': 'RUSJ',
            'institution': 'RUSJ',
            'department': '',
            'email': 'youssef.ghaleb@usj.edu.lb',
            'director_name': 'Samir BECHARA s.j.',
            'director_code': '700634',
            'director_ldap': '700634',
            'director_email': 'samir.bechara@usj.edu.lb'},
 '706666': {'ldap': '706666',
            'code': '706666',
            'role': 'psg',
            'name': 'Georges SAMAHA',
            'poste': "Agent d'accueil et de sécurité",
            'faculty': 'RUSJ',
            'institution': 'RUSJ',
            'department': '',
            'email': 'georges.samaha@usj.edu.lb',
            'director_name': 'Samir BECHARA s.j.',
            'director_code': '700634',
            'director_ldap': '700634',
            'director_email': 'samir.bechara@usj.edu.lb'},
 '713622': {'ldap': '713622',
            'code': '713622',
            'role': 'psg',
            'name': 'Ibrahim YOUSSEF',
            'poste': "Agent d'accueil et de sécurité",
            'faculty': 'RUSJ',
            'institution': 'RUSJ',
            'department': '',
            'email': 'ibrahim.youssef@usj.edu.lb',
            'director_name': 'Samir BECHARA s.j.',
            'director_code': '700634',
            'director_ldap': '700634',
            'director_email': 'samir.bechara@usj.edu.lb'},
 '712947': {'ldap': '712947',
            'code': '712947',
            'role': 'psg',
            'name': 'Chantal ABOU KARAM HOKAYEM (EL)',
            'poste': 'Assistant social',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'chantal.aboukaram1@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '700610': {'ldap': '700610',
            'code': '700610',
            'role': 'director',
            'name': 'Shiraz AKL ZOGHBY',
            'poste': 'Directeur du service social',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'shiraz.akl@usj.edu.lb'},
 '715124': {'ldap': '715124',
            'code': '715124',
            'role': 'psg',
            'name': 'Elise AYOUB',
            'poste': 'Assistant social',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'elise.ayoub2@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '709581': {'ldap': '709581',
            'code': '709581',
            'role': 'psg',
            'name': 'Rouba BADRAN SROUJI (EL)',
            'poste': 'Assistant social',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'rouba.badran2@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '713954': {'ldap': '713954',
            'code': '713954',
            'role': 'psg',
            'name': 'Pascale BOU SAMRA AOUN',
            'poste': 'Assistant social',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'pascale.bousamra@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '719125': {'ldap': '719125',
            'code': '719125',
            'role': 'psg',
            'name': 'Sandy BOUTROS',
            'poste': 'Assistant social',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'sandy.boutros2@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '716919': {'ldap': '716919',
            'code': '716919',
            'role': 'psg',
            'name': 'Najat CHAHINE',
            'poste': 'Chargé de support administratif',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'najat.chahine1@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '709336': {'ldap': '709336',
            'code': '709336',
            'role': 'psg',
            'name': 'Zeina CHAHWAN FAHED',
            'poste': 'Gestionnaire des aides et des fonds',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'zeina.chahwane@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '701830': {'ldap': '701830',
            'code': '701830',
            'role': 'psg',
            'name': 'Samar CHAMOUN GHOSSOUB',
            'poste': 'Assistant social',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'samar.chamoun@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '702151': {'ldap': '702151',
            'code': '702151',
            'role': 'psg',
            'name': 'Mirna DACCACHE KHOURY (EL)',
            'poste': 'Assistant social',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'mirna.daccache@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '702256': {'ldap': '702256',
            'code': '702256',
            'role': 'psg',
            'name': 'Lamia DAOU CHELALA',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'lamia.daou@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '716585': {'ldap': '716585',
            'code': '716585',
            'role': 'psg',
            'name': 'Nawal EID',
            'poste': "Chargé d'accueil social",
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'nawal.eid@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '711908': {'ldap': '711908',
            'code': '711908',
            'role': 'psg',
            'name': 'Lynn FARAH BOU SAMRA',
            'poste': 'Gestionnaire des fonds sociaux',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'lynn.farahbousamra@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '711903': {'ldap': '711903',
            'code': '711903',
            'role': 'psg',
            'name': 'Carmen FAYAD HAYECK (EL)',
            'poste': 'Assistant social',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'carmen.fayad1@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '709075': {'ldap': '709075',
            'code': '709075',
            'role': 'psg',
            'name': 'Myriam GHOSN',
            'poste': 'Assistant social senior',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'myriam.ghosn@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '710401': {'ldap': '710401',
            'code': '710401',
            'role': 'psg',
            'name': 'Nadine HADDAD (EL) ZBEIDY',
            'poste': 'Assistant social',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'nadine.haddad5@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '704496': {'ldap': '704496',
            'code': '704496',
            'role': 'psg',
            'name': 'Leila KHATTAR ABI NADER AKL',
            'poste': 'Assistant social senior',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'leyla.abinader@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '705598': {'ldap': '705598',
            'code': '705598',
            'role': 'psg',
            'name': 'Rita NABHANE HATEM',
            'poste': 'Assistant social senior',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'rita.hatem@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '711623': {'ldap': '711623',
            'code': '711623',
            'role': 'psg',
            'name': 'Maria SAADÉ BADR',
            'poste': 'Assistant social',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'maria.saadebadr@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '706817': {'ldap': '706817',
            'code': '706817',
            'role': 'psg',
            'name': 'Patricia SEMAAN',
            'poste': 'Assistant social senior',
            'faculty': 'SS',
            'institution': 'SS',
            'department': '',
            'email': 'patricia.semaan@usj.edu.lb',
            'director_name': 'Shiraz AKL ZOGHBY',
            'director_code': '700610',
            'director_ldap': '700610',
            'director_email': 'shiraz.akl@usj.edu.lb'},
 '710970': {'ldap': '710970',
            'code': '710970',
            'role': 'psg',
            'name': 'Pamela ACHKAR (EL) SAHYOUN',
            'poste': 'coordinateur administratif des affaires académiques',
            'faculty': 'ILO',
            'institution': 'ILO',
            'department': '',
            'email': 'pamela.achkar@usj.edu.lb',
            'director_name': 'Tony KAHWAJI (EL)',
            'director_code': '711736',
            'director_ldap': '711736',
            'director_email': 'tony.kahwaji@usj.edu.lb'},
 '711736': {'ldap': '711736',
            'code': '711736',
            'role': 'director',
            'name': 'Tony KAHWAJI (EL)',
            'poste': "Directeur de l' Institut de lettres orientales",
            'faculty': 'ILO',
            'institution': 'ILO',
            'department': '',
            'email': 'tony.kahwaji@usj.edu.lb'},
 '703787': {'ldap': '703787',
            'code': '703787',
            'role': 'psg',
            'name': 'Rima HOUT (EL)',
            'poste': 'Agent administratif',
            'faculty': 'ILO',
            'institution': 'ILO',
            'department': '',
            'email': 'rima.hout@usj.edu.lb',
            'director_name': 'Tony KAHWAJI (EL)',
            'director_code': '711736',
            'director_ldap': '711736',
            'director_email': 'tony.kahwaji@usj.edu.lb'},
 '716935': {'ldap': '716935',
            'code': '716935',
            'role': 'psg',
            'name': 'Tamara KARAM',
            'poste': 'Chargé de support administratif',
            'faculty': 'ILO',
            'institution': 'ILO',
            'department': '',
            'email': 'tamara.karam@usj.edu.lb',
            'director_name': 'Tony KAHWAJI (EL)',
            'director_code': '711736',
            'director_ldap': '711736',
            'director_email': 'tony.kahwaji@usj.edu.lb'},
 '718193': {'ldap': '718193',
            'code': '718193',
            'role': 'psg',
            'name': 'Nadine YAMMINE',
            'poste': 'Chargé de support administratif',
            'faculty': 'ILO',
            'institution': 'ILO',
            'department': '',
            'email': 'nadine.yammine1@usj.edu.lb',
            'director_name': 'Tony KAHWAJI (EL)',
            'director_code': '711736',
            'director_ldap': '711736',
            'director_email': 'tony.kahwaji@usj.edu.lb'},
 '700621': {'ldap': '700621',
            'code': '700621',
            'role': 'psg',
            'name': 'Asmahan AKOURY (EL)',
            'poste': 'Appariteur',
            'faculty': 'IESAV',
            'institution': 'IESAV',
            'department': '',
            'email': 'asmahan.akoury@usj.edu.lb',
            'director_name': 'Toufic KHOURY (EL)',
            'director_code': '704672',
            'director_ldap': '704672',
            'director_email': 'toufic.khoury@usj.edu.lb'},
 '704672': {'ldap': '704672',
            'code': '704672',
            'role': 'director',
            'name': 'Toufic KHOURY (EL)',
            'poste': "Directeur de l' Institut d'études scéniques, audiovisuelles et cinématographiques",
            'faculty': 'IESAV',
            'institution': 'IESAV',
            'department': '',
            'email': 'toufic.khoury@usj.edu.lb'},
 '715355': {'ldap': '715355',
            'code': '715355',
            'role': 'psg',
            'name': 'Rita BACHA (EL)',
            'poste': 'chargé de communication',
            'faculty': 'IESAV',
            'institution': 'IESAV',
            'department': '',
            'email': 'rita.bacha3@usj.edu.lb',
            'director_name': 'Toufic KHOURY (EL)',
            'director_code': '704672',
            'director_ldap': '704672',
            'director_email': 'toufic.khoury@usj.edu.lb'},
 '703262': {'ldap': '703262',
            'code': '703262',
            'role': 'psg',
            'name': 'Nadine HADDAD',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'IESAV',
            'institution': 'IESAV',
            'department': '',
            'email': 'nadine.haddad@usj.edu.lb',
            'director_name': 'Toufic KHOURY (EL)',
            'director_code': '704672',
            'director_ldap': '704672',
            'director_email': 'toufic.khoury@usj.edu.lb'},
 '704501': {'ldap': '704501',
            'code': '704501',
            'role': 'psg',
            'name': 'Amale KHAWAND (EL)',
            'poste': 'Chargé de support académique',
            'faculty': 'IESAV',
            'institution': 'IESAV',
            'department': '',
            'email': 'amal.khawand@usj.edu.lb',
            'director_name': 'Toufic KHOURY (EL)',
            'director_code': '704672',
            'director_ldap': '704672',
            'director_email': 'toufic.khoury@usj.edu.lb'},
 '719107': {'ldap': '719107',
            'code': '719107',
            'role': 'psg',
            'name': 'Toni NAASSAN',
            'poste': 'Technicien spécialisé',
            'faculty': 'IESAV',
            'institution': 'IESAV',
            'department': '',
            'email': 'toni.naassan@usj.edu.lb',
            'director_name': 'Toufic KHOURY (EL)',
            'director_code': '704672',
            'director_ldap': '704672',
            'director_email': 'toufic.khoury@usj.edu.lb'},
 '713470': {'ldap': '713470',
            'code': '713470',
            'role': 'psg',
            'name': 'Joseph SLEIMAN',
            'poste': 'Vidéographe',
            'faculty': 'IESAV',
            'institution': 'IESAV',
            'department': '',
            'email': 'joseph.sleiman@usj.edu.lb',
            'director_name': 'Toufic KHOURY (EL)',
            'director_code': '704672',
            'director_ldap': '704672',
            'director_email': 'toufic.khoury@usj.edu.lb'},
 '716584': {'ldap': '716584',
            'code': '716584',
            'role': 'psg',
            'name': 'Nadine AOUAD MEOUCHI',
            'poste': 'Chargé de support administratif',
            'faculty': 'VRAA',
            'institution': 'VRAA',
            'department': '',
            'email': 'nadine.aouad2@usj.edu.lb',
            'director_name': 'Toufic RIZK',
            'director_code': '706269',
            'director_ldap': '706269',
            'director_email': 'toufic.rizk@usj.edu.lb'},
 '706269': {'ldap': '706269',
            'code': '706269',
            'role': 'director',
            'name': 'Toufic RIZK',
            'poste': 'Vice-Recteur aux Vice-rectorat aux affaires académiques',
            'faculty': 'VRAA',
            'institution': 'VRAA',
            'department': '',
            'email': 'toufic.rizk@usj.edu.lb'},
 '719130': {'ldap': '719130',
            'code': '719130',
            'role': 'psg',
            'name': 'Jihane NACOUZI',
            'poste': 'Coordinateur administratif',
            'faculty': 'VRAA',
            'institution': 'VRAA',
            'department': '',
            'email': 'jihane.nacouzi1@usj.edu.lb',
            'director_name': 'Toufic RIZK',
            'director_code': '706269',
            'director_ldap': '706269',
            'director_email': 'toufic.rizk@usj.edu.lb'},
 '717149': {'ldap': '717149',
            'code': '717149',
            'role': 'psg',
            'name': 'Joe CHAHWAN',
            'poste': 'Coordinateur et Mentor en entreprenariat',
            'faculty': 'SIP',
            'institution': 'SIP',
            'department': '',
            'email': 'joe.chahwan@usj.edu.lb',
            'director_name': 'Ursula HAGE (EL)',
            'director_code': '712546',
            'director_ldap': '712546',
            'director_email': 'ursula.hage@usj.edu.lb'},
 '712546': {'ldap': '712546',
            'code': '712546',
            'role': 'director',
            'name': 'Ursula HAGE (EL)',
            'poste': "Directeur du service de l'insertion professionnelle",
            'faculty': 'SIP',
            'institution': 'SIP',
            'department': '',
            'email': 'ursula.hage@usj.edu.lb'},
 '714466': {'ldap': '714466',
            'code': '714466',
            'role': 'psg',
            'name': 'Roy DAHER (EL)',
            'poste': 'Chef de projets',
            'faculty': 'SIP',
            'institution': 'SIP',
            'department': '',
            'email': 'roy.daher3@usj.edu.lb',
            'director_name': 'Ursula HAGE (EL)',
            'director_code': '712546',
            'director_ldap': '712546',
            'director_email': 'ursula.hage@usj.edu.lb'},
 '708392': {'ldap': '708392',
            'code': '708392',
            'role': 'psg',
            'name': 'Nada HAJJ (EL) GHANDOUR',
            'poste': 'Coordinateur administratif',
            'faculty': 'SIP',
            'institution': 'SIP',
            'department': '',
            'email': 'nada.ghandour@usj.edu.lb',
            'director_name': 'Ursula HAGE (EL)',
            'director_code': '712546',
            'director_ldap': '712546',
            'director_email': 'ursula.hage@usj.edu.lb'},
 '705495': {'ldap': '705495',
            'code': '705495',
            'role': 'psg',
            'name': 'Carole MOUKAWAM DIB',
            'poste': 'Chargé du recrutement étudiants',
            'faculty': 'SIP',
            'institution': 'SIP',
            'department': '',
            'email': 'carole.dib@usj.edu.lb',
            'director_name': 'Ursula HAGE (EL)',
            'director_code': '712546',
            'director_ldap': '712546',
            'director_email': 'ursula.hage@usj.edu.lb'},
 '715418': {'ldap': '715418',
            'code': '715418',
            'role': 'psg',
            'name': 'Nour SARDOUK',
            'poste': 'Chargé de communication',
            'faculty': 'SIP',
            'institution': 'SIP',
            'department': '',
            'email': 'nour.sardouk1@usj.edu.lb',
            'director_name': 'Ursula HAGE (EL)',
            'director_code': '712546',
            'director_ldap': '712546',
            'director_email': 'ursula.hage@usj.edu.lb'},
 '719104': {'ldap': '719104',
            'code': '719104',
            'role': 'psg',
            'name': 'Anthony BASSIL',
            'poste': 'Ingénieur en intelligence artificielle',
            'faculty': 'CINIA',
            'institution': 'CINIA',
            'department': '',
            'email': 'anthony.bassil5@usj.edu.lb',
            'director_name': 'Wadad WAZEN GERGY',
            'director_code': '703972',
            'director_ldap': '703972',
            'director_email': 'wadad.wazen@usj.edu.lb'},
 '703972': {'ldap': '703972',
            'code': '703972',
            'role': 'director',
            'name': 'Wadad WAZEN GERGY',
            'poste': "Directeur du Centre de l'innovation numérique et de l'intelligence artificielle",
            'faculty': 'CINIA',
            'institution': 'CINIA',
            'department': '',
            'email': 'wadad.wazen@usj.edu.lb'},
 '717180': {'ldap': '717180',
            'code': '717180',
            'role': 'psg',
            'name': 'Elie BECHARA',
            'poste': 'Administrateur - plateformes éducatives',
            'faculty': 'CINIA',
            'institution': 'CINIA',
            'department': '',
            'email': 'elie.bechara2@usj.edu.lb',
            'director_name': 'Wadad WAZEN GERGY',
            'director_code': '703972',
            'director_ldap': '703972',
            'director_email': 'wadad.wazen@usj.edu.lb'},
 '712299': {'ldap': '712299',
            'code': '712299',
            'role': 'psg',
            'name': 'Mario GHARIB',
            'poste': 'Administrateur - plateformes éducatives - Team leader',
            'faculty': 'CINIA',
            'institution': 'CINIA',
            'department': '',
            'email': 'mario.gharib@usj.edu.lb',
            'director_name': 'Wadad WAZEN GERGY',
            'director_code': '703972',
            'director_ldap': '703972',
            'director_email': 'wadad.wazen@usj.edu.lb'},
 '718027': {'ldap': '718027',
            'code': '718027',
            'role': 'psg',
            'name': 'Elise OUEISS MELKI (EL)',
            'poste': 'Graphiste',
            'faculty': 'CINIA',
            'institution': 'CINIA',
            'department': '',
            'email': 'elise.oueissmelki@usj.edu.lb',
            'director_name': 'Wadad WAZEN GERGY',
            'director_code': '703972',
            'director_ldap': '703972',
            'director_email': 'wadad.wazen@usj.edu.lb'},
 '708968': {'ldap': '708968',
            'code': '708968',
            'role': 'psg',
            'name': 'Héléna SAADE',
            'poste': 'Chef de projets',
            'faculty': 'CINIA',
            'institution': 'CINIA',
            'department': '',
            'email': 'helena.saade@usj.edu.lb',
            'director_name': 'Wadad WAZEN GERGY',
            'director_code': '703972',
            'director_ldap': '703972',
            'director_email': 'wadad.wazen@usj.edu.lb'},
 '703470': {'ldap': '703470',
            'code': '703470',
            'role': 'psg',
            'name': 'Nadia CHEHAB',
            'poste': "Agent de propreté et d'hygiène",
            'faculty': 'ESIAM',
            'institution': 'ESIAM',
            'department': '',
            'email': 'nadia.chehab@usj.edu.lb',
            'director_name': 'Wadih SKAFF (EL)',
            'director_code': '706898',
            'director_ldap': '706898',
            'director_email': 'wadih.skaff@usj.edu.lb'},
 '706898': {'ldap': '706898',
            'code': '706898',
            'role': 'director',
            'name': 'Wadih SKAFF (EL)',
            'poste': "Directeur de l' École supérieure d'ingénieurs d'agronomie méditerranéenne",
            'faculty': 'ESIAM',
            'institution': 'ESIAM',
            'department': '',
            'email': 'wadih.skaff@usj.edu.lb'},
 '710392': {'ldap': '710392',
            'code': '710392',
            'role': 'psg',
            'name': 'Tanios HAJJ (EL)',
            'poste': 'Agent de sécurité',
            'faculty': 'ESIAM',
            'institution': 'ESIAM',
            'department': '',
            'email': 'tanios.hajj@usj.edu.lb',
            'director_name': 'Wadih SKAFF (EL)',
            'director_code': '706898',
            'director_ldap': '706898',
            'director_email': 'wadih.skaff@usj.edu.lb'},
 '719138': {'ldap': '719138',
            'code': '719138',
            'role': 'psg',
            'name': 'Céline MACHAALANY ABI BOUTROS',
            'poste': 'Chargé de support académique',
            'faculty': 'ESIAM',
            'institution': 'ESIAM',
            'department': '',
            'email': 'celine.machaalany1@usj.edu.lb',
            'director_name': 'Wadih SKAFF (EL)',
            'director_code': '706898',
            'director_ldap': '706898',
            'director_email': 'wadih.skaff@usj.edu.lb'},
 '714928': {'ldap': '714928',
            'code': '714928',
            'role': 'psg',
            'name': 'Joanna TABET ABOU EID',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'ESIAM',
            'institution': 'ESIAM',
            'department': '',
            'email': 'joanna.tabet2@usj.edu.lb',
            'director_name': 'Wadih SKAFF (EL)',
            'director_code': '706898',
            'director_ldap': '706898',
            'director_email': 'wadih.skaff@usj.edu.lb'},
 '701091': {'ldap': '701091',
            'code': '701091',
            'role': 'psg',
            'name': 'Norma AZZI AZZI (EL)',
            'poste': 'Coordinateur administratif',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'norma.azzi@usj.edu.lb',
            'director_name': 'Walid MEZHER',
            'director_code': '705342',
            'director_ldap': '705342',
            'director_email': 'walid.mezher@usj.edu.lb'},
 '705342': {'ldap': '705342',
            'code': '705342',
            'role': 'director',
            'name': 'Walid MEZHER',
            'poste': 'Directeur financier',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'walid.mezher@usj.edu.lb'},
 '717186': {'ldap': '717186',
            'code': '717186',
            'role': 'psg',
            'name': 'Rita BAAKLINI NAKHOUL',
            'poste': 'Assistante financière',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'rita.baaklini1@usj.edu.lb',
            'director_name': 'Walid MEZHER',
            'director_code': '705342',
            'director_ldap': '705342',
            'director_email': 'walid.mezher@usj.edu.lb'},
 '702726': {'ldap': '702726',
            'code': '702726',
            'role': 'psg',
            'name': 'Liliane FAYAD',
            'poste': 'Directeur adjoint - Scolarités',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'liliane.fayad@usj.edu.lb',
            'director_name': 'Walid MEZHER',
            'director_code': '705342',
            'director_ldap': '705342',
            'director_email': 'walid.mezher@usj.edu.lb'},
 '716951': {'ldap': '716951',
            'code': '716951',
            'role': 'psg',
            'name': 'Noha GERGES',
            'poste': 'Caissier',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'noha.gerges1@usj.edu.lb',
            'director_name': 'Walid MEZHER',
            'director_code': '705342',
            'director_ldap': '705342',
            'director_email': 'walid.mezher@usj.edu.lb'},
 '702925': {'ldap': '702925',
            'code': '702925',
            'role': 'psg',
            'name': 'Dolly GERGES EL HAGE',
            'poste': 'Chargé du recouvrement',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'dolly.hage@usj.edu.lb',
            'director_name': 'Walid MEZHER',
            'director_code': '705342',
            'director_ldap': '705342',
            'director_email': 'walid.mezher@usj.edu.lb'},
 '715597': {'ldap': '715597',
            'code': '715597',
            'role': 'psg',
            'name': 'Pamela HADDAD',
            'poste': 'Chargé de support administratif',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'pamela.haddad1@usj.edu.lb',
            'director_name': 'Walid MEZHER',
            'director_code': '705342',
            'director_ldap': '705342',
            'director_email': 'walid.mezher@usj.edu.lb'},
 '716217': {'ldap': '716217',
            'code': '716217',
            'role': 'psg',
            'name': 'Nicolas HANNOUN',
            'poste': 'Caissier',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'nicolas.hannoun@usj.edu.lb',
            'director_name': 'Walid MEZHER',
            'director_code': '705342',
            'director_ldap': '705342',
            'director_email': 'walid.mezher@usj.edu.lb'},
 '703734': {'ldap': '703734',
            'code': '703734',
            'role': 'psg',
            'name': 'Suzanne HOBEIKA CHAWI',
            'poste': 'Chargé du recouvrement',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'suzanne.chawi@usj.edu.lb',
            'director_name': 'Walid MEZHER',
            'director_code': '705342',
            'director_ldap': '705342',
            'director_email': 'walid.mezher@usj.edu.lb'},
 '704509': {'ldap': '704509',
            'code': '704509',
            'role': 'psg',
            'name': 'Sami KHAWAND (EL)',
            'poste': 'Agent de liaison',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'sami.khawand@usj.edu.lb',
            'director_name': 'Walid MEZHER',
            'director_code': '705342',
            'director_ldap': '705342',
            'director_email': 'walid.mezher@usj.edu.lb'},
 '719112': {'ldap': '719112',
            'code': '719112',
            'role': 'psg',
            'name': 'Eliana OMRAN LOUCA',
            'poste': 'Assistante financière',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'eliana.omran@usj.edu.lb',
            'director_name': 'Walid MEZHER',
            'director_code': '705342',
            'director_ldap': '705342',
            'director_email': 'walid.mezher@usj.edu.lb'},
 '706468': {'ldap': '706468',
            'code': '706468',
            'role': 'psg',
            'name': 'Maha SADER AKL',
            'poste': 'Chargé de paiements',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'maha.akl@usj.edu.lb',
            'director_name': 'Walid MEZHER',
            'director_code': '705342',
            'director_ldap': '705342',
            'director_email': 'walid.mezher@usj.edu.lb'},
 '713933': {'ldap': '713933',
            'code': '713933',
            'role': 'psg',
            'name': 'Claudina YOUNAN NJEIM',
            'poste': 'Chargé du budget',
            'faculty': 'SFI',
            'institution': 'SFI',
            'department': '',
            'email': 'claudina.younan@usj.edu.lb',
            'director_name': 'Walid MEZHER',
            'director_code': '705342',
            'director_ldap': '705342',
            'director_email': 'walid.mezher@usj.edu.lb'},
 '700736': {'ldap': '700736',
            'code': '700736',
            'role': 'psg',
            'name': 'Ghada AOUAD',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'ghada.aouad@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '706148': {'ldap': '706148',
            'code': '706148',
            'role': 'director',
            'name': 'Wassim RAPHAEL',
            'poste': "Doyen de l' École supérieure d'ingénieurs de Beyrouth",
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'wassim.raphael@usj.edu.lb'},
 '701797': {'ldap': '701797',
            'code': '701797',
            'role': 'psg',
            'name': 'Charbel AOUN',
            'poste': 'Technicien de laboratoire',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'charbel.aoun@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '718298': {'ldap': '718298',
            'code': '718298',
            'role': 'psg',
            'name': 'Rita Maria AZAR TANNOUS',
            'poste': 'Chargé de support administratif',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'ritamaria.azar1@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '701609': {'ldap': '701609',
            'code': '701609',
            'role': 'psg',
            'name': 'Carine BOUSTANY (EL) SAWAYA',
            'poste': 'Chargé de support académique',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'carine.boustany@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '708383': {'ldap': '708383',
            'code': '708383',
            'role': 'psg',
            'name': 'Rose DAGHER MRAD',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'rose.dagher@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '718441': {'ldap': '718441',
            'code': '718441',
            'role': 'psg',
            'name': 'Joyce GERGES CHEHADE',
            'poste': "Agent d'accueil",
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'joyce.gerges1@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '711155': {'ldap': '711155',
            'code': '711155',
            'role': 'psg',
            'name': 'Tatiana JABBOUR',
            'poste': 'Chargé de support administratif',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'tatiana.jabbour1@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '704381': {'ldap': '704381',
            'code': '704381',
            'role': 'psg',
            'name': 'Elie KHACHO',
            'poste': 'Assistant de laboratoire',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'elie.khacho@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '717403': {'ldap': '717403',
            'code': '717403',
            'role': 'psg',
            'name': 'Cynthia KHAIRALLAH KHAIRALLAH',
            'poste': 'Chargé de support académique',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'cynthia.khairallah2@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '719400': {'ldap': '719400',
            'code': '719400',
            'role': 'psg',
            'name': 'Maria KHATER TOHME',
            'poste': 'Chargé de support administratif',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'maria.khater2@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '704508': {'ldap': '704508',
            'code': '704508',
            'role': 'psg',
            'name': 'Jihad KHAWAND (EL)',
            'poste': 'Agent administratif',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'jihad.khawand@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '716679': {'ldap': '716679',
            'code': '716679',
            'role': 'psg',
            'name': 'Grace MAALOUF',
            'poste': 'Chargé de support administratif',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'grace.maalouf1@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '716136': {'ldap': '716136',
            'code': '716136',
            'role': 'psg',
            'name': 'Lynn SADER',
            'poste': 'Assistant aux affaires administratives',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'lynn.sader1@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '713932': {'ldap': '713932',
            'code': '713932',
            'role': 'psg',
            'name': 'Elyse SALIBA',
            'poste': 'Assistant aux affaires académiques',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'elyse.saliba@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '709440': {'ldap': '709440',
            'code': '709440',
            'role': 'psg',
            'name': 'Zeina SAWAYA BOUERI',
            'poste': 'Chargé de support académique',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'zeina.sawaya2@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '719109': {'ldap': '719109',
            'code': '719109',
            'role': 'psg',
            'name': 'Marianne YOUSSEF HAJJ (EL)',
            'poste': 'Chargé de support académique',
            'faculty': 'ESIB',
            'institution': 'ESIB',
            'department': '',
            'email': 'marianne.youssef1@usj.edu.lb',
            'director_name': 'Wassim RAPHAEL',
            'director_code': '706148',
            'director_ldap': '706148',
            'director_email': 'wassim.raphael@usj.edu.lb'},
 '710739': {'ldap': '710739',
            'code': '710739',
            'role': 'psg',
            'name': 'Joseph ABD EL SATER',
            'poste': 'Agent administratif',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'joseph.abdelsater@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '709855': {'ldap': '709855',
            'code': '709855',
            'role': 'director',
            'name': 'Wassim SELWAN',
            'poste': "Administrateur du Campus de l'innovation et du sport",
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'wassim.selwan@usj.edu.lb'},
 '710740': {'ldap': '710740',
            'code': '710740',
            'role': 'psg',
            'name': 'François BARADHY',
            'poste': 'Technicien',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'francois.baradhy@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '701296': {'ldap': '701296',
            'code': '701296',
            'role': 'psg',
            'name': 'Alexandre BAZ',
            'poste': 'Intendant de campus',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'alexandre.baz@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '710370': {'ldap': '710370',
            'code': '710370',
            'role': 'psg',
            'name': 'Mounir BEAINI (EL)',
            'poste': "Agent de maintenance et d'entretien",
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'mounir.beaini@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '718959': {'ldap': '718959',
            'code': '718959',
            'role': 'psg',
            'name': 'Joe BEJJANI',
            'poste': 'Technicien spécialisé',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'joe.bejjani@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '713328': {'ldap': '713328',
            'code': '713328',
            'role': 'psg',
            'name': 'Chady CHAHINE',
            'poste': 'Agent de sécurité',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'chady.chahine@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '711010': {'ldap': '711010',
            'code': '711010',
            'role': 'psg',
            'name': 'Joseph FAYAD (AL)',
            'poste': 'Appariteur',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'joseph.fayad@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '718398': {'ldap': '718398',
            'code': '718398',
            'role': 'psg',
            'name': 'Gisele GHORRA SOUAIDAN',
            'poste': 'Chargé de support administratif',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'gisele.ghorra1@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '711546': {'ldap': '711546',
            'code': '711546',
            'role': 'psg',
            'name': 'Imad JABER',
            'poste': 'Appariteur',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'imad.jaber@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '717522': {'ldap': '717522',
            'code': '717522',
            'role': 'psg',
            'name': 'Rebecca KAROUT',
            'poste': 'Bibliothécaire',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'rebecca.karout@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '710559': {'ldap': '710559',
            'code': '710559',
            'role': 'psg',
            'name': 'Rachid MERHI',
            'poste': 'Agent de stock',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'rachid.merhi@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '713431': {'ldap': '713431',
            'code': '713431',
            'role': 'psg',
            'name': 'Toni NADER',
            'poste': 'Agent de sécurité',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'toni.nader@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '710367': {'ldap': '710367',
            'code': '710367',
            'role': 'psg',
            'name': 'Georges NASRALLAH',
            'poste': 'Surveillant de site',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'georges.nasrallah@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '706253': {'ldap': '706253',
            'code': '706253',
            'role': 'psg',
            'name': 'Jeanette RIZK',
            'poste': 'Bibliothécaire en chef',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'janet.rizk@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '710766': {'ldap': '710766',
            'code': '710766',
            'role': 'psg',
            'name': 'Charbel ZIYAB',
            'poste': 'Agent de sécurité',
            'faculty': 'CIS',
            'institution': 'CIS',
            'department': '',
            'email': 'charbel.ziyab@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '700425': {'ldap': '700425',
            'code': '700425',
            'role': 'psg',
            'name': 'André ABOU RJEILY',
            'poste': 'Intendant du Rectorat',
            'faculty': 'SMCPI',
            'institution': 'SMCPI',
            'department': '',
            'email': 'andre.abourjeily@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '719285': {'ldap': '719285',
            'code': '719285',
            'role': 'psg',
            'name': 'Khalil BOU KHALIL',
            'poste': 'Gestionnaire de projets et des opérations immobilières',
            'faculty': 'SMCPI',
            'institution': 'SMCPI',
            'department': '',
            'email': 'khalil.boukhalil@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '717859': {'ldap': '717859',
            'code': '717859',
            'role': 'psg',
            'name': 'Clara NAKAD FAYSAL',
            'poste': 'Chargé de support administratif',
            'faculty': 'SMCPI',
            'institution': 'SMCPI',
            'department': '',
            'email': 'clara.nakad@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '715848': {'ldap': '715848',
            'code': '715848',
            'role': 'psg',
            'name': 'Hasan RABIUL',
            'poste': "Agent de maintenance et d'entretien",
            'faculty': 'SMCPI',
            'institution': 'SMCPI',
            'department': '',
            'email': 'hasan.rabiul@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '714237': {'ldap': '714237',
            'code': '714237',
            'role': 'psg',
            'name': 'Pierre SEMAAN',
            'poste': 'Technicien',
            'faculty': 'SMCPI',
            'institution': 'SMCPI',
            'department': '',
            'email': 'pierre.semaan@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '716429': {'ldap': '716429',
            'code': '716429',
            'role': 'psg',
            'name': 'Mtanos TOHME',
            'poste': 'Technicien spécialisé',
            'faculty': 'SMCPI',
            'institution': 'SMCPI',
            'department': '',
            'email': 'mtanos.tohme@usj.edu.lb',
            'director_name': 'Wassim SELWAN',
            'director_code': '709855',
            'director_ldap': '709855',
            'director_email': 'wassim.selwan@usj.edu.lb'},
 '713027': {'ldap': '713027',
            'code': '713027',
            'role': 'psg',
            'name': 'Mireille BOU NADER',
            'poste': 'Coordinateur administratif des affaires académiques',
            'faculty': 'ISSR',
            'institution': 'ISSR',
            'department': '',
            'email': 'mireille.bounader@usj.edu.lb',
            'director_name': 'Yara MATTA',
            'director_code': '705195',
            'director_ldap': '705195',
            'director_email': 'yara.matta@usj.edu.lb'},
 '705195': {'ldap': '705195',
            'code': '705195',
            'role': 'director',
            'name': 'Yara MATTA',
            'poste': "Directrice de l' Institut supérieur de sciences religieuses",
            'faculty': 'ISSR',
            'institution': 'ISSR',
            'department': '',
            'email': 'yara.matta@usj.edu.lb'},
 '715094': {'ldap': '715094',
            'code': '715094',
            'role': 'psg',
            'name': 'Claude MATTA EID',
            'poste': 'Chargé de communication',
            'faculty': 'ISSR',
            'institution': 'ISSR',
            'department': '',
            'email': 'claude.matta2@usj.edu.lb',
            'director_name': 'Yara MATTA',
            'director_code': '705195',
            'director_ldap': '705195',
            'director_email': 'yara.matta@usj.edu.lb'},
 '716974': {'ldap': '716974',
            'code': '716974',
            'role': 'psg',
            'name': 'Micheline SKAFF MEDAWAR',
            'poste': 'Chargé de support administratif',
            'faculty': 'ISSR',
            'institution': 'ISSR',
            'department': '',
            'email': 'micheline.skaff@usj.edu.lb',
            'director_name': 'Yara MATTA',
            'director_code': '705195',
            'director_ldap': '705195',
            'director_email': 'yara.matta@usj.edu.lb'},
 '715161': {'ldap': '715161',
            'code': '715161',
            'role': 'psg',
            'name': 'Pierre KAMEL',
            'poste': 'Assistant chef de chœur',
            'faculty': 'CHOEUR',
            'institution': 'CHOEUR',
            'department': '',
            'email': 'pierre.kamel1@usj.edu.lb',
            'director_name': 'Yasmina SABBAH RAHY (EL)',
            'director_code': '712734',
            'director_ldap': '712734',
            'director_email': 'yasmina.sabbah@usj.edu.lb'},
 '712734': {'ldap': '712734',
            'code': '712734',
            'role': 'director',
            'name': 'Yasmina SABBAH RAHY (EL)',
            'poste': 'Directeur de musique',
            'faculty': 'CHOEUR',
            'institution': 'CHOEUR',
            'department': '',
            'email': 'yasmina.sabbah@usj.edu.lb'},
 '715798': {'ldap': '715798',
            'code': '715798',
            'role': 'psg',
            'name': 'Elsa ABI HABIB',
            'poste': 'Auditeur interne',
            'faculty': 'AIC',
            'institution': 'AIC',
            'department': '',
            'email': 'elsa.abihabib1@usj.edu.lb',
            'director_name': 'Ziad HOYEK',
            'director_code': '703795',
            'director_ldap': '703795',
            'director_email': 'ziad.hoyek@usj.edu.lb'},
 '703795': {'ldap': '703795',
            'code': '703795',
            'role': 'director',
            'name': 'Ziad HOYEK',
            'poste': "Directeur du service d'audit interne et contrôle du patrimoine",
            'faculty': 'AIC',
            'institution': 'AIC',
            'department': '',
            'email': 'ziad.hoyek@usj.edu.lb'},
 '718192': {'ldap': '718192',
            'code': '718192',
            'role': 'psg',
            'name': 'Nathalie ABOU NADER',
            'poste': 'Contrôleur interne',
            'faculty': 'AIC',
            'institution': 'AIC',
            'department': '',
            'email': 'nathalie.abounader1@usj.edu.lb',
            'director_name': 'Ziad HOYEK',
            'director_code': '703795',
            'director_ldap': '703795',
            'director_email': 'ziad.hoyek@usj.edu.lb'},
 '717527': {'ldap': '717527',
            'code': '717527',
            'role': 'psg',
            'name': 'Joya Maria AZZI (EL)',
            'poste': 'Auditeur interne',
            'faculty': 'AIC',
            'institution': 'AIC',
            'department': '',
            'email': 'joya-maria.azzi1@usj.edu.lb',
            'director_name': 'Ziad HOYEK',
            'director_code': '703795',
            'director_ldap': '703795',
            'director_email': 'ziad.hoyek@usj.edu.lb'},
 '718903': {'ldap': '718903',
            'code': '718903',
            'role': 'psg',
            'name': 'Anna Maria MERHEJ',
            'poste': 'Contrôleur interne',
            'faculty': 'AIC',
            'institution': 'AIC',
            'department': '',
            'email': 'annamaria.merhej1@usj.edu.lb',
            'director_name': 'Ziad HOYEK',
            'director_code': '703795',
            'director_ldap': '703795',
            'director_email': 'ziad.hoyek@usj.edu.lb'},
 'ADMIN2032': {'ldap': 'ADMIN2032',
               'code': 'ADMIN2032',
               'role': 'admin',
               'name': 'Administrateur TNA',
               'poste': 'Administrateur',
               'faculty': 'USJ',
               'institution': 'USJ',
               'department': '',
               'email': ''},
 'MIREILLE': {'ldap': 'MIREILLE',
              'code': 'MIREILLE',
              'role': 'admin',
              'name': 'Mireille',
              'poste': 'Administrateur',
              'faculty': 'USJ',
              'institution': 'USJ',
              'department': '',
              'email': ''}}

TRIAL_PSG_RESPONSES = {
    # DD001 - mixed cases
    "PSG001": ["Communication constructive", "Diversité culturelle", "Communication écrite"],          # 0 common with director
    "PSG002": ["Outils intelligence artificielle", "Gestion du temps", "Communication écrite"],         # 1 common
    "PSG003": ["Bureautique-Excel", "Outils intelligence artificielle", "Gestion de projets"],          # 2 common
    "PSG004": ["Résolution de conflits", "Communication orale", "Team building"],                      # 0 common
    "PSG005": ["Customer service", "Gestion du stress", "Communication constructive"],                  # 3 common

    # DD002 - mostly low/no agreement
    "PSG006": ["Santé mentale", "Gestion du stress", "Intelligence émotionnelle"],                     # 1 common
    "PSG007": ["Bureautique-Excel", "Ergonomie", "Gestion du temps"],                                  # 0 common
    "PSG008": ["Customer service", "Communication orale", "Diversité culturelle"],                      # 1 common
    "PSG009": ["Gestion de projets", "Collaboration", "Communication écrite"],                         # 0 common
    "PSG010": ["Outils intelligence artificielle", "Bureautique-PowerPoint", "Création de contenu-Réseaux sociaux"], # 2 common

    # DD003 - varied business/admin cases
    "PSG011": ["Gestion financière", "Bureautique-Excel", "Esprit critique et résolution de problèmes"], # 0 common
    "PSG012": ["Communication orale", "Public speaking and Body language", "Customer service"],          # 1 common
    "PSG013": ["Branding", "Création de contenu-Réseaux sociaux", "Customer service"],                  # 2 common
    "PSG014": ["Gestion du changement en milieu universitaire", "Gestion de projets", "Collaboration"], # 0 common
    "PSG015": ["Esprit critique et résolution de problèmes", "Bureautique-Excel", "Communication écrite"], # 1 common

    # DD004 - mostly no common themes
    "PSG016": ["Communication écrite", "Bureautique-Word", "Customer service"],                         # 0 common
    "PSG017": ["Gestion du temps", "Gestion du stress", "Collaboration"],                              # 1 common
    "PSG018": ["Inclusion", "Diversité culturelle", "Intelligence interpersonnelle"],                   # 0 common
    "PSG019": ["Outils intelligence artificielle", "Bureautique-PowerPoint", "Gestion de projets"],     # 2 common
    "PSG020": ["Branding", "Communication orale", "Création de contenu-Réseaux sociaux"],               # 0 common

    # DD005 - technical/project cases
    "PSG021": ["Ergonomie", "Gestion de projets", "Bureautique-Excel"],                                 # 1 common
    "PSG022": ["Outils intelligence artificielle", "Esprit critique et résolution de problèmes", "Communication constructive"], # 0 common
    "PSG023": ["Customer service", "Gestion du temps", "Communication écrite"],                          # 1 common
    "PSG024": ["Collaboration", "Gestion du changement en milieu universitaire", "Team building"],       # 2 common
    "PSG025": ["Outils intelligence artificielle", "Gestion de projets", "Esprit critique et résolution de problèmes"] # 0 common
}


TRIAL_DIRECTOR_RESPONSES = {
    "DD001": {
        "leader": ["Data-driven decision making", "Outils intelligence artificielle-IA", "Strategic decision making"],
        "employees": {
            "PSG001": ["Gestion financière", "Ergonomie", "Bureautique-PowerPoint"],                    # 0 common
            "PSG002": ["Collaboration", "Outils intelligence artificielle", "Customer service"],        # 1 common, not same priority
            "PSG003": ["Gestion de projets", "Bureautique-Excel", "Team building"],                     # 2 common
            "PSG004": ["Bureautique-Excel", "Bien-être au travail", "Gestion financière"],              # 0 common
            "PSG005": ["Customer service", "Gestion du stress", "Communication constructive"]           # 3 common
        }
    },
    "DD002": {
        "leader": ["Crisis management and institutional resilience", "Gestion budgétaire", "Change management in academic institutions"],
        "employees": {
            "PSG006": ["Bien-être au travail", "Santé mentale", "Mindfulness"],                         # 1 common
            "PSG007": ["Communication constructive", "Collaboration", "Bureautique-PowerPoint"],        # 0 common
            "PSG008": ["Gestion du temps", "Diversité culturelle", "Ergonomie"],                        # 1 common
            "PSG009": ["Customer service", "Gestion du stress", "Bureautique-Excel"],                   # 0 common
            "PSG010": ["Branding", "Bureautique-PowerPoint", "Outils intelligence artificielle"]        # 2 common
        }
    },
    "DD003": {
        "leader": ["Strategic decision making", "Digital marketing", "Gestion financière"],
        "employees": {
            "PSG011": ["Communication orale", "Gestion du temps", "Customer service"],                  # 0 common
            "PSG012": ["Gestion financière", "Customer service", "Bureautique-Excel"],                  # 1 common
            "PSG013": ["Branding", "Customer service", "Gestion de projets"],                           # 2 common
            "PSG014": ["Santé mentale", "Bureautique-Word", "Ergonomie"],                               # 0 common
            "PSG015": ["Communication écrite", "Team building", "Gestion du stress"]                    # 1 common
        }
    },
    "DD004": {
        "leader": ["Agile management", "Change management in academic institutions", "Data-driven decision making"],
        "employees": {
            "PSG016": ["Collaboration", "Gestion de projets", "Ergonomie"],                             # 0 common
            "PSG017": ["Branding", "Collaboration", "Bureautique-PowerPoint"],                          # 1 common
            "PSG018": ["Bureautique-Excel", "Customer service", "Gestion financière"],                   # 0 common
            "PSG019": ["Gestion de projets", "Outils intelligence artificielle", "Communication orale"], # 2 common
            "PSG020": ["Gestion du stress", "Bureautique-Word", "Customer service"]                     # 0 common
        }
    },
    "DD005": {
        "leader": ["Outils intelligence artificielle-IA", "Data-driven decision making", "Gestion budgétaire"],
        "employees": {
            "PSG021": ["Gestion du temps", "Ergonomie", "Customer service"],                            # 1 common
            "PSG022": ["Bureautique-Word", "Team building", "Gestion financière"],                      # 0 common
            "PSG023": ["Communication orale", "Customer service", "Gestion financière"],                # 1 common
            "PSG024": ["Team building", "Bureautique-Excel", "Collaboration"],                          # 2 common
            "PSG025": ["Customer service", "Communication orale", "Ergonomie"]                         # 0 common
        }
    }
}


def image_to_base64(image_path):
    if not os.path.exists(image_path):
        return ""

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def apply_style():
    st.markdown(f"""
    <style>

    section[data-testid="stSidebar"],
    div[data-testid="stSidebar"],
    [data-testid="stSidebar"] {{
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }}

    [data-testid="collapsedControl"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    

    header,
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stMainMenu"],
    [data-testid="stDeployButton"],
    .stDeployButton,
    #MainMenu {{
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }}
    
    .stApp {{
        background: linear-gradient(180deg, #F7FAFE 0%, #EEF3F9 100%);
        color: {USJ_TEXT};
    }}

    .block-container {{
        padding-top: 1.1rem;
        max-width: 1320px;
    }}

    h1, h2, h3 {{
        color: {USJ_BLUE};
        font-weight: 400;
    }}

    .platform-header {{
        background: #ffffff;
        border: 1px solid #DDE5F0;
        border-radius: 22px;
        padding: 16px 24px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 10px 30px rgba(27,42,65,0.07);
    }}

    .logo-side {{
        width: 180px;
        display: flex;
        align-items: center;
    }}

    .left-logo {{
        justify-content: flex-start;
    }}

    .right-logo {{
        justify-content: flex-end;
    }}

    .platform-logo {{
        max-height: 82px;
        max-width: 165px;
        object-fit: contain;
        display: block;
    }}

    .cfp-logo {{
        max-height: 86px;
    }}

    .usj-logo {{
        max-height: 78px;
    }}

    .header-center {{
        text-align: center;
        flex: 1;
        padding: 0 20px;
    }}

    .header-title {{
        color: {USJ_BLUE};
        font-weight: 400;
        font-size: 1.45rem;
        line-height: 1.2;
    }}

    .header-subtitle {{
        color: #6B7688;
        font-weight: 700;
        font-size: 0.96rem;
        margin-top: 4px;
    }}

    .logo-placeholder {{
        border: 2px solid {USJ_BLUE};
        color: {USJ_BLUE};
        border-radius: 14px;
        padding: 14px 20px;
        font-weight: 400;
        background: #F7FAFE;
    }}

    .main-hero {{
        background: linear-gradient(135deg, {USJ_BLUE} 0%, #123E7C 60%, {USJ_RED} 100%);
        border-radius: 24px;
        padding: 30px 34px;
        margin-bottom: 24px;
        color: white;
        box-shadow: 0 18px 45px rgba(0,31,91,0.18);
    }}

    .hero-kicker {{
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        opacity: 0.85;
        font-weight: 700;
        margin-bottom: 8px;
    }}

    .hero-title {{
        font-size: 2.15rem;
        line-height: 1.1;
        font-weight: 400;
        margin-bottom: 10px;
    }}

    .hero-subtitle {{
        font-size: 1.02rem;
        line-height: 1.55;
        opacity: 0.95;
    }}

    div[data-baseweb="input"],
    div[data-baseweb="select"],
    div[data-baseweb="textarea"] {{
        background-color: #ffffff !important;
        border: 2px solid {USJ_BLUE} !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 14px rgba(0,31,91,0.12) !important;
        min-height: 52px !important;
    }}

    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"]:focus-within,
    div[data-baseweb="textarea"]:focus-within {{
        border: 3px solid {USJ_RED} !important;
        box-shadow: 0 0 0 4px rgba(139,21,56,0.14) !important;
    }}

    div[data-baseweb="input"] input {{
        background-color: #ffffff !important;
        color: {USJ_BLUE} !important;
        font-weight: 750 !important;
        font-size: 17px !important;
        padding: 12px 14px !important;
    }}

    div[data-baseweb="select"] {{
        min-height: 58px !important;
        padding: 3px 6px !important;
        box-sizing: border-box !important;
        overflow: visible !important;
    }}

    div[data-baseweb="select"] > div {{
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        padding-left: 10px !important;
        padding-right: 10px !important;
        box-sizing: border-box !important;
    }}

    div[data-baseweb="select"] div,
    div[data-baseweb="select"] span {{
        color: {USJ_BLUE} !important;
        font-weight: 750 !important;
        font-size: 16px !important;
        opacity: 1 !important;
        line-height: 1.35 !important;
    }}

    div[data-baseweb="select"] svg {{
        color: {USJ_BLUE} !important;
        fill: {USJ_BLUE} !important;
    }}


    div[data-baseweb="textarea"] textarea {{
        background-color: #ffffff !important;
        color: {USJ_BLUE} !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        padding: 14px 16px !important;
        min-height: 120px !important;
        line-height: 1.5 !important;
    }}

    .stSelectbox,
    .stTextArea,
    .stTextInput {{
        margin-bottom: 12px !important;
        overflow: visible !important;
    }}

    label {{
        color: {USJ_BLUE} !important;
        font-weight: 800 !important;
        font-size: 16px !important;
    }}

    .identity-card {{
        background:#ffffff;
        border: 1px solid #DDE5F0;
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 10px 28px rgba(27,42,65,0.06);
        min-height: 112px;
    }}

    .identity-label {{
        color:#6B7688;
        font-size: 0.84rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 10px;
    }}

    .identity-value {{
        color:{USJ_TEXT};
        font-size: 1.35rem;
        font-weight: 750;
        line-height: 1.2;
    }}

    .section-card {{
        background:#ffffff;
        border:1px solid #DDE5F0;
        border-radius:20px;
        padding:20px 22px;
        margin: 18px 0;
        box-shadow: 0 12px 32px rgba(27,42,65,0.07);
    }}

    .blue {{ border-top: 5px solid {USJ_BLUE}; }}
    .red {{ border-top: 5px solid {USJ_RED}; }}
    .gold {{ border-top: 5px solid {USJ_GOLD}; }}

    .step-title {{
        color:{USJ_BLUE};
        font-weight: 820;
        font-size: 1.18rem;
        margin-bottom: 8px;
    }}

    .step-help {{
        color:#5D697A;
        font-size:0.94rem;
    }}

    .card {{
        background:#ffffff;
        border:1px solid #DDE5F0;
        border-radius:16px;
        padding:16px 18px;
        margin-bottom:12px;
        box-shadow:0 8px 22px rgba(27,42,65,0.06);
    }}

    .blue-card {{ border-left:6px solid {USJ_BLUE}; }}
    .red-card {{ border-left:6px solid {USJ_RED}; }}
    .gold-card {{ border-left:6px solid {USJ_GOLD}; }}

    .pill {{
        display:inline-block;
        padding:8px 12px;
        margin:4px 5px 4px 0;
        border-radius:999px;
        background:#EAF2F8;
        color:{USJ_BLUE};
        font-weight:750;
        font-size:14px;
    }}

    .pill-red {{ background:#F8EDEF; color:{USJ_RED}; }}
    .pill-green {{ background:#E9F7EF; color:#146C43; }}
    .pill-final {{ background:#FFF8DF; color:{USJ_BLUE}; border:1px solid #E6D58D; }}

    .visual-column {{
        background: #ffffff;
        border: 1px solid #DDE5F0;
        border-radius: 18px;
        padding: 14px;
        box-shadow: 0 10px 28px rgba(27,42,65,0.06);
        margin-bottom: 10px;
    }}

    .visual-column-title {{
        font-size: 1.08rem;
        font-weight: 400;
        color: #001F5B;
        margin-bottom: 10px;
        padding-bottom: 6px;
        border-bottom: 1px solid #DDE5F0;
    }}

    .visual-employee {{ border-top: 5px solid #001F5B; }}
    .visual-director {{ border-top: 5px solid #8B1538; }}
    .visual-final {{ border-top: 5px solid #C9A227; }}

    .priority-card {{
        border-radius: 16px;
        padding: 10px 12px;
        margin-bottom: 8px;
        border: 1px solid #DDE5F0;
    }}

    .employee-card {{
        background: #EAF2F8;
        border-left: 6px solid #001F5B;
    }}

    .director-card {{
        background: #F8EDEF;
        border-left: 6px solid #8B1538;
    }}

    .final-card {{
        background: #FFF8DF;
        border-left: 6px solid #C9A227;
    }}

    .priority-rank {{
        font-size: 0.78rem;
        font-weight: 400;
        color: #5D697A;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 5px;
    }}

    .priority-theme {{
        font-size: 0.98rem;
        font-weight: 400;
        color: #001F5B;
        line-height: 1.35;
    }}

    .priority-badge {{
        margin-top: 8px;
        display: inline-block;
        padding: 5px 9px;
        border-radius: 999px;
        background: #ffffff;
        color: #735C00;
        font-size: 0.76rem;
        font-weight: 500;
        border: 1px solid #E6D58D;
    }}

    div.stButton > button {{
        border-radius:12px;
        background:{USJ_BLUE};
        color:white;
        border:0;
        font-weight:500;
        min-height: 46px;
    }}

    div.stButton > button:hover {{
        background:#123E7C;
        color:white;
        border:0;
    }}

    @media (max-width: 760px) {{
        .platform-header {{
            padding: 14px 16px;
            gap: 10px;
        }}

        .logo-side {{
            width: 90px;
        }}

        .platform-logo {{
            max-height: 58px;
            max-width: 88px;
        }}

        .header-title {{
            font-size: 1.05rem;
        }}

        .header-subtitle {{
            font-size: 0.78rem;
        }}

        .hero-title {{
            font-size: 1.55rem;
        }}
    }}
    
    .admin-action-button {{
        width: 100%;
        min-height: 50px;
        background: #001F5B;
        color: #ffffff;
        border: 0;
        border-radius: 12px;
        padding: 13px 18px;
        font-weight: 400;
        font-size: 15px;
        cursor: pointer;
        box-shadow: 0 6px 16px rgba(0,31,91,0.16);
    }}

    .admin-action-button:hover {{
        background: #123E7C;
        color: #ffffff;
    }}

    div[data-testid="stDownloadButton"] > button {{
        width: 100% !important;
        min-height: 50px !important;
        background: #001F5B !important;
        color: #ffffff !important;
        border: 0 !important;
        border-radius: 12px !important;
        padding: 13px 18px !important;
        font-weight: 400 !important;
        font-size: 15px !important;
        box-shadow: 0 6px 16px rgba(0,31,91,0.16) !important;
    }}

    div[data-testid="stDownloadButton"] > button:hover {{
        background: #123E7C !important;
        color: #ffffff !important;
        border: 0 !important;
    }}

    @media print {{
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        button,
        .admin-action-button {{
            display: none !important;
        }}

        .main-hero {{
            box-shadow: none !important;
            border-radius: 0 !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}
    }}

    
    div[data-testid="stDownloadButton"] > button {{
        width: 100% !important;
        min-height: 50px !important;
        height: 50px !important;
        background: #001F5B !important;
        color: #ffffff !important;
        border: 0 !important;
        border-radius: 12px !important;
        padding: 13px 18px !important;
        font-weight: 400 !important;
        font-size: 15px !important;
        line-height: 1.2 !important;
        box-shadow: 0 6px 16px rgba(0,31,91,0.16) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    div[data-testid="stDownloadButton"] > button:hover {{
        background: #123E7C !important;
        color: #ffffff !important;
        border: 0 !important;
    }}

    @media print {{
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        .main-hero,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr {{
            display: none !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        .card.blue-card {{
            page-break-before: always !important;
            break-before: page !important;
            margin-top: 0 !important;
        }}

        .card.blue-card:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .visual-column {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            box-shadow: none !important;
        }}

        .priority-card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}

        h3 {{
            page-break-after: avoid !important;
        }}

        body {{
            background: white !important;
        }}
    }}

    
    .employee-grid-print {{
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 16px;
        align-items: start;
    }}

    .employee-print-page {{
        margin-bottom: 26px;
        page-break-inside: avoid;
        break-inside: avoid;
    }}

    .employee-main-card {{
        margin-bottom: 12px;
    }}

    .employee-summary-card {{
        margin-bottom: 14px;
    }}

    .empty-choice {{
        color: #6B7688;
        font-weight: 600;
        padding: 8px 0;
    }}

    @media print {{
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        .no-print,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr {{
            display: none !important;
        }}

        .platform-header {{
            display: flex !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
        }}

        .main-hero {{
            box-shadow: none !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        body,
        .stApp {{
            background: white !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 92vh !important;
            box-sizing: border-box !important;
            padding-top: 8px !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print {{
            display: grid !important;
            grid-template-columns: 1fr 1fr 1fr !important;
            gap: 12px !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}

        .visual-column,
        .priority-card,
        .card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            box-shadow: none !important;
        }}

        .visual-column {{
            min-height: auto !important;
        }}

        .priority-card {{
            margin-bottom: 7px !important;
        }}

        .employee-main-card,
        .employee-summary-card {{
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        h1, h2, h3 {{
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}
    }}

    
    @media print {{
        .no-print,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr {{
            display: none !important;
        }}

        .platform-header {{
            display: flex !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 92vh !important;
            box-sizing: border-box !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print,
        .visual-column,
        .priority-card,
        .card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}
    }}

    
    /* FINAL PRINT FIX */
    @media print {{
        .no-print,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr {{
            display: none !important;
        }}

        .platform-header {{
            display: flex !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .main-hero {{
            display: block !important;
            box-shadow: none !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        body,
        .stApp {{
            background: white !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 90vh !important;
            box-sizing: border-box !important;
            padding-top: 8px !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print {{
            display: grid !important;
            grid-template-columns: 1fr 1fr 1fr !important;
            gap: 12px !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}

        .visual-column,
        .priority-card,
        .card,
        .employee-main-card,
        .employee-summary-card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            box-shadow: none !important;
        }}

        h1, h2, h3 {{
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}
    }}

    
    /* FINAL PDF PRINT HEADER FIX */
    @media print {{
        .platform-header {{
            display: flex !important;
            visibility: visible !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            border-radius: 12px !important;
            margin-bottom: 16px !important;
            padding: 12px 18px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .platform-logo {{
            display: block !important;
            visibility: visible !important;
            max-height: 68px !important;
            max-width: 145px !important;
        }}

        .header-title,
        .header-subtitle {{
            display: block !important;
            visibility: visible !important;
        }}

        .no-print,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr,
        label,
        div[data-baseweb="select"],
        .stSelectbox {{
            display: none !important;
            visibility: hidden !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        body,
        .stApp {{
            background: white !important;
        }}

        .main-hero {{
            box-shadow: none !important;
            margin-bottom: 14px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 90vh !important;
            box-sizing: border-box !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print,
        .visual-column,
        .priority-card,
        .card,
        .employee-main-card,
        .employee-summary-card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            box-shadow: none !important;
        }}
    }}

    </style>
    """, unsafe_allow_html=True)


def render_platform_header():
    cfp_logo = image_to_base64(CFP_LOGO_PATH)
    usj_logo = image_to_base64(USJ_LOGO_PATH)

    cfp_html = (
        f"<img src='data:image/png;base64,{cfp_logo}' class='platform-logo cfp-logo'>"
        if cfp_logo else
        "<div class='logo-placeholder'>CFP</div>"
    )

    usj_html = (
        f"<img src='data:image/png;base64,{usj_logo}' class='platform-logo usj-logo'>"
        if usj_logo else
        "<div class='logo-placeholder'>USJ</div>"
    )

    st.markdown(f"""
    <div class="platform-header">
        <div class="logo-side left-logo">{cfp_html}</div>
        <div class="header-center">
            <div class="header-title">Centre de Formation Professionnelle</div>
            <div class="header-subtitle">Training Needs Assessment - TNA 2026-2027</div>
        </div>
        <div class="logo-side right-logo">{usj_html}</div>
    </div>
    """, unsafe_allow_html=True)


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            respondent_code TEXT,
            role TEXT,
            name TEXT,
            faculty TEXT,
            institution TEXT,
            department TEXT,
            data_json TEXT,
            submitted_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS admin_theme_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT UNIQUE,
            employee_ranked_json TEXT,
            director_ranked_json TEXT,
            updated_by TEXT,
            updated_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS custom_users (
            code TEXT PRIMARY KEY,
            role TEXT,
            name TEXT,
            poste TEXT,
            faculty TEXT,
            institution TEXT,
            department TEXT,
            director_code TEXT,
            created_by TEXT,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS director_employee_exclusions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            director_code TEXT,
            employee_code TEXT,
            removed_by TEXT,
            removed_at TEXT,
            UNIQUE(director_code, employee_code)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS employee_validations (
            employee_code TEXT PRIMARY KEY,
            validated_by TEXT,
            validated_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS director_validations (
            director_code TEXT PRIMARY KEY,
            validated_by TEXT,
            validated_at TEXT
        )
    """)

    
    
    conn.commit()
    conn.close()



def load_custom_users():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT code, role, name, poste, faculty, institution, department, director_code
        FROM custom_users
    """).fetchall()
    conn.close()

    users = {}

    for code, role, name, poste, faculty, institution, department, director_code in rows:
        clean_code = str(code).strip().upper()
        users[clean_code] = {
            "ldap": clean_code,
            "code": clean_code,
            "role": role,
            "name": name,
            "poste": poste or "",
            "faculty": faculty or "",
            "institution": institution or "USJ",
            "department": department or "",
            "director_code": str(director_code or "").strip().upper()
        }

    return users



def get_all_users():
    users = DEMO_USERS.copy()
    users.update(load_custom_users())
    return users


def get_user_by_code(code):
    entered_values = login_variants(code)
    all_users = get_all_users()

    for entered in entered_values:
        if entered in all_users:
            user = all_users[entered].copy()
            user["ldap"] = user.get("ldap", entered)
            user["code"] = user.get("code", entered)
            return user

    for user_code, user in all_users.items():
        possible_values = set()
        possible_values.update(login_variants(user_code))
        for field in ["ldap", "code", "email", "director_code", "director_ldap"]:
            possible_values.update(login_variants(user.get(field, "")))

        if entered_values.intersection(possible_values):
            user = user.copy()
            user["ldap"] = user.get("ldap", user_code)
            user["code"] = user.get("code", user_code)
            return user

    return None


def custom_user_exists(code):
    code = clean_login_value(code)

    if code in get_all_users():
        return True

    conn = sqlite3.connect(DB_NAME)
    row = conn.execute(
        "SELECT code FROM custom_users WHERE code = ?",
        (code,)
    ).fetchone()
    conn.close()

    return row is not None


def add_custom_employee(code, name, poste, faculty, institution, department, director_code):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO custom_users (
            code, role, name, poste, faculty, institution, department, director_code, created_by, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(code).strip().upper(),
        "psg",
        str(name).strip(),
        str(poste).strip(),
        str(faculty).strip(),
        str(institution).strip() or "USJ",
        str(department).strip(),
        str(director_code).strip().upper(),
        st.session_state.get("code", ""),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()



def get_removed_employee_codes_for_director(director_code):
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT employee_code
        FROM director_employee_exclusions
        WHERE director_code = ?
    """, (str(director_code).strip().upper(),)).fetchall()
    conn.close()

    return {row[0] for row in rows}


def remove_employee_from_director(director_code, employee_code):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT OR IGNORE INTO director_employee_exclusions (
            director_code,
            employee_code,
            removed_by,
            removed_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        str(director_code).strip().upper(),
        str(employee_code).strip().upper(),
        st.session_state.get("code", ""),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def save_response(user, data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO responses (
            respondent_code, role, name, faculty, institution, department, data_json, submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        st.session_state["code"],
        user["role"],
        user["name"],
        user["faculty"],
        user["institution"],
        user["department"],
        json.dumps(data, ensure_ascii=False),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()




def load_responses():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT respondent_code, role, name, faculty, institution, department, data_json, submitted_at
        FROM responses
        ORDER BY submitted_at DESC
    """).fetchall()
    conn.close()

    current_codes = {
        str(code).strip().upper()
        for code, user in get_all_users().items()
        if user.get("role") in ["psg", "director"]
    }

    records = []

    for row in rows:
        code, role, name, faculty, institution, department, data_json, submitted_at = row
        code = str(code).strip().upper()

        # Ignore old trial/demo responses still stored in SQLite, without deleting any real data.
        if code not in current_codes:
            continue

        try:
            data = json.loads(data_json)
        except Exception:
            data = {}

        records.append({
            "Code": code,
            "Profil": role,
            "Nom": name,
            "Faculté": faculty,
            "Institution": institution,
            "Date": submitted_at,
            "Données": data
        })

    return pd.DataFrame(records)


def load_submitted_answers_for_admin():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT id, respondent_code, role, name, faculty, institution, submitted_at
        FROM responses
        WHERE role IN ('psg', 'director')
        ORDER BY submitted_at DESC
    """).fetchall()
    conn.close()

    current_codes = {
        str(code).strip().upper()
        for code, user in get_all_users().items()
        if user.get("role") in ["psg", "director"]
    }

    records = []

    for response_id, code, role, name, faculty, institution, submitted_at in rows:
        clean_code = str(code).strip().upper()

        if clean_code not in current_codes:
            continue

        records.append({
            "id": response_id,
            "code": clean_code,
            "role": role,
            "name": name or "",
            "faculty": faculty or "",
            "institution": institution or "",
            "submitted_at": submitted_at or ""
        })

    return records


def delete_submitted_answer(response_id, respondent_code, role, delete_all_for_user=False):
    respondent_code = str(respondent_code).strip().upper()
    role = str(role).strip()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if delete_all_for_user:
        c.execute(
            "DELETE FROM responses WHERE respondent_code = ?",
            (respondent_code,)
        )
    else:
        c.execute(
            "DELETE FROM responses WHERE id = ?",
            (response_id,)
        )

    remaining = c.execute(
        "SELECT COUNT(*) FROM responses WHERE respondent_code = ?",
        (respondent_code,)
    ).fetchone()[0]

    if remaining == 0:
        if role == "psg":
            c.execute(
                "DELETE FROM employee_validations WHERE employee_code = ?",
                (respondent_code,)
            )
            c.execute(
                "DELETE FROM admin_theme_overrides WHERE employee_code = ?",
                (respondent_code,)
            )

        elif role == "director":
            c.execute(
                "DELETE FROM director_validations WHERE director_code = ?",
                (respondent_code,)
            )

    conn.commit()
    conn.close()



def save_admin_theme_override(employee_code, employee_ranked, director_ranked):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO admin_theme_overrides (
            employee_code,
            employee_ranked_json,
            director_ranked_json,
            updated_by,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(employee_code) DO UPDATE SET
            employee_ranked_json = excluded.employee_ranked_json,
            director_ranked_json = excluded.director_ranked_json,
            updated_by = excluded.updated_by,
            updated_at = excluded.updated_at
    """, (
        employee_code,
        json.dumps(employee_ranked, ensure_ascii=False),
        json.dumps(director_ranked, ensure_ascii=False),
        st.session_state.get("code", "ADMIN"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def load_admin_theme_overrides():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT employee_code, employee_ranked_json, director_ranked_json, updated_by, updated_at
        FROM admin_theme_overrides
    """).fetchall()
    conn.close()

    overrides = {}

    for employee_code, employee_json, director_json, updated_by, updated_at in rows:
        try:
            employee_ranked = json.loads(employee_json or "[]")
        except Exception:
            employee_ranked = []

        try:
            director_ranked = json.loads(director_json or "[]")
        except Exception:
            director_ranked = []

        overrides[employee_code] = {
            "employee_ranked": employee_ranked,
            "director_ranked": director_ranked,
            "updated_by": updated_by,
            "updated_at": updated_at
        }

    return overrides


def get_employees_for_director(director_code):
    employees = []
    all_users = get_all_users()
    removed_codes = get_removed_employee_codes_for_director(director_code)

    for code, info in all_users.items():
        if (
            info.get("role") == "psg"
            and info.get("director_code") == director_code
            and code not in removed_codes
        ):
            emp = info.copy()
            emp["code"] = code
            emp["is_custom"] = code not in DEMO_USERS
            employees.append(emp)

    employees = sorted(
        employees,
        key=lambda x: (
            1 if x.get("is_custom") else 0,
            x.get("code", "")
        )
    )

    return employees


def latest_by_code(df, code):
    if df.empty:
        return None

    subset = df[df["Code"] == code].sort_values("Date", ascending=False)

    if subset.empty:
        return None

    return subset.iloc[0].to_dict()


def unique_ranked_select(label, options, key_prefix):
    st.markdown(f"**{label}**")

    c1, c2, c3 = st.columns(3)

    with c1:
        p1 = st.selectbox("Priorité 1", [""] + options, key=f"{key_prefix}_p1")

    with c2:
        remaining2 = [x for x in options if x != p1]
        p2 = st.selectbox("Priorité 2", [""] + remaining2, key=f"{key_prefix}_p2")

    with c3:
        remaining3 = [x for x in options if x not in [p1, p2]]
        p3 = st.selectbox("Priorité 3", [""] + remaining3, key=f"{key_prefix}_p3")

    return [x for x in [p1, p2, p3] if x]


def ranked_select_with_defaults(label, options, key_prefix, defaults=None, disabled=False):
    defaults = defaults or []
    defaults = [x for x in defaults if x in options]

    p1_default = defaults[0] if len(defaults) > 0 else ""
    p2_default = defaults[1] if len(defaults) > 1 else ""
    p3_default = defaults[2] if len(defaults) > 2 else ""

    st.markdown(f"**{label}**")

    c1, c2, c3 = st.columns(3)

    with c1:
        options_1 = [""] + options
        p1 = st.selectbox(
            "Priorité 1",
            options_1,
            index=options_1.index(p1_default) if p1_default in options_1 else 0,
            key=f"{key_prefix}_p1",
            disabled=disabled
        )

    with c2:
        remaining_2 = [x for x in options if x != p1]
        options_2 = [""] + remaining_2
        p2 = st.selectbox(
            "Priorité 2",
            options_2,
            index=options_2.index(p2_default) if p2_default in options_2 else 0,
            key=f"{key_prefix}_p2",
            disabled=disabled
        )

    with c3:
        remaining_3 = [x for x in options if x not in [p1, p2]]
        options_3 = [""] + remaining_3
        p3 = st.selectbox(
            "Priorité 3",
            options_3,
            index=options_3.index(p3_default) if p3_default in options_3 else 0,
            key=f"{key_prefix}_p3",
            disabled=disabled
        )

    return [x for x in [p1, p2, p3] if x]


def calculate_final_themes(employee_ranked, director_ranked):
    """
    Final selection method:
    1. Common themes are always selected first.
    2. If there are 3 common themes, final = the 3 common themes.
    3. If there are 2 common themes, add 1 extra theme from the director.
    4. If there is 1 common theme, add 2 extra themes from the director.
    5. If there is no common theme, select 2 themes from the director and 1 theme from the employee.
    6. Final list always contains maximum 3 themes.
    """

    employee_ranked = employee_ranked or []
    director_ranked = director_ranked or []

    final = []
    matched = []

    employee_set = set(employee_ranked)
    director_set = set(director_ranked)

    common_themes = [
        theme for theme in employee_ranked
        if theme in director_set
    ]

    def add_theme(theme, is_common=False):
        if theme and theme not in final and len(final) < 3:
            final.append(theme)
            if is_common and theme not in matched:
                matched.append(theme)

    # 1. Add common themes first
    for theme in common_themes:
        add_theme(theme, is_common=True)

    # 2. Count how many non-common themes are needed
    remaining_slots = 3 - len(final)

    # Case A: 3 common themes
    if remaining_slots <= 0:
        return matched[:3], final[:3]

    # Case B: 2 common themes, director chooses 1 extra
    # Case C: 1 common theme, director chooses 2 extra
    # Case D: 0 common themes, director chooses 2 and employee chooses 1
    director_slots = min(2, remaining_slots)

    if len(common_themes) == 2:
        director_slots = 1

    elif len(common_themes) == 1:
        director_slots = 2

    elif len(common_themes) == 0:
        director_slots = 2

    # 3. Add director choices first
    added_director = 0

    for theme in director_ranked:
        if len(final) >= 3:
            break

        if theme not in common_themes and added_director < director_slots:
            before_count = len(final)
            add_theme(theme, is_common=False)

            if len(final) > before_count:
                added_director += 1

    # 4. Add employee choice only if needed
    for theme in employee_ranked:
        if len(final) >= 3:
            break

        if theme not in common_themes:
            add_theme(theme, is_common=False)

    # 5. Emergency fallback if still incomplete
    for theme in director_ranked + employee_ranked:
        if len(final) >= 3:
            break

        add_theme(theme, is_common=theme in employee_set and theme in director_set)

    return matched[:3], final[:3]


def render_theme_pills(themes, css_class="pill"):
    if not themes:
        st.caption("Aucun thème sélectionné.")
        return

    html = "".join([
        f"<span class='{css_class}'>{i}. {theme}</span>"
        for i, theme in enumerate(themes, start=1)
    ])

    st.markdown(html, unsafe_allow_html=True)


def render_form_hero(profile_label, title, objective):
    st.markdown(f"""
    <div class="main-hero">
        <div class="hero-kicker">TNA 2026-2027 | {profile_label}</div>
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{objective}</div>
    </div>
    """, unsafe_allow_html=True)


def render_identity_cards(user):
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="identity-card">
            <div class="identity-label">Nom</div>
            <div class="identity-value">{user['name']}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="identity-card">
            <div class="identity-label">Poste</div>
            <div class="identity-value">{user.get('poste', '')}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="identity-card">
            <div class="identity-label">Faculté / Institution</div>
            <div class="identity-value">{user.get('institution', user.get('faculty', ''))}</div>
        </div>
        """, unsafe_allow_html=True)

def render_ranked_section_header(title, help_text, color_class="blue"):
    st.markdown(f"""
    <div class="section-card {color_class}">
        <div class="step-title">{title}</div>
        <div class="step-help">{help_text}</div>
    </div>
    """, unsafe_allow_html=True)

def submit_login_code():
    st.session_state["enter_login"] = True


def login_page():
    st.markdown("""
    <div class="main-hero">
        <div class="hero-kicker">TNA 2026-2027</div>
        <div class="hero-title">Plateforme d’analyse des besoins en formation</div>
        <div class="hero-subtitle">Accès sécurisé par code au questionnaire PSG, au questionnaire Doyens / Directeurs et au tableau de bord administrateur.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    .st-key-access_code input {
        -webkit-text-security: disc !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        code = st.text_input(
            "Ajoutez votre code LDAP",
            type="default",
            placeholder="",
            key="access_code",
            on_change=submit_login_code
        )

        enter_form = st.button(
            "Accéder au questionnaire",
            use_container_width=True
        ) or st.session_state.pop("enter_login", False)

        if enter_form:
            cleaned_code = code.strip().upper()

            if not cleaned_code:
                st.warning("Veuillez saisir votre code d’accès.")
                st.stop()

            user_info = get_user_by_code(cleaned_code)

            if user_info:
                ldap_code = user_info.get("ldap", cleaned_code)

                st.session_state["logged_in"] = True
                st.session_state["code"] = ldap_code
                st.session_state["login_code"] = cleaned_code
                st.session_state["user"] = user_info
                st.rerun()
            else:
                st.error("Code d’accès non reconnu.")

def load_latest_response_for_code(code):
    conn = sqlite3.connect(DB_NAME)
    row = conn.execute("""
        SELECT data_json
        FROM responses
        WHERE respondent_code = ?
        ORDER BY submitted_at DESC
        LIMIT 1
    """, (str(code).strip().upper(),)).fetchone()
    conn.close()

    if not row:
        return {}

    try:
        return json.loads(row[0])
    except Exception:
        return {}

def is_employee_validated(employee_code):
    conn = sqlite3.connect(DB_NAME)
    row = conn.execute(
        "SELECT employee_code FROM employee_validations WHERE employee_code = ?",
        (str(employee_code).strip().upper(),)
    ).fetchone()
    conn.close()
    return row is not None


def validate_employee_response(employee_code):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        INSERT OR REPLACE INTO employee_validations (
            employee_code, validated_by, validated_at
        )
        VALUES (?, ?, ?)
    """, (
        str(employee_code).strip().upper(),
        st.session_state.get("code", ""),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def allow_employee_resubmission(employee_code):
    """Allow an employee to submit again by clearing the existing submitted answer."""
    clean_code = str(employee_code).strip().upper()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        "DELETE FROM responses WHERE respondent_code = ? AND role = ?",
        (clean_code, "psg")
    )

    c.execute(
        "DELETE FROM employee_validations WHERE employee_code = ?",
        (clean_code,)
    )

    c.execute(
        "DELETE FROM admin_theme_overrides WHERE employee_code = ?",
        (clean_code,)
    )

    conn.commit()
    conn.close()


def is_director_validated(director_code):
    conn = sqlite3.connect(DB_NAME)
    row = conn.execute(
        "SELECT director_code FROM director_validations WHERE director_code = ?",
        (str(director_code).strip().upper(),)
    ).fetchone()
    conn.close()
    return row is not None


def validate_director_response(director_code):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        INSERT OR REPLACE INTO director_validations (
            director_code, validated_by, validated_at
        )
        VALUES (?, ?, ?)
    """, (
        str(director_code).strip().upper(),
        st.session_state.get("code", ""),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def render_psg_form(user):
    render_form_hero(
        "Personnel de soutien et de gestion",
        "Questionnaire d’analyse des besoins en formation - PSG",
        "Ce court questionnaire nous aide à comprendre vos besoins en formation. Les résultats seront utilisés pour concevoir des programmes de formation qui soutiennent votre travail, améliorent vos compétences et favorisent votre développement professionnel.<br><br><b>Il vous faudra environ 5 à 10 minutes pour le compléter. Vos réponses resteront confidentielles.</b>"
    )

    saved_data = load_latest_response_for_code(st.session_state["code"])

    # Once the employee has submitted, the page is intentionally kept blank.
    # The employee cannot view or modify answers unless the director authorizes a new submission.
    if saved_data or is_employee_validated(st.session_state["code"]):
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.success(
            "Vos réponses ont été soumises. Vous ne pouvez plus les modifier. "
            "Votre Doyen / Directeur peut vous autoriser à remplir à nouveau le questionnaire si nécessaire."
        )
        return

    render_identity_cards(user)

    saved_ranked = []
    saved_other = ""

    st.markdown("<br>", unsafe_allow_html=True)

    render_ranked_section_header(
        "Classement des thèmes prioritaires",
        "Veuillez choisir exactement 3 thèmes, dans l’ordre d’importance. La priorité 1 correspond au besoin le plus important.",
        "blue"
    )

    ranked_themes = ranked_select_with_defaults(
        "Vos 3 thèmes de formation prioritaires :",
        PSG_THEMES,
        "psg_ranked",
        saved_ranked,
        disabled=False
    )

    other_themes = st.text_area(
        "Autre(s) thème(s) ou sujet(s) de formation proposés",
        value=saved_other,
        key="psg_other",
        placeholder="Indiquez ici un thème non présent dans la liste, si nécessaire.",
        disabled=False
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Soumettre mes réponses", use_container_width=True):
        if len(ranked_themes) != 3:
            st.warning("Veuillez sélectionner exactement 3 thèmes classés par ordre de priorité.")
            return

        data = {
            "ranked_themes": ranked_themes,
            "selected_themes": ranked_themes,
            "other_themes": other_themes,
            "director_code": user.get("director_code", "")
        }

        save_response(user, data)
        st.success("Vos réponses ont été enregistrées avec succès.")
        st.rerun()

def render_director_form(user):
    render_form_hero(
        "Doyens et Directeurs",
        "Questionnaire d’analyse des besoins en formation - Doyens et Directeurs",
        "Ce questionnaire vise à identifier vos besoins en formation en tant que leader ainsi que les besoins de développement de vos employés. Les résultats nous aideront à concevoir des programmes de formation qui soutiennent le leadership, améliorent la performance des équipes et s’alignent sur les objectifs de l’université.<br><br><b>Il vous faudra environ 10 minutes pour le compléter.</b>"
    )

    render_identity_cards(user)

    saved_data = load_latest_response_for_code(st.session_state["code"])
    director_read_only = is_director_validated(st.session_state["code"])
    saved_leader_ranked = saved_data.get("leader_ranked_themes", [])
    saved_leader_other = saved_data.get("leader_other_themes", "")
    saved_employees_map = {
        item.get("employee_code"): item
        for item in saved_data.get("employees_training_needs", [])
    }

    st.markdown("<br>", unsafe_allow_html=True)

    render_ranked_section_header(
        "A. Vos besoins de formation en tant que leader",
        "Veuillez choisir au moins 1 thématique, dans l’ordre d’importance pour votre rôle de direction.",
        "red"
    )

    leader_ranked = ranked_select_with_defaults(
        "Vos 3 thématiques prioritaires :",
        DD_LEADER_THEMES,
        "leader_ranked",
        saved_leader_ranked,
        disabled=director_read_only
    )

    leader_other = st.text_area(
        "Autre(s) thème(s) proposés pour vous-même",
        value=saved_leader_other,
        key="leader_other",
        placeholder="Indiquez ici un thème de leadership non présent dans la liste, si nécessaire.",
        disabled=director_read_only
    )

    st.markdown("<br>", unsafe_allow_html=True)

    employees = get_employees_for_director(st.session_state["code"])

    render_ranked_section_header(
        "B. Besoins de formation de vos employés",
        f"{len(employees)} employé(s) lié(s) à votre compte. Pour chaque employé, vous pouvez classer jusqu’à 3 thèmes prioritaires.",
        "gold"
    )

    employee_training_needs = []
    director_visible_df = load_responses()

    for emp in employees:
        with st.expander(f"{emp['name']}", expanded=True):
            info_col, remove_col = st.columns([6, 1])

            with info_col:
                st.markdown(
                    f"<span class='pill'>Code : {emp['code']}</span>",
                    unsafe_allow_html=True
                )

            with remove_col:
                if st.button(
                    "Retirer",
                    key=f"remove_employee_{emp['code']}",
                    use_container_width=True
                ):
                    remove_employee_from_director(
                        st.session_state["code"],
                        emp["code"]
                    )
                    st.success(f"{emp['name']} a été retiré de votre liste.")
                    st.rerun()


            emp_response = latest_by_code(director_visible_df, emp["code"])

            if emp_response:
                emp_data = emp_response["Données"]
                employee_submitted_themes = emp_data.get(
                    "ranked_themes",
                    emp_data.get("selected_themes", [])
                )
                employee_other_themes = emp_data.get("other_themes", "")

                st.markdown("**Réponses déjà soumises par l’employé :**")
                render_theme_pills(employee_submitted_themes, "pill")

                if employee_other_themes:
                    st.markdown(f"""
                    <div class='card blue-card'>
                        <b>Autre(s) thème(s) proposé(s) par l’employé :</b><br>
                        {employee_other_themes}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Cet employé n’a pas encore soumis ses réponses.")

            if emp_response and not director_read_only:
                if st.button(
                    "Autoriser une nouvelle soumission",
                    key=f"allow_resubmission_{emp['code']}",
                    use_container_width=True
                ):
                    allow_employee_resubmission(emp["code"])
                    st.success(f"{emp['name']} peut maintenant remplir à nouveau le questionnaire.")
                    st.rerun()

            saved_emp_item = saved_employees_map.get(emp["code"], {})
            saved_emp_ranked = saved_emp_item.get("ranked_themes_by_director", [])
            saved_emp_other = saved_emp_item.get("other_themes", "")
            
            emp_ranked = ranked_select_with_defaults(
                f"Classement des 3 thèmes prioritaires pour {emp['name']} :",
                PSG_THEMES,
                f"director_emp_{emp['code']}",
                saved_emp_ranked,
                disabled=director_read_only
            )

            emp_other = st.text_area(
                f"Autre(s) besoin(s) spécifique(s) pour {emp['name']}",
                value=saved_emp_other,
                key=f"other_{emp['code']}",
                placeholder="Indiquez ici un besoin particulier, si nécessaire.",
                disabled=director_read_only
            )

            validate_col, status_col = st.columns([1.4, 4])

            with validate_col:
                if is_employee_validated(emp["code"]):
                    st.button(
                        "Validé",
                        key=f"validated_employee_{emp['code']}",
                        use_container_width=False,
                        disabled=True
                    )
                else:
                    if st.button(
                        "Valider",
                        key=f"validate_employee_{emp['code']}",
                        use_container_width=False,
                        disabled=director_read_only
                    ):
                        validate_employee_response(emp["code"])
                        st.success(f"Les réponses de {emp['name']} ont été validées.")
                        st.rerun()

            with status_col:
                if is_employee_validated(emp["code"]):
                    st.success("Réponses validées.")


            
            employee_training_needs.append({
                "employee_code": emp["code"],
                "employee_name": emp["name"],
                "employee_department": "",
                "ranked_themes_by_director": emp_ranked,
                "selected_themes": emp_ranked,
                "other_themes": emp_other
            })

    
    with st.expander("+ Ajouter un employé", expanded=False):
        new_emp_code = st.text_input(
            "Code de l’employé",
            key="new_emp_code",
            placeholder="Exemple : PSG026"
        )

        new_emp_name = st.text_input(
            "Nom de l’employé",
            key="new_emp_name"
        )

        new_emp_poste = st.text_input(
            "Poste",
            key="new_emp_poste"
        )

        if st.button("Ajouter cet employé", use_container_width=True):
            cleaned_new_code = new_emp_code.strip().upper()

            if not cleaned_new_code or not new_emp_name.strip():
                st.warning("Veuillez saisir au minimum le code et le nom.")
            elif custom_user_exists(cleaned_new_code):
                st.warning("Ce code existe déjà. Veuillez utiliser un autre code.")
            else:
                add_custom_employee(
                    code=cleaned_new_code,
                    name=new_emp_name,
                    poste=new_emp_poste,
                    faculty=user.get("faculty", ""),
                    institution=user.get("institution", "USJ"),
                    department="",
                    director_code=st.session_state["code"]
                )

                st.success(
                    f"Employé ajouté avec le code {cleaned_new_code}. "
                    "Il peut maintenant accéder à sa page avec ce code."
                )
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if director_read_only:
        st.info("Vos réponses ont été validées. Vous pouvez les consulter en lecture seule.")
    else:
        if st.button("Soumettre mes réponses", use_container_width=True):
            if len(leader_ranked) < 1:
                st.warning("Veuillez sélectionner au moins 1 thème pour vous-même.")
                return


            data = {
                "leader_ranked_themes": leader_ranked,
                "leader_selected_themes": leader_ranked,
                "leader_other_themes": leader_other,
                "employees_training_needs": employee_training_needs
            }

            save_response(user, data)
            st.success("Vos réponses ont été enregistrées avec succès.")
            st.rerun()

        if saved_data:
            if st.button("Valider définitivement mes réponses", use_container_width=True):
                validate_director_response(st.session_state["code"])
                st.success("Vos réponses ont été validées définitivement.")
                st.rerun()


def render_employee_visual_cards(employee_name, employee_code, employee_department, employee_ranked, director_ranked, final_themes, matched):
    def priority_card(css_class, rank_label, theme, badge=None):
        badge_html = ""
        if badge:
            badge_html = f"<div class='priority-badge'>{badge}</div>"

        return (
            f"<div class='priority-card {css_class}'>"
            f"<div class='priority-rank'>{rank_label}</div>"
            f"<div class='priority-theme'>{theme}</div>"
            f"{badge_html}"
            f"</div>"
        )

    employee_cards = "".join([
        priority_card("employee-card", f"Priorité {i}", theme)
        for i, theme in enumerate(employee_ranked, start=1)
    ])

    director_cards = "".join([
        priority_card("director-card", f"Priorité {i}", theme)
        for i, theme in enumerate(director_ranked, start=1)
    ])

    final_cards = "".join([
        priority_card(
            "final-card",
            f"Priorité finale {i}",
            theme,
            "Thème commun" if theme in matched else "Décision / complément"
        )
        for i, theme in enumerate(final_themes, start=1)
    ])

    if not employee_cards:
        employee_cards = "<div class='empty-choice'>Aucun choix employé.</div>"

    if not director_cards:
        director_cards = "<div class='empty-choice'>Aucun choix directeur.</div>"

    if not final_cards:
        final_cards = "<div class='empty-choice'>Aucun thème final.</div>"

    html = (
        "<section class='employee-print-page'>"
        "<div class='card blue-card employee-main-card'>"
        f"<h3 style='margin-top:0;'>{employee_name}</h3>"
        f"<span class='pill'>Code : {employee_code}</span>"
        "</div>"
        "<div class='card gold-card employee-summary-card'>"
        "<h3 style='margin-top:0; color:#001F5B;'>Synthèse visuelle</h3>"
        "<div style='color:#5D697A; font-weight:600;'>"
        "Comparaison des priorités classées par l’employé, par le Doyen / Directeur, puis sélection finale proposée."
        "</div>"
        "</div>"
        "<div class='employee-grid-print'>"
        "<div class='visual-column visual-employee'>"
        "<div class='visual-column-title'>Choix de l’employé</div>"
        f"{employee_cards}"
        "</div>"
        "<div class='visual-column visual-director'>"
        "<div class='visual-column-title'>Choix du Doyen / Directeur</div>"
        f"{director_cards}"
        "</div>"
        "<div class='visual-column visual-final'>"
        "<div class='visual-column-title'>Thèmes finaux proposés</div>"
        f"{final_cards}"
        "</div>"
        "</div>"
        "</section>"
    )

    st.markdown(html, unsafe_allow_html=True)


def build_admin_flat_exports(df, overrides):
    respondent_rows = []
    theme_rows = []
    final_rows = []

    for _, row in df.iterrows():
        respondent_rows.append({
            "Code": row["Code"],
            "Profil": row["Profil"],
            "Nom": row["Nom"],
            "Faculté": row["Faculté"],
            "Institution": row["Institution"],
            "Département": "",
            "Date": row["Date"]
        })

        data = row["Données"]

        if row["Profil"] == "psg":
            themes = data.get("ranked_themes", data.get("selected_themes", []))
            for i, theme in enumerate(themes, start=1):
                theme_rows.append({
                    "Code": row["Code"],
                    "Nom": row["Nom"],
                    "Profil": "PSG",
                    "Faculté": row["Faculté"],
                    "Département": "",
                    "Source": "Choix employé",
                    "Priorité": i,
                    "Thème": theme
                })

        elif row["Profil"] == "director":
            leader_themes = data.get("leader_ranked_themes", data.get("leader_selected_themes", []))
            for i, theme in enumerate(leader_themes, start=1):
                theme_rows.append({
                    "Code": row["Code"],
                    "Nom": row["Nom"],
                    "Profil": "Doyen / Directeur",
                    "Faculté": row["Faculté"],
                    "Département": "",
                    "Source": "Choix leader",
                    "Priorité": i,
                    "Thème": theme
                })

            for emp in data.get("employees_training_needs", []):
                director_themes = emp.get("ranked_themes_by_director", emp.get("selected_themes", []))
                for i, theme in enumerate(director_themes, start=1):
                    theme_rows.append({
                        "Code": emp.get("employee_code", ""),
                        "Nom": emp.get("employee_name", ""),
                        "Profil": "PSG",
                        "Faculté": row["Faculté"],
                        "Département": "",
                        "Source": "Choix directeur pour employé",
                        "Priorité": i,
                        "Thème": theme
                    })

    for code, user in get_all_users().items():
        if user.get("role") != "psg":
            continue

        employee_response = latest_by_code(df, code)
        director_code = user.get("director_code", "")
        director_response = latest_by_code(df, director_code)

        employee_original = []
        if employee_response:
            employee_original = employee_response["Données"].get(
                "ranked_themes",
                employee_response["Données"].get("selected_themes", [])
            )

        director_original = []
        if director_response:
            for item in director_response["Données"].get("employees_training_needs", []):
                if item.get("employee_code") == code:
                    director_original = item.get(
                        "ranked_themes_by_director",
                        item.get("selected_themes", [])
                    )

        employee_ranked = overrides.get(code, {}).get("employee_ranked", employee_original)
        director_ranked = overrides.get(code, {}).get("director_ranked", director_original)

        matched, final = calculate_final_themes(employee_ranked, director_ranked)

        for i, theme in enumerate(final, start=1):
            final_rows.append({
                "Employee code": code,
                "Employee name": user.get("name", ""),
                "Director code": director_code,
                "Faculty": user.get("faculty", ""),
                "Department": "",
                "Final priority": i,
                "Final theme": theme,
                "Decision type": "Thème commun" if theme in matched else "Décision / complément selon priorité"
            })

    return (
        pd.DataFrame(respondent_rows),
        pd.DataFrame(theme_rows),
        pd.DataFrame(final_rows)
    )

def build_theme_frequency_excel_report(df):
    detail_rows = []

    for _, row in df.iterrows():
        data = row["Données"]

        if row["Profil"] == "psg":
            themes = data.get("ranked_themes", data.get("selected_themes", []))

            for priority, theme in enumerate(themes, start=1):
                detail_rows.append({
                    "Thème": theme,
                    "Source": "Employé",
                    "Priorité": priority,
                    "Code répondant": row["Code"],
                    "Nom": row["Nom"],
                    "Profil": "PSG",
                    "Faculté": row["Faculté"],
                    "Institution": row["Institution"],
                    "Département": "",
                    "Date": row["Date"]
                })

        elif row["Profil"] == "director":
            leader_themes = data.get("leader_ranked_themes", data.get("leader_selected_themes", []))

            for priority, theme in enumerate(leader_themes, start=1):
                detail_rows.append({
                    "Thème": theme,
                    "Source": "Doyen / Directeur pour lui-même",
                    "Priorité": priority,
                    "Code répondant": row["Code"],
                    "Nom": row["Nom"],
                    "Profil": "Doyen / Directeur",
                    "Faculté": row["Faculté"],
                    "Institution": row["Institution"],
                    "Département": "",
                    "Date": row["Date"]
                })

            for emp in data.get("employees_training_needs", []):
                director_themes = emp.get("ranked_themes_by_director", emp.get("selected_themes", []))

                for priority, theme in enumerate(director_themes, start=1):
                    detail_rows.append({
                        "Thème": theme,
                        "Source": "Doyen / Directeur pour employé",
                        "Priorité": priority,
                        "Code répondant": emp.get("employee_code", ""),
                        "Nom": emp.get("employee_name", ""),
                        "Profil": "PSG évalué par Doyen / Directeur",
                        "Faculté": row["Faculté"],
                        "Institution": row["Institution"],
                        "Département": "",
                        "Date": row["Date"]
                    })

    details_df = pd.DataFrame(detail_rows)

    if details_df.empty:
        summary_df = pd.DataFrame(columns=[
            "Thème",
            "Sélections employés",
            "Sélections Doyens / Directeurs pour eux-mêmes",
            "Sélections Doyens / Directeurs pour employés",
            "Total sélections Doyens / Directeurs",
            "Total général"
        ])
    else:
        summary_df = (
            details_df
            .pivot_table(
                index="Thème",
                columns="Source",
                values="Code répondant",
                aggfunc="count",
                fill_value=0
            )
            .reset_index()
        )

        for col in [
            "Employé",
            "Doyen / Directeur pour lui-même",
            "Doyen / Directeur pour employé"
        ]:
            if col not in summary_df.columns:
                summary_df[col] = 0

        summary_df["Total sélections Doyens / Directeurs"] = (
            summary_df["Doyen / Directeur pour lui-même"]
            + summary_df["Doyen / Directeur pour employé"]
        )

        summary_df["Total général"] = (
            summary_df["Employé"]
            + summary_df["Total sélections Doyens / Directeurs"]
        )

        summary_df = summary_df.rename(columns={
            "Employé": "Sélections employés",
            "Doyen / Directeur pour lui-même": "Sélections Doyens / Directeurs pour eux-mêmes",
            "Doyen / Directeur pour employé": "Sélections Doyens / Directeurs pour employés"
        })

        summary_df = summary_df[
            [
                "Thème",
                "Sélections employés",
                "Sélections Doyens / Directeurs pour eux-mêmes",
                "Sélections Doyens / Directeurs pour employés",
                "Total sélections Doyens / Directeurs",
                "Total général"
            ]
        ].sort_values("Total général", ascending=False)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Synthèse par thème", index=False)
        details_df.to_excel(writer, sheet_name="Détails par thème", index=False)

        if not details_df.empty:
            for theme in sorted(details_df["Thème"].dropna().unique()):
                safe_sheet_name = (
                    theme[:31]
                    .replace("/", "-")
                    .replace("\\", "-")
                    .replace("*", "")
                    .replace("?", "")
                    .replace(":", "")
                    .replace("[", "")
                    .replace("]", "")
                )

                theme_df = details_df[details_df["Thème"] == theme].copy()
                theme_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)

    output.seek(0)
    return output
    
def build_theme_frequency_dataframe(df):
    rows = []

    for _, row in df.iterrows():
        data = row["Données"]

        if row["Profil"] == "psg":
            themes = data.get("ranked_themes", data.get("selected_themes", []))

            for priority, theme in enumerate(themes, start=1):
                rows.append({
                    "Thème": theme,
                    "Source": "Employés",
                    "Priorité": priority,
                    "Nom": row["Nom"],
                    "Faculté": row["Faculté"],
                    "Département": ""
                })

        elif row["Profil"] == "director":
            leader_themes = data.get("leader_ranked_themes", data.get("leader_selected_themes", []))

            for priority, theme in enumerate(leader_themes, start=1):
                rows.append({
                    "Thème": theme,
                    "Source": "Doyens / Directeurs",
                    "Priorité": priority,
                    "Nom": row["Nom"],
                    "Faculté": row["Faculté"],
                    "Département": ""
                })

            for emp in data.get("employees_training_needs", []):
                director_themes = emp.get(
                    "ranked_themes_by_director",
                    emp.get("selected_themes", [])
                )

                for priority, theme in enumerate(director_themes, start=1):
                    rows.append({
                        "Thème": theme,
                        "Source": "Doyens / Directeurs pour employés",
                        "Priorité": priority,
                        "Nom": emp.get("employee_name", ""),
                        "Faculté": row["Faculté"],
                        "Département": ""
                    })

    return pd.DataFrame(rows)


def render_theme_visualization_dashboard(df):
    st.markdown("### Visualisation générale des thèmes")

    if st.button(
        "Générer les figures des thèmes sélectionnés",
        use_container_width=True,
        key="generate_theme_visuals_main"
    ):
        st.session_state["show_theme_visuals"] = True

    if not st.session_state.get("show_theme_visuals", False):
        return

    theme_visual_df = build_theme_frequency_dataframe(df)

    if theme_visual_df.empty:
        st.info("Aucune donnée disponible pour générer les figures.")
        return

    employee_related_df = theme_visual_df[
        theme_visual_df["Source"].isin([
            "Employés",
            "Doyens / Directeurs pour employés"
        ])
    ]

    employee_related_counts = (
        employee_related_df
        .groupby(["Thème", "Source"])
        .size()
        .reset_index(name="Fréquence")
    )

    st.markdown("#### 1. Thèmes liés aux employés")

    if employee_related_counts.empty:
        st.info("Aucune donnée disponible pour les thèmes liés aux employés.")
    else:
        fig_employee_related = px.bar(
            employee_related_counts,
            x="Fréquence",
            y="Thème",
            color="Source",
            orientation="h",
            barmode="group",
            text="Fréquence",
            title="Thèmes liés aux employés : choix des employés et choix des Doyens / Directeurs"
        )

        fig_employee_related.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        fig_employee_related.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=850,
            margin=dict(l=260, r=80, t=70, b=40),
            legend_title_text="Source"
        )

        st.plotly_chart(fig_employee_related, use_container_width=True)

    director_only_df = theme_visual_df[
        theme_visual_df["Source"] == "Doyens / Directeurs"
    ]

    director_only_counts = (
        director_only_df
        .groupby("Thème")
        .size()
        .reset_index(name="Fréquence")
        .sort_values("Fréquence", ascending=False)
    )

    st.markdown("#### 2. Thèmes liés uniquement aux Doyens / Directeurs")

    if director_only_counts.empty:
        st.info("Aucune donnée disponible pour les thèmes liés aux Doyens / Directeurs.")
    else:
        fig_director_only = px.bar(
            director_only_counts,
            x="Fréquence",
            y="Thème",
            orientation="h",
            text="Fréquence",
            title="Thèmes sélectionnés par les Doyens / Directeurs pour eux-mêmes"
        )

        fig_director_only.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        fig_director_only.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=600,
            margin=dict(l=260, r=80, t=70, b=40),
            showlegend=False
        )

        st.plotly_chart(fig_director_only, use_container_width=True)

    report_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Visualisation des thèmes TNA 2026/2027</title>
    </head>
    <body>
        <h1>Visualisation générale des thèmes sélectionnés - TNA 2026/2027</h1>
        <h2>1. Thèmes liés aux employés</h2>
        {fig_employee_related.to_html(full_html=False, include_plotlyjs="cdn") if not employee_related_counts.empty else "<p>Aucune donnée.</p>"}
        <br><br>
        <h2>2. Thèmes liés uniquement aux Doyens / Directeurs</h2>
        {fig_director_only.to_html(full_html=False, include_plotlyjs=False) if not director_only_counts.empty else "<p>Aucune donnée.</p>"}
    </body>
    </html>
    """

    d1, d2 = st.columns(2)

    with d1:
        st.download_button(
            "Télécharger la visualisation HTML",
            data=report_html.encode("utf-8"),
            file_name="tna_visualisation_themes.html",
            mime="text/html",
            use_container_width=True
        )

    with d2:
        st.download_button(
            "Télécharger les données de visualisation CSV",
            theme_visual_df.to_csv(index=False).encode("utf-8-sig"),
            "tna_visualisation_themes.csv",
            "text/csv",
            use_container_width=True
        )



def build_director_report_html(selected_director, df, overrides):
    all_users = get_all_users()
    director_user = all_users[selected_director]
    director_response = latest_by_code(df, selected_director)
    employees = get_employees_for_director(selected_director)

    leader_themes = []
    if director_response:
        leader_themes = director_response["Données"].get(
            "leader_ranked_themes",
            director_response["Données"].get("leader_selected_themes", [])
        )

    director_emp_map = {}
    if director_response:
        for item in director_response["Données"].get("employees_training_needs", []):
            director_emp_map[item.get("employee_code")] = item

    rows_html = ""

    for emp in employees:
        emp_response = latest_by_code(df, emp["code"])

        employee_original = []
        if emp_response:
            employee_original = emp_response["Données"].get(
                "ranked_themes",
                emp_response["Données"].get("selected_themes", [])
            )

        director_original = []
        if emp["code"] in director_emp_map:
            director_original = director_emp_map[emp["code"]].get(
                "ranked_themes_by_director",
                director_emp_map[emp["code"]].get("selected_themes", [])
            )

        employee_ranked = overrides.get(emp["code"], {}).get("employee_ranked", employee_original)
        director_ranked = overrides.get(emp["code"], {}).get("director_ranked", director_original)

        matched, final = calculate_final_themes(employee_ranked, director_ranked)

        employee_list = "".join([f"<li><b>P{i}</b> - {theme}</li>" for i, theme in enumerate(employee_ranked, start=1)])
        director_list = "".join([f"<li><b>P{i}</b> - {theme}</li>" for i, theme in enumerate(director_ranked, start=1)])
        final_list = "".join([
            f"<li><b>P{i}</b> - {theme} <span>{'Thème commun' if theme in matched else 'Décision / complément'}</span></li>"
            for i, theme in enumerate(final, start=1)
        ])

        rows_html += f"""
        <section class="employee-card">
            <h2>{emp['name']}</h2>
            <p class="meta">Code : {emp['code']}</p>
            <div class="three-cols">
                <div class="box employee">
                    <h3>Choix de l’employé</h3>
                    <ol>{employee_list}</ol>
                </div>
                <div class="box director">
                    <h3>Choix du Doyen / Directeur</h3>
                    <ol>{director_list}</ol>
                </div>
                <div class="box final">
                    <h3>Thèmes finaux proposés</h3>
                    <ol>{final_list}</ol>
                </div>
            </div>
        </section>
        """

    leader_html = "".join([f"<li><b>P{i}</b> - {theme}</li>" for i, theme in enumerate(leader_themes, start=1)])

    cfp_logo = image_to_base64(CFP_LOGO_PATH)
    usj_logo = image_to_base64(USJ_LOGO_PATH)

    cfp_logo_src = f"data:image/png;base64,{cfp_logo}" if cfp_logo else ""
    usj_logo_src = f"data:image/png;base64,{usj_logo}" if usj_logo else ""

    director_affiliation = director_user.get("institution", director_user.get("faculty", ""))

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Rapport TNA 2026 - {director_user['name']}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                color: #1B2A41;
                background: #ffffff;
                margin: 28px;
            }}

            .report-logo-header {{
                background: #ffffff;
                border: 1px solid #DDE5F0;
                border-radius: 18px;
                padding: 14px 22px;
                margin-bottom: 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}

            .report-logo {{
                max-height: 70px;
                max-width: 170px;
            }}

            .report-center {{
                text-align: center;
                color: #001F5B;
            }}

            .report-center-title {{
                font-size: 26px;
                font-weight: 500;
            }}

            .report-center-subtitle {{
                font-size: 16px;
                color: #5D697A;
                font-weight: 600;
            }}

            .header {{
                border-bottom: 4px solid #001F5B;
                padding-bottom: 16px;
                margin-bottom: 24px;
            }}
            .kicker {{
                color: #8B1538;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 12px;
            }}
            h1 {{
                color: #001F5B;
                margin: 8px 0 6px 0;
                font-size: 28px;
            }}
            h2 {{
                color: #001F5B;
                margin-bottom: 6px;
            }}
            h3 {{
                color: #001F5B;
                margin-top: 0;
            }}
            .meta {{
                color: #5D697A;
                font-weight: 600;
            }}
            .leader {{
                background: #F8EDEF;
                border-left: 6px solid #8B1538;
                border-radius: 12px;
                padding: 14px 18px;
                margin-bottom: 22px;
            }}
            .employee-card {{
                page-break-before: always;
                page-break-inside: avoid;
                break-before: page;
                break-inside: avoid;
                border: 1px solid #DDE5F0;
                border-radius: 14px;
                padding: 16px;
                margin-bottom: 18px;
                box-sizing: border-box;
            }}
            .employee-card:first-of-type {{
                page-break-before: auto;
                break-before: auto;
            }}
            .three-cols {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 14px;
            }}
            .box {{
                border-radius: 12px;
                padding: 12px;
                min-height: 120px;
            }}
            .employee {{
                background: #EAF2F8;
                border-left: 5px solid #001F5B;
            }}
            .director {{
                background: #F8EDEF;
                border-left: 5px solid #8B1538;
            }}
            .final {{
                background: #FFF8DF;
                border-left: 5px solid #C9A227;
            }}
            li {{
                margin-bottom: 8px;
                line-height: 1.35;
            }}
            span {{
                display: inline-block;
                margin-left: 6px;
                font-size: 11px;
                background: #ffffff;
                border: 1px solid #C9A227;
                border-radius: 999px;
                padding: 3px 7px;
                color: #735C00;
                font-weight: 700;
            }}

            .print-btn {{
                width: 100%;
                background: #001F5B;
                color: white;
                border: 0;
                border-radius: 12px;
                padding: 14px;
                font-size: 14px;
                cursor: pointer;
                margin-bottom: 20px;
                box-shadow: 0 6px 16px rgba(0,31,91,0.16);
            }}

            @media print {{
                body {{
                    margin: 14mm;
                }}

                .print-btn {{
                    display: none;
                }}

                .employee-card {{
                    page-break-before: always;
                    break-before: page;
                    page-break-inside: avoid;
                    break-inside: avoid;
                    min-height: 90vh;
                }}
                .employee-card:first-of-type {{
                    page-break-before: auto;
                    break-before: auto;
                }}
            }}
        </style>
    </head>

    <body>

        <button class="print-btn" onclick="window.print()">
            Enregistrer en PDF
        </button>

        <div class="report-logo-header">
            <img src="{cfp_logo_src}" class="report-logo">
            <div class="report-center">
                <div class="report-center-title">Centre de Formation Professionnelle</div>
                <div class="report-center-subtitle">Training Needs Assessment - TNA 2026</div>
            </div>
            <img src="{usj_logo_src}" class="report-logo">
        </div>

        <div class="header">
            <div class="kicker">Training Needs Assessment - TNA 2026</div>
            <h1>Rapport par Doyen / Directeur</h1>
            <p class="meta">{director_user['name']} | {director_affiliation}</p>
            <p class="meta">Date de génération : {datetime.now().strftime("%Y-%m-%d")}</p>
        </div>

        <section class="leader">
            <h2>Besoins de formation sélectionnés pour le leader</h2>
            <ol>{leader_html}</ol>
        </section>

        {rows_html}
    </body>
    </html>
    """

    return html



def render_save_pdf_button():
    components.html(
        """
        <style>
            html, body {
                margin: 0;
                padding: 0;
                background: transparent;
                font-family: inherit;
            }
            .pdf-button {
                width: 100%;
                min-height: 50px;
                background: #001F5B;
                color: #ffffff;
                border: 0;
                border-radius: 12px;
                padding: 13px 18px;
                font-weight: 400;
                font-size: 14px;
                line-height: 50px;
                cursor: pointer;
                box-shadow: 0 6px 16px rgba(0,31,91,0.16);
                display: block;
                text-align: center;
                padding: 0;
                box-sizing: border-box;
            }
            .pdf-button:hover {
                background: #123E7C;
            }
        
    @media print {{
        .no-print,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr {{
            display: none !important;
        }}

        .platform-header {{
            display: flex !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 92vh !important;
            box-sizing: border-box !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print,
        .visual-column,
        .priority-card,
        .card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}
    }}

    
    /* FINAL PRINT FIX */
    @media print {{
        .no-print,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr {{
            display: none !important;
        }}

        .platform-header {{
            display: flex !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .main-hero {{
            display: block !important;
            box-shadow: none !important;
            margin-bottom: 12px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        body,
        .stApp {{
            background: white !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 90vh !important;
            box-sizing: border-box !important;
            padding-top: 8px !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print {{
            display: grid !important;
            grid-template-columns: 1fr 1fr 1fr !important;
            gap: 12px !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }}

        .visual-column,
        .priority-card,
        .card,
        .employee-main-card,
        .employee-summary-card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            box-shadow: none !important;
        }}

        h1, h2, h3 {{
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}
    }}

    
    /* FINAL PDF PRINT HEADER FIX */
    @media print {{
        .platform-header {{
            display: flex !important;
            visibility: visible !important;
            box-shadow: none !important;
            border: 1px solid #DDE5F0 !important;
            border-radius: 12px !important;
            margin-bottom: 16px !important;
            padding: 12px 18px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .platform-logo {{
            display: block !important;
            visibility: visible !important;
            max-height: 68px !important;
            max-width: 145px !important;
        }}

        .header-title,
        .header-subtitle {{
            display: block !important;
            visibility: visible !important;
        }}

        .no-print,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDownloadButton"],
        iframe,
        button,
        .admin-action-button,
        div[data-testid="stExpander"],
        [data-testid="stMetric"],
        hr,
        label,
        div[data-baseweb="select"],
        .stSelectbox {{
            display: none !important;
            visibility: hidden !important;
        }}

        .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        body,
        .stApp {{
            background: white !important;
        }}

        .main-hero {{
            box-shadow: none !important;
            margin-bottom: 14px !important;
            page-break-after: avoid !important;
            break-after: avoid !important;
        }}

        .employee-print-page {{
            page-break-before: always !important;
            break-before: page !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            min-height: 90vh !important;
            box-sizing: border-box !important;
        }}

        .employee-print-page:first-of-type {{
            page-break-before: auto !important;
            break-before: auto !important;
        }}

        .employee-grid-print,
        .visual-column,
        .priority-card,
        .card,
        .employee-main-card,
        .employee-summary-card {{
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            box-shadow: none !important;
        }}
    }}

    </style>
        <button class="pdf-button" onclick="window.parent.print();">
            Enregistrer le rapport en PDF
        </button>
        """,
        height=64
    )


def render_admin_dashboard():
    st.markdown("""
    <div class="main-hero">
        <div class="hero-kicker">Administration | TNA 2026</div>
        <div class="hero-title">Tableau de bord administrateur</div>
        <div class="hero-subtitle">Vue interactive des besoins de formation avec comparaison employé-directeur et modification administrative des priorités.</div>
    </div>
    """, unsafe_allow_html=True)

    df = load_responses()
    overrides = load_admin_theme_overrides()
    all_users = get_all_users()

    valid_user_codes = {
        str(code).strip().upper()
        for code, user in all_users.items()
        if user.get("role") in ["psg", "director"]
    }

    if not df.empty:
        df = df[df["Code"].astype(str).str.upper().isin(valid_user_codes)].copy()

    with st.sidebar:
        st.header("Filtres administrateur")


    if st.button("Réinitialiser les réponses", use_container_width=True):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM responses")
        c.execute("DELETE FROM admin_theme_overrides")
        c.execute("DELETE FROM employee_validations")
        c.execute("DELETE FROM director_validations")
        conn.commit()
        conn.close()
        st.success("Les réponses ont été réinitialisées.")
        st.rerun()

    with st.expander("Supprimer une réponse soumise", expanded=False):
        submitted_answers = load_submitted_answers_for_admin()

        if not submitted_answers:
            st.info("Aucune réponse soumise à supprimer.")
        else:
            selected_answer = st.selectbox(
                "Sélectionner la réponse à supprimer",
                submitted_answers,
                format_func=lambda x: (
                    f"{x['submitted_at']} | "
                    f"{'PSG' if x['role'] == 'psg' else 'Doyen / Directeur'} | "
                    f"{x['name']} | {x['code']}"
                ),
                key="admin_delete_submitted_answer_selector"
            )

            delete_all_for_user = st.checkbox(
                "Supprimer toutes les réponses de ce répondant",
                value=False,
                key="admin_delete_all_answers_for_user"
            )

            st.warning(
                "Cette action supprimera la réponse sélectionnée de la base. "
                "Si aucune autre réponse ne reste pour ce répondant, sa validation sera aussi retirée "
                "afin qu’il puisse soumettre à nouveau."
            )

            confirm_delete = st.text_input(
                "Pour confirmer, écrivez SUPPRIMER",
                key="admin_confirm_delete_submitted_answer"
            )

            if st.button(
                "Supprimer la réponse sélectionnée",
                use_container_width=True,
                key="admin_delete_submitted_answer_button"
            ):
                if confirm_delete.strip().upper() != "SUPPRIMER":
                    st.warning("Veuillez écrire SUPPRIMER pour confirmer.")
                else:
                    delete_submitted_answer(
                        response_id=selected_answer["id"],
                        respondent_code=selected_answer["code"],
                        role=selected_answer["role"],
                        delete_all_for_user=delete_all_for_user
                    )

                    st.success("La réponse sélectionnée a été supprimée.")
                    st.rerun()

    view = "Synthèse directeur-employés"


    filtered = df.copy()


    total_psg_users = len([
        code for code, user in all_users.items()
        if user.get("role") == "psg"
    ])

    total_director_users = len([
        code for code, user in all_users.items()
        if user.get("role") == "director"
    ])

    unique_respondents = 0 if filtered.empty else filtered["Code"].nunique()
    unique_psg_responses = 0 if filtered.empty else filtered[filtered["Profil"] == "psg"]["Code"].nunique()
    unique_director_responses = 0 if filtered.empty else filtered[filtered["Profil"] == "director"]["Code"].nunique()

    valid_user_codes = set(DEMO_USERS.keys())
    
    if filtered.empty or "Code" not in filtered.columns:
        filtered_valid = pd.DataFrame(columns=["Code", "Profil"])
    else:
        filtered_valid = filtered[filtered["Code"].isin(valid_user_codes)]
    
    total_psg_users = len([
        code for code, user in DEMO_USERS.items()
        if user.get("role") == "psg"
    ])
    
    total_director_users = len([
        code for code, user in DEMO_USERS.items()
        if user.get("role") == "director"
    ])
    
    unique_psg_responses = filtered_valid[
        filtered_valid["Profil"] == "psg"
    ]["Code"].nunique()
    
    unique_director_responses = filtered_valid[
        filtered_valid["Profil"] == "director"
    ]["Code"].nunique()
    
    unique_respondents = unique_psg_responses + unique_director_responses
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Répondants uniques", unique_respondents)
    k2.metric("PSG", f"{unique_psg_responses} / {total_psg_users}")
    k3.metric("Doyens / Directeurs", f"{unique_director_responses} / {total_director_users}")

    if df.empty:
        st.info("Aucune réponse enregistrée pour le moment.")
        return

    st.divider()

    respondents_export, themes_export, final_export = build_admin_flat_exports(df, overrides)
    theme_frequency_excel = build_theme_frequency_excel_report(df)

    with st.expander("Exports administrateur", expanded=False):
        ex1, ex2, ex3, ex4 = st.columns(4)

        with ex1:
            st.download_button(
                "Télécharger les répondants CSV",
                respondents_export.to_csv(index=False).encode("utf-8-sig"),
                "tna_repondants.csv",
                "text/csv",
                use_container_width=True
            )

        with ex2:
            st.download_button(
                "Télécharger les thèmes CSV",
                themes_export.to_csv(index=False).encode("utf-8-sig"),
                "tna_themes_selectionnes.csv",
                "text/csv",
                use_container_width=True
            )

        with ex3:
            st.download_button(
                "Télécharger les thèmes finaux CSV",
                final_export.to_csv(index=False).encode("utf-8-sig"),
                "tna_themes_finaux.csv",
                "text/csv",
                use_container_width=True
            )

        with ex4:
            st.download_button(
                "Rapport Excel par thème",
                data=theme_frequency_excel,
                file_name="tna_rapport_frequence_par_theme.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    render_theme_visualization_dashboard(df)

    if view == "Visualisation des thèmes":
        return

    st.divider()

    directors = [
        code for code, user in all_users.items()
        if user.get("role") == "director"
    ]

    director_labels = {
        code: f"{all_users[code]['name']} | {all_users[code].get('institution', all_users[code].get('faculty', ''))}"
        for code in directors
    }

    if view in ["Synthèse directeur-employés", "Modifier les priorités"]:
        selected_director = st.selectbox(
            "Sélectionner un Doyen / Directeur",
            directors,
            format_func=lambda x: director_labels[x],
            key=f"admin_director_selector_{view}"
        )

        director_user = all_users[selected_director]
        director_response = latest_by_code(df, selected_director)

        report_html = build_director_report_html(selected_director, df, overrides)
        safe_report_html = json.dumps(report_html)

        components.html(
            f"""
            <button onclick="openReport()" style="
                width:100%;
                min-height:50px;
                background:#001F5B;
                color:white;
                border:0;
                border-radius:12px;
                font-size:14px;
                font-weight:400;
                cursor:pointer;
                box-shadow:0 6px 16px rgba(0,31,91,0.16);
            ">
                Ouvrir le rapport du directeur
            </button>

            <script>
            function openReport() {{
                const html = {safe_report_html};
                const win = window.open("", "_blank");
                win.document.open();
                win.document.write(html);
                win.document.close();
            }}
            </script>
            """,
            height=64
        )

        st.markdown("### 1. Besoins sélectionnés par le Doyen / Directeur pour lui-même")

        st.markdown(f"""
        <div class='card red-card'>
            <h3 style='margin-top:0;'>{director_user['name']}</h3>
            <span class='pill pill-red'>{director_user.get('institution', director_user.get('faculty', ''))}</span>
        </div>
        """, unsafe_allow_html=True)

        if director_response:
            leader_themes = director_response["Données"].get(
                "leader_ranked_themes",
                director_response["Données"].get("leader_selected_themes", [])
            )
            render_theme_pills(leader_themes, "pill pill-red")
        else:
            st.warning("Ce directeur n’a pas encore soumis ses réponses.")

        st.divider()

        employees = get_employees_for_director(selected_director)

        director_emp_map = {}

        if director_response:
            for item in director_response["Données"].get("employees_training_needs", []):
                director_emp_map[item.get("employee_code")] = item

        if view == "Modifier les priorités":
            st.markdown("### Modification administrative des priorités par employé")
            st.info(
                "L’administrateur peut modifier les thèmes classés par l’employé "
                "et les thèmes classés par le Doyen / Directeur. Ces modifications sont enregistrées "
                "dans une table administrative séparée."
            )
        else:
            st.markdown("### 2. Analyse visuelle par employé")

        for emp in employees:
            emp_response = latest_by_code(df, emp["code"])

            employee_original = []

            if emp_response:
                employee_original = emp_response["Données"].get(
                    "ranked_themes",
                    emp_response["Données"].get("selected_themes", [])
                )

            director_original = []

            if emp["code"] in director_emp_map:
                director_original = director_emp_map[emp["code"]].get(
                    "ranked_themes_by_director",
                    director_emp_map[emp["code"]].get("selected_themes", [])
                )

            employee_ranked = overrides.get(emp["code"], {}).get("employee_ranked", employee_original)
            director_ranked = overrides.get(emp["code"], {}).get("director_ranked", director_original)

            matched, final = calculate_final_themes(employee_ranked, director_ranked)

            if emp["code"] in overrides:
                st.caption(f"Priorités modifiées par l’administrateur le {overrides[emp['code']]['updated_at']}.")

            if view == "Modifier les priorités":
                c1, c2 = st.columns(2)

                with c1:
                    admin_employee_ranked = ranked_select_with_defaults(
                        "Modifier le classement de l’employé",
                        PSG_THEMES,
                        f"admin_edit_employee_{emp['code']}",
                        employee_ranked
                    )

                with c2:
                    admin_director_ranked = ranked_select_with_defaults(
                        "Modifier le classement du Doyen / Directeur",
                        PSG_THEMES,
                        f"admin_edit_director_{emp['code']}",
                        director_ranked
                    )

                if st.button(
                    f"Enregistrer les priorités modifiées pour {emp['name']}",
                    key=f"save_override_{emp['code']}",
                    use_container_width=True
                ):
                    if len(admin_employee_ranked) > 3 or len(admin_director_ranked) > 3:
                        st.warning("Veuillez sélectionner au maximum 3 thèmes pour chaque classement.")
                    else:
                        save_admin_theme_override(emp["code"], admin_employee_ranked, admin_director_ranked)
                        st.success(f"Priorités modifiées pour {emp['name']}.")
                        st.rerun()

                st.divider()

            else:
                render_employee_visual_cards(
                    emp["name"],
                    emp["code"],
                    "",
                    employee_ranked,
                    director_ranked,
                    final,
                    matched
                )
                st.divider()

    elif view == "Réponses PSG":
        st.markdown("### Réponses PSG")

        psg_df = filtered[filtered["Profil"] == "psg"].copy()

        if psg_df.empty:
            st.info("Aucune réponse PSG dans les filtres sélectionnés.")
        else:
            for _, row in psg_df.iterrows():
                themes = row["Données"].get("ranked_themes", row["Données"].get("selected_themes", []))

                st.markdown(f"""
                <div class='card blue-card'>
                    <b>{row['Nom']}</b><br>
                    {row['Faculté']} | {row['Date']}
                </div>
                """, unsafe_allow_html=True)

                render_theme_pills(themes, "pill")

    elif view == "Réponses Doyens / Directeurs":
        st.markdown("### Réponses Doyens / Directeurs")

        dd_df = filtered[filtered["Profil"] == "director"].copy()

        if dd_df.empty:
            st.info("Aucune réponse Doyen / Directeur dans les filtres sélectionnés.")
        else:
            for _, row in dd_df.iterrows():
                data = row["Données"]

                st.markdown(f"""
                <div class='card red-card'>
                    <b>{row['Nom']}</b><br>
                    {row['Faculté']} | {row['Date']}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("**Thèmes sélectionnés pour lui-même :**")
                render_theme_pills(
                    data.get("leader_ranked_themes", data.get("leader_selected_themes", [])),
                    "pill pill-red"
                )

                st.markdown("**Thèmes sélectionnés pour les employés :**")

                for emp in data.get("employees_training_needs", []):
                    st.markdown(f"""
                    <div class='card'>
                        <b>{emp.get('employee_name')}</b>
                    </div>
                    """, unsafe_allow_html=True)

                    render_theme_pills(
                        emp.get("ranked_themes_by_director", emp.get("selected_themes", [])),
                        "pill"
                    )

    elif view == "Base de données":
        st.markdown("### Base de données filtrée")

        display_df = filtered.drop(columns=["Données"]) if not filtered.empty else pd.DataFrame()

        if "Département" in display_df.columns:
            display_df = display_df.drop(columns=["Département"])

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Télécharger CSV",
            display_df.to_csv(index=False).encode("utf-8-sig"),
            "tna_reponses.csv",
            "text/csv"
        )



def main():
    st.set_page_config(
        page_title="TNA 2026",
        page_icon="📘",
        layout="wide"
    )

    apply_style()
    init_db()
    render_platform_header()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
        return

    user = st.session_state["user"]

    if user["role"] != "admin":
        st.markdown(
            """
            <style>
            section[data-testid="stSidebar"] {
                display: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    if user["role"] == "psg":
        render_psg_form(user)

    elif user["role"] == "director":
        render_director_form(user)

    elif user["role"] == "admin":
        render_admin_dashboard()


if __name__ == "__main__":
    main()


