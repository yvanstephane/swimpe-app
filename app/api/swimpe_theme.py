#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
swimpe_theme.py — Habillage Swimpe de l'application (harmonisation site <-> app)
Reprend les variables EXACTES du site vitrine swimpe.com :
  encre #0A1244 · bleu #2653F1 · gris #F4F6FB · filet #E3E7F4
  vert #116B45/#E7F4EE · ambre #8A6116/#FFF3D6 · degrade teaser #101B5C->#1B2C86
Trois briques : injecter() / entete() / bande_stats(items).
Chaque brique echoue en silence : l'app ne casse jamais pour une question de style.
"""
import streamlit as st

ENCRE = "#0A1244"; BLEU = "#2653F1"; BLEU2 = "#1B41C9"; GRIS = "#F4F6FB"
FILET = "#E3E7F4"; MUET = "#5A6486"


def injecter():
    """CSS global + barre utilitaire marine. A appeler juste apres set_page_config."""
    try:
        st.markdown("""
<style>
:root{--sw-encre:#0A1244;--sw-bleu:#2653F1;--sw-bleu2:#1B41C9;--sw-gris:#F4F6FB;
      --sw-filet:#E3E7F4;--sw-muet:#5A6486;--sw-vert:#116B45;--sw-vert-p:#E7F4EE;
      --sw-ambre:#8A6116;--sw-ambre-p:#FFF3D6;}
.stButton>button{border-radius:6px;font-weight:600}
.stButton>button[kind="primary"]{background:var(--sw-bleu);border-color:var(--sw-bleu)}
.stButton>button[kind="primary"]:hover{background:var(--sw-bleu2);border-color:var(--sw-bleu2)}
div[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--sw-filet)!important;border-radius:6px}
div[data-testid="stAlert"]{border-radius:6px}
section[data-testid="stSidebar"]{background:var(--sw-gris)}
section[data-testid="stSidebar"] .stButton>button{background:#fff;border:1px solid var(--sw-filet)}
.sw-util{background:var(--sw-encre);color:#C7D2F4;font-size:12.5px;
  border-radius:6px;padding:8px 16px;margin:-8px 0 14px 0;
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.sw-util a{color:#C7D2F4;text-decoration:none}
.sw-util a:hover{color:#fff;text-decoration:underline}
.sw-util .ici{color:#fff;font-weight:700;border-bottom:2px solid rgba(255,255,255,.45)}
.sw-stats{background:var(--sw-encre);color:#fff;border-radius:6px;
  display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));margin:4px 0 10px}
.sw-stat{padding:16px 16px;border-left:1px solid rgba(255,255,255,.14)}
.sw-stat:first-child{border-left:none}
.sw-stat .n{display:block;font-size:30px;font-weight:800;letter-spacing:-.02em;line-height:1.1}
.sw-stat .l{font-size:12.5px;color:#B9C6EE;margin-top:3px;display:block}
.sw-marque{display:flex;align-items:center;gap:12px;justify-content:center;margin:2px 0 0}
.sw-logo{width:44px;height:44px;background:var(--sw-bleu);color:#fff;border-radius:8px;
  display:inline-grid;place-items:center;font-weight:800;font-size:24px}
.sw-nom{font-size:2.35rem;font-weight:800;letter-spacing:-.015em;color:var(--sw-encre)}
.sw-baseline{text-align:center;color:var(--sw-muet);margin:2px 0 6px}
</style>""", unsafe_allow_html=True)
        st.markdown(
            '<div class="sw-util">'
            '<span><a href="https://swimpe.com" target="_blank">swimpe.com</a>'
            '&nbsp;&nbsp;·&nbsp;&nbsp;<span class="ici">Application · Espace membre</span></span>'
            '<span><a href="https://swimpe.com/verifier.html" target="_blank">Verifier une offre</a></span>'
            '</div>', unsafe_allow_html=True)
    except Exception:
        pass


def entete(nom="Swimpe", baseline="Votre trajectoire vers le monde"):
    """Logo S + nom + baseline. Remplace l'ancien Yorbity."""
    try:
        st.markdown(
            f'<div class="sw-marque"><span class="sw-logo">S</span>'
            f'<span class="sw-nom">{nom}</span></div>'
            f'<p class="sw-baseline">{baseline}</p>', unsafe_allow_html=True)
        return True
    except Exception:
        return False


def bande_stats(items):
    """Compteurs facon bande marine du site. items = liste de (libelle, valeur)."""
    try:
        cases = "".join(
            f'<div class="sw-stat"><span class="n">{v}</span>'
            f'<span class="l">{lib}</span></div>' for lib, v in items)
        st.markdown(f'<div class="sw-stats">{cases}</div>', unsafe_allow_html=True)
        return True
    except Exception:
        return False
