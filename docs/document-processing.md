# Lecture persistante des documents et fallback vision

`POST /api/v1/analysis-cases/{case_id}/documents/{document_id}/process` répond
`202` dès que la tâche est enregistrée. Répéter cette requête laisse les tâches
actives et les documents terminés intacts. Une première exécution démarre dans
une tâche de fond FastAPI, avec une session indépendante. Le Cron reprend le
travail restant chaque minute, même si le navigateur est fermé.

## Détection et traçabilité

Xberg reste le premier parseur. PDFium fournit le nombre réel de pages et
complète les pages absentes de sa sortie. Les pages qui contiennent moins de
40 caractères alphanumériques, tableaux compris, sont examinées à faible
résolution. Une page qui ne contient qu’un court pied de page (moins de 200
caractères), avec une image occupant plus de la moitié de sa surface, est aussi
candidate. La différence avec le fond de la page écarte les pages visuellement
blanches, y compris les fonds gris uniformes de scans.

Chaque candidate est rendue séparément, avec un côté maximal de 2048 pixels,
puis envoyée à `gpt-6-luna` via Responses. La réponse structurée et validée
distingue texte, illustration sans texte et texte illisible. Les transcriptions
restent attachées au numéro original de page. Les images sont temporaires,
en mémoire, et seuls les clichés candidats sont envoyés pour la lecture visuelle.
La classification et l’analyse continuent à recevoir le texte extrait, comme
auparavant. Aucun nouveau bucket ou fichier public n’est créé.

Les pages portent `extraction_method` (`xberg`, `vision`), `read_status`, un
nombre de tentatives et les métadonnées de consommation OpenAI. Les passages
partiellement illisibles, les échecs et les pages au-delà du plafond produisent
le constat déterministe `UNREAD_DOCUMENT_PAGES`, sourcé au document et aux pages.
Les éléments rassurants de ces documents incomplets sont supprimés du rapport.

## Reprise et limites

Les tâches utilisent une réservation atomique avec `FOR UPDATE SKIP LOCKED`,
un jeton et une échéance. Les pages et chaque étape d’analyse sont persistées
avant de poursuivre. Une réservation expirée est récupérable. Les images ne
sont pas mises en cache sur disque ; une reprise peut refaire un rendu local,
mais conserve les transcriptions déjà enregistrées.
Les anciennes extractions réutilisées pendant une reprise sont inspectées une
première fois. Si elles contiennent des pages candidates, leurs anciennes
analyses structurées sont invalidées pour intégrer le texte récupéré.

Le budget `llm_rate_budgets`, inaccessible aux rôles Data API, partage entre
instances le nombre de requêtes, les tokens réservés, les appels simultanés et
les périodes de refroidissement. Les tokens sont estimés de façon conservatrice
avant l’appel, puis remplacés par la consommation reçue. Adapter les paramètres
aux limites réellement attribuées au projet OpenAI. Ce budget concerne le
traitement persistant utilisé par le frontend ; les anciennes routes manuelles
d’analyse restent disponibles pour les documents sans tâche active.

Les retries internes du SDK sont désactivés. Les `429`, erreurs temporaires
serveur et erreurs de connexion sont reportées sans attente bloquante. Les
en-têtes `Retry-After` (secondes ou date HTTP) et `retry-after-ms` sont respectés,
avec un backoff et une variation aléatoire. Le quota de facturation épuisé et les
erreurs d’authentification arrêtent le traitement. Une attente avant admission
ne consomme pas une tentative de page. Les appels interrompus après admission
comptent, afin de borner les coûts après des interruptions répétées.

Valeurs par défaut, configurables dans `.env` :

| Variable | Valeur | Effet |
| --- | --- | --- |
| `PROCESSING_BATCH_SECONDS` | 45 | Temps d’un lot de travail |
| `PROCESSING_LEASE_SECONDS` | 180 | Reprise après interruption |
| `VISION_MAX_PAGES` | 100 | Candidates vision autorisées par document |
| `VISION_BATCH_PAGES` | 4 | Pages lancées simultanément par lot |
| `VISION_MAX_ATTEMPTS` | 3 | Tentatives par page et par étape en erreur |
| `OPENAI_TIMEOUT_SECONDS` | 35 | Timeout d’un appel au fournisseur |
| `OPENAI_MAX_CONCURRENCY` | 4 | Appels actifs partagés entre instances |
| `OPENAI_REQUESTS_PER_MINUTE` | 60 | Budget de requêtes |
| `OPENAI_TOKENS_PER_MINUTE` | 200000 | Budget de tokens |

L’inspection refuse les PDF de plus de 2000 pages. Les requêtes dont le budget
de tokens estimé dépasse à lui seul le plafond configuré sont arrêtées. Le
timeout du lot annule les appels async ; les bibliothèques natives exécutées
dans un thread peuvent terminer leur opération locale avant de libérer ce thread.

## Mise en service

1. Installer les dépendances du backend avec `uv sync`, puis appliquer la
   migration avec `uv run alembic upgrade head` sur l’environnement de déploiement.
2. Définir `PROCESSING_CRON_SECRET` sur le backend, avec un secret long généré
   localement. Déployer le backend et le frontend ensemble, car la réponse de
   `/process` est maintenant asynchrone.
3. Activer Cron et `pg_net` dans Supabase. Dans Vault, créer
   `acquora_processing_endpoint`, contenant l’URL HTTPS du backend suivie de
   `/api/v1/internal/document-processing`, et `acquora_processing_secret`, avec
   la même valeur que `PROCESSING_CRON_SECRET`.
4. Exécuter [le script Cron](../backend/scripts/document_processing_cron.sql).
   Le nom stable permet de remplacer la configuration sans créer un second job.
   Le secret est lu depuis Vault à chaque exécution, sans le copier dans
   `cron.job.command`.
5. Vérifier le résultat d’une invocation dans `net._http_response`, les
   exécutions dans `cron.job_run_details`, puis un document en attente dans
   le frontend. L’endpoint retourne `processed_documents` et rejette une requête
   sans le Bearer secret dédié.

La tâche de fond immédiate accélère les petits documents. Elle ne remplace pas
le planificateur durable, notamment sur un runtime serverless. Avec la cadence
par défaut, une reprise peut attendre jusqu’à la minute suivante. Le frontend
interroge les états toutes les trois secondes, ralentit en cas de problème réseau
ou dans un onglet masqué, et retrouve la progression après rechargement.

## Validation et références

Les tests utilisent des PDF textuels et des PDF réellement constitués d’images,
avec faux appels fournisseur. Ils couvrent les pages omises, blanches et
illustrées, les pieds de page, les plafonds, les citations, les `429`, le budget
partagé, les réservations expirées, les lots interrompus, l’idempotence de
`/process`, l’authentification du Cron et les avertissements dans le rapport.
Ils n’évaluent pas la précision OCR du modèle réel sur des documents clients.
La commande explicite `uv run python -m evals.run_vision_evals` fournit un jeu
de pages synthétiques pour mesurer rappel des montants/dates, latence et tokens
avec le modèle réel. Cette évaluation est distincte des tests unitaires et
nécessite `OPENAI_API_KEY`.

Sources officielles : [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna),
[images](https://developers.openai.com/api/docs/guides/images-vision),
[limites API](https://developers.openai.com/api/docs/guides/rate-limits),
[Supabase Cron](https://supabase.com/docs/guides/cron),
[pg_net](https://supabase.com/docs/guides/database/extensions/pg_net),
[Vault](https://supabase.com/docs/guides/database/vault),
[PDFium et threads](https://pypdfium2.readthedocs.io/en/stable/python_api.html).
