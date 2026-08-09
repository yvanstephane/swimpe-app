# =============================================================================
# tri_bourses_v1.py — Lot C : TRIER les résultats web de recherche de bourses
# Deux étages, dans cet ordre de fiabilité :
#   1) CLASSEMENT PAR CONFIANCE (règle nette, pas une devinette) :
#      - 🏛️ officiel   : domaine dans la liste blanche data/domaines_officiels_v1.json
#      - ⚠️ non officiel: ailleurs
#   2) MÉNAGE PAR OLLAMA (llama3.3:70b) : lit chaque page et dit si c'est
#      vraiment une bourse, son type (complète/partielle/excellence), si elle
#      semble périmée. Ollama NE détecte PAS les arnaques — il enlève le bruit.
# Ne plante JAMAIS : si Ollama est éteint/injoignable, on garde les résultats
# (dégradation propre) sans jugement de contenu, juste le classement par domaine.
# Le lien réel (issu de Tavily) et l'étiquette « à vérifier » restent sur tout.
# =============================================================================
import json
import os
import re
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELE = os.environ.get("MAIN_MODEL", "llama3.3:70b")
_TIMEOUT = 60


# ── Liste blanche ────────────────────────────────────────────────────────────
def _wl_path():
    p = Path("data/domaines_officiels_v1.json")
    if p.exists():
        return p
    return Path(__file__).resolve().parents[2] / "data" / "domaines_officiels_v1.json"


def _liste_blanche():
    try:
        with open(_wl_path(), encoding="utf-8") as f:
            wl = json.load(f)
        return (list(wl.get("suffixes_officiels", [])),
                list(wl.get("domaines_officiels", [])))
    except Exception:
        return [], []


def _domaine(url):
    try:
        h = (urlparse(url).hostname or "").lower()
        return h[4:] if h.startswith("www.") else h
    except Exception:
        return ""


def est_officiel(url, suffixes=None, domaines=None):
    """True si l'URL vient d'un domaine de confiance (règle nette)."""
    if suffixes is None or domaines is None:
        suffixes, domaines = _liste_blanche()
    h = _domaine(url)
    if not h:
        return False
    if any(h == d or h.endswith("." + d) for d in domaines):
        return True
    if any(h.endswith(sfx) or h == sfx.lstrip(".") for sfx in suffixes):
        return True
    return False


# ── Ollama (facultatif, dégradation propre) ─────────────────────────────────
def ollama_dispo():
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5):
            return True
    except Exception:
        return False


_PROMPT = (
    "Tu analyses une page web pour un service d'aide aux bourses d'études. "
    "On te donne le TITRE, l'URL et un EXTRAIT. Réponds UNIQUEMENT en JSON, sans "
    "aucun texte autour, avec ce format exact :\n"
    '{{"est_bourse": true/false, "type": "complète"|"partielle"|"excellence"|"inconnu", '
    '"perimee": true/false, "resume": "une phrase courte et factuelle"}}\n'
    "Règles : est_bourse=false si la page n'offre pas concrètement une bourse "
    "(article de blog, actualité, page hors sujet). perimee=true si les dates/"
    "l'année indiquent une campagne déjà passée. N'invente RIEN : si tu n'es pas "
    "sûr, mets \"inconnu\" et perimee=false. Ne donne aucun avis sur l'authenticité.\n\n"
    "TITRE: {titre}\nURL: {url}\nEXTRAIT: {extrait}"
)


def _juger_ollama(res):
    """Retourne un dict de jugement, ou None si Ollama indisponible/illisible."""
    prompt = _PROMPT.format(titre=res.get("titre", "")[:200],
                            url=res.get("url", ""),
                            extrait=(res.get("extrait", "") or "")[:1200])
    corps = json.dumps({"model": MODELE, "prompt": prompt, "stream": False,
                        "format": "json", "options": {"temperature": 0}}).encode()
    try:
        req = urllib.request.Request(OLLAMA_URL, data=corps, method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as rep:
            brut = json.loads(rep.read()).get("response", "")
        j = json.loads(brut)
        return {
            "est_bourse": bool(j.get("est_bourse", True)),
            "type": j.get("type", "inconnu") if j.get("type") in
                    ("complète", "partielle", "excellence", "inconnu") else "inconnu",
            "perimee": bool(j.get("perimee", False)),
            "resume": str(j.get("resume", ""))[:220],
        }
    except Exception:
        return None


# ── Fonction publique ────────────────────────────────────────────────────────
def trier(resultats, utiliser_ollama=True):
    """Classe et nettoie une liste de résultats web {titre,url,extrait}.
    Retourne un dict :
      { officielles: [...], non_officielles: [...], ecartees: [...],
        ollama: True/False }
    Chaque bourse gardée : {titre, url, confiance('officiel'|'non_officiel'),
      badge, type, resume, a_verifier: True, perimee}.
    NE PLANTE JAMAIS.
    """
    suffixes, domaines = _liste_blanche()
    with_ollama = bool(utiliser_ollama) and ollama_dispo()

    officielles, non_off, ecartees = [], [], []
    for r in resultats or []:
        url = (r.get("url") or "").strip()
        if not url:
            continue  # jamais de résultat sans lien réel
        officiel = est_officiel(url, suffixes, domaines)
        jugement = _juger_ollama(r) if with_ollama else None

        # Ménage : on n'écarte QUE si Ollama est sûr que ce n'est pas une bourse.
        if jugement is not None and jugement["est_bourse"] is False:
            ecartees.append({"titre": r.get("titre", url), "url": url,
                             "raison": "pas une bourse (jugé par Ollama)"})
            continue

        item = {
            "titre": r.get("titre", url),
            "url": url,
            "confiance": "officiel" if officiel else "non_officiel",
            "badge": "🏛️ Source officielle" if officiel
                     else "⚠️ Source non officielle — à vérifier",
            "type": (jugement or {}).get("type", "inconnu"),
            "resume": (jugement or {}).get("resume", "") or (r.get("extrait", "") or "")[:180],
            "perimee": (jugement or {}).get("perimee", False),
            "a_verifier": True,
        }
        (officielles if officiel else non_off).append(item)

    # tri interne : non périmées d'abord
    officielles.sort(key=lambda x: x["perimee"])
    non_off.sort(key=lambda x: x["perimee"])
    return {"officielles": officielles, "non_officielles": non_off,
            "ecartees": ecartees, "ollama": with_ollama}


def compter_domaines():
    s, d = _liste_blanche()
    return len(s), len(d)


# _lot_bourses_c_v1
