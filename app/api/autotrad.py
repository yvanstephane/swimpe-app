# =============================================================================
# autotrad.py — v2.1 — Traduction AUTOMATIQUE GLOBALE de l'interface Yorbity
# Intercepte les méthodes d'affichage au niveau de DeltaGenerator : couvre la
# page, la sidebar, les COLONNES (c1.selectbox...), les expanders, les forms.
# Dès que la langue ≠ fr, tout label/texte passe par traduire() (cache).
# Garde-fous : pas de HTML/CSS, pas de liens, pas de double traduction.
# =============================================================================
import streamlit as st
try:
    from traduction import traduire
except Exception:
    def traduire(x, lang):
        return x

_HTML = ("<style", "<script", "<div", "<span", "<img", "<a ", "<br", "<p>",
         "<h1", "<h2", "<h3", "<h4", "<table", "<ul", "<li", "</")


class _Deja(str):
    """Marqueur : chaîne déjà traduite (évite la double traduction write→markdown)."""
    pass

_CIBLES = ("markdown", "write", "title", "header", "subheader", "caption",
           "text", "success", "info", "warning", "error", "button",
           "checkbox", "radio", "selectbox", "multiselect", "text_input",
           "text_area", "number_input", "expander", "form_submit_button",
           "link_button", "download_button", "metric", "toggle", "slider",
           "date_input", "time_input", "color_picker", "file_uploader",
           "popover", "pills", "segmented_control")


def _lang():
    try:
        return st.session_state.get("lang", "fr")
    except Exception:
        return "fr"


def _translatable(s):
    if not isinstance(s, str):
        return False
    s2 = s.strip()
    if len(s2) < 2 or s2[0] == "<":
        return False
    if not any(c.isalpha() for c in s2):
        return False
    low = s2.lower()
    if any(h in low for h in _HTML):
        return False
    if "](" in s2 or "http" in low or "```" in s2:
        return False
    return True


def _maybe(s):
    if isinstance(s, _Deja):
        return s
    if _lang() == "fr" or not _translatable(s):
        return s
    try:
        return _Deja(traduire(s, _lang()))
    except Exception:
        return s


def _wrap(orig):
    def wrapper(self, *args, **kwargs):
        if kwargs.get("unsafe_allow_html"):
            return orig(self, *args, **kwargs)
        if args and isinstance(args[0], str):
            args = (_maybe(args[0]),) + args[1:]
        elif "label" in kwargs and isinstance(kwargs["label"], str):
            kwargs = dict(kwargs, label=_maybe(kwargs["label"]))
        elif "body" in kwargs and isinstance(kwargs["body"], str):
            kwargs = dict(kwargs, body=_maybe(kwargs["body"]))
        return orig(self, *args, **kwargs)
    wrapper._yorbity_wrapped = True
    try:
        wrapper.__name__ = orig.__name__
        wrapper.__doc__ = orig.__doc__
    except Exception:
        pass
    return wrapper


def _patch_class(cls):
    if cls is None:
        return
    for name in _CIBLES:
        orig = getattr(cls, name, None)
        if orig is None or getattr(orig, "_yorbity_wrapped", False):
            continue
        try:
            setattr(cls, name, _wrap(orig))
        except Exception:
            pass


# 1) classe DeltaGenerator : couvre st.*, sidebar, colonnes, expanders, forms
try:
    from streamlit.delta_generator import DeltaGenerator
    _patch_class(DeltaGenerator)
except Exception:
    pass

# 2) filet de sécurité : fonctions module-level
for _n in _CIBLES:
    _f = getattr(st, _n, None)
    if _f is None or getattr(_f, "_yorbity_wrapped", False):
        continue
    def _mk(f):
        def w(*a, **k):
            if k.get("unsafe_allow_html"):
                return f(*a, **k)
            if a and isinstance(a[0], str):
                a = (_maybe(a[0]),) + a[1:]
            elif "label" in k and isinstance(k["label"], str):
                k = dict(k, label=_maybe(k["label"]))
            return f(*a, **k)
        w._yorbity_wrapped = True
        return w
    try:
        setattr(st, _n, _mk(_f))
    except Exception:
        pass
