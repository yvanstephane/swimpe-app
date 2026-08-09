#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sonde_uk_vide_v1.py — Yorbity
Diagnostic LECTURE SEULE : pourquoi la page Royaume-Uni n'affiche aucune offre ?
Ne modifie AUCUN fichier. N'affiche JAMAIS la valeur des clés (.env), noms seulement.
Lancer depuis la racine du projet (~/mobilite-ia), puis coller la sortie COMPLÈTE
dans la conversation.
"""

import ast
import importlib
import inspect
import json
import logging
import os
import re
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

RACINE = Path.cwd()
API = RACINE / "app" / "api"
SRC = API / "sources"

VERDICT = {}  # indices accumulés pour la lecture rapide finale


def titre(t):
    print("\n" + "=" * 10 + " " + t + " " + "=" * 10)


def tb_court():
    lignes = traceback.format_exc().splitlines()
    return "\n".join("  " + l for l in lignes[-10:])


def lire(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def infos_fichier(p):
    p = Path(p)
    if not p.exists():
        return f"{p} : ABSENT"
    st = p.stat()
    return (f"{p.name} : {st.st_size} octets, "
            f"modifié {datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M:%S}")


# ------------------------------------------------------------------ A
def sec_environnement():
    titre("A. ENVIRONNEMENT")
    print("dossier courant :", RACINE)
    print("python :", sys.version.split()[0], "->", sys.executable)
    for p in (API / "ui.py", SRC / "uk_sponsors.py", SRC / "adzuna.py",
              SRC / "registre.py", RACINE / "data" / "uk_sponsors.csv",
              RACINE / ".env"):
        print(" -", infos_fichier(p))
    if not (API / "ui.py").exists():
        print("!! Lance la sonde depuis la racine du projet (~/mobilite-ia).")


# ------------------------------------------------------------------ B
def lire_env():
    env = {}
    p = RACINE / ".env"
    if not p.exists():
        return env
    for brute in lire(p).splitlines():
        s = brute.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        if s.startswith("export "):
            s = s[len("export "):]
        k, v = s.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def sec_env():
    titre("B. FICHIER .env (noms seulement, valeurs JAMAIS affichées)")
    env = lire_env()
    if not env:
        print(".env absent ou vide")
    for k, v in env.items():
        print(f" - {k} (longueur valeur : {len(v)})")
    a_id = a_key = None
    for k, v in env.items():
        K = k.upper()
        if "ADZUNA" in K and "KEY" in K:
            a_key = v
        elif "ADZUNA" in K and "ID" in K:
            a_id = v
    for k, v in os.environ.items():  # variables déjà exportées dans le shell
        K = k.upper()
        if "ADZUNA" in K and "KEY" in K and not a_key:
            a_key = v
            print(f" - {k} (trouvée dans l'environnement shell)")
        elif "ADZUNA" in K and "ID" in K and not a_id:
            a_id = v
            print(f" - {k} (trouvée dans l'environnement shell)")
    print("identifiant Adzuna (app_id)  :", "présent" if a_id else "INTROUVABLE")
    print("clé Adzuna (app_key)         :", "présente" if a_key else "INTROUVABLE")
    VERDICT["creds"] = bool(a_id and a_key)
    return a_id, a_key


# ------------------------------------------------------------------ C
def sec_vars_code():
    titre("C. VARIABLES D'ENVIRONNEMENT LUES PAR LE CODE")
    motifs = [
        re.compile(r"""getenv\(\s*['"]([A-Za-z_][A-Za-z0-9_]*)"""),
        re.compile(r"""environ\.get\(\s*['"]([A-Za-z_][A-Za-z0-9_]*)"""),
        re.compile(r"""environ\[\s*['"]([A-Za-z_][A-Za-z0-9_]*)"""),
        re.compile(r"""secrets\[\s*['"]([A-Za-z_][A-Za-z0-9_]*)"""),
    ]
    vus = {}
    for f in sorted(API.rglob("*.py")):
        if "__pycache__" in f.parts:
            continue
        texte = lire(f)
        for m in motifs:
            for nom in m.findall(texte):
                vus.setdefault(nom, set()).add(f.name)
    if not vus:
        print("aucune trouvée (surprenant)")
    for nom in sorted(vus):
        print(f" - {nom}  <- {', '.join(sorted(vus[nom]))}")


# ------------------------------------------------------------------ D
def noms_toplevel(texte):
    try:
        arbre = ast.parse(texte)
    except SyntaxError as e:
        return None, f"SyntaxError : {e}"
    noms = []
    for n in arbre.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            noms.append(n.name + "()")
        elif isinstance(n, ast.ClassDef):
            meths = [m.name for m in n.body
                     if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            noms.append(f"class {n.name}[{', '.join(meths)}]")
        elif isinstance(n, ast.Assign):
            for c in n.targets:
                if isinstance(c, ast.Name):
                    noms.append(c.id)
    return noms, None


def sec_uk_sponsors():
    titre("D. uk_sponsors.py — ÉTAT COURANT vs DERNIER .bak")
    f = SRC / "uk_sponsors.py"
    texte = lire(f)
    if not texte:
        print("uk_sponsors.py ABSENT ou vide")
        VERDICT["uk_py"] = False
        return
    print(infos_fichier(f), f"— {len(texte.splitlines())} lignes")
    for motif in ("PLAFOND", "findajob", "UKS-", "adzuna"):
        print(f"  '{motif}' : {texte.count(motif)} occurrence(s)")
    for lg in texte.splitlines():
        if re.match(r"\s*PLAFOND\s*=", lg):
            print("  ligne PLAFOND :", lg.strip())
    noms, err = noms_toplevel(texte)
    print("  ast.parse :", "OK" if not err else err)
    VERDICT["uk_py"] = err is None
    baks = sorted(SRC.glob("uk_sponsors.py.bak-*"))
    if not baks:
        print("  aucun .bak trouvé à côté")
        return
    bak = baks[-1]
    tb = lire(bak)
    print(f"  dernier .bak : {bak.name} — {len(tb.splitlines())} lignes")
    for lg in tb.splitlines():
        if re.match(r"\s*PLAFOND\s*=", lg):
            print("  ligne PLAFOND (.bak) :", lg.strip())
    n_bak, _ = noms_toplevel(tb)
    if noms is not None and n_bak is not None:
        manquants = [x for x in n_bak if x not in noms]
        nouveaux = [x for x in noms if x not in n_bak]
        if manquants:
            print("  !! présents dans le .bak, ABSENTS du fichier courant :",
                  ", ".join(manquants))
        if nouveaux:
            print("  nouveaux depuis le .bak :", ", ".join(nouveaux))
        if not manquants and not nouveaux:
            print("  mêmes définitions de haut niveau que le .bak")


# ------------------------------------------------------------------ E
def sec_adzuna_py():
    titre("E. adzuna.py — EXCLUSION GB")
    f = SRC / "adzuna.py"
    texte = lire(f)
    if not texte:
        print("adzuna.py ABSENT")
        return
    print("marqueur patch_uk_exclusif :",
          "présent" if "patch_uk_exclusif" in texte else "ABSENT")
    _, err = noms_toplevel(texte)
    print("ast.parse :", "OK" if not err else err)
    lignes = [lg.strip()[:120] for lg in texte.splitlines()
              if re.search(r"""['"]gb['"]|\bGB\b""", lg)]
    for lg in lignes[:12]:
        print("  .", lg)
    if len(lignes) > 12:
        print(f"  ... +{len(lignes) - 12} autres lignes mentionnant GB")


# ------------------------------------------------------------------ F
def sec_ui():
    titre("F. ui.py — MARQUEURS")
    texte = lire(API / "ui.py")
    for m in ("_yorbity_patience", "patch_seed_v1"):
        present = m in texte
        print(f" - {m} : {'présent' if present else 'ABSENT'}")
        if m == "_yorbity_patience":
            VERDICT["patience"] = present


# ------------------------------------------------------------------ G
def sec_message():
    titre("G. OÙ VIT LE MESSAGE « Aucune offre ... pays d'origine »")
    motif = re.compile(r"pays d.origine", re.IGNORECASE)  # apostrophe droite ou typographique
    fichiers = [f for f in sorted(API.rglob("*.py")) if "__pycache__" not in f.parts]
    dossier_i18n = RACINE / "data" / "i18n"
    if dossier_i18n.is_dir():
        fichiers += sorted(dossier_i18n.glob("*.json"))
    trouves = 0
    for f in fichiers:
        texte = lire(f)
        if not texte or not motif.search(texte):
            continue
        trouves += 1
        if f.suffix == ".json":
            try:
                data = json.loads(texte)
                cles = [k for k, v in data.items()
                        if isinstance(v, str) and motif.search(v)]
                print(f" - {f.name} : clé(s) {cles[:4]}")
            except Exception:
                print(f" - {f.name} : motif présent (json illisible)")
        else:
            lignes = texte.splitlines()
            for i, lg in enumerate(lignes):
                if motif.search(lg):
                    debut, fin = max(0, i - 8), min(len(lignes), i + 6)
                    print(f" - {f.relative_to(RACINE)} — contexte lignes {debut + 1}-{fin} :")
                    for j in range(debut, fin):
                        marque = ">>" if j == i else "  "
                        print(f"   {marque} {j + 1:4d} {lignes[j][:118]}")
                    break  # un seul contexte par fichier
        if trouves >= 3:
            break
    if not trouves:
        print("motif introuvable dans app/ et data/i18n/ "
              "(message peut-être construit dynamiquement)")


# ------------------------------------------------------------------ H
def sec_csv():
    titre("H. REGISTRE SPONSORS (CSV)")
    f = RACINE / "data" / "uk_sponsors.csv"
    if not f.exists():
        print("uk_sponsors.csv ABSENT")
        VERDICT["csv"] = False
        return
    n = 0
    entete = ""
    with open(f, encoding="utf-8", errors="replace") as fh:
        for i, lg in enumerate(fh):
            if i == 0:
                entete = lg.strip()[:120]
            n += 1
    print(f"{n} lignes — en-tête : {entete}")
    VERDICT["csv"] = n > 1000
    d = RACINE / "data" / "uk_sponsors.date"
    if d.exists():
        print("uk_sponsors.date :", lire(d).strip())


# ------------------------------------------------------------------ I
def sec_api_directe(a_id, a_key):
    titre("I. TEST DIRECT API ADZUNA (gb, « electrician »)")
    if not (a_id and a_key):
        print("sauté : identifiants introuvables (voir section B)")
        VERDICT["api"] = "sans_cles"
        return
    params = urllib.parse.urlencode({
        "app_id": a_id, "app_key": a_key,
        "what": "electrician", "results_per_page": "3",
    })
    url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "yorbity-sonde/1"})
    try:
        with urllib.request.urlopen(req, timeout=25) as rep:
            corps = rep.read().decode("utf-8", errors="replace")
        data = json.loads(corps)
        print(f"HTTP 200 — count = {data.get('count')} ; "
              f"{len(data.get('results', []))} résultat(s) page 1")
        VERDICT["api"] = "ok"
    except urllib.error.HTTPError as e:
        corps = ""
        try:
            corps = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        print(f"HTTP {e.code} — {corps}")
        VERDICT["api"] = f"http_{e.code}"
    except Exception as e:
        print("échec réseau :", repr(e)[:200])
        VERDICT["api"] = "reseau"


# ------------------------------------------------------------------ J
VOCAB = {
    "metier": "electrician", "titre": "electrician", "query": "electrician",
    "q": "electrician", "quoi": "electrician", "mot": "electrician",
    "mots_cles": "electrician", "recherche": "electrician", "terme": "electrician",
    "what": "electrician",
    "pays": "GB", "country": "GB", "code_pays": "GB", "cc": "GB",
    "page": 1, "limite": 25, "limit": 25, "max_resultats": 25, "nb": 25, "n": 25,
    "langue": "fr", "lang": "fr", "origine": "ZA", "pays_origine": "ZA",
}

CHAMPS = ("ref", "reference", "id", "titre", "title", "employeur",
          "entreprise", "lien", "url", "sans_permis", "lien_accessible")


def construire_kwargs(sig, vocab):
    kwargs, inconnus = {}, []
    for nom, p in sig.parameters.items():
        if nom == "self" or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if nom in vocab:
            kwargs[nom] = vocab[nom]
        elif p.default is p.empty:
            inconnus.append(nom)
    return kwargs, inconnus


def apercu(o):
    if isinstance(o, dict):
        return {k: o.get(k) for k in CHAMPS if o.get(k) is not None}
    return {k: getattr(o, k) for k in CHAMPS if getattr(o, k, None) is not None}


def tester_module(nom_module, etiquette, surcharges=None):
    vocab = dict(VOCAB)
    if surcharges:
        vocab.update(surcharges)
    print(f"\n-> {etiquette} ({nom_module})")
    try:
        mod = importlib.import_module(nom_module)
    except Exception:
        print("  IMPORT IMPOSSIBLE :\n" + tb_court())
        return "import"
    filtre = re.compile(r"(?i)(recher|offre|search|fetch|jobs|lister|resultats)")
    cibles = []
    for _, cls in inspect.getmembers(mod, inspect.isclass):
        if cls.__module__ != mod.__name__:
            continue
        try:
            sig = inspect.signature(cls)
        except (TypeError, ValueError):
            sig = None
        kwargs, inconnus = construire_kwargs(sig, vocab) if sig else ({}, [])
        if inconnus:
            print(f"  classe {cls.__name__} : constructeur non instanciable "
                  f"automatiquement (params {inconnus}) — signature {sig}")
            continue
        try:
            obj = cls(**kwargs)
        except Exception:
            print(f"  classe {cls.__name__} : échec d'instanciation\n" + tb_court())
            continue
        for nm, meth in inspect.getmembers(obj, inspect.ismethod):
            if filtre.search(nm) and not nm.startswith("_"):
                cibles.append((f"{cls.__name__}.{nm}", meth))
    for nm, fn in inspect.getmembers(mod, inspect.isfunction):
        if fn.__module__ == mod.__name__ and filtre.search(nm) and not nm.startswith("_"):
            cibles.append((nm, fn))
    if not cibles:
        publiques = [n for n, o in inspect.getmembers(mod)
                     if not n.startswith("_") and callable(o)]
        print("  aucune méthode évidente (recher/offre/search/fetch) — "
              "callables publics :", publiques[:15])
        return None
    dernier = None
    for nom, fn in cibles:
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            print(f"  {nom} : signature illisible, sauté")
            continue
        kwargs, inconnus = construire_kwargs(sig, vocab)
        if inconnus:
            print(f"  {nom}{sig} : sauté (paramètres inconnus {inconnus})")
            continue
        args_txt = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
        print(f"  appel {nom}({args_txt}) ... (réseau possible, patiente)")
        try:
            res = fn(**kwargs)
        except Exception:
            print("  EXCEPTION pendant l'appel :\n" + tb_court())
            dernier = "exception"
            continue
        try:
            taille = len(res)
        except Exception:
            taille = None
        print(f"  -> type {type(res).__name__}, taille {taille}")
        if isinstance(res, (list, tuple)):
            for o in list(res)[:3]:
                print("     .", apercu(o))
            dernier = taille
        elif taille is not None:
            dernier = taille
    return dernier


def sec_dynamique():
    titre("J. TEST DYNAMIQUE DES SOURCES (hors Streamlit)")
    sys.path.insert(0, str(RACINE))
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    logging.getLogger("streamlit").setLevel(logging.ERROR)
    injectees = 0
    for k, v in lire_env().items():  # reproduire ce que voit l'app (valeurs non affichées)
        if k not in os.environ:
            os.environ[k] = v
            injectees += 1
    print(f"({injectees} variable(s) du .env injectée(s) dans l'environnement du test)")
    try:
        reg = importlib.import_module("app.api.sources.registre")
        rien = True
        for nom, val in vars(reg).items():
            if isinstance(val, dict) and val and all(
                    isinstance(k, str) and len(k) == 2 for k in list(val)[:8]):
                print(f"registre.{nom} = {val}")
                rien = False
        for nom, fn in inspect.getmembers(reg, inspect.isfunction):
            if re.search(r"(?i)pays", nom):
                try:
                    sig = inspect.signature(fn)
                except (TypeError, ValueError):
                    continue
                if not [p for p in sig.parameters.values()
                        if p.default is p.empty]:
                    try:
                        print(f"registre.{nom}() = {fn()}")
                        rien = False
                    except Exception:
                        print(f"registre.{nom}() a levé :\n" + tb_court())
        if rien:
            print("registre importé, mais aucune cartographie pays->sources repérée "
                  "automatiquement")
    except Exception:
        print("import du registre impossible :\n" + tb_court())
    VERDICT["uk_dyn"] = tester_module(
        "app.api.sources.uk_sponsors", "source Royaume-Uni")
    VERDICT["adz_dyn"] = tester_module(
        "app.api.sources.adzuna",
        "source Adzuna générique (test différentiel sur FR)",
        surcharges={"pays": "FR", "country": "FR", "code_pays": "FR", "cc": "FR"})


# ------------------------------------------------------------------ K
def sec_verdict():
    titre("K. LECTURE RAPIDE")
    api = VERDICT.get("api")
    uk = VERDICT.get("uk_dyn")
    if api == "sans_cles":
        print("* Pas d'identifiants Adzuna trouvés -> cause n°1 probable de la page GB")
        print("  vide (uk_sponsors = Adzuna gb INTERSECTION registre sponsors ;")
        print("  sans clés, l'intersection est vide). File d'attente #5 : régénérer")
        print("  les clés sur developer.adzuna.com puis les remettre dans .env sous")
        print("  les noms listés en section C.")
    elif isinstance(api, str) and api.startswith("http_4"):
        print("* Clés Adzuna présentes mais l'API répond " + api.replace("http_", "HTTP "))
        print("  (voir le corps de réponse en section I). Si le message parle")
        print("  d'authentification : clés révoquées après la fuite git -> régénérer")
        print("  (file #5) puis mettre à jour .env.")
    elif api == "ok" and uk in (0, "exception", "import"):
        print(f"* L'API Adzuna répond, mais la source uk_sponsors donne « {uk} »")
        print("  -> regarder la section D (diff avec le .bak) et la trace en section J.")
    elif api == "ok" and isinstance(uk, int) and uk > 0:
        print("* La source uk_sponsors fonctionne HORS Streamlit -> cache Streamlit ou")
        print("  filtre côté ui.py (voir section G). Arrête streamlit (Ctrl-C), relance,")
        print("  puis menu ... > Clear cache si besoin.")
    else:
        print("* Pas de conclusion automatique — colle toute la sortie dans la")
        print("  conversation.")
    if VERDICT.get("patience") is False:
        print("* !! _yorbity_patience ABSENT de ui.py (il n'est plus que dans un .bak ?)")
        print("  -> risque de retour des « database is locked ». À retraiter juste")
        print("  après le point UK.")


def main():
    print("SONDE UK VIDE v1 —", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("(lecture seule : aucun fichier modifié, aucune clé affichée)")
    try:
        sec_environnement()
    except Exception:
        print(tb_court())
    try:
        a_id, a_key = sec_env()
    except Exception:
        a_id = a_key = None
        print(tb_court())
    for fn in (sec_vars_code, sec_uk_sponsors, sec_adzuna_py,
               sec_ui, sec_message, sec_csv):
        try:
            fn()
        except Exception:
            print(tb_court())
    try:
        sec_api_directe(a_id, a_key)
    except Exception:
        print(tb_court())
    try:
        sec_dynamique()
    except Exception:
        print(tb_court())
    try:
        sec_verdict()
    except Exception:
        print(tb_court())
    print("\nFIN — colle TOUTE cette sortie dans la conversation.")


if __name__ == "__main__":
    main()
