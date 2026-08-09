r"""
traduction_offres.py  (v2)
Traduction des OFFRES D'EMPLOI (titre / lieu / description / domaine).

/!\ NE PAS confondre avec app/api/traduction.py, qui traduit le CONTENU
    (fiches pays, services). Ce module-ci est dedie aux offres ingerees
    depuis Job Bank / Adzuna et utilise sa PROPRE base de cache.

Corrections v1 -> v2 :
  * Les consignes passent en prompt SYSTEME, pas dans le prompt utilisateur.
    Un modele 3B recopiait les regles dans sa reponse.
  * Sequences d'arret + nettoyage du post-ambule ("Note :", "Remarque :",
    "J'ai respecte...") qui polluait les descriptions.
  * Docstring en raw string (le /!\ declenchait un SyntaxWarning).

Jamais traduits : employeur, reference, url, date.
Modele surchargeable : export OLLAMA_MODEL_OFFRES=llama3.3:70b-instruct-q4_K_M
"""

from __future__ import annotations

import os
import re
import sqlite3
import hashlib
import logging
from pathlib import Path

import requests

log = logging.getLogger("yorbity.traduction_offres")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_OFFRES", "llama3.2:3b")
DB_PATH = Path(os.getenv("DB_TRADUCTIONS_OFFRES", "data/traductions_offres.db"))

LANGUES = {
    "fr": "francais",
    "en": "anglais",
    "es": "espagnol",
    "pt": "portugais",
    "ar": "arabe",
    "de": "allemand",
    "it": "italien",
    "zh": "chinois simplifie",
    "tr": "turc",
}

CHAMPS_TRADUISIBLES = ("titre", "lieu", "description", "domaine")

_SYSTEME = (
    "Tu es un moteur de traduction. Tu ne converses pas. "
    "Tu renvoies exclusivement la traduction du texte fourni, en {lc}. "
    "Interdiction absolue d'ajouter une introduction, une conclusion, une note, "
    "une remarque, une explication ou des guillemets englobants. "
    "Conserve intacts : noms d'entreprises, marques, sigles, numeros de reference, "
    "URL, codes de province entre parentheses. "
    "Conserve les sauts de ligne et la ponctuation. "
    "Si le texte est deja en {lc}, renvoie-le mot pour mot."
)

# Le modele colle parfois un commentaire apres la traduction. On coupe net.
_POSTAMBULE = re.compile(
    r"\n\s*(?:note|remarque|n\.?b\.?|attention|explication|traduction|translation)\s*[:\-]",
    re.I,
)
_PREAMBULE = re.compile(
    r"^\s*(?:voici|here is|la traduction|the translation|traduction|translation)\b[^\n:]*:\s*",
    re.I,
)
_JAI_RESPECTE = re.compile(r"\n\s*(?:j'ai|i have|i've)\s+\w+.*$", re.I | re.S)


def _init() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(DB_PATH, check_same_thread=False)
    cx.execute(
        "CREATE TABLE IF NOT EXISTS traductions_offres ("
        "cle TEXT PRIMARY KEY, langue TEXT NOT NULL, source TEXT NOT NULL,"
        "cible TEXT NOT NULL, cree_le TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    cx.commit()
    return cx


_CX = _init()


def _cle(texte: str, langue: str) -> str:
    return hashlib.sha1((langue + "::" + texte).encode()).hexdigest()


def _nettoyer(out: str) -> str:
    out = _PREAMBULE.sub("", out.strip())
    out = _POSTAMBULE.split(out)[0]
    out = _JAI_RESPECTE.sub("", out)
    out = out.strip()
    # guillemets englobants uniquement
    if len(out) > 1 and out[0] == out[-1] and out[0] in "\"'\u00ab\u201c":
        out = out[1:-1].strip()
    return out


def _ollama(texte: str, lc: str, timeout: int = 120) -> str:
    r = requests.post(
        OLLAMA_URL,
        timeout=timeout,
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "system": _SYSTEME.format(lc=lc),
            "prompt": texte,
            "options": {
                "temperature": 0.0,
                "top_p": 0.9,
                "num_predict": 1200,
                "stop": ["\nNote :", "\nNote:", "\nRemarque", "\nN.B."],
            },
        },
    )
    r.raise_for_status()
    return _nettoyer(r.json().get("response") or "")


def traduire(texte: str, langue: str, langue_source: str | None = None) -> str:
    """Traduit un texte. Renvoie l'original si Ollama echoue."""
    if not texte or not texte.strip() or langue not in LANGUES:
        return texte
    if langue_source and langue_source == langue:
        return texte

    row = _CX.execute(
        "SELECT cible FROM traductions_offres WHERE cle=?", (_cle(texte, langue),)
    ).fetchone()
    if row:
        return row[0]

    try:
        cible = _ollama(texte, LANGUES[langue])
    except Exception as e:
        log.warning("Ollama KO (%s) -> texte original conserve.", e)
        return texte

    if not cible:
        return texte

    _CX.execute(
        "INSERT OR REPLACE INTO traductions_offres (cle,langue,source,cible) VALUES (?,?,?,?)",
        (_cle(texte, langue), langue, texte, cible),
    )
    _CX.commit()
    return cible


def traduire_offre(offre: dict, langue: str) -> dict:
    """Copie de l'offre, champs traduits. L'offre en base reste intacte."""
    src = offre.get("langue_source")
    if src == langue:
        return dict(offre)
    out = dict(offre)
    for champ in CHAMPS_TRADUISIBLES:
        v = offre.get(champ)
        if isinstance(v, str) and v.strip():
            out[champ] = traduire(v, langue, langue_source=src)
    out["_traduit_en"] = langue
    return out


def traduire_offres(offres: list[dict], langue: str) -> list[dict]:
    return [traduire_offre(o, langue) for o in offres]


def prechauffer(offres: list[dict], langues: list[str] | None = None) -> None:
    """A appeler depuis offres_sync.py apres l'ingestion (cycle 12 h)."""
    for lg in (langues or list(LANGUES)):
        for o in offres:
            traduire_offre(o, lg)
        log.info("Prechauffage %s : %s offres.", lg, len(offres))


def stats_cache() -> dict:
    return dict(
        _CX.execute("SELECT langue, COUNT(*) FROM traductions_offres GROUP BY langue").fetchall()
    )


def purger(langue: str | None = None) -> int:
    if langue:
        cur = _CX.execute("DELETE FROM traductions_offres WHERE langue=?", (langue,))
    else:
        cur = _CX.execute("DELETE FROM traductions_offres")
    _CX.commit()
    return cur.rowcount


def diagnostic() -> dict:
    info = {"url": OLLAMA_URL, "modele": OLLAMA_MODEL, "db": str(DB_PATH)}
    try:
        info["exemple"] = _ollama("Hello world.", "francais", timeout=60)
        info["ok"] = True
    except Exception as e:
        info["ok"] = False
        info["erreur"] = str(e)
    return info


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    d = diagnostic()
    for k, v in d.items():
        print(f"{k:10} : {v}")
    if not d["ok"]:
        raise SystemExit(1)

    print("\nEssai offre reelle :")
    offre = {
        "titre": "Apprentice-Technician",
        "employeur": "Trane Technologies",
        "lieu": "Charlesbourg, Quebec City",
        "description": (
            "Be a part of our mission! As a world leader in creating comfortable, "
            "sustainable and efficient climate solutions for buildings, homes and "
            "transportation, it's our responsibility to put the planet first."
        ),
        "reference": "JOB-5747579222",
        "url": "https://example.com",
        "langue_source": "en",
    }
    for k, v in traduire_offre(offre, "fr").items():
        print(f"  {k:14} = {v}")

    print("\nControle : la description ne doit contenir NI 'Note' NI 'J'ai respecte'.")
