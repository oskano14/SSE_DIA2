# Note éthique : biais, RGPD et limites d'usage

## 1. Biais possibles des modèles par région

**Modèle de retard** ([notebook 03](../notebooks/03_delay_model.ipynb), section 6) :

- **Constat.** On prend le seuil opérationnel, qui consiste à alerter sur les 10 % de commandes les plus risquées.
  - Les clients du **Nordeste** reçoivent **2,7 fois plus d'alertes** que ceux du Sudeste (21 % contre 8 %).
  - Ils ont aussi **2,8 fois plus de fausses alertes** : 18 % des commandes livrées à l'heure y sont signalées à tort, contre 6 % dans le Sudeste.
- **Origine.** Le modèle reproduit une **inégalité réelle de service** : le délai moyen est de 20 jours dans le Nordeste, contre 11 dans le Sudeste. Il ne s'agit pas d'un défaut de calcul. L'État du client n'est pas une variable du modèle, mais la distance au vendeur en est un fort substitut.
- **Risque.** Si l'on utilisait la prédiction pour **restreindre** le service, on pénaliserait une population déjà moins bien servie. Exemples : majorer le port, refuser l'express, ou allonger la date promise.
- **Atténuations retenues :**
  - l'usage est réservé à des actions **protectrices** (voir la section 3) ;
  - l'équité est suivie par région à chaque ré-entraînement (taux d'alerte, rappel, faux positifs) ;
  - on peut ajouter un seuil par région si l'on veut égaliser les faux positifs.

**Modèle de sentiment** : son taux d'erreur est un peu plus élevé dans le Nordeste et le Nord (7,6 % et 7,1 %) que dans le Sud (5,1 %). Le rappel des avis négatifs y est de 91 %, contre 96 %. L'hypothèse la plus probable est la variation régionale du vocabulaire, avec moins d'exemples d'apprentissage hors Sudeste. L'écart reste modéré, mais il faut le suivre : sous-détecter les plaintes d'une région, c'est la servir moins bien.

**Segmentation RFM** : elle dépend du montant dépensé. Les régions aux paniers plus faibles risquent d'être moins ciblées par les offres. Les campagnes doivent donc être évaluées par région.

## 2. Conformité RGPD des données clients

Les données Olist concernent des clients brésiliens, qui relèvent de la **LGPD**, la loi brésilienne proche du RGPD. On applique les principes du RGPD, comme si ShopPulse opérait en Europe.

| Principe | Application dans le projet |
|---|---|
| **Minimisation** | Pas de nom, d'e-mail, d'adresse complète ni de téléphone. Seuls un identifiant pseudonymisé (hash), le **préfixe** du code postal (5 chiffres), la ville et l'État sont conservés. |
| **Pseudonymisation** | `customer_unique_id` est un hash. C'est une donnée **pseudonymisée et non anonyme** : elle reste personnelle au sens du RGPD. |
| **Sécurité** | Les données complètes ne sont **jamais versionnées** (`data/raw/` est ignoré par git, seul un échantillon de moins de 1 Mo l'est). Les identifiants de la base sont dans `.env`, non versionné. La base n'est accessible qu'en local. |
| **Finalité et base légale** | Pour la logistique (prédire le retard), la base légale est l'**intérêt légitime** et l'exécution du contrat. Pour les campagnes marketing (personas), il faut un **consentement** préalable à la prospection par e-mail, et seuls les clients ayant accepté sont ciblés. |
| **Transparence et droits** | Les clients sont informés du profilage marketing (art. 13-14). Le **droit d'opposition** au profilage est respecté (art. 21) : un client opposé sort des segments. |
| **Décision automatisée** (art. 22) | Aucune décision produisant un effet juridique ou significatif n'est prise **sans intervention humaine**. Les prédictions aident un opérateur, elles ne tranchent pas. |
| **Conservation** | Les données sont gardées 3 ans après le dernier achat pour le marketing. Au-delà, elles sont supprimées ou agrégées. |
| **Textes des avis** | Ils peuvent contenir des données personnelles saisies librement par le client (nom, téléphone). Ils sont traités **en interne** : aucune API de traduction externe n'est utilisée, ce qui évite un transfert à un tiers. |

## 3. Limites d'usage des prédictions

**Usages autorisés :**
- prioriser le suivi d'une commande à risque (transporteur, appel au vendeur) ;
- prévenir le client d'un retard probable ;
- trier les avis négatifs pour que le service client les traite en premier ;
- cibler des offres auprès de clients ayant consenti.

**Usages proscrits :**
- refuser une vente, majorer le prix ou dégrader le service selon le score de retard, et donc indirectement selon la région ;
- sanctionner automatiquement un vendeur sur la seule base du modèle ;
- supprimer ou masquer un avis parce qu'il est négatif.

**Limites techniques à rappeler à chaque utilisateur :**
- **Modèle de retard.** Sa PR-AUC n'est que de 0,23. La plupart des alertes sont de fausses alertes (précision d'environ 25 % au seuil opérationnel), et 63 % des retards ne sont pas signalés. C'est un **outil de priorisation**, pas une certitude.
- **Dérive.** Les données s'arrêtent en 2018, et les performances baissent sur une période future (PR-AUC de 0,16). Il faut ré-entraîner et surveiller le modèle chaque mois.
- **Sentiment.** Les étiquettes viennent des notes, qui sont parfois contradictoires avec le texte. Les avis neutres sont exclus, et ni l'ironie ni les avis mixtes ne sont bien traités.
- **Personas.** Les gains annoncés reposent sur des **hypothèses de conversion** à valider par un test A/B avant tout engagement budgétaire.
