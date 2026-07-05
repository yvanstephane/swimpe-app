# ANNEXE A — ARCHITECTURE MULTI-CORRIDORS
### Extension v1.1 du PLAN_MOBILITE_IA.md — à placer dans docs/
### Cible : étudiants des pays en développement / à revenu intermédiaire → pays riches
### (ex : Cameroun→France, Gabon→Canada, Haïti→France, Chine→France…)
### Dernière mise à jour : 2026-07-04

---

## A1. LE CONCEPT CENTRAL : LE CORRIDOR

L'unité de base du produit n'est plus « la France » mais le **corridor** :
`corridor = (pays_origine, pays_destination)`.

Toute la donnée, tout le pricing, tout le marketing s'organisent par corridor, car :
- La procédure change selon l'origine (un Camerounais passe par Études en France,
  un Chinois aussi, mais avec des espaces Campus France, des frais et des délais différents).
- La preuve financière change selon la destination (France ≈ 7 380 €/an ;
  Canada hors Québec ≈ 22 895 CAD + frais de scolarité ; Québec ≈ 24 617 CAD depuis le 01/01/2026).
- La concurrence change selon le corridor (Chine→partout : marché d'agents saturé ;
  Haïti→Canada : quasi désert de services fiables).
- Le moyen de paiement change selon l'origine (Mobile Money, MonCash, Alipay, carte).

### Schéma de données (à ajouter dans app/normalizers/schemas.py)
```python
class Corridor(BaseModel):
    origine: str            # code ISO : CM, GA, HT, CN, SN, CI, DZ, MA...
    destination: str        # FR, CA, BE, DE, US, UK...
    procedure: str          # "etudes_en_france" | "ircc_pal" | "ircc_caq" | "uni_direct"...
    preuve_financiere: dict # {montant, devise, valable_depuis, source_url}
    frais_procedure: dict   # {montant, devise, source_url}   ex: Campus France 70-85k FCFA
    calendrier: list        # jalons datés (vœux, réponses, visa)
    tests_langue: list      # TCF/DELF, IELTS/TEF selon destination + établissement
    droit_travail_etudiant: str   # FR: 964 h/an ; CA: 20 h/sem en session
    post_diplome: str       # FR: APS/RECE ; CA: PGWP (master 3 ans possible)...
    famille: str            # CA: permis conjoint restreint aux master/doctorat/pro
    risques: list           # plafonds, taux de refus élevés, changements récents
    collected_at: date
    sources: list[str]      # URLs officielles UNIQUEMENT pour ce bloc
```

---

## A2. FICHES DESTINATION (état vérifié juillet 2026 — à re-vérifier tous les 90 jours)

### A2.1 FRANCE (déjà couverte au §2 du plan principal)
- Procédure Études en France obligatoire depuis ~70 pays (dont Cameroun, Gabon, Haïti,
  Chine, Sénégal…) ; ~350 établissements connectés ; frais locaux ~70–85 000 FCFA en
  Afrique centrale/ouest, non remboursables.
- Ressources exigées : 615 €/mois soit 7 380 €/an (AVI ≈ 460–470 € chez Studely/RSG).
- Droits différenciés non-UE en université publique (licence/master), exonérations possibles.
- Post-diplôme : APS / carte « recherche d'emploi ou création d'entreprise ».

### A2.2 CANADA — la destination « à forte valeur informationnelle » (règles mouvantes)
- **Plafond national** : IRCC prévoit jusqu'à 408 000 permis d'études délivrés en 2026,
  dont 155 000 pour les nouveaux étudiants ; 309 670 places de demande sous plafond,
  réparties par province. → Message produit : « postule TÔT, les quotas provinciaux s'épuisent ».
- **LAP/LAT** (lettre d'attestation provinciale) exigée pour la plupart des candidats
  post-secondaires ; EXEMPTIONS depuis le 01/01/2026 : maîtrise/doctorat dans un EED
  public, primaire/secondaire, échanges.
- **Québec ≠ reste du Canada** : CAQ (≈ 127 CAD, 4–6 semaines) au lieu de la LAP ;
  preuve de fonds Québec portée à **24 617 CAD** (adulte seul, hors scolarité) au 01/01/2026 —
  elle a plus que triplé pour les mineurs. Hors Québec : ≈ **22 895 CAD** + scolarité
  (montant relevé au 01/09/2025, révisé chaque année).
- Frais : demande 150 CAD, biométrie 85 CAD. Travail : 20 h/sem en session, temps plein
  aux congés. Conjoints : permis de travail ouvert restreint aux étudiants de
  maîtrise/doctorat/programmes professionnels. Post-diplôme : PGWP (jusqu'à 3 ans pour
  un master ≥ 8 mois, conditions).
- ⚠️ **Réglementaire** : au Canada, conseiller en immigration contre rémunération est
  réservé aux consultants réglementés (CISR/CICC) et avocats. Notre module Canada reste
  **informatif + préparation de documents génériques** ; pour du conseil personnalisé,
  partenariat d'affiliation avec un RCIC (modèle Immiland : plateforme + pros agréés).

### A2.3 Destinations Phase 2+ (fiches à construire sur le même modèle)
- **Belgique** : équivalences de diplômes (fédération Wallonie-Bruxelles), preuve ~ montant
  annuel fixé par arrêté ; très demandée par Cameroun/RDC.
- **Allemagne** : compte bloqué (Sperrkonto ≈ 11 904 €/an, à vérifier), gratuité quasi
  totale des universités publiques ; forte demande, peu d'offre francophone d'accompagnement.
- **Maroc/Turquie/Chine** comme destinations intermédiaires « plan B » : bourses
  gouvernementales généreuses pour étudiants africains — différenciateur original.

---

## A3. FICHES ORIGINE (les 4 profils types du lancement)

| Origine | Spécificités | Paiement | Concurrence | Priorité |
|---|---|---|---|---|
| **Cameroun** | Volume énorme vers France/Canada/Belgique/Allemagne ; procédure EEF ; forte culture « agences » (méfiance à retourner en avantage par la transparence) | MTN MoMo, Orange Money | Agences locales + Studely présents | ★★★ Lancement |
| **Gabon** | Ton marché de départ (réseau local) ; EEF ; pouvoir d'achat supérieur à la moyenne régionale | Airtel Money, Moov | Faible | ★★★ Lancement |
| **Haïti** | EEF pour la France ; forte demande Canada (francophone, Québec) MAIS preuve de fonds Québec 24 617 CAD = barrière → notre valeur : orientation réaliste (autres provinces, bourses, plan B Belgique/France) ; contexte : diaspora paie souvent depuis US/Canada | MonCash, Zelle/virement diaspora | Quasi désert de services fiables | ★★☆ Corridor solidaire |
| **Chine** | Marché géant mais SATURÉ d'agents établis (New Oriental Vision, Bright…) ; barrière langue/canaux (WeChat) ; réglementation locale des agences | Alipay/WeChat | Extrême | ☆ Phase 5+, via partenaires seulement |

**Règle de priorisation des corridors** (score 0–5 sur chaque axe, on lance si ≥ 14/20) :
`score = demande + capacité_à_payer + faiblesse_concurrence + notre_avantage(langue, réseau, données)`
→ Lancement : **CM→FR, GA→FR, GA→CA, HT→FR/CA**. Extension : SN, CI, CD, DZ, MA → FR/CA/BE/DE.

---

## A4. IMPACT PRODUIT

1. **M1 Orientation** devient un **routeur de corridors** : le questionnaire produit non
   pas « tes formations en France » mais « tes 3 meilleurs corridors », avec pour chacun
   budget total réaliste, probabilité indicative, calendrier. Exemple de sortie honnête :
   *« Québec : preuve de fonds 24 617 CAD + scolarité → hors budget. Alternatives :
   Nouveau-Brunswick (francophone, seuil 22 895 CAD), France (7 380 €), Belgique. »*
   C'est CE réalisme chiffré que ni les agences ni les rêves TikTok n'offrent.
2. **M5 Visa** se décline par destination : checklist France-Visas / IRCC (LAP ou CAQ,
   biométrie, plan d'études d'une page — motif n°1 de refus au Canada = fonds mal
   présentés et lettre d'intention faible → produit S3-CA « lettre d'intention béton »).
3. **M10 Immigration** : par destination, chaîne claire études → travail post-diplôme →
   résidence (FR : APS→salarié→résident ; CA : PGWP→Entrée express/PSTQ), toujours
   informatif et sourcé.
4. **RAG** : une collection Chroma par destination + une par origine ; le retrieval
   filtre TOUJOURS sur le corridor de l'utilisateur (métadonnées origine/destination)
   pour éviter les réponses mélangées (le piège classique : citer un montant Québec à
   un candidat pour l'Ontario).

---

## A5. PRICING MULTI-CORRIDORS (parité de pouvoir d'achat)

Trois zones tarifaires, mêmes services (S1–S8, P1, P2 du §8 du plan) :

| Zone | Origines | Coefficient | Ex. Pack S2 « Trouver mon université » | Ex. P1 complet |
|---|---|---|---|---|
| Z1 Solidaire | Haïti, RDC, Madagascar… | ×0,6 | ~21 000 FCFA éq. (≈ 32 USD via MonCash) | ~82 USD |
| Z2 Standard | Cameroun, Gabon, Sénégal, CI… | ×1 | 35 000 FCFA (~53 €) | 89 000 FCFA (~136 €) |
| Z3 Confort | Chine, Maroc, Algérie urbain, diaspora payeuse | ×1,8–2,5 | ~95–130 € | ~250–340 € |

Suppléments destination (la donnée Canada coûte plus cher à maintenir et vaut plus) :
- **+ S5-CA « Visa serein Canada »** : checklist LAP/CAQ + montage de la preuve de fonds
  (GIC/relevés 4 mois/lettre de garant conforme IMM 5826) + plan d'études relu : 30 000 FCFA Z2.
- **+ S9 « Plan B intelligent »** : rapport comparatif 3 destinations chiffrées : 15 000 FCFA Z2.
- Cas diaspora (fréquent pour Haïti) : le payeur est aux USA/Canada → prix Z3 acceptés
  via Stripe/Zelle même si l'étudiant est en Z1. Détecter le payeur, pas l'étudiant.

---

## A6. NOUVELLES TÂCHES (à fusionner dans la roadmap §9 du plan principal)

### Phase 1bis — Corridorisation des données
- [ ] T-060 Ajouter le schéma `Corridor` + table SQLite `corridors`
- [ ] T-061 Fiches corridor CM→FR, GA→FR, HT→FR (réutiliser les données France du plan)
- [ ] T-062 Collector Canada : pages IRCC preuve de fonds + plafond/allocations 2026 + liste EED (CSV officiel) + délais de traitement par pays
- [ ] T-063 Fiches corridor GA→CA, CM→CA, HT→CA (Québec ET hors Québec séparés)
- [ ] T-064 Collector bourses Canada (EduCanada) + bourses Vanier/provinciales
- [ ] T-065 Métadonnées corridor dans Chroma + filtre retrieval obligatoire + test : « un Haïtien demande le montant de preuve de fonds pour Montréal vs Toronto » → 2 réponses distinctes et sourcées
- [ ] T-066 M1 v2 : questionnaire → top 3 corridors avec budget total réaliste
- [ ] T-067 Grille tarifaire Z1/Z2/Z3 dans app/billing + détection du payeur
- [ ] T-068 [DÉCISION HUMAINE] Identifier 1 consultant RCIC partenaire pour le conseil Canada personnalisé (affiliation)
- [ ] T-069 Intégration paiements par origine : MonCash (Haïti), MTN/Orange Money (CM), Airtel (GA) — via agrégateur (CinetPay/Flutterwave couvrent l'Afrique ; MonCash direct)

### Indicateur nouveau (§11)
- Fraîcheur corridor : 100 % des montants financiers (7 380 €, 22 895/24 617 CAD…)
  re-vérifiés < 90 jours, avec date affichée à l'utilisateur.

---

## A7. MESSAGE DE MARQUE PAR CORRIDOR (pour le marketing)
- Afrique francophone → France : « Le dossier béton, sans agence opaque, au prix juste. »
- → Canada : « Les quotas 2026 sont limités et les montants ont changé : pars avec les
  vrais chiffres, pas les rumeurs. »
- Haïti : « On te dit ce qui est vraiment possible avec ton budget — et tes plans B. »
- Jamais, nulle part : « visa garanti », « admission garantie ».
