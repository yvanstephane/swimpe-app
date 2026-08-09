"""
sources — Registre d'adaptateurs de sources d'offres.

Usage :
    from app.api.sources import registre
    offres = registre.collecter("CA", "metier", sans_permis=True)

Ajouter un pays :
    1. copier _modele.py -> pole_emploi_fr.py
    2. remplir nom, libelle, destinations, types_projet
    3. implementer collecter() et lien_public()
    4. l'ajouter dans registre.charger_defaut()
Rien d'autre a toucher.
"""

from .base import Offre, SourceOffres, TYPES_PROJET  # noqa: F401
from . import registre  # noqa: F401

__all__ = ["Offre", "SourceOffres", "TYPES_PROJET", "registre"]
