# RAPPORT YORBITY — état au 2026-07-09

## Contexte technique
Plateforme mobilité étudiante. Streamlit/Python, Mac, dossier ~/mobilite-ia, venv .venv.
Raccourci terminal : `yorbity` lance l'app.
Modules dans app/api/ : ui.py, auth.py, espace.py, dossiers.py, traduction.py, autotrad.py,
admin_projets.py, admin_comptes.py, mdp_oublie.py, config_projets.py, opportunites_ui.py,
jobs_api.py, eligibilite.py, offres_cfg.py, devises_cfg.py, services_cfg.py, pays_i18n.py,
i18n.py, destinations_monde.py, pays_monde.py, paiement.py, securite.py.
Base SQLite : data/mobilite.db.
3 types de projet : "Formation (admission)", "Bourse", "Stage / Emploi étudiant".
SMTP Gmail configuré (yvanstephanenkoo@gmail.com). Job board API : Adzuna (clés à poser).

## Fait (sessions 7-9 juillet)
### Étoiles et configuration par projet
- config_projet_pays réparée, seed auto au démarrage, étoiles admin uniquement.
- Écran admin : liste déroulante + interrupteur (anti-erreur), ⭐=validé / 🔵=forcé / ◻️=inactif.
- Visibilité visiteur = actif seul (pays_visibles → if ac).

### Traduction
- autotrad v2.1 (patch DeltaGenerator = page+sidebar+colonnes+forms+expanders).
- traduction.py blindé (rejet réponses parasites LLM), cache purgé.
- pretraduire.py créé (préchauffage par langue, ~2126 textes EN en cache).

### Devise
- Base EUR partout (constante R=655.96 dans ui.py).
- Admin : tarifs services en EUR (info-bulle FCFA), forfaits Premium CRUD complet en EUR.
- Visiteur : sélecteur devise (sidebar), format plateforme d'admission (symboles locaux,
  arrondi centaine pour montants >= 1000, unité pour devises fortes, équivalent EUR discret).
- Admin : écran 💱 Devises pour activer/désactiver les devises proposées.

### Sécurité
- PBKDF2-SHA256 200k itérations + sel (existant). Réinitialisation admin (mdp temporaire
  24h usage unique, changement forcé 1re connexion). "Mot de passe oublié" libre-service
  (code 6 chiffres haché, 15 min, 3 essais, anti-énumération, envoi Gmail OK, WhatsApp
  prêt si Twilio configuré). Journalisation security_events.

### Contenu par type de projet
- Formation : budget + travail + après-diplôme + étapes complètes.
- Stage/Emploi : masque budget/étapes d'études, affiche offres filtrées par origine
  (base opportunites + job board Adzuna en direct, cache 12h, 19 pays couverts).
- Bourse : bourses filtrées par origine, liens visibles (visiteur et admin).
- Métiers spécialisés (menuisier, charpentier, électricien, maçon, plombier, soudeur) :
  intégrés sous Stage/Emploi, recherche API dédiée par mots-clés métiers.
- Offres emploi/stage/métier : liens ADMIN uniquement, visiteur voit une référence JOB/OPP.

### Admissibilité
- Module eligibilite.py : règles par destination × type (TOUS / liste / SAUF:xx).
- Admin : écran 🛂 pour définir qui peut candidater (expertise immigration).
- Système croise automatiquement avec origine du visiteur avant affichage.

### Forfaits Premium
- offres_cfg.py : CRUD complet (créer/modifier/désactiver/supprimer), base EUR.
- espace.py : affichage dynamique depuis config_offres (plus figé dans paiement.OFFRES).
- Mode test fonctionnel ; branchement CinetPay réel à finaliser.

### Bugfixes
- espace.est_premium → auth.est_premium.
- Clé session _mdpo_email (conflit widget Streamlit).
- prix_min_eur → prix_min_fcfa / 655.96 (variable manquante).

## À FAIRE (prochaine session)
1. BRANCHEMENT PAIEMENT RÉEL CinetPay pour les offres Premium personnalisées.
   → Claude a besoin de : cat app/api/paiement.py
2. Clés API Adzuna à poser dans .env (compte gratuit sur developer.adzuna.com).
3. Remplir les règles d'admissibilité (admin → 🛂) pour les destinations clés.
4. Tester la traduction en anglais sur toutes les pages après les derniers ajouts.
5. Optionnel : API France Travail pour enrichir les offres France.

## Méthode de travail convenue
- Claude livre UN SEUL script bash/heredoc par lot (pas de fichiers à télécharger).
- Chaque patch : sauvegarde .bak horodatée, ancres exactes, idempotent, syntaxe vérifiée.
- Claude teste tout dans sa sandbox (AppTest Streamlit) avant de livrer.

## Commande d'ouverture prochaine session
Dans une nouvelle page Claude, coller la sortie de :
cd ~/mobilite-ia && { cat RAPPORT_YORBITY.md; echo; echo "===== paiement.py ====="; cat app/api/paiement.py; } | pbcopy && echo "Collé — ouvre Claude et colle (Cmd+V)"

## Session du 10 juillet (ajouts)
- 4e type de projet « Métier spécialisé » (i18n 9 langues, config_projets, pays_i18n).
- recherche_poste.py : le champ « Niveau visé » devient « Poste recherché » pour
  Métier et Stage/Emploi (suggestions base + 20 métiers de référence, saisie libre,
  filtre des offres). Fix : « Choisir… » sur champ grisé ne bloque plus le résultat.
- jobs_api : dédup offres, filtre BRUIT (Uber/Deliveroo/VTC), mots-clés qualifiés
  (« student campus part-time »), ciblage par domaine, titres/lieux traduits.
- offres_sync.py : ingestion continue (12h) + agent Ollama (valide international,
  extrait nationalités, nomme le métier) + vérification des liens morts (404).
  Deux interrupteurs admin : « Montrer les liens » et « Montrer les descriptions ».
- eligibilite.py : règles admissibilité par destination × type (TOUS / liste / SAUF:).
- Clés Adzuna posées dans .env (ff822529). API testée : 8 offres métier CA.
- Note : « job not available in your region » = géo-blocage du site Adzuna, pas un bug.

## À FAIRE
1. Brancher paiement réel CinetPay sur offres Premium personnalisées → cat app/api/paiement.py
2. Remplir les règles 🛂 pour les destinations clés.
3. Vérifier pertinence des offres après filtres (domaine + anti-bruit).
4. Tester traduction EN sur toutes les pages.
