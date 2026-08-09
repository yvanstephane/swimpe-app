# =============================================================================
# moteur_bourses_v1.py — Tiroir A : bourses VÉRIFIÉES à la main (Lot A)
# Principe : 100 % déterministe, AUCUNE donnée inventée. Lit
# data/bourses_verifiees_v1.json. Le web (lots C-D) viendra confirmer/enrichir.
# Chaque bourse porte un interrupteur `active` et une date `verifie_le` ;
# le moteur n'affiche que les bourses actives et signale celles trop anciennes.
# Aucune dépendance à Streamlit : ce module est testable seul.
# =============================================================================
import json
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

# 53 codes ISO Afrique (même liste que le moteur de plans).
AFRIQUE_ISO = {
    "DZ", "AO", "BJ", "BW", "BF", "BI", "CV", "CM", "CF", "TD", "KM", "CG",
    "CD", "CI", "DJ", "EG", "GQ", "ER", "SZ", "ET", "GA", "GM", "GH", "GN",
    "GW", "KE", "LS", "LR", "LY", "MG", "MW", "ML", "MR", "MU", "MA", "MZ",
    "NA", "NE", "NG", "RW", "ST", "SN", "SC", "SL", "SO", "ZA", "SS", "SD",
    "TZ", "TG", "TN", "UG", "ZM", "ZW",
}


def _kb_path():
    p = Path("data/bourses_verifiees_v1.json")
    if p.exists():
        return p
    return Path(__file__).resolve().parents[2] / "data" / "bourses_verifiees_v1.json"


@lru_cache(maxsize=1)
def _kb():
    with open(_kb_path(), encoding="utf-8") as f:
        return json.load(f)


def _seuil_peremption():
    return _kb().get("meta", {}).get("seuil_peremption_jours", 180)


def _eligible(b, code_orig):
    """Le pays d'origine est-il éligible à cette bourse ?"""
    e = b.get("origines_eligibles", "tous")
    if e == "tous":
        return True
    if e == "afrique":
        return code_orig in AFRIQUE_ISO
    if isinstance(e, list):
        return code_orig in e
    return True  # valeur inconnue → on montre (avec « à vérifier »)


def _domaine_ok(b, domaine):
    """Filtre par domaine SEULEMENT si la bourse est explicitement ciblée."""
    doms = b.get("domaines")
    if not domaine or not doms:
        return True
    d = domaine.strip().lower()
    return any(d in x.lower() or x.lower() in d for x in doms)


def _peremption_jours(b):
    try:
        j = datetime.strptime(b["verifie_le"], "%Y-%m-%d").date()
        return (date.today() - j).days
    except Exception:
        return None


def chercher(code_orig, dest, domaine=""):
    """Bourses vérifiées ACTIVES pour (origine, destination, domaine optionnel).
    Retourne une liste de dicts prêts à afficher, chacun avec la source
    « vérifié Yorbity » et le drapeau « à vérifier ». Tri : vérifications les
    plus récentes d'abord."""
    kb = _kb()
    seuil = _seuil_peremption()
    out = []
    for b in kb.get("bourses", []):
        if not b.get("active", True):
            continue
        if dest not in b.get("destinations", []):
            continue
        if not _eligible(b, code_orig):
            continue
        if not _domaine_ok(b, domaine):
            continue
        j = _peremption_jours(b)
        out.append({
            "nom": b["nom"],
            "type": b.get("type", "à préciser"),
            "url": b.get("url", ""),
            "resume": b.get("resume", ""),
            "note": b.get("note", ""),
            "source": "vérifié Yorbity",
            "a_verifier": bool(b.get("a_verifier", True)),
            "verifie_le": b.get("verifie_le", ""),
            "peremption_jours": j,
            "perime": (j is not None and j > seuil),
        })
    out.sort(key=lambda x: (x["peremption_jours"] if x["peremption_jours"] is not None else 10**9, x["nom"]))
    return out


def destinations_couvertes():
    """Codes destination ayant au moins une bourse active (pour l'UI plus tard)."""
    d = set()
    for b in _kb().get("bourses", []):
        if b.get("active", True):
            d.update(b.get("destinations", []))
    return d


def compter():
    """(actives, total) — utile pour l'admin."""
    bourses = _kb().get("bourses", [])
    actives = sum(1 for b in bourses if b.get("active", True))
    return actives, len(bourses)


# _lot_bourses_a_v1
