#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tableau_bord.py — Espace client enrichi (Swimpe)"""
import sqlite3
try:
    import sqlite3 as _sqlite3
    from importlib import import_module as _imp
    _dbc = _imp("db")
    if getattr(_dbc, "MODE_PG", False):
        _sqlite3.connect = lambda *a, **k: _dbc.connect(*a, **k)
        _sqlite3.Row = _dbc.Row
except Exception:
    pass
import streamlit as st

DB = "data/mobilite.db"

def _lg():
    return st.session_state.get("lang", "fr")

def _t(fr, pt=None):
    if _lg() == "pt" and pt:
        return pt
    return fr

def ecran(user):
    if not st.session_state.get("show_espace"):
        return False
    import espace, auth
    try:
        import file_plans
    except Exception:
        file_plans = None
    try:
        import dossiers
    except Exception:
        dossiers = None

    uid = user["id"]
    nom = (user["nom"] if "nom" in user.keys() else None) or (user["email"] if "email" in user.keys() else "")
    st.markdown(f"## {_t('Mon espace', 'O meu espaco')} — {nom}")

    projets = espace.mes_projets(uid)
    demandes = file_plans.mes_demandes(uid) if file_plans else []
    prets = [d for d in demandes if d["statut"] == "pret"]
    en_cours = [d for d in demandes if d["statut"] in ("en_attente", "en_cours")]
    dmcs = dossiers.liste_user(uid) if dossiers else []

    premium = False
    try:
        premium = auth.est_premium(user)
    except Exception:
        pass

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(_t("Projets", "Projetos"), len(projets))
    c2.metric(_t("Plans prets", "Planos prontos"), len(prets))
    c3.metric(_t("En preparation", "Em preparacao"), len(en_cours))
    c4.metric(_t("Demarches", "Tramites"), len(dmcs))

    if premium:
        st.success("⭐ " + _t("Premium actif", "Premium ativo"))
    st.divider()

    st.markdown("### " + _t("📁 Mes projets", "📁 Meus projetos"))
    if not projets:
        st.info(_t("Vous n'avez pas encore de projet. Lancez le questionnaire pour en creer un.",
                   "Ainda nao tem projetos. Inicie o questionario para criar um."))
    else:
        dem_par_couple = {}
        for d in demandes:
            dem_par_couple.setdefault((d["origine"], d["destination"]), d)
        for p in projets:
            with st.container(border=True):
                st.markdown(f"**{p['origine']} → {p['destination']}** · {p['type']} · {p['niveau']}")
                st.caption(_t("cree le", "criado a") + f" {p['date']}")
                dem = dem_par_couple.get((p["origine"], p["destination"]))
                if file_plans is None:
                    st.caption("—")
                elif dem is None:
                    if st.button("🎯 " + _t("Demander mon plan personnalise",
                                            "Pedir o meu plano personalizado"),
                                 key=f"askplan_{p['id']}", use_container_width=True):
                        file_plans.creer_demande(uid, p["origine"], p["destination"],
                                                 offre=(p["domaine"] if "domaine" in p.keys() else "") or "")
                        st.rerun()
                elif dem["statut"] in ("en_attente", "en_cours"):
                    st.info("⏳ " + _t("Votre plan personnalise est en preparation…",
                                       "O seu plano esta em preparacao…"))
                elif dem["statut"] == "pret":
                    st.success("✅ " + _t("Votre plan est pret !", "O seu plano esta pronto!"))
                    with st.expander("📄 " + _t("Voir le plan", "Ver o plano")):
                        st.markdown(dem["resultat"] or "")
    st.divider()

    if prets:
        st.markdown("### " + _t("📄 Mes plans recus", "📄 Meus planos recebidos"))
        for d in prets:
            with st.container(border=True):
                st.markdown(f"**{d['origine']} → {d['destination']}** · "
                            + _t("livre le", "entregue a") + f" {(d["traite_le"] if "traite_le" in d.keys() else "")}")
                st.download_button("⬇️ " + _t("Telecharger (texte)", "Descarregar (texto)"),
                    data=(d["resultat"] or "").encode("utf-8"),
                    file_name=f"plan_{d['origine']}_{d['destination']}.md", key=f"dl_{d['id']}")
        st.divider()

    if dossiers is not None:
        st.markdown("### " + _t("📌 Suivi de mes demarches", "📌 Acompanhamento dos meus tramites"))
        if not dmcs:
            st.caption(_t("Aucune demarche deleguee pour le moment.",
                          "Nenhum tramite delegado de momento."))
        else:
            for d in dmcs:
                pct = dossiers.STATUT_PCT.get(d["statut"], 5)
                label = dossiers.statut_label(d["statut"])
                with st.container(border=True):
                    st.markdown(f"**{d['service']}** → {d['destination']}")
                    st.progress(pct / 100, text=f"{label} · {pct} %")
                    if d["note_client"]:
                        st.info("💬 " + d["note_client"])
        st.divider()

    st.markdown("### " + _t("Actions", "Acoes"))
    a1, a2 = st.columns(2)
    if a1.button("🔍 " + _t("Nouveau projet (questionnaire)", "Novo projeto (questionario)"),
                 use_container_width=True):
        st.session_state.show_espace = False
        st.rerun()
    if not premium:
        if a2.button("⭐ " + _t("Passer Premium", "Passar a Premium"), use_container_width=True):
            st.session_state.show_espace = False
            st.session_state.show_premium = True
            st.rerun()

    st.divider()
    if st.button("← " + _t("Retour", "Voltar")):
        st.session_state.show_espace = False
        st.rerun()
    return True
