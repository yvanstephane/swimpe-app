# Diagnostic Yorbity — 2026-07-10 12:21

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


## 1. Environnement

- Python : 3.14.5  (/Users/yvannkoo/mobilite-ia/.venv/bin/python)
- Racine projet : /Users/yvannkoo/mobilite-ia
- requests : 2.34.2
- beautifulsoup4 : 4.15.0
- streamlit : 1.58.0

## 2. Fichiers et patchs

- app/api/jobs_api.py : present  [OK:patch registre (chercher -> registre) | OK:patch lien (masquage geo-bloques) | OK:patch traduction des offres]
- app/api/offres_sync.py : present  [OK:ingestion en base neutralisee]
- app/api/sources/base.py : present  [OK:contrat v2]
- app/api/sources/registre.py : present  [OK:adaptateur adzuna charge | OK:tri + champ injecte]
- app/api/sources/jobbank_ca.py : present  [OK:filtre international]
- app/api/sources/adzuna.py : present  [OK:liens marques bloques]
- app/api/traduction_offres.py : present
- app/api/traduction.py : present

## 3. Base de donnees (data/mobilite.db)

- taille : 3792 Ko
- journal_mode : wal
- tables : config_devises, config_origines, config_params, config_pays, config_projet_pays, config_services, config_tarifs, corridors, destinations, dossiers, eligibilite, jobs_cache, leads, opportunites, origines, projets, reset_codes, security_events, sqlite_sequence, trad_cache, users
- opportunites : 56 lignes, par statut {'a_verifier': 56}
- index opportunites : ['idx_opp_unique']
- jobs_cache : 1 entree(s), dont 0 VIDE(s)
    ca:metier:                                       3265 o  2026-07-10T12:20:42

## 4. Registre de sources

- sources : ['jobbank_ca', 'adzuna']
    jobbank_ca     active=True
    adzuna         active=True
- CA/metier  -> ['jobbank_ca(permis=non requis, lien=ok)', 'adzuna(permis=requis, lien=bloque)']
- CA/emploi  -> ['jobbank_ca(permis=requis, lien=ok)', 'adzuna(permis=requis, lien=bloque)']
- FR/stage   -> ['adzuna(permis=requis, lien=bloque)']

## 5. Reseau — sources externes (saute : --rapide)


## 6. Ollama (traduction et agents)

- joignable, 5 modele(s) : nomic-embed-text:latest, qwen3-coder:30b, gpt-oss:120b, llama3.3:70b-instruct-q4_K_M, llama3.2:3b
- modele traduction offres : llama3.2:3b
- cache traductions : {'fr': 65}

## 7. Processus

- instances Streamlit : 0

## 8. ANOMALIES DETECTEES

Aucune. L'application semble saine.