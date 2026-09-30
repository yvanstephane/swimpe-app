# SWIMPE — CONTEXTE DE REPRISE (à uploader en début de session)

## OÙ ON EN EST (10 août 2026)
L'app Streamlit **Swimpe** est EN LIGNE et FONCTIONNELLE sur Supabase PostgreSQL.
- URL app : swimpe-app-gxjuhhnhuhbbfcrwfr6wvg.streamlit.app
- Repo GitHub : github.com/yvanstephane/swimpe-app (branche `main`, PUBLIC)
- Dépôt local Mac : ~/mobilite-ia (commande `yorbity`, lancée via `streamlit run app/api/ui.py`)
- Connexion utilisateur validée end-to-end (lecture+écriture Supabase, envoi email OK)
- Rebrand VISUEL fait : logo « S », nom Swimpe, couleurs CFA, barre marine (dernier commit)

## SUPABASE
- Projet « swimpe », région EU Central Frankfurt, id `nwvcsqqukgygudbjnryk`
- Session pooler port 6543 obligatoire (IPv6)
- 25 tables, 29 293 lignes migrées
- URL (mdp dans secrets Streamlit, prouvé bon) :
  postgresql://postgres.nwvcsqqukgygudbjnryk:MOTDEPASSE@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
- ⚠️ DISJONCTEUR : un seul essai de connexion à la fois, jamais en boucle (sinon blocage ~15 min)

## COUCHE db.py (corrigée en 4 étapes aujourd'hui, toutes poussées)
Traduit SQLite→PostgreSQL à la volée, décision paresseuse à chaque connexion.
Gère : récursion, timing st.secrets, CREATE TABLE (AUTOINCREMENT→SERIAL),
curseur itérable, ALTER TABLE ADD COLUMN IF NOT EXISTS.

## SECRETS STREAMLIT (noms exacts)
DATABASE_URL, YORBITY_SMTP_USER, YORBITY_SMTP_PASS, ADMIN_PASSWORD

## TÂCHES RESTANTES (par priorité)

### 1. LENTEUR (demandé en priorité)
L'app est lente au réveil (plan gratuit Streamlit + Supabase Nano).
Causes : app s'endort après ~15 min sans visiteur ; connexions PG non réutilisées.
Pistes : mettre en cache la connexion via st.cache_resource ; réduire les requêtes
au chargement ; envisager un keep-alive ; option plan payant si trafic.
→ Sonder ui.py pour voir combien de connexions/requêtes au démarrage.

### 2. VOUVOIEMENT + FIN DU RENOMMAGE
Restent en tutoiement/Yorbity : i18n.py (clés "fr"), espace.py, mdp_oublie.py, etc.
Exemples visibles : « Bienvenue sur Yorbity », « Ta trajectoire », « Tes données », « Ton mot de passe ».
⚠️ NE PAS toucher l'espagnol/portugais. Approche sûre : convertir UNIQUEMENT la valeur
derrière la clé "fr": dans i18n.py, et lister explicitement les chaînes FR en dur ailleurs.
→ Il FAUT voir i18n.py réel avant (structure inconnue). Uploader app/api/i18n.py.

### 3. WORKER MAC OLLAMA
Lit les demandes_plan dans Supabase, traite par lots avec Ollama local, écrit le résultat.
Statuts : en_attente → en_cours → pret. Fichiers : file_plans.py, moteur_plans.py.

### 4. app.swimpe.com
CNAME Cloudflare → app Streamlit + brancher les boutons du site vitrine (swimpe.com).

## FICHIERS UTILES DÉJÀ CRÉÉS (dans les livrables des sessions passées)
- db.py (couche corrigée v4) — installé chez Yvan
- swimpe_theme.py — installé chez Yvan (barre util + bande stats + thème CFA)
- Site vitrine : 5 fichiers dans swimpe_site/ (index/chiffres/espace/verifier.html + swimpe.js)

## MÉTHODE DE TRAVAIL
- Sondes lecture seule AVANT tout patch
- Livrables via base64 (increvable au copier-coller, pas d'emoji brut)
- Toujours : sauvegarde auto + vérif syntaxe dans les scripts
- Captures = validation
- Yvan colle dans Terminal ~/mobilite-ia, puis git add/commit/push + reboot Streamlit
- Username GitHub : yvanstephane (+ token classic scope repo)
