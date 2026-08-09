# =============================================================================
# jobs_api.py — Job board intégré (offres d'emploi/stage EN DIRECT via API)
# Source : API Adzuna (gratuite — clés dans .env : ADZUNA_APP_ID, ADZUNA_APP_KEY).
# Cache SQLite 12 h pour respecter les quotas. Affichage en cartes :
#   - VISITEUR : titre, entreprise, lieu, salaire, extrait — SANS lien externe,
#     avec une référence à indiquer dans le formulaire de contact.
#   - ADMIN    : mêmes cartes + lien direct vers l'offre.
# =============================================================================
import streamlit as st
import sqlite3, os, json, datetime, urllib.request, urllib.parse

DB = "data/mobilite.db"
CACHE_HEURES = 12
MAX_OFFRES = 8
MAX_JOURS_OFFRE = 30   # n'afficher que les offres publiées dans les 30 derniers jours (réglable)

# --- ajoute par patch_yorbity.py -------------------------------------------
def _langue_courante():
    """La cle i18n varie selon les pages ; on essaie les noms connus."""
    for cle in ("langue", "lang", "language"):
        v = st.session_state.get(cle)
        if v:
            return str(v)[:2].lower()
    return "fr"


def _toff(texte):
    """
    tr() est un dictionnaire de cles STATIQUES : un titre d'offre anglais
    n'y figure pas et ressortait tel quel. On tente d'abord tr(), puis
    traduction_offres (Ollama + cache SQLite).
    """
    if not texte:
        return texte
    try:
        traduit = tr(texte)
        if traduit and traduit != texte:
            return traduit
    except Exception:
        pass
    try:
        import traduction_offres
        return traduction_offres.traduire(texte, _langue_courante(), langue_source="en")
    except Exception:
        return texte
# ---------------------------------------------------------------------------


PAYS_ADZUNA = {"FR": "fr", "GB": "gb", "CA": "ca", "DE": "de", "US": "us",
               "IT": "it", "ES": "es", "NL": "nl", "AT": "at", "BE": "be",
               "CH": "ch", "AU": "au", "NZ": "nz", "BR": "br", "IN": "in",
               "MX": "mx", "PL": "pl", "SG": "sg", "ZA": "za"}

FRANCOPHONES = {"fr", "be", "ch"}

# Offres à écarter : plateformes de livraison / VTC, sans valeur pour un projet étudiant
BRUIT = ("uber", "deliveroo", "doordash", "skipthedishes", "lyft", "instacart",
         "livreur", "delivery driver", "food delivery", "courier", "coursier")


def _bruit(offre):
    txt = (offre.get("titre", "") + " " + offre.get("entreprise", "")).lower()
    return any(b in txt for b in BRUIT)

METIERS_FR = "menuisier charpentier électricien maçon plombier soudeur"
METIERS_EN = "carpenter electrician plumber welder bricklayer joiner"


def _mots(type_projet, pays, domaine=""):
    """(mots, champ_api) selon le type, la langue du pays et le domaine visé."""
    if type_projet == "metier":
        return (METIERS_FR if pays in FRANCOPHONES else METIERS_EN), "what_or"
    if type_projet == "stage":
        base = "stage" if pays in FRANCOPHONES else "internship"
    else:
        base = ("emploi étudiant campus" if pays in FRANCOPHONES
                else "student campus part-time")
    if domaine and "tous" not in domaine.lower() and "all" not in domaine.lower():
        base = f"{base} {domaine.split('&')[0].strip()}"
    return base, "what"


def _env(cle, defaut=""):
    v = os.environ.get(cle)
    if v:
        return v
    for chemin in (".env", "app/.env", "app/api/.env"):
        if os.path.exists(chemin):
            for l in open(chemin, encoding="utf-8", errors="ignore"):
                l = l.strip()
                if l.startswith(cle + "="):
                    return l.split("=", 1)[1].strip().strip('"').strip("'")
    return defaut


def disponible():
    a, b = _env("ADZUNA_APP_ID"), _env("ADZUNA_APP_KEY")
    return bool(a and b and b != "A_REMPLACER")


def _couvre_adzuna(dest_code):
    return dest_code.upper() in PAYS_ADZUNA


def _init():
    con = _cx()
    con.execute("""CREATE TABLE IF NOT EXISTS jobs_cache(
        cle TEXT PRIMARY KEY, dest TEXT, type TEXT, contenu TEXT, maj TEXT)""")
    con.commit(); con.close()


def _requete_api(pays_adz, mots, champ="what"):
    """Appel Adzuna. Liste d'offres normalisées, ou None si échec."""
    app_id, app_key = _env("ADZUNA_APP_ID"), _env("ADZUNA_APP_KEY")
    params = urllib.parse.urlencode({
        "app_id": app_id, "app_key": app_key,
        "results_per_page": MAX_OFFRES, champ: mots,
        "max_days_old": MAX_JOURS_OFFRE, "sort_by": "date",
        "content-type": "application/json"})
    url = f"https://api.adzuna.com/v1/api/jobs/{pays_adz}/search/1?{params}"
    try:
        rep = json.loads(urllib.request.urlopen(url, timeout=20).read())
    except Exception:
        return None
    offres = []
    for r in rep.get("results", [])[:MAX_OFFRES]:
        sal = ""
        smin, smax = r.get("salary_min"), r.get("salary_max")
        if smin or smax:
            if smin and smax and int(smin) != int(smax):
                sal = f"{int(smin):,} – {int(smax):,}".replace(",", " ")
            else:
                sal = f"{int(smin or smax):,}".replace(",", " ")
        offres.append({
            "id": str(r.get("id", "")),
            "titre": (r.get("title") or "").strip(),
            "entreprise": ((r.get("company") or {}).get("display_name") or "").strip(),
            "lieu": ((r.get("location") or {}).get("display_name") or "").strip(),
            "salaire": sal,
            "extrait": (r.get("description") or "")[:220],
            "date": (r.get("created") or "")[:10],
            "url": r.get("redirect_url") or "",
        })
    return offres


def _chercher_adzuna(dest_code, type_projet, domaine=""):
    """Offres en direct (cache 12 h). Retourne une liste (peut être vide)."""
    pays = PAYS_ADZUNA.get(dest_code.upper())
    if not pays or not disponible():
        return []
    mots, champ = _mots(type_projet, pays, domaine)
    cle = f"{pays}:{type_projet}:{domaine[:20]}"
    _init()
    con = _cx(); con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM jobs_cache WHERE cle=?", (cle,)).fetchone()
    con.close()
    if row:
        try:
            age = datetime.datetime.now() - datetime.datetime.fromisoformat(row["maj"])
            if age < datetime.timedelta(hours=CACHE_HEURES):
                return json.loads(row["contenu"])
        except Exception:
            pass
    offres = _requete_api(pays, mots, champ)
    if offres:                       # dédup + retrait du bruit (livraison, VTC)
        vus, uniques = set(), []
        for o in offres:
            if _bruit(o):
                continue
            cle_o = (o.get("titre", "").lower(), o.get("entreprise", "").lower())
            if cle_o in vus:
                continue
            vus.add(cle_o); uniques.append(o)
        offres = uniques
    if offres is None:                      # API en panne → dernier cache connu
        return json.loads(row["contenu"]) if row else []
    con = _cx()
    con.execute("INSERT OR REPLACE INTO jobs_cache VALUES(?,?,?,?,?)",
                (cle, dest_code.upper(), type_projet, json.dumps(offres),
                 datetime.datetime.now().isoformat(timespec="seconds")))
    con.commit(); con.close()
    return offres


# --- ajoute par patch_registre.py ------------------------------------------
def _cx(timeout=30):
    """Connexion SQLite tolerante aux acces concurrents (Streamlit reruns)."""
    con = sqlite3.connect(DB, timeout=timeout)
    try:
        con.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass
    return con


def _cache_lire(cle, heures=CACHE_HEURES):
    _init()
    con = _cx()
    con.row_factory = sqlite3.Row
    try:
        row = con.execute("SELECT * FROM jobs_cache WHERE cle=?", (cle,)).fetchone()
    finally:
        con.close()
    if not row:
        return None
    try:
        age = datetime.datetime.now() - datetime.datetime.fromisoformat(row["maj"])
        if age.total_seconds() < heures * 3600:
            return json.loads(row["contenu"])
    except Exception:
        pass
    return None


def _cache_ecrire(cle, dest, type_projet, offres):
    _init()
    con = _cx()
    try:
        con.execute(
            "INSERT OR REPLACE INTO jobs_cache(cle,dest,type,contenu,maj) "
            "VALUES(?,?,?,?,?)",
            (cle, dest, type_projet, json.dumps(offres, ensure_ascii=False),
             datetime.datetime.now().isoformat(timespec="seconds")))
        con.commit()
    finally:
        con.close()


def chercher(dest_code, type_projet, domaine=""):
    """
    Offres en direct, TOUTES SOURCES (registre : Adzuna + Job Bank + futures).
    Cache 12 h. Repli sur Adzuna seul si le registre est indisponible.
    """
    cle = f"all:{dest_code.upper()}:{type_projet}:{domaine[:20]}"
    cache = _cache_lire(cle)
    if cache is not None:
        return cache

    try:
        from sources import registre
        offres = registre.collecter(dest_code, type_projet,
                                    mots_cles=domaine or None, limite=MAX_OFFRES)
    except Exception as e:
        print("registre indisponible, repli Adzuna seul :", e)
        offres = _chercher_adzuna(dest_code, type_projet, domaine) or []

    offres = [o for o in offres if not _bruit(o)]
    try:
        _cache_ecrire(cle, dest_code.upper(), type_projet, offres)
    except Exception as e:
        print("cache non ecrit :", e)
    return offres


def couvre(dest_code):
    """Vrai si AU MOINS une source du registre couvre cette destination."""
    if dest_code.upper() in PAYS_ADZUNA:
        return True
    try:
        from sources import registre
        return dest_code.upper() in registre.destinations_couvertes()
    except Exception:
        return False
# ---------------------------------------------------------------------------

# --- ajoute par patch_pagination.py ----------------------------------------
def _cle_page(dest_code, type_p, domaine):
    return f"page__{dest_code}__{type_p}__{domaine[:20]}"


def chercher_page(dest_code, type_projet, domaine="", page=1, par_page=None):
    """
    Une PAGE d'offres, toutes sources, + le total disponible.
    Cache 12 h par page (cle distincte de celle de chercher()).
    """
    par_page = par_page or MAX_OFFRES
    page = max(1, int(page))
    cle = f"page:{dest_code.upper()}:{type_projet}:{domaine[:20]}:{page}:{par_page}"

    cache = _cache_lire(cle)
    if isinstance(cache, dict):
        return cache.get("offres", []), cache.get("total", 0)

    try:
        from sources import registre
        offres, total = registre.collecter_page(
            dest_code, type_projet, mots_cles=domaine or None,
            page=page, par_page=par_page)
    except Exception as e:
        print("registre indisponible, repli Adzuna seul :", e)
        tout = _chercher_adzuna(dest_code, type_projet, domaine) or []
        total = len(tout)
        debut = (page - 1) * par_page
        offres = tout[debut:debut + par_page]

    offres = [o for o in offres if not _bruit(o)]
    try:
        _cache_ecrire(cle, dest_code.upper(), type_projet,
                      {"offres": offres, "total": total})
    except Exception as e:
        print("cache non ecrit :", e)
    return offres, total


def _cta_offre(o, tr, cle):
    """Appel a l'action AU MOMENT DE L'INTENTION : sous la reference."""
    if st.button("🤝 " + tr("Postuler avec notre accompagnement"),
                 key=cle, use_container_width=True):
        st.session_state["offre_choisie"] = {
            "reference": o.get("reference") or f"JOB-{o['id'][:10]}",
            "titre": o.get("titre", ""),
            "entreprise": o.get("entreprise", ""),
            "source": o.get("source", ""),
        }
        st.success("✅ " + tr("Offre sélectionnée — clique sur « Parle-nous de ton projet » "
                             "et indique cette référence."))


def afficher(dest_code, tr, admin=False, code_orig="",
             types_live=("stage", "emploi", "metier"), poste="", domaine=""):
    """Affiche le job board pagine. Retourne le nb d'offres de la page."""
    try:
        import eligibilite
    except Exception:
        eligibilite = None
    try:
        import offres_sync
        _liens = offres_sync.liens_actifs()
        _desc = offres_sync.descriptions_actives()
    except Exception:
        _liens = False
        _desc = True

    TITRES = {"stage": "🧑‍💻 Stages en direct",
              "emploi": "💼 Emplois étudiants en direct",
              "metier": "🔧 Métiers spécialisés qui recrutent"}
    total_affiche = 0

    for type_p in types_live:
        titre = TITRES.get(type_p, type_p)

        if eligibilite is not None and code_orig:
            ok, note = eligibilite.autorise(dest_code, type_p, code_orig)
            if not ok:
                st.warning("🛂 " + tr("D'après nos informations, ce type d'offre "
                           "n'est pas ouvert aux ressortissants de ton pays "
                           "d'origine pour cette destination.")
                           + ((" " + tr(note)) if note else ""))
                continue
            if note:
                st.caption("🛂 " + tr(note))

        page_cle = _cle_page(dest_code, type_p, domaine)
        page = int(st.session_state.get(page_cle, 1))
        offres, total = chercher_page(dest_code, type_p, domaine, page)

        if poste:
            try:
                import recherche_poste
                offres = recherche_poste.filtre(offres, poste)
            except Exception:
                pass

        # Page devenue vide (filtre ou offres retirees) : revenir a la page 1.
        if not offres and page > 1:
            st.session_state[page_cle] = 1
            st.rerun()
        if not offres:
            continue

        st.markdown("#### " + tr(titre))

        par_page = MAX_OFFRES
        debut = (page - 1) * par_page + 1
        fin = debut + len(offres) - 1
        pages = max(1, -(-total // par_page))       # ceil
        if total > par_page:
            st.caption(f"{tr('Offres')} {debut}–{fin} {tr('sur environ')} {total}"
                       f"  ·  {tr('page')} {page}/{pages}")

        for i, o in enumerate(offres):
            total_affiche += 1
            entete = _toff(o["titre"]) if o["titre"] else tr("Offre")
            if o["entreprise"]:
                entete += f" — {o['entreprise']}"

            with st.expander(entete):
                if admin or _desc:
                    if o["lieu"]:
                        st.markdown("📍 " + _toff(o["lieu"]))
                    if o["salaire"]:
                        st.markdown("💶 " + o["salaire"])
                    if o["extrait"]:
                        st.write(_toff(o["extrait"]) + "…")
                    if o["date"]:
                        st.caption(tr("Publiée le") + " " + o["date"])
                else:
                    st.caption("🔒 " + tr("Description réservée — contacte-nous via le "
                                          "formulaire en bas de page."))

                st.caption("📌 " + tr("Référence à indiquer dans le formulaire :")
                           + " " + (o.get("reference") or f"JOB-{o['id'][:10]}"))

                _cta_offre(o, tr, f"cta_{type_p}_{page}_{o['id']}")

                if o.get("url") and (admin or (_liens and o.get("lien_accessible", True))):
                    st.link_button(
                        "🔗 " + (tr("Lien (admin)") if admin and not _liens
                                 else tr("Voir l'offre")), o["url"])

            # Rappel compact, une seule fois, apres la 3e offre.
            if i == 2 and len(offres) > 3:
                st.info("🤝 " + tr("Une offre t'intéresse ? On s'occupe du dossier, "
                                   "du visa et des traductions — voir nos services "
                                   "en bas de page."))

        # ---- Navigation ----------------------------------------------------
        if pages > 1:
            g, m, d = st.columns([1, 2, 1])
            with g:
                if st.button("‹ " + tr("Précédent"), key=f"prec_{type_p}",
                             disabled=page <= 1, use_container_width=True):
                    st.session_state[page_cle] = page - 1
                    st.rerun()
            with m:
                st.caption(f"<div style='text-align:center'>{page} / {pages}</div>",
                           unsafe_allow_html=True)
            with d:
                if st.button(tr("Suivant") + " ›", key=f"suiv_{type_p}",
                             disabled=fin >= total, use_container_width=True):
                    st.session_state[page_cle] = page + 1
                    st.rerun()

    return total_affiche
# ---------------------------------------------------------------------------
