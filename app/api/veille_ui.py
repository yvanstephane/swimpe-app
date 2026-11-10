# =============================================================================
# veille_ui.py — Écran admin « 👁 Veille » (tendances & sources, par pays)
# -----------------------------------------------------------------------------
# L'équivalent Swimpe d'un « Agent Reach » : des yeux sur le web ouvert.
# S'appuie sur la brique EXISTANTE recherche_web_v1 (Tavily, cache 24 h,
# compteur de crédits, voyant 🟢🟡🔴). Grâce au cache, relancer la veille le
# même jour ne consomme AUCUN crédit supplémentaire.
#
# Trois blocs :
#   1. Le voyant d'état (clé, quota, dernier succès)
#   2. La veille : requêtes par pays → résultats (tendances, idées de posts,
#      sources d'offres potentielles)
#   3. Les « pages à surveiller » (liste de pages qu'on visite à la main,
#      ex. pages Facebook virales — pas de robot là-dessus)
#
# Les réglages (requêtes, pages) vivent dans les paramètres clé/valeur
# d'offres_sync — aucune nouvelle table, rien à coller dans Supabase.
# =============================================================================
import streamlit as st

try:
    import recherche_web_v1 as rw
except Exception:
    rw = None

try:
    import offres_sync as _osy
except Exception:
    _osy = None

DRAPEAUX = {"CM": "🇨🇲 Cameroun", "SN": "🇸🇳 Sénégal", "CI": "🇨🇮 Côte d'Ivoire",
            "ALL": "🌍 Général"}

# Requêtes par défaut : « CODE_PAYS: requête », une par ligne.
REQUETES_DEFAUT = """CM: offres emploi et stages jeunes Cameroun
CM: concours fonction publique Cameroun
CM: arnaques recrutement faux concours Cameroun
SN: offres emploi et stages jeunes Sénégal
SN: concours fonction publique Sénégal
SN: arnaques recrutement Sénégal
CI: offres emploi et stages jeunes Côte d'Ivoire
CI: concours fonction publique Côte d'Ivoire
CI: arnaques recrutement Côte d'Ivoire
ALL: bourses et volontariat jeunes Afrique francophone"""

PAGES_DEFAUT = """Fanné Yaya | https://www.facebook.com/profile.php?id=100086192266443"""


def _param(cle, defaut=""):
    if _osy is None:
        return defaut
    try:
        return _osy.param(cle, defaut) or defaut
    except Exception:
        return defaut


def _definir_param(cle, valeur):
    if _osy is None:
        return
    try:
        _osy.definir_param(cle, valeur)
    except Exception as e:
        st.error(f"Enregistrement impossible : {e}")


def _lire_requetes():
    """[(code_pays, requête), …] depuis le paramètre, sinon les défauts."""
    brut = _param("veille_requetes", REQUETES_DEFAUT)
    out = []
    for ligne in brut.splitlines():
        ligne = ligne.strip()
        if not ligne:
            continue
        if ":" in ligne:
            code, req = ligne.split(":", 1)
            code = code.strip().upper()
            if code not in DRAPEAUX:
                code, req = "ALL", ligne
        else:
            code, req = "ALL", ligne
        req = req.strip()
        if req:
            out.append((code, req))
    return out


def _lire_pages():
    """[(nom, url), …] des pages à surveiller à la main."""
    brut = _param("veille_pages", PAGES_DEFAUT)
    out = []
    for ligne in brut.splitlines():
        ligne = ligne.strip()
        if not ligne:
            continue
        if "|" in ligne:
            nom, url = ligne.split("|", 1)
        else:
            nom, url = ligne, ligne
        nom, url = nom.strip(), url.strip()
        if url.startswith("http"):
            out.append((nom or url, url))
    return out


def _voyant():
    if rw is None:
        st.error("Brique de recherche web introuvable (recherche_web_v1).")
        return
    try:
        e = rw.etat_recherche()
        st.markdown(f"{e['voyant']} {e['message']}")
        if e.get("code") == "pas_de_cle":
            st.caption("Ajoute TAVILY_API_KEY dans les secrets Streamlit "
                       "(Settings → Secrets) pour activer la veille en ligne.")
    except Exception as ex:
        st.caption(f"Voyant indisponible : {ex}")


def _lancer_veille():
    """Interroge chaque requête (le cache 24 h rend les relances gratuites)."""
    resultats = {}
    requetes = _lire_requetes()
    barre = st.progress(0.0, text="Veille en cours…")
    for i, (code, req) in enumerate(requetes):
        try:
            res, etat = rw.chercher_web(req)
        except Exception:
            res, etat = [], "tavily_injoignable"
        resultats[(code, req)] = (res, etat)
        barre.progress((i + 1) / max(len(requetes), 1),
                       text=f"Veille : {req[:50]}…")
        if etat in ("pas_de_cle", "quota_epuise"):
            break  # inutile d'insister, le voyant explique
    barre.empty()
    st.session_state["veille_resultats"] = resultats


def _afficher_resultats():
    resultats = st.session_state.get("veille_resultats") or {}
    if not resultats:
        st.info("Appuie sur « Lancer la veille » : je cherche ce qui bouge "
                "(emplois, concours, arnaques, bourses) dans tes 3 pays. "
                "Relancer le même jour ne coûte aucun crédit.")
        return
    # Regroupe par pays, dans l'ordre CM / SN / CI / ALL
    for code in ("CM", "SN", "CI", "ALL"):
        groupe = {req: v for (c, req), v in resultats.items() if c == code}
        if not groupe:
            continue
        st.markdown(f"### {DRAPEAUX[code]}")
        for req, (res, etat) in groupe.items():
            with st.expander(f"🔍 {req}  ·  {len(res)} résultat(s)"):
                if etat != "ok":
                    st.warning({"pas_de_cle": "Clé Tavily absente.",
                                "quota_epuise": "Quota mensuel épuisé.",
                                "pas_de_wifi": "Pas de connexion.",
                                "tavily_injoignable": "Le service de recherche ne répond pas."
                                }.get(etat, etat))
                    continue
                if not res:
                    st.caption("Rien trouvé pour cette requête aujourd'hui.")
                    continue
                for r in res[:6]:
                    st.markdown(f"**[{r['titre']}]({r['url']})**")
                    extrait = (r.get("extrait") or "").replace("\n", " ").strip()
                    if extrait:
                        st.caption(extrait[:260] + ("…" if len(extrait) > 260 else ""))
                st.caption("💡 Une tendance = une idée de post · un bon site "
                           "d'offres = une future source pour l'usine.")


def _bloc_pages():
    st.markdown("### 📌 Pages à surveiller (à la main)")
    st.caption("Les pages Facebook & réseaux qu'aucun robot ne peut lire "
               "proprement : on les garde ici et on les visite ensemble, "
               "comme pour Fanné Yaya.")
    for nom, url in _lire_pages():
        st.link_button(f"👁 {nom}", url, use_container_width=True)


def _bloc_reglages():
    with st.expander("⚙️ Réglages de la veille"):
        st.caption("Une requête par ligne, au format « CM: … », « SN: … », "
                   "« CI: … » ou « ALL: … ». Avec le cache 24 h, chaque "
                   "requête coûte au plus 1 crédit par jour.")
        req = st.text_area("Requêtes de veille",
                           value=_param("veille_requetes", REQUETES_DEFAUT),
                           height=220, key="veille_req_edit")
        pages = st.text_area("Pages à surveiller (Nom | lien)",
                             value=_param("veille_pages", PAGES_DEFAUT),
                             height=120, key="veille_pages_edit")
        if st.button("💾 Enregistrer les réglages", key="veille_save"):
            _definir_param("veille_requetes", req.strip())
            _definir_param("veille_pages", pages.strip())
            st.success("Réglages enregistrés.")
            st.rerun()


def ecran():
    """Écran admin de veille. True s'il est affiché (bloque la page)."""
    if not st.session_state.get("show_veille"):
        return False

    st.markdown("## 👁 Veille — tendances & sources")
    st.caption("Les yeux de Swimpe sur le web ouvert : ce qui bouge pour les "
               "jeunes de tes 3 pays (emplois, concours, arnaques, bourses). "
               "Nourrit tes posts ET tes futures sources d'offres.")

    _voyant()

    c1, c2 = st.columns([2, 1])
    if c1.button("🔍 Lancer la veille maintenant", type="primary",
                 use_container_width=True, key="veille_go"):
        if rw is None:
            st.error("Brique de recherche indisponible.")
        else:
            _lancer_veille()
            st.rerun()
    if c2.button("🧹 Vider l'affichage", use_container_width=True,
                 key="veille_clear"):
        st.session_state.pop("veille_resultats", None)
        st.rerun()

    _afficher_resultats()
    st.divider()
    _bloc_pages()
    _bloc_reglages()

    st.divider()
    if st.button("← Retour", key="veille_retour"):
        st.session_state.show_veille = False
        st.rerun()
    return True
