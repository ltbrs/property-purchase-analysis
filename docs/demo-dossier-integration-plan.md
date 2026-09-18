# Intégration du dossier de démonstration

## Architecture retenue

Le dossier Lyon est un dossier global partagé, analysé une seule fois par environnement. Il utilise les tables, les modèles Pydantic, Xberg, les extractions structurées, les règles déterministes et l'assembleur de rapport du produit.

Une démo publiée est visible par défaut pour tous les utilisateurs authentifiés. Elle est toujours renvoyée après les dossiers personnels, avec `case_kind = "demo"`, `read_only = true` et un accès d'analyse `active`. Elle ne crée ni accès payant ni consommation de crédit.

Chaque utilisateur conserve uniquement la préférence `users.show_demo_case`. La désactivation masque la démo des listes, sans supprimer ses données et sans révoquer son accès direct.

## Documents inclus

La sélection est définie dans `backend/app/demo/config.py`. La version `lyon_v1` utilise actuellement :

- 02, règlement de copropriété et EDD ;
- 03, 04 et 05, procès-verbaux d'AG 2024 à 2026 ;
- 09, appel de fonds travaux toiture ;
- 11, conclusions du DTG et PPPT ;
- 12, DPE ;
- 14, état des risques, termites et bruit ;
- 15, taxe foncière.

Toute modification de cette sélection change l'empreinte calculée. Une version déjà créée avec une autre empreinte doit recevoir une nouvelle clé, par exemple `lyon_v2`.

## Préparation et publication

Après application de la migration, préparer la démo depuis la racine du dépôt :

```bash
cd backend
uv run python -m app.demo.seed \
  --manifest ../docs/demo-dossier-lyon/manifest.json \
  --template-key lyon_v1 \
  --publish
```

La commande est idempotente. Elle valide le manifeste, les tailles, les empreintes et les signatures PDF, envoie les objets dans le stockage privé sous `demo-templates/lyon_v1/<sha256>.pdf`, reprend les traitements incomplets, contrôle la pagination extraite et les pages citées, génère le rapport, puis publie le dossier.

Sans `--publish`, le dossier reste un brouillon invisible. Un échec conserve également un brouillon reprenable. Aucun seed n'est exécuté au démarrage de FastAPI.

## Lecture seule et sécurité

Les lectures d'une démo publiée sont autorisées à tout utilisateur authentifié. Les documents restent dans le bucket privé et sont servis par les URLs signées existantes.

Toutes les mutations du dossier démo renvoient `409` avec le message « Ce dossier de démonstration est en lecture seule. » Cela couvre le type de bien, l'upload, la suppression, les traitements manuels, le recalcul du rapport, la revue des constats et l'activation payante.

L'interface masque ces contrôles et affiche toujours un badge ou un bandeau textuel. La carte utilise la surface neutre `--demo-surface`, sans bordure d'accent.

## Déploiement

1. Appliquer la migration Alembic `1c439cb1ee8b`.
2. Déployer le backend et le frontend.
3. Exécuter la commande sans `--publish` en préproduction.
4. Contrôler le rapport, les PDF et les citations.
5. Relancer avec `--publish`.
6. Répéter en production.

Pour masquer immédiatement la démo à tous les utilisateurs, remettre `published_at` à `NULL` sur sa ligne. Les données et objets peuvent rester en place pour une republication.
