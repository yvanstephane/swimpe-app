# =============================================================================
# bourses_web_ui_v1.py — Lot D : AFFICHAGE de la recherche de bourses
# Assemble les trois couches, dans l'ordre de fiabilité :
#   1) ✓ vérifié Yorbity  (tiroir A : moteur_bourses_v1, filtré origine/destination)
#   2) 🏛️ officiel        (web trié par tri_bourses_v1, domaine de confiance)
#   3) ⚠️ non officiel     (web, ailleurs — montré en dernier, averti)
# Déclenchement : AUTO pour l'admin, sur BOUTON pour les clients (protège le quota).
# Voyant 🟢🟡🔴 pour l'admin. Avertissement anti-arnaque partout. Le tiroir A
# s'affiche toujours, même si le web est indisponible (dégradation propre).
# Aucune de ces briques n'est obligatoire : si un module manque, on n'affiche
# que ce qu'on peut, sans jamais planter l'écran.
# =============================================================================
import streamlit as st

ANTI_ARNAQUE = ("🛡️ **Une vraie bourse ne demande JAMAIS d'argent pour candidater.** "
                "Vérifie toujours sur le site officiel avant d'envoyer quoi que ce soit.")


def _avert_elig(nom_origine):
    """Avertissement d'éligibilité nominatif (ne valide PAS, prévient)."""
    pays = (nom_origine or "").strip()
    if pays:
        return f"⚠️ Vérifie que **{pays}** fait partie des pays éligibles avant de candidater."
    return "⚠️ Vérifie que ton pays fait partie des pays éligibles avant de candidater."


def _imp(nom):
    """Import tolérant : renvoie le module ou None (jamais d'erreur)."""
    try:
        return __import__(nom)
    except Exception:
        return None


def _badge_type(t):
    return {"complète": "🟢 complète", "partielle": "🟡 partielle",
            "excellence": "🔵 excellence"}.get(t, "")


def _voyant_admin():
    rw = _imp("recherche_web_v1")
    if not rw:
        return
    try:
        e = rw.etat_recherche()
    except Exception:
        return
    msg = f"{e.get('voyant', '')} Recherche web — {e.get('message', '')}"
    code = e.get("code", "")
    if code == "ok":
        st.caption(msg)
    elif e.get("voyant") == "🟡":
        st.warning(msg)
    else:
        st.error(msg)


def _rendre_verifiees(code_orig, destination):
    """Couche 1 : tiroir A (bourses vérifiées à la main)."""
    mb = _imp("moteur_bourses_v1")
    if not mb:
        return 0
    try:
        bourses = mb.chercher(code_orig, destination)
    except Exception:
        return 0
    for b in bourses:
        etiq = _badge_type(b.get("type", ""))
        with st.expander(f"✓ {b['nom']}" + (f" · {etiq}" if etiq else ""), expanded=False):
            if b.get("resume"):
                st.write(b["resume"])
            st.caption("✓ Source vérifiée par Yorbity — à confirmer sur le site officiel.")
            if b.get("url"):
                st.markdown(f"[🔗 Site officiel]({b['url']})")
    return len(bourses)


def _rendre_web(code_orig, destination, domaine="", nom_pays="", nom_origine=""):
    """Couches 2 et 3 : recherche web + tri par confiance."""
    rw = _imp("recherche_web_v1")
    tb = _imp("tri_bourses_v1")
    if not rw or not tb:
        st.info("La recherche web n'est pas disponible sur cette installation.")
        return
    # Requête ciblée : le nom du pays entre guillemets force Tavily à prioriser
    # les pages qui parlent VRAIMENT de cette destination (évite le hors-sujet
    # géographique, ex. une page Canada qui remontait pour une recherche France).
    pays = (nom_pays or destination or "").strip()
    bits = ["bourses", "études"]
    if domaine:
        bits.append(domaine)
    if pays:
        bits.append(f'"{pays}"')
    bits += ["étudiants", "internationaux", "africains"]
    requete = " ".join(bits).replace("  ", " ").strip()
    try:
        with st.spinner("Recherche de bourses sur le web…"):
            resultats, etat = rw.chercher_web(requete)
    except Exception:
        resultats, etat = [], "tavily_injoignable"

    if etat != "ok":
        libelle = {
            "pas_de_cle": "La recherche web n'est pas encore configurée.",
            "pas_de_wifi": "Pas de connexion Internet pour l'instant.",
            "quota_epuise": "La recherche web a atteint sa limite ce mois-ci.",
            "tavily_injoignable": "Le service de recherche est momentanément indisponible.",
        }.get(etat, "Recherche web momentanément indisponible.")
        st.info(f"{libelle} Les bourses vérifiées ci-dessus restent valables.")
        return

    try:
        trie = tb.trier(resultats)
    except Exception:
        st.info("Résultats web indisponibles pour l'instant — les bourses vérifiées "
                "ci-dessus restent valables.")
        return

    off = trie.get("officielles", [])
    non_off = trie.get("non_officielles", [])
    if not off and not non_off:
        st.info("Aucune bourse supplémentaire trouvée sur le web pour cette recherche. "
                "Les bourses vérifiées ci-dessus restent ta meilleure piste.")
        return

    if off:
        st.markdown("#### 🏛️ Sources officielles trouvées sur le web")
        for b in off:
            etiq = _badge_type(b.get("type", ""))
            titre = b["titre"] + (f" · {etiq}" if etiq else "") + (" · ⏳ peut-être périmée" if b.get("perimee") else "")
            with st.expander(titre, expanded=False):
                if b.get("resume"):
                    st.write(b["resume"])
                st.caption(b.get("badge", "") + " — à vérifier sur le site officiel.")
                st.caption(_avert_elig(nom_origine))
                st.markdown(f"[🔗 Ouvrir la page]({b['url']})")
    if non_off:
        st.markdown("#### ⚠️ Autres pistes (sources non officielles)")
        st.caption("Ces pages proviennent de sites non officiels : à vérifier avec un soin "
                   "particulier.")
        for b in non_off:
            titre = b["titre"] + (" · ⏳ peut-être périmée" if b.get("perimee") else "")
            with st.expander(titre, expanded=False):
                if b.get("resume"):
                    st.write(b["resume"])
                st.caption(b.get("badge", ""))
                st.caption(_avert_elig(nom_origine))
                st.markdown(f"[🔗 Ouvrir la page]({b['url']})")


def afficher(code_orig, destination, domaine="", nom_pays="", nom_origine="", connecte=False, est_admin=False):
    """Point d'entrée appelé depuis ui.py sous l'écran bourses.
    - admin      → recherche web automatique + voyant (pour tester en direct) ;
    - connecté   → bourses vérifiées + bouton de recherche web ;
    - visiteur   → invitation à créer un compte (respecte le gating existant).
    nom_pays : nom lisible de la destination (ex. « France ») pour cibler la recherche.
    Ne plante jamais."""
    try:
        st.markdown("### 🔎 Bourses trouvées pour toi")
        if est_admin:
            _voyant_admin()
        # Visiteur non connecté : on respecte le gating d'inscription de l'app.
        if not connecte and not est_admin:
            st.markdown(ANTI_ARNAQUE)
            st.caption("Crée un compte gratuit (bouton ci-dessus) pour voir toutes les "
                       "bourses en détail et lancer une recherche en ligne.")
            return
        n = _rendre_verifiees(code_orig, destination)
        st.markdown(ANTI_ARNAQUE)
        st.divider()
        if est_admin:
            # Admin : recherche web automatique (pour tester en direct).
            _rendre_web(code_orig, destination, domaine, nom_pays, nom_origine)
        else:
            # Client connecté : sur bouton, pour protéger le quota.
            if st.button("🔎 Chercher plus de bourses sur le web",
                         key=f"web_bourses_{code_orig}_{destination}"):
                _rendre_web(code_orig, destination, domaine, nom_pays, nom_origine)
            else:
                st.caption("Clique pour chercher d'autres bourses en ligne (sources "
                           "officielles et autres pistes, à vérifier).")
    except Exception as e:  # filet ultime : ne casse jamais l'écran
        try:
            st.caption(f"(Section bourses web indisponible : {e})")
        except Exception:
            pass


# _lot_bourses_req_v1 : requête web ciblée par nom de pays
# _lot_bourses_elig_v1 : avertissement d'éligibilité nominatif sur chaque résultat web


# _lot_bourses_d_v1
