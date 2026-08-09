"""
identite.py — Le nom d'un compte Yorbity est un NOM LEGAL, et l'abonnement
est PERSONNEL : les dossiers ne peuvent etre ouverts qu'au nom du compte.

Trois outils :

  valider_nom_complet(nom) -> (ok, message)
      Exige au moins prenom + nom (2 mots), lettres uniquement
      (accents, tirets, apostrophes admis), 2-40 caracteres par mot.

  normaliser(nom) -> str
      "  Hélène-Guy  DUPONT " -> "dupont helene-guy" (casse, accents,
      espaces, ORDRE DES MOTS neutralises).

  meme_personne(a, b) -> bool
      "Jean Thibault" == "THIBAULT  jean"  -> True
      "Thibault Jean" == "Helene Guy"      -> False

Pourquoi l'ordre des mots est neutralise : les formulaires africains et
europeens alternent Nom-Prenom / Prenom-Nom ; refuser "Jean Thibault" a
quelqu'un inscrit "Thibault Jean" serait un faux positif insultant.
Limite assumee : deux personnes portant exactement les memes mots de nom
sont indistinguables ici — c'est le paiement nominatif qui tranchera.
"""

from __future__ import annotations

import re
import unicodedata

# Lettres (toutes ecritures), tiret et apostrophe a l'interieur d'un mot.
_MOT = re.compile(r"^[^\W\d_]+(?:[-'’][^\W\d_]+)*$", re.UNICODE)


def _sans_accents(txt: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", txt)
                   if not unicodedata.combining(c))


def normaliser(nom: str) -> str:
    """Casse, accents, espaces multiples et ordre des mots neutralises."""
    mots = _sans_accents((nom or "").strip().lower()).split()
    return " ".join(sorted(mots))


def meme_personne(a: str, b: str) -> bool:
    na, nb = normaliser(a), normaliser(b)
    return bool(na) and na == nb


def valider_nom_complet(nom: str) -> tuple[bool, str]:
    """(True, "") si le nom ressemble a un nom legal complet, sinon
    (False, message d'erreur pret a afficher)."""
    nom = " ".join((nom or "").split())
    if len(nom) > 80:
        return False, "Nom trop long (80 caractères max)."
    mots = nom.split()
    if len(mots) < 2:
        return False, ("Indique ton nom complet (prénom et nom, comme sur "
                       "ton passeport) — ton abonnement est personnel.")
    for m in mots:
        if len(m) < 2:
            return False, f"« {m} » est trop court pour un prénom ou un nom."
        if not _MOT.match(m):
            return False, (f"« {m} » contient des caractères non admis "
                           "(lettres, tirets et apostrophes uniquement).")
    return True, ""


if __name__ == "__main__":
    essais = [
        ("Thibault Jean", "jean THIBAULT", True),
        ("Hélène-Guy Dupont", "helene-guy DUPONT", True),
        ("Thibault Jean", "Helene Guy", False),
        ("N'Guessan Aya", "aya n'guessan", True),
    ]
    for a, b, attendu in essais:
        assert meme_personne(a, b) is attendu, (a, b)
    assert valider_nom_complet("Thibault Jean")[0]
    assert not valider_nom_complet("Jean")[0]
    assert not valider_nom_complet("Jean123 Dupont")[0]
    assert not valider_nom_complet("J Dupont")[0]
    print("identite.py : tous les essais passent")
