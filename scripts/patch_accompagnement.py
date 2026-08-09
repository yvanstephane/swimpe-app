#!/usr/bin/env python3
"""
patch_accompagnement.py — Trois demandes, quatre retouches chirurgicales.

CE QUE CA CHANGE
  1. PAGE DEDIEE  ?page=accompagnement&dest=CA&lg=fr&orig=Cameroun
     Un nouvel onglet = une NOUVELLE session Streamlit : le contexte passe
     donc par l'URL. La page rend le theme du pays, l'en-tete
     t('accompagne'), les services de la destination (SVC filtres par
     services_cfg) et le formulaire lead — puis st.stop().
  2. HERO  A cote du prix « Commence ton projet a partir de … », un lien
     « 🤝 On t'accompagne jusqu'en {pays} → » qui ouvre la page dediee
     dans un nouvel onglet.
  3. DEVISE  Le prix du hero passe en DEVISE DE DESTINATION via devises.py
     (Canada -> $ CA, Cameroun -> FCFA a parite exacte), avec « ≈ X € ».
     Repli automatique sur devises_cfg si devises.py est absent.
     Le selecteur « Devise » de la sidebar n'est PAS touche.
  4. BAS DE PAGE  Le bloc de services (ui.py:1024-1037) est remplace par le
     meme lien. La boucle est conservee sous forme compacte car le
     FORMULAIRE juste en dessous depend de `noms_services`.

ANCRES (toutes vues dans regions.txt, uniques dans ui.py) :
  A. `if "svc" not in st.session_state: st.session_state.svc = None`
  B. `    # ---- Bandeau héro marketing`
  C. `{t("start_from", LG)} {devises_cfg.prix_affiche(prix_min_fcfa / 655.96, TAUX, avec_equivalent=True)}`
  D. de `    # ---- Bloc accompagnement` a `    st.markdown("#### " + t("form_titre", LG))`

Idempotent. Sauvegarde .bak. Verifie la syntaxe, restaure si casse.
Usage : python scripts/patch_accompagnement.py [--dry]
"""
from __future__ import annotations

import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
P = RACINE / "app" / "api" / "ui.py"

MARQUE = "patch_accompagnement"

# --------------------------------------------------------------------------- #
# A. Routeur de la page dediee — insere apres l'init de session_state.svc
# --------------------------------------------------------------------------- #
ANCRE_A = 'if "svc" not in st.session_state: st.session_state.svc = None'

BLOC_ROUTEUR = '''

# --- Page dediee « Accompagnement » (patch_accompagnement) ------------------
# Un NOUVEL ONGLET = une nouvelle session : le contexte arrive par l'URL.
#   ?page=accompagnement&dest=CA&lg=fr&orig=Cameroun
_qp = st.query_params
if _qp.get("page") == "accompagnement":
    import urllib.parse as _up
    _tr = globals().get("tr", lambda s: s)
    _lg_qp = _qp.get("lg") or ""
    if _lg_qp in LANGUES and _lg_qp != LG:
        st.session_state.lang = _lg_qp
        LG = _lg_qp
    _dst = (_qp.get("dest") or "").upper()
    _d = D.get(_dst)
    if not _d:
        st.warning("🌍 " + _tr("Choisis d'abord un pays de destination sur la page principale."))
        st.link_button("← Yorbity", "/")
        st.stop()

    try:
        import theme_pays
        theme_pays.appliquer(_dst, "etudes", _tr)
    except Exception:
        pass

    st.markdown(f"## {t('accompagne', LG)} {nom_pays(_d['nom'], LG)}")
    st.write(t("accompagne_desc", LG))

    _svc_dest = services_cfg.effectifs(_dst, _d["services"], list(SVC.keys())) \\
        or _d["services"]
    _noms = []
    for _s in _svc_dest:
        _n, _de, _ = SVC[_s]
        _n, _de = _tr(_n), _tr(_de)
        _noms.append(_n)
        with st.expander(_n):
            st.write(_de)

    st.markdown("#### " + t("form_titre", LG))
    with st.form("lead_accompagnement"):
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
    st.stop()
# -----------------------------------------------------------------------------
'''

# --------------------------------------------------------------------------- #
# B. Avant le hero : calcul du prix destination + URL de la page dediee
# --------------------------------------------------------------------------- #
ANCRE_B = "    # ---- Bandeau héro marketing"

BLOC_PRE_HERO = '''    # ---- Prix en DEVISE DE DESTINATION + lien accompagnement (patch_accompagnement)
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
                + "&orig=" + _up.quote(origine or ""))
'''

# --------------------------------------------------------------------------- #
# C. Dans le hero : prix remplace + lien a cote
# --------------------------------------------------------------------------- #
ANCRE_C = ('{t("start_from", LG)} {devises_cfg.prix_affiche('
           'prix_min_fcfa / 655.96, TAUX, avec_equivalent=True)}</span>')

REMPLACE_C = (
    '{t("start_from", LG)} {_prix_banniere}</span>\n'
    "  <a class='prix' href='{_url_acc}' target='_blank' "
    "style='text-decoration:none; margin-left:.6rem;'>"
    "🤝 {t('accompagne', LG)} {nom_pays(d['nom'], LG)} →</a>"
)

# --------------------------------------------------------------------------- #
# D. Bloc services du bas -> lien (en gardant noms_services pour le formulaire)
# --------------------------------------------------------------------------- #
ANCRE_D_DEBUT = "    # ---- Bloc accompagnement (services filtrés par destination, SANS prix)"
ANCRE_D_FIN = '    st.markdown("#### " + t("form_titre", LG))'

BLOC_D = '''    # ---- Accompagnement : deplace sur sa page dediee (patch_accompagnement)
    st.markdown("---")
    st.link_button("🤝 " + t("accompagne", LG) + " " + nom_pays(d["nom"], LG) + " →",
                   _url_acc, use_container_width=True)
    # Le formulaire ci-dessous a besoin de la liste des services :
    noms_services = [tr(SVC[s][0]) for s in services_dest]

'''


# --------------------------------------------------------------------------- #
def main() -> None:
    if not P.exists():
        print("ui.py introuvable")
        sys.exit(1)
    src = P.read_text(encoding="utf-8")

    if MARQUE in src:
        print("= ui.py : deja patche")
        return

    manquantes = [nom for nom, a in
                  [("A", ANCRE_A), ("B", ANCRE_B), ("C", ANCRE_C),
                   ("D-debut", ANCRE_D_DEBUT), ("D-fin", ANCRE_D_FIN)]
                  if a not in src]
    if manquantes:
        print(f"? ancres introuvables : {manquantes} — RIEN ECRIT.")
        print("  Envoie : grep -n 'Bloc accompagnement\\|Bandeau héro\\|start_from' app/api/ui.py")
        sys.exit(2)
    for nom, a in [("A", ANCRE_A), ("C", ANCRE_C),
                   ("D-debut", ANCRE_D_DEBUT), ("D-fin", ANCRE_D_FIN)]:
        if src.count(a) != 1:
            print(f"? ancre {nom} presente {src.count(a)} fois — RIEN ECRIT.")
            sys.exit(2)

    n = 0
    # A — routeur
    src = src.replace(ANCRE_A, ANCRE_A + BLOC_ROUTEUR, 1); n += 1
    # B — pre-hero
    src = src.replace(ANCRE_B, BLOC_PRE_HERO + ANCRE_B, 1); n += 1
    # C — hero
    src = src.replace(ANCRE_C, REMPLACE_C, 1); n += 1
    # D — section du bas -> lien
    i_deb = src.index(ANCRE_D_DEBUT)
    # l'ancre de fin existe aussi dans le routeur insere plus haut :
    # on cherche a partir du debut du bloc D.
    i_fin = src.index(ANCRE_D_FIN, i_deb)
    src = src[:i_deb] + BLOC_D + src[i_fin:]; n += 1

    if DRY:
        print(f"~ ui.py : {n} retouches [DRY-RUN, rien ecrit]")
        return

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"x syntaxe cassee ligne {e.lineno} — RIEN ECRIT")
        sys.exit(1)

    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    P.write_text(src, encoding="utf-8")
    print(f"v ui.py : {n} retouches, syntaxe OK ({bak.name})")
    print("Relance : yorbity")
    print("Test : choisis un pays, clique le lien 🤝 du bandeau -> nouvel onglet.")


if __name__ == "__main__":
    main()
