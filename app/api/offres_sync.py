# =============================================================================
# offres_sync.py — Synchronisation continue du job board + contrôle des liens
# - Paramètre admin : liens des offres visibles ou non pour les visiteurs
#   (modèle « réservé membres » façon CFA Institute — désactivé par défaut)
# - Ingestion : les offres API (stage/emploi/métier) sont ENREGISTRÉES en base
#   par pays ; les nouvelles offres (ex : jardinier en Belgique) sont ajoutées
#   automatiquement après passage par l'AGENT de validation (Ollama) qui lit
#   la description et estime l'ouverture aux internationaux + les nationalités
# - Vérification des liens : les offres au lien mort sont retirées de la base
# - Rafraîchissement : automatique quand le dernier passage date de +12 h,
#   ou manuel via l'écran admin 🔄
# =============================================================================
import streamlit as st
import sqlite3, json, datetime, re, urllib.request, urllib.error

DB = "data/mobilite.db"
SYNC_HEURES = 12


def _init():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS config_params(cle TEXT PRIMARY KEY, valeur TEXT)")
    con.commit(); con.close()


def param(cle, defaut=""):
    _init()
    con = sqlite3.connect(DB)
    row = con.execute("SELECT valeur FROM config_params WHERE cle=?", (cle,)).fetchone()
    con.close()
    return row[0] if row else defaut


def definir_param(cle, valeur):
    _init()
    con = sqlite3.connect(DB)
    con.execute("INSERT OR REPLACE INTO config_params VALUES(?,?)", (cle, str(valeur)))
    con.commit(); con.close()


def liens_actifs():
    """Les visiteurs voient-ils les liens des offres ? (défaut : non)"""
    return param("liens_offres_visibles", "0") == "1"


def descriptions_actives():
    """Les visiteurs voient-ils la description des offres ? (défaut : oui)"""
    return param("descriptions_offres_visibles", "1") == "1"


def agent_valide(titre, description, dest_code):
    """Lit la description d'une offre et estime :
      - international : ouverte aux candidats internationaux ?
      - origines : 'TOUS' ou liste de codes ISO2 si des nationalités sont citées
      - metier : intitulé court du métier
    Repli sûr (TOUS/international) si Ollama indisponible."""
    try:
        from traduction import OLLAMA, MODEL
        prompt = ("Tu es un analyste d'offres d'emploi. Lis cette offre et réponds "
                  "UNIQUEMENT par un JSON de la forme "
                  '{"international": true|false, "origines": "TOUS" ou "CM,GA,SN", '
                  '"metier": "intitulé court"}. '
                  '"international"=false SEULEMENT si l\'offre exige explicitement la '
                  "citoyenneté ou un permis de travail local préexistant. "
                  '"origines" = codes pays ISO2 UNIQUEMENT si des nationalités '
                  "précises sont citées, sinon TOUS.\n\n"
                  f"Destination : {dest_code}\nTitre : {titre}\nDescription : {description[:800]}")
        payload = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                              "options": {"temperature": 0.1}}).encode()
        req = urllib.request.Request(f"{OLLAMA}/api/generate", data=payload,
                                     headers={"Content-Type": "application/json"})
        rep = json.loads(urllib.request.urlopen(req, timeout=60).read()).get("response", "")
        m = re.search(r"\{.*\}", rep, re.S)
        if m:
            d = json.loads(m.group(0))
            origines = str(d.get("origines", "TOUS")).upper().replace(" ", "")
            if not re.fullmatch(r"TOUS|([A-Z]{2})(,[A-Z]{2})*", origines):
                origines = "TOUS"
            return {"international": bool(d.get("international", True)),
                    "origines": origines,
                    "metier": str(d.get("metier", ""))[:60]}
    except Exception:
        pass
    return {"international": True, "origines": "TOUS", "metier": ""}


def _existe(con, url, titre, dest):
    if url and con.execute("SELECT 1 FROM opportunites WHERE source_url=?",
                           (url,)).fetchone():
        return True
    return bool(con.execute(
        "SELECT 1 FROM opportunites WHERE titre=? AND destination=?",
        (titre, dest)).fetchone())


def ingerer(dest_code, avec_agent=True):
    """Récupère les offres API (stage/emploi/métier) et les ENREGISTRE en base
    pour ce pays. Retourne (ajoutées, ignorées)."""
    try:
        import jobs_api
    except Exception:
        return 0, 0
    if not (jobs_api.disponible() and jobs_api.couvre(dest_code)):
        return 0, 0
    ajout, deja = 0, 0
    con = sqlite3.connect(DB)
    for type_p in ("stage", "emploi", "metier"):
        for o in jobs_api.chercher(dest_code, type_p):
            if _existe(con, o.get("url", ""), o.get("titre", ""), dest_code.upper()):
                deja += 1
                continue
            infos = agent_valide(o.get("titre", ""), o.get("extrait", ""),
                                 dest_code) if avec_agent else \
                {"international": True, "origines": "TOUS", "metier": ""}
            if not infos["international"]:
                deja += 1
                continue
            titre = o.get("titre", "")
            if type_p == "metier" and infos.get("metier") and \
                    infos["metier"].lower() not in titre.lower():
                titre = f"{infos['metier']} — {titre}"
            con.execute(
                "INSERT INTO opportunites(type,titre,destination,origines_eligibles,"
                "niveau,domaine,montant,deadline,source_url,maj,statut) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (type_p, titre, dest_code.upper(), infos["origines"], "",
                 o.get("entreprise", ""), o.get("salaire", ""), "",
                 o.get("url", ""),
                 datetime.date.today().isoformat(), "auto"))
            con.commit()   # patch_verrou_sync: relache le verrou entre chaque offre (jamais tenu pendant le reseau)
            ajout += 1
    con.commit(); con.close()
    return ajout, deja


# --- ajoute par patch_yorbity.py -------------------------------------------
def _ingerer_sources_obsolete(dest_code, sans_permis=None):
    """OBSOLETE — la table opportunites n'a ni description ni reference.
    Job Bank passe desormais par jobs_api.chercher() -> registre.
    Conservee pour reference ; ne pas appeler.

    
    Ingere via le REGISTRE de sources (app/api/sources/) plutot que via une
    source codee en dur. Ajouter un pays = ecrire un adaptateur, rien d'autre.

    sans_permis=True  -> ne garde que les offres postulables SANS permis de
                         travail. Au Canada, aucun emploi etudiant ne l'est :
                         le travail hors campus exige un permis d'etudes valide.
    Retourne (ajoutees, ignorees).
    """
    try:
        from sources import registre
    except Exception as e:
        print("registre indisponible :", e)
        return 0, 0

    ajout, deja = 0, 0
    con = sqlite3.connect(DB)
    for type_p in ("stage", "emploi", "metier"):
        for o in registre.collecter(dest_code, type_p, sans_permis=sans_permis):
            if _existe(con, o.get("url", ""), o.get("titre", ""), dest_code.upper()):
                deja += 1
                continue
            con.execute(
                "INSERT INTO opportunites(type,titre,destination,origines_eligibles,"
                "niveau,domaine,montant,deadline,source_url,maj,statut) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (type_p, o.get("titre", ""), dest_code.upper(), "TOUS", "",
                 o.get("entreprise", ""), o.get("salaire", ""), "",
                 o.get("url", ""), datetime.date.today().isoformat(), "auto"))
            ajout += 1
    con.commit()
    con.close()
    return ajout, deja


def prechauffer_traductions(offres, langues=None):
    """Traduit d'avance les offres : l'utilisateur n'attend jamais Ollama."""
    try:
        import traduction_offres
        traduction_offres.prechauffer(offres, langues)
    except Exception as e:
        print("prechauffage impossible :", e)
# ---------------------------------------------------------------------------

def verifier_liens(dest_code=None):
    """Retire de la base les offres AUTO dont le lien est mort (404/410)."""
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    q = "SELECT id, source_url FROM opportunites WHERE statut='auto' AND source_url<>''"
    args = ()
    if dest_code:
        q += " AND destination=?"; args = (dest_code.upper(),)
    rows = con.execute(q, args).fetchall()
    mortes = 0
    for r in rows:
        try:
            req = urllib.request.Request(r["source_url"], method="HEAD",
                                         headers={"User-Agent": "Mozilla/5.0"})
            urllib.request.urlopen(req, timeout=10)
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                con.execute("DELETE FROM opportunites WHERE id=?", (r["id"],))
                mortes += 1
        except Exception:
            pass          # timeout/refus : on garde, on retentera
    con.commit(); con.close()
    return mortes


def sync_si_necessaire(dest_code):
    """Rafraîchissement continu : ingère si le dernier passage date de +12 h."""
    cle = f"sync_{dest_code.upper()}"
    dernier = param(cle, "")
    try:
        if dernier and (datetime.datetime.now()
                        - datetime.datetime.fromisoformat(dernier)
                        < datetime.timedelta(hours=SYNC_HEURES)):
            return
    except Exception:
        pass
    definir_param(cle, datetime.datetime.now().isoformat(timespec="seconds"))
    try:
        ingerer(dest_code, avec_agent=True)
        verifier_liens(dest_code)
    except Exception:
        pass


def ecran():
    if not st.session_state.get("show_sync"):
        return False
    st.markdown("## 🔄 Offres & liens")

    st.markdown("#### 🔗 Liens des offres (modèle « réservé »)")
    actuel = liens_actifs()
    nv = st.toggle("Montrer les liens des offres aux visiteurs",
                   value=actuel,
                   help="Désactivé : le visiteur voit la description et une référence, "
                        "sans lien (l'admin voit toujours les liens). Tu pourras plus "
                        "tard réserver les liens aux clients Premium.")
    if nv != actuel:
        definir_param("liens_offres_visibles", "1" if nv else "0")
        st.rerun()

    actuel_d = descriptions_actives()
    nd = st.toggle("Montrer la description des offres aux visiteurs",
                   value=actuel_d,
                   help="Désactivé : le visiteur voit le titre du poste, mais la "
                        "description est réservée (l'admin la voit toujours).")
    if nd != actuel_d:
        definir_param("descriptions_offres_visibles", "1" if nd else "0")
        st.rerun()

    st.markdown("#### 🔄 Synchronisation manuelle")
    dest = st.text_input("Code destination (ex : CA)", max_chars=2)
    c1, c2 = st.columns(2)
    if c1.button("Ingérer les offres API", type="primary") and dest:
        a, d = ingerer(dest)
        st.success(f"{a} offre(s) ajoutée(s), {d} déjà connue(s)/écartée(s).")
    if c2.button("Vérifier les liens") and dest:
        m = verifier_liens(dest)
        st.success(f"{m} offre(s) au lien mort retirée(s).")

    con = sqlite3.connect(DB)
    try:
        n_auto = con.execute("SELECT COUNT(*) FROM opportunites WHERE statut='auto'").fetchone()[0]
        n_tot = con.execute("SELECT COUNT(*) FROM opportunites").fetchone()[0]
        st.caption(f"Base : {n_tot} offre(s) dont {n_auto} ingérée(s) automatiquement.")
    except Exception:
        pass
    con.close()

    st.divider()
    if st.button("← Retour", key="sync_retour"):
        st.session_state.show_sync = False
        st.rerun()
    return True
