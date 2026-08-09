# =============================================================================
# admin_comptes.py — Gestion sécurisée des comptes utilisateurs (admin)
# - Liste des comptes (jamais de hash ni de sel affichés)
# - Réinitialisation : mot de passe TEMPORAIRE aléatoire, montré UNE seule
#   fois, valable 24 h, changement obligatoire à la première connexion
# - Écran de changement forcé pour l'utilisateur concerné
# =============================================================================
import streamlit as st
import auth


def ecran():
    """Écran admin de gestion des comptes. True si affiché."""
    if not st.session_state.get("show_comptes"):
        return False

    st.markdown("## 🔐 Comptes utilisateurs")
    st.caption("Réinitialiser un compte génère un mot de passe temporaire "
               "aléatoire, valable 24 h, à changer obligatoirement à la "
               "première connexion. Il n'est montré qu'une seule fois et "
               "n'est jamais stocké en clair.")

    frais = st.session_state.pop("mdp_temp_frais", None)
    if frais:
        uid, email, temp = frais
        st.success(f"Mot de passe temporaire pour **{email}** — copie-le "
                   "MAINTENANT, il ne sera plus jamais affiché :")
        st.code(temp)
        st.warning("Transmets-le par un canal sûr (de vive voix, appel...). "
                   "Valable 24 h, une seule connexion.")

    for u in auth.lister_utilisateurs():
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
        badge = " 🔑" if u.get("pwd_temp") else ""
        c1.markdown(f"**{u['email']}**{badge}")
        c2.markdown(u.get("nom") or "—")
        c3.markdown(u.get("role") or "etudiant")
        cle_conf = f"conf_reset_{u['id']}"
        if st.session_state.get(cle_conf):
            if c4.button("⚠️ Confirmer", key=f"go_reset_{u['id']}", type="primary"):
                ok, temp = auth.reinitialiser_mdp(u["id"])
                st.session_state[cle_conf] = False
                if ok:
                    st.session_state["mdp_temp_frais"] = (u["id"], u["email"], temp)
                else:
                    st.error(temp)
                st.rerun()
        else:
            if c4.button("Réinitialiser", key=f"ask_reset_{u['id']}"):
                st.session_state[cle_conf] = True
                st.rerun()

    st.divider()
    if st.button("← Retour", key="comptes_retour"):
        st.session_state.show_comptes = False
        st.rerun()
    return True


def ecran_changement_force():
    """Si l'utilisateur connecté a un mot de passe temporaire, impose le
    changement avant tout accès. True si affiché (bloque la page)."""
    u = st.session_state.get("user")
    if not u or not u.get("pwd_temp"):
        return False

    st.markdown("## 🔑 Choisis ton nouveau mot de passe")
    st.info("Ton compte a été réinitialisé. Pour ta sécurité, choisis "
            "maintenant un mot de passe personnel (8 caractères minimum, "
            "au moins un chiffre).")
    with st.form("chg_mdp_force"):
        ancien = st.text_input("Mot de passe temporaire reçu", type="password")
        n1 = st.text_input("Nouveau mot de passe", type="password")
        n2 = st.text_input("Confirme le nouveau mot de passe", type="password")
        ok = st.form_submit_button("Valider")
        if ok:
            if n1 != n2:
                st.error("Les deux mots de passe ne correspondent pas.")
            else:
                reussi, msg = auth.changer_mdp(u["id"], ancien, n1)
                if reussi:
                    st.session_state.user["pwd_temp"] = False
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    return True
