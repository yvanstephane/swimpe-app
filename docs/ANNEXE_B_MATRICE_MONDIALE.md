# ANNEXE B — MATRICE MONDIALE DES CORRIDORS (TOUS PAYS)
### Extension v1.2 du PLAN_MOBILITE_IA.md — à placer dans docs/
### Couvre : ~195 origines × 30 destinations = ~5 850 corridors générés automatiquement
### Dernière mise à jour : 2026-07-04

---

## B1. PRINCIPE : ON NE RÉDIGE PAS 6 000 FICHES, ON LES GÉNÈRE

La matrice mondiale = **Origines (toutes, ISO-3166) × Destinations (30 gabarits)**.

- Une **fiche DESTINATION** (gabarit) contient 90 % de l'information : procédure, preuve
  financière, frais, calendrier, droit au travail, post-diplôme. Elle est écrite UNE fois,
  vérifiée, sourcée.
- Une **fiche ORIGINE** contient les attributs du pays de départ : groupe de procédure
  (ex. « procédure Études en France » oui/non), zone tarifaire (Z1/Z2/Z3), moyens de
  paiement, langues, exigences consulaires particulières, délais de traitement connus.
- Le **corridor** = croisement automatique des deux + un champ `specificites` que les
  LLM locaux remplissent progressivement (collector + extraction), avec statut
  `a_verifier → verifie → perime`.

Le script `scripts/gen_matrice.py` (fourni) crée les ~5 850 lignes dans SQLite en
statut `a_verifier`. Tes agents locaux les traitent ensuite par ordre de priorité (B5).

---

## B2. LES 30 DESTINATIONS (gabarits), en 3 tiers

### Tier D1 — Destinations majeures (fiches complètes en priorité)
| Dest. | Points clés vérifiés (juillet 2026) |
|---|---|
| **France** | Études en France (~70 pays), 7 380 €/an de ressources, AVI ~470 € — voir plan §2 |
| **Canada** | Plafond 2026 : ~408 000 permis dont 155 000 nouveaux ; LAP/LAT sauf exemptions (master/doctorat EED public) ; fonds : ~22 895 CAD hors Québec + scolarité ; Québec : CAQ (127 CAD) + 24 617 CAD depuis 01/01/2026 ; travail 20 h/sem ; PGWP jusqu'à 3 ans — voir Annexe A |
| **USA** | Visa F-1 : I-20 d'un établissement SEVP → taxe SEVIS I-901 **350 $** → DS-160 → frais MRV **185 $** (janv. 2026) → entretien consulaire. Montant I-20 à prouver : typiquement **40 000–90 000 $+/an** (scolarité + vie). Travail : 20 h/sem sur campus, CPT/OPT **12 mois (36 mois STEM)**. Motif n°1 de refus : **214(b)** (liens avec le pays d'origine / fonds jugés instables) → notre produit clé USA = dossier financier cohérent + prépa d'un entretien de 2 à 5 min. ⚠️ Vérifier sur travel.state.gov l'éventuelle taxe additionnelle d'intégrité visa évoquée depuis 2025. |
| **Royaume-Uni** | Student visa à points : CAS de l'université, preuve de fonds (Londres vs hors Londres), IHS santé — fiche à compléter (T-072) |
| **Allemagne** | Compte bloqué (Sperrkonto ~11 900 €/an à vérifier), uni-assist, quasi-gratuité du public |
| **Belgique** | Équivalence des diplômes (FWB), montants annuels par arrêté ; très demandée CM/RDC |
| **Australie** | GTE/Genuine Student, fonds élevés, marché d'agents structuré |

### Tier D2 — Destinations montantes / bourses massives (l'angle « plan B intelligent »)
| Dest. | Points clés vérifiés |
|---|---|
| **Japon** | Bourse **MEXT** : scolarité complète + **¥143 000–145 000/mois (~960–970 USD)** + billets ; candidature via ambassade ; **JICA ABE** : ~300 jeunes Africains/an (master + stage en entreprise) ; JASSO ¥48–80 000/mois ; exonérations 50–100 % dans les universités nationales |
| **Corée du Sud** | **GKS/KGSP** : scolarité + **₩900 000/mois** + vols + année de coréen ; ~**1 500 lauréats/an**, taux ~10–15 %, filière ambassade moins concurrentielle ; liste des pays APD éligibles inclut Cameroun, Gabon, Haïti, Sénégal… |
| **Chine (destination)** | Bourse **CSC** : scolarité + logement + **¥2 500–3 500/mois** + assurance ; 289 universités ; programmes bilatéraux (type A) via ambassades |
| **Turquie** | Türkiye Bursları (complet : scolarité + allocation + logement + turc) |
| **Malaisie, Maroc, Tunisie, Russie, Inde (ICCR), Qatar/EAU/Arabie saoudite, Hongrie (Stipendium), Roumanie/Pologne** | Fiches gabarit courtes : bourses gouvernementales + coût de vie faible = plans B crédibles pour budgets Z1/Z2 |

### Tier D3 — Reste de l'OCDE (fiches légères, à la demande)
Pays-Bas, Espagne, Italie, Portugal, Suisse, Suède, Norvège, Finlande, Danemark,
Irlande, Autriche, Nouvelle-Zélande, Japon régional… (générées en `a_verifier`,
complétées quand un utilisateur les demande — production « pull », pas « push »).

---

## B3. CLASSIFICATION DES ORIGINES (tous les pays, par attributs)

Chaque pays ISO reçoit ces attributs dans `data/origines.csv` (généré puis affiné) :

| Attribut | Valeurs | Exemple |
|---|---|---|
| `region` | AFR_W, AFR_C, AFR_E, AFR_N, AFR_S, ASIA_S, ASIA_SE, ASIA_E, ASIA_C, MENA, LATAM, CARIB, EU, OCEANIA, NAM | Cameroun=AFR_C, Inde=ASIA_S, Haïti=CARIB |
| `procedure_fr` | eef / dap_ambassade / hors_eef | Gabon=eef, Kenya=eef, Norvège=hors_eef |
| `zone_tarif` | Z1 / Z2 / Z3 (voir Annexe A5) | Haïti=Z1, Vietnam=Z2, Chine=Z3 |
| `paiement` | momo_mtn, momo_orange, momo_airtel, moncash, alipay_wechat, upi, carte, virement, cash_partenaire | Inde=upi, Haïti=moncash |
| `langues` | fr, en, ar, zh, es, pt… | Sénégal=fr, Philippines=en |
| `apd_gks` | oui/non (éligible bourses type GKS/APD) | Cameroun=oui |
| `concurrence` | faible / moyenne / saturee | Chine=saturee, Haïti=faible |
| `diaspora_payeuse` | oui/non (payeur probable hors du pays) | Haïti=oui, Philippines=oui |

### Focus ASIE comme ORIGINE (ta question)
- **Inde, Népal, Bangladesh, Pakistan, Sri Lanka** : volumes gigantesques vers
  Canada/USA/UK/Australie, mais marché d'agents ultra-dense et anglophone → n'y entrer
  qu'avec un angle : « destinations francophones + bourses Asie (MEXT/GKS/CSC) que les
  agents locaux ne vendent pas ». Zone Z2, paiement UPI.
- **Vietnam, Indonésie, Philippines** : croissance forte, agents nombreux ; corridor
  original : Vietnam→France (EEF s'applique au Vietnam).
- **Chine** : origine Z3 saturée (Annexe A) — partenaires seulement.
- **Asie centrale (Ouzbékistan, Kazakhstan…)** : demande émergente vers UE/Corée, peu
  d'acteurs francophones — opportunité de niche.

---

## B4. LA MATRICE (vue synthétique)

```
                    DESTINATIONS →
ORIGINES ↓      FR   CA   US   UK   DE   BE   AU   JP   KR   CN   TR   ...
Cameroun        ●●●  ●●●  ●●   ●●   ●●●  ●●●  ●    ●●   ●●   ●●   ●●
Gabon           ●●●  ●●●  ●●   ●    ●●   ●●   ●    ●    ●●   ●●   ●
Haïti           ●●●  ●●●  ●●   ●    ●    ●●   ○    ●    ●●   ●    ●
Sénégal/CI/CD   ●●●  ●●●  ●●   ●●   ●●●  ●●●  ●    ●●   ●●   ●●   ●●
Maghreb         ●●●  ●●●  ●●   ●●   ●●●  ●●   ●    ●    ●    ●    ●●
Inde/Asie Sud   ●    ●●●  ●●●  ●●●  ●●   ●    ●●●  ●●   ●●   ●    ○
Vietnam/ASE     ●●   ●●●  ●●●  ●●   ●●   ●    ●●●  ●●●  ●●●  ●●   ○
Chine           ●●   ●●   ●●●  ●●●  ●●   ○    ●●●  ●●●  ●●●  —    ○
LATAM           ●●   ●●   ●●●  ●●   ●●   ●    ●●   ●    ●    ●    ○

●●● = corridor prioritaire (on vend)   ●● = actif (fiches générées + vérifiées)
●   = généré, complété à la demande    ○ = dormant   — = non pertinent
```
Cette vue est *indicative* ; la vraie matrice vit dans SQLite (table `corridors`,
~5 850 lignes) et chaque cellule porte son score calculé (B5).

---

## B5. SCORE DE PRIORITÉ (calculé automatiquement pour chaque corridor)

```
score = 2×demande(0-5) + 2×capacite_payer(0-5) + faiblesse_concurrence(0-5)
        + avantage_langue(0-5) + faisabilite_visa(0-5)            # max 35
```
- `demande` : proxys = volume d'étudiants sortants (UNESCO UIS, open data) + tendances.
- `faisabilite_visa` : taux de refus connus, plafonds (ex. Canada), coût d'entrée
  (ex. USA 40–90 k$/an → faible pour Z1 sans bourse ; élevé si bourse type Fulbright).
- File de travail des agents locaux = corridors triés par score décroissant ;
  un corridor n'est « vendable » que si `statut=verifie` et fraîcheur < 90 j.

---

## B6. IMPACT PRODUIT : LE « ROUTEUR MONDIAL »

M1 v3 : l'utilisateur (de N'IMPORTE quel pays) décrit profil + budget → le moteur
classe les 30 destinations par faisabilité RÉELLE et honnête, ex. pour un bachelier
camerounais avec 4 000 €/an :
1. France (7 380 € à prouver mais études quasi gratuites au public) — faisable avec garant
2. Bourses Asie : GKS Corée (~1 500 places/an, ambassade), MEXT Japon, CSC Chine — 100 % financées, très compétitives → on vend la préparation du dossier
3. Turquie/Maroc — coût faible
4. Canada — difficile : 22 895 CAD + scolarité à prouver, quotas
5. USA — hors budget sans bourse complète (40–90 k$/an sur l'I-20)

C'est exactement ce que ni un agent (qui vend SA destination commissionnée) ni
Campus France (mono-pays) ne diront jamais. **Notre produit = la vérité chiffrée
multi-destinations.**

---

## B7. NOUVELLES TÂCHES (roadmap, suite de l'Annexe A)

- [ ] T-070 Exécuter `scripts/gen_matrice.py` → tables `destinations`, `origines`, `corridors` peuplées (tous pays)
- [ ] T-071 Fiches destination D1 complètes : USA (F-1/SEVIS/MRV/OPT/214b) + UK + Allemagne + Australie, sourcées
- [ ] T-072 Fiches D2 « bourses massives » : MEXT, GKS, CSC, Türkiye Bursları, JICA ABE (critères, calendriers, liens ambassades)
- [ ] T-073 Affiner `origines.csv` : zone_tarif, paiement, concurrence pour les 60 origines au score le plus élevé
- [ ] T-074 Collector UNESCO/open data : volumes d'étudiants sortants par pays → champ `demande`
- [ ] T-075 M1 v3 « routeur mondial » : profil → classement honnête des 30 destinations
- [ ] T-076 Produit S10 « Dossier bourse Asie » (MEXT/GKS/CSC) : 25 000 FCFA Z2 — personne ne le vend en Afrique francophone
- [ ] T-077 [DÉCISION HUMAINE] Choisir les 10 corridors « ●●● » du lancement commercial
- [ ] T-078 Règle RAG : filtre corridor obligatoire + test croisé (question Inde→Canada ne doit jamais renvoyer un montant Québec/France)
