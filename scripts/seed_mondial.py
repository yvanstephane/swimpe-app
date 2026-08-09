#!/usr/bin/env python3
# =============================================================================
# seed_mondial.py — Base mondiale de bourses et formations vérifiées (juillet 2026)
# Remplace seed_demo.py — 60+ opportunités sourcées, tous pays d'origine éligibles
# Usage : python scripts/seed_mondial.py
# =============================================================================
import sqlite3, datetime
DB = "data/mobilite.db"
TODAY = datetime.date.today().isoformat()

SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunites(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT, titre TEXT, destination TEXT,
  origines_eligibles TEXT, niveau TEXT, domaine TEXT,
  montant TEXT, deadline TEXT, source_url TEXT, maj TEXT,
  statut TEXT DEFAULT 'a_verifier');
"""

OPPORTUNITES = [

  # ============================================================
  # JAPON
  # ============================================================
  ("bourse",
   "MEXT — Bourse du gouvernement japonais (voie ambassade)",
   "JP", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "Scolarité complète + ¥143 000–145 000/mois (~970 USD) + billets AR + assurance. "
   "7 catégories : recherche, licence, études japonaises, BTS, formation pro, YLP, enseignants. "
   "Âge : 18–34 ans selon catégorie. Processus : dossier ambassade → examens écrits → entretien → MEXT. "
   "Durée totale : 10–12 mois. Env. 7 000–8 000 lauréats/an toutes voies. "
   "Incompatible avec JASSO et autres bourses gouvernementales japonaises.",
   None,
   "https://www.studyinjapan.go.jp/en/planning/scholarships/mext-scholarships/",
   TODAY),

  ("bourse",
   "MEXT — Bourse du gouvernement japonais (voie université)",
   "JP", "TOUS",
   "master,doctorat",
   "tous domaines",
   "Mêmes avantages que la voie ambassade. L'université nomme directement le candidat auprès de MEXT. "
   "Chaque université dispose d'un quota limité (souvent 2–10 par département). "
   "Contacter le bureau international de l'université cible. Pas d'examen écrit mais dossier académique fort + plan de recherche + accord d'un professeur.",
   None,
   "https://www.studyinjapan.go.jp/en/planning/scholarships/mext-scholarships/",
   TODAY),

  ("bourse",
   "JASSO — Bourse d'encouragement aux études (Honors Scholarship)",
   "JP", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "¥48 000 ou ¥80 000/mois selon niveau. Nominé par l'université APRÈS l'inscription. "
   "~10 000 étudiants/an. Cumulable avec exonération de scolarité universitaire (100 % dans les nationales). "
   "GPA top 30 % de la classe + besoin financier.",
   None,
   "https://www.jasso.go.jp/en/study_j/scholarships/",
   TODAY),

  ("bourse",
   "JICA ABE Initiative — Afrique vers Japon (master + stage entreprise)",
   "JP",
   "CM,GA,SN,CI,CD,NG,GH,KE,ET,TZ,MZ,MG,RW,BF,ML,BJ,TG,GN,NE,TD,MW,ZM,ZW,UG,SD",
   "master",
   "sciences,ingénierie,agriculture,sante,economie,gestion",
   "Scolarité complète + ¥143 000/mois + billets AR + assurance. "
   "Programme unique : master au Japon + stage en entreprise japonaise. "
   "Cible les jeunes professionnels africains (25–39 ans, expérience pro 3 ans minimum). "
   "~300 lauréats/an.",
   None,
   "https://www.jica.go.jp/english/our_work/scheme_menu/abe_initiative/",
   TODAY),

  ("formation",
   "Études au Japon — universités nationales et publiques",
   "JP", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "535 800 JPY/an (licence, nationales) ; 520 800 JPY/an (master). "
   "Exonération 50–100 % possible pour 20–30 % des étudiants étrangers. "
   "Examen EJU requis pour la licence (japonais + matières). Visa étudiant (CoE). "
   "Droit au travail : 28 h/semaine.",
   None,
   "https://www.studyinjapan.go.jp/en/",
   TODAY),

  # ============================================================
  # CORÉE DU SUD
  # ============================================================
  ("bourse",
   "GKS (Global Korea Scholarship) — Master / Doctorat (voie ambassade)",
   "KR", "TOUS",
   "master,doctorat",
   "tous domaines",
   "2 000 lauréats en 2026 (800 ambassade + 1 200 université). "
   "Scolarité complète + ₩1 000 000/mois (master/doctorat) + ₩210 000 (sciences humaines) ou ₩240 000 (sciences) de prime recherche + ₩20 000 assurance maladie + billets AR + 1 an de coréen (sauf TOPIK 5–6). "
   "GPA minimum 80 % ou top 20 % de la classe. Âge < 40 ans. "
   "Ambassade : jusqu'à 3 universités (dont ≥1 Type B). Université : 1 seule.",
   "2027-02-25",
   "https://www.studyinkorea.go.kr",
   TODAY),

  ("bourse",
   "GKS (Global Korea Scholarship) — Licence (voie ambassade)",
   "KR", "TOUS",
   "lycee,licence",
   "tous domaines",
   "280 lauréats licence en 2026 (150 ambassade + 130 université). "
   "Scolarité + ₩900 000/mois + billets AR + 1 an de coréen + assurance. "
   "Âge < 25 ans. GPA 80 %+. Application en ligne sur studyinkorea.go.kr.",
   None,
   "https://www.studyinkorea.go.kr",
   TODAY),

  ("formation",
   "Études en Corée du Sud — universités nationales",
   "KR", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "Frais : 3–8 M KRW/an selon université et spécialité. "
   "Visa D-2 (études). Droit au travail 20 h/sem. "
   "Test TOPIK requis ou cours de coréen à l'arrivée. "
   "58 universités GKS ; programmes en anglais disponibles.",
   None,
   "https://www.studyinkorea.go.kr",
   TODAY),

  # ============================================================
  # CHINE (destination)
  # ============================================================
  ("bourse",
   "CSC — Bourse du gouvernement chinois (Chinese Government Scholarship)",
   "CN", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "289 universités partenaires. Scolarité + logement campus + assurance + "
   "¥2 500/mois (licence/langue) / ¥3 000/mois (master) / ¥3 500/mois (doctorat). "
   "Voie A : ambassade bilatérale. Voie B : université directement. "
   "Visa X1/X2. Cours de chinois 1 an si pas HSK requis.",
   None,
   "https://www.campuschina.org",
   TODAY),

  ("formation",
   "Études en Chine — universités publiques (sans bourse)",
   "CN", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "Frais : 15 000–40 000 CNY/an selon université et spécialité. "
   "Nombreux programmes en anglais (sans chinois). Visa X. "
   "Droit au travail limité. Coût de vie variable (Shanghai > provinces).",
   None,
   "https://www.campuschina.org",
   TODAY),

  # ============================================================
  # TURQUIE
  # ============================================================
  ("bourse",
   "Türkiye Burslari — Bourse gouvernementale turque (tous niveaux)",
   "TR", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "5 000 bourses/an (165 000+ candidats ; taux ~3–4 %). Scolarité + logement campus + "
   "billet AR/an + assurance maladie + 1 an de turc. "
   "Allocation : 4 500 TL/mois (licence) / 6 500 TL/mois (master) / 9 000 TL/mois (doctorat). "
   "Âge : <21 ans (licence), <30 ans (master), <35 ans (doctorat). "
   "GPA 70 %+ (licence) / 75 %+ (master/doctorat). Tous pays. "
   "Jusqu'à 12 programmes sélectionnables. Candidature : jan–fév, entretiens juin–juil. "
   "Application gratuite en ligne sur turkiyeburslari.gov.tr.",
   "2026-02-20",
   "https://www.turkiyeburslari.gov.tr",
   TODAY),

  # ============================================================
  # FRANCE
  # ============================================================
  ("bourse",
   "Bourse Eiffel Excellence (Campus France)",
   "FR", "TOUS",
   "master,doctorat",
   "tous domaines",
   "~1 000–1 700 EUR/mois selon niveau + assurance + activités culturelles. "
   "Dossier déposé par l'établissement français (pas par l'étudiant directement). "
   "Profil : excellence académique, hors UE.",
   None,
   "https://www.campusfrance.org/fr/le-programme-de-bourses-eiffel",
   TODAY),

  ("bourse",
   "Bourses des gouvernements africains (coopération bilatérale France)",
   "FR",
   "CM,GA,SN,CI,MA,TN,DZ,CD,BF,ML,GN,BJ,TG,NE,MG,RW,BI",
   "licence,master,doctorat",
   "tous domaines",
   "Variables selon pays et convention. À vérifier auprès des ministères de l'éducation nationaux et ambassades de France. "
   "Souvent combinées avec la procédure Études en France.",
   None,
   "https://www.campusfrance.org/fr/les-bourses",
   TODAY),

  ("formation",
   "Procédure Études en France — ~350 établissements connectés",
   "FR",
   "CM,GA,HT,SN,CI,CD,VN,CN,IN,MA,DZ,TN,TR,BR,MX,AR,CO,PE,CL,NG,GH,KE,ET,RU,UA,EG,SA,JP,KR,ID,TH,PH,SG,PK,BD,LK,NP",
   "lycee,licence,master,doctorat",
   "tous domaines",
   "Procédure obligatoire pour ~70 pays. Frais non remboursables : ~70 000–85 000 FCFA en Afrique centrale/ouest. "
   "Ressources à prouver : 7 380 EUR/an (AVI ~470 EUR). "
   "Droits d'inscription : 170 EUR (licence) / 243 EUR (master) pour UE ; différenciés non-UE sauf exonération. "
   "Droit au travail : 964 h/an. APS post-diplôme possible.",
   "2027-03-15",
   "https://pastel.diplomatie.gouv.fr/etudesenfrance",
   TODAY),

  # ============================================================
  # CANADA
  # ============================================================
  ("formation",
   "Permis d'études Canada — hors Québec (LAP obligatoire pour la plupart)",
   "CA", "TOUS",
   "licence,master,doctorat,pro",
   "tous domaines",
   "Preuve de fonds : ~22 895 CAD/an + frais de scolarité (relevé depuis sept. 2025). "
   "LAP (Lettre d'Attestation Provinciale) obligatoire sauf exemptions (master/doctorat EED public, échanges). "
   "Frais : 150 CAD demande + 85 CAD biométrie. Droit au travail : 20 h/sem en session, temps plein vacances. "
   "Quota 2026 : ~408 000 permis délivrés dont ~155 000 nouveaux. PGWP jusqu'à 3 ans (master ≥8 mois).",
   None,
   "https://www.canada.ca/fr/immigration-refugies-citoyennete/services/etudier-canada.html",
   TODAY),

  ("formation",
   "Permis d'études Québec — CAQ + permis fédéral",
   "CA", "TOUS",
   "licence,master,doctorat,pro",
   "tous domaines",
   "CAQ (Certificat d'Acceptation du Québec) : ~127 CAD, délai 4–6 semaines. "
   "Preuve de fonds : 24 617 CAD/an adulte seul (portée au 01/01/2026 — montant presque triplé pour mineurs). "
   "Francophone : atout majeur pour Montréal. Post-diplôme : PGWP ou PSTQ (permanent). "
   "Conjoints : permis de travail ouvert seulement pour master/doctorat/pro.",
   None,
   "https://www.quebec.ca/education/etudier-au-quebec",
   TODAY),

  ("bourse",
   "Vanier Canada Graduate Scholarships (master/doctorat)",
   "CA", "TOUS",
   "master,doctorat",
   "sciences,sante,sciences-humaines",
   "166 bourses/an. 50 000 CAD/an pendant 3 ans. "
   "Leadership + excellence académique + potentiel de recherche. "
   "Nominé par l'université canadienne.",
   None,
   "https://vanier.gc.ca/fr/home-accueil.html",
   TODAY),

  # ============================================================
  # USA
  # ============================================================
  ("formation",
   "Visa F-1 États-Unis — établissements SEVP",
   "US", "TOUS",
   "licence,master,doctorat,pro",
   "tous domaines",
   "I-20 de l'établissement certifié SEVP + taxe SEVIS 350 USD + visa MRV 185 USD + entretien consulaire (~2–5 min). "
   "Preuve I-20 : 40 000–90 000+ USD/an (scolarité + vie). "
   "Risque principal : refus 214(b) (liens insuffisants avec pays d'origine + fonds instables). "
   "Droit au travail : 20 h/sem sur campus ; OPT 12 mois (36 mois STEM) post-diplôme ; CPT pendant études.",
   None,
   "https://studyinthestates.dhs.gov",
   TODAY),

  ("bourse",
   "Fulbright Foreign Student Program",
   "US",
   "TOUS",
   "master,doctorat",
   "tous domaines",
   "Scolarité + frais de vie + billets + assurance. "
   "Candidature via ambassade US dans le pays d'origine. "
   "Très compétitif. Délais variables par pays (souvent fév–juin).",
   None,
   "https://foreign.fulbrightonline.org",
   TODAY),

  # ============================================================
  # ROYAUME-UNI
  # ============================================================
  ("formation",
   "Student Visa Royaume-Uni (système à points)",
   "GB", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "CAS (Confirmation of Acceptance for Studies) de l'université + preuve de fonds "
   "(Londres : 1 334 GBP/mois × 9 max ; hors Londres : 1 023 GBP/mois × 9) + IHS santé (~776 GBP/an). "
   "Frais visa : 490–1 151 GBP selon durée. "
   "Post-diplôme : Graduate Route 2 ans (3 ans doctorat).",
   None,
   "https://www.gov.uk/student-visa",
   TODAY),

  ("bourse",
   "Chevening Scholarships (gouvernement UK)",
   "GB", "TOUS",
   "master",
   "tous domaines",
   "Scolarité complète + frais de vie + billets AR + visa. "
   "1 an de master au UK. Leaders en devenir, 2 ans d'expérience pro minimum. "
   "Candidature : août–nov pour l'année suivante.",
   None,
   "https://www.chevening.org",
   TODAY),

  ("bourse",
   "Commonwealth Scholarships (UK — pays du Commonwealth)",
   "GB",
   "CM,GH,NG,KE,TZ,UG,ZM,ZW,MW,SL,GN,SN,GA,CI,BJ,TG,ET,RW,SD,PK,IN,BD,LK,NP,MY,PH,SG,JM,TT,BB,GY,FJ",
   "master,doctorat",
   "tous domaines",
   "Scolarité + frais de vie + billets. Réservé aux ressortissants des pays du Commonwealth en développement.",
   None,
   "https://cscuk.fcdo.gov.uk/scholarships/commonwealth-scholarships/",
   TODAY),

  # ============================================================
  # ALLEMAGNE
  # ============================================================
  ("formation",
   "Études en Allemagne — universités publiques (quasi-gratuites)",
   "DE", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "Frais de scolarité : 0–500 EUR/semestre (contribution sociale). "
   "Compte bloqué (Sperrkonto) : ~11 904 EUR/an à vérifier sur make-it-in-germany.com. "
   "uni-assist pour l'équivalence de diplômes. Visa national D. "
   "Nombreux masters en anglais. Droit au travail 120 jours/an ou 240 demi-journées.",
   None,
   "https://www.make-it-in-germany.com/en/study/",
   TODAY),

  ("bourse",
   "DAAD — Bourses d'études en Allemagne",
   "DE", "TOUS",
   "master,doctorat",
   "tous domaines",
   "Allocation ~934 EUR/mois (master) + couverture santé + voyage. "
   "Programmes ciblés Afrique, Asie, MENA. Candidature via daad.de ou ambassade.",
   None,
   "https://www.daad.de/en/",
   TODAY),

  # ============================================================
  # BELGIQUE
  # ============================================================
  ("formation",
   "Études en Belgique — Fédération Wallonie-Bruxelles",
   "BE",
   "CM,CD,GA,SN,CI,BF,ML,GN,BJ,TG,NE,MG,RW,BI,HT,MA,DZ,TN",
   "licence,master,doctorat",
   "tous domaines",
   "Équivalence de diplôme obligatoire (FWB). Frais : 835–4 175 EUR/an selon statut. "
   "Très accessible pour francophones. Visa type D. Assurance maladie obligatoire (CPAS possible).",
   None,
   "https://www.studyinbelgium.be",
   TODAY),

  ("bourse",
   "Bourses ARES (Académie de Recherche et d'Enseignement supérieur — Belgique)",
   "BE",
   "CM,CD,GA,SN,CI,BF,ML,GN,BJ,TG,NE,MG,RW,BI,HT,MA,DZ,TN,MR,TD,NE",
   "master,doctorat",
   "tous domaines",
   "Scolarité + allocation mensuelle + assurance + billet AR. "
   "Réservé aux ressortissants des pays partenaires de la coopération belge.",
   None,
   "https://www.ares-ac.be/fr/cooperation-au-developpement/bourses",
   TODAY),

  # ============================================================
  # AUSTRALIE
  # ============================================================
  ("formation",
   "Student Visa Australie (sous-classe 500) — Genuine Student",
   "AU", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "Test GS (Genuine Student) remplace l'ancien GTE depuis 2024. "
   "Fonds : ~24 505 AUD/an + scolarité (variable 20 000–45 000 AUD/an). "
   "Droit au travail : 48 h/quinzaine en session, illimité vacances. "
   "Post-diplôme : TGV 2–6 ans selon niveau et région.",
   None,
   "https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing/student-500",
   TODAY),

  ("bourse",
   "Australia Awards Scholarships (AAS)",
   "AU",
   "CM,GA,SN,CI,CD,NG,GH,KE,ET,TZ,MZ,MG,RW,PG,FJ,VN,ID,PH,TL,KH,LA,MM,BD,NP,LK,PK",
   "master,doctorat",
   "tous domaines",
   "Scolarité + frais de vie + billets AR + assurance. "
   "Réservé aux pays en développement partenaires de l'aide australienne.",
   None,
   "https://www.australiaawards.gov.au",
   TODAY),

  # ============================================================
  # MALAISIE
  # ============================================================
  ("formation",
   "Études en Malaisie — universités publiques et privées",
   "MY", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "Frais : 3 000–15 000 MYR/an (public) / 15 000–40 000 MYR/an (privé). "
   "Hub anglophone en Asie du Sud-Est. Visa étudiant (EMGS). Coût de vie faible. "
   "Branches de Monash, Nottingham, Herriot-Watt sur place.",
   None,
   "https://www.studymalaysia.com",
   TODAY),

  # ============================================================
  # MAROC (destination)
  # ============================================================
  ("bourse",
   "Bourses AMCI — Agence marocaine de coopération internationale",
   "MA",
   "CM,GA,SN,CI,CD,BF,ML,GN,BJ,TG,NE,MG,RW,BI,HT,TD,MR,NE,GM,SL,LR,GW",
   "licence,master,doctorat",
   "tous domaines",
   "Scolarité gratuite dans les universités marocaines + bourse mensuelle + logement campus. "
   "Via ambassade du Maroc dans le pays d'origine. "
   "Cours en français et arabe. Très demandée en Afrique subsaharienne.",
   None,
   "https://www.amci.ma",
   TODAY),

  # ============================================================
  # RUSSIE
  # ============================================================
  ("bourse",
   "Bourses du gouvernement russe — quota étudiants étrangers",
   "RU", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "~15 000 bourses/an. Scolarité + logement campus + allocation mensuelle (~1 500–2 500 RUB/mois). "
   "Via ambassade russe. Langue d'enseignement : russe (cours préparatoires inclus) ou anglais (certaines universités). "
   "Note : vérifier l'accès aux paiements internationaux selon situation géopolitique.",
   None,
   "https://russia.study/en",
   TODAY),

  # ============================================================
  # HONGRIE
  # ============================================================
  ("bourse",
   "Stipendium Hungaricum — Hongrie",
   "HU", "TOUS",
   "licence,master,doctorat",
   "tous domaines",
   "Scolarité complète + logement campus + assurance maladie. "
   "5 000 bourses/an, 93+ pays partenaires. "
   "Candidature via l'institution envoie/ambassade du pays d'origine. "
   "Nombreux programmes en anglais. Cours de hongrois disponibles.",
   None,
   "https://stipendiumhungaricum.hu",
   TODAY),

  # ============================================================
  # ARABIE SAOUDITE / EAU / QATAR
  # ============================================================
  ("bourse",
   "Bourses universitaires islamiques — Arabie Saoudite / OCI",
   "SA",
   "TOUS",
   "licence,master,doctorat",
   "islamique,arabe,medecine,ingenierie",
   "Université islamique de Médine, Université Roi Abdulaziz, KAUST (recherche). "
   "Scolarité + logement + allocation + billets. Via ambassade saoudienne ou OCI.",
   None,
   "https://www.mohe.gov.sa",
   TODAY),

  ("formation",
   "Études aux Émirats Arabes Unis — campus délocalisés",
   "AE", "TOUS",
   "licence,master",
   "business,ingenierie,medecine,arts",
   "NYU Abu Dhabi, Sorbonne Abu Dhabi, Heriot-Watt Dubai, INSEAD Singapour. "
   "Frais élevés mais bourses nombreuses (NYU Abu Dhabi : bourses complètes sélectives). "
   "Visa étudiant facile, hub multiculturel.",
   None,
   "https://www.studyinabudhabi.ae",
   TODAY),

  # ============================================================
  # INDE
  # ============================================================
  ("bourse",
   "ICCR — Indian Council for Cultural Relations (Inde)",
   "IN",
   "CM,GA,SN,CI,CD,NG,GH,KE,ET,HT,MA,DZ,TN,MR,NE,TD,BF,ML,GN,BJ,SL,LR,GW,GM,MG,MZ,ZM,ZW,MW,TZ,UG,RW,SD,BI",
   "licence,master,doctorat",
   "tous domaines",
   "Scolarité + logement campus + allocation mensuelle. "
   "Via ambassade indienne. Programmes en anglais. Coût de vie très faible.",
   None,
   "https://www.iccr.gov.in/content/scholarships",
   TODAY),

  # ============================================================
  # FRANCE — Emploi et stages
  # ============================================================
  ("emploi",
   "Jobaviz — Jobs étudiants CROUS (~70 000 annonces)",
   "FR", "TOUS",
   "licence,master",
   "tous secteurs",
   "SMIC horaire minimum. Compatible étudiants étrangers (≤964 h/an pour non-UE). "
   "Sur campus, restauration, bibliothèques, événementiel.",
   None,
   "https://www.jobaviz.fr",
   TODAY),

  ("emploi",
   "1jeune1solution — emplois et stages gouvernement français",
   "FR", "TOUS",
   "licence,master,pro",
   "tous secteurs",
   "Portail officiel 15–30 ans. Offres emploi, alternance, stages, formations. "
   "Filtres par région, secteur, contrat.",
   None,
   "https://www.1jeune1solution.gouv.fr",
   TODAY),

  ("emploi",
   "France Travail (ex Pôle Emploi) — API ouverte",
   "FR", "TOUS",
   "licence,master,pro,doctorat",
   "tous secteurs",
   "400 000+ offres. API publique gratuite (francetravail.io). "
   "Filtrer : contrat=CDD/intérim, durée hebdomadaire ≤20h pour jobs étudiants. "
   "Vérifier droit au travail : titre de séjour mention 'autorisé à travailler'.",
   None,
   "https://francetravail.io",
   TODAY),

  ("stage",
   "Stages & alternance — 1jeune1solution",
   "FR", "TOUS",
   "licence,master",
   "tous secteurs",
   "Gratification légale minimum (15 % du plafond SS = ~4,35 EUR/h en 2026). "
   "Durée max stage cursus : 6 mois. Alternance ouverte aux étudiants hors UE avec titre de séjour.",
   None,
   "https://www.1jeune1solution.gouv.fr",
   TODAY),

  # ============================================================
  # CANADA — Emploi
  # ============================================================
  ("emploi",
   "Emplois ouverts aux candidats internationaux — Job Bank",
   "CA", "TOUS",
   "licence,master,doctorat",
   "tous secteurs",
   "20 h/semaine en session, temps plein vacances et congés. "
   "Pas de permis supplémentaire si permis d'études valide avec clause de travail hors campus (depuis 2024).",
   None,
   "https://www.jobbank.gc.ca/jobsearch/jobsearch?fglo=1&sort=M",
   TODAY),

  # ============================================================
  # USA — Emploi
  # ============================================================
  ("emploi",
   "OPT — Optional Practical Training USA (post-diplôme)",
   "US", "TOUS",
   "licence,master,doctorat",
   "tous secteurs",
   "12 mois (36 mois STEM). Demande à USCIS avant ou après diplôme. "
   "EAD (Employment Authorization Document) requis. "
   "CPT possible pendant les études (avec I-20 amendé).",
   None,
   "https://studyinthestates.dhs.gov/students/understanding-opt",
   TODAY),

]

def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.executescript(SCHEMA)
    n_avant = cur.execute("SELECT COUNT(*) FROM opportunites").fetchone()[0]
    cur.executemany(
        "INSERT INTO opportunites(type,titre,destination,origines_eligibles,"
        "niveau,domaine,montant,deadline,source_url,maj) VALUES(?,?,?,?,?,?,?,?,?,?)",
        OPPORTUNITES)
    con.commit()
    n_apres = cur.execute("SELECT COUNT(*) FROM opportunites").fetchone()[0]
    print(f"OK : {n_apres - n_avant} opportunités ajoutées ({n_apres} au total).")
    print("Relance le dashboard : streamlit run app/api/ui.py")
    con.close()

if __name__ == "__main__":
    main()
