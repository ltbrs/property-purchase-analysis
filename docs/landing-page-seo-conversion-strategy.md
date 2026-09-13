# Acquora : stratégie de la page d’accueil et du parcours de conversion

## Objectif et décision de positionnement

La page d’accueil doit donner envie à un acheteur ayant visité un bien de faire examiner ses documents. Le résultat attendu n’est pas seulement un clic sur un bouton : c’est un dossier créé, alimenté avec des pièces exploitables, puis un rapport effectivement consulté.

Le positionnement retenu est : **comprendre ce qui peut changer le budget ou la décision avant de signer**. La catégorie du produit reste explicite : analyse des documents d’un achat immobilier. Les fonctionnalités servent cette promesse, avec un exemple concret et des sources vérifiables.

Ce choix constitue une hypothèse de conversion. Aucune hausse de trafic, de classement ou de transformation n’est encore mesurée. Les requêtes ci-dessous sont des intentions éditoriales, sans volumes de recherche inventés. État du dépôt et sources consultés le 12 septembre 2026.

## Diagnostic initial

La version à reprendre avait un conflit de fusion dans `page.tsx`. Elle opposait une accroche descriptive et une accroche émotionnelle, au risque de perdre les métadonnées, le canonical et les entités de marque existantes.

La recherche avait correctement rejeté le « 50 % des DPE faux », mais la page plaçait trois statistiques complexes avant la démonstration du service. La donnée DPE concernait une suspicion de manipulation sur une période passée, loin de la question immédiate de l’acheteur. Les sources électriques et argiles demandaient une actualisation, et la référence de page du Sénat était décalée.

Le visiteur arrivait ensuite à un CTA vers `/app`, qui nécessite une authentification. Il n’avait pas de chemin immédiat pour examiner la valeur du rapport. L’exemple graphique portait des citations fictives sans mention suffisamment visible de leur caractère illustratif.

Les familles de documents et les objections avant inscription étaient peu présentes. La page ne profitait pas pleinement des deux guides déjà publiés. Le site Tarifs annonçait parallèlement des achats désactivés, ce qui excluait une promesse d’analyse payante immédiatement disponible.

## Parcours implémenté

| Étape | Contenu | Rôle dans la décision |
|---|---|---|
| Arrivée | H1 mentionnant l’achat immobilier, budget et décision dans l’introduction | Comprendre le service en quelques secondes |
| Première action | « Voir un exemple de rapport », ancre publique | Examiner la valeur sans créer de compte |
| Besoin déjà mûr | « Créer mon dossier », lien vers `/app` | Entrer dans le parcours existant de connexion et de dossier |
| Identification du problème | Travaux, budget, diagnostics, informations manquantes | Se reconnaître dans une situation concrète |
| Preuve produit | Trois constats fictifs dépliables, avec limite d’interprétation et question | Comprendre le livrable avant inscription |
| Contexte | ONSE 2025, Sénat 2024, Géorisques 2026 | Montrer pourquoi lire les pièces, sans transférer un taux national au bien |
| Couverture | Huit familles de documents | Confirmer que les documents du visiteur correspondent au produit |
| Fonctionnement | Trois étapes, vidéo optionnelle | Réduire l’incertitude sur la prochaine action |
| Objections | Dossier incomplet, DPE, notaire, tarif et disponibilité | Donner une réponse avant de demander un engagement |
| Préparation | Liens vers les guides documentaires et travaux | Accueillir aussi les visiteurs encore sans dossier |
| Dernière action | Création de dossier et contact | Offrir une suite concrète au parcours |

L’exemple fonctionne avec les éléments HTML natifs `details` et `summary`. Son contenu reste dans le HTML sans JavaScript. Il est explicitement fictif : il ne prétend pas être un rapport généré pour un véritable client. Le dossier de démonstration complet décrit dans `demo-dossier-integration-plan.md` reste un chantier distinct, non implémenté par cette landing.

Le CTA principal conduit à une section de la même page, pas à un faux parcours produit public. Les CTA de création conservent les protections d’authentification existantes. Le statut de préparation et d’achats désactivés est annoncé dans la FAQ et près du dernier CTA. Aucune nouvelle inscription à une liste d’attente ni aucun achat n’est créé.

## SEO : intentions et répartition des pages

| Intention cible | Page qui doit la servir | Angle |
|---|---|---|
| Analyse documents achat immobilier | Accueil | Service, résultat attendu, exemple et entrée dans le produit |
| Vérifier documents avant achat immobilier | Accueil et lien vers guide | Problème acheteur et périmètre du service |
| Documents achat appartement | Guide existant `/blog/documents-achat-appartement` | Checklist détaillée, pièces à demander et sources |
| Travaux votés avant compromis, qui paie | Guide existant `/blog/travaux-votes-avant-compromis` | Explication spécialisée avec contexte de paiement |
| Prix analyse documents immobiliers | `/tarifs` | Offre, limites et disponibilité |
| Comment analyser un dossier immobilier | `/comment-ca-marche` | Parcours détaillé et fonctionnement |

La page d’accueil conserve un titre descriptif, une description propre, l’URL canonique de la racine et les métadonnées de partage. Elle comporte un seul H1 et une hiérarchie de sections lisible. Les données structurées conservent `WebSite` et `Organization`, et ajoutent `WebPage`, reliée aux mêmes identifiants. Aucun avis, note, prix disponible ou validation institutionnelle n’est inventé.

Les recommandations de Google privilégient un contenu utile, des titres descriptifs et des liens compréhensibles. Elles ne justifient ni la répétition artificielle d’un mot-clé ni un allongement de page sans utilité.[^1] Les expressions documentaires sont donc portées par de véritables descriptions, et les liens vers les guides précisent la question à laquelle ils répondent.

La FAQ répond à des objections et enrichit le contenu accessible. Elle n’est pas vendue comme un moyen d’obtenir un résultat enrichi : Google a retiré les résultats enrichis FAQ depuis le 7 mai 2026, puis leur documentation en juin. Aucun schéma `FAQPage` n’a été ajouté dans ce but.[^2]

Le sitemap et les protections `noindex` des pages produit existaient déjà. Il n’est pas nécessaire de les réécrire pour modifier le contenu de l’accueil. Le classement réel, l’indexation du domaine et les requêtes qui apportent des visiteurs devront être évalués dans Search Console après publication.

## Performance, lisibilité et accessibilité

La page reste rendue côté serveur. Seuls les liens de conversion ont un petit composant client pour compter les clics. L’image existante conserve l’optimisation Next.js et un espace réservé ; son indication de taille suit le passage à une colonne à 1088 px. La vidéo est rangée dans une section dépliable avec `preload="none"` et des contrôles manuels.

Les blocs ajoutés utilisent des surfaces et bordures neutres, sans bordure d’accent. Les aperçus et la FAQ sont utilisables au clavier. Le contenu des accordéons est présent sans script et les exemples ne présentent pas une couleur comme seule indication de statut. La largeur et la taille des textes sont vérifiées sur mobile ainsi que sur ordinateur.

Les tests de laboratoire ne démontrent pas des Core Web Vitals réels. Après publication, surveiller les performances de terrain par type d’appareil et la part des visiteurs qui atteignent l’exemple. Ne pas ajouter de widget publicitaire ou de vidéo automatique pour compenser une promesse insuffisamment claire.

## Mesure de la conversion

Le composant `HomeCta` émet **`landing_cta_clicked`** via la fonction `captureProductEvent` de l’intégration PostHog déjà présente. Les propriétés sont strictement éditoriales :

| Propriété | Valeurs |
|---|---|
| `action` | `report_example`, `create_case`, `contact` |
| `placement` | `hero`, `report`, `closing` |

Aucun contenu de document, nom de fichier, adresse du bien ou texte saisi n’est ajouté à cet événement. Les liens fonctionnent sans JavaScript. Cette instrumentation compte une intention, pas une inscription ni un achat.

**Limite opérationnelle :** l’émission utilise la configuration PostHog existante. Si elle est absente, le composant conserve le comportement habituel, sans collecte. Le contrôle local peut vérifier l’appel et ses propriétés, mais ne prouve pas sa réception dans le tableau de bord de production. Aucun changement d’identification, de consentement ou d’enregistrement de session n’est introduit.

Indicateurs à suivre après publication :

1. Sessions sur l’accueil, par provenance et appareil.
2. Clics vers l’exemple et clics de création, distingués par emplacement.
3. Authentifications abouties et créations réelles de dossiers.
4. Dossiers contenant un premier document exploitable.
5. Rapports consultés et, une fois les achats activés, analyses payées.

Les étapes produit utilisent déjà PostHog. Le clic de la landing peut donc être étudié dans le même outil que `analysis_case_created`, sans ajouter de rapprochement entre Vercel et PostHog. L’identification et la réinitialisation à la déconnexion restent celles du produit. L’attribution complète après OAuth et la qualité des événements en production doivent être validées avant de publier un taux de transformation.

Un clic sur l’exemple n’est pas une preuve de lecture. La comparaison essentielle porte sur les utilisateurs qui alimentent un dossier après leur passage sur l’accueil. Un meilleur taux de clic accompagné de moins de dossiers utiles serait un recul.

## Expérimentations et prochaines priorités

La première expérience à envisager est le choix du CTA principal : exemple public ou création de dossier. Attendre une période de référence, répartir les visiteurs comparables et définir à l’avance le résultat principal, idéalement un premier document exploitable. Sans trafic ou taille d’effet cible, annoncer une durée ou un nombre de conversions nécessaire serait arbitraire.

La seconde expérience peut comparer une accroche centrée sur le budget avec celle centrée sur la décision. Conserver le reste de la page pendant cette comparaison. Les statistiques ne doivent pas varier avec les versions au point de rendre le résultat impossible à interpréter.

Les priorités suivantes sont : vérifier l’activation réelle et les frictions après connexion, synchroniser les tarifs à l’ouverture, disposer d’une démonstration complète fidèle au produit, puis développer des contenus spécialisés à partir des requêtes Search Console et questions clients. Les sujets DPE, PV d’AG et charges sont des pistes ; ils ne constituent pas un calendrier SEO fondé sur des volumes validés.

Le contenu de recherche complet et les limites de chaque chiffre sont conservés dans [la note sur les risques documentaires](landing-page-document-risk-research.md). Les deux guides existants ne sont pas réécrits dans ce changement.

## Validation de l’implémentation

Contrôles terminés lors de la finalisation du 13 septembre 2026 :

- `npm run build` : compilation, TypeScript et génération statique réussis.
- `npm run lint` : réussi.
- Chrome : largeurs 320, 390, 768, 1080, 1366 et 1920 px, sans débordement horizontal détecté.
- Axe : aucune violation détectée sur le contenu de l’accueil pour les règles WCAG 2 A/AA et 2.1 AA testées. Cela ne remplace pas un audit manuel complet.
- Exemple de rapport et FAQ : ouverture des détails vérifiée ; l’ancre atteint le rapport sous le bandeau de navigation.
- Sans JavaScript : titre, huit familles de documents et cinq réponses de FAQ présents.
- Liens internes de l’accueil : réponses HTTP 200, avec redirection attendue de `/app` vers `/connexion` pour un visiteur anonyme.
- Métadonnées : un H1, canonical de la racine et JSON-LD lisible.
- PostHog : raccordement du composant vérifié dans le code, mais émission et réception de l’événement non confirmées par le contrôle navigateur. Les visites locales ne démontrent pas une collecte de production.

Les contrôles n’incluent ni une authentification OAuth réelle, ni un envoi de document, ni un achat. Aucun déploiement ni test A/B n’a été effectué.

## Sources

[^1]: Google Search Central, [SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide), documentation consultée le 12 septembre 2026.
[^2]: Google Search Central, [Documentation updates](https://developers.google.com/search/updates), entrées du 8 mai et du 15 juin 2026 concernant la suppression des résultats enrichis FAQ.
