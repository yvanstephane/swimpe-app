# =============================================================================
# recherche_poste.py — Champ « Poste recherché » (façon Guichet-Emplois/Indeed)
# Remplace « Niveau visé » quand le projet est Métier spécialisé ou Stage/Emploi.
# Liste des postes réellement disponibles pour la destination (base + référence),
# avec saisie libre : taper « plo » propose « Plombier ».
# =============================================================================
import streamlit as st
import sqlite3, re

DB = "data/mobilite.db"

METIERS_REF = [
    "Plombier", "Électricien", "Menuisier", "Charpentier", "Maçon", "Soudeur",
    "Mécanicien", "Couvreur", "Peintre en bâtiment", "Chauffagiste",
    "Grutier", "Conducteur d'engins", "Infirmier", "Aide-soignant",
    "Cuisinier", "Boulanger", "Boucher", "Coiffeur", "Serrurier", "Jardinier",
]
POSTES_ETUDIANTS_REF = [
    "Stage informatique", "Stage ingénierie", "Stage marketing", "Stage finance",
    "Stage ressources humaines", "Stage communication", "Stage recherche",
    "Emploi étudiant — restauration", "Emploi étudiant — vente",
    "Emploi étudiant — administration", "Assistant de recherche", "Tutorat",
]

TYPES_BASE = {"Métier spécialisé": ("metier",),
              "Stage / Emploi étudiant": ("stage", "emploi")}


def concerne(type_c):
    return type_c in TYPES_BASE


def _postes_base(dest_code, types):
    con = sqlite3.connect(DB)
    try:
        q = ",".join("?" * len(types))
        rows = con.execute(
            f"SELECT DISTINCT titre FROM opportunites WHERE destination=? "
            f"AND type IN ({q})", (dest_code.upper(), *types)).fetchall()
    except sqlite3.Error:
        rows = []
    con.close()
    postes = set()
    for (titre,) in rows:
        t = re.split(r"[—–-]", titre)[0].strip()
        if 2 < len(t) < 50:
            postes.add(t)
    return postes


def options(type_c, dest_code):
    ref = METIERS_REF if type_c == "Métier spécialisé" else POSTES_ETUDIANTS_REF
    base = _postes_base(dest_code, TYPES_BASE.get(type_c, ()))
    return ["Tous les postes"] + sorted(base | set(ref), key=str.lower)


def selecteur(conteneur, type_c, dest_code, tr, cle="poste_rech"):
    """Champ de recherche de poste. Retourne le poste choisi ('' = tous)."""
    opts = options(type_c, dest_code)
    libelle = ("🔧 " + tr("Poste recherché")) if type_c == "Métier spécialisé" \
        else ("💼 " + tr("Poste ou stage recherché"))
    aide = tr("Tape les premières lettres (ex : « plo » pour plombier) "
              "ou choisis dans la liste.")
    try:
        choix = conteneur.selectbox(libelle, opts, key=cle,
                                    accept_new_options=True, help=aide)
    except TypeError:                      # Streamlit plus ancien
        choix = conteneur.selectbox(libelle, opts, key=cle, help=aide)
    return "" if choix == "Tous les postes" else choix


def filtre(offres, poste):
    """Ne garde que les offres correspondant au poste recherché."""
    if not poste:
        return offres
    mots = [m for m in re.split(r"\W+", poste.lower()) if len(m) > 2]
    if not mots:
        return offres
    gardees = []
    for o in offres:
        texte = " ".join(str(o.get(k, "")) for k in
                         ("titre", "domaine", "extrait", "entreprise")).lower()
        if any(m in texte for m in mots):
            gardees.append(o)
    return gardees
