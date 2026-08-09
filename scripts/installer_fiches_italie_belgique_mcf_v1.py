#!/usr/bin/env python3
"""
installer_fiches_italie_belgique_mcf_v1.py
Patch idempotent sur app/api/ui.py :
  - Enrichit D["BE"] : ARES (détails complets + anti-arnaque) + MCF
  - Enrichit D["IT"] : ajoute le Decreto Flussi (Métier/Saisonnier) en section dédiée
Règles projet : .bak horodaté · ast.parse · ancres EXACTES · restauration si casse.
Usage : python3 installer_fiches_italie_belgique_mcf_v1.py
"""

import ast, shutil, sys, textwrap
from datetime import datetime
from pathlib import Path

CIBLE = Path.home() / "mobilite-ia/app/api/ui.py"

# ── ANCRES EXACTES extraites du vrai fichier ─────────────────────────────────

ANCRE_BE = 'D["BE"] = dict(nom="Belgique", flag="🇧🇪",'
ANCRE_IT = 'D["IT"] = dict(nom="Italie", flag="🇮🇹",'

# ── REMPLACEMENT BE ──────────────────────────────────────────────────────────
# On remplace uniquement le bloc bourses=[ de BE pour y ajouter ARES enrichi + MCF.
# Ancre de fin = la 1re ligne du bloc D["IT"] qui suit immédiatement.

ANCIEN_BE = '''\
D["BE"] = dict(nom="Belgique", flag="🇧🇪",
 resume="Le choix naturel des francophones : frais modérés (835–4 175 €/an), universités réputées.",
 ressources="≈650 €/mois à justifier",
 travail="20 h/semaine", post="Séjour de recherche d'emploi possible",
 portail="https://www.studyinbelgium.be",
 services=["ORIENT","ADMIS","DOSSIER","FONDS","VISA","BOURSE","TRAD","PACK"],
 etapes=[
  ("Faire reconnaître ton diplôme (équivalence FWB)", "Dossier à déposer TÔT : 3–4 mois de délai, indispensable pour s'inscrire.", "https://www.equivalences.cfwb.be", "TRAD"),
  ("S'inscrire à l'université", "Candidatures juin–septembre pour la rentrée d'octobre.", None, "ADMIS"),
  ("Visa D étudiant", "Admission + équivalence + fonds + assurance.", None, "VISA"),
 ],
 bourses=[("ARES", "Bourse complète de la coopération belge (pays partenaires).", "https://www.ares-ac.be")])'''

NOUVEAU_BE = '''\
D["BE"] = dict(nom="Belgique", flag="🇧🇪",
 resume="Le choix naturel des francophones : frais modérés (835–4 175 €/an), universités réputées. "
        "Deux bourses entièrement financées s'adressent directement aux Africains : ARES (Belgique, "
        "Bac+3/Bac+5, 20 pays partenaires) et MasterCard Foundation Scholars (mondial, jusqu'à 35 ans).",
 ressources="≈650 €/mois à justifier",
 travail="20 h/semaine", post="Séjour de recherche d'emploi possible",
 portail="https://www.studyinbelgium.be",
 services=["ORIENT","ADMIS","DOSSIER","FONDS","VISA","BOURSE","TRAD","PACK"],
 etapes=[
  ("Faire reconnaître ton diplôme (équivalence FWB)", "Dossier à déposer TÔT : 3–4 mois de délai, indispensable pour s'inscrire.", "https://www.equivalences.cfwb.be", "TRAD"),
  ("S'inscrire à l'université", "Candidatures juin–septembre pour la rentrée d'octobre.", None, "ADMIS"),
  ("Visa D étudiant", "Admission + équivalence + fonds + assurance.", None, "VISA"),
 ],
 bourses=[
  # ── ARES ──────────────────────────────────────────────────────────────────
  ("🇧🇪 Bourses ARES — coopération belge",
   "200 bourses entièrement financées/an : Bachelier ou Master de spécialisation (1 an) "
   "ou Formation continue (2–6 mois) dans les universités FWB (ULB, UCLouvain, ULiège, "
   "UNamur, HE Vinci…). Couverture : inscription + 1 150 €/mois × 12 + billet A/R + visa "
   "+ assurance. "
   "Conditions : résider ET travailler dans l'un des 31 pays éligibles · Bac+3 minimum · "
   "≥ 2 ans d'expérience professionnelle après le diplôme · diplôme ≤ 20 ans · "
   "1 seule candidature · GRATUIT (fraude → bourses-cooperation@ares-ac.be). "
   "Pays africains éligibles (20/31) : Afrique du Sud, Bénin, Burkina Faso, Burundi, "
   "Cameroun, Éthiopie, Guinée, Kenya, Madagascar, Mali, Maroc, Mozambique, Niger, "
   "Ouganda, RDC, Rwanda, Sénégal, Tanzanie, Tunisie, Zimbabwe. "
   "ABSENTS : Congo-Brazzaville, Gabon, Tchad, Togo, Guinée équatoriale. "
   "⚠️ Pas de critère d'âge — le '40 ans max' circulant sur les réseaux est FAUX. "
   "Calendrier : appel ~4 août → clôture ~mi-septembre (plateforme GIRAF). "
   "Préparer le dossier DÈS MAINTENANT.",
   "https://www.ares-ac.be/fr/bourses"),
  # ── MasterCard Foundation ──────────────────────────────────────────────────
  ("🌍 MasterCard Foundation Scholars Program",
   "L'un des plus grands programmes de bourses au monde (50 000+ boursiers, objectif 100 000 "
   "d'ici 2030, 71 % de femmes). Entièrement financé : frais de scolarité + logement + "
   "matériel + transport + assurance + mentorat. Niveaux : Secondaire, Bachelor (≤ 29 ans), "
   "Master (≤ 35 ans). Réservé aux citoyens africains — réfugiés inclus. "
   "EXCLUS : double nationalité ou résidence permanente US/Canada/UK/UE. "
   "62+ universités partenaires dont Sciences Po (Paris), Cambridge, McGill, Toronto, "
   "UC Berkeley, CMU-Africa, Makerere, KNUST, Univ. Rwanda… "
   "Candidature DÉCENTRALISÉE : postuler directement auprès de chaque université partenaire "
   "(chacune a son calendrier, sept → janv pour une rentrée 2027). "
   "⚠️ ALERTE OFFICIELLE : des posts Facebook frauduleux 'recrutent' en demandant des frais. "
   "Le programme ne demande JAMAIS d'argent. Signalement : privacy@mastercardfdn.org.",
   "https://mastercardfdn.org/en/what-we-do/our-programs/mastercard-foundation-scholars-program/where-to-apply/"),
 ])'''

# ── REMPLACEMENT IT ──────────────────────────────────────────────────────────

ANCIEN_IT = '''\
D["IT"] = dict(nom="Italie", flag="🇮🇹",
 resume="Le secret le mieux gardé d'Europe : frais calculés sur TES revenus (souvent 500–3 000 €/an) "
        "et bourses régionales DSU qui couvrent logement + repas + allocation, même pour les étrangers.",
 ressources="≈6 500 €/an à justifier (hors bourse DSU)",
 travail="20 h/semaine", post="Permesso de recherche d'emploi 12 mois",
 portail="https://studyinitaly.esteri.it",
 services=["ORIENT","ADMIS","DOSSIER","BOURSE","VISA","TRAD","PACK"],
 etapes=[
  ("Pré-inscription sur Universitaly", "La plateforme officielle reliée à ton consulat — l'équivalent italien de Campus France.", "https://www.universitaly.it", "ADMIS"),
  ("Demander la bourse régionale DSU", "Sur critères sociaux : logement + cantine + ~5 200 €/an. Peu de candidats étrangers la connaissent.", None, "BOURSE"),
  ("Visa D études", "Admission + fonds + logement + assurance.", None, "VISA"),
 ],
 bourses=[("DSU régional", "Logement + repas + allocation sur critères sociaux.", None),
          ("Invest Your Talent in Italy", "Masters ciblés + stage en entreprise italienne.", "https://investyourtalentapplication.esteri.it")])'''

NOUVEAU_IT = '''\
D["IT"] = dict(nom="Italie", flag="🇮🇹",
 resume="Deux voies complémentaires pour l'Italie : les ÉTUDES (frais calculés sur tes revenus, "
        "souvent 500–3 000 €/an, bourses DSU) et le TRAVAIL via le Decreto Flussi "
        "(497 550 entrées 2026-2028 — quota réservé pour 14 pays africains, voie générale pour tous).",
 ressources="≈6 500 €/an à justifier (hors bourse DSU) pour les études · "
            "Travail : employeur requis avant toute démarche",
 travail="20 h/semaine (études) · Temps plein (Decreto Flussi)",
 post="Permesso de recherche d'emploi 12 mois (études) · Renouvellement contrat (travail)",
 portail="https://studyinitaly.esteri.it",
 services=["ORIENT","ADMIS","DOSSIER","BOURSE","VISA","TRAD","PACK"],
 etapes=[
  ("Pré-inscription sur Universitaly", "La plateforme officielle reliée à ton consulat — l'équivalent italien de Campus France.", "https://www.universitaly.it", "ADMIS"),
  ("Demander la bourse régionale DSU", "Sur critères sociaux : logement + cantine + ~5 200 €/an. Peu de candidats étrangers la connaissent.", None, "BOURSE"),
  ("Visa D études", "Admission + fonds + logement + assurance.", None, "VISA"),
  # ── Decreto Flussi (Métier / Saisonnier) ──────────────────────────────────
  ("🛂 Decreto Flussi — trouver un emploi en Italie",
   "DPCM 02/10/2025 : 497 550 entrées sur 2026-2028 (164 850/an). "
   "L'employeur fait TOUT : il dépose la demande de nulla osta sur le Portale ALI, "
   "tu n'as qu'à être prêt avec les documents. "
   "Trois groupes selon ton pays d'origine — voir ci-dessous.", None, None),
  ("Groupe 1 — 14 pays africains à quota réservé (click day 16 fév)",
   "Algérie, Côte d'Ivoire, Égypte, Éthiopie, Gambie, Ghana, Mali, Maroc, Maurice, "
   "Niger, Nigeria, Sénégal, Soudan, Tunisie. "
   "25 000 places/an rien que pour ces pays. "
   "⚠️ Maroc : circuit d'avis renforcé Questura + Inspectorat — délais plus longs, "
   "dossier irréprochable requis. "
   "Précompilation ALI : oct–déc 2026 (fenêtre annuelle). "
   "Secteurs : transport CQC, bâtiment, mécanique, télécoms, hôtellerie, "
   "électriciens, plombiers, alimentaire, naval.",
   "https://portaleservizi.dlci.interno.it/AliSportello/ali/home.htm", None),
  ("Groupe 2 — tous les autres pays (Cameroun, RDC, Guinée…) — click day 18 fév",
   "Quote générale — compétition plus large mais deux canaux stratégiques sous-utilisés : "
   "(1) SAISONNIER (agricole 12 jan, tourisme 9 fév) : la concurrence s'est effondrée "
   "(72 000 demandes en 2025 vs 337 000 en 2024 pour ~82 000 quotas). "
   "(2) BADANTI hors quota (DL 146/2025) : 10 000 places supplémentaires pour l'assistance "
   "aux handicapés et aux 80+ ans, ouverts dès le 1er janvier via agences pour l'emploi — "
   "utilisés à seulement 13 % en 2025. Aucune restriction de nationalité.",
   "https://portaleservizi.dlci.interno.it/AliSportello/ali/home.htm", None),
  ("Groupe 3 — colf/badanti (aide domestique) — click day 18 fév",
   "13 600 places A-bis exclusif domestique + ~19 300 hors quota. "
   "AUCUNE restriction de nationalité. Condition côté employeur : revenu ≥ 20 000 €/an. "
   "Canal le plus accessible pour qui a une expérience dans l'aide à la personne.",
   None, None),
  ("Préparer MAINTENANT pour 2027",
   "Les click days 2026 sont passés. Les dates 2027 sont déjà connues (même calendrier annuel). "
   "Action immédiate : trouver un employeur italien intéressé (offres Yorbity + candidature à distance), "
   "rassembler les documents (casier judiciaire international, diplômes traduits, CV en italien). "
   "La précompilation ALI ouvre en octobre 2026 — l'employeur doit être prêt à ce moment-là.",
   "https://www.interno.gov.it/it/servizi/servizi-line/procedure-flussi", None),
 ],
 bourses=[
  ("DSU régional", "Logement + repas + allocation sur critères sociaux (études).", None),
  ("Invest Your Talent in Italy", "Masters ciblés + stage en entreprise italienne.", "https://investyourtalentapplication.esteri.it"),
 ])'''

# ── MOTEUR DU PATCH ──────────────────────────────────────────────────────────

def main():
    if not CIBLE.exists():
        sys.exit(f"❌ Fichier introuvable : {CIBLE}")

    source = CIBLE.read_text(encoding="utf-8")

    # Idempotence
    if "_patch_fiches_italie_belgique_mcf_v1" in source:
        print("ℹ️  Patch déjà appliqué — rien à faire.")
        sys.exit(0)

    # Vérifier les ancres
    for label, ancre in [("BE", ANCRE_BE), ("IT", ANCRE_IT)]:
        if ancre not in source:
            sys.exit(f"❌ Ancre {label} introuvable — fichier modifié ? Abandon.")

    # Vérifier les blocs complets à remplacer
    if ANCIEN_BE not in source:
        sys.exit("❌ Bloc BE exact non trouvé — vérifier les ancres. Abandon.")
    if ANCIEN_IT not in source:
        sys.exit("❌ Bloc IT exact non trouvé — vérifier les ancres. Abandon.")

    # Backup
    bak = CIBLE.with_suffix(
        f".bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}.py"
    )
    shutil.copy2(CIBLE, bak)
    print(f"✅ Backup : {bak.name}")

    # Appliquer les deux remplacements
    nouvelle = source.replace(ANCIEN_BE, NOUVEAU_BE, 1)
    nouvelle = nouvelle.replace(ANCIEN_IT, NOUVEAU_IT, 1)

    # Ajouter le marqueur d'idempotence
    nouvelle += "\n# _patch_fiches_italie_belgique_mcf_v1\n"

    # Vérification syntaxique
    try:
        ast.parse(nouvelle)
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe : {e}")
        print("   Restauration du fichier original…")
        shutil.copy2(bak, CIBLE)
        sys.exit(1)

    # Écriture
    CIBLE.write_text(nouvelle, encoding="utf-8")
    print("✅ ui.py patché avec succès.")
    print("   → Fiche BE : ARES enrichi + MasterCard Foundation")
    print("   → Fiche IT : Decreto Flussi (3 groupes + canal badanti + saisonnier)")
    print(f"   → Backup conservé : {bak.name}")
    print("\nRelancer Streamlit pour vérifier :")
    print("  pkill -f streamlit; cd ~/mobilite-ia && streamlit run app/api/ui.py")

if __name__ == "__main__":
    main()
