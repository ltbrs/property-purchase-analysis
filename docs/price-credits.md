Je pense que ton unité commerciale ne doit être **ni le PDF, ni le nombre de dossiers**, mais **l’analyse d’un bien immobilier**, avec une limite technique suffisamment généreuse pour que l’utilisateur n’ait presque jamais à y penser.

Pour Acquora, j’éviterais donc un système visible du type « 100 crédits » où chaque PDF/page consomme des crédits. C’est cohérent techniquement, mais assez mauvais côté UX : l’acheteur veut savoir « combien me coûte l’analyse de cet appartement ? », pas calculer combien de crédits va coûter son règlement de copropriété de 180 pages.

### Le modèle que je privilégierais

Je partirais sur quelque chose comme :

| Offre                      | Prix indicatif | Contenu                       |
| -------------------------- | -------------: | ----------------------------- |
| **Analyse d'un bien**      |       **19 €** | 1 bien, jusqu'à ~500 pages    |
| **Pack recherche**         |       **39 €** | 3 analyses de biens           |
| **Analyse supplémentaire** |       **15 €** | 1 analyse supplémentaire      |
| **Pro / illimité**         |      plus tard | agences, chasseurs, courtiers |

Le point important est que **« 1 analyse » = 1 bien**, et non « 1 dossier figé après upload ».

L'utilisateur achète par exemple une analyse à 19 €, crée `Appartement rue de Reuilly`, puis peut y ajouter DPE, PV d'AG, règlement de copropriété, diagnostics, taxe foncière, etc. Tant qu'il s'agit du même bien, **cela ne consomme pas une nouvelle analyse**.

C'est beaucoup plus facile à comprendre :

> **1 crédit = l'analyse complète d'un bien immobilier**

Tu peux même cacher complètement le mot *crédit* sur la landing page et parler de **« 1 analyse »**.

---

### Mais ton problème de taille reste réel

Il faut dissocier **pricing utilisateur** et **metering interne**.

En interne, tu mesures par exemple :

`pages parsées + pages OCR + tokens LLM + stockage + nombre de réanalyses`

Mais tu ne présentes pas cette complexité au client.

Je mettrais une fair-use limit du genre **500 pages par bien**, éventuellement 1 000 si tes coûts le permettent. Ça couvre largement la majorité des cas tout en empêchant quelqu'un d'uploader 12 000 pages.

Et surtout, je ne limiterais **pas le nombre de fichiers**. 5 PDF de 100 pages ou 50 PDF de 10 pages devraient être équivalents.

Techniquement, tu peux donc avoir :

```text
AnalysisCredit
    property_id
    user_id
    status
    activated_at
    page_count
    ocr_page_count
    llm_tokens
```

avec quelque chose comme :

```text
MAX_PAGES_PER_PROPERTY = 500
MAX_FILE_SIZE = 100 MB
MAX_TOTAL_STORAGE = 1 GB
```

Les limites servent surtout d'anti-abus.

---

### Et surtout : ne consomme pas le crédit au moment de créer le dossier

C'est un détail UX important.

Imagine :

1. Je crée « Appartement Vincennes »
2. J'uploade le DPE.
3. J'ajoute les PV d'AG.
4. Je réalise que j'ai oublié le règlement de copropriété.
5. Je reviens demain et je l'ajoute.

Ça doit toujours être **la même analyse**.

Je ferais donc plutôt :

**Création du dossier → gratuite**
**Upload des documents → gratuit éventuellement jusqu'au lancement**
**Lancer l'analyse complète → consomme 1 analyse**

Ensuite, les nouveaux documents ajoutés à ce même bien peuvent être analysés sans reprendre un crédit, dans une certaine fenêtre.

Par exemple :

> Analyse valable **30 jours pour un même bien**, documents ajoutables librement dans la limite de 500 pages.

C'est particulièrement cohérent avec le parcours immobilier : les documents arrivent souvent progressivement.

---

### Pourquoi le pack de plusieurs analyses reste intéressant

Tu as raison sur un point : si tu autorises énormément de fichiers dans un dossier, **« 3 dossiers » n'est pas naturellement un upsell**.

Mais il le devient si tu présentes le produit autrement.

L'utilisateur ne pense pas :

> « J'ai besoin d'analyser 47 PDF. »

Il pense :

> « J'hésite entre trois appartements. »

Donc :

**19 € — Je vérifie un bien**
Analyse complète avant de faire mon offre.

**39 € — Je cherche activement**
Analyse de jusqu'à 3 biens.

À mon sens, le deuxième produit est même potentiellement ton **offre principale**. Quelqu'un en phase d'achat peut visiter et considérer plusieurs biens avant de faire une offre.

Le prix unitaire passe de 19 € à 13 €, ce qui donne une vraie raison d'acheter le pack sans te forcer à rationner artificiellement les documents.

---

### Il y a aussi une mécanique intéressante : le dossier gratuit

Pour l'acquisition, je testerais quelque chose d'encore plus malin.

Tu laisses gratuitement :

**Upload → inventaire des documents → détection des documents manquants → quelques informations de base.**

Puis :

> **Débloquer l'analyse complète — 19 €**

pour obtenir risques copropriété, travaux votés/envisagés, DPE, anomalies diagnostics, charges, points d'attention, questions à poser au vendeur/notaire, synthèse avant offre, etc.

Tu fais ainsi comprendre la valeur **avant le paywall**.

Et ça résout un problème important d'un système de crédits : demander à quelqu'un de payer avant même qu'il sache si Acquora comprend correctement ses documents.

---

### Ce que je lancerais pour le MVP

Je ferais extrêmement simple :

**Gratuit** → création du bien + upload + identification des documents + aperçu.

**19 € / analyse** → analyse complète d'un bien, limite fair-use de ~500 pages.

**39 € / Pack 3 analyses** → trois biens, valables par exemple 12 mois.

Pas d'abonnement B2C. Pas de crédits à la page. Pas de tarification au PDF. Pas de 5 plans différents.

Et dans ton backend, **tu mesures quand même précisément le coût réel par dossier** dès le premier jour. Après tes 50–100 premiers dossiers, tu auras la distribution réelle : médiane de pages, P90/P99, coût OCR, coût LLM, stockage et nombre de réanalyses. À ce moment-là, tu pourras ajuster la limite de 500 pages et les prix avec des données réelles.

Le principe central serait donc : **l'utilisateur achète le droit d'analyser un bien ; Acquora absorbe la variabilité documentaire à l'intérieur de ce bien.** C'est à mon avis beaucoup plus naturel pour ton produit que de vendre des PDF ou des crédits techniques.
