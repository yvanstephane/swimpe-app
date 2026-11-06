#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
carte_image.py — Génère l'image « carte » d'un post Facebook Swimpe.
Fond marine (#0A1244, encre Swimpe), texte blanc centré, « swimpe.com » en bas.
C'est la version Swimpe des cartes texte-sur-couleur des pages virales.

Les emojis sont retirés du TEXTE DE L'IMAGE (les polices système ne les
dessinent pas en couleur) mais restent dans le texte du post, copié à côté.

generer_png(carte_texte) -> octets PNG, ou None si Pillow est absent.
"""
import io
import os
import re

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = None

# Couleurs de marque Swimpe (voir swimpe_theme.py)
ENCRE = (10, 18, 68)       # #0A1244
ACCENT = (199, 210, 244)   # #C7D2F4
BLANC = (255, 255, 255)

TAILLE = 1080              # carré, format idéal pour Facebook
MARGE = 110

# Retire emojis / symboles que les polices système ne dessinent pas.
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF\U0000FE00-\U0000FE0F\U0001F1E6-\U0001F1FF\U0000200D]",
    flags=re.UNICODE)

_FONTS_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
]


def _nettoyer(txt):
    t = _EMOJI.sub("", txt or "")
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def _font(taille):
    for p in _FONTS_BOLD:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, taille)
            except Exception:
                pass
    return ImageFont.load_default()


def _largeur(draw, texte, font):
    return draw.textbbox((0, 0), texte, font=font)[2]


def _wrap(draw, texte, font, largeur_max):
    lignes, courante = [], ""
    for mot in texte.split():
        essai = (courante + " " + mot).strip()
        if _largeur(draw, essai, font) <= largeur_max or not courante:
            courante = essai
        else:
            lignes.append(courante)
            courante = mot
    if courante:
        lignes.append(courante)
    return lignes


def generer_png(carte_texte):
    """Octets PNG de la carte, ou None si Pillow n'est pas installé."""
    if Image is None:
        return None
    texte = _nettoyer(carte_texte) or "swimpe.com"
    img = Image.new("RGB", (TAILLE, TAILLE), ENCRE)
    draw = ImageDraw.Draw(img)
    largeur_max = TAILLE - 2 * MARGE

    # Auto-ajustement : on réduit la police jusqu'à ce que le texte tienne.
    font = _font(92)
    lignes = _wrap(draw, texte, font, largeur_max)
    interligne = int(92 * 1.28)
    for taille in range(92, 40, -4):
        font = _font(taille)
        lignes = _wrap(draw, texte, font, largeur_max)
        interligne = int(taille * 1.28)
        if len(lignes) * interligne <= TAILLE - 2 * MARGE - 90:
            break

    hauteur = len(lignes) * interligne
    y = (TAILLE - hauteur) // 2
    for ligne in lignes:
        w = _largeur(draw, ligne, font)
        draw.text(((TAILLE - w) // 2, y), ligne, font=font, fill=BLANC)
        y += interligne

    # Pied de carte : swimpe.com
    pied = _font(48)
    txt = "swimpe.com"
    w = _largeur(draw, txt, pied)
    draw.text(((TAILLE - w) // 2, TAILLE - MARGE - 4), txt, font=pied, fill=ACCENT)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


if __name__ == "__main__":
    data = generer_png("Tu as postulé partout. Silence total. 😮‍💨")
    if data:
        with open("/tmp/carte_test.png", "wb") as f:
            f.write(data)
        print(f"OK — {len(data)} octets écrits dans /tmp/carte_test.png")
    else:
        print("Pillow absent : pas d'image générée.")
