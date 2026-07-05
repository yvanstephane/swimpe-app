# PLAN DIRECTEUR — Plateforme IA de Mobilité Internationale
### Version 1.0 — Document vivant, conçu pour être maintenu par des LLM locaux (Ollama) sur macOS
### Dernière mise à jour : 2026-07-04

---

## 0. COMMENT UTILISER CE DOCUMENT

Ce fichier est la **source de vérité** du projet. Il est conçu pour que tes LLM locaux
(via Ollama, LM Studio ou llama.cpp) puissent :
1. Lire ce plan (`cat PLAN_MOBILITE_IA.md`)
2. Exécuter la prochaine tâche non cochée de la roadmap (§9)
3. Mettre à jour ce fichier eux-mêmes (cocher les tâches, ajouter des notes dans §12 — Journal)

Convention de mise à jour automatique :
- Chaque tâche a un ID unique (ex : `T-021`).
- Un LLM local ne modifie JAMAIS les sections 1 à 8 sans validation humaine ; il ne
  touche qu'aux cases `[ ]` → `[x]` et au Journal (§12).
- Toute modification passe par git : `git add PLAN_MOBILITE_IA.md && git commit -m "T-021 done"`.

---

## 1. VISION

Un écosystème unique qui accompagne une personne de son projet d'études jusqu'à son
insertion professionnelle et son installation : orientation → formations → universités →
bourses → candidatures → visa → logement → installation → jobs étudiants → stages →
premier emploi → immigration → famille → carrière.

**Positionnement** : ni une agence, ni un simple annuaire. Un **assistant IA de mobilité**
qui agrège, structure et personnalise l'information de dizaines de plateformes, avec un
accompagnement automatisé de bout en bout. Premier marché : **Afrique francophone → France**
(Gabon, Cameroun, Sénégal, Côte d'Ivoire, Congo…), là où la demande est massive et
l'offre fragmentée.

---

## 2. ÉTUDE CONCURRENTIELLE (recherches juillet 2026)

### 2.1 Recrutement étudiant international / candidatures
| Acteur | Modèle | À retenir |
|---|---|---|
| **ApplyBoard** | Plateforme unique étudiants + agents + écoles ; +1 200 établissements partenaires, +4 000 partenaires recruteurs (Canada, USA, UK, Australie). Utilise les données ouvertes visa (IRCC) pour estimer les chances d'acceptation. | Revenus = commissions versées par les écoles (10–20 % des frais de scolarité 1re année, standard du secteur). N° 1 mondial du trafic. |
| **Studyportals** (Mastersportal, Bachelorsportal…) | Annuaire mondial de formations, ~3,4 M utilisateurs/mois sur Mastersportal. | Modèle : leads + publicité payée par les universités. |
| **IDP / Edvoy / CanApply / Craydel** | Agents digitalisés ; CanApply se positionne "IA". | La couche IA est le nouveau champ de bataille. |
| **Campus France (Études en France)** | Procédure OBLIGATOIRE pour 40–70+ pays dont le Gabon ; ~350 établissements connectés ; frais de dossier ~70 000–85 000 FCFA en Afrique de l'Ouest/Centrale, non remboursables ; calendrier strict (vœux janv.–mars, réponses avril, choix mai). | ⚠️ On ne peut PAS la remplacer ni l'accélérer (Campus France le dit explicitement). Notre valeur = préparer un dossier béton AVANT et AUTOUR de la procédure. |

### 2.2 Bourses
| Acteur | À retenir |
|---|---|
| **Campus Bourses** (Campus France) | Annuaire officiel : bourses des États, collectivités, entreprises, fondations, établissements ; filtres nationalité/domaine/niveau. |
| **Scholarships.com** | Base géante (millions d'entrées), filtres par profil ; gratuit + emails. |
| **Fastweb, InternationalScholarships.com, Peterson's, Fulbright/Erasmus+** | Bases massives, surtout US/anglophone. Le créneau "bourses pour Afrique francophone, en français, personnalisé par profil" est SOUS-SERVI. |

### 2.3 Logement étudiant
| Acteur | Modèle économique (précieux pour notre pricing) |
|---|---|
| **Studapart** | 1re plateforme française, +120 000 logements vérifiés, partenariats avec 160+ écoles (clé du succès), garantie loyers impayés Allianz. Rachetée à 55 % par HousingAnywhere. |
| **HousingAnywhere** | Commission ~25 % du 1er mois de loyer côté propriétaire + 150–250 € côté locataire. Réservation 100 % en ligne sans visite. |
| **Uniplaces, Spotahome** | Annonces vérifiées, contrats flexibles, sans garant. |
| CROUS / résidences | Canal public, à référencer gratuitement. |

### 2.4 Jobs étudiants / stages / premier emploi
- **Institutionnels (gratuits, à agréger)** : Jobaviz (CROUS, ~70 000 annonces), 1jeune1solution (gouv, 15–30 ans, jobs + stages), France Travail (400 000+ offres, API publique), CIDJ, alternance.emploi.gouv.fr.
- **Privés** : JobTeaser (intégré aux écoles), Indeed, LinkedIn, StudentJob, Jobmania, Side, Welcome to the Jungle.
- Enseignement : personne n'agrège ces sources **pour le profil spécifique "étudiant international"** (droit au travail limité à 964 h/an, besoin d'employeurs habitués aux titres de séjour). C'est notre angle.

### 2.5 Visa / finance / installation
| Acteur | Prix constatés (repères de facturation) |
|---|---|
| **Studely** | AVI (attestation de virement irrévocable, preuve des 7 380 €/an exigés) ≈ **470 €** en 48 h ; pack "Serenity" (AVI + 3 assurances + compte de paiement) ≈ **660 €** ; 15 agences en Afrique ; adossé à des banques françaises. |
| **Ready Study Go** | AVI + accompagnement ≈ **460 €**. |
| **Boundless** (US) | Immigration guidée par logiciel + avocats — le modèle "tech + expert humain" à imiter. |
| **CIBTvisas** | Kits visa personnalisés par programme, B2B écoles. |

### 2.6 Trous dans le marché (notre opportunité)
1. Aucune plateforme ne couvre **tout le parcours** (études → emploi → immigration) : chacun fait un maillon.
2. L'Afrique francophone est servie par des agences opaques et chères, peu digitalisées.
3. Personne n'offre un **assistant IA en français** qui connaît à la fois la procédure Études en France, les bourses, le logement ET le droit au travail étudiant.
4. Les modèles économiques existants (commission écoles, commission loyer, frais AVI, abonnements B2B) sont **combinables** — voir §8.

### 2.7 Garde-fous légaux (IMPORTANT, à respecter dans tout le produit)
- Campus France précise qu'un intermédiaire payant ne facilite ni l'admission ni le visa → on vend de la **préparation, de l'information et de l'organisation**, jamais une promesse de résultat.
- Conseil en immigration = activité réglementée dans plusieurs pays (Canada : consultants agréés ; France : avocats/associations). Le module immigration reste **informatif** avec renvoi systématique aux sources officielles (France-Visas, service-public.fr, ANEF).
- Scraping : privilégier les **API et données ouvertes** ; respecter robots.txt et CGU ; ne jamais automatiser de comptes sur les plateformes tierces (EEF, Parcoursup).
- RGPD : données de mineurs (lycéens) → consentement parental, minimisation, hébergement identifié.

---

## 3. ARCHITECTURE TECHNIQUE 100 % LOCALE (macOS)

### 3.1 Principe
Tout tourne d'abord sur ton Mac : développement, ingestion de données, IA, base de
connaissances. Le passage en ligne (VPS) n'arrive qu'en Phase 4.

```
┌─────────────────────────── Mac (Apple Silicon) ───────────────────────────┐
│                                                                            │
│  Ollama (serveur local :11434)                                             │
│   ├── qwen2.5:14b ou llama3.1:8b  → agent principal / rédaction            │
│   ├── mistral / mistral-nemo      → extraction structurée, classification  │
│   └── nomic-embed-text            → embeddings (RAG)                       │
│                                                                            │
│  Base de connaissances                                                     │
│   ├── SQLite (données structurées : formations, bourses, offres, users)    │
│   └── ChromaDB (vecteurs : fiches pays, guides visa, FAQ)                  │
│                                                                            │
│  Pipelines Python (FastAPI + scripts)                                      │
│   ├── collectors/   → API & données ouvertes (France Travail, ONISEP,      │
│   │                   data.gouv, Erasmus+, flux RSS bourses…)              │
│   ├── normalizers/  → nettoyage, dédoublonnage, schéma commun              │
│   ├── rag/          → indexation Chroma + retrieval                        │
│   └── agents/       → orchestration des LLM (prompts §10)                  │
│                                                                            │
│  Interface                                                                 │
│   ├── Phase 1 : CLI (typer) + Streamlit local                              │
│   └── Phase 3 : Next.js (web) → déploiement VPS                            │
│                                                                            │
│  Automatisation : Makefile + launchd (cron macOS) + git                    │
└────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Installation (commandes à exécuter une fois)
```bash
# 1. Outils de base
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git python@3.12 sqlite node ollama

# 2. Modèles locaux (adapter à ta RAM : 16 Go → 8b ; 32 Go+ → 14b)
ollama pull qwen2.5:14b        # ou llama3.1:8b si RAM limitée
ollama pull mistral            # extraction JSON rapide
ollama pull nomic-embed-text   # embeddings

# 3. Projet
mkdir -p ~/mobilite-ia && cd ~/mobilite-ia && git init
python3 -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn typer streamlit chromadb requests \
            beautifulsoup4 pydantic feedparser python-dotenv httpx pandas

# 4. Structure
mkdir -p app/{collectors,normalizers,rag,agents,api,billing} data/{raw,clean,chroma} docs scripts
cp /chemin/vers/PLAN_MOBILITE_IA.md docs/
```

### 3.3 Makefile (le "cerveau" des commandes — le plan se met à jour depuis ici)
```makefile
# ~/mobilite-ia/Makefile
plan:            ## Affiche les prochaines tâches non cochées
	@grep -n "\[ \] T-" docs/PLAN_MOBILITE_IA.md | head -5

collect:         ## Lance tous les collecteurs de données
	.venv/bin/python -m app.collectors.run_all

index:           ## Ré-indexe la base RAG
	.venv/bin/python -m app.rag.build_index

agent:           ## Lance l'agent local sur la prochaine tâche du plan
	.venv/bin/python -m app.agents.executor --plan docs/PLAN_MOBILITE_IA.md

chat:            ## Assistant conversationnel local (test produit)
	.venv/bin/python -m app.agents.chat

ui:              ## Interface Streamlit locale
	.venv/bin/streamlit run app/api/ui.py

update-plan:     ## Coche une tâche et commit (usage: make update-plan T=T-003)
	.venv/bin/python scripts/check_task.py $(T) && \
	git add docs/PLAN_MOBILITE_IA.md && git commit -m "$(T) terminé"

backup:          ## Sauvegarde chiffrée de data/
	tar czf - data | openssl enc -aes-256-cbc -pbkdf2 -out backups/data-$$(date +%F).tgz.enc
```
Mise à jour automatique quotidienne (launchd) : un job à 6 h lance `make collect index`
et journalise dans §12 via `scripts/append_journal.py`.

### 3.4 Sécurité (règles non négociables)
- Données utilisateurs chiffrées au repos : FileVault activé + `backup` chiffré (ci-dessus).
- Aucun secret en clair : `.env` (jamais commité, `.gitignore` dès le premier commit).
- Les LLM locaux ne reçoivent JAMAIS de documents d'identité bruts : on stocke des
  métadonnées ("passeport ✔ vérifié le…"), les fichiers restent dans un dossier chiffré.
- Journal d'accès : chaque lecture de dossier utilisateur est loggée (SQLite `audit_log`).
- Quand on passera en ligne : hébergement UE, HTTPS, authentification forte, mentions
  RGPD, consentement parental pour les mineurs.

---

## 4. LES 15 MODULES — SPÉCIFICATIONS D'IMPLÉMENTATION

Chaque module = 1 dossier `app/modules/mXX_nom/` + 1 table SQLite + 1 collection Chroma
si besoin. Ordre de construction = ordre de valeur pour le client Afrique → France.

| # | Module | MVP local (Phase 1–2) | Sources de données prioritaires |
|---|---|---|---|
| M1 | Orientation intelligente | Questionnaire CLI/Streamlit → profil JSON (nationalité, résidence, diplômes, notes, langues, budget, objectifs) | — (données saisies) |
| M2 | Recherche universités/formations | Base des ~350 établissements connectés EEF + catalogue ONISEP + licences/masters (données ouvertes ESR sur data.gouv.fr) ; filtres coût/langue/niveau/ville | data.enseignementsup-recherche.gouv.fr, ONISEP open data, trouvermonmaster.gouv.fr, Parcoursup open data |
| M3 | Moteur de bourses | Ingestion Campus Bourses + pages bourses des ambassades + fondations + Erasmus+ ; matching par nationalité/niveau/domaine | campusbourses.campusfrance.org, sites gouvernementaux, flux RSS |
| M4 | Assistant candidature | Le LLM local relit CV/lettre, vérifie la checklist EEF (bulletins scannés, projet motivé), simule l'entretien Campus France (15 min, questions type) | Guides officiels Campus France Gabon |
| M5 | Assistant visa | Checklist France-Visas par nationalité ; calcul des 7 380 € (615 €/mois) ; comparateur AVI (Studely 470 €, RSG 460 €…) | france-visas.gouv.fr |
| M6 | Logement | Agrégateur d'annonces publiques (CROUS, résidences) + guides ; renvoi affilié vers Studapart/Uniplaces plus tard | trouverunlogement.lescrous.fr |
| M7 | Jobs étudiants | Agrégation API France Travail + Jobaviz + 1jeune1solution, filtrées "compatible étudiant étranger" (≤ 964 h/an) | API francetravail.io (gratuite) |
| M8 | Stages | API France Travail (contrat stage) + 1jeune1solution | idem |
| M9 | Premier emploi | Matching CV ↔ offres, simulation salaire, prépa entretien (LLM local) | idem + APEC open data |
| M10 | Immigration (informatif) | Fiches par parcours : APS/carte "recherche d'emploi", passage étudiant→salarié, regroupement familial — TOUJOURS avec lien source officielle + date de vérification | service-public.fr, ANEF, France-Visas |
| M11 | Tableau de bord | Vue candidatures/échéances/documents/tâches (Streamlit puis Next.js) | interne |
| M12 | Assistant IA conversationnel | RAG sur toute la base (Chroma) + profil M1 ; répond en citant ses sources | interne |
| M13 | Espace recruteurs | Phase 5 (post-lancement) | — |
| M14 | Portail universités | Phase 5 | — |
| M15 | Portail gouvernements/organismes | Phase 6 | — |

Règle d'or produit : **chaque réponse de l'IA cite sa source et sa date de fraîcheur**
("Vérifié le 04/07/2026 sur france-visas.gouv.fr"). C'est notre différenciateur confiance.

---

## 5. PIPELINE DE DONNÉES (le nerf de la guerre)

1. **Collecte** (`app/collectors/`) — un script par source, sortie JSON brut dans `data/raw/`.
   Priorité aux API/open data (légal, stable) : France Travail, ONISEP, data.gouv,
   Erasmus+, flux RSS de bourses. Le HTML n'est parsé que si CGU/robots.txt le permettent.
2. **Normalisation** (`app/normalizers/`) — schémas Pydantic communs :
   `Formation`, `Bourse`, `OffreEmploi`, `Logement`, `FicheVisa`. Dédoublonnage par hash.
3. **Stockage** — SQLite (`data/mobilite.db`) pour le structuré ; Chroma pour le textuel.
4. **Fraîcheur** — chaque enregistrement porte `collected_at` + `source_url`. Un job
   quotidien marque "à re-vérifier" tout ce qui a plus de 30 jours (90 pour les fiches visa).
5. **Contrôle qualité par LLM** — mistral relit les entrées et signale les champs
   incohérents (montant de bourse absurde, deadline passée…).

---

## 6. RÔLE DES LLM LOCAUX (division du travail)

| Tâche | Modèle | Pourquoi |
|---|---|---|
| Chat utilisateur, lettres, rapports | qwen2.5:14b / llama3.1:8b | Bon français, raisonnement |
| Extraction JSON depuis pages/documents | mistral | Rapide, suit les formats |
| Embeddings RAG | nomic-embed-text | Léger, efficace |
| Auto-maintenance du plan (executor) | qwen2.5:14b | Lit §9, exécute, coche, journalise |

Limites assumées : un modèle 8–14b hallucine sur les faits réglementaires → **le RAG est
obligatoire** pour tout ce qui touche visa/immigration/bourses ; sans passage retrouvé
dans la base, l'agent répond "je ne sais pas, voici la source officielle à consulter".

---

## 7. UX / ATTRACTIVITÉ

- Mobile-first (la cible utilise surtout un téléphone) ; en Phase 1, Streamlit suffit pour tester.
- Parcours guidé type "GPS" : l'utilisateur voit toujours *où il en est* (frise M1→M10)
  et *la prochaine action* — c'est le tableau de bord M11.
- Ton : clair, tutoiement, zéro jargon administratif non expliqué.
- Preuve sociale : compteurs (bourses référencées, formations indexées), témoignages.
- Gratuit généreux (recherche + checklists) / payant sur l'accompagnement (voir §8) :
  c'est le modèle qui a fait le succès des leaders.

---

## 8. MODÈLE ÉCONOMIQUE ET GRILLE DE FACTURATION

### 8.1 Principe : facturer au SERVICE (à l'acte), avec des packs
Repères marché : AVI seule 460–470 € ; pack Studely Serenity 660 € ; agences
d'accompagnement Afrique facturent souvent 300–800 € le dossier complet ; frais Campus
France ~70–85 000 FCFA (≈ 107–130 €) restent à la charge de l'étudiant.

### 8.2 Grille (exemple cible Gabon/Afrique centrale — 1 € ≈ 656 FCFA)
| Code | Service | Contenu | Prix indicatif |
|---|---|---|---|
| S1 | **Rapport d'orientation IA** | Profil complet + 10 formations compatibles (dont 3 "sécurité") + estimation budget + calendrier personnalisé | 15 000 FCFA (~23 €) |
| S2 | **Pack "Trouver mon université en France"** (ex. lycéen au Gabon) | S1 + sélection fine des 3 vœux EEF (établissements connectés uniquement) + argumentaire par vœu + checklist des justificatifs (bulletins, scans conformes) | 35 000 FCFA (~53 €) |
| S3 | **Dossier béton** | Relecture/optimisation lettre de motivation + CV + projet d'études (3 itérations) | 25 000 FCFA (~38 €) |
| S4 | **Simulation entretien Campus France** | 2 sessions de simulation IA + débrief + fiches réponses | 15 000 FCFA (~23 €) |
| S5 | **Pack Visa serein** | Checklist France-Visas personnalisée + plan de preuve des ressources (7 380 €) + comparateur AVI + suivi des rendez-vous | 20 000 FCFA (~30 €) |
| S6 | **Recherche bourses ciblée** | Rapport des bourses éligibles (nationalité/niveau/domaine) + calendrier + aide au dossier pour 2 bourses | 20 000 FCFA (~30 €) |
| S7 | **Pack installation** | Logement (dossier locataire + candidatures CROUS/plateformes) + banque + assurance + transport | 25 000 FCFA (~38 €) |
| S8 | **Pack emploi/stage** | CV français + profil LinkedIn + 20 offres matchées + prépa entretien | 25 000 FCFA (~38 €) |
| P1 | **Pack COMPLET "Du lycée au campus"** (S1→S5) | | 89 000 FCFA (~136 €) au lieu de 110 000 |
| P2 | **Abonnement Premium** | Assistant IA illimité + tableau de bord + alertes bourses/offres | 5 000 FCFA/mois (~7,6 €) |

### 8.3 Revenus B2B (à partir de la Phase 5)
- Universités/écoles : abonnement de visibilité + commission par inscrit (standard 10–15 %
  des frais 1re année pour le privé ; pour le public français, plutôt un forfait de promotion).
- Entreprises : publication d'offres + accès CVthèque (modèle JobTeaser).
- Affiliation : AVI (Studely & co reversent des commissions d'apporteur), logement
  (Studapart/Uniplaces), assurances, banques, billets d'avion.
- Organismes de bourses : diffusion sponsorisée d'appels à candidatures.

### 8.4 Encaissement (réalité terrain Afrique)
Mobile Money (Airtel Money, Moov Money au Gabon), virement, cash via partenaires ;
en ligne : CinetPay / Flutterwave / Stripe selon pays. Facture PDF générée par
`app/billing/invoice.py` (numérotation continue, TVA selon statut juridique choisi).

### 8.5 Éthique tarifaire (protection de la marque)
Jamais de "visa garanti", jamais de "admission garantie". Remboursement partiel si un
livrable n'est pas fourni. Prix affichés, pas de frais cachés — c'est exactement
l'inverse des agences qui ont mauvaise réputation, et c'est notre argument n°1.

---

## 9. ROADMAP EXÉCUTABLE (les LLM locaux cochent ici)

### Phase 0 — Fondations (semaine 1)
- [ ] T-001 Installer la stack §3.2 et vérifier `ollama run qwen2.5:14b "bonjour"`
- [ ] T-002 Créer le repo git, `.gitignore` (.env, data/, backups/), premier commit
- [ ] T-003 Créer le Makefile §3.3 et `make plan` fonctionnel
- [ ] T-004 Créer les schémas Pydantic (Formation, Bourse, OffreEmploi, FicheVisa, Profil)
- [ ] T-005 Créer SQLite `data/mobilite.db` avec les tables + table `audit_log`

### Phase 1 — Données & RAG (semaines 2–4)
- [ ] T-010 Collector : liste des établissements connectés EEF (PDF officiel → JSON)
- [ ] T-011 Collector : catalogue formations (open data ESR/ONISEP)
- [ ] T-012 Collector : Campus Bourses + 20 sources de bourses (ambassades, fondations, Erasmus+)
- [ ] T-013 Collector : API France Travail (jobs étudiants + stages), clé API gratuite
- [ ] T-014 Fiches pays rédigées et sourcées : Gabon→France (procédure EEF, frais, calendrier 2026-27, visa, AVI)
- [ ] T-015 Indexation Chroma (`make index`) + tests de retrieval (20 questions type)

### Phase 2 — Produit local testable (semaines 5–8)
- [ ] T-020 M1 : questionnaire d'orientation → profil JSON
- [ ] T-021 M2 : moteur de recherche formations avec filtres (CLI + Streamlit)
- [ ] T-022 M3 : matching bourses × profil
- [ ] T-023 M12 : chat RAG avec citations obligatoires + refus si source absente
- [ ] T-024 M4 : générateur/correcteur de lettre de motivation + simulateur d'entretien
- [ ] T-025 Livrable S2 automatisé : "rapport université pour un lycéen au Gabon" en PDF
- [ ] T-026 Test réel avec 5 étudiants pilotes (gratuits contre feedback)

### Phase 3 — Monétisation artisanale (semaines 9–12)
- [ ] T-030 Générateur de factures + suivi paiements (Mobile Money manuel au début)
- [ ] T-031 Vendre 10 services S1/S2 (canaux : WhatsApp, TikTok, groupes Facebook "étudier en France", lycées partenaires à Libreville)
- [ ] T-032 Boucle qualité : chaque dossier vendu enrichit la base (anonymisé)
- [ ] T-033 Choisir le statut juridique (entreprise au Gabon et/ou micro-entreprise France) + CGV + politique de confidentialité

### Phase 4 — Mise en ligne (mois 4–6)
- [ ] T-040 Front Next.js + API FastAPI ; le LLM reste local OU bascule sur un petit VPS GPU
- [ ] T-041 Paiement en ligne (CinetPay/Flutterwave), comptes utilisateurs, RGPD
- [ ] T-042 M11 tableau de bord en ligne + alertes email/WhatsApp
- [ ] T-043 SEO : 50 pages "Étudier en France depuis [pays]" générées depuis la base sourcée

### Phase 5 — B2B & extension (mois 7–12)
- [ ] T-050 M13/M14 : portails entreprises et établissements
- [ ] T-051 Partenariats affiliation (AVI, logement, assurance)
- [ ] T-052 2e corridor : Cameroun/Sénégal→France, puis →Canada/Belgique/Maroc

---

## 10. PROMPTS SYSTÈME POUR TES LLM LOCAUX (à copier dans app/agents/prompts/)

### 10.1 `executor.md` — l'agent qui continue ce plan hors Claude
```
Tu es l'agent d'exécution du projet Mobilité-IA. À chaque lancement :
1. Lis docs/PLAN_MOBILITE_IA.md, trouve la première tâche "[ ] T-xxx".
2. Décris en 5 lignes ton plan pour cette tâche, puis exécute-la en écrivant le code
   dans app/ (fichiers complets, testés par `python -m pytest` si tests présents).
3. Ne modifie dans le plan QUE la case de la tâche et le Journal (§12) : ajoute une
   ligne "AAAA-MM-JJ | T-xxx | résumé | fichiers créés".
4. Commit git avec le message "T-xxx: <résumé>".
Règles : jamais de secret en dur ; jamais de scraping d'un site sans vérifier
robots.txt ; toute donnée réglementaire (visa, bourse) doit porter source_url et date.
Si une tâche demande une décision produit ou juridique : STOP et écris la question
dans §12 avec le tag [DECISION HUMAINE REQUISE].
```

### 10.2 `assistant_etudiant.md` — le produit
```
Tu es l'assistant de mobilité internationale. Tu réponds en français, simplement.
CONTRAINTES ABSOLUES :
- Tu ne réponds sur les visas, bourses, procédures QUE si le contexte RAG fourni
  contient l'information ; sinon tu dis "Je préfère vérifier" et tu donnes le lien
  officiel pertinent (france-visas.gouv.fr, campusfrance.org, service-public.fr).
- Chaque fait cité = (source, date de vérification).
- Tu ne promets JAMAIS une admission ou un visa.
- Tu adaptes tout au profil fourni (nationalité, résidence, niveau, budget).
- Pour un mineur : ton adapté, et rappel que les décisions se prennent avec les parents.
```

### 10.3 `extracteur.md` — normalisation de données
```
Tu reçois du texte brut (page bourse, offre, formation). Rends UNIQUEMENT un JSON
valide conforme au schéma fourni. Champs inconnus = null. Ajoute "confidence" (0-1).
N'invente aucune valeur.
```

---

## 11. INDICATEURS DE SUCCÈS
- Phase 2 : 5 pilotes, temps de génération d'un rapport S2 < 10 min, 0 fait non sourcé.
- Phase 3 : 10 ventes, panier moyen ≥ 25 000 FCFA, NPS ≥ 8/10.
- Phase 4 : 500 comptes, 3 % de conversion payante, coût d'acquisition < 2 000 FCFA.
- Qualité data : > 90 % des fiches visa vérifiées < 90 jours.

## 12. JOURNAL (mis à jour par les agents locaux — ne pas éditer au-dessus)
| Date | Tâche | Résumé | Fichiers |
|---|---|---|---|
| 2026-07-04 | INIT | Création du plan v1.0 (recherche concurrentielle incluse) | docs/PLAN_MOBILITE_IA.md |
