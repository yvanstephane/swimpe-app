# =============================================================================
# YORBITY — Ta trajectoire vers le monde (multilingue, détection auto)
# - Parcours guidé 4 questions → conditions d'admission déroulées (style Campus France)
# - Procédure adaptée au pays d'ORIGINE (ex : Gabon → France = Études en France)
# - Services d'accompagnement PAR DESTINATION, intégrés aux étapes, sans prix affichés
# - Bandeau marketing « Commence ton projet à partir de X » (service le moins cher)
# - Admin : activer/désactiver pays + voir les demandes (mot de passe .env)
# Lancement : streamlit run app/api/ui.py
# =============================================================================
# --- Secrets (.env) : charges AVANT tout import applicatif ---
try:
    from pathlib import Path as _PathEnv
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(_PathEnv(__file__).resolve().parents[2] / ".env")
except Exception:
    pass

import sqlite3, os, datetime

# --- Verrous SQLite : patience globale (patch_verrous) ------------------------
# Toute connexion ouverte par N'IMPORTE QUEL module de ce processus recoit
# timeout=30 s + busy_timeout=30 s (sauf timeout explicite de l'appelant).
# Streamlit relance ce script a chaque interaction : les acces concurrents
# attendent leur tour au lieu de lever « database is locked ».
if not getattr(sqlite3, "_yorbity_patience", False):
    _sq_connect_origine = sqlite3.connect

    def _sq_connect_patient(*args, **kwargs):
        kwargs.setdefault("timeout", 30)
        con = _sq_connect_origine(*args, **kwargs)
        try:
            con.execute("PRAGMA busy_timeout=30000")
        except Exception:
            pass
        return con

    sqlite3.connect = _sq_connect_patient
    sqlite3._yorbity_patience = True
# ------------------------------------------------------------------------------
import streamlit as st
from i18n import t, T, detecter_langue, LANGUES, RTL
from pays_i18n import nom_pays
import espace, auth, dossiers, services_cfg, config_projets, admin_projets, admin_comptes, mdp_oublie, opportunites_ui, offres_cfg, devises_cfg, eligibilite, offres_sync, recherche_poste, moteur_plans, console_accompagnement
from traduction import traduire
import autotrad  # traduction automatique globale (la langue prime sur tout)

# Libellés du projet « Métier spécialisé » dans toutes les langues (grise le niveau)
_METIER_LBLS = {v[3] for v in T["types"].values() if len(v) > 3}
# Accroche du bandeau selon le type de projet (le résumé études reste pour Formation)
_PITCH_PROJET = {
    "Bourse": "Bourses accessibles selon ton pays d'origine — sélection mise à jour en continu.",
    "Stage / Emploi étudiant": "Offres de stage et d'emploi étudiant ouvertes à ton profil — mises à jour en continu.",
    "Métier spécialisé": "Postes pour travailleurs qualifiés ouverts aux candidats internationaux — mis à jour en continu.",
}

APP_NAME = "Yorbity"
TAGLINE = "Ta trajectoire vers le monde"
DB = "data/mobilite.db"
ADMIN_PWD = os.environ.get("ADMIN_PASSWORD") or None  # fail-closed : admin verrouille si variable absente
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

# ---------- Compte utilisateur (sidebar + écran auth) ----------
espace.bloc_compte_sidebar()
if espace.user_connecte():
    with st.sidebar:
        if st.button(t("mes_projets", LG), use_container_width=True):
            st.session_state.show_espace = True
            st.rerun()
        try:  # patch_monetisation : bouton Premium masque tant que monetisation OFF
            import offres_sync as _osy_mon
            _mon_on = _osy_mon.param("monetisation_active", "0") != "0"
        except Exception:
            _mon_on = False
        if _mon_on and st.button(t("btn_premium", LG), use_container_width=True):
            st.session_state.show_premium = True
        try:  # patch_plans_visiteur : bouton visiteur (masque si vue coupee)
            import offres_sync as _osy_pvb
            _pv_on = _osy_pvb.param("plans_visiteur_actif", "0") != "0"
        except Exception:
            _pv_on = True
        if _pv_on and st.button("🗺️ " + traduire("Programmes d'accompagnement",
                                st.session_state.get("lang", "fr")),
                                use_container_width=True, key="btn_pv"):
            st.session_state.show_programmes = True
            st.rerun()
        if st.button("📋 " + traduire("Mes démarches", st.session_state.get("lang","fr")), use_container_width=True):
            st.session_state.show_demarches = True
            st.rerun()
        if espace.est_admin():
            if st.button("🛠 " + traduire("Gestion des dossiers", st.session_state.get("lang","fr")), use_container_width=True):
                st.session_state.show_gestion = True
                st.rerun()
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
.badge {display:inline-block; background:rgba(59,130,246,.16);
  color:var(--text-color); border:1px solid rgba(59,130,246,.4); border-radius:999px;
  padding:.18rem .75rem; font-size:.88rem; margin-right:.4rem;}
div[data-testid="stExpander"] {border-radius:12px;
  border:1px solid rgba(128,128,128,.35); margin-bottom:.4rem;}
/* --- Lisibilite (patch_lisibilite) : tailles + couleurs liees au theme --- */
div[data-testid="stWidgetLabel"] p, div[data-testid="stWidgetLabel"] label {
  font-size:1.06rem !important; font-weight:600;
  color:var(--text-color) !important;}
div[data-baseweb="select"] div {font-size:1.04rem !important;}
li[role="option"], ul[data-testid="stSelectboxVirtualDropdown"] li {
  font-size:1.04rem !important;}
div[data-testid="stExpander"] summary p {
  font-size:1.06rem !important; font-weight:600;
  color:var(--text-color) !important;}
div[data-testid="stExpander"] p, div[data-testid="stExpander"] li {
  font-size:1.0rem; color:var(--text-color);}
div[data-testid="stCaptionContainer"] p {font-size:.95rem !important;
  color:var(--text-color) !important; opacity:.8;}
div[data-testid="stMarkdownContainer"] p {color:var(--text-color);}
</style>""", unsafe_allow_html=True)

# ---------- Taux internes (uniquement pour le prix d'appel) ----------
R = 655.96  # FCFA/EUR (taux fixe depuis 1999)
TAUX = {"EUR":1.0,"USD":1.08,"XOF":655.96,"XAF":655.96,"CAD":1.47,"GBP":0.85,
        "MAD":10.8,"TND":3.4,"NGN":1650,"GHS":16,"KES":140,"HTG":145,"INR":92,
        "PKR":300,"IDR":17500,"BRL":6.0,"RWF":1420,"CDF":2900,"EGP":52,"ZAR":19.5}
def conv(m, de, vers):
    if de in TAUX and vers in TAUX: return m / TAUX[de] * TAUX[vers]
    return None

with st.sidebar:
    st.session_state.setdefault("devise", "EUR")  # devise auto par destination — selecteur retire (patch_jobboard2)

# ---------- Pays d'origine (nom → code, devise locale) ----------
# --- Tri des noms sans accents (Sénégal, Bénin retrouvent leur place) ---
_ACCENTS = str.maketrans(
    "àáâãäåçèéêëìíîïñòóôõöùúûüýÿ",
    "aaaaaaceeeeiiiinooooouuuuyy")
def _tri_sans_accents(_s):
    return _s.lower().translate(_ACCENTS)


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

# --- Toutes les origines du monde (fusion : n'écrase pas les existantes) ---
try:
    from pays_monde import ORIGINES_MONDE
    for _p, _v in ORIGINES_MONDE.items():
        ORIGINES.setdefault(_p, _v)
except ImportError:
    pass

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
             "rendez-vous, préparation des justificatifs, suivi jusqu'au dépôt + une relance.", 20000),
 "LOGEMENT":("🏠 Recherche de logement & attestation",
             "Dossier locataire, candidatures résidences/CROUS/privé et obtention de "
             "l'attestation d'hébergement exigée pour le visa.", 25000),
 "BOURSE":  ("💰 Chasse aux bourses ciblée",
             "Identification des bourses auxquelles TON profil est éligible et aide "
             "complète au montage de 2 dossiers.", 20000),
 "TRAD":    ("📑 Traductions certifiées & légalisations",
             "Coordination des traductions assermentées, apostilles et "
             "authentifications exigées par ta destination.", 10000),
# patch_pack_retire : PACK retire du catalogue tant que les heures
# reelles ne sont pas mesurees (remise de 63 % sur la somme des parties
# = travail a perte). Pour le reactiver : retirer les '# ' ci-dessous.
# "PACK":    ("🚀 Pack complet « Décollage »",
#              "On gère tout ton projet de bout en bout : orientation, admissions, "
#              "dossier, fonds, visa, installation. Toi, tu prépares ta valise.", 89000),
}

# --- Services applicables PAR TYPE DE PROJET (patch_jobboard2) ---------------
# Cle absente = service propose pour tous les types de projet.
SVC_TYPES = {
    "ADMIS":    {"Formation (admission)"},
    "EEF":      {"Formation (admission)"},
    "PACK":     {"Formation (admission)"},
    "ORIENT":   {"Formation (admission)", "Bourse"},
    "BOURSE":   {"Formation (admission)", "Bourse"},
    "FONDS":    {"Formation (admission)", "Stage / Emploi étudiant"},
    "VISA":     {"Formation (admission)", "Stage / Emploi étudiant", "Métier spécialisé"},
    "LOGEMENT": {"Formation (admission)", "Stage / Emploi étudiant", "Métier spécialisé"},
    "FLUSSI":   {"Métier spécialisé"},  # _lot6_parcours_v1 : étiquette étapes travail
}


def _services_pour_type(codes, type_projet):
    """Ne garde que les services pertinents pour CE type de projet.
    Repli : si le filtre vide tout, on rend la liste d'origine."""
    filt = [s for s in codes if type_projet in SVC_TYPES.get(s, {type_projet})]
    return filt or list(codes)


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
 resume="Le choix naturel des francophones : frais modérés (835–4 175 €/an), universités réputées. "
        "Deux bourses entièrement financées s'adressent directement aux Africains : ARES (Belgique, "
        "Bac+3/Bac+5, 20 pays partenaires) et MasterCard Foundation Scholars (mondial, jusqu'à 35 ans).",
 ressources="≈650 €/mois à justifier",
 travail="20 h/semaine", post="Séjour de recherche d'emploi possible",
 portail="https://www.studyinbelgium.be",
 services=["ORIENT","ADMIS","DOSSIER","FONDS","VISA","BOURSE","TRAD","PACK"],
 etapes=[
  ("Faire reconnaître ton diplôme (équivalence FWB)", "Dossier à déposer TÔT : 3–4 mois de délai, indispensable pour s'inscrire.", "https://www.equivalences.cfwb.be", "TRAD"),
  ("S'inscrire à l'université", "Candidatures juin–septembre pour la rentrée d'octobre.", None, "ADMIS"),
  ("Visa D étudiant", "Admission + équivalence + fonds + assurance.", None, "VISA"),
 ],
 bourses=[
  # ── ARES ──────────────────────────────────────────────────────────────────
  ("🇧🇪 Bourses ARES — coopération belge",
   "200 bourses entièrement financées/an : Bachelier ou Master de spécialisation (1 an) "
   "ou Formation continue (2–6 mois) dans les universités FWB (ULB, UCLouvain, ULiège, "
   "UNamur, HE Vinci…). Couverture : inscription + 1 150 €/mois × 12 + billet A/R + visa "
   "+ assurance. "
   "Conditions : résider ET travailler dans l'un des 31 pays éligibles · Bac+3 minimum · "
   "≥ 2 ans d'expérience professionnelle après le diplôme · diplôme ≤ 20 ans · "
   "1 seule candidature · GRATUIT (fraude → bourses-cooperation@ares-ac.be). "
   "Pays africains éligibles (20/31) : Afrique du Sud, Bénin, Burkina Faso, Burundi, "
   "Cameroun, Éthiopie, Guinée, Kenya, Madagascar, Mali, Maroc, Mozambique, Niger, "
   "Ouganda, RDC, Rwanda, Sénégal, Tanzanie, Tunisie, Zimbabwe. "
   "ABSENTS : Congo-Brazzaville, Gabon, Tchad, Togo, Guinée équatoriale. "
   "⚠️ Pas de critère d'âge — le '40 ans max' circulant sur les réseaux est FAUX. "
   "Calendrier : appel ~4 août → clôture ~mi-septembre (plateforme GIRAF). "
   "Préparer le dossier DÈS MAINTENANT.",
   "https://www.ares-ac.be/fr/bourses"),
  # ── MasterCard Foundation ──────────────────────────────────────────────────
  ("🌍 MasterCard Foundation Scholars Program",
   "L'un des plus grands programmes de bourses au monde (50 000+ boursiers, objectif 100 000 "
   "d'ici 2030, 71 % de femmes). Entièrement financé : frais de scolarité + logement + "
   "matériel + transport + assurance + mentorat. Niveaux : Secondaire, Bachelor (≤ 29 ans), "
   "Master (≤ 35 ans). Réservé aux citoyens africains — réfugiés inclus. "
   "EXCLUS : double nationalité ou résidence permanente US/Canada/UK/UE. "
   "62+ universités partenaires dont Sciences Po (Paris), Cambridge, McGill, Toronto, "
   "UC Berkeley, CMU-Africa, Makerere, KNUST, Univ. Rwanda… "
   "Candidature DÉCENTRALISÉE : postuler directement auprès de chaque université partenaire "
   "(chacune a son calendrier, sept → janv pour une rentrée 2027). "
   "⚠️ ALERTE OFFICIELLE : des posts Facebook frauduleux 'recrutent' en demandant des frais. "
   "Le programme ne demande JAMAIS d'argent. Signalement : privacy@mastercardfdn.org.",
   "https://mastercardfdn.org/en/what-we-do/our-programs/mastercard-foundation-scholars-program/where-to-apply/"),
 ])

D["IT"] = dict(nom="Italie", flag="🇮🇹",
 resume="Études en Italie : frais calculés sur tes revenus, souvent 500–3 000 €/an, "  # _lot7_desc_italie_v1
        "avec les bourses régionales DSU. Inscription via la plateforme officielle Universitaly. "
        "Coût de la vie modéré et diplômes reconnus dans toute l'Europe.",
 ressources="≈6 500 €/an à justifier pour le visa (hors bourse DSU).",
 travail="20 h/semaine autorisées pendant les études.",
 post="Permesso de recherche d'emploi 12 mois après le diplôme.",
 portail="https://studyinitaly.esteri.it",
 services=["ORIENT","ADMIS","DOSSIER","BOURSE","VISA","TRAD","PACK"],
 etapes=[
  ("Pré-inscription sur Universitaly", "La plateforme officielle reliée à ton consulat — l'équivalent italien de Campus France.", "https://www.universitaly.it", "ADMIS"),
  ("Demander la bourse régionale DSU", "Sur critères sociaux : logement + cantine + ~5 200 €/an. Peu de candidats étrangers la connaissent.", None, "BOURSE"),
  ("Visa D études", "Admission + fonds + logement + assurance.", None, "VISA"),
  # ── Decreto Flussi (Métier / Saisonnier) ──────────────────────────────────
  ("🛂 Decreto Flussi — trouver un emploi en Italie",
   "DPCM 02/10/2025 : 497 550 entrées sur 2026-2028 (164 850/an). "
   "L'employeur fait TOUT : il dépose la demande de nulla osta sur le Portale ALI, "
   "tu n'as qu'à être prêt avec les documents. "
   "Trois groupes selon ton pays d'origine — voir ci-dessous.", None, "FLUSSI"),
  ("Groupe 1 — 14 pays africains à quota réservé (click day 16 fév)",
   "Algérie, Côte d'Ivoire, Égypte, Éthiopie, Gambie, Ghana, Mali, Maroc, Maurice, "
   "Niger, Nigeria, Sénégal, Soudan, Tunisie. "
   "25 000 places/an rien que pour ces pays. "
   "⚠️ Maroc : circuit d'avis renforcé Questura + Inspectorat — délais plus longs, "
   "dossier irréprochable requis. "
   "Précompilation ALI : oct–déc 2026 (fenêtre annuelle). "
   "Secteurs : transport CQC, bâtiment, mécanique, télécoms, hôtellerie, "
   "électriciens, plombiers, alimentaire, naval.",
   "https://portaleservizi.dlci.interno.it/AliSportello/ali/home.htm", "FLUSSI"),
  ("Groupe 2 — tous les autres pays (Cameroun, RDC, Guinée…) — click day 18 fév",
   "Quote générale — compétition plus large mais deux canaux stratégiques sous-utilisés : "
   "(1) SAISONNIER (agricole 12 jan, tourisme 9 fév) : la concurrence s'est effondrée "
   "(72 000 demandes en 2025 vs 337 000 en 2024 pour ~82 000 quotas). "
   "(2) BADANTI hors quota (DL 146/2025) : 10 000 places supplémentaires pour l'assistance "
   "aux handicapés et aux 80+ ans, ouverts dès le 1er janvier via agences pour l'emploi — "
   "utilisés à seulement 13 % en 2025. Aucune restriction de nationalité.",
   "https://portaleservizi.dlci.interno.it/AliSportello/ali/home.htm", "FLUSSI"),
  ("Groupe 3 — colf/badanti (aide domestique) — click day 18 fév",
   "13 600 places A-bis exclusif domestique + ~19 300 hors quota. "
   "AUCUNE restriction de nationalité. Condition côté employeur : revenu ≥ 20 000 €/an. "
   "Canal le plus accessible pour qui a une expérience dans l'aide à la personne.",
   None, "FLUSSI"),
  ("Préparer MAINTENANT pour 2027",
   "Les click days 2026 sont passés. Les dates 2027 sont déjà connues (même calendrier annuel). "
   "Action immédiate : trouver un employeur italien intéressé (offres Yorbity + candidature à distance), "
   "rassembler les documents (casier judiciaire international, diplômes traduits, CV en italien). "
   "La précompilation ALI ouvre en octobre 2026 — l'employeur doit être prêt à ce moment-là.",
   "https://www.interno.gov.it/it/servizi/servizi-line/procedure-flussi", "FLUSSI"),
 ],
 bourses=[
  ("DSU régional", "Logement + repas + allocation sur critères sociaux (études).", None),
  ("Invest Your Talent in Italy", "Masters ciblés + stage en entreprise italienne.", "https://investyourtalentapplication.esteri.it"),
 ])

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


D["RU"] = dict(
    nom='Russie',
    flag='🇷🇺',
    resume="Universités scientifiques et médicales réputées, coût de la vie bas. Voie principale : le quota de bourses de l'État russe, avec une année de langue russe intégrée au parcours.",
    ressources="Frais et coût de la vie parmi les plus bas ; quota d'État couvrant la scolarité (environ 15 000 places/an).",
    travail="Depuis 2020, travail pendant le temps libre SANS permis pour les étudiants à temps plein d'un établissement accrédité (sauf postes réglementés : comptabilité en chef, fonction publique/sécurité).",
    post="Pas de dispositif post-études simple et documenté — se renseigner en fin d'études auprès de l'université.",
    portail='https://education-in-russia.com',
    services=['ORIENT', 'ADMIS', 'DOSSIER', 'VISA', 'TRAD'],
    etapes=[
        ("Déposer une demande de quota d'État", 'Candidature via le portail officiel des quotas (sélection par le canal russe accrédité dans ton pays).', 'https://education-in-russia.com', None),
        ('Passer la sélection', 'Épreuves ou entretien selon la filière, puis classement des candidats.', None, None),
        ('Année préparatoire de langue russe', 'Intégrée au parcours quota pour les cursus enseignés en russe.', None, None),
    ],
    bourses=[],
)

D["RS"] = dict(
    nom='Serbie',
    flag='🇷🇸',
    resume="Coût de la vie bas au cœur des Balkans. Cursus surtout en serbe, quelques programmes en anglais (médecine, ingénierie). Reconnaissance du diplôme obligatoire AVANT l'inscription.",
    ressources='Coût de la vie bas (chambre partagée dès ~50 €/mois) ; scolarité hors bourse ~500 à 2 500 €/an.',
    travail="Permis unique séjour + travail depuis la réforme de la loi sur les étrangers ; pas de quota d'heures « étudiant » publié — à confirmer au moment voulu.",
    post='À confirmer auprès des autorités serbes.',
    portail='https://studyinserbia.rs',
    services=['ORIENT', 'ADMIS', 'DOSSIER', 'VISA', 'TRAD'],
    etapes=[
        ('Faire reconnaître ton diplôme (ENIC/NARIC)', "Démarche via l'agence serbe (azk.gov.rs) AVANT l'inscription — s'y prendre tôt, c'est long.", 'https://studyinserbia.rs', None),
        ('Choisir un programme accrédité', 'Catalogue officiel des programmes (dont ~180 en anglais).', 'https://studyinserbia.rs', None),
        ("Passer l'examen d'entrée", "Vers juin (licence), septembre–octobre (master) selon l'université.", None, None),
    ],
    bourses=[],
)

D["DZ"] = dict(
    nom='Algérie',
    flag='🇩🇿',
    resume="Frais d'inscription très bas, enseignement en arabe et en français. L'inscription d'un étudiant étranger passe OBLIGATOIREMENT par la voie officielle (Direction de la coopération).",
    ressources="Frais d'inscription très modestes ; coût de la vie bas.",
    travail="Pas de cadre publié pour l'emploi étudiant étranger — ne pas compter dessus.",
    post='À confirmer auprès des autorités algériennes.',
    portail='https://www.mesrs.dz',
    services=['ORIENT', 'ADMIS', 'DOSSIER', 'VISA', 'TRAD'],
    etapes=[
        ("Obtenir l'équivalence de ton diplôme", "Équivalence du baccalauréat/diplôme requise pour l'inscription.", 'https://www.mesrs.dz', None),
        ('Passer par la Direction de la coopération (MESRS)', "Autorisation d'inscription via le canal officiel (circulaire n°47) ; pour les boursiers, demande via le pays d'origine.", None, None),
        ("Visite médicale d'admission", "À l'arrivée, selon l'établissement.", None, None),
    ],
    bourses=[],
)

D["MU"] = dict(
    nom='Maurice',
    flag='🇲🇺',
    resume='Hub régional anglophone et francophone, environnement sûr. Deux universités publiques ; possibilité de travailler et de rester après le diplôme.',
    ressources='Scolarité hors bourse ~120 000 à 350 000 MUR/an (licence) ; coût de la vie modéré.',
    travail="Jusqu'à 20 h/semaine pour les étudiants étrangers à temps plein (inscrits depuis ≥1 an, visa valide) ; pas de travail les 90 premiers jours.",
    post="Young Professional Occupation Permit : jusqu'à 3 ans après une licence obtenue à Maurice (demande déposée par l'employeur).",
    portail='https://edbmauritius.org/education',
    services=['ORIENT', 'ADMIS', 'DOSSIER', 'VISA', 'TRAD'],
    etapes=[
        ('Être admis dans un établissement mauricien', 'Universités publiques (University of Mauritius, UTM) ou privées agréées.', 'https://edbmauritius.org/education', None),
        ('Obtenir le visa étudiant', "Via l'établissement et l'immigration mauricienne.", None, None),
        ('Option travail (après 90 jours)', "Jusqu'à 20 h/semaine une fois inscrit et en règle.", None, None),
    ],
    bourses=[],
)

D["BN"] = dict(
    nom='Brunei',
    flag='🇧🇳',
    resume="Petit État riche d'Asie du Sud-Est, cursus en anglais. La bourse du gouvernement (BDGS) couvre presque tout ; guichet unique une fois par an.",
    ressources='Scolarité et vie couvertes par la bourse BDGS (allocation, logement, repas, billets aller-retour).',
    travail="Cadre d'emploi étudiant limité — se renseigner auprès de l'établissement.",
    post="À confirmer ; la bourse vise en priorité un PREMIER séjour d'études au Brunei.",
    portail='https://www.mfa.gov.bn/Pages/scholarship.aspx',
    services=['ORIENT', 'ADMIS', 'DOSSIER', 'VISA', 'TRAD'],
    etapes=[
        ('Choisir un établissement public', 'UBD, UNISSA, UTB ou Politeknik Brunei ; programmes sur leurs sites.', 'https://www.mfa.gov.bn/Pages/scholarship.aspx', None),
        ('Candidater à la BDGS pendant la fenêtre', 'Ouverture ~mi-décembre, clôture STRICTE le 15 février (heure de Brunei).', None, None),
        ("Justifier le niveau d'anglais", 'IELTS 6.0 / TOEFL 550 ou équivalent.', None, None),
    ],
    bourses=[],
)

D["MX"] = dict(
    nom='Mexique',
    flag='🇲🇽',
    resume="Grand système universitaire hispanophone (UNAM, IPN, COLMEX…). Les bourses d'excellence AMEXCID financent master, doctorat et séjours de recherche.",
    ressources='Coût de la vie modéré ; bourse AMEXCID couvrant scolarité, allocation et assurance santé.',
    travail='Selon le statut migratoire de la bourse — se renseigner ; études à temps plein attendues.',
    post='À confirmer auprès des autorités mexicaines.',
    portail='https://www.gob.mx/amexcid/acciones-y-programas/becas-para-extranjeros-29785',
    services=['ORIENT', 'ADMIS', 'DOSSIER', 'VISA', 'TRAD'],
    etapes=[
        ("Obtenir une (pré)acceptation d'un établissement", "Souvent exigée par l'appel AMEXCID — anticiper cette démarche.", 'https://www.gob.mx/amexcid/acciones-y-programas/becas-para-extranjeros-29785', None),
        ("Candidater pendant l'appel annuel", 'Publication vers mai, clôture vers juin.', None, None),
        ("Justifier le niveau d'espagnol", 'Études en espagnol : niveau exigé.', None, None),
    ],
    bourses=[],
)

D["SK"] = dict(
    nom='Slovaquie',
    flag='🇸🇰',
    resume="Bourses d'État de la coopération slovaque, tous cycles dans les universités publiques. Quotas par pays fixés à chaque cycle ; cursus en slovaque avec préparation linguistique.",
    ressources='Scolarité couverte + allocation mensuelle ; coût de la vie modéré.',
    travail='Selon la réglementation étudiante slovaque — à confirmer.',
    post='À confirmer auprès des autorités slovaques.',
    portail='https://www.vladnestipendia.sk/en/',
    services=['ORIENT', 'ADMIS', 'DOSSIER', 'VISA', 'TRAD'],
    etapes=[
        ("Vérifier l'éligibilité de ton pays", "Liste des pays partenaires revue à chaque cycle (annexe de l'appel).", 'https://www.vladnestipendia.sk/en/', None),
        ('Candidater en ligne (mars–mai)', 'Portail actif ~23 mars → fin mai ; réponse au plus tard le 15 juillet.', None, None),
        ('Envoyer le dossier papier (si lauréat)', "Seuls les lauréats transmettent l'original signé au ministère.", None, None),
    ],
    bourses=[],
)

D["KZ"] = dict(
    nom='Kazakhstan',
    flag='🇰🇿',
    resume="Environ 550 bourses d'État par an (tous cycles), cursus en kazakh, russe ou anglais. Prise en charge PARTIELLE : billet, visa et assurance restent à ta charge.",
    ressources='Scolarité + allocation mensuelle couvertes ; billet, visa et assurance à ta charge.',
    travail='Selon la réglementation étudiante kazakhe — à confirmer.',
    post='À confirmer auprès des autorités kazakhes.',
    portail='https://studyin.kz/admission',
    services=['ORIENT', 'ADMIS', 'DOSSIER', 'VISA', 'TRAD'],
    etapes=[
        ('Créer un compte sur le portail', 'Inscription et dépôt en ligne pendant la fenêtre (30 mars → 31 mai).', 'https://studyin.kz/admission', None),
        ("Passer le test et l'entretien en ligne", "Sélection par l'opérateur national de l'enseignement supérieur.", None, None),
        ('Prévoir billet, visa et assurance', 'Non couverts par la bourse.', None, None),
    ],
    bourses=[],
)

# =============================================================================
# BASE (pays actifs + demandes)
# =============================================================================
# --- Toutes les destinations du monde (fiches générales pour les non-détaillées) ---
try:
    from destinations_monde import completer_destinations
    D["KW"] = dict(
        nom='Koweït',
        flag='🇰🇼',
        resume='Marché privé porté par les services, la finance et le BTP ; recrutement encadré par la Public Authority for Manpower (PAM).',
        ressources='Emploi via un employeur sponsor (permis art. 18) ; démarches en ligne sur la plateforme Sahel/Ashal de la PAM.',
        travail='Restreint',
        post='Selon secteur',
        portail='https://www.manpower.gov.kw',
        services=['ORIENT', 'DOSSIER', 'VISA', 'TRAD'],
        etapes=[('Trouver un employeur sponsor', "L'employeur dépose la demande de permis de travail (art. 18) auprès de la Public Authority for Manpower.", 'https://www.manpower.gov.kw', 'ORIENT'), ('Permis + résidence (iqama)', "Après approbation, entrée puis résidence liée à l'employeur ; démarches via le portail e-gov.", 'https://www.e.gov.kw', 'DOSSIER')],
        bourses=[],
    )
    D["BH"] = dict(
        nom='Bahreïn',
        flag='🇧🇭',
        resume='Hub financier régional, installation moins coûteuse que ses voisins ; marché du travail régulé par la LMRA.',
        ressources="Tout permis de travail passe par la LMRA (Expat Management System) ; le poste est d'abord publié localement.",
        travail='Restreint',
        post='Selon secteur',
        portail='https://lmra.gov.bh',
        services=['ORIENT', 'DOSSIER', 'VISA', 'TRAD'],
        etapes=[("Offre d'emploi via la LMRA", "L'employeur publie le poste puis dépose le permis via l'Expat Management System de la LMRA.", 'https://lmra.gov.bh', 'ORIENT'), ('Permis de travail + résidence', 'Après approbation LMRA et examen médical : permis de travail et carte de résidence.', 'https://lmra.gov.bh', 'DOSSIER')],
        bourses=[],
    )
    D["OM"] = dict(
        nom='Oman',
        flag='🇴🇲',
        resume="Économie tirée par l'énergie et la logistique (Vision 2040) ; réformes récentes du travail (mobilité d'employeur après 1 an).",
        ressources="Deux étapes : autorisation de main-d'œuvre (ministère du Travail, soumise au quota d'omanisation) puis visa d'emploi (ROP).",
        travail='Restreint',
        post='Selon secteur',
        portail='https://www.rop.gov.om',
        services=['ORIENT', 'DOSSIER', 'VISA', 'TRAD'],
        etapes=[("Autorisation de main-d'œuvre", "L'employeur obtient la clearance du ministère du Travail (soumise au quota d'omanisation — vérifier que le poste est ouvert).", None, 'ORIENT'), ("Visa d'emploi (Royal Oman Police)", "L'employeur dépose le visa d'emploi auprès de la ROP ; iqama après examen médical.", 'https://www.rop.gov.om', 'DOSSIER')],
        bourses=[],
    )
    completer_destinations(D)
except ImportError:
    pass

def db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS config_pays(code TEXT PRIMARY KEY, actif INT DEFAULT 1)")
    con.execute("""CREATE TABLE IF NOT EXISTS leads(
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, nom TEXT, contact TEXT,
        origine TEXT, destination TEXT, service TEXT, message TEXT)""")
    # Seed des pays UNIQUEMENT s'il en manque (patch_seed_v1) : plus
    # d'ecriture a chaque rerun -> plus de collision entre onglets.
    _n = con.execute("SELECT COUNT(*) FROM config_pays").fetchone()[0]
    if _n < len(D):
        for code in D:
            con.execute("INSERT OR IGNORE INTO config_pays(code,actif) VALUES(?,1)", (code,))
        con.commit()
    return con

con = db()
actifs = {r[0] for r in con.execute("SELECT code FROM config_pays WHERE actif=1")}

if "svc" not in st.session_state: st.session_state.svc = None

# --- Pages dediees « accompagnement » et « contact » (patch_jobboard2) ------
# Un NOUVEL ONGLET = une nouvelle session : le contexte arrive par l'URL.
#   ?page=accompagnement&dest=DE&lg=fr&orig=Benin&type=M%C3%A9tier%20sp%C3%A9cialis%C3%A9
_qp = st.query_params
if _qp.get("page") in ("accompagnement", "contact"):
    import urllib.parse as _up
    _tr = globals().get("tr", lambda s: s)
    _lg_qp = _qp.get("lg") or ""
    if _lg_qp in LANGUES and _lg_qp != LG:
        st.session_state.lang = _lg_qp
        LG = _lg_qp
    _dst = (_qp.get("dest") or "").upper()
    _type_qp = _up.unquote(_qp.get("type") or "")
    _d = D.get(_dst)
    if not _d:
        st.warning("🌍 " + _tr("Choisis d'abord un pays de destination sur la page principale."))
        st.link_button("← Yorbity", "/")
        st.stop()

    try:
        import theme_pays
        theme_pays.appliquer(_dst, theme_pays.type_interne(_type_qp), _tr)
    except Exception:
        pass

    _svc_dest = (services_cfg.effectifs(_dst, _d["services"], list(SVC.keys()))
                 or _d["services"])
    if _type_qp:
        _svc_dest = _services_pour_type(_svc_dest, _type_qp)
    _noms = []

    if _qp.get("page") == "accompagnement":
        st.markdown(f"## {t('accompagne', LG)} {nom_pays(_d['nom'], LG)}")
        st.write(t("accompagne_desc", LG))
        for _s in _svc_dest:
            _n, _de, _ = SVC[_s]
            _n, _de = _tr(_n), _tr(_de)
            _noms.append(_n)
            with st.expander(_n):
                st.write(_de)
    else:
        _noms = [_tr(SVC[_s][0]) for _s in _svc_dest]

    st.markdown("#### " + t("form_titre", LG))
    with st.form("lead_page_dediee"):
        _f1, _f2 = st.columns(2)
        _nom_lead = _f1.text_input(t("nom", LG))
        _contact = _f2.text_input(t("contact", LG))
        _svc_choisi = st.selectbox(t("service_interet", LG), _noms)
        _msg = st.text_area(t("projet_2lignes", LG))
        if st.form_submit_button(t("lancer", LG)):
            if _nom_lead.strip() and _contact.strip():
                con.execute(
                    "INSERT INTO leads(date,nom,contact,origine,destination,service,message) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (TODAY, _nom_lead.strip(), _contact.strip(),
                     _up.unquote(_qp.get("orig") or ""), _d["nom"],
                     _svc_choisi, _msg.strip()))
                con.commit()
                st.success("✅ " + _tr("Merci ! Notre équipe te répond sous 24 h."))
            else:
                st.error(_tr("Nom et contact sont obligatoires."))
    st.caption(_tr("Nous préparons et organisons tes démarches avec toi. "
                   "Personne ne peut garantir une admission ou un visa — "
                   "méfie-toi de ceux qui le promettent."))
    st.stop()
# -----------------------------------------------------------------------------


# =============================================================================
# EN-TÊTE
# =============================================================================
st.markdown(f"""
<div style='text-align:center; padding:.4rem 0 .8rem;'>
  <h1 style='margin-bottom:0; font-size:2.7rem;'>🚀 {APP_NAME}</h1>
  <p style='color:var(--text-color); opacity:.72; margin-top:.15rem; font-size:1.1rem;'>{t('tagline', LG)}</p>
</div>""", unsafe_allow_html=True)

# ---------- Listes traduites (affichage) + valeurs canoniques (logique) ----------
T_TYPES    = T["types"][LG]
T_NIVEAUX  = T["niveaux"][LG]
T_DOMAINES = T["domaines"][LG]
CANON_TYPES   = T["types"]["fr"]
CANON_NIVEAUX = T["niveaux"]["fr"]
CANON_DOM     = T["domaines"]["fr"]

# ---------- Écran connexion/inscription (si demandé) ----------
if espace.ecran_auth(ORIGINES):
    st.stop()

# --- Changement de mot de passe obligatoire apres reinitialisation ---
if admin_comptes.ecran_changement_force():
    st.stop()
if mdp_oublie.ecran():
    st.stop()

# ---------- Boutique : Premium + services a la carte (patch_boutique) -------
import paiement as _paiement
# patch_fix_ordre : helper défini avant sa 1re utilisation
def _monetisation_active():  # patch_monetisation : interrupteur maitre (defaut OFF)
    try:
        import offres_sync as _osy_mon2
        return _osy_mon2.param("monetisation_active", "0") != "0"
    except Exception:
        return False
_paiement.enregistrer_services(SVC)
if _monetisation_active() and espace.user_connecte() and _paiement.ecran_boutique(st.session_state.user):  # patch_monetisation
    st.stop()

# ---------- Écran Premium ----------
import questionnaire_reco as _questionnaire_reco  # patch_questionnaire
if _questionnaire_reco.ecran(ORIGINES): st.stop()
if _monetisation_active() and espace.ecran_premium():
    st.stop()

# ---------- Suivi des démarches ----------
if espace.user_connecte() and dossiers.ecran_mes_demarches(espace.user_connecte()):
    st.stop()
if espace.est_admin() and dossiers.ecran_admin():
    st.stop()
# --- Seed automatique des etoiles (une fois par session) ---
if "seed_etoiles_fait" not in st.session_state:
    try:
        admin_projets._seed_initial(D, ORIGINES)
        st.session_state.seed_etoiles_fait = True
    except Exception:
        pass
if espace.est_admin() and admin_projets.ecran(D, ORIGINES):
    st.stop()
if espace.est_admin() and admin_comptes.ecran():
    st.stop()
if espace.est_admin() and offres_cfg.ecran():
    st.stop()
if espace.est_admin() and devises_cfg.ecran_admin(TAUX):
    st.stop()
if espace.est_admin() and eligibilite.ecran():
    st.stop()
if espace.est_admin() and offres_sync.ecran():
    st.stop()
if espace.est_admin() and moteur_plans.ecran(ORIGINES):
    st.stop()
if espace.est_admin() and console_accompagnement.ecran(D, ORIGINES):
    st.stop()
import plans_visiteur as _pv_mod  # patch_plans_visiteur : vue visiteur,
# placee AVANT le bloc qui fait st.query_params.clear() plus bas.
if _pv_mod.ecran(ORIGINES):
    st.stop()

# ---------- Retour de paiement CinetPay (mode réel) ----------
_params = st.query_params
if "paiement_retour" in _params:
    import paiement
    tid = _params["paiement_retour"]
    statut = paiement.verifier_paiement(tid)
    if statut == "paye":
        info = paiement.offre_de_transaction(tid)
        if info and espace.user_connecte():
            jours = paiement.duree_jours(info["offre"])  # patch_boutique :
            # 0 jour = service a la carte (l'ancien defaut offrait 30 j de
            # Premium a tout code inconnu).
            if jours > 0:
                nouveau = auth.activer_premium(espace.user_connecte()["id"], jours)
                st.session_state.user["premium_jusqu"] = nouveau
            else:
                st.success("✅ " + paiement.livrer_service(
                    info, espace.user_connecte()))
            st.success(t("recu", LG))
    else:
        st.error("Le paiement n'a pas abouti. Réessaie ou contacte-nous.")
    st.query_params.clear()

# ---------- Espace perso : tableau de bord enrichi ----------
if st.session_state.get("show_espace") and espace.user_connecte():
    u = espace.user_connecte()
    try:
        import tableau_bord
        tableau_bord.ecran(u)
    except Exception as _e_tb:
        st.markdown(f"## {t('mon_espace', LG)} — {u['nom'] or u['email']}")
        projets = espace.mes_projets(u["id"])
        if projets:
            st.markdown("### " + t("projets_sauv", LG))
            for p in projets:
                st.markdown(f"- **{p['origine']} \u2192 {p['destination']}** \u00b7 {p['type']} \u00b7 "
                            f"{p['niveau']}  _(cr\u00e9\u00e9 le {p['date']})_")
        else:
            st.info(t("aucun_projet", LG))
        if st.button(t("retour_recherche", LG)):
            st.session_state.show_espace = False
            st.rerun()
    st.stop()

# =============================================================================
# patch_questionnaire : bouton conseiller auto (visible anonymes)
if st.button("🎯 " + t("questionnaire_btn", LG),
             use_container_width=True, key="btn_quest"):
    st.session_state.show_questionnaire = True
    st.rerun()
# LE PARCOURS — 4 questions
# =============================================================================
c1, c2 = st.columns(2)
# --- patch_projets_visibles : l'admin peut retirer des projets du menu
# visiteur (config_params · projet_visible:<canon>, defaut visible).
# Filtre PARALLELE T_TYPES/CANON_TYPES : la conversion par index
# (l.~1279 et ~1345) reste juste dans toutes les langues.
def _projet_visible(_pc):
    try:
        import offres_sync
        return offres_sync.param(f"projet_visible:{_pc}", "1") != "0"
    except Exception:
        return True
_idx_pjv = [i for i, _pc in enumerate(CANON_TYPES) if _projet_visible(_pc)]
if _idx_pjv and len(_idx_pjv) < len(CANON_TYPES):
    T_TYPES = [T_TYPES[i] for i in _idx_pjv]
    CANON_TYPES = [CANON_TYPES[i] for i in _idx_pjv]
# tout masque -> repli : listes inchangees (jamais de menu vide)
# --- fin patch_projets_visibles
# 1) Type de projet d'abord (il filtre les pays proposés)
type_ = c1.selectbox(t("q_type", LG), [t("choisir", LG)] + T_TYPES)
# projet canonique (indépendant de la langue) pour la config
_proj_canon = CANON_TYPES[T_TYPES.index(type_)] if type_ in T_TYPES else None

# 2) Origine — filtrée par projet (étoile OU activée) + masquage global admin
_orig_off = services_cfg.origines_desactivees()
if _proj_canon:
    _vis_o = set(config_projets.pays_visibles(_proj_canon, "origine"))
    _orig_list = [p for p in sorted(ORIGINES.keys(), key=_tri_sans_accents) if p not in _orig_off and (not _vis_o or p in _vis_o)]
    _etoiles_o = dict(config_projets.etat(_proj_canon, "origine"))
else:
    _orig_list = [p for p in sorted(ORIGINES.keys(), key=_tri_sans_accents) if p not in _orig_off]
    _etoiles_o = {}
def _lbl_o(p):
    if p == t("choisir", LG): return p
    return nom_pays(p, LG)
origine = c2.selectbox(t("q_origine", LG), [t("choisir", LG)] + _orig_list, format_func=_lbl_o)

c3, c4 = st.columns(2)
# 3) Destination — filtrée par projet
if _proj_canon:
    _vis_d = set(config_projets.pays_visibles(_proj_canon, "destination"))
    _dnoms = dict(config_projets.etat(_proj_canon, "destination"))
    dest_codes = sorted([c for c in D if c in actifs and (not _vis_d or D[c]["nom"] in _vis_d)],
                        key=lambda c: D[c]["nom"])
else:
    _dnoms = {}
    dest_codes = sorted([c for c in D if c in actifs], key=lambda c: D[c]["nom"])
def _lbl_d(c):
    if c == t("choisir", LG): return c
    return f"{D[c]['flag']} {nom_pays(D[c]['nom'], LG)}"
if _proj_canon == "Volontariat":
    # patch_vol_programmes : pour le Volontariat, la « destination » devient le
    # PROGRAMME (ONU, VIF, weltwärts…), filtre par le pays d'origine.
    import volontariat_flux as _vfx
    _co_vfx = ORIGINES[origine][0] if origine != t("choisir", LG) else None
    _progs_vfx = _vfx.programmes(_co_vfx)
    _plbl_vfx = dict(_progs_vfx)
    _plab_vfx = {"fr": "🤝 Programme de volontariat", "en": "🤝 Volunteering programme", "es": "🤝 Programa de voluntariado", "pt": "🤝 Programa de voluntariado", "zh": "🤝 志愿服务项目", "ar": "🤝 برنامج التطوع", "ja": "🤝 ボランティアプログラム", "ko": "🤝 자원봉사 프로그램", "id": "🤝 Program relawan"}.get(LG, "🤝 Programme de volontariat")
    destination = c3.selectbox(_plab_vfx, [t("choisir", LG)] + [c for c, _ in _progs_vfx], format_func=lambda c: _plbl_vfx.get(c, c))
else:
    destination = c3.selectbox(t("q_dest", LG), [t("choisir", LG)] + dest_codes, format_func=_lbl_d)

_poste_rech = ""
if _proj_canon in ("Sport", "Art", "Volontariat"):
    _dmap = T.get("disciplines", {}).get(_proj_canon, {})
    _disc = _dmap.get(LG) or _dmap.get("fr", [])
    _dlabel = {"fr": "🏅 Discipline", "en": "🏅 Discipline", "es": "🏅 Disciplina", "pt": "🏅 Disciplina", "zh": "🏅 项目", "ar": "🏅 التخصص", "ja": "🏅 種目", "ko": "🏅 종목", "id": "🏅 Disiplin"}.get(LG, "🏅 Discipline")
    if _proj_canon == "Volontariat":
        _dlabel = {"fr": "🤝 Domaine de mission", "en": "🤝 Mission field", "es": "🤝 Ámbito de misión", "pt": "🤝 Área de missão", "zh": "🤝 志愿领域", "ar": "🤝 مجال المهمة", "ja": "🤝 活動分野", "ko": "🤝 활동 분야", "id": "🤝 Bidang misi"}.get(LG, "🤝 Domaine de mission")
    niveau = c4.selectbox(_dlabel, [t("choisir", LG)] + _disc)
elif recherche_poste.concerne(_proj_canon) and destination != t("choisir", LG):
    _poste_rech = recherche_poste.selecteur(c4, _proj_canon, destination, lambda x: traduire(x, LG))
    niveau = t("choisir", LG)
else:
    niveau = c4.selectbox(t("q_niveau", LG), [t("choisir", LG)] + T_NIVEAUX, disabled=(type_ in _METIER_LBLS))
if _proj_canon in ("Sport", "Art", "Volontariat"):
    domaine = T_DOMAINES[0]        # pas de filiere academique pour Sport/Art
else:
    domaine = st.selectbox(t("q_domaine", LG), T_DOMAINES)

st.divider()

# =============================================================================
# RÉSULTAT
# =============================================================================
_sans_niveau = recherche_poste.concerne(_proj_canon) and _proj_canon not in ("Sport", "Art", "Volontariat")
_req = (origine, destination, type_) if _sans_niveau else (origine, destination, type_, niveau)
if _proj_canon == "Volontariat":
    # patch_vol_programmes : resultat = le PROGRAMME choisi (plan client + offres liees)
    if t("choisir", LG) in (origine, destination):
        st.info(t("intro", LG))
    else:
        import volontariat_flux as _vfx2
        _vfx2.rendre(destination, ORIGINES[origine][0], ORIGINES, LG)
elif t("choisir", LG) in _req:
    st.info(t("intro", LG))
else:
    d = D[destination]
    code_orig, dev_orig = ORIGINES[origine]
    # ---- Swimpe : bouton "Sauvegarder ce projet" (si connecte) ----
    try:
        _u_save = espace.user_connecte()
        _cols_save = st.columns([3, 2])
        with _cols_save[0]:
            if _u_save:
                if st.button("\U0001F4BE " + t("sauver_projet_btn", LG), key="save_projet_top",
                             use_container_width=True):
                    espace.sauver_projet(_u_save["id"], origine, destination,
                                         type_, niveau, domaine)
                    st.success(t("projet_sauve_ok", LG))
                    st.balloons()
            else:
                st.caption("\U0001F512 " + t("connecte_pour_sauver", LG))
    except Exception:
        pass
    # ---- fin bouton sauvegarder ----
    def tr(x): return traduire(x, LG)  # traduit le contenu dans la langue courante
    if LG != "fr":
        st.caption("🌐 " + {"en":"Content translated automatically.","es":"Contenido traducido automáticamente.",
                   "pt":"Conteúdo traduzido automaticamente.","zh":"内容为自动翻译。","ar":"المحتوى مترجم آليًا.",
                   "ja":"内容は自動翻訳されています。","ko":"콘텐츠는 자동 번역되었습니다.",
                   "id":"Konten diterjemahkan secara otomatis."}.get(LG,""))
    # Convertir les choix affichés (traduits) en valeurs canoniques FR pour la logique
    type_c   = CANON_TYPES[T_TYPES.index(type_)]     if type_   in T_TYPES   else type_
    niveau_c = CANON_NIVEAUX[T_NIVEAUX.index(niveau)] if niveau in T_NIVEAUX else niveau
    domaine_c= CANON_DOM[T_DOMAINES.index(domaine)]   if domaine in T_DOMAINES else domaine

    # ---- Prix d'appel = service le moins cher proposé pour cette destination
    services_dest = services_cfg.effectifs(destination, d["services"], list(SVC.keys()))
    if not services_dest:
        services_dest = d["services"]
    services_dest = _services_pour_type(services_dest, type_c)  # patch_jobboard2
    _prix = services_cfg.tarifs_tous({k: v[2] for k, v in SVC.items()})
    prix_min_fcfa = min((_prix[s] for s in services_dest if s in _prix), default=(min(_prix.values()) if _prix else 0))
    prix_local = conv(prix_min_fcfa, "XOF", dev_orig)
    if dev_orig in ("XOF", "XAF") or prix_local is None:
        prix_txt = f"{prix_min_fcfa:,} FCFA".replace(",", " ")
    else:
        prix_txt = f"{prix_local:,.0f} {dev_orig}".replace(",", " ")

    # ---- Prix en DEVISE DE DESTINATION + lien accompagnement (patch_accompagnement)
    import urllib.parse as _up
    _eur_min = prix_min_fcfa / 655.96
    try:
        import devises as _dev
        _p = _dev.prix(_eur_min, destination)
        _n = _dev.note(_eur_min, destination)
        _prix_banniere = _p + ((" · " + _n) if _n else "")
    except Exception:
        _prix_banniere = devises_cfg.prix_affiche(_eur_min, TAUX, avec_equivalent=True)
    _url_acc = ("?page=accompagnement&dest=" + destination + "&lg=" + LG
                + "&orig=" + _up.quote(origine or "")
                + "&type=" + _up.quote(type_c or ""))
    _url_contact = _url_acc.replace("page=accompagnement", "page=contact")
    # ---- Bandeau héro marketing
    st.markdown(f"""
<div class='hero'>
  <h2>{d['flag']} {nom_pays(origine, LG)} → {nom_pays(d['nom'], LG)}</h2>
  <p>{tr(d['resume']) if type_c == "Formation (admission)" else tr(_PITCH_PROJET.get(type_c, ''))}</p>
  <div style='display:flex; flex-wrap:wrap; align-items:center; gap:.7rem; margin-top:1.15rem;'>  <!-- patch_finitions -->
    <span class='prix' style='margin:0;'>{t("start_from", LG)} {_prix_banniere}</span>
    <a href='{_url_acc}' target='_blank' style='text-decoration:none; background:#e9b949; color:#1f2937; padding:.55rem 1.1rem; border-radius:10px; font-weight:600; display:inline-block; box-shadow:0 1px 3px rgba(0,0,0,.18);'>{t('accompagne', LG)} {nom_pays(d['nom'], LG)} →</a>
    <a href='{_url_contact}' target='_blank' style='text-decoration:none; background:rgba(255,255,255,.94); color:#1f2937; padding:.55rem 1.1rem; border-radius:10px; font-weight:600; display:inline-block; box-shadow:0 1px 3px rgba(0,0,0,.18);'>{t('form_titre', LG).split('—')[0].strip()} →</a>
  </div>
</div>""", unsafe_allow_html=True)

    # Badges type/niveau retires (patch_finitions) : redondants avec les selecteurs.

    # ---- Infos budget/travail/après : uniquement pour Formation (admission) ----
    if type_c == "Formation (admission)":
        colA, colB = st.columns(2)
        colA.markdown(f"**{t('budget', LG)}** {tr(d['ressources'])}")
        colB.markdown(f"**{t('travail', LG)}** {tr(d['travail'])}")
        st.markdown(f"**{t('apres', LG)}** {tr(d['post'])}")

    # ---- Bourses d'abord si le projet est "Bourse"
    if type_c == "Bourse":
        st.markdown("### " + t("bourses_pour_toi", LG))
        _connecte = espace.user_connecte() is not None
        for nom_b, det, lien in d["bourses"]:
            with st.expander(f"💰 {tr(nom_b)}", expanded=True):
                if _connecte:
                    st.write(tr(det))
                    if lien: st.markdown(f"[🔗 Site officiel]({lien})")
                else:
                    # Aperçu : 1re phrase seulement, puis invitation à créer un compte
                    apercu = tr(det.split(".")[0]) + "…"
                    st.write(apercu)
                    st.warning("🔒 Crée un compte gratuit pour voir les montants exacts, "
                               "les conditions détaillées et le lien de candidature.")
                    if st.button(tr("Débloquer gratuitement"), key=f"unlock_{nom_b}"):
                        st.session_state.show_auth = True
                        st.rerun()

    if type_c == "Stage / Emploi étudiant":
        st.success(tr(f"💼 {d['nom']} — pendant tes études, tu peux travailler : **{(d.get('travail') or '').rstrip(' .')}**. Après le diplôme : {(d.get('post') or '').rstrip(' .')}."))

    # ---- Contenu par TYPE DE PROJET (offres emploi/stage/bourse filtrées) ----
    # --- habillage destination (patch_theme.py) ---
    try:
        import theme_pays
        theme_pays.appliquer(destination, theme_pays.type_interne(type_c), tr)
    except Exception as _e_theme:
        print('theme_pays indisponible :', _e_theme)
    # -----------------------------------------------
    if type_c == "Bourse":  # _lot_bourses_d_v1
        try:
            import bourses_web_ui_v1
            bourses_web_ui_v1.afficher(code_orig, destination, domaine_c,
                                       nom_pays=d["nom"], nom_origine=origine,
                                       connecte=(espace.user_connecte() is not None),
                                       est_admin=espace.est_admin())
        except Exception as _e_bw:
            print("bourses_web_ui indisponible :", _e_bw)
    _mode_opp = opportunites_ui.afficher(type_c, destination, code_orig, tr, poste=_poste_rech, domaine=domaine_c)
    etapes = []
    if not _mode_opp:
        # ---- Étapes (adaptées à l'origine pour la France)
        st.markdown("### " + t("chemin", LG))
        if destination == "FR":
            etapes = d["etapes_eef"] if code_orig in EEF else d["etapes_std"]
            if code_orig in EEF:
                st.caption(tr(f"ℹ️ En tant que ressortissant·e du pays « {origine} », ta procédure "
                           f"passe par **Campus France / Études en France**. Voici exactement comment ça se déroule :"))
        else:
            etapes = d["etapes"]

    # _lot6_parcours_v1 : masquer les étapes "travail" (Decreto Flussi) hors parcours métier
    _TAGS_TRAVAIL = {"FLUSSI"}
    _etapes_vues = []
    for _et in etapes:
        _sc = _et[3] if len(_et) >= 4 else None
        if _sc in _TAGS_TRAVAIL and type_c not in SVC_TYPES.get(_sc, set()):
            continue
        _etapes_vues.append(_et)
    for i, etape in enumerate(_etapes_vues, 1):
        titre, det, lien, svc_code = (etape + (None,))[:4] if len(etape) == 3 else etape
        with st.expander(f"{t('etape', LG)} {i} — {tr(titre)}", expanded=(i == 1)):
            st.write(tr(det))
            if lien:
                st.markdown(f"[{t('lien_officiel', LG)}]({lien})")
            if svc_code and svc_code in services_dest:
                if st.button(t("aide_etape", LG),
                             key=f"btn_{i}_{svc_code}"):
                    st.session_state.svc = svc_code
                if st.session_state.get("svc") == svc_code:
                    _sn, _sd, _sp = SVC[svc_code]
                    st.success("✅ **" + tr(_sn) + "**\n\n" + tr(_sd))
                    st.caption(tr("📩 Ce service est présélectionné dans le formulaire tout en bas de la page — remplis-le pour qu'on démarre."))

    if d.get("portail"):
        st.link_button(f"{t('portail', LG)} {nom_pays(d['nom'], LG)}", d["portail"])

    # ---- Accompagnement : deplace sur sa page dediee (patch_accompagnement)
    st.markdown("---")
    _cA, _cB = st.columns(2)  # patch_jobboard3
    _cA.link_button(t("accompagne", LG) + " " + nom_pays(d["nom"], LG) + " →",
                    _url_acc, use_container_width=True, type="primary")
    _cB.link_button(t("form_titre", LG).split("—")[0].strip() + " →",
                    _url_contact, use_container_width=True, type="secondary")
    # Le formulaire ci-dessous a besoin de la liste des services :
    noms_services = [tr(SVC[s][0]) for s in services_dest]

    # Formulaire retire de la page principale (patch_jobboard3) :
    # il vit sur ?page=contact et ?page=accompagnement (liens ci-dessus).
    st.caption(t("disclaimer", LG))

# =============================================================================
# ADMIN
# =============================================================================
with st.sidebar:
    if espace.est_admin():
        st.markdown(f"### {APP_NAME} · Admin")
        st.link_button("🧭 Console d'accompagnement", "?page=console",
                       use_container_width=True)  # _lot4_bouton_console_v1
        st.link_button("🗺️ Moteur de plans", "?page=plans",
                       use_container_width=True)
        st.markdown("**💰 " + traduire("Monétisation :", st.session_state.get("lang","fr")) + "**")  # patch_monetisation
        try:
            import offres_sync as _osy_monT
            _on_mon = _osy_monT.param("monetisation_active", "0") != "0"
        except Exception:
            _osy_monT = None
            _on_mon = False
        _nv_mon = st.checkbox(traduire("Activer Premium & boutique", st.session_state.get("lang","fr")),
                              value=_on_mon, key="mon_active")
        if _osy_monT is not None and _nv_mon != _on_mon:
            _osy_monT.definir_param("monetisation_active", "1" if _nv_mon else "0")
            st.rerun()
        st.markdown("---")
        st.markdown("**🗺️ " + traduire("Plans visiteur :", st.session_state.get("lang","fr")) + "**")  # patch_plans_visiteur
        for _cle_pv, _lib_pv, _def_pv in (
            ("plans_visiteur_actif", "Afficher les programmes aux visiteurs", "0"),
            ("plans_visiteur_premium", "Réserver au Premium", "0"),
        ):
            try:
                import offres_sync as _osy_pvt
                _on_pv = _osy_pvt.param(_cle_pv, _def_pv) != "0"
            except Exception:
                _osy_pvt = None
                _on_pv = _def_pv != "0"
            _nv_pv = st.checkbox(traduire(_lib_pv, st.session_state.get("lang","fr")),
                                 value=_on_pv, key=f"pvv_{_cle_pv}")
            if _osy_pvt is not None and _nv_pv != _on_pv:
                _osy_pvt.definir_param(_cle_pv, "1" if _nv_pv else "0")
                st.rerun()
        st.markdown("---")
        st.markdown("**🗂 " + traduire("Projets visibles (menu visiteur) :", st.session_state.get("lang","fr")) + "**")  # patch_projets_visibles
        st.caption(traduire("Décoché = retiré du menu du visiteur. Tout décocher = tout afficher.", st.session_state.get("lang","fr")))
        for _pj in config_projets.PROJETS:
            try:
                import offres_sync as _osy_pjv
                _on_pj = _osy_pjv.param(f"projet_visible:{_pj}", "1") != "0"
            except Exception:
                _osy_pjv = None
                _on_pj = True
            _nv_pj = st.checkbox(traduire(_pj, st.session_state.get("lang","fr")),
                                 value=_on_pj, key=f"pjv_{_pj}")
            if _osy_pjv is not None and _nv_pj != _on_pj:
                try:
                    _osy_pjv.definir_param(f"projet_visible:{_pj}", "1" if _nv_pj else "0")
                except Exception as _e_pjv:
                    st.error(f"Enregistrement impossible : {_e_pjv}")
                else:
                    st.rerun()
        st.markdown("---")
        st.markdown("**" + traduire("Pays visibles :", st.session_state.get("lang","fr")) + "**")
        for code in sorted(D, key=lambda c: D[c]["nom"]):
            etat = code in actifs
            nouveau = st.checkbox(f"{D[code]['flag']} " + nom_pays(D[code]['nom'], st.session_state.get("lang","fr")), value=etat, key=f"adm_{code}")
            if nouveau != etat:
                con.execute("UPDATE config_pays SET actif=? WHERE code=?", (1 if nouveau else 0, code))
                con.commit(); st.rerun()
        st.markdown("---")
        st.markdown("**📥 " + traduire("Demandes clients (15 dernières) :", st.session_state.get("lang","fr")) + "**")
        rows = con.execute("SELECT date,nom,contact,origine,destination,service "
                           "FROM leads ORDER BY id DESC LIMIT 15").fetchall()
        for r in rows:
            st.write(f"• {r[0]} — **{r[1]}** ({r[2]}) : {r[3]} → {r[4]} · {r[5]}")
        if not rows: st.caption(traduire("Aucune demande pour l'instant.", st.session_state.get("lang","fr")))
        st.markdown("---")
        if st.button("🎛 " + traduire("Configuration par projet", st.session_state.get("lang","fr")), key="btn_cfg_proj", use_container_width=True):
            st.session_state.show_cfg_projets = True
            st.rerun()
        if st.button("🔐 Comptes utilisateurs", key="btn_cfg_comptes", use_container_width=True):
            st.session_state.show_comptes = True
            st.rerun()
        if st.button("💎 Offres Premium", key="btn_cfg_offres", use_container_width=True):
            st.session_state.show_offres = True
            st.rerun()
        if st.button("💱 Devises", key="btn_cfg_devises", use_container_width=True):
            st.session_state.show_devises = True
            st.rerun()
        if st.button("🛂 Admissibilité", key="btn_cfg_elig", use_container_width=True):
            st.session_state.show_eligibilite = True
            st.rerun()
        if st.button("🔄 Offres & liens", key="btn_cfg_sync", use_container_width=True):
            st.session_state.show_sync = True
            st.rerun()
        st.markdown("**🌍 " + traduire("Pays d'origine masqués (non proposés) :", st.session_state.get("lang","fr")) + "**")
        _off_act = sorted(services_cfg.origines_desactivees())
        _off_sel = st.multiselect(traduire("Masquer ces origines", st.session_state.get("lang","fr")), sorted(ORIGINES.keys(), key=_tri_sans_accents),
                                  default=_off_act, key="orig_off")
        if set(_off_sel) != set(_off_act):
            for _p in set(_off_sel) - set(_off_act):
                services_cfg.definir_origine(_p, False)
            for _p in set(_off_act) - set(_off_sel):
                services_cfg.definir_origine(_p, True)
            st.rerun()
        st.markdown("---")
        st.markdown("**🧩 " + traduire("Services proposés par destination :", st.session_state.get("lang","fr")) + "**")
        _dsel = st.selectbox(traduire("Destination", st.session_state.get("lang","fr")), sorted(D, key=lambda c: D[c]["nom"]),
                             format_func=lambda c: f"{D[c]['flag']} " + nom_pays(D[c]['nom'], st.session_state.get("lang","fr")),
                             key="cfg_dest")
        _eff = services_cfg.effectifs(_dsel, D[_dsel]["services"], list(SVC.keys()))
        for _cs in SVC:
            _on = st.checkbox(traduire(SVC[_cs][0], st.session_state.get("lang","fr")), value=_cs in _eff, key=f"svc_{_dsel}_{_cs}")
            if _on != (_cs in _eff):
                services_cfg.definir(_dsel, _cs, _on)
                st.rerun()
        st.markdown("---")
        st.markdown("**💰 " + traduire("Tarifs des services (EUR) — modifiables :", st.session_state.get("lang","fr")) + "**")
        _prix_adm = services_cfg.tarifs_tous({k: v[2] for k, v in SVC.items()})
        for _cs2 in SVC:
            _px_eur = int(round(_prix_adm[_cs2] / R)) if _prix_adm[_cs2] > 500 else int(_prix_adm[_cs2])
            _np = st.number_input(traduire(SVC[_cs2][0], st.session_state.get("lang","fr")), min_value=0, step=5,
                                  value=_px_eur, key=f"tar_{_cs2}",
                                  help=f"Equivalent: {int(_px_eur * R):,} FCFA")
            if _np != _px_eur:
                services_cfg.definir_tarif(_cs2, int(_np))
                st.rerun()



# =============================================================================
# NOUS CONTACTER (pied de page)
# =============================================================================
st.divider()
st.markdown("## " + t("contact_titre", LG))
_cw = os.environ.get("CONTACT_WHATSAPP", "+241 00 00 00 00")
_ce = os.environ.get("CONTACT_EMAIL", "contact@yorbity.com")
_fa, _fb = st.columns(2)
_fa.markdown(f"**WhatsApp :** [{_cw}](https://wa.me/{_cw.replace(' ','').replace('+','')})")
_fb.markdown(f"**E-mail :** [{_ce}](mailto:{_ce})")
st.caption(t("contact_texte", LG))

# _patch_fiches_italie_belgique_mcf_v1
