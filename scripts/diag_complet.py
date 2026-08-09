#!/usr/bin/env python3
"""
diag_complet.py — Diagnostic COMPLET de Yorbity, auto-porteur, analysable
par n'importe quel LLM local via Ollama.

    python scripts/diag_complet.py                    # rapport complet
    python scripts/diag_complet.py --rapide           # sans requetes reseau
    python scripts/diag_complet.py --llm gpt-oss:120b # + analyse par le LLM
    python scripts/diag_complet.py --llm llama3.2:3b  # analyse rapide

Le rapport est ecrit dans diagnostic_yorbity.md a la racine du projet et
contient l'ARRIERE-PLAN de l'application (architecture, faits etablis, modes
de panne connus) : le LLM n'a besoin d'aucun autre contexte pour raisonner.

Lecture seule. Aucune modification de fichiers ni de base.
"""
from __future__ import annotations

import importlib
import importlib.metadata
import json
import os
import re
import sqlite3
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "app" / "api"))
sys.path.insert(0, str(RACINE))

RAPIDE = "--rapide" in sys.argv
DB = RACINE / "data" / "mobilite.db"
RAPPORT = RACINE / "diagnostic_yorbity.md"

L: list[str] = []          # lignes du rapport
ANOMALIES: list[str] = []  # (gravite, message)


def w(txt: str = "") -> None:
    L.append(txt)
    print(txt)


def anomalie(gravite: str, msg: str) -> None:
    ANOMALIES.append(f"[{gravite}] {msg}")


def section(t: str) -> None:
    w(f"\n## {t}\n")


# =========================================================================== #
ARRIERE_PLAN = """\
# Diagnostic Yorbity — {date}

## ARRIERE-PLAN (contexte pour l'analyste, humain ou LLM)

Yorbity est une application Streamlit (Python) d'aide a la mobilite
internationale : etudes, stages, emplois et metiers specialises a l'etranger,
pour un public principalement africain (Cameroun, Senegal...). L'utilisateur
final est HORS du pays de destination, souvent sans permis de travail.

### Architecture des offres d'emploi
- `app/api/sources/` : REGISTRE d'adaptateurs. Chaque source (site d'emploi)
  implemente le contrat `SourceOffres` (base.py) :
    * collecter(destination, type_projet, mots_cles, limite, lang) -> [Offre]
    * lien_public(dest, type) : URL montrable qui ne rejette pas l'etranger
    * admissible_sans_permis(dest, type) : postulable SANS permis de travail ?
    * lien_accessible_depuis_etranger(dest, type) : le lien s'ouvre-t-il
      pour un visiteur hors du pays ?
  Adaptateurs livres : jobbank_ca (Job Bank Canada), adzuna (19 pays).
  registre.collecter() trie : postulables + liens accessibles d'abord, puis
  catalogues ; il pose `lien_accessible` sur chaque offre (dict).
- `app/api/jobs_api.py` : affichage des offres en direct (fonction afficher()).
  `chercher()` interroge le registre avec cache SQLite 12 h (table jobs_cache),
  repli Adzuna seul si le registre est indisponible. L'ancien code Adzuna est
  conserve sous `_chercher_adzuna()`. Le lien d'une offre n'est montre au
  visiteur que si `lien_accessible` est vrai ; l'admin voit tout.
- `app/api/offres_sync.py` : parametres admin (param/definir_param,
  liens_actifs, descriptions_actives), agent Ollama de validation, verif 404.
  `_ingerer_sources_obsolete()` est VOLONTAIREMENT hors service : la table
  `opportunites` n'a ni colonne description ni reference.
- `app/api/traduction_offres.py` : traduction des offres via Ollama
  (modele OLLAMA_MODEL_OFFRES, defaut llama3.2:3b), cache SQLite dedie
  data/traductions_offres.db. NE PAS confondre avec app/api/traduction.py
  (module i18n du contenu, llama3.3:70b, data/mobilite.db).
- `data/mobilite.db` : table `opportunites` (cartes statiques seedees par
  scripts/seed_mondial.py, index UNIQUE titre+destination+type) et
  `jobs_cache`. La base doit etre en journal_mode=WAL (Streamlit relance le
  script a chaque interaction -> acces concurrents).

### Faits etablis experimentalement (ne pas re-deviner)
- Job Bank : flux Atom /jobsearch/feed/jobSearchRSSfeed. Seul `dkw` filtre
  (teste contre jkw/searchstring/term/q/keyword, tous ignores). `dkw` cherche
  en PLEIN TEXTE et matche le boilerplate "Are you currently a student?" ->
  ne jamais filtrer/scorer sur ce mot seul.
- `fglo=1` = "Canadians and international candidates" : seules offres
  postulables sans permis. `fsrc=21` (Summer Jobs) croise avec fglo=1 -> 0
  offre : AUCUN emploi etudiant canadien n'est ouvert sans permis.
  D'ou : admissible_sans_permis CA = True uniquement pour type "metier".
- Detail d'offre Job Bank : RDFa. employeur=[property=hiringOrganization],
  lieu=addressLocality(+addressRegion), description=[property=description],
  date=[property=datePosted], salaire=[property=baseSalary].
  Pieges : span[property=name] attrape "Government of Canada" ; <time> porte
  une date sans rapport. Reference = id d'URL /jobposting/NNNN (JOB-NNNN).
- Geo-blocage (diag_geoblocage v2) : Adzuna SUBSTITUE le contenu hors du
  domaine national ("Sorry, this job is not available in your region") ->
  lien inutilisable pour l'utilisateur cible ; son API, elle, passe partout.
  Job Bank sert le contenu avec une simple banniere (AVERTI).
- L'UI peut envoyer un domaine generique ("Tous secteurs") comme mot-cle ;
  jobbank_ca._params() le neutralise avant dkw.

### Modes de panne connus
1. "database is locked" : plusieurs processus Streamlit ou journal_mode
   != wal. Correctif : pkill -f streamlit ; PRAGMA journal_mode=WAL.
2. 0 offre Job Bank affichee : (a) mot-cle pollue avant la sanitisation,
   (b) cache jobs_cache contenant [] fige 12 h, (c) exception d'adaptateur
   avalee par registre.collecter (visible en log seulement).
3. Traduction qui rend l'anglais : Ollama eteint, ou modele absent
   (verifier /api/tags), ou collision avec app/api/traduction.py.
4. Doublons dans opportunites : seed_mondial relance sans INSERT OR IGNORE
   (l'index UNIQUE le bloque desormais).
5. Popup "visiting Job Bank from outside Canada" : lien sans fglo=1.
"""

# =========================================================================== #
def env() -> None:
    section("1. Environnement")
    w(f"- Python : {sys.version.split()[0]}  ({sys.executable})")
    w(f"- Racine projet : {RACINE}")
    # module a importer -> nom du paquet pip
    for module, pkg in (("requests", "requests"),
                        ("bs4", "beautifulsoup4"),
                        ("streamlit", "streamlit")):
        try:
            importlib.import_module(module)
        except ImportError:
            w(f"- {pkg} : ABSENT")
            anomalie("HAUTE", f"paquet {pkg} absent (pip install {pkg})")
            continue
        try:
            v = importlib.metadata.version(pkg)
        except Exception:
            v = "version inconnue"
        w(f"- {pkg} : {v}")


def fichiers() -> None:
    section("2. Fichiers et patchs")
    attendus = {
        "app/api/jobs_api.py": {
            "_chercher_adzuna": "patch registre (chercher -> registre)",
            "lien_accessible": "patch lien (masquage geo-bloques)",
            "_toff": "patch traduction des offres",
        },
        "app/api/offres_sync.py": {
            "_ingerer_sources_obsolete": "ingestion en base neutralisee",
        },
        "app/api/sources/base.py": {
            "lien_accessible_depuis_etranger": "contrat v2",
        },
        "app/api/sources/registre.py": {
            "from . import adzuna": "adaptateur adzuna charge",
            "lien_accessible": "tri + champ injecte",
        },
        "app/api/sources/jobbank_ca.py": {"fglo": "filtre international"},
        "app/api/sources/adzuna.py": {"return False": "liens marques bloques"},
        "app/api/traduction_offres.py": {},
        "app/api/traduction.py": {},
    }
    for rel, marqueurs in attendus.items():
        p = RACINE / rel
        if not p.exists():
            w(f"- {rel} : ABSENT")
            anomalie("HAUTE", f"{rel} manquant")
            continue
        src = p.read_text(encoding="utf-8", errors="ignore")
        etats = []
        for m, sens in marqueurs.items():
            ok = m in src
            etats.append(f"{'OK' if ok else 'MANQUE'}:{sens}")
            if not ok:
                anomalie("MOYENNE", f"{rel} : marqueur absent -> {sens}")
        w(f"- {rel} : present" + (f"  [{' | '.join(etats)}]" if etats else ""))


def base_de_donnees() -> None:
    section("3. Base de donnees (data/mobilite.db)")
    if not DB.exists():
        w("- ABSENTE")
        anomalie("HAUTE", "data/mobilite.db introuvable")
        return
    w(f"- taille : {DB.stat().st_size // 1024} Ko")
    try:
        con = sqlite3.connect(DB, timeout=10)
    except Exception as e:
        anomalie("HAUTE", f"ouverture impossible : {e}")
        return
    try:
        jm = con.execute("PRAGMA journal_mode").fetchone()[0]
        w(f"- journal_mode : {jm}")
        if jm.lower() != "wal":
            anomalie("HAUTE", "journal_mode != wal -> 'database is locked' "
                     "sous Streamlit. Correctif : PRAGMA journal_mode=WAL")
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]
        w(f"- tables : {', '.join(sorted(tables))}")

        if "opportunites" in tables:
            n = con.execute("SELECT COUNT(*) FROM opportunites").fetchone()[0]
            par = dict(con.execute(
                "SELECT statut, COUNT(*) FROM opportunites GROUP BY statut"))
            w(f"- opportunites : {n} lignes, par statut {par}")
            dbl = con.execute(
                "SELECT COUNT(*) FROM (SELECT 1 FROM opportunites "
                "GROUP BY titre,destination,type HAVING COUNT(*)>1)"
            ).fetchone()[0]
            if dbl:
                anomalie("MOYENNE", f"{dbl} doublon(s) de carte dans opportunites "
                         "(scripts/nettoyer_offres.py --dedup-carte)")
            idx = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND tbl_name='opportunites'")]
            w(f"- index opportunites : {idx}")
            if not any("unique" in i.lower() or i == "idx_opp_unique" for i in idx):
                anomalie("BASSE", "index UNIQUE absent -> seed_mondial peut "
                         "recreer des doublons (nettoyer_offres.py --index)")

        if "jobs_cache" in tables:
            rows = con.execute(
                "SELECT cle, length(contenu), maj FROM jobs_cache").fetchall()
            vides = [r for r in rows if (r[1] or 0) <= 2]
            w(f"- jobs_cache : {len(rows)} entree(s), dont {len(vides)} VIDE(s)")
            for cle, taille, maj in rows[:12]:
                w(f"    {cle:46} {taille or 0:>6} o  {maj}"
                  + ("   <<< VIDE" if (taille or 0) <= 2 else ""))
            if vides:
                anomalie("HAUTE", f"{len(vides)} entree(s) de cache VIDES figees "
                         "12 h -> 0 offre affichee. Correctif : DELETE FROM jobs_cache")
    finally:
        con.close()


def registre_et_sources() -> None:
    section("4. Registre de sources")
    try:
        from sources import registre
    except Exception as e:
        w(f"- IMPORT IMPOSSIBLE : {e}")
        w("```\n" + traceback.format_exc() + "```")
        anomalie("HAUTE", "le registre ne s'importe pas -> jobs_api retombe "
                 "sur Adzuna seul")
        return
    w(f"- sources : {list(registre.toutes())}")
    for nom in registre.toutes():
        w(f"    {nom:14} active={registre.est_active(nom)}")
        if not registre.est_active(nom):
            anomalie("MOYENNE", f"source {nom} desactivee par l'admin")
    for dest, tp in (("CA", "metier"), ("CA", "emploi"), ("FR", "stage")):
        srcs = registre.sources_pour(dest, tp)
        detail = [
            f"{s.nom}(permis={'non requis' if s.admissible_sans_permis(dest, tp) else 'requis'},"
            f" lien={'ok' if s.lien_accessible_depuis_etranger(dest, tp) else 'bloque'})"
            for s in srcs
        ]
        w(f"- {dest}/{tp:7} -> {detail or 'AUCUNE SOURCE'}")
        if dest == "CA" and tp == "metier" and not any(
                s.nom == "jobbank_ca" for s in srcs):
            anomalie("HAUTE", "jobbank_ca absent du routage CA/metier")


def reseau() -> None:
    section("5. Reseau — sources externes" + (" (saute : --rapide)" if RAPIDE else ""))
    if RAPIDE:
        return
    try:
        import requests
    except ImportError:
        anomalie("HAUTE", "requests absent")
        return

    # Flux Job Bank
    try:
        from sources import jobbank_ca as jb
        src = jb.JobBankCanada()
        brut = src._liste(src._params("metier", None, 5, "en"), timeout=20)
        w(f"- flux Atom Job Bank : {len(brut)} resultat(s) (attendu > 0)")
        if not brut:
            anomalie("HAUTE", "flux Job Bank vide — site en panne ou "
                     "parametres invalides")
        else:
            d = src._detail(brut[0]["url"], jb._session(), 20)
            champs = {k: bool(v) for k, v in d.items()}
            w(f"- detail 1re offre : {champs}")
            if not d.get("entreprise"):
                anomalie("MOYENNE", "selecteur employeur ne matche plus "
                         "(HTML Job Bank a change ?)")
    except Exception as e:
        w(f"- Job Bank : ERREUR {e}")
        anomalie("HAUTE", f"sonde Job Bank en echec : {e}")

    # Adzuna : cles presentes ?
    try:
        import jobs_api
        dispo = jobs_api.disponible()
        w(f"- Adzuna disponible (cles .env) : {dispo}")
        if not dispo:
            anomalie("MOYENNE", "cles ADZUNA_APP_ID / ADZUNA_APP_KEY absentes "
                     "ou invalides dans .env")
    except Exception as e:
        w(f"- jobs_api : ERREUR {e}")
        anomalie("HAUTE", f"jobs_api ne s'importe pas : {e}")


def ollama() -> None:
    section("6. Ollama (traduction et agents)")
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=4)
        r.raise_for_status()
        modeles = [m["name"] for m in r.json().get("models", [])]
        w(f"- joignable, {len(modeles)} modele(s) : {', '.join(modeles)}")
    except Exception as e:
        w(f"- INJOIGNABLE ({e})")
        anomalie("MOYENNE", "Ollama eteint -> traductions rendues en langue "
                 "source. Correctif : ollama serve")
        return
    try:
        import traduction_offres as toff
        w(f"- modele traduction offres : {toff.OLLAMA_MODEL}")
        if toff.OLLAMA_MODEL not in modeles and \
                not any(m.startswith(toff.OLLAMA_MODEL) for m in modeles):
            anomalie("HAUTE", f"modele {toff.OLLAMA_MODEL} introuvable dans "
                     "Ollama -> traductions silencieusement ignorees")
        w(f"- cache traductions : {toff.stats_cache()}")
        if not RAPIDE:
            essai = toff.traduire("Be a part of our mission.", "fr",
                                  langue_source="en")
            w(f"- essai de traduction : {essai!r}")
            if essai.strip().lower().startswith("be a part"):
                anomalie("HAUTE", "la traduction rend l'anglais : modele "
                         "absent ou Ollama en erreur (voir logs)")
    except Exception as e:
        w(f"- traduction_offres : ERREUR {e}")
        anomalie("MOYENNE", f"traduction_offres inutilisable : {e}")


def processus() -> None:
    section("7. Processus")
    try:
        out = subprocess.run(["pgrep", "-fl", "streamlit"],
                             capture_output=True, text=True, timeout=5)
        lignes = [l for l in out.stdout.strip().splitlines() if l]
        w(f"- instances Streamlit : {len(lignes)}")
        for l in lignes[:5]:
            w(f"    {l}")
        if len(lignes) > 1:
            anomalie("HAUTE", f"{len(lignes)} instances Streamlit -> risque "
                     "'database is locked'. Correctif : pkill -f streamlit")
    except Exception as e:
        w(f"- pgrep indisponible ({e})")


def synthese() -> None:
    section("8. ANOMALIES DETECTEES")
    if not ANOMALIES:
        w("Aucune. L'application semble saine.")
        return
    ordre = {"HAUTE": 0, "MOYENNE": 1, "BASSE": 2}
    for a in sorted(ANOMALIES, key=lambda x: ordre.get(x[1:x.index("]")], 3)):
        w(f"- {a}")


# =========================================================================== #
def analyser_avec_llm(modele: str, rapport: str) -> None:
    print(f"\n{'=' * 74}\nANALYSE PAR {modele}\n{'=' * 74}")
    try:
        import requests
    except ImportError:
        print("requests absent — analyse impossible")
        return
    if len(rapport) > 60000:
        rapport = rapport[:30000] + "\n\n[... rapport tronque ...]\n\n" + rapport[-25000:]
    prompt = (
        "Tu es un developpeur Python/Streamlit senior. Voici le rapport de "
        "diagnostic complet d'une application (arriere-plan inclus).\n"
        "1) Liste les problemes par ordre de gravite.\n"
        "2) Pour chacun : cause probable et commande shell de correction.\n"
        "3) Si tout est sain, dis-le et propose la prochaine amelioration.\n"
        "Reponds en francais, de facon concise et actionnable.\n\n"
        "=== RAPPORT ===\n" + rapport
    )
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": modele, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.2, "num_predict": 1600}},
            timeout=600,
        )
        r.raise_for_status()
        print(r.json().get("response", "").strip())
    except Exception as e:
        print(f"Analyse impossible : {e}")
        print("Modeles installes : curl -s localhost:11434/api/tags | "
              "python -m json.tool | grep name")


def main() -> None:
    w(ARRIERE_PLAN.format(date=datetime.now().strftime("%Y-%m-%d %H:%M")))
    env()
    fichiers()
    base_de_donnees()
    registre_et_sources()
    reseau()
    ollama()
    processus()
    synthese()

    rapport = "\n".join(L)
    try:
        RAPPORT.write_text(rapport, encoding="utf-8")
        print(f"\nRapport ecrit : {RAPPORT.relative_to(RACINE)}")
    except Exception as e:
        print(f"\nRapport non ecrit ({e})")

    if "--llm" in sys.argv:
        i = sys.argv.index("--llm")
        modele = sys.argv[i + 1] if i + 1 < len(sys.argv) else "llama3.2:3b"
        analyser_avec_llm(modele, rapport)


if __name__ == "__main__":
    main()
