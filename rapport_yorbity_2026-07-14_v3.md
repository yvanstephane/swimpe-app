# RAPPORT DE PASSATION v3 — Yorbity (état au 2026-07-14)

Remplace le rapport v2 du 2026-07-13. Demain : glisse CE fichier + un
`reprise3.txt` frais (commande en bas) dans la nouvelle conversation, avec :
« Reprends Yorbity à partir de ces deux fichiers. »

## Projet
Yorbity (`~/mobilite-ia`) : app Streamlit d'aide à la mobilité internationale
(études / bourses / stages / métiers) pour un public africain, utilisateur
final HORS pays de destination, souvent sans permis. Lancement :
`cd ~/mobilite-ia && streamlit run app/api/ui.py` — MAIS l'utilisateur a un
alias/fonction **`yorbity`** qui fait tout (le binaire `streamlit` seul
renvoie « command not found » hors venv ; `yorbity` active le venv et lance).
Tuer avant : `pkill -f streamlit`. DB SQLite `data/mobilite.db` (WAL). Ollama
local : llama3.3:70b (interface/contenu), llama3.2:3b (offres, var
OFFRES_MODEL). macOS, zsh, venv 3.14. Machine active de la session : invite
`yvans-macbook-pro3` (rappel v2 : une 2e invite `yvans-macbook-pro` avait été
vue le 13/07 — vérifier la synchro de ~/mobilite-ia avant gros travaux).

## Règles de travail (durement apprises — non négociables)
1. JAMAIS de heredoc en zsh ; livrer des fichiers + UNE commande.
2. Noms de fichiers TOUJOURS versionnés (`_v1`, `_v2`…).
3. Tout fichier qui REMPLACE un existant voyage en installeur base64
   auto-vérifiant (SHA-256 + ast.parse/json.loads + .bak + idempotent).
   Modèle éprouvé cette session : tous les `installer_*_v1.py` ci-dessous.
4. Patchs : idempotents, `.bak`, `ast.parse`, restauration si casse, ancres
   EXACTES extraites du vrai fichier (demander la région avant d'écrire).
   Vérifier l'UNICITÉ de l'ancre (`count == 1`) avant de remplacer.
5. Les téléchargements Claude atterrissent dans des SOUS-DOSSIERS
   `~/Downloads/files-N/` → toute commande cherche avec
   `find ~/Downloads -maxdepth 3 -name '…'`. Le navigateur renomme parfois
   d'après le titre de la conversation → repli : chercher PAR CONTENU
   (`grep -l`). Commande d'install type validée cette session :
   `find ~/Downloads -maxdepth 3 -name "installer_X*" | head -1 | xargs python3`
6. Les pièces jointes de l'utilisateur arrivent souvent VIDES à l'écran mais
   le fichier EST sur disque (`/mnt/user-data/uploads/`) : lire le disque.
   Replis 100 % fiables : collage terminal, captures d'écran.
7. Mesurer avant de corriger : sondes avant adaptateurs ; captures avant CSS.
8. ⚠️ NOUVEAU (leçon du 14/07) : NE PAS coller les phrases d'explication de
   Claude dans le terminal — l'utilisateur a collé « …commande — si 0, lance… »
   et zsh a renvoyé une erreur. Toujours donner la commande SEULE, sur sa
   propre ligne, sans texte autour.
9. ⚠️ NOUVEAU : bien vérifier QUEL compte est connecté. Il existe « Yvan
   Admin » (admin, badge Premium + section « Yorbity · Admin ») ET « yvan »
   (compte gratuit NON admin). Les écrans admin (`est_admin()`) ne
   s'affichent QUE connecté en « Yvan Admin ».

## ⭐ CE QUE LA SESSION DU 13-14/07 A AJOUTÉ (nouveautés v3)

### A. Trois documents de référence (dans `data/`, PAS du code)
- **`data/feuille_route_italie_belgique_mcf_v1.md`** — recherche vérifiée
  Italie (Decreto Flussi, 3 groupes, 38 pays, badanti, saisonnier) +
  Belgique ARES (âge TRANCHÉ : pas de limite, c'est « diplôme ≤ 20 ans » ;
  le « <40 ans » de la source FB est FAUX) + MasterCard Foundation
  (VÉRIFIÉE : réelle, 29 ans Bachelor / 35 ans Master, candidature
  décentralisée par université, alerte fraude FB officielle).
- **`data/etude_marche_afrique_yorbity_v1.md`** — étude de marché 5 piliers.
  VERDICTS : marchés tier 1 = **Cameroun, Côte d'Ivoire, Sénégal** (CinetPay
  ✓ + corridors réels + demande). Tier 2 = RDC, Guinée, Mali, Niger, Bénin,
  Burkina, Togo. CinetPay = 11 pays 100 % francophones (dont FRANCE → diaspora
  peut payer pour un proche). Argument de vente central chiffré : refus visa
  Afrique francophone ~75 % (Canada) / ~45 % (Schengen), 3 causes principales
  RÉPARABLES par le dossier (ressources→FONDS, assurance→DOSSIER,
  retour→ENTRETIEN). CI et TG NON éligibles ARES → router vers MCF.
- Ces deux .md ont été rangés dans `data/` via des commandes `find … grep -l`.

### B. Le MOTEUR DE PLANS (déterministe, sans IA) — INSTALLÉ ✅
- **`app/api/moteur_plans.py`** + **`data/plans_pays_v1.json`** (désormais
  **v1.1**, voir E). Écran admin **`?page=plans`**.
- Principe cardinal : **AUCUN fait inventé**. Tout vient du JSON vérifié.
  L'option Ollama existe dans moteur_plans.ecran() mais la CONSOLE l'ignore
  (choix : 100 % déterministe, « le moins d'erreurs possible »).
- Génère un plan par (destination × pays d'origine) : routage groupe 1 / 2
  Italie, éligibilité ARES avec renvoi MCF, alertes pays (Maroc = circuit
  d'avis renforcé), dates calculées depuis aujourd'hui (click days 12/1,
  9/2, 16/2, 18/2 ; ARES ~4/8→19/9).
- Installé via `installer_moteur_plans_v1.py` puis branché dans ui.py via
  `patch_branchement_moteur_plans_v1.py` (import + bloc admin, ancres
  lignes 35 et ~1034).

### C. La CONSOLE D'ACCOMPAGNEMENT — INSTALLÉE ✅
- **`app/api/console_accompagnement.py`** + **`data/refus_par_pays_v1.json`**.
  Écran admin **`?page=console`** (⚠️ PAS `?page=accompagnement` : ce nom
  était DÉJÀ pris par un écran existant de ui.py ligne ~910 qui interceptait
  et bloquait — d'où `patch_renommer_console_v1.py` qui a corrigé la
  collision). Branché en ui.py ligne ~1038.
- 5 zones (blueprint validé avec l'utilisateur) : (0) profil client isolé
  — état `acc_*`, ne pollue pas l'accueil ; (1) recherche métier ; (2)
  diagnostic refus par pays sourcé (admin-only) ; (3) offres réelles via
  `jobs_api.afficher(...)` NON MODIFIÉ ; (4) plan daté via moteur_plans +
  compteurs J−.
- Décisions produit de l'utilisateur (à respecter) : profil ISOLÉ ;
  diagnostic admin-only MAIS prévoir **envoi PDF au client par email** (v2b,
  réutiliser la tuyauterie email de mdp_oublie.py) ; offres = sources réelles
  à jour ; nom `?page=console`. IA retirée de la console. Le moins d'erreurs
  possible même si c'est plus long.
- État VÉRIFIÉ À L'ÉCRAN : plan Cameroun→Italie généré correctement
  (quote générale, 18 fév, badanti, saisonnier). ✅

### D. Fiches D (études/bourses) Italie + Belgique — PATCH APPLIQUÉ ✅
- `installer_fiches_italie_belgique_mcf_v1.py` a enrichi `ui.py` :
  D["BE"] = ARES détaillé + entrée MasterCard Foundation ;
  D["IT"] = Decreto Flussi (3 groupes conditionnels + badanti + saisonnier).
  Marqueur présent (`grep -c "_patch_fiches_italie_belgique_mcf_v1" ui.py`
  → 1). RÉPOND à la question de l'utilisateur : oui, études+bourses BE/IT
  sont à jour dans les fiches.

### E. MAJ « ressources par étape » (v1.1) — INSTALLÉE ✅
- `installer_maj_ressources_etapes_v1.py` a remplacé plans_pays (→ v1.1) et
  moteur_plans (helper `_rendre_etape` qui rend les ressources 📚 sous chaque
  étape). Recherche approfondie « comment les dossiers réussissent » :
  - Étape employeur Italie : 6 ressources (DecretoFlussiItalia.it ; Job in
    Country Coldiretti ; liste officielle des associations d'employeurs
    autorisées — Coldiretti/Confagricoltura/CIA/CNA ; portails Indeed/InfoJobs ;
    Carte Bleue UE toute l'année pour qualifiés).
  - INSIGHT clé injecté : 30k des 40k places saisonnières agricoles réservées
    aux demandes via associations (toutes satisfaites le jour même en 2026) →
    viser un employeur ADHÉRENT. Et no-show 30 % (2/3 en 2023) → se présenter
    comme candidat FIABLE/DOCUMENTÉ (argument de candidature).
  - **BOUCLIER ANTI-ARNAQUE** (bloc dédié dans le plan IT) : réseaux de faux
    nulla osta 3 000-10 000 € (Bologne, Lecce/Taranto 30 arrestations, Naples
    milliers de victimes). Règle : le travailleur ne paie JAMAIS pour un
    contrat/nulla osta (c'est à l'employeur) ; vérifier l'entreprise sur
    registroimprese.it. Délai visa réel : 120+ jours (vs 20 légaux) → ne rien
    engager avant de l'avoir.

## En production (hérité v2, toujours valable)
- **Registre de sources** `app/api/sources/` : base, registre (tri
  sans_permis > lien_accessible, +_traduire_offre), jobbank_ca, adzuna (GB
  exclu par patch_uk_exclusif — CONFIRMÉ appliqué via reprise2), mig_de,
  uk_sponsors, pole_emploi_fr.
- **Canada** : Job Bank `fglo=1` — seul « sans permis » prouvé ; liens
  masqués aux visiteurs (choix produit).
- **Allemagne** : API BA v4 (X-API-Key: jobboerse-jobsuche) ; sans_permis=False
  en attente du drapeau MIG (inspecteur Safari, JAMAIS fait — voir file).
- **Royaume-Uni** ⭐ : uk_sponsors = Adzuna gb ∩ registre Home Office
  (125 846 employeurs, CSV data/uk_sponsors.csv 10 Mo daté 10/07 — CONFIRMÉ
  frais via reprise2, maj mensuelle scripts/maj_registre_uk_v1.py), PLAFOND
  500, bandeau 🛂, réfs UKS-, liens Find a Job (findajob.dwp.gov.uk, patch
  findajob CONFIRMÉ appliqué), lien_accessible=True.
- **Multilingue** : 11 langues (fr en es pt zh ar de it ja ko id) ; i18n.py
  repli + surcouches data/i18n/*.json ; traduction.py durci ; traduire_vers()
  + _traduire_offre() (offres traduites par l'app, cache SQLite, OFFRES_MODEL
  défaut llama3.2:3b). Quirk 3b : bégaie sur titres courts (« Countermaître »
  ×3) — remède à faire (OFFRES_MODEL plus gros / garde-fou anti-répétition).
- **Boutique/paiement v2** (paiement.py) : Premium 3 offres + 9 services,
  CinetPay par zone (XOF/XAF parité, GNF/CDF convertis, definir_param), mode
  test, livrer_service. Passage réel = .env CINETPAY_MODE=reel + API_KEY +
  SITE_ID (PAS ENCORE fournis). reprise2 : .env a 2 clés (présence booléenne).
- **Stabilité** : monkeypatch sqlite timeout 30 s (_yorbity_patience) +
  patch_seed_v1 (seed gardé par COUNT). NE JAMAIS réintroduire d'écriture à
  chaque rerun.
- **Lisibilité/CSS** (patchs v1→v5 sur ui.py) : mode clair OK prouvé ; mode
  sombre après v5 NON CONFIRMÉ. ⚠️ reprise2 a révélé : **PAS de config.toml**
  → la cause racine suspectée (secondaryBackgroundColor figé) est ÉCARTÉE. Si
  mode sombre encore cassé, chercher dans ui.py même.

## File d'attente (ordre conseillé, v3)
1. **Vérif écran** de la MAJ v1.1 : régénérer un plan CM→IT dans la console,
   confirmer les ressources 📚 sous chaque étape + le Bouclier 🛡️. Tester
   aussi SN→IT (groupe 1, 16 fév) et TG→BE (→ renvoi MCF).
2. **Bouton d'accès console** dans la barre latérale admin (section « Yorbity ·
   Admin ») — l'utilisateur tape l'URL à la main, pas viable en usage réel.
   Ancre à extraire : `grep -n "Yorbity · Admin\\|Pays visibles" app/api/*.py`.
   Ajouter un `st.link_button("🧭 Console", "?page=console")`.
3. **Console v2b** (persistance + valeur) : (a) « Créer le dossier client »
   → brancher dossiers.py, étapes cochables, statut (Nouveau→Diagnostic→
   Dossier→Soumis→Décision) ; (b) **export PDF + envoi email au client**
   (demande explicite utilisateur — réutiliser email mdp_oublie.py) ;
   (c) clic offre→plan (demande une petite modif de jobs_api, repoussée exprès
   en v2a pour ne rien casser).
4. **Lot 2 ressources** : approfondir ARES (lettre « développement », dossier
   gagnant) et MCF (essais leadership, cas McGill/Toronto) étape par étape,
   comme fait pour l'Italie. Puis **lot 3** : Allemagne + Canada (corridors
   tier 1 restants) dans plans_pays.
5. **Mode nuit** : confirmer v5 dans les DEUX modes (config.toml écarté).
6. **Drapeau MIG** (2 min Safari EN) : Settings→Advanced→dev features ;
   make-it-in-germany.com job-listings ; Network filtre `arbeitsagentur` ;
   Copy URL → _params() de mig_de, sans_permis DE=True.
7. **Clés CinetPay réelles** (+ vérifier taux GNF/CDF avant 1er encaissement).
8. Régénérer clés Adzuna (fuite git) ; maj registre UK mensuelle (~10/08).
9. Garde-fou anti-répétition 3b sur titres d'offres.
10. Optionnel : sonde_europe_v2 (jamais exécutée), Actiris, work-in-luxembourg,
    câblage offre→dossier, vérif MasterCard Foundation côté source FB.
11. Hygiène : proton-recovery-phrase.pdf traînait dans Downloads →
    gestionnaire de mots de passe puis suppression.
12. Fonctionnalité produit notée : « offrir un accompagnement à un proche »
    (la diaspora en France, dans CinetPay, finance souvent les projets).

## Fichiers clés (mis à jour v3)
**app/api/** : ui.py (CSS v1→v5, seed gardé, +patch fiches BE/IT,
+branchements moteur_plans & console) ; **moteur_plans.py** (NOUVEAU,
?page=plans, v1.1) ; **console_accompagnement.py** (NOUVEAU, ?page=console) ;
paiement.py, espace.py (est_admin), dossiers.py, devises.py, i18n.py,
pays_i18n.py, traduction.py, theme_pays.py, jobs_api.py (afficher() réutilisé
par la console, NON modifié), destinations_monde.py, pays_monde.py,
eligibilite.py, mdp_oublie.py (email → réutiliser pour PDF client),
sources/{base,registre,jobbank_ca,adzuna,mig_de,uk_sponsors,pole_emploi_fr}.py.
**data/** : mobilite.db, uk_sponsors.csv(+.date), i18n/*.json,
sources_pays_v1.json, **plans_pays_v1.json** (v1.1, base de faits du moteur —
ÉDITER CE JSON pour changer le contenu des plans, jamais le code),
**refus_par_pays_v1.json** (NOUVEAU, chiffres refus sourcés),
**feuille_route_italie_belgique_mcf_v1.md** (NOUVEAU, référence),
**etude_marche_afrique_yorbity_v1.md** (NOUVEAU, référence).
**Installeurs de la session** (dans ~/Downloads/files-N/, tous idempotents) :
installer_moteur_plans_v1, patch_branchement_moteur_plans_v1,
installer_console_accompagnement_v1, patch_renommer_console_v1,
installer_fiches_italie_belgique_mcf_v1, installer_maj_ressources_etapes_v1.

## Commande de reprise (générer reprise3.txt)
Réutiliser la commande qui a produit reprise2.txt (elle sonde patchs, sources,
config, registre UK, langues, clés). AJOUTER la vérification des nouveautés v3 :
```
{
echo "=== moteur & console ==="
ls -la ~/mobilite-ia/app/api/moteur_plans.py ~/mobilite-ia/app/api/console_accompagnement.py 2>&1
echo "--- versions base de faits ---"
grep -m1 '"version"' ~/mobilite-ia/data/plans_pays_v1.json
python3 -c "import json;k=json.load(open('$HOME/mobilite-ia/data/plans_pays_v1.json'));print('bouclier:', bool(k['destinations']['IT'].get('bouclier')))"
echo "--- branchements dans ui.py ---"
grep -n "moteur_plans.ecran\|console_accompagnement.ecran\|_patch_fiches_italie_belgique_mcf_v1" ~/mobilite-ia/app/api/ui.py
echo "--- docs de référence ---"
ls -la ~/mobilite-ia/data/*.md 2>&1
} > ~/reprise3_extra.txt 2>&1
```
(à fusionner avec la commande reprise2 d'origine si tu la retrouves ; sinon
ce bloc + reprise2.txt existant suffisent à la reprise.)
