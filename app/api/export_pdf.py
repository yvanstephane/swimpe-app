# -*- coding: utf-8 -*-
# export_pdf.py — generation de PDF Yorbity (fpdf2, pur Python)
# =============================================================================
# Deux produits :
#   pdf_plan(...)    -> le plan personnalise issu du questionnaire
#   pdf_dossier(...) -> un livrable client de l'atelier admin
# Testable sans Streamlit (retourne des bytes). patch_export_pdf
# Dependance : pip install fpdf2
# =============================================================================
from datetime import date

try:
    from fpdf import FPDF
except Exception as e:  # fpdf2 absent : les appelants masquent le bouton
    FPDF = None
    _ERREUR_IMPORT = str(e)

# ── Sanitizer : les polices de base sont latin-1 ; on remplace le reste ──
_MAP = {
    "—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"',
    "…": "...", "•": "-", "·": "-", "→": "->", "←": "<-", "≈": "~",
    "×": "x", "€": "EUR", "⚠": "!", "✓": "v", "✔": "v", "☑": "v",
    "🟢": "[FORTE]", "🟡": "[SELECTIF]", "🔴": "[TRES SELECTIF]",
    "⚪": "[NON DOCUMENTE]", "⛔": "[FERME]", "🎁": "[LANGUE INCLUSE]",
    "🚪": "", "🏆": "", "📊": "", "🔑": "", "🏛️": "", "🏛": "",
    "🛂": "", "💰": "", "🗣️": "", "🗣": "", "📋": "", "🔓": "",
    "💎": "", "📤": "", "📄": "", "🚜": "", "🎯": "", "🇮🇹": "", "🇪🇸": "", "🇵🇹": "", "\u00a0": " ", "\u202f": " ",
}


def _lat(s):
    s = str(s or "")
    for k, v in _MAP.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "ignore").decode("latin-1")


class _PDF(FPDF if FPDF else object):
    """Gabarit Yorbity : en-tete de marque + pied avec disclaimer."""

    def __init__(self, titre_pied=""):
        super().__init__(format="A4")
        self.titre_pied = titre_pied
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(16, 16, 16)

    def header(self):
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(20, 20, 20)
        self.cell(0, 8, "YORBITY", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(110, 110, 110)
        self.cell(0, 4, _lat("Ta trajectoire vers le monde - yorbity"),
                  new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(16, self.get_y() + 2, 194, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(120, 120, 120)
        self.cell(0, 4, _lat(
            "Informations publiques verifiees a la date d'edition - "
            "Yorbity ne garantit ni admission ni visa. " + self.titre_pied),
            align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 7)
        self.cell(0, 4, f"Page {self.page_no()}/{{nb}}", align="C")

    # ── briques ──
    def h1(self, txt):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 7, _lat(txt), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def h2(self, txt):
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 6, _lat(txt), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(225, 225, 225)
        self.line(16, self.get_y() + 1, 120, self.get_y() + 1)
        self.ln(3)

    def p(self, txt, gris=False, retrait=0):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*(110, 110, 110) if gris else (35, 35, 35))
        if retrait:
            self.set_x(16 + retrait)
        self.multi_cell(0, 5, _lat(txt), new_x="LMARGIN", new_y="NEXT")

    def li(self, txt):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(35, 35, 35)
        self.set_x(20)
        self.multi_cell(0, 5, _lat("- " + txt), new_x="LMARGIN", new_y="NEXT")

    def encadre(self, txt):
        self.ln(1)
        self.set_fill_color(245, 245, 245)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 5, _lat(txt), fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)


def disponible():
    return FPDF is not None


def pdf_plan(prof, meilleure, portes, pistes, alerte_visa=None,
             bloc_langue=None, contact=""):
    """Plan personnalise du questionnaire.
    prof : dict (nat, age, niveau_lbl, domaine, objectif_lbl)
    meilleure : str | None
    portes : liste de dicts (nom, capacite, mecanique_detail,
             barriere_langue, canal_officiel, arnaques)
    pistes : liste de dicts (pastille, titre, destination, capacite,
             taux, barriere, lien)
    alerte_visa : dict | None (taux, motifs:str)
    Retourne bytes.
    """
    if FPDF is None:
        raise RuntimeError("fpdf2 absent : pip install fpdf2")
    pdf = _PDF(titre_pied="Edite le " + date.today().strftime("%d/%m/%Y"))
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.h1("Plan personnalise de mobilite")
    pdf.p(f"{prof.get('nat','')} - {prof.get('age','')} ans - "
          f"{prof.get('niveau_lbl','')} - {prof.get('domaine','')} - "
          f"objectif : {prof.get('objectif_lbl','')}", gris=True)
    pdf.ln(2)

    if meilleure:
        pdf.encadre(f"MEILLEURE PISTE : {meilleure.upper()}")

    if portes:
        pdf.h2("Portes reservees a ta nationalite")
        for p in portes:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(25, 25, 25)
            pdf.multi_cell(0, 5.5, _lat(p.get("nom", "")), new_x="LMARGIN", new_y="NEXT")
            for cle, pre in (("capacite", "Capacite : "),
                             ("mecanique_detail", "Mecanique : "),
                             ("barriere_langue", "Langue : "),
                             ("canal_officiel", "CANAL OFFICIEL : ")):
                if p.get(cle):
                    pdf.p(pre + p[cle], retrait=4)
            if p.get("arnaques"):
                pdf.p(p["arnaques"], gris=True, retrait=4)
            pdf.ln(2)

    pdf.h2("Tes pistes, classees par chances reelles")
    for x in pistes:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(25, 25, 25)
        pdf.multi_cell(0, 5.5, _lat(
            f"{x.get('pastille','')} {x.get('titre','')}"
            + (f" - {x['destination']}" if x.get("destination") else "")),
            new_x="LMARGIN", new_y="NEXT")
        for cle, pre in (("capacite", ""), ("taux", "Taux : "),
                         ("barriere", "Cle d'entree : "),
                         ("lien", "Lien officiel : ")):
            if x.get(cle):
                pdf.p(pre + x[cle], retrait=4,
                      gris=(cle in ("capacite",)))
        pdf.ln(1.5)

    if alerte_visa:
        pdf.h2("A savoir sur les visas pour ton passeport")
        pdf.p(f"Refus du visa Schengen COURT sejour pour ta nationalite : "
              f"{alerte_visa.get('taux','?')} % (donnees officielles). "
              "Le visa long sejour ETUDES suit une autre logique et reste "
              "bien plus accessible.")
        if alerte_visa.get("motifs"):
            pdf.p("Motifs de refus dominants (corrigeables dans le "
                  "dossier) : " + alerte_visa["motifs"], gris=True)

    if bloc_langue:
        pdf.h2("La langue n'est pas un mur")
        for ligne in bloc_langue:
            pdf.li(ligne)

    pdf.h2("Regle d'or Yorbity")
    pdf.li("Une vraie bourse ou un vrai programme public ne demande "
           "JAMAIS d'argent pour candidater.")
    pdf.li("Verifie toujours sur le canal officiel indique ci-dessus - "
           "et nulle part ailleurs.")
    if contact:
        pdf.li("Une question ? " + contact)

    return bytes(pdf.output())


def pdf_dossier(client, service, destination, corps, pieces=None,
                contact=""):
    """Livrable client de l'atelier admin (note_interne JAMAIS incluse)."""
    if FPDF is None:
        raise RuntimeError("fpdf2 absent : pip install fpdf2")
    pdf = _PDF(titre_pied="Edite le " + date.today().strftime("%d/%m/%Y"))
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.h1(service)
    pdf.p(f"Prepare pour : {client}" +
          (f" - Destination : {destination}" if destination else ""),
          gris=True)
    pdf.ln(2)
    for bloc in corps:  # liste de (titre, texte) ou (titre, [lignes])
        titre, contenu = bloc
        pdf.h2(titre)
        if isinstance(contenu, (list, tuple)):
            for l in contenu:
                pdf.li(l)
        else:
            pdf.p(contenu)
    if pieces:
        pdf.h2("Pieces jointes / a fournir")
        for l in pieces:
            pdf.li(l)
    if contact:
        pdf.ln(2)
        pdf.p("Contact Yorbity : " + contact, gris=True)
    return bytes(pdf.output())
