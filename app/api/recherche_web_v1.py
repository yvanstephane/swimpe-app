# =============================================================================
# recherche_web_v1.py — Lot B : brique de RECHERCHE WEB (via Tavily)
# La recherche tourne sur la machine (wifi) ; ce module ne fait QUE chercher :
# pas de classification (lot C), pas d'affichage (lot D).
# Garanties : ne plante JAMAIS. En cas de souci, renvoie une liste vide + un
# code d'état clair pour le voyant admin 🟢🟡🔴 :
#   "ok" · "pas_de_cle" · "pas_de_wifi" · "quota_epuise" · "tavily_injoignable"
# Cache 24 h dans SQLite (table recherche_web_cache) → une même requête ne
# coûte qu'1 crédit/jour. Compteur mensuel de crédits pour le voyant.
# Clé lue depuis .env : TAVILY_API_KEY (jamais en dur).
# =============================================================================
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone

DB = "data/mobilite.db"
TAVILY_URL = "https://api.tavily.com/search"
CACHE_HEURES = 24
QUOTA_MENSUEL = 1000          # palier gratuit Tavily (pour le voyant)
SEUIL_ALERTE = 0.90          # 🟡 au-delà de 90 % du quota
_TIMEOUT = 25


# ── Base : chemin robuste (depuis la racine projet ou app/api) ──────────────
def _db_path():
    from pathlib import Path
    p = Path(DB)
    if p.exists():
        return str(p)
    alt = Path(__file__).resolve().parents[2] / "data" / "mobilite.db"
    return str(alt)


def _cx(timeout=30):
    con = sqlite3.connect(_db_path(), timeout=timeout)
    try:
        con.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass
    return con


def _init(con):
    con.execute("""CREATE TABLE IF NOT EXISTS recherche_web_cache(
        cle TEXT PRIMARY KEY,
        requete TEXT,
        resultats TEXT,
        maj TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS recherche_web_usage(
        mois TEXT PRIMARY KEY,
        credits INTEGER DEFAULT 0)""")
    con.execute("""CREATE TABLE IF NOT EXISTS recherche_web_etat(
        id INTEGER PRIMARY KEY CHECK (id = 1),
        code TEXT,
        detail TEXT,
        mois TEXT,
        dernier_succes TEXT,
        maj TEXT)""")


def _cle_api():
    return (os.environ.get("TAVILY_API_KEY") or "").strip()


# ── Compteur de crédits (voyant) ────────────────────────────────────────────
def _mois_courant():
    return date.today().strftime("%Y-%m")


def _incr_credits(con, n=1):
    m = _mois_courant()
    con.execute("INSERT INTO recherche_web_usage(mois,credits) VALUES(?,?) "
                "ON CONFLICT(mois) DO UPDATE SET credits=credits+?", (m, n, n))


def _marquer_quota_epuise(con):
    """Aligne le compteur sur le quota (Tavily a dit non). Se réinitialise le mois suivant."""
    con.execute("INSERT INTO recherche_web_usage(mois,credits) VALUES(?,?) "
                "ON CONFLICT(mois) DO UPDATE SET credits=?",
                (_mois_courant(), QUOTA_MENSUEL, QUOTA_MENSUEL))


def credits_utilises():
    """Crédits consommés ce mois-ci (pour le voyant admin)."""
    try:
        con = _cx(); _init(con)
        row = con.execute("SELECT credits FROM recherche_web_usage WHERE mois=?",
                          (_mois_courant(),)).fetchone()
        con.close()
        return row[0] if row else 0
    except Exception:
        return 0


# ── État de la recherche (voyant 🟢🟡🔴) ────────────────────────────────────
def _memoriser_etat(con, code, detail=""):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    row = con.execute("SELECT dernier_succes FROM recherche_web_etat WHERE id=1").fetchone()
    dernier = row[0] if row else None
    if code == "ok":
        dernier = now
    con.execute("INSERT INTO recherche_web_etat(id,code,detail,mois,dernier_succes,maj) "
                "VALUES(1,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                "code=excluded.code, detail=excluded.detail, mois=excluded.mois, "
                "dernier_succes=excluded.dernier_succes, maj=excluded.maj",
                (code, detail, _mois_courant(), dernier, now))


def etat_recherche():
    """Résumé pour le voyant admin. Retourne un dict :
    { voyant: '🟢'|'🟡'|'🔴', code, message, credits, quota, dernier_succes }."""
    try:
        con = _cx(); _init(con)
        row = con.execute("SELECT code,detail,mois,dernier_succes FROM recherche_web_etat WHERE id=1").fetchone()
        con.close()
    except Exception:
        row = None
    code = row[0] if row else "inconnu"
    mois_etat = row[2] if row else None
    dernier = row[3] if row else None
    used = credits_utilises()

    if not _cle_api():
        return {"voyant": "🔴", "code": "pas_de_cle",
                "message": "Clé Tavily absente du fichier .env.",
                "credits": used, "quota": QUOTA_MENSUEL, "dernier_succes": dernier}
    # Quota jugé EN DIRECT sur le compteur (se réinitialise chaque mois).
    if used >= QUOTA_MENSUEL:
        return {"voyant": "🔴", "code": "quota_epuise",
                "message": f"Quota Tavily épuisé pour ce mois ({used}/{QUOTA_MENSUEL})."
                + (f" · dernier succès : {dernier}" if dernier else ""),
                "credits": used, "quota": QUOTA_MENSUEL, "dernier_succes": dernier}
    # Panne réseau/infra : seulement si elle date du mois courant (sinon obsolète).
    if code in ("pas_de_wifi", "tavily_injoignable") and mois_etat == _mois_courant():
        libelle = {"pas_de_wifi": "Pas de connexion Internet",
                   "tavily_injoignable": "Tavily ne répond pas"}[code]
        return {"voyant": "🔴", "code": code,
                "message": libelle + (f" · dernier succès : {dernier}" if dernier else ""),
                "credits": used, "quota": QUOTA_MENSUEL, "dernier_succes": dernier}
    if used >= QUOTA_MENSUEL * SEUIL_ALERTE:
        return {"voyant": "🟡", "code": "quota_bientot",
                "message": f"Quota bientôt épuisé ({used}/{QUOTA_MENSUEL}).",
                "credits": used, "quota": QUOTA_MENSUEL, "dernier_succes": dernier}
    return {"voyant": "🟢", "code": "ok",
            "message": f"Recherche web : OK ({used}/{QUOTA_MENSUEL} ce mois).",
            "credits": used, "quota": QUOTA_MENSUEL, "dernier_succes": dernier}


# ── Journal (réutilise security_events si présent, sinon silencieux) ────────
def _journal(con, evenement, detail):
    try:
        con.execute("INSERT INTO security_events(type,detail,ts) VALUES(?,?,?)",
                    (evenement, detail, datetime.now(timezone.utc).isoformat(timespec="seconds")))
    except Exception:
        pass  # table absente ou schéma différent → on n'échoue pas pour si peu


# ── Cache ────────────────────────────────────────────────────────────────────
def _cache_lire(con, cle, heures=CACHE_HEURES):
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM recherche_web_cache WHERE cle=?", (cle,)).fetchone()
    if not row:
        return None
    try:
        age = time.time() - datetime.fromisoformat(row["maj"]).timestamp()
    except Exception:
        return None
    if age > heures * 3600:
        return None
    try:
        return json.loads(row["resultats"])
    except Exception:
        return None


def _cache_ecrire(con, cle, requete, resultats):
    con.execute("INSERT OR REPLACE INTO recherche_web_cache(cle,requete,resultats,maj) "
                "VALUES(?,?,?,?)",
                (cle, requete, json.dumps(resultats, ensure_ascii=False),
                 datetime.now(timezone.utc).isoformat(timespec="seconds")))


# ── Appel Tavily (POST HTTP direct — aucune librairie tierce) ───────────────
def _appel_tavily(requete, cle, max_results=6):
    corps = json.dumps({
        "query": requete,
        "search_depth": "basic",        # 1 crédit / recherche
        "max_results": max_results,
        "include_raw_content": True,    # texte propre des pages
        "include_answer": False,
        "include_usage": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        TAVILY_URL, data=corps, method="POST",
        headers={"Authorization": f"Bearer {cle}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as rep:
        return json.loads(rep.read())


def _normaliser(brut):
    """Transforme la réponse Tavily en liste de résultats simples et sûrs."""
    out = []
    for r in (brut.get("results") or []):
        url = (r.get("url") or "").strip()
        if not url:
            continue  # jamais de résultat sans lien réel
        texte = r.get("raw_content") or r.get("content") or ""
        out.append({
            "titre": (r.get("title") or url).strip(),
            "url": url,                          # provient de Tavily, jamais inventé
            "extrait": (texte or "").strip()[:1500],
        })
    return out


# ── Fonction publique ────────────────────────────────────────────────────────
def chercher_web(requete, forcer=False):
    """Cherche sur le web via Tavily. NE PLANTE JAMAIS.
    Retourne (resultats, etat) où etat ∈
    {ok, pas_de_cle, pas_de_wifi, quota_epuise, tavily_injoignable}.
    resultats = liste de {titre, url, extrait} (vide si etat != ok)."""
    requete = (requete or "").strip()
    cle = _cle_api()
    if not cle:
        try:
            con = _cx(); _init(con); _memoriser_etat(con, "pas_de_cle"); con.commit(); con.close()
        except Exception:
            pass
        return [], "pas_de_cle"
    if not requete:
        return [], "ok"

    cle_cache = "tavily:" + requete.lower()
    con = _cx(); _init(con)

    # 1) cache 24 h (n'utilise aucun crédit)
    if not forcer:
        cached = _cache_lire(con, cle_cache)
        if cached is not None:
            _memoriser_etat(con, "ok")
            con.commit(); con.close()
            return cached, "ok"

    # 2) quota atteint → on ne rappelle pas Tavily
    if credits_utilises() >= QUOTA_MENSUEL:
        _memoriser_etat(con, "quota_epuise")
        _journal(con, "recherche_web", "quota mensuel atteint")
        con.commit(); con.close()
        return [], "quota_epuise"

    # 3) appel réseau, avec dégradation propre
    try:
        brut = _appel_tavily(requete, cle)
    except urllib.error.HTTPError as e:
        if e.code in (402, 429):
            _marquer_quota_epuise(con)   # aligne le compteur : Tavily a dit non
            _memoriser_etat(con, "quota_epuise", f"HTTP {e.code}")
            _journal(con, "recherche_web", f"quota (HTTP {e.code})")
            con.commit(); con.close()
            return [], "quota_epuise"
        _memoriser_etat(con, "tavily_injoignable", f"HTTP {e.code}")
        _journal(con, "recherche_web", f"HTTP {e.code} sur '{requete[:60]}'")
        con.commit(); con.close()
        return [], "tavily_injoignable"
    except urllib.error.URLError as e:
        # pas de réseau / DNS / connexion refusée
        _memoriser_etat(con, "pas_de_wifi", str(getattr(e, "reason", e))[:120])
        _journal(con, "recherche_web", "réseau indisponible")
        con.commit(); con.close()
        return [], "pas_de_wifi"
    except Exception as e:
        _memoriser_etat(con, "tavily_injoignable", str(e)[:120])
        _journal(con, "recherche_web", f"erreur : {str(e)[:80]}")
        con.commit(); con.close()
        return [], "tavily_injoignable"

    # 4) succès : normaliser, compter le crédit, mettre en cache
    resultats = _normaliser(brut)
    cout = 1
    usage = brut.get("usage") or {}
    if isinstance(usage, dict) and isinstance(usage.get("total"), int) and usage["total"] > 0:
        cout = usage["total"]
    _incr_credits(con, cout)
    _cache_ecrire(con, cle_cache, requete, resultats)
    _memoriser_etat(con, "ok")
    con.commit(); con.close()
    return resultats, "ok"


# _lot_bourses_b_v1
