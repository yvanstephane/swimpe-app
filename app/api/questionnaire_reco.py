# -*- coding: utf-8 -*-
# questionnaire_reco.py — «🎯 Trouve mon meilleur projet» — v2 CALIBRÉ
# =============================================================================
# Change majeur v2 : le classement n'est plus un score d'opinion, il est
# pondere par la CAPACITE REELLE des voies (data/capacites_voies_v1.json,
# taux sources). Corrections apportees :
#   1) meilleur type = meilleure offre du type (max), plus la somme
#      (la somme favorisait le type le plus NOMBREUX, pas le meilleur)
#   2) objectif = filtre dur (avec repli si rien ne reste)
#   3) domaine = correspondance par mots-cles sur listes a virgules
#   4) chaque piste affiche 🟢/🟡/🔴 + capacite + taux + source
#   5) alerte visa court sejour par nationalite (avec les 3 motifs
#      de refus corrigeables)
# =============================================================================
import json, os, re, sqlite3, urllib.parse
from pathlib import Path
import streamlit as st

try:
    from traduction import traduire
except Exception:
    def traduire(x, lg="fr"): return x

_RACINE = Path(__file__).resolve().parents[2]
DB = str(_RACINE / "data" / "mobilite.db")
PORTES_JSON = _RACINE / "data" / "portes_speciales_v1.json"
CAPACITES_JSON = _RACINE / "data" / "capacites_voies_v1.json"

NIVEAUX = ["lyceen","licence","master","doctorat","pro"]
NIVEAUX_LBL = {"lyceen":"Lycée / Bac","licence":"Licence (Bac+3)",
               "master":"Master (Bac+5)","doctorat":"Doctorat","pro":"Professionnel / Métier"}
DOMAINES = ["tous domaines","Santé","Ingénierie","Informatique","Sciences","Droit",
            "Économie & gestion","Agriculture","Éducation","Arts & culture","Sport"]
# synonymes pour matcher les listes a virgules du catalogue
DOM_SYN = {
  "santé":["sante","santé","medecine","médecine","medical","infirm","pharma"],
  "ingénierie":["ingenierie","ingénierie","ingenieur","genie","mecanique","electr","industri"],
  "informatique":["informatique","numerique","numérique","logiciel","tech","data","it"],
  "sciences":["science","physique","chimie","biolog","math"],
  "droit":["droit","juridique","law"],
  "économie & gestion":["econom","économ","gestion","business","management","commerce","finance"],
  "agriculture":["agri","rural","agronom","elevage","élevage"],
  "éducation":["educ","éduc","enseign","pedagog"],
  "arts & culture":["art","culture","design","musique","cinema"],
  "sport":["sport","athlet","football"],
}
BUDGETS = [("serre","Très serré (je cherche du 100 % financé)"),
           ("moyen","Quelques économies (frais de dossier possibles)"),
           ("ok","Budget disponible pour les démarches")]
OBJECTIFS = [("etudier","🎓 Étudier (bourse, formation)"),
             ("travailler","💼 Travailler (métier, stage, emploi)"),
             ("experience","🤝 Vivre une expérience (volontariat)")]
HORIZONS = [("asap","Dès que possible"),("an","Dans 6-12 mois"),("deux","Dans 1-2 ans")]
# formation figure dans les DEUX : une Ausbildung est une formation ET une
# voie de travail remuneree ; une formation academique releve des etudes.
TYPES_OBJ = {"etudier":("bourse","formation"),
             "travailler":("metier","stage","emploi","formation"),
             "experience":("volontariat","stage")}
PASTILLE = {"forte":"🟢","moyenne":"🟡","faible":"🔴"}
BONUS_NIVEAU = {"forte":6,"moyenne":3,"faible":0}

def _connecte():
    """True si l'utilisateur a un compte actif (filtre de qualification)."""
    try:
        import espace
        return espace.user_connecte() is not None
    except Exception:
        return False

N_LIBRES = 3          # pistes en detail complet pour un visiteur sans compte
def _lg(): return st.session_state.get("lang","fr")
def _t(x): return traduire(x, _lg())

def _origines(passe=None):
    if passe: return passe
    try:
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        rows = con.execute("SELECT nom, code FROM origines WHERE nom IS NOT NULL").fetchall()
        con.close()
        if rows: return {n:(c,"") for n,c in rows if n}
    except Exception: pass
    try:
        from pays_monde import ORIGINES_MONDE
        return {n:(c,"") for n,c in ORIGINES_MONDE.items()}
    except Exception: return {}

def _capacites():
    try:
        return json.loads(CAPACITES_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {"voies":{}, "alertes_visa":{"taux_refus":{}}}

def _portes_pour(code):
    try:
        d = json.loads(PORTES_JSON.read_text(encoding="utf-8"))
        return [dict(p, code_porte=k) for k,p in d.get("portes",{}).items()
                if code.upper() in [c.upper() for c in p.get("nationalites",[])]]
    except Exception: return []

def _voie_de(offre, cap):
    """Retrouve la voie calibree correspondant a une offre du catalogue."""
    titre = (offre.get("titre") or "").lower()
    dest  = (offre.get("destination") or "").upper()
    typ   = (offre.get("type") or "").lower()
    for cid, v in cap.get("voies",{}).items():
        c = v.get("correspondance",{})
        if any(m in titre for m in c.get("mots_cles",[])):
            return cid, v
        ds, ts = c.get("destinations",[]), c.get("types",[])
        if ds and dest in ds and (not ts or typ in ts):
            return cid, v
    return None, None

def _voie_de_porte(code_porte, cap):
    for cid, v in cap.get("voies",{}).items():
        if code_porte in v.get("correspondance",{}).get("portes",[]):
            return cid, v
    return None, None

def _offres_curees():
    try:
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT id,titre,type,destination,origines_eligibles,niveau,domaine,"
            "montant,source_url FROM opportunites "
            "WHERE statut NOT IN ('doublon','auto')").fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception: return []

def _nat_ok(o, code):
    oe = (o.get("origines_eligibles") or "TOUS").strip()
    if oe.upper() in ("TOUS",""): return True
    return code.upper() in {c.strip().upper() for c in re.split(r"[,;| ]+",oe) if c.strip()}

def _financee(o):
    return bool(re.search(r"financ|complet|couvert|indemn|salari|mensuel|allocation|gratuit|bourse",
                          (o.get("montant") or "").lower()))

def _dom_match(dom_user, dom_offre):
    """Correspondance de domaine tolerante aux listes a virgules."""
    d = (dom_offre or "").lower()
    if not d or "tous" in d: return "generique"
    if dom_user.lower() == "tous domaines": return "generique"
    for mot in DOM_SYN.get(dom_user.lower(), [dom_user.lower()]):
        if mot in d: return "exact"
    return "hors"

def _score(o, prof, cap):
    """Score = pertinence profil + BONUS DE CAPACITE REELLE."""
    s, just = 0, []
    cid, voie = _voie_de(o, cap)
    if voie:
        s += BONUS_NIVEAU.get(voie.get("niveau"), 0)
    niv = (o.get("niveau") or "").lower()
    if prof["niveau"] in niv or "tous" in niv or not niv: s += 2
    m = _dom_match(prof["domaine"], o.get("domaine"))
    if m == "exact": s += 3; just.append(_t("ton domaine"))
    elif m == "generique": s += 1
    else: s -= 2
    if prof["budget"] == "serre" and _financee(o):
        s += 3; just.append(_t("financée"))
    return s, just, cid, voie

def _vol(code):
    try:
        import volontariat_flux as vf
        return [{"titre":lib,"type":"volontariat","destination":lib,"montant":"",
                 "domaine":"","niveau":"tous","origines_eligibles":"TOUS","source_url":""}
                for c,lib in vf.programmes(code)]
    except Exception: return []

def _ligne_voie(voie):
    if not voie: return
    st.caption(PASTILLE.get(voie["niveau"],"") + " " + _t(voie["nom"]) + " — " +
               _t(voie.get("capacite","")))
    if voie.get("taux"): st.caption("   📊 " + _t(voie["taux"]))
    if voie.get("barriere_reelle"): st.caption("   🔑 " + _t(voie["barriere_reelle"]))

def ecran(origines=None):
    if not st.session_state.get("show_questionnaire"): return False
    st.markdown("## 🎯 " + _t("Trouve ton meilleur projet"))
    st.caption(_t("Recommandation honnête, chiffrée et sourcée — aucune inscription requise"))
    origines = _origines(origines)
    # tri insensible aux accents : Sénégal avec les S, Égypte avec les E
    import unicodedata as _ud
    def _cle_tri(x):
        return _ud.normalize("NFD", x).encode("ascii", "ignore").decode().casefold()
    noms = sorted(origines.keys(), key=_cle_tri)
    if not noms:
        st.warning(_t("Liste des nationalités indisponible."))
        return True
    cap = _capacites()
    nat = st.selectbox("🛂 " + _t("Ta nationalité (passeport)"), noms, key="q_nat")
    code = origines.get(nat, ("XX",))[0]
    portes = _portes_pour(code)
    a_saison = any(p.get("type") == "saisonnier" for p in portes)

    with st.form("form_questionnaire"):
        c1,c2 = st.columns(2)
        age = c1.number_input("🎂 " + _t("Ton âge"), 15, 60, 22)
        niveau = c2.selectbox("🎓 " + _t("Ton niveau d'études"), NIVEAUX,
                              format_func=lambda x: _t(NIVEAUX_LBL[x]))
        domaine = st.selectbox("📚 " + _t("Ton domaine"), DOMAINES, format_func=lambda x: _t(x))
        budget = st.radio("💰 " + _t("Ton budget"), [b[0] for b in BUDGETS],
                          format_func=lambda x: _t(dict(BUDGETS)[x]))
        objectif = st.radio("🧭 " + _t("Ton objectif"), [o[0] for o in OBJECTIFS],
                            format_func=lambda x: _t(dict(OBJECTIFS)[x]))
        c5,c6 = st.columns(2)
        apprendre = c5.selectbox("🗣️ " + _t("Prêt·e à apprendre une langue (~1 an) ?"),
                                 ["oui","peut_etre","non"],
                                 format_func=lambda x: _t({"oui":"Oui !","peut_etre":"Peut-être","non":"Non"}[x]))
        horizon = c6.selectbox("📅 " + _t("Horizon de départ"), [h[0] for h in HORIZONS],
                               format_func=lambda x: _t(dict(HORIZONS)[x]))
        saison = "n/a"
        if a_saison:
            saison = st.radio("🚜 " + _t("Ouvert au travail saisonnier encadré (3-9 mois) ?"),
                              ["oui","non"], format_func=lambda x: _t({"oui":"Oui","non":"Non"}[x]))
        ok = st.form_submit_button("🎯 " + _t("Voir mes recommandations"),
                                   type="primary", use_container_width=True)
        ret = st.form_submit_button(_t("Retour"), use_container_width=True)
    if ret:
        st.session_state.show_questionnaire = False; st.rerun()
    if not ok: return True

    prof = {"nat":nat,"code":code,"age":age,"niveau":niveau,"domaine":domaine,
            "budget":budget,"objectif":objectif,"apprendre":apprendre,
            "horizon":horizon,"saisonnier":saison}

    # ---- Collecte + FILTRE DUR par objectif ----
    brut = _offres_curees() + _vol(code)
    retenues, fermees, hors_objectif = [], 0, []
    cibles = TYPES_OBJ[objectif]
    for o in brut:
        if not _nat_ok(o, code): fermees += 1; continue
        s, just, cid, voie = _score(o, prof, cap)
        item = (s, just, o, voie)
        if (o.get("type") or "").lower() in cibles: retenues.append(item)
        else: hors_objectif.append(item)
    repli = False
    if not retenues:
        retenues, repli = hors_objectif, True
    retenues.sort(key=lambda x: -x[0])

    # ---- Meilleur type : MAX par type (pas la somme) ----
    best = {}
    for s,_,o,_v in retenues:
        t = (o.get("type") or "?").lower()
        best[t] = max(best.get(t, -99), s)
    if best:
        gagnant = max(best, key=best.get)
        st.success("🏆 " + _t("Ta meilleure piste") + f" : **{_t(gagnant)}**")
    if repli:
        st.info("ℹ️ " + _t("Rien ne correspond exactement à ton objectif — voici les "
                          "pistes les plus proches."))

    # ---- Portes speciales (avec calibration) ----
    if portes:
        st.markdown("### 🚪 " + _t("Portes réservées à ta nationalité"))
        for p in portes:
            cid, voie = _voie_de_porte(p.get("code_porte",""), cap)
            titre = p["nom"]
            if voie: titre = PASTILLE.get(voie["niveau"],"") + " " + titre
            if p.get("type")=="saisonnier" and saison=="oui":
                titre += "  ·  ✅ " + _t("compatible avec ta réponse")
            st.markdown("**" + titre + "**")
            if voie:
                st.caption("📊 " + _t(voie.get("capacite","")))
                st.caption("🔑 " + _t(voie.get("barriere_reelle","")))
            st.caption("🏛️ " + _t("Canal officiel") + " : " + p.get("canal_officiel",""))
            st.caption(p.get("arnaques",""))

    # ---- Pistes du catalogue, avec chances chiffrees ----
    _cx = _connecte()
    st.markdown("### 📋 " + _t("Tes pistes, classées par chances réelles"))
    for _i, (s, just, o, voie) in enumerate(retenues[:6]):
        past = PASTILLE.get(voie["niveau"],"") if voie else "⚪"
        ligne = f"{past} **{o['titre']}** — {o.get('destination','')}"
        if just: ligne += "  ·  " + ", ".join(just)
        st.markdown(ligne)
        if _cx or _i < N_LIBRES:
            # detail complet : capacite, taux, barriere, lien officiel
            _ligne_voie(voie)
            if o.get("source_url"): st.caption("   🔗 " + o["source_url"])
        else:
            # piste MONTREE (nom + chances) mais detail reserve aux inscrits.
            # La capacite reste visible : on ne cache jamais l'existence
            # d'une chance, seulement le mode d'emploi.
            if voie: st.caption("   " + _t(voie.get("capacite","")))
            st.caption("   🔒 " + _t("Crée un compte gratuit pour voir comment "
                                     "y entrer (canal officiel, étapes, délais)."))
    st.caption("🟢 " + _t("forte capacité") + " · 🟡 " + _t("sélectif mais réel") +
               " · 🔴 " + _t("très sélectif") + " · ⚪ " + _t("capacité non documentée"))

    # ---- Strategie honnete ----
    verts = [x for x in retenues if x[3] and x[3]["niveau"]=="forte"]
    rouges = [x for x in retenues if x[3] and x[3]["niveau"]=="faible"]
    if rouges and verts:
        st.info("💡 " + _t("Stratégie : vise d'abord une piste 🟢 (capacité forte), et "
                          "tente une 🔴 en PLUS — jamais à la place."))
    elif rouges and not verts:
        st.warning("⚠️ " + _t("Tes pistes actuelles sont toutes très sélectives. "
                              "Réponds « oui » à la question langue pour débloquer les "
                              "voies à forte capacité (Ausbildung, etc.)."))

    # ---- Alerte visa court sejour ----
    av = cap.get("alertes_visa",{})
    tr = av.get("taux_refus",{}).get(code.upper())  # None si non listee
    if tr:
        st.markdown("### 🛂 " + _t("À savoir sur les visas, pour ton passeport"))
        st.caption(_t("Refus du visa Schengen COURT séjour pour ta nationalité") +
                   f" : **{tr} %** " + _t("(données 2025). Le visa long séjour ÉTUDES "
                   "suit une autre logique et reste bien plus accessible."))
        mo = av.get("motifs_dominants",{})
        if mo:
            st.caption("📌 " + _t("Motifs de refus les plus fréquents") + " : " +
                       _t("ressources financières") + f" {mo.get('ressources_financieres','')} %, " +
                       _t("assurance non conforme") + f" {mo.get('assurance_non_conforme','')} %, " +
                       _t("doutes sur le retour") + f" {mo.get('doutes_sur_le_retour','')} %. " +
                       _t("Ces trois motifs se corrigent dans le dossier."))

    # ---- Langue ----
    if apprendre != "non":
        st.markdown("### 🔓 " + _t("La langue n'est pas un mur"))
        st.markdown(_t(
            "🟢 **Allemagne (Ausbildung)** : 150 000+ places non pourvues, formation "
            "PAYÉE 724–1 490 €/mois. Unique péage : allemand B1 (~12 mois, "
            "Goethe-Institut près de chez toi). C'est statistiquement la voie la plus "
            "ouverte au monde.\n\n"
            "🔴 **Corée (GKS), Japon (MEXT)** : la bourse enseigne la langue en te "
            "finançant — mais 2 à 13 % de réussite seulement. À tenter en plus, pas à "
            "la place.\n\n"
            "🟢 **Espagnol / portugais** : langues sœurs du français — la barrière la "
            "plus courte."))

    if fermees:
        st.caption("⛔ " + str(fermees) + " " +
                   _t("offres fermées à ta nationalité ont été écartées — aucun faux espoir."))
    st.caption("ℹ️ " + _t("Les taux indiqués sont des ordres de grandeur publics, "
                         "pas une prédiction sur ton dossier."))

    # ---- 💎 CE QUE TU VIENS D OBTENIR (rendre la valeur visible) ----
    n_pistes   = len(retenues)
    n_portes   = len(portes)
    n_sources  = len({o.get("source_url") for _s,_j,o,_v in retenues
                      if o.get("source_url")})
    n_officiels = sum(1 for p in portes if p.get("canal_officiel"))
    st.markdown("### 💎 " + _t("Ce que tu viens d'obtenir, gratuitement"))
    lignes = []
    lignes.append(f"**{n_pistes}** " + _t("pistes vérifiées pour TON passeport"))
    if n_portes:
        lignes.append(f"**{n_portes}** " + _t("porte(s) réservée(s) à ta nationalité "
                                              "que presque personne ne présente"))
    if n_sources:
        lignes.append(f"**{n_sources}** " + _t("liens officiels directs (jamais un "
                                               "intermédiaire)"))
    if n_officiels:
        lignes.append(f"**{n_officiels}** " + _t("canal(aux) officiel(s) GRATUIT(s) "
                                                 "identifié(s)"))
    lignes.append(_t("Les taux de réussite réels de chaque voie — ce que personne "
                     "ne te dit avant que tu paies"))
    if fermees:
        _mot = _t("fausse piste écartée") if fermees == 1 else _t("fausses pistes écartées")
        lignes.append(f"**{fermees}** " + _mot + " " +
                      _t("(fermée(s) à ta nationalité — aucun faux espoir)"))
    for l in lignes:
        st.markdown("✓ " + l)
    if tr:
        st.info("💰 " + _t("Concrètement : un visa Schengen refusé, ce sont ~90 € de "
                           "frais perdus et non remboursables. Les 3 motifs "
                           "ci-dessus causent près de la moitié des refus — et ils "
                           "se corrigent AVANT de payer."))
    else:
        st.info("💰 " + _t("Ces informations sont publiques et gratuites. Si "
                           "quelqu'un te les fait payer, c'est déjà un mauvais "
                           "signe."))

    # ---- 🔑 INVITATION A CREER UN COMPTE (apres la valeur recue) ----
    if not _cx:
        _caches = max(0, len(retenues[:6]) - N_LIBRES)
        st.markdown("### 🔑 " + _t("Va plus loin — c'est gratuit"))
        _l = []
        if _caches:
            _l.append(f"**{_caches}** " + _t("piste(s) dont le mode d'emploi "
                                             "complet t'attend"))
        _l.append("📄 " + _t("Télécharge ton plan complet en PDF"))
        _l.append(_t("Ton profil pré-rempli : plus besoin de tout retaper"))
        _l.append(_t("Tes résultats sauvegardés dans « Mes projets »"))
        _l.append(_t("Alerté quand une nouvelle porte s'ouvre pour ") + f"**{nat}**")
        for _x in _l:
            st.markdown("→ " + _x)
        st.caption("⏱️ " + _t("30 secondes, sans carte bancaire. Yorbity reste "
                              "gratuit."))

    # ---- 📤 PARTAGE : uniquement ce qui ne coûte AUCUNE chance ----
    # Doctrine : on ne partage jamais une voie rivale (🔴, 2-4 places/pays) —
    # ce serait demander a quelqu un de reduire ses propres chances.
    # On partage les voies 🟢 (places non pourvues) et l alerte anti-arnaque :
    # partager ne coute rien et protege les siens.
    partageables = [x for x in retenues if x[3] and x[3]["niveau"] == "forte"]
    porte_verte = None
    for p in portes:
        _cid, _v = _voie_de_porte(p.get("code_porte",""), cap)
        if _v and _v.get("niveau") == "forte":
            porte_verte = (p, _v); break
    if partageables or porte_verte:
        st.markdown("### 📤 " + _t("Fais-en profiter quelqu'un"))
        if porte_verte:
            p, v = porte_verte
            texte = (_t("Regarde ça") + " : " + p["nom"] + ". " +
                     v.get("capacite","") + ". " +
                     _t("Canal officiel GRATUIT") + " : " +
                     p.get("canal_officiel","") + " — " +
                     _t("si on te demande de l'argent, c'est une arnaque.") + " " +
                     _t("Vérifie ton passeport ici :"))
        else:
            _s0, _j0, o0, v0 = partageables[0]
            texte = (_t("Regarde ça") + " : " + o0.get("titre","") + " — " +
                     v0.get("capacite","") + ". " +
                     _t("Vérifie si ton passeport passe :"))
        st.caption(_t("Ces voies ont plus de places que de candidats : les "
                      "partager ne réduit les chances de personne."))
        _url_site = os.environ.get("YORBITY_URL", "")
        _msg = texte + (" " + _url_site if _url_site else "")
        st.markdown("📲 [" + _t("Partager sur WhatsApp") + "]"
                    "(https://wa.me/?text=" + urllib.parse.quote(_msg) + ")")
        if not _url_site:
            st.caption("⚙️ " + _t("(admin : définis YORBITY_URL dans .env pour "
                                  "ajouter le lien du site au message partagé)"))
        st.caption("🛡️ " + _t("Partager une mise en garde contre les arnaques ne "
                              "coûte rien et protège les tiens."))

    # ---- 📄 EXPORT PDF DU PLAN (comptes) — patch_export_pdf ----
    if _cx:
        try:
            import export_pdf as _ep
            if _ep.disponible():
                _portes_pdf = []
                for _p in portes:
                    _cid2, _v2 = _voie_de_porte(_p.get("code_porte",""), cap)
                    _portes_pdf.append({
                        "nom": (PASTILLE.get(_v2["niveau"],"")+" " if _v2 else "") + _p.get("nom",""),
                        "capacite": (_v2 or {}).get("capacite",""),
                        "mecanique_detail": _p.get("mecanique_detail",""),
                        "barriere_langue": _p.get("barriere_langue",""),
                        "canal_officiel": _p.get("canal_officiel",""),
                        "arnaques": _p.get("arnaques","")})
                _pistes_pdf = []
                for _s2, _j2, _o2, _v2 in retenues[:6]:
                    _pistes_pdf.append({
                        "pastille": PASTILLE.get(_v2["niveau"],"") if _v2 else "⚪",
                        "titre": _o2.get("titre",""),
                        "destination": _o2.get("destination",""),
                        "capacite": (_v2 or {}).get("capacite",""),
                        "taux": (_v2 or {}).get("taux",""),
                        "barriere": (_v2 or {}).get("barriere_reelle",""),
                        "lien": _o2.get("source_url","")})
                _al = None
                if tr:
                    _mo = av.get("motifs_dominants",{})
                    _al = {"taux": tr, "motifs":
                           f"ressources financières {_mo.get('ressources_financieres','')} %, "
                           f"assurance non conforme {_mo.get('assurance_non_conforme','')} %, "
                           f"doutes sur le retour {_mo.get('doutes_sur_le_retour','')} %"}
                _lgn = None
                if apprendre != "non":
                    _lgn = [
                     "🟢 Allemagne (Ausbildung) : 150 000+ places non pourvues, formation "
                     "PAYÉE 724–1 490 €/mois — péage unique : allemand B1 (~12 mois).",
                     "🔴 Corée (GKS), Japon (MEXT) : la bourse enseigne la langue en te "
                     "finançant — mais 2 à 13 % de réussite. À tenter EN PLUS, jamais à la place.",
                     "🟢 Espagnol / portugais : langues sœurs du français — la barrière la plus courte."]
                _octets = _ep.pdf_plan(
                    {"nat": nat, "age": age, "niveau_lbl": NIVEAUX_LBL[niveau],
                     "domaine": domaine, "objectif_lbl": dict(OBJECTIFS)[objectif]},
                    gagnant if best else None, _portes_pdf, _pistes_pdf, _al, _lgn,
                    contact=("WhatsApp " + os.environ.get("CONTACT_WHATSAPP","")
                             if os.environ.get("CONTACT_WHATSAPP") else ""))
                st.download_button("📄 " + _t("Télécharger mon plan (PDF)"),
                                   data=_octets,
                                   file_name=f"yorbity_plan_{code.lower()}.pdf",
                                   mime="application/pdf",
                                   use_container_width=True)
        except Exception as _e_pdf:
            st.caption("⚙️ " + _t("(admin : « pip install fpdf2 » pour activer "
                                  "l'export PDF)") + f" [{type(_e_pdf).__name__}]")

    num = os.environ.get("CONTACT_WHATSAPP","").replace(" ","").replace("+","")
    if num:
        msg = (f"Bonjour Yorbity ! Profil : {nat}, {age} ans, {NIVEAUX_LBL[niveau]}, "
               f"{domaine}. Objectif : {dict(OBJECTIFS)[objectif]}. Questionnaire fait.")
        st.markdown(f"💬 [{_t('En parler sur WhatsApp')}]"
                    f"(https://wa.me/{num}?text={urllib.parse.quote(msg)})")
    if st.button("← " + _t("Retour au parcours"), key="q_retour2"):
        st.session_state.show_questionnaire = False; st.rerun()
    return True
