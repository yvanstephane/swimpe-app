"""
devises.py — Affiche les prix dans la DEVISE DU PAYS DE DESTINATION.

Regle produit : "Commence ton projet a partir de 15 €" devient
    Canada       ->  a partir de 24 $ CA
    Etats-Unis   ->  a partir de 17 $ US
    Allemagne    ->  a partir de 15 €
    Cameroun     ->  a partir de 9 900 FCFA
Le prix de reference reste stocke en EUR ; seule la PRESENTATION change.

Taux : figes dans TAUX (base 1 EUR), dates du 2026-07. Ils servent a
l'affichage marketing, pas a la facturation — l'arrondi est volontairement
"joli" (vers le haut, jamais en dessous du prix EUR reel).
L'admin peut surcharger un taux sans toucher au code, via les parametres
existants d'offres_sync :
    definir_param("taux_eur:CAD", "1.58")
Cas particulier : XAF/XOF sont arrimes a l'euro (655,957) — taux EXACT.

Usage :
    import devises
    devises.prix(15, "CA")        -> "24 $ CA"
    devises.prix(15, "DE")        -> "15 €"
    devises.note(15, "CA")        -> "≈ 15 €, taux indicatif 2026-07"
"""

from __future__ import annotations

import math

DATE_TAUX = "2026-07"

# code destination -> (code devise, libelle affiche, taux pour 1 EUR)
# Libelles en convention francophone : montant PUIS symbole.
PAYS_DEVISE: dict[str, tuple[str, str, float]] = {
    # Zone euro
    "FR": ("EUR", "€", 1.0), "DE": ("EUR", "€", 1.0), "BE": ("EUR", "€", 1.0),
    "ES": ("EUR", "€", 1.0), "IT": ("EUR", "€", 1.0), "NL": ("EUR", "€", 1.0),
    "AT": ("EUR", "€", 1.0), "PT": ("EUR", "€", 1.0), "IE": ("EUR", "€", 1.0),
    # Amerique du Nord
    "CA": ("CAD", "$ CA", 1.56),
    "US": ("USD", "$ US", 1.09),
    "MX": ("MXN", "$ MX", 20.9),
    # Europe hors zone euro
    "GB": ("GBP", "£", 0.85),
    "CH": ("CHF", "CHF", 0.94),
    "PL": ("PLN", "zł", 4.27),
    "TR": ("TRY", "₺", 39.5),        # volatile : surcharge admin conseillee
    # Oceanie / Asie
    "AU": ("AUD", "$ AU", 1.66),
    "NZ": ("NZD", "$ NZ", 1.80),
    "JP": ("JPY", "¥", 167.0),
    "CN": ("CNY", "¥", 7.8),
    "SG": ("SGD", "$ SG", 1.45),
    "IN": ("INR", "₹", 92.0),
    # Afrique
    "ZA": ("ZAR", "R", 19.6),
    "MA": ("MAD", "DH", 10.8),
    "DZ": ("DZD", "DA", 148.0),      # dinar algerien — indicatif, volatil
    "TN": ("TND", "DT", 3.35),
    "GN": ("GNF", "FG", 9500.0),     # franc guineen — indicatif, volatil
    "CD": ("CDF", "FC", 2900.0),     # franc congolais — tres volatil
    "NG": ("NGN", "₦", 1650.0),
    "GH": ("GHS", "GH₵", 16.0),
    "KE": ("KES", "KSh", 140.0),
    "CM": ("XAF", "FCFA", 655.957),   # parite fixe euro — exact
    "SN": ("XOF", "FCFA", 655.957),
    "CI": ("XOF", "FCFA", 655.957),
    "GA": ("XAF", "FCFA", 655.957),
    "BR": ("BRL", "R$", 6.15),
}

_DEFAUT = ("EUR", "€", 1.0)

# Devises sans decimales usuelles / gros montants : arrondi plus large.
_SANS_CENTIMES = {"JPY", "XAF", "XOF", "INR", "TRY", "MXN", "ZAR", "CNY"}


def _param(cle: str) -> str | None:
    """Surcharge admin via offres_sync.param, si disponible."""
    try:
        import offres_sync
        v = offres_sync.param(cle, "")
        return v or None
    except Exception:
        return None


def devise_de(dest_code: str | None) -> tuple[str, str, float]:
    code, symbole, taux = PAYS_DEVISE.get((dest_code or "").upper(), _DEFAUT)
    surchage = _param(f"taux_eur:{code}")
    if surchage:
        try:
            taux = float(str(surchage).replace(",", "."))
        except ValueError:
            pass
    return code, symbole, taux


def _arrondi_joli(v: float, code: str) -> int:
    """
    Arrondi marketing, TOUJOURS vers le haut (on ne vend jamais sous le
    prix EUR de reference) :
      < 50     -> entier superieur          (23.4 -> 24)
      < 1000   -> multiple de 5 superieur   (161  -> 165)
      >= 1000  -> multiple de 50 superieur  (9839 -> 9850)
    Devises "gros chiffres" (JPY, FCFA...) : palier minimal 50.
    """
    if v < 50 and code not in _SANS_CENTIMES:
        return math.ceil(v)
    if v < 1000:
        pas = 50 if code in _SANS_CENTIMES and v >= 100 else 5
        return math.ceil(v / pas) * pas
    return math.ceil(v / 50) * 50


def _format_fr(n: int) -> str:
    """12345 -> '12 345' (espace insecable fine francophone)."""
    return f"{n:,}".replace(",", "\u202f")


def convertir(montant_eur: float, dest_code: str | None) -> int:
    code, _, taux = devise_de(dest_code)
    return _arrondi_joli(montant_eur * taux, code)


def prix(montant_eur: float, dest_code: str | None) -> str:
    """15, 'CA' -> '24 $ CA'   |   15, 'DE' -> '15 €'"""
    code, symbole, _ = devise_de(dest_code)
    return f"{_format_fr(convertir(montant_eur, dest_code))}\u00a0{symbole}"


def _tr_auto():
    """tr par defaut (patch_fixpack2) : traduit via le cache Ollama dans la
    langue de session. Evite que « taux indicatif » reste en francais quand
    l'appelant n'a pas transmis de tr."""
    try:
        import streamlit as st
        lg = st.session_state.get("lang", "fr")
        if lg == "fr":
            return lambda s: s
        import traduction
        return lambda s: traduction.traduire(s, lg)
    except Exception:
        return lambda s: s


def note(montant_eur: float, dest_code: str | None, tr=None) -> str:
    """Mention de transparence a mettre en petit sous le prix converti.
    tr=None -> traduction automatique dans la langue de session."""
    code, _, _ = devise_de(dest_code)
    if code == "EUR":
        return ""
    if tr is None:
        tr = _tr_auto()
    return (f"≈ {_format_fr(math.ceil(montant_eur))}\u00a0€ — "
            + tr("taux indicatif") + f" {tr(DATE_TAUX)}")


if __name__ == "__main__":
    for m, d in [(15, "CA"), (15, "US"), (15, "DE"), (15, "CM"), (15, "JP"),
                 (15, "GB"), (49, "CA"), (149, "CM"), (15, None)]:
        print(f"{m:>4} EUR -> {d or '??'}: {prix(m, d):>14}   {note(m, d)}")
