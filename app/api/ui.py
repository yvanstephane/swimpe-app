# =============================================================================
# YORBITY — Ta trajectoire vers le monde (multilingue, détection auto)
# - Parcours guidé 4 questions → conditions d'admission déroulées (style Campus France)
# - Procédure adaptée au pays d'ORIGINE (ex : Gabon → France = Études en France)
# - Services d'accompagnement PAR DESTINATION, intégrés aux étapes, sans prix affichés
# - Bandeau marketing « Commence ton projet à partir de X » (service le moins cher)
# - Admin : activer/désactiver pays + voir les demandes (mot de passe .env)
# Lancement : streamlit run app/api/ui.py
# =============================================================================
import sqlite3, os, datetime
import streamlit as st
from i18n import t, T, detecter_langue, LANGUES, RTL

APP_NAME = "Yorbity"
TAGLINE = "Ta trajectoire vers le monde"
DB = "data/mobilite.db"
ADMIN_PWD = os.environ.get("ADMIN_PASSWORD", "yorbity2026")
TODAY = datetime.date.today().isoformat()

st.set_page_config(page_title=APP_NAME, page_icon="🚀", layout="centered")

# ---------- Langue : détection auto (1re visite) + sélecteur ----------
if "lang" not in st.session_state:
    st.session_state.lang = detecter_langue("fr")
_lcodes = list(LANGUES.keys())
with st.sidebar:
    st.markdown("### 🌐 " + t("langue_label", st.session_state.lang))
    choix_lang = st.selectbox(" ", _lcodes,
        index=_lcodes.index(st.session_state.lang),
        format_func=lambda c: LANGUES[c], label_visibility="collapsed")
    if choix_lang != st.session_state.lang:
        st.session_state.lang = choix_lang
        st.rerun()
LG = st.session_state.lang
if LG in RTL:
    st.markdown("<style>.main .block-container{direction:rtl; text-align:right;}</style>",
                unsafe_allow_html=True)

# ---------- Style ----------
st.markdown("""
<style>
.hero {background: linear-gradient(135deg,#1e3a8a 0%,#3b82f6 55%,#06b6d4 100%);
  color:white; border-radius:18px; padding:1.6rem 1.8rem; margin:0.8rem 0 1.2rem;}
.hero h2 {color:white; margin:0 0 .3rem; font-size:1.5rem;}
.hero p {margin:0; opacity:.92; font-size:1.02rem;}
.prix {display:inline-block; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.4);
  padding:.45rem 1rem; border-radius:999px; margin-top:.7rem; font-weight:600;}
.badge {display:inline-block; background:#eff6ff; color:#1d4ed8; border-radius:999px;
  padding:.15rem .7rem; font-size:.8rem; margin-right:.4rem;}
div[data-testid="stExpander"] {border-radius:12px; border:1px solid #e5e7eb; margin-bottom:.4rem;}
</style>""", unsafe_allow_html=True)

# ---------- Taux internes (uniquement pour le prix d'appel) ----------
TAUX = {"EUR":1.0,"USD":1.08,"XOF":655.96,"XAF":655.96,"CAD":1.47,"GBP":0.85,
        "MAD":10.8,"TND":3.4,"NGN":1650,"GHS":16,"KES":140,"HTG":145,"INR":92,
        "PKR":300,"IDR":17500,"BRL":6.0,"RWF":1420,"CDF":2900,"EGP":52,"ZAR":19.5}
def conv(m, de, vers):
    if de in TAUX and vers in TAUX: return m / TAUX[de] * TAUX[vers]
    return None

# ---------- Pays d'origine (nom → code, devise locale) ----------
ORIGINES = {
 "Afghanistan":("AF","USD"),"Afrique du Sud":("ZA","ZAR"),"Algérie":("DZ","EUR"),
 "Angola":("AO","USD"),"Bangladesh":("BD","USD"),"Bénin":("BJ","XOF"),
 "Brésil":("BR","BRL"),"Burkina Faso":("BF","XOF"),"Burundi":("BI","USD"),
 "Cameroun":("CM","XAF"),"Chine":("CN","USD"),"Colombie":("CO","USD"),
 "Comores":("KM","EUR"),"Congo (Brazzaville)":("CG","XAF"),"Congo (RDC)":("CD","CDF"),
 "Côte d'Ivoire":("CI","XOF"),"Djibouti":("DJ","USD"),"Égypte":("EG","EGP"),
 "Éthiopie":("ET","USD"),"Gabon":("GA","XAF"),"Gambie":("GM","USD"),
 "Ghana":("GH","GHS"),"Guinée":("GN","USD"),"Haïti":("HT","HTG"),
 "Inde":("IN","INR"),"Indonésie":("ID","IDR"),"Kenya":("KE","KES"),
 "Liban":("LB","USD"),"Madagascar":("MG","EUR"),"Mali":("ML","XOF"),
 "Maroc":("MA","MAD"),"Mauritanie":("MR","EUR"),"Mexique":("MX","USD"),
 "Népal":("NP","USD"),"Niger":("NE","XOF"),"Nigeria":("NG","NGN"),
 "Ouganda":("UG","USD"),"Pakistan":("PK","PKR"),"Philippines":("PH","USD"),
 "République centrafricaine":("CF","XAF"),"Rwanda":("RW","RWF"),
 "Sénégal":("SN","XOF"),"Sri Lanka":("LK","USD"),"Tanzanie":("TZ","USD"),
 "Tchad":("TD","XAF"),"Togo":("TG","XOF"),"Tunisie":("TN","TND"),
 "Turquie":("TR","USD"),"Ukraine":("UA","USD"),"Vietnam":("VN","USD"),
 "Zambie":("ZM","USD"),"Zimbabwe":("ZW","USD"),
}

# Pays soumis à la procédure Études en France (EEF / Campus France)
EEF = {"ZA","DZ","BJ","BF","BI","CM","CN","CO","KM","CG","CD","CI","DJ","EG","ET",
       "GA","GN","HT","IN","ID","KE","LB","MG","ML","MA","MR","MX","NP","NE","NG",
       "PK","CF","RW","SN","LK","TD","TG","TN","TR","UA","VN","GH","GM","UG","TZ",
       "ZM","ZW","BD","AF","AO","BR","PH"}

# =============================================================================
# CATALOGUE DES SERVICES (les prix restent INTERNES : jamais affichés en liste,
# seuls le "à partir de" du bandeau et le back-office les utilisent)
# =============================================================================
SVC = {
 "ORIENT":  ("🧭 Orientation & choix des formations",
             "On analyse ton profil et on te propose les formations et établissements "
             "les plus cohérents avec ton niveau, ton budget et ton projet — comme le "
             "ferait un conseiller Parcoursup, mais dédié à toi.", 15000),
 "ADMIS":   ("🎓 Admission directe auprès des écoles",
             "Nous contactons les établissements pour toi, montons tes candidatures "
             "(y compris hors plateformes officielles) et t'obtenons des admissions "
             "que tu intègres ensuite à ta procédure officielle.", 45000),
 "EEF":     ("🗂 Prise en charge du dossier Études en France",
             "Création et remplissage complet de ton dossier EEF, choix stratégique "
             "des vœux, vérification des pièces, suivi des délais Campus France.", 30000),
 "DOSSIER": ("✍️ Lettre de motivation, CV & projet d'études",
             "Rédaction et optimisation de ton dossier (3 itérations) pour maximiser "
             "tes chances d'acceptation.", 25000),
 "ENTRETIEN":("🎤 Préparation à l'entretien",
             "Simulations réalistes (Campus France, consulat…) + débrief + fiches "
             "réponses personnalisées.", 15000),
 "FONDS":   ("💶 Montage de la preuve de fonds",
             "AVI, compte bloqué, GIC ou relevés : on construit un dossier financier "
             "conforme aux exigences exactes de ta destination.", 20000),
 "VISA":    ("🛂 Accompagnement visa de A à Z",
             "Checklist personnalisée, remplissage des formulaires, prise de "
             "rendez-vous, préparation des justificatifs, suivi jusqu'à la décision.", 20000),
 "LOGEMENT":("🏠 Recherche de logement & attestation",
             "Dossier locataire, candidatures résidences/CROUS/privé et obtention de "
             "l'attestation d'hébergement exigée pour le visa.", 25000),
 "BOURSE":  ("💰 Chasse aux bourses ciblée",
             "Identification des bourses auxquelles TON profil est éligible et aide "
             "complète au montage de 2 dossiers.", 20000),
 "TRAD":    ("📑 Traductions certifiées & légalisations",
             "Coordination des traductions assermentées, apostilles et "
             "authentifications exigées par ta destination.", 10000),
 "PACK":    ("🚀 Pack complet « Décollage »",
             "On gère tout ton projet de bout en bout : orientation, admissions, "
             "dossier, fonds, visa, installation. Toi, tu prépares ta valise.", 89000),
}

# =============================================================================
# DESTINATIONS — chaque étape : (titre, détail, lien, code_service_ou_None)
# `services` = codes pertinents pour CE pays (rien d'autre ne s'affiche)
# =============================================================================
D = {}

D["FR"] = dict(nom="France", flag="🇫🇷",
 resume="Études quasi gratuites à l'université publique (exonérations fréquentes des "
        "droits différenciés). Diplômes reconnus mondialement, vie étudiante riche.",
 ressources="7 380 € par an à justifier (615 €/mois) — l'AVI est la solution la plus simple",
 travail="964 h/an (~20 h/semaine)", post="APS 1 an : rester chercher un emploi ou créer ton entreprise",
 portail="https://www.campusfrance.org",
 services=["ORIENT","EEF","ADMIS","DOSSIER","ENTRETIEN","FONDS","VISA","LOGEMENT","BOURSE","TRAD","PACK"],
 etapes_eef=[
  ("Créer ton dossier Études en France (Campus France)",
   "Ta procédure passe obligatoirement par la plateforme EEF gérée par Campus France : "
   "création du compte, saisie des vœux (souvent 3), paiement des frais de dossier "
   "(~70 000–85 000 FCFA selon le pays, non remboursables), dépôt des bulletins et diplômes scannés.",
   "https://pastel.diplomatie.gouv.fr/etudesenfrance", "EEF"),
  ("Booster tes chances : l'admission directe en parallèle",
   "En plus de tes vœux EEF, tu peux contacter directement des écoles et obtenir une "
   "admission par tes propres démarches, puis l'ajouter dans EEF via « Je suis accepté » "
   "et continuer ta procédure normalement. C'est le meilleur plan B — et on peut le faire pour toi.",
   None, "ADMIS"),
  ("Préparer un dossier qui se démarque",
   "Lettre de motivation, CV et projet d'études : c'est ce que lisent les universités "
   "ET l'agent Campus France. Un dossier moyen = refus silencieux.",
   None, "DOSSIER"),
  ("Réussir l'entretien Campus France",
   "≈15 minutes décisives : motivation, cohérence du projet, connaissance de la France. "
   "Ça se prépare comme un oral d'examen.",
   None, "ENTRETIEN"),
  ("Prouver tes ressources (7 380 €/an)",
   "Attestation de Virement Irrévocable (AVI), garant ou compte : le consulat veut un "
   "dossier financier carré. C'est le motif n°1 de refus de visa évitable.",
   None, "FONDS"),
  ("Demander le visa étudiant (VLS-TS)",
   "Sur France-Visas : formulaire, justificatifs, rendez-vous, dépôt. Délai 3–8 semaines.",
   "https://france-visas.gouv.fr", "VISA"),
  ("Trouver ton logement AVANT le visa",
   "Une attestation d'hébergement est exigée au dossier visa : CROUS, résidences privées, "
   "colocation… On peut mener cette démarche en parallèle pour toi.",
   "https://trouverunlogement.lescrous.fr", "LOGEMENT"),
 ],
 etapes_std=[
  ("Candidater directement (Parcoursup / établissements)",
   "Ton pays n'est pas soumis à la procédure Études en France : tu candidates via "
   "Parcoursup (licence) ou directement auprès des établissements (DAP au consulat pour la L1).",
   "https://www.parcoursup.gouv.fr", "ADMIS"),
  ("Préparer ton dossier", "Lettre, CV, projet d'études solides.", None, "DOSSIER"),
  ("Prouver tes ressources", "7 380 €/an (AVI, garant…).", None, "FONDS"),
  ("Visa étudiant VLS-TS", "Sur France-Visas.", "https://france-visas.gouv.fr", "VISA"),
  ("Logement", "Attestation exigée pour le visa.", "https://trouverunlogement.lescrous.fr", "LOGEMENT"),
 ],
 bourses=[("Bourse Eiffel", "Master/doctorat d'excellence, ~1 000–1 700 €/mois, déposée par l'établissement.", "https://www.campusfrance.org/fr/le-programme-de-bourses-eiffel"),
          ("Bourses bilatérales", "Selon accords entre ton gouvernement et la France.", "https://www.campusfrance.org/fr/les-bourses")])

D["CA"] = dict(nom="Canada", flag="🇨🇦",
 resume="Études + travail + immigration possible après le diplôme (PGWP → résidence). "
        "Attention : quotas 2026 et preuves financières élevées — un dossier solide fait la différence.",
 ressources="≈22 895 CAD/an + frais de scolarité (hors Québec) · Québec : 24 617 CAD + CAQ",
 travail="20 h/semaine en session, temps plein aux vacances",
 post="Permis post-diplôme (PGWP) jusqu'à 3 ans, puis voies vers la résidence permanente",
 portail="https://www.educanada.ca",
 services=["ORIENT","ADMIS","DOSSIER","FONDS","VISA","BOURSE","TRAD","PACK"],
 etapes=[
  ("Décrocher l'admission d'un établissement désigné (EED)",
   "Seuls les établissements de la liste officielle IRCC permettent un permis d'études. "
   "Le choix province/programme conditionne aussi tes chances (quotas).",
   "https://www.canada.ca/fr/immigration-refugies-citoyennete/services/etudier-canada/etablissements-designes.html", "ADMIS"),
  ("Obtenir la LAP (hors Québec) ou le CAQ (Québec)",
   "Lettre d'attestation provinciale ou Certificat d'acceptation du Québec (~127 CAD, 4–6 semaines).",
   None, None),
  ("Monter une preuve de fonds irréprochable",
   "GIC ou relevés bancaires 4 mois + lettre de garant conforme. Fonds mal présentés = "
   "motif n°1 de refus.",
   None, "FONDS"),
  ("Rédiger un plan d'études convaincant",
   "Une page qui explique pourquoi CE programme, CE pays, et ton retour/projet. "
   "La 2e cause de refus la plus fréquente.",
   None, "DOSSIER"),
  ("Déposer la demande de permis d'études (IRCC)",
   "150 CAD + biométrie 85 CAD. Délais 4–16 semaines selon le pays.",
   "https://www.canada.ca/fr/immigration-refugies-citoyennete.html", "VISA"),
 ],
 bourses=[("Vanier CGS", "50 000 CAD/an ×3 ans (master/doctorat), nomination par l'université.", "https://vanier.gc.ca"),
          ("Bourses d'entrée des universités", "Automatiques ou sur dossier selon l'établissement.", None)])

D["US"] = dict(nom="États-Unis", flag="🇺🇸",
 resume="Le système universitaire le plus puissant du monde — et le plus cher. La clé : "
        "viser les universités qui financent les internationaux, et réussir un entretien de 3 minutes.",
 ressources="40 000 à 90 000+ USD/an selon l'I-20 de l'école (bourses complètes possibles)",
 travail="20 h/semaine sur campus · OPT 12 mois (36 mois STEM) après le diplôme",
 post="OPT puis visa de travail H-1B (loterie) ou poursuite d'études",
 portail="https://educationusa.state.gov",
 services=["ORIENT","ADMIS","DOSSIER","ENTRETIEN","FONDS","BOURSE","TRAD","PACK"],
 etapes=[
  ("Être admis dans une école certifiée SEVP",
   "L'école t'envoie le formulaire I-20 avec le montant annuel à prouver.",
   "https://studyinthestates.dhs.gov", "ADMIS"),
  ("Payer SEVIS puis remplir le DS-160",
   "Taxe SEVIS 350 USD (fmjfee.com) + formulaire DS-160 + frais visa 185 USD.",
   "https://fmjfee.com", None),
  ("Préparer le dossier financier",
   "Les fonds doivent être stables, traçables et cohérents avec l'I-20.",
   None, "FONDS"),
  ("Réussir l'entretien consulaire (2 à 5 minutes !)",
   "Le refus 214(b) tombe si l'agent doute de tes liens avec ton pays ou de tes fonds. "
   "Chaque réponse doit être prête.",
   None, "ENTRETIEN"),
 ],
 bourses=[("Fulbright", "Bourse complète master/doctorat, via l'ambassade US de ton pays.", "https://foreign.fulbrightonline.org"),
          ("Universités need-blind / full-need", "Certaines financent à 100 % les internationaux admis.", None)])

D["GB"] = dict(nom="Royaume-Uni", flag="🇬🇧",
 resume="Diplômes prestigieux en 3 ans (licence) ou 1 an (master). Procédure visa claire à points.",
 ressources="1 334 £/mois (Londres) ou 1 023 £/mois (ailleurs) ×9 + scolarité · IHS ~776 £/an",
 travail="20 h/semaine", post="Graduate Route : 2 ans (3 ans doctorat) pour travailler",
 portail="https://study-uk.britishcouncil.org",
 services=["ORIENT","ADMIS","DOSSIER","FONDS","VISA","BOURSE","TRAD","PACK"],
 etapes=[
  ("Être admis et recevoir le CAS", "L'université émet le Confirmation of Acceptance for Studies.", None, "ADMIS"),
  ("Réunir les fonds exigés", "Montants stricts, sur compte 28 jours consécutifs.", None, "FONDS"),
  ("Payer l'IHS et déposer le visa en ligne", "490–1 151 £ selon durée + biométrie.", "https://www.gov.uk/student-visa", "VISA"),
 ],
 bourses=[("Chevening", "Master complet pour futurs leaders (2 ans d'expérience).", "https://www.chevening.org"),
          ("Commonwealth", "Pays du Commonwealth en développement.", "https://cscuk.fcdo.gov.uk")])

D["DE"] = dict(nom="Allemagne", flag="🇩🇪",
 resume="Universités publiques quasi GRATUITES (~350 €/semestre) et forte demande d'ingénieurs. "
        "Beaucoup de masters en anglais.",
 ressources="Compte bloqué (Sperrkonto) ≈11 904 €/an",
 travail="120 jours/an", post="18 mois pour chercher un emploi après le diplôme",
 portail="https://www.daad.de/en/",
 services=["ORIENT","ADMIS","DOSSIER","FONDS","VISA","BOURSE","TRAD","PACK"],
 etapes=[
  ("Vérifier l'équivalence de ton diplôme", "Via anabin/uni-assist (~75 €). Certains bacs exigent une année préparatoire (Studienkolleg).", "https://www.uni-assist.de", "ADMIS"),
  ("Ouvrir le compte bloqué", "≈11 904 €/an chez Expatrio, Coracle ou Deutsche Bank.", "https://www.make-it-in-germany.com", "FONDS"),
  ("Visa national D", "Admission + Sperrkonto + assurance + logement.", None, "VISA"),
 ],
 bourses=[("DAAD", "~934 €/mois en master, programmes dédiés Afrique/Asie.", "https://www.daad.de/en/")])

D["BE"] = dict(nom="Belgique", flag="🇧🇪",
 resume="Le choix naturel des francophones : frais modérés (835–4 175 €/an), universités réputées.",
 ressources="≈650 €/mois à justifier",
 travail="20 h/semaine", post="Séjour de recherche d'emploi possible",
 portail="https://www.studyinbelgium.be",
 services=["ORIENT","ADMIS","DOSSIER","FONDS","VISA","BOURSE","TRAD","PACK"],
 etapes=[
  ("Faire reconnaître ton diplôme (équivalence FWB)", "Dossier à déposer TÔT : 3–4 mois de délai, indispensable pour s'inscrire.", "https://www.equivalences.cfwb.be", "TRAD"),
  ("S'inscrire à l'université", "Candidatures juin–septembre pour la rentrée d'octobre.", None, "ADMIS"),
  ("Visa D étudiant", "Admission + équivalence + fonds + assurance.", None, "VISA"),
 ],
 bourses=[("ARES", "Bourse complète de la coopération belge (pays partenaires).", "https://www.ares-ac.be")])

D["IT"] = dict(nom="Italie", flag="🇮🇹",
 resume="Le secret le mieux gardé d'Europe : frais calculés sur TES revenus (souvent 500–3 000 €/an) "
        "et bourses régionales DSU qui couvrent logement + repas + allocation, même pour les étrangers.",
 ressources="≈6 500 €/an à justifier (hors bourse DSU)",
 travail="20 h/semaine", post="Permesso de recherche d'emploi 12 mois",
 portail="https://studyinitaly.esteri.it",
 services=["ORIENT","ADMIS","DOSSIER","BOURSE","VISA","TRAD","PACK"],
 etapes=[
  ("Pré-inscription sur Universitaly", "La plateforme officielle reliée à ton consulat — l'équivalent italien de Campus France.", "https://www.universitaly.it", "ADMIS"),
  ("Demander la bourse régionale DSU", "Sur critères sociaux : logement + cantine + ~5 200 €/an. Peu de candidats étrangers la connaissent.", None, "BOURSE"),
  ("Visa D études", "Admission + fonds + logement + assurance.", None, "VISA"),
 ],
 bourses=[("DSU régional", "Logement + repas + allocation sur critères sociaux.", None),
          ("Invest Your Talent in Italy", "Masters ciblés + stage en entreprise italienne.", "https://investyourtalentapplication.esteri.it")])

D["ES"] = dict(nom="Espagne", flag="🇪🇸",
 resume="Frais publics 1 000–3 500 €/an, qualité de vie, espagnol = 2e langue mondiale.",
 ressources="≈600 €/mois à justifier",
 travail="30 h/semaine", post="Séjour de recherche d'emploi 12 mois",
 portail="https://www.universidades.gob.es",
 services=["ORIENT","ADMIS","DOSSIER","VISA","TRAD","PACK"],
 etapes=[
  ("Homologuer ton bac (UNEDasiss)", "Obligatoire pour entrer en licence.", "https://unedasiss.uned.es", "TRAD"),
  ("Candidater aux universités", "Directement ou via les préinscriptions régionales.", None, "ADMIS"),
  ("Visa D études", "Admission + fonds + assurance.", None, "VISA"),
 ],
 bourses=[("Fundación Carolina / MAEC-AECID", "Coopération espagnole (Amérique latine, Afrique).", "https://www.fundacioncarolina.es")])

D["PT"] = dict(nom="Portugal", flag="🇵🇹",
 resume="Coût de vie parmi les plus bas d'Europe de l'Ouest, concours dédiés aux étudiants internationaux.",
 ressources="≈7 000 €/an", travail="Autorisé (déclaration)", post="Séjour de recherche d'emploi",
 portail="https://www.study-research.pt",
 services=["ORIENT","ADMIS","DOSSIER","VISA","TRAD","PACK"],
 etapes=[
  ("Concours « estudante internacional »", "Candidature directe auprès des universités.", None, "ADMIS"),
  ("Visa D4", "Admission + fonds + casier + assurance.", None, "VISA"),
 ],
 bourses=[("Bourses des universités + Camões", "Selon accords (pays lusophones surtout).", None)])

D["NL"] = dict(nom="Pays-Bas", flag="🇳🇱",
 resume="Énorme offre en anglais, l'université dépose elle-même ta demande de séjour : zéro stress visa.",
 ressources="≈13 500 €/an (norme IND) + scolarité 8 000–20 000 €/an",
 travail="16 h/semaine", post="Orientation year : 12 mois pour trouver un emploi",
 portail="https://www.studyinnl.org",
 services=["ORIENT","ADMIS","DOSSIER","FONDS","BOURSE","PACK"],
 etapes=[
  ("Candidater via Studielink", "Plateforme nationale unique.", "https://www.studielink.nl", "ADMIS"),
  ("L'université gère ton visa", "Elle dépose la demande IND pour toi après admission et preuve de fonds.", None, "FONDS"),
 ],
 bourses=[("Orange Knowledge / Orange Tulip", "Pays ciblés + bourses d'universités.", "https://www.studyinnl.org")])

D["GR"] = dict(nom="Grèce", flag="🇬🇷",
 resume="Frais très bas (licence publique quasi gratuite en grec ; 1 500–3 000 €/an en anglais).",
 ressources="≈6 000 €/an", travail="Partiel autorisé", post="Selon titre de séjour",
 portail="https://studyingreece.edu.gr",
 services=["ORIENT","ADMIS","DOSSIER","VISA","TRAD","PACK"],
 etapes=[
  ("Candidater via Study in Greece", "Plateforme nationale des programmes internationaux.", "https://studyingreece.edu.gr", "ADMIS"),
  ("Visa D études", "Admission + fonds + assurance.", None, "VISA"),
 ],
 bourses=[("Bourses IKY", "Fondation d'État, selon accords bilatéraux.", "https://www.iky.gr")])

D["CZ"] = dict(nom="République tchèque", flag="🇨🇿",
 resume="GRATUIT si tu étudies en tchèque (année de langue possible) ; 2 000–6 000 €/an en anglais. "
        "Bourses d'État pour les pays en développement.",
 ressources="≈4 400 €/an à justifier",
 travail="Autorisé avec les études", post="9 mois de recherche d'emploi",
 portail="https://www.studyin.cz",
 services=["ORIENT","ADMIS","DOSSIER","VISA","TRAD","BOURSE","PACK"],
 etapes=[
  ("Candidater + nostrifier ton diplôme", "Reconnaissance du diplôme (nostrification) + candidature directe.", "https://www.studyin.cz", "ADMIS"),
  ("Visa long séjour", "Admission + fonds + logement + casier.", None, "VISA"),
 ],
 bourses=[("Bourses du gouvernement tchèque", "Pays en développement, via l'ambassade.", "https://www.mzv.cz")])

D["PL"] = dict(nom="Pologne", flag="🇵🇱",
 resume="Frais 2 000–5 000 €/an, coût de vie bas, programme national de bourses NAWA très actif.",
 ressources="≈7 000 €/an", travail="Libre pour les étudiants", post="9 mois de recherche d'emploi",
 portail="https://study.gov.pl",
 services=["ORIENT","ADMIS","DOSSIER","BOURSE","VISA","TRAD","PACK"],
 etapes=[
  ("Candidater (universités / NAWA)", "", "https://nawa.gov.pl/en", "ADMIS"),
  ("Visa national D", "Admission + fonds + assurance.", None, "VISA"),
 ],
 bourses=[("NAWA — Banach / Poland My First Choice", "Bourses complètes pour pays en développement.", "https://nawa.gov.pl/en")])

D["RO"] = dict(nom="Roumanie", flag="🇷🇴",
 resume="LA destination montante pour médecine et pharmacie en français (5 000–7 500 €/an) — "
        "et des bourses d'État accessibles via les ambassades.",
 ressources="≈5 000 €/an hors scolarité",
 travail="4 h/jour", post="Selon titre",
 portail="https://studyinromania.gov.ro",
 services=["ORIENT","ADMIS","DOSSIER","BOURSE","VISA","TRAD","PACK"],
 etapes=[
  ("Obtenir la lettre d'acceptation du ministère",
   "L'université transmet ton dossier au ministère roumain (4–8 semaines). C'est LA pièce clé du visa.",
   None, "ADMIS"),
  ("Visa D/SD", "Acceptation + fonds + assurance + casier.", None, "VISA"),
 ],
 bourses=[("Bourses de l'État roumain", "Tous cycles, année de roumain incluse — via l'ambassade.", "https://www.mae.ro/en/node/10251")])

D["HU"] = dict(nom="Hongrie", flag="🇭🇺",
 resume="Stipendium Hungaricum : 5 000 bourses COMPLÈTES par an (scolarité + logement + allocation), 90+ pays éligibles.",
 ressources="Couvert si boursier · sinon ≈6 000 €/an",
 travail="24 h/semaine", post="9 mois de recherche d'emploi",
 portail="https://studyinhungary.hu",
 services=["ORIENT","DOSSIER","BOURSE","VISA","TRAD","PACK"],
 etapes=[
  ("Candidater au Stipendium (janvier)", "Via l'organisme d'envoi de ton pays + la plateforme officielle.", "https://stipendiumhungaricum.hu", "BOURSE"),
  ("Visa D après attribution", "", None, "VISA"),
 ],
 bourses=[("Stipendium Hungaricum", "Bourse complète, tous cycles.", "https://stipendiumhungaricum.hu")])

D["TR"] = dict(nom="Turquie", flag="🇹🇷",
 resume="Türkiye Bursları : bourse 100 % complète (scolarité + logement + allocation + billets + année de turc). "
        "Candidature GRATUITE janvier–février.",
 ressources="Couvert si boursier · sinon ≈4 000 €/an",
 travail="Limité pendant les études", post="Permis de travail selon secteur",
 portail="https://www.studyinturkiye.gov.tr",
 services=["ORIENT","DOSSIER","ENTRETIEN","BOURSE","VISA","TRAD","PACK"],
 etapes=[
  ("Candidater sur turkiyeburslari.gov.tr", "Jusqu'à 12 programmes ; l'université est ensuite assignée.", "https://www.turkiyeburslari.gov.tr", "BOURSE"),
  ("Réussir l'entretien (juin–juillet)", "Motivation + projet — un entretien préparé multiplie tes chances (taux global ~3–4 %).", None, "ENTRETIEN"),
  ("Visa étudiant", "Après acceptation.", None, "VISA"),
 ],
 bourses=[("Türkiye Bursları", "Complète, tous cycles, tous pays.", "https://www.turkiyeburslari.gov.tr")])

D["JP"] = dict(nom="Japon", flag="🇯🇵",
 resume="MEXT : LA bourse de référence (scolarité + ≈145 000 ¥/mois + billets). "
        "Pour l'Afrique : JICA ABE = master + stage en entreprise japonaise.",
 ressources="Couvert si MEXT · sinon ≈1 200 000 ¥/an",
 travail="28 h/semaine (avec permis)", post="Visa recherche d'emploi 6 mois",
 portail="https://www.studyinjapan.go.jp",
 services=["ORIENT","DOSSIER","ENTRETIEN","BOURSE","VISA","TRAD","PACK"],
 etapes=[
  ("Candidater à MEXT via l'ambassade", "Dossier → examens écrits → entretien. Compter 10–12 mois : anticipe !", "https://www.studyinjapan.go.jp/en/planning/scholarships/mext-scholarships/", "BOURSE"),
  ("CoE puis visa", "L'université demande le Certificate of Eligibility, base du visa.", None, "VISA"),
 ],
 bourses=[("MEXT", "Complète, tous cycles, 2 voies (ambassade/université).", "https://www.studyinjapan.go.jp"),
          ("JICA ABE (Afrique)", "Master + stage en entreprise (~300/an).", "https://www.jica.go.jp")])

D["KR"] = dict(nom="Corée du Sud", flag="🇰🇷",
 resume="GKS : 2 000 bourses complètes en 2026 (scolarité + ₩900 000–1 000 000/mois + billets + année de coréen).",
 ressources="Couvert si GKS · sinon ≈10 000 000 ₩/an",
 travail="20 h/semaine", post="Visa D-10 de recherche d'emploi",
 portail="https://www.studyinkorea.go.kr",
 services=["ORIENT","DOSSIER","ENTRETIEN","BOURSE","VISA","TRAD","PACK"],
 etapes=[
  ("Candidater à la GKS (ambassade : sept–oct)", "GPA ≥80 % exigé. Voie ambassade = 3 universités possibles.", "https://www.studyinkorea.go.kr", "BOURSE"),
  ("Visa D-2", "Admission + fonds (~8 000 $ recommandés).", None, "VISA"),
 ],
 bourses=[("GKS", "Complète, licence à doctorat.", "https://www.studyinkorea.go.kr")])

D["CN"] = dict(nom="Chine", flag="🇨🇳",
 resume="Bourse CSC dans 289 universités : scolarité + logement + allocation mensuelle. "
        "Cursus en anglais nombreux.",
 ressources="Couvert si CSC · sinon ≈30 000 ¥/an",
 travail="Interdit (visa X)", post="Visa Z si employeur trouvé",
 portail="https://www.campuschina.org",
 services=["ORIENT","DOSSIER","BOURSE","VISA","TRAD","PACK"],
 etapes=[
  ("Candidater CSC (ambassade ou université)", "Formulaire JW201 (boursier) / JW202.", "https://www.campuschina.org", "BOURSE"),
  ("Visa X1", "Admission + JW + certificat médical.", None, "VISA"),
 ],
 bourses=[("CSC", "Complète.", "https://www.campuschina.org")])

D["IN"] = dict(nom="Inde", flag="🇮🇳",
 resume="600+ établissements sur le portail national Study in India, cours en anglais, "
        "coût de vie imbattable. Bourses ICCR complètes via les ambassades.",
 ressources="≈2 500 €/an suffisent (hors bourse)",
 travail="Non autorisé en principe", post="Limité",
 portail="https://www.studyinindia.gov.in",
 services=["ORIENT","ADMIS","DOSSIER","BOURSE","VISA","TRAD"],
 etapes=[
  ("Candidater sur Study in India", "Portail unique d'admission pour les internationaux.", "https://www.studyinindia.gov.in", "ADMIS"),
  ("Ou viser la bourse ICCR", "Scolarité + logement + allocation — via l'ambassade de l'Inde.", "https://www.iccr.gov.in", "BOURSE"),
  ("Visa étudiant", "Admission + fonds.", None, "VISA"),
 ],
 bourses=[("ICCR", "Complète (Afrique, Asie, Caraïbes).", "https://www.iccr.gov.in")])

D["PK"] = dict(nom="Pakistan", flag="🇵🇰",
 resume="Universités anglophones à frais très bas ; accueil organisé par la HEC et accords bilatéraux.",
 ressources="≈2 000 €/an suffisent",
 travail="Limité", post="Selon visa",
 portail="https://www.hec.gov.pk",
 services=["ORIENT","ADMIS","DOSSIER","VISA","TRAD"],
 etapes=[
  ("Candidater via la HEC / universités", "La Higher Education Commission centralise l'accueil international.", "https://www.hec.gov.pk", "ADMIS"),
  ("Visa étudiant", "Admission + NOC selon programme.", None, "VISA"),
 ],
 bourses=[("Bourses HEC / accords bilatéraux", "Selon conventions avec ton pays.", "https://www.hec.gov.pk")])

D["ID"] = dict(nom="Indonésie", flag="🇮🇩",
 resume="Bourse KNB dédiée aux pays en développement : scolarité + allocation + billets. "
        "Darmasiswa : 1 an de langue et culture, sans condition de diplôme.",
 ressources="Couvert si KNB · sinon ≈2 500 €/an",
 travail="Non autorisé", post="Limité",
 portail="https://knb.kemdikbud.go.id",
 services=["ORIENT","DOSSIER","BOURSE","VISA","TRAD"],
 etapes=[
  ("Candidater à la KNB (janv–mars)", "Via l'ambassade d'Indonésie + portail officiel.", "https://knb.kemdikbud.go.id", "BOURSE"),
  ("Visa études (KITAS)", "Après acceptation.", None, "VISA"),
 ],
 bourses=[("KNB Scholarship", "Complète, licence/master/doctorat.", "https://knb.kemdikbud.go.id"),
          ("Darmasiswa", "1 an langue & culture.", "https://darmasiswa.kemdikbud.go.id")])

D["MY"] = dict(nom="Malaisie", flag="🇲🇾",
 resume="Hub anglophone : campus de Monash, Nottingham… à 1 500–8 000 €/an. Visa 100 % en ligne (EMGS).",
 ressources="≈5 000 €/an",
 travail="20 h/sem (vacances surtout)", post="Limité",
 portail="https://educationmalaysia.gov.my",
 services=["ORIENT","ADMIS","DOSSIER","VISA","TRAD"],
 etapes=[
  ("Admission + visa via EMGS", "La plateforme nationale gère tout le processus étudiant.", "https://educationmalaysia.gov.my", "ADMIS"),
 ],
 bourses=[("Malaysia International Scholarship", "Master/doctorat.", "https://biasiswa.mohe.gov.my")])

D["TH"] = dict(nom="Thaïlande", flag="🇹🇭",
 resume="Programmes internationaux en anglais à frais modérés, cadre de vie exceptionnel.",
 ressources="≈5 000 €/an", travail="Restreint", post="Limité",
 portail="https://www.studyinthailand.org",
 services=["ORIENT","ADMIS","DOSSIER","VISA","TRAD"],
 etapes=[
  ("Candidater aux 'international colleges'", "Admission directe.", None, "ADMIS"),
  ("Visa ED", "Admission + fonds.", None, "VISA"),
 ],
 bourses=[("Bourses d'universités (AIT, Chula…)", "Selon programmes.", None)])

D["AU"] = dict(nom="Australie", flag="🇦🇺",
 resume="Salaires étudiants élevés (48 h/quinzaine autorisées) et visa post-études généreux.",
 ressources="≈24 505 AUD/an + scolarité (20 000–45 000 AUD/an)",
 travail="48 h/quinzaine", post="Temporary Graduate Visa 2–6 ans",
 portail="https://www.studyaustralia.gov.au",
 services=["ORIENT","ADMIS","DOSSIER","FONDS","VISA","BOURSE","TRAD","PACK"],
 etapes=[
  ("Admission CRICOS + assurance OSHC", "", "https://cricos.education.gov.au", "ADMIS"),
  ("Visa 500 avec test Genuine Student", "Déclaration écrite décisive + fonds.", "https://immi.homeaffairs.gov.au", "VISA"),
 ],
 bourses=[("Australia Awards", "Complète (Afrique, Asie, Pacifique).", "https://www.australiaawards.gov.au")])

D["BR"] = dict(nom="Brésil", flag="🇧🇷",
 resume="PEC-G / PEC-PG : places GRATUITES dans les universités publiques pour les pays "
        "en développement partenaires (Afrique, Caraïbes dont Haïti, Amérique latine).",
 ressources="Scolarité gratuite (PEC-G) — prévoir ≈1 500 BRL/mois pour vivre",
 travail="Non autorisé (PEC-G)", post="Retour prévu par le programme",
 portail="https://www.gov.br/mre",
 services=["ORIENT","DOSSIER","TRAD","VISA"],
 etapes=[
  ("Candidater au PEC-G via l'ambassade du Brésil", "Dossier annuel (souvent juin–juillet).", "https://www.gov.br/mre/pt-br/assuntos/cooperacao-internacional/pec-g", "DOSSIER"),
  ("Certificat de portugais CELPE-Bras", "Ou année de langue sur place.", None, None),
  ("Visa VITEM-IV", "Après sélection.", None, "VISA"),
 ],
 bourses=[("PEC-G / PEC-PG", "Scolarité gratuite + bourses complémentaires possibles (Milton Santos).", "https://www.gov.br/mre")])

D["MA"] = dict(nom="Maroc", flag="🇲🇦",
 resume="Bourses AMCI pour l'Afrique subsaharienne : scolarité gratuite + allocation + campus. "
        "Filières en français, proximité culturelle.",
 ressources="Couvert si AMCI · sinon ≈2 800 €/an",
 travail="Limité", post="Selon convention",
 portail="https://www.amci.ma",
 services=["ORIENT","DOSSIER","BOURSE","TRAD"],
 etapes=[
  ("Candidater à l'AMCI", "Via le ministère de ton pays ou l'ambassade du Maroc — dossier annuel.", "https://www.amci.ma", "BOURSE"),
  ("Inscription + séjour", "Beaucoup de nationalités africaines sont exemptées de visa.", None, None),
 ],
 bourses=[("AMCI", "Scolarité + allocation + logement campus.", "https://www.amci.ma")])

D["TN"] = dict(nom="Tunisie", flag="🇹🇳",
 resume="Filières santé et ingénierie en français à coût très bas ; places subventionnées "
        "pour l'Afrique subsaharienne via la coopération.",
 ressources="≈2 500 €/an",
 travail="Limité", post="Selon convention",
 portail="https://www.mes.tn",
 services=["ORIENT","ADMIS","DOSSIER","TRAD"],
 etapes=[
  ("Candidater via la coopération / directement", "Ministère de ton pays ou ambassade de Tunisie.", None, "ADMIS"),
  ("Carte de séjour étudiant", "Après l'arrivée.", None, None),
 ],
 bourses=[("Bourses de coopération tunisienne", "Selon accords bilatéraux.", None)])

D["SN"] = dict(nom="Sénégal", flag="🇸🇳",
 resume="Hub universitaire francophone de la région (UCAD, UGB, grandes écoles privées reconnues).",
 ressources="≈1 500 000 FCFA/an",
 travail="Possible", post="Marché régional dynamique",
 portail="https://www.campusen.sn",
 services=["ORIENT","ADMIS","DOSSIER"],
 etapes=[
  ("Candidater via Campusen ou directement", "Plateforme nationale d'orientation.", "https://www.campusen.sn", "ADMIS"),
  ("Séjour étudiant", "Formalités simplifiées pour la CEDEAO.", None, None),
 ],
 bourses=[("Bourses de coopération + établissements", "Selon accords.", None)])

D["RW"] = dict(nom="Rwanda", flag="🇷🇼",
 resume="La destination tech montante d'Afrique : ALU, Carnegie Mellon Africa, University of Rwanda. "
        "Visa ultra simplifié pour les Africains.",
 ressources="≈2 000 000 RWF/an",
 travail="Possible", post="Hub technologique régional",
 portail="https://www.ur.ac.rw",
 services=["ORIENT","ADMIS","DOSSIER","BOURSE"],
 etapes=[
  ("Candidater directement (ALU, CMU-Africa, UR)", "", "https://www.ur.ac.rw", "ADMIS"),
  ("Visa en ligne (Irembo)", "Procédure simple et rapide.", "https://irembo.gov.rw", None),
 ],
 bourses=[("MasterCard Foundation / ALU", "Bourses complètes pour Africains sur critères.", "https://mastercardfdn.org/all/scholars/")])

D["GH"] = dict(nom="Ghana", flag="🇬🇭",
 resume="Universités anglophones réputées (Legon, KNUST, Ashesi) — le bon plan pour étudier en anglais en Afrique.",
 ressources="≈2 000 €/an",
 travail="Limité", post="Marché régional",
 portail="https://www.ug.edu.gh",
 services=["ORIENT","ADMIS","DOSSIER","BOURSE"],
 etapes=[
  ("Candidater directement", "Portails des universités.", "https://www.ug.edu.gh", "ADMIS"),
  ("Visa + residence permit", "Après admission.", None, None),
 ],
 bourses=[("MasterCard Foundation (Ashesi…)", "Bourses complètes sur critères.", "https://mastercardfdn.org/all/scholars/")])

D["ZA"] = dict(nom="Afrique du Sud", flag="🇿🇦",
 resume="Les meilleures universités du continent (UCT, Wits, Stellenbosch) à frais internationaux modérés.",
 ressources="≈120 000 ZAR/an + scolarité",
 travail="20 h/semaine", post="Critical skills visa possible",
 portail="https://www.universitiessa.ac.za",
 services=["ORIENT","ADMIS","DOSSIER","VISA","TRAD"],
 etapes=[
  ("Candidater tôt (deadlines juin–sept)", "Directement auprès des universités.", None, "ADMIS"),
  ("Study visa", "Admission + fonds + assurance médicale sud-africaine.", None, "VISA"),
 ],
 bourses=[("Bourses d'universités + MasterCard Foundation", "Selon campus.", None)])

D["EG"] = dict(nom="Égypte", flag="🇪🇬",
 resume="Portail national unifié + bourses Al-Azhar complètes ; frais publics très bas.",
 ressources="≈2 000 €/an",
 travail="Limité", post="Selon titre",
 portail="https://admission.study-in-egypt.gov.eg",
 services=["ORIENT","ADMIS","DOSSIER","BOURSE","TRAD"],
 etapes=[
  ("Candidater sur Study in Egypt", "Portail gouvernemental unique.", "https://admission.study-in-egypt.gov.eg", "ADMIS"),
  ("Visa étudiant", "Après admission.", None, None),
 ],
 bourses=[("Bourses Al-Azhar", "Complètes, via les ambassades.", None)])

D["SA"] = dict(nom="Arabie Saoudite", flag="🇸🇦",
 resume="Bourses complètes fréquentes (logement + allocation + billets). KAUST : 20–30 000 $/an pour la recherche.",
 ressources="Souvent couvert par la bourse",
 travail="Restreint", post="Selon secteur",
 portail="https://studyinsaudi.moe.gov.sa",
 services=["ORIENT","DOSSIER","BOURSE","TRAD"],
 etapes=[
  ("Candidater via Study in Saudi / universités", "", "https://studyinsaudi.moe.gov.sa", "BOURSE"),
  ("Visa pris en charge si bourse", "", None, None),
 ],
 bourses=[("KAUST Fellowship", "Master/PhD : scolarité + 20–30 k$/an + logement.", "https://www.kaust.edu.sa"),
          ("Université islamique de Médine", "Complète + billets.", None)])

D["AE"] = dict(nom="Émirats Arabes Unis", flag="🇦🇪",
 resume="NYU Abu Dhabi finance à 100 % les admis qui en ont besoin. Visa sponsorisé par l'université.",
 ressources="Couvert si bourse · sinon élevé",
 travail="Autorisé avec NOC", post="Golden visa possible pour l'excellence",
 portail="https://www.moe.gov.ae",
 services=["ORIENT","ADMIS","DOSSIER","BOURSE"],
 etapes=[
  ("Candidater (NYUAD via Common App…)", "", "https://nyuad.nyu.edu", "ADMIS"),
  ("Visa sponsorisé par l'université", "", None, None),
 ],
 bourses=[("NYU Abu Dhabi full-need", "Couvre tout — ultra sélective.", "https://nyuad.nyu.edu")])

D["QA"] = dict(nom="Qatar", flag="🇶🇦",
 resume="Education City : Georgetown, Carnegie Mellon, HEC Paris… avec bourses HBKU complètes.",
 ressources="Couvert si bourse · sinon élevé",
 travail="Restreint", post="Selon secteur",
 portail="https://www.edu.gov.qa",
 services=["ORIENT","ADMIS","DOSSIER","BOURSE"],
 etapes=[
  ("Candidater (HBKU / Education City)", "", "https://www.hbku.edu.qa", "ADMIS"),
  ("Visa sponsorisé", "Par l'établissement.", None, None),
 ],
 bourses=[("HBKU / Qatar Foundation", "Complètes selon programmes.", "https://www.hbku.edu.qa")])

D["CH"] = dict(nom="Suisse", flag="🇨🇭",
 resume="EPFL/ETH parmi les meilleures du monde pour 1 500 CHF/an de frais — mais coût de vie très élevé.",
 ressources="21 000 CHF/an à justifier",
 travail="15 h/sem (après 6 mois)", post="6 mois de recherche d'emploi",
 portail="https://www.swissuniversities.ch",
 services=["ORIENT","ADMIS","DOSSIER","FONDS","VISA","BOURSE","TRAD"],
 etapes=[
  ("Candidater (déc–avril)", "EPFL, ETH, universités cantonales.", None, "ADMIS"),
  ("Visa D + attestation financière", "21 000 CHF/an.", None, "FONDS"),
 ],
 bourses=[("Bourses d'excellence de la Confédération", "Master/PhD chercheurs.", "https://www.sbfi.admin.ch")])

D["SE"] = dict(nom="Suède", flag="🇸🇪",
 resume="Tout en anglais, candidature centralisée, travail étudiant ILLIMITÉ, bourses SI très généreuses.",
 ressources="≈129 000 SEK/an (norme Migrationsverket)",
 travail="Illimité pour les étudiants", post="12 mois de recherche d'emploi",
 portail="https://studyinsweden.se",
 services=["ORIENT","ADMIS","DOSSIER","FONDS","BOURSE","PACK"],
 etapes=[
  ("Candidater sur universityadmissions.se (janvier)", "Plateforme centralisée (900 SEK).", "https://www.universityadmissions.se", "ADMIS"),
  ("Permis de séjour études", "En ligne : fonds + assurance.", None, "FONDS"),
 ],
 bourses=[("SI Scholarships for Global Professionals", "Master complet, pays ciblés.", "https://si.se/en/apply/scholarships/")])

D["IE"] = dict(nom="Irlande", flag="🇮🇪",
 resume="Anglophone, en zone euro, siège européen de Google/Meta/Apple : le tremplin tech.",
 ressources="≈10 000 €/an + scolarité (10–25 000 €/an)",
 travail="20 h/semaine", post="Stamp 1G : 1–2 ans pour travailler",
 portail="https://www.educationinireland.com",
 services=["ORIENT","ADMIS","DOSSIER","FONDS","VISA","BOURSE"],
 etapes=[
  ("Candidater (CAO ou direct)", "", "https://www.cao.ie", "ADMIS"),
  ("Visa D study", "Admission + fonds + assurance.", None, "VISA"),
 ],
 bourses=[("Government of Ireland Intl Scholarship", "10 000 € + frais offerts (60/an).", "https://hea.ie")])

# =============================================================================
# BASE (pays actifs + demandes)
# =============================================================================
def db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS config_pays(code TEXT PRIMARY KEY, actif INT DEFAULT 1)")
    con.execute("""CREATE TABLE IF NOT EXISTS leads(
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, nom TEXT, contact TEXT,
        origine TEXT, destination TEXT, service TEXT, message TEXT)""")
    for code in D:
        con.execute("INSERT OR IGNORE INTO config_pays(code,actif) VALUES(?,1)", (code,))
    con.commit()
    return con

con = db()
actifs = {r[0] for r in con.execute("SELECT code FROM config_pays WHERE actif=1")}

if "svc" not in st.session_state: st.session_state.svc = None

# =============================================================================
# EN-TÊTE
# =============================================================================
st.markdown(f"""
<div style='text-align:center; padding:.4rem 0 .8rem;'>
  <h1 style='margin-bottom:0; font-size:2.7rem;'>🚀 {APP_NAME}</h1>
  <p style='color:#6b7280; margin-top:.15rem; font-size:1.05rem;'>{t('tagline', LG)}</p>
</div>""", unsafe_allow_html=True)

# ---------- Listes traduites (affichage) + valeurs canoniques (logique) ----------
T_TYPES    = T["types"][LG]
T_NIVEAUX  = T["niveaux"][LG]
T_DOMAINES = T["domaines"][LG]
CANON_TYPES   = T["types"]["fr"]
CANON_NIVEAUX = T["niveaux"]["fr"]
CANON_DOM     = T["domaines"]["fr"]

# =============================================================================
# LE PARCOURS — 4 questions
# =============================================================================
c1, c2 = st.columns(2)
origine = c1.selectbox(t("q_origine", LG), [t("choisir", LG)] + sorted(ORIGINES.keys()))
dest_codes = sorted([c for c in D if c in actifs], key=lambda c: D[c]["nom"])
destination = c2.selectbox(t("q_dest", LG), [t("choisir", LG)] + dest_codes,
    format_func=lambda c: c if c == t("choisir", LG) else f"{D[c]['flag']} {D[c]['nom']}")
c3, c4 = st.columns(2)
type_ = c3.selectbox(t("q_type", LG), [t("choisir", LG)] + T_TYPES)
niveau = c4.selectbox(t("q_niveau", LG), [t("choisir", LG)] + T_NIVEAUX)
domaine = st.selectbox(t("q_domaine", LG), T_DOMAINES)

st.divider()

# =============================================================================
# RÉSULTAT
# =============================================================================
if t("choisir", LG) in (origine, destination, type_, niveau):
    st.info(t("intro", LG))
else:
    d = D[destination]
    code_orig, dev_orig = ORIGINES[origine]
    # Convertir les choix affichés (traduits) en valeurs canoniques FR pour la logique
    type_c   = CANON_TYPES[T_TYPES.index(type_)]     if type_   in T_TYPES   else type_
    niveau_c = CANON_NIVEAUX[T_NIVEAUX.index(niveau)] if niveau in T_NIVEAUX else niveau
    domaine_c= CANON_DOM[T_DOMAINES.index(domaine)]   if domaine in T_DOMAINES else domaine

    # ---- Prix d'appel = service le moins cher proposé pour cette destination
    prix_min_fcfa = min(SVC[s][2] for s in d["services"])
    prix_local = conv(prix_min_fcfa, "XOF", dev_orig)
    if dev_orig in ("XOF", "XAF") or prix_local is None:
        prix_txt = f"{prix_min_fcfa:,} FCFA".replace(",", " ")
    else:
        prix_txt = f"{prix_local:,.0f} {dev_orig}".replace(",", " ")

    # ---- Bandeau héro marketing
    st.markdown(f"""
<div class='hero'>
  <h2>{d['flag']} {origine} → {d['nom']}</h2>
  <p>{d['resume']}</p>
  <span class='prix'>{t("start_from", LG)} {prix_txt}</span>
</div>""", unsafe_allow_html=True)

    st.markdown(
        f"<span class='badge'>{type_}</span><span class='badge'>{niveau}</span>"
        + (f"<span class='badge'>{domaine}</span>" if domaine_c != "Tous les domaines" else ""),
        unsafe_allow_html=True)

    colA, colB = st.columns(2)
    colA.markdown(f"**{t('budget', LG)}** {d['ressources']}")
    colB.markdown(f"**{t('travail', LG)}** {d['travail']}")
    st.markdown(f"**{t('apres', LG)}** {d['post']}")

    # ---- Bourses d'abord si le projet est "Bourse"
    if type_c == "Bourse":
        st.markdown("### " + t("bourses_pour_toi", LG))
        for nom_b, det, lien in d["bourses"]:
            with st.expander(f"💰 {nom_b}", expanded=True):
                st.write(det)
                if lien: st.markdown(f"[🔗 Site officiel]({lien})")

    if type_c == "Stage / Emploi étudiant":
        st.success(f"💼 En {d['nom']}, tu peux travailler **{d['travail']}** pendant tes études, "
                   f"et après le diplôme : {d['post']}. La porte d'entrée reste le statut étudiant :")

    # ---- Étapes (adaptées à l'origine pour la France)
    st.markdown("### " + t("chemin", LG))
    if destination == "FR":
        etapes = d["etapes_eef"] if code_orig in EEF else d["etapes_std"]
        if code_orig in EEF:
            st.caption(f"ℹ️ En tant que ressortissant·e du pays « {origine} », ta procédure "
                       f"passe par **Campus France / Études en France**. Voici exactement comment ça se déroule :")
    else:
        etapes = d["etapes"]

    for i, etape in enumerate(etapes, 1):
        titre, det, lien, svc_code = (etape + (None,))[:4] if len(etape) == 3 else etape
        with st.expander(f"{t('etape', LG)} {i} — {titre}", expanded=(i == 1)):
            st.write(det)
            if lien:
                st.markdown(f"[{t('lien_officiel', LG)}]({lien})")
            if svc_code and svc_code in d["services"]:
                if st.button(t("aide_etape", LG),
                             key=f"btn_{i}_{svc_code}"):
                    st.session_state.svc = svc_code

    st.link_button(f"{t('portail', LG)} {d['nom']}", d["portail"])

    # ---- Bloc accompagnement (services filtrés par destination, SANS prix)
    st.markdown("---")
    st.markdown(f"## {t('accompagne', LG)} {d['nom']}")
    st.write(t("accompagne_desc", LG))

    noms_services = []
    for s in d["services"]:
        nom_s, desc_s, _ = SVC[s]
        noms_services.append(nom_s)
        ouvert = (st.session_state.svc == s)
        with st.expander(nom_s, expanded=ouvert):
            st.write(desc_s)

    st.markdown("#### " + t("form_titre", LG))
    with st.form("lead"):
        f1, f2 = st.columns(2)
        nom_lead = f1.text_input(t("nom", LG))
        contact = f2.text_input(t("contact", LG))
        pre = 0
        if st.session_state.svc and SVC[st.session_state.svc][0] in noms_services:
            pre = noms_services.index(SVC[st.session_state.svc][0])
        service_choisi = st.selectbox(t("service_interet", LG), noms_services, index=pre)
        msg = st.text_area(t("projet_2lignes", LG))
        ok = st.form_submit_button(t("lancer", LG))
        if ok:
            if nom_lead.strip() and contact.strip():
                con.execute("INSERT INTO leads(date,nom,contact,origine,destination,service,message) "
                            "VALUES(?,?,?,?,?,?,?)",
                            (TODAY, nom_lead, contact, origine, d["nom"], service_choisi, msg))
                con.commit()
                st.success(t("recu", LG))
                st.balloons()
            else:
                st.error(t("champs_requis", LG))

    st.caption(t("disclaimer", LG))

# =============================================================================
# ADMIN
# =============================================================================
with st.sidebar:
    st.markdown(f"### {APP_NAME} · Admin")
    pwd = st.text_input("Mot de passe", type="password")
    if pwd == ADMIN_PWD:
        st.success("Mode admin")
        st.markdown("**Pays visibles :**")
        for code in sorted(D, key=lambda c: D[c]["nom"]):
            etat = code in actifs
            nouveau = st.checkbox(f"{D[code]['flag']} {D[code]['nom']}", value=etat, key=f"adm_{code}")
            if nouveau != etat:
                con.execute("UPDATE config_pays SET actif=? WHERE code=?", (1 if nouveau else 0, code))
                con.commit(); st.rerun()
        st.markdown("---")
        st.markdown("**📥 Demandes clients (15 dernières) :**")
        rows = con.execute("SELECT date,nom,contact,origine,destination,service "
                           "FROM leads ORDER BY id DESC LIMIT 15").fetchall()
        for r in rows:
            st.write(f"• {r[0]} — **{r[1]}** ({r[2]}) : {r[3]} → {r[4]} · {r[5]}")
        if not rows: st.caption("Aucune demande pour l'instant.")
        st.markdown("---")
        st.markdown("**💰 Grille interne (jamais affichée aux clients) :**")
        for code_s, (nom_s, _, prix) in SVC.items():
            st.caption(f"{nom_s} : {prix:,} FCFA".replace(",", " "))
    elif pwd:
        st.error("Mot de passe incorrect")
