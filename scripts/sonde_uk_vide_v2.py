#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sonde_uk_vide_v2.py — Yorbity
Suite de la v1. LECTURE SEULE : ne modifie rien, n'écrit rien.
Les chaînes ressemblant à des clés (16+ caractères alphanumériques) sont
MASQUÉES avant affichage. Lancer depuis ~/mobilite-ia, coller TOUTE la sortie.

Objectif : pourquoi la page GB affiche 0 offre alors que clés, CSV et API
sont bons individuellement. Trois pistes : diff patch_fixpack2 sur
uk_sponsors.py, chargement du .env dans le process Streamlit, règles
d'admissibilité par pays d'origine.
"""

import ast
import difflib
import importlib
import inspect
import logging
import os
import re
import socket
import sqlite3
import sys
import traceback
from datetime import datetime
from pathlib import Path

RACINE = Path.cwd()
API = RACINE / "app" / "api"
SRC = API / "sources"
BILAN = {}

socket.setdefaulttimeout(45)  # évite les appels réseau qui pendent


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


def masquer(texte):
    """Masque toute chaîne littérale de 16+ caractères alphanumériques
    (clés API probables) ; sur les lignes sensibles (app_id, app_key,
    secret, token, pass), masque dès 6 caractères."""
    texte = re.sub(r"""(["'])([A-Za-z0-9]{16,})\1""",
                   r"\1<<clé masquée>>\1", texte)
    if re.search(r"(?i)app_?id|app_?key|api_?key|secret|token|passw", texte):
        texte = re.sub(r"""(["'])([A-Za-z0-9]{6,})\1""",
                       r"\1<<masqué>>\1", texte)
    return texte


def afficher_code(chemin, debut=1, fin=None, plafond=240):
    texte = lire(chemin)
    if not texte:
        print(f"{chemin} : ABSENT ou vide")
        return
    lignes = texte.splitlines()
    if debut > len(lignes):
        debut = 1
    fin = fin or len(lignes)
    fin = min(fin, len(lignes))
    total = fin - debut + 1
    print(f"[{Path(chemin).name} — {len(lignes)} lignes, "
          f"affichage {debut}-{fin}]")
    for i in range(debut - 1, fin):
        if i - (debut - 1) >= plafond:
            print(f"   ... tronqué à {plafond} lignes "
                  f"({total - plafond} restantes)")
            break
        print(f"  {i + 1:4d} {masquer(lignes[i])[:118]}")


# ------------------------------------------------------------------ 1
def sec_diff_fixpack2():
    titre("1. DIFF patch_fixpack2 : uk_sponsors.py.bak -> uk_sponsors.py")
    f = SRC / "uk_sponsors.py"
    baks = sorted(SRC.glob("uk_sponsors.py.bak-*"))
    if not f.exists() or not baks:
        print("fichier ou .bak manquant")
        return
    bak = baks[-1]
    avant = lire(bak).splitlines()
    apres = lire(f).splitlines()
    diff = list(difflib.unified_diff(avant, apres,
                                     fromfile=bak.name,
                                     tofile="uk_sponsors.py",
                                     lineterm=""))
    if not diff:
        print("aucune différence (?)")
        return
    for i, lg in enumerate(diff):
        if i >= 200:
            print(f"   ... diff tronqué ({len(diff) - 200} lignes restantes)")
            break
        print("  " + masquer(lg)[:118])


# ------------------------------------------------------------------ 2/3/4
def sec_code():
    titre("2. CONTRAT sources/base.py (complet)")
    afficher_code(SRC / "base.py")
    titre("3. ORCHESTRATEUR jobs_api.py (complet)")
    afficher_code(API / "jobs_api.py")
    titre("4. opportunites_ui.py — autour du rendu des offres (lignes 40-135)")
    afficher_code(API / "opportunites_ui.py", debut=40, fin=135)


# ------------------------------------------------------------------ 5
def sec_env_chargement():
    titre("5. QUI CHARGE LE .env ? + accès clés dans adzuna.py")
    motif = re.compile(r"dotenv|load_dotenv|\.env", re.IGNORECASE)
    trouve = False
    for f in sorted(API.rglob("*.py")):
        if "__pycache__" in f.parts:
            continue
        for i, lg in enumerate(lire(f).splitlines()):
            if motif.search(lg):
                print(f"  {f.relative_to(RACINE)}:{i + 1}: "
                      f"{masquer(lg.strip())[:100]}")
                trouve = True
    if not trouve:
        print("  AUCUNE mention de dotenv/.env dans app/api/*.py "
              "-> le process Streamlit ne voit PAS le contenu du .env")
    print("\n  -- adzuna.py : lignes mentionnant app_id / app_key "
          "(clés masquées) --")
    for i, lg in enumerate(lire(SRC / "adzuna.py").splitlines()):
        if re.search(r"(?i)app_?id|app_?key", lg):
            print(f"  {i + 1:4d} {masquer(lg.strip())[:110]}")
    print("\n  -- uk_sponsors.py : lignes mentionnant app_id / app_key "
          "(clés masquées) --")
    for i, lg in enumerate(lire(SRC / "uk_sponsors.py").splitlines()):
        if re.search(r"(?i)app_?id|app_?key", lg):
            print(f"  {i + 1:4d} {masquer(lg.strip())[:110]}")


# ------------------------------------------------------------------ 6
def sec_db():
    titre("6. BASE SQLITE : admissibilité + jobs_cache (lecture seule)")
    chemin = (RACINE / "data" / "mobilite.db").as_posix()
    try:
        con = sqlite3.connect(f"file:{chemin}?mode=ro", uri=True, timeout=30)
    except Exception:
        print(tb_court())
        return
    try:
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        print("tables :", ", ".join(tables))
        for t in tables:
            if re.search(r"(?i)elig|admis|regle", t):
                print(f"\n  -- table {t} --")
                cols = [c[1] for c in con.execute(f"PRAGMA table_info({t})")]
                print("  colonnes :", cols)
                for row in con.execute(f"SELECT * FROM {t} LIMIT 40"):
                    print("   .", row)
        if "jobs_cache" in tables:
            cols = [c[1] for c in con.execute("PRAGMA table_info(jobs_cache)")]
            n = con.execute("SELECT COUNT(*) FROM jobs_cache").fetchone()[0]
            print(f"\n  jobs_cache : {n} ligne(s) — colonnes {cols}")
            col_pays = next((c for c in cols
                             if c in ("pays", "dest", "destination")), None)
            if col_pays and n:
                for row in con.execute(
                        f"SELECT {col_pays}, COUNT(*) FROM jobs_cache "
                        f"GROUP BY {col_pays}"):
                    print("   .", row)
    finally:
        con.close()


# ------------------------------------------------------------------ 7/8
VOCAB = {
    "dest": "GB", "destination": "GB", "code_dest": "GB",
    "pays": "GB", "country": "GB", "code_pays": "GB", "cc": "GB",
    "metier": "electrician", "poste": "electrician", "what": "electrician",
    "query": "electrician", "q": "electrician", "titre": "electrician",
    "terme": "electrician", "recherche": "electrician", "mot": "electrician",
    "origine": "ZA", "code_orig": "ZA", "pays_origine": "ZA", "orig": "ZA",
    "type": "metier", "type_offre": "metier", "categorie": "metier",
    "types_live": ["metier"], "types": ["metier"],
    "limite": 25, "limit": 25, "max_resultats": 25, "nb": 25, "n": 25,
    "page": 1, "langue": "fr", "lang": "fr", "domaine": "",
    "admin": False, "visiteur": True,
}

CHAMPS = ("ref", "reference", "id", "titre", "title", "employeur",
          "entreprise", "lien", "url", "sans_permis", "lien_accessible",
          "source", "pays")

INTERDIT = re.compile(r"(?i)(enregist|sauv|ecri|maj_|update|delete|suppr|"
                      r"purge|telecharg|download|insert|drop|reset|init)")
PRIORITAIRE = re.compile(r"(?i)(pour|offre|cherch|recher|live|search|"
                         r"collect|flux|trouv|list|dispo)")


def construire_kwargs(sig):
    kwargs, inconnus = {}, []
    for nom, p in sig.parameters.items():
        if nom == "self" or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if nom in VOCAB:
            kwargs[nom] = VOCAB[nom]
        elif p.default is p.empty:
            inconnus.append(nom)
    return kwargs, inconnus


def apercu(o):
    if isinstance(o, dict):
        return {k: o.get(k) for k in CHAMPS if o.get(k) is not None}
    return {k: getattr(o, k) for k in CHAMPS if getattr(o, k, None) is not None}


def appeler(nom, fn, deja):
    """Appelle fn si sa signature est satisfiable ; retourne taille ou étiquette."""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        print(f"    {nom} : signature illisible, sauté")
        return None
    if INTERDIT.search(nom):
        print(f"    {nom}{sig} : sauté (nom évoquant une écriture)")
        return None
    kwargs, inconnus = construire_kwargs(sig)
    if inconnus:
        print(f"    {nom}{sig} : sauté (paramètres inconnus {inconnus})")
        return None
    if len(deja) >= 4:
        print(f"    {nom}{sig} : sauté (plafond d'appels atteint)")
        return None
    deja.append(nom)
    args_txt = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    print(f"    appel {nom}({args_txt}) ...")
    try:
        res = fn(**kwargs)
    except Exception:
        print("    EXCEPTION :\n" + tb_court())
        return "exception"
    try:
        taille = len(res)
    except Exception:
        taille = None
    print(f"    -> {type(res).__name__}"
          + (f", taille {taille}" if taille is not None else f" = {res!r}"))
    if isinstance(res, (list, tuple)):
        for o in list(res)[:3]:
            print("       .", apercu(o))
        return taille
    if isinstance(res, bool):
        return res
    return taille


def purger_modules():
    for k in list(sys.modules):
        if (k == "app" or k.startswith("app.")
                or k == "sources" or k.startswith("sources.")
                or k in ("jobs_api", "i18n", "registre")):
            sys.modules.pop(k, None)


def importer(nom_pkg, nom_plat):
    """Essaie app.api.<x> puis <x> avec app/api dans le path."""
    try:
        return importlib.import_module(nom_pkg), nom_pkg
    except Exception:
        pass
    if str(API) not in sys.path:
        sys.path.insert(0, str(API))
    return importlib.import_module(nom_plat), nom_plat


def passe(numero, libelle, injecter):
    titre(f"{numero}. PASSE {libelle}")
    resume = {"uk": None, "dispo": None}
    if injecter:
        n = 0
        for brute in lire(RACINE / ".env").splitlines():
            s = brute.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            if s.startswith("export "):
                s = s[len("export "):]
            k, v = s.split("=", 1)
            k = k.strip()
            if k not in os.environ:
                os.environ[k] = v.strip().strip('"').strip("'")
                n += 1
        print(f"({n} variable(s) du .env injectée(s))")
    else:
        presentes = [k for k in ("ADZUNA_APP_ID", "ADZUNA_APP_KEY")
                     if k in os.environ]
        print(f"(environnement tel quel — ADZUNA dans os.environ : "
              f"{presentes or 'aucune'})")
    purger_modules()
    sys.path.insert(0, str(RACINE))
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    logging.getLogger("streamlit").setLevel(logging.ERROR)

    # registre -> sources_pour('GB','metier')
    try:
        reg, style = importer("app.api.sources.registre", "sources.registre")
        print(f"registre importé ({style})")
    except Exception:
        print("import registre impossible :\n" + tb_court())
        return resume
    try:
        srcs = reg.sources_pour("GB", "metier")
        print("sources_pour('GB','metier') ->",
              [f"{type(s).__name__}(nom={getattr(s, 'nom', '?')})"
               for s in srcs])
    except Exception:
        print("sources_pour a levé :\n" + tb_court())
        srcs = []
    for s in srcs:
        print(f"  objet {type(s).__name__} — méthodes publiques :")
        meths = [(n, m) for n, m in inspect.getmembers(s, inspect.ismethod)
                 if not n.startswith("_")]
        for n, m in meths:
            try:
                print(f"    . {n}{inspect.signature(m)}")
            except (TypeError, ValueError):
                print(f"    . {n}(?)")
        meths.sort(key=lambda nm: 0 if PRIORITAIRE.search(nm[0]) else 1)
        deja = []
        for n, m in meths:
            r = appeler(f"{type(s).__name__}.{n}", m, deja)
            if isinstance(r, int) and not isinstance(r, bool):
                if resume["uk"] is None or r > resume["uk"]:
                    resume["uk"] = r
            elif r == "exception" and resume["uk"] is None:
                resume["uk"] = "exception"

    # jobs_api
    try:
        ja, style = importer("app.api.jobs_api", "jobs_api")
        print(f"\njobs_api importé ({style}) — fonctions publiques :")
    except Exception:
        print("\nimport jobs_api impossible :\n" + tb_court())
        return resume
    fonctions = [(n, f) for n, f in inspect.getmembers(ja, inspect.isfunction)
                 if f.__module__ == ja.__name__ and not n.startswith("_")]
    for n, f in fonctions:
        try:
            print(f"  . {n}{inspect.signature(f)}")
        except (TypeError, ValueError):
            print(f"  . {n}(?)")
    def nb_requis(f):
        try:
            return len([p for p in inspect.signature(f).parameters.values()
                        if p.default is p.empty])
        except (TypeError, ValueError):
            return 99
    fonctions.sort(key=lambda nf: (
        nb_requis(nf[1]),
        0 if PRIORITAIRE.search(nf[0]) else 1))
    deja = []
    for n, f in fonctions:
        r = appeler(f"jobs_api.{n}", f, deja)
        if n == "disponible":
            resume["dispo"] = r
        elif isinstance(r, int) and not isinstance(r, bool):
            if resume["uk"] is None or r > resume["uk"]:
                resume["uk"] = r
    return resume


# ------------------------------------------------------------------ 9
def sec_theme():
    titre("9. AU PASSAGE : theme_pays « 'accent' » (erreur vue au démarrage)")
    f = API / "theme_pays.py"
    texte = lire(f)
    if not texte:
        print("theme_pays.py ABSENT")
        return
    lignes = texte.splitlines()
    montre = 0
    for i, lg in enumerate(lignes):
        if "accent" in lg:
            print(f"  {i + 1:4d} {masquer(lg.strip())[:110]}")
            montre += 1
        if montre >= 12:
            print("  ... (tronqué)")
            break
    if not montre:
        print("  aucune ligne contenant 'accent' — la clé est demandée "
              "ailleurs (grep manuel plus tard)")


# ------------------------------------------------------------------ 10
def sec_verdict(p1, p2):
    titre("10. LECTURE RAPIDE")
    def fmt(x):
        return "?" if x is None else x
    print(f"* passe SANS .env : offres GB = {fmt(p1['uk'])}, "
          f"jobs_api.disponible() = {fmt(p1['dispo'])}")
    print(f"* passe AVEC .env : offres GB = {fmt(p2['uk'])}, "
          f"jobs_api.disponible() = {fmt(p2['dispo'])}")
    u1, u2 = p1["uk"], p2["uk"]
    if isinstance(u2, int) and u2 > 0 and (u1 in (0, "exception", None)):
        print("=> Le pipeline marche AVEC le .env mais pas sans :")
        print("   le process Streamlit ne charge pas le .env alors que")
        print("   uk_sponsors lit désormais les clés via os.getenv")
        print("   (probable effet patch_fixpack2, voir diff section 1).")
        print("   Correctif attendu : load_dotenv au démarrage de l'app.")
    elif isinstance(u1, int) and u1 > 0 and isinstance(u2, int) and u2 > 0:
        print("=> Le pipeline renvoie des offres dans les deux passes :")
        print("   le zéro vient de la couche UI/filtres (admissibilité")
        print("   par pays d'origine ? voir sections 4 et 6).")
    elif u1 in (0, "exception", None) and u2 in (0, "exception", None):
        print("=> Le pipeline sort 0/exception même avec le .env :")
        print("   voir le diff section 1 et les traces des passes.")
    else:
        print("=> Cas non tranché automatiquement — tout coller dans la")
        print("   conversation.")


def main():
    print("SONDE UK VIDE v2 —",
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("(lecture seule — clés masquées à l'affichage ; la passe AVEC .env")
    print(" fait de vrais appels réseau : jusqu'à ~1 min)")
    for fn in (sec_diff_fixpack2, sec_code, sec_env_chargement, sec_db):
        try:
            fn()
        except Exception:
            print(tb_court())
    try:
        p1 = passe(7, "SANS injection .env (ce que voit Streamlit au départ)",
                   injecter=False)
    except Exception:
        print(tb_court())
        p1 = {"uk": None, "dispo": None}
    try:
        p2 = passe(8, "AVEC injection .env (référence)", injecter=True)
    except Exception:
        print(tb_court())
        p2 = {"uk": None, "dispo": None}
    for fn in (sec_theme,):
        try:
            fn()
        except Exception:
            print(tb_court())
    try:
        sec_verdict(p1, p2)
    except Exception:
        print(tb_court())
    print("\nFIN — colle TOUTE cette sortie dans la conversation.")


if __name__ == "__main__":
    main()
