"""
theme_pays.py — Habillage de la page selon la DESTINATION et le TYPE de projet.

Principe : chaque pays a un theme (palette, nom du portail officiel, titres par
type de projet) qui EVOQUE les codes de son portail gouvernemental — sans en
copier la marque. Le registre est le jumeau de app/api/sources : ajouter un
pays = ajouter un dict, rien d'autre.

Usage (une ligne dans ui.py, juste avant l'affichage des opportunites) :

    import theme_pays
    theme_pays.appliquer(destination, type_c, tr)

Ce que ca fait :
  1. Injecte un CSS global "cabinet / grande universite" : conteneur centre,
     beaucoup de blanc, hierarchie typographique nette, cartes (expanders)
     avec liseré couleur du pays, boutons a l'accent du pays.
  2. Affiche un BANDEAU HERO officiel : drapeau, "Travailler au Canada" /
     "Etudier en Allemagne", sous-titre citant la source des donnees
     (Guichet-Emplois, Make it in Germany...).

Limite assumee : Streamlit ne garantit pas ses classes CSS entre versions.
On cible les selecteurs stables (data-testid). Si un futur Streamlit casse un
style, la page reste fonctionnelle — juste moins habillee.
"""

from __future__ import annotations

import html

try:
    import streamlit as st
except ImportError:          # tests hors Streamlit
    st = None

# --------------------------------------------------------------------------- #
# Registre des themes.
# `titres` : libelles FR par type de projet — passes dans tr(), donc
# traduisibles en ajoutant les cles dans i18n.py.
# --------------------------------------------------------------------------- #
THEMES: dict[str, dict] = {
    "CA": {
        "drapeau": "🇨🇦",
        "nom_fr": "Canada",
        # Codes visuels du domaine canada.ca / Guichet-Emplois
        "primaire": "#26374A",     # bleu institutionnel
        "accent":   "#AF3C43",     # rouge officiel
        "hero_fond": "linear-gradient(120deg,#26374A 0%,#2f4a63 100%)",
        "hero_texte": "#ffffff",
        "portail": "Guichet-Emplois · Gouvernement du Canada",
        "titres": {
            "etudes": "Étudier au Canada",
            "stage":  "Faire un stage au Canada",
            "emploi": "Travailler au Canada",
            "metier": "Métiers spécialisés au Canada",
        },
        "sous_titre": "Offres ouvertes aux candidats internationaux — "
                      "données du portail officiel, mises à jour en continu.",
    },
    "DE": {
        "drapeau": "🇩🇪",
        "nom_fr": "Allemagne",
        # Codes visuels de make-it-in-germany.com (petrole / teal federal)
        "primaire": "#005c66",
        "accent":   "#d4a017",
        "hero_fond": "linear-gradient(120deg,#004a52 0%,#00707c 100%)",
        "hero_texte": "#ffffff",
        "portail": "Make it in Germany · portail fédéral allemand",
        "titres": {
            "etudes": "Étudier en Allemagne",
            "stage":  "Faire un stage en Allemagne",
            "emploi": "Travailler en Allemagne",
            "metier": "Métiers qualifiés en Allemagne",
        },
        "sous_titre": "Employeurs ayant choisi de recruter à l'international — "
                      "issus du portail fédéral pour les professionnels étrangers.",
    },
    "FR": {
        "drapeau": "🇫🇷",
        "nom_fr": "France",
        "primaire": "#000091",     # bleu Marianne (design de l'Etat)
        "accent":   "#e1000f",
        "hero_fond": "linear-gradient(120deg,#000091 0%,#2323b6 100%)",
        "hero_texte": "#ffffff",
        "portail": "Campus France · France Travail",
        "titres": {
            "etudes": "Étudier en France",
            "stage":  "Faire un stage en France",
            "emploi": "Travailler en France",
            "metier": "Métiers en tension en France",
        },
        "sous_titre": "Procédures officielles et opportunités — "
                      "style des services publics français.",
    },
    "US": {
        "drapeau": "🇺🇸",
        "nom_fr": "États-Unis",
        "primaire": "#112e51",
        "accent":   "#b31942",
        "hero_fond": "linear-gradient(120deg,#112e51 0%,#1a4480 100%)",
        "hero_texte": "#ffffff",
        "portail": "EducationUSA · U.S. Department of State",
        "titres": {
            "etudes": "Étudier aux États-Unis",
            "stage":  "Faire un stage aux États-Unis",
            "emploi": "Travailler aux États-Unis",
            "metier": "Métiers spécialisés aux États-Unis",
        },
        "sous_titre": "Visas F-1, OPT et parcours officiels — repères fiables.",
    },
    "GB": {                                    # patch_uk_v1
        "primaire": "#1d70b8",                 # bleu GOV.UK
        "fonce":    "#0b0c0c",
        "degrade":  "linear-gradient(120deg,#0b0c0c 0%,#1d70b8 100%)",
    },
    "_defaut": {
        "drapeau": "🌍",
        "nom_fr": "",
        "primaire": "#1f3a5f",
        "accent":   "#c8553d",
        "hero_fond": "linear-gradient(120deg,#1f3a5f 0%,#2e527f 100%)",
        "hero_texte": "#ffffff",
        "portail": "Yorbity — sources officielles",
        "titres": {
            "etudes": "Étudier à l'étranger",
            "stage":  "Faire un stage à l'étranger",
            "emploi": "Travailler à l'étranger",
            "metier": "Métiers spécialisés à l'international",
        },
        "sous_titre": "Ta trajectoire vers le monde — données de portails officiels.",
    },
}

# Types dont le hero prend l'allure "job board" (bande compteur) plutot
# que "brochure universitaire".
TYPES_JOB_BOARD = ("stage", "emploi", "metier")


def theme(dest_code: str | None) -> dict:
    return THEMES.get((dest_code or "").upper(), THEMES["_defaut"])


# --------------------------------------------------------------------------- #
# CSS global — "grande universite / cabinet de conseil"
# --------------------------------------------------------------------------- #
def css(dest_code: str | None) -> str:
    t = theme(dest_code)
    p, a = t["primaire"], t["accent"]
    return f"""
<style>
/* -- Mise en page : contenu centre, respiration ------------------------- */
.block-container {{
    max-width: 1080px;
    padding-top: 1.2rem;
}}

/* -- Hierarchie typographique ------------------------------------------- */
h1, h2, h3 {{
    color: {p};
    letter-spacing: -0.01em;
}}
h4 {{
    color: {p};
    text-transform: uppercase;
    font-size: 0.92rem;
    letter-spacing: 0.08em;
    border-bottom: 2px solid {a};
    padding-bottom: 0.35rem;
    margin-top: 2.2rem;
}}

/* -- Cartes d'offres (expanders) ----------------------------------------- */
div[data-testid="stExpander"] {{
    border: 1px solid #e5e8ee;
    border-left: 4px solid {p};
    border-radius: 10px;
    box-shadow: 0 1px 4px rgba(20,30,50,.06);
    margin-bottom: 0.6rem;
    background: #ffffff;
}}
div[data-testid="stExpander"]:hover {{
    box-shadow: 0 3px 10px rgba(20,30,50,.10);
    border-left-color: {a};
}}

/* -- Boutons -------------------------------------------------------------- */
.stButton > button, .stLinkButton > a {{
    border-radius: 8px;
    border: 1px solid {p};
    color: {p};
    font-weight: 600;
}}
.stButton > button:hover, .stLinkButton > a:hover {{
    border-color: {a};
    color: {a};
}}

/* -- Bandeau hero ---------------------------------------------------------- */
.yb-hero {{
    background: {t["hero_fond"]};
    color: {t["hero_texte"]};
    border-radius: 14px;
    padding: 1.6rem 2rem 1.4rem 2rem;
    margin: 0.4rem 0 1.6rem 0;
}}
.yb-hero .yb-portail {{
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    opacity: 0.85;
    margin-bottom: 0.4rem;
}}
.yb-hero h2 {{
    color: {t["hero_texte"]};
    margin: 0 0 0.3rem 0;
    font-size: 1.9rem;
}}
.yb-hero .yb-sous {{
    opacity: 0.92;
    font-size: 0.98rem;
    max-width: 46rem;
}}
.yb-hero .yb-badge {{
    display: inline-block;
    background: rgba(255,255,255,.14);
    border: 1px solid rgba(255,255,255,.35);
    border-radius: 999px;
    padding: 0.15rem 0.75rem;
    font-size: 0.8rem;
    margin-top: 0.7rem;
}}
</style>
"""


# --------------------------------------------------------------------------- #
# Hero
# --------------------------------------------------------------------------- #
def hero_html(dest_code: str | None, type_projet: str, tr=lambda s: s,
              nb_offres: int | None = None) -> str:
    t = theme(dest_code)
    titre = t["titres"].get(type_projet, t["titres"]["etudes"])
    badge = ""
    if type_projet in TYPES_JOB_BOARD and nb_offres:
        badge = (f'<span class="yb-badge">📋 {nb_offres} '
                 f'{html.escape(tr("offres actives"))}</span>')
    return (
        '<div class="yb-hero">'
        f'<div class="yb-portail">{t["drapeau"]} '
        f'{html.escape(tr(t["portail"]))}</div>'
        f'<h2>{html.escape(tr(titre))}</h2>'
        f'<div class="yb-sous">{html.escape(tr(t["sous_titre"]))}</div>'
        f'{badge}'
        '</div>'
    )


def appliquer(dest_code: str | None, type_projet: str, tr=lambda s: s,
              nb_offres: int | None = None) -> None:
    """CSS global + bandeau hero. Une ligne a appeler dans ui.py."""
    if st is None:
        return
    st.markdown(css(dest_code), unsafe_allow_html=True)
    st.markdown(hero_html(dest_code, type_projet, tr, nb_offres),
                unsafe_allow_html=True)


# Correspondance libelles UI -> cles internes (l'UI passe "Métier spécialisé").
LIBELLES_TYPE = {
    "métier spécialisé": "metier",
    "metier specialise": "metier",
    "stage/emploi": "emploi",
    "stage / emploi": "emploi",
    "stage": "stage",
    "emploi": "emploi",
    "études": "etudes",
    "etudes": "etudes",
    "étude": "etudes",
}


def type_interne(libelle: str) -> str:
    return LIBELLES_TYPE.get((libelle or "").strip().lower(), "etudes")
