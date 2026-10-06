# Fallback de lecture pour les pages scannées

## Résumé

Conserver Xberg comme premier parseur. Lorsqu’une page contient visiblement du contenu mais fournit peu ou pas de texte, envoyer **cette page seule** à `gpt-6-luna` pour une transcription contrôlée. Le modèle accepte les images via l’API Responses, selon la [documentation officielle OpenAI](https://developers.openai.com/api/docs/models/gpt-6-luna).

## Changements

- **Détection et extraction :** comparer le nombre de pages Xberg à celui du PDF, puis examiner les pages sans texte exploitable par rendu à résolution bornée. Écarter les pages blanches ; demander à Luna si du texte est lisible et, si oui, sa transcription structurée. Conserver pour chaque page le numéro, la méthode d’extraction et son état. Ne jamais compléter un passage illisible par supposition.
- **Traitement persistant :** enregistrer la progression en base. `POST /process` devient idempotent et répond `202` après mise en file ; un traitement par lots reprend les pages et les étapes d’analyse. Supabase Cron déclenche chaque minute un endpoint FastAPI protégé, avec réservation des tâches et reprise après interruption. Cette cadence est prise en charge par [Supabase Cron](https://supabase.com/docs/guides/cron) ; elle évite de dépendre de la cadence quotidienne de Vercel Hobby décrite dans sa [documentation](https://vercel.com/docs/cron-jobs/usage-and-pricing).
- **Limites et interface :** borner à 100 pages de fallback par document et à quatre pages par lot, avec au plus trois tentatives par page. Pour les erreurs temporaires `429` ou `503`, enregistrer la prochaine tentative, respecter `Retry-After` et ajouter un délai aléatoire, conformément à la [documentation officielle OpenAI](https://developers.openai.com/api/docs/guides/rate-limits). Exposer étape, progression, prochaine tentative et pages non lues dans `DocumentRead`. Le frontend interroge ces états, les retrouve après rechargement et affiche une attente ou une alerte claire.
- **Rapport et traçabilité :** les pages définitivement illisibles restent explicitement signalées dans le rapport. L’analyse continue sur les pages exploitables, sans conclusion rassurante fondée sur les pages manquantes. Mettre à jour le compteur de pages lues par vision et l’intitulé de l’extraction brute.

## Vérification

Tester les PDF textuels, mixtes, scannés, blancs et illustrés ; les numéros de page et citations ; les `429` avec et sans `Retry-After` ; l’épuisement des tentatives ; la reprise après interruption et les appels `/process` répétés. Vérifier que le frontend affiche la progression et l’alerte après rechargement.

## Hypothèses

Le traitement peut démarrer à la prochaine minute du planificateur. Les plafonds proposés sont configurables. Les documents et images restent privés ; seuls les clichés des pages candidates sont transmis à OpenAI.

## Implémentation

- [x] Inspection déterministe des pages réelles, blancs exclus, pages manquantes reconstituées.
- [x] Transcription structurée page par page avec `gpt-6-luna` et conservation des citations.
- [x] File persistante, réservation atomique, reprise après expiration et `/process` idempotent en `202`.
- [x] Premier lot immédiat, quatre lectures concurrentes, résultats persistés, appels réussis conservés.
- [x] Budget partagé de requêtes, tokens et concurrence, `Retry-After`, retries bornés et délais persistés.
- [x] Progression frontend après rechargement, attente automatique et pages incomplètes signalées.
- [x] Constat déterministe dans le rapport et exclusion des éléments rassurants des documents incomplets.
- [x] Migration, endpoint interne protégé et script de configuration Supabase Cron.

La configuration de production (migration, secret et Cron) accompagne le déploiement.
Les étapes sont détaillées dans [la documentation de traitement](docs/document-processing.md).
