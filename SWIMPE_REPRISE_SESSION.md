# SWIMPE — CONTEXTE DE REPRISE (à uploader en début de session)

> Dernière mise à jour : 30 septembre 2026. Remplace la version du 10 août 2026.

## OÙ ON EN EST
L'app Streamlit **Swimpe** est EN LIGNE et FONCTIONNELLE sur Supabase PostgreSQL.
- URL app : swimpe-app-gxjuhhnhuhbbfcrwfr6wvg.streamlit.app
- Site vitrine : swimpe.com (séparé de l'app ; formulaires encore en maquette « SERA RELIÉE À L'APPLICATION »)
- Repo GitHub : github.com/yvanstephane/swimpe-app (branche `main`, PUBLIC)
- Dépôt local Mac : ~/mobilite-ia (lancée via `streamlit run app/api/ui.py`)
- Connexion utilisateur validée end-to-end (lecture+écriture Supabase, auth OK)
- Rebrand visuel fait (logo « S », nom Swimpe, couleurs CFA, barre marine)

## SUPABASE
- Projet « swimpe », région EU Central Frankfurt, id `nwvcsqqukgygudbjnryk`
- Compte : connexion « avec GitHub » (email des commits : yvanstephanenkoo@gmail.com)
- Session/Transaction pooler port 6543 obligatoire
- 25 tables, ~29 000 lignes ; nouvelle table technique `heartbeat` (keep-alive)
- URL de connexion dans les secrets Streamlit ET dans les secrets GitHub (nom : DATABASE_URL)
- ⚠️ DISJONCTEUR : un seul essai de connexion à la fois, jamais en boucle (sinon blocage ~15 min)
- ⚠️ Plan gratuit : le projet se met en PAUSE après ~7 jours d'inactivité → géré par le keep-alive (voir plus bas)

## SECRETS
- Streamlit (Settings → Secrets) : DATABASE_URL, YORBITY_SMTP_USER, YORBITY_SMTP_PASS, ADMIN_PASSWORD
- GitHub (Settings → Secrets and variables → Actions) : DATABASE_URL (même valeur que Streamlit)

## GITHUB / GIT
- Token classic « swimpe-deploy » : scopes `repo` + `workflow` (le scope workflow est requis
  pour pousser des fichiers dans .github/workflows/)
- Username : yvanstephane
- ⚠️ Piège récurrent : le copier-coller ajoute parfois un `~` ou `^[[200~` parasite en fin de
  commande → taper `git push` à la main plutôt que le coller.

## ✅ FAIT (sessions d'août + reprise du 30 sept.)
- **Perf / lenteur** : cache de la connexion (`st.cache_resource`) + des pays actifs
  (`st.cache_data`) dans ui.py, avec ping `SELECT 1` + reconnexion auto. Invalidation du cache
  au toggle admin (`_charger_actifs.clear()`). NB : ce patch avait été annulé par erreur
  (commit « revert cache ») puis RÉ-APPLIQUÉ le 30 sept.
- **Incident Supabase** résolu : l'erreur `psycopg2.OperationalError` venait de la base
  (mise en pause / DSN), PAS du code. L'app + l'auth refonctionnent.
- **Keep-alive** : GitHub Action `.github/workflows/keepalive.yml` + `.github/keepalive/ping_db.py`
  → écrit un battement réel dans la table `heartbeat` tous les 2 jours (cron `17 6 */2 * *`).
  Empêche la mise en pause Supabase. Déclenchable à la main via l'onglet Actions.
- **Rebrand Yorbity → Swimpe** : complet dans i18n.py (toutes langues) ET ui.py (offres + bouton retour).
- **Vouvoiement (tu → vous)** : i18n.py (23 chaînes FR) + ui.py (62 remplacements dans le
  contenu en dur : services, guides pays, disclaimer, formulaire, avertissements, 2 f-strings).
  ⚠️ NON touchés volontairement : commentaires du code (non affichés) et la clé i18n
  `bourses_pour_toi` (nom de clé, pas du texte).
- **Invite compte** (clé i18n `compte_invite`) : reformulée pour couvrir les 7 voies
  (études, bourses, stages, sport, art, volontariat), traduite dans les 9 langues.
- **Repo propre** : `.gitignore` ignore `*.bak_*`, `*.avant_*`, `app/api/patch_lenteur.py`.

## 🔲 TÂCHES RESTANTES (par priorité)

### 1. Finir vouvoiement + renommage ailleurs
Vérifier `app/api/espace.py` et `app/api/mdp_oublie.py` : le contexte d'août les citait comme
contenant encore du tutoiement / « Yorbity ». Uploader ces fichiers, sonder, patcher (même méthode).

### 2. Bandeau en dur (cosmétique)
Dans ui.py, le bandeau « swimpe.com · Application · Espace membre · Verifier une offre » est
en dur ; « Verifier » manque l'accent (« Vérifier »). Petit polish.

### 3. Site vitrine → application (domaine)
- Brancher les boutons/formulaires de swimpe.com sur l'app Streamlit (aujourd'hui : maquette).
- Option : CNAME Cloudflare `app.swimpe.com` → app Streamlit.

### 4. Worker Mac Ollama (gros chantier, session dédiée)
Lit les `demandes_plan` dans Supabase, traite par lots avec Ollama local, écrit le résultat.
Statuts : en_attente → en_cours → pret. Fichiers : file_plans.py, moteur_plans.py.

### 5. Contacter l'influenceuse (Fanné Yaya, Adecopa, Cameroun)
Mail de présentation prêt (2 versions : « communauté d'abord » recommandée, + « partenariat »).
⚠️ Mettre le VRAI lien Swimpe dans le mail, et n'envoyer qu'une fois l'app confirmée en ligne.

## STRUCTURE i18n.py (utile pour patcher)
- Dictionnaire `T` : chaque clé → `{"fr":..., "en":..., "es":..., "pt":..., "zh":..., "ar":..., "ja":..., "ko":..., "id":...}`
- 6+ langues gérées (fr/en/es/pt/zh/ar, parfois ja/ko/id). NE PAS casser les langues non-FR.
- `def t(cle, lang)` pour lire. `def _tr`/`tr` dans ui.py = souvent passthrough (texte FR en dur affiché tel quel).

## MÉTHODE DE TRAVAIL (à respecter)
- Sondes lecture seule AVANT tout patch (montrer le plan, valider le périmètre).
- Livrables : soit **heredoc scellé** `<< 'EOF'` si le patcher est **100 % ASCII** (accents/emojis
  encodés en `\uXXXX` via JSON), soit **fichier à télécharger** si le patcher est long.
  ⚠️ Éviter le base64 collé en chat : il s'est corrompu plusieurs fois (double-base64 surtout).
- Toujours dans les scripts : sauvegarde horodatée auto + `py_compile` + rollback auto si échec
  + vérification (import, comptages, diff FR-only).
- Yvan colle dans Terminal `~/mobilite-ia`, puis git add/commit/push + reboot/redeploy Streamlit.
- Après un push qui touche i18n/ui : `Cmd + Maj + R` sur l'app pour vider le cache navigateur.
- Distinguer TOUJOURS les 3 cibles : `localhost` (SQLite local) ≠ `swimpe.com` (site vitrine)
  ≠ `swimpe-app-...streamlit.app` (l'app en ligne, PostgreSQL). Les patchs i18n/ui se voient
  sur l'app en ligne, PAS sur le site vitrine.
