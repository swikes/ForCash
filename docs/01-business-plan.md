# ScolaPay — Business plan

> **Nom de travail.** Avant de l'imprimer sur un flyer, vérifier la disponibilité du nom et le déposer à l'OAPI (un seul dépôt protège la marque dans ses 17 pays membres).
>
> Version : octobre 2026 · Marché de départ : Côte d'Ivoire (Abidjan), puis Afrique francophone.

---

## 1. Résumé en une page

**Ce que fait ScolaPay.** ScolaPay aide les écoles privées à **encaisser leurs frais de scolarité** : échéancier par classe, relances WhatsApp en un clic, paiement par mobile money, reçus numérotés avec QR code anti-fraude et tableau de bord en temps réel pour le fondateur.

**Le problème.** Dans une école privée, la scolarité, c'est presque tout le chiffre d'affaires. Pourtant elle se gère encore souvent avec un cahier, un fichier Excel et une caisse en espèces. Résultat : des retards de paiement qui mettent en difficulté la paie des enseignants, des heures passées à relancer, des reçus perdus ou contestés, et parfois de l'argent qui disparaît entre la caisse et le coffre.

**Pourquoi maintenant.**
- Le privé pèse très lourd : en Côte d'Ivoire, **76,6 % des établissements du secondaire général sont privés et accueillent 64 % des élèves** ([source](https://www.agenceecofin.com/actualites-services/2205-138688-education-en-cote-d-ivoire-le-secteur-prive-face-au-controle-de-l-etat)), soit de l'ordre de 3 000 établissements privés.
- Les parents paient déjà tout par mobile money. Wave facture environ 1 % aux marchands ([source](https://kolonell.com/fr/blog/wave-cote-ivoire-integration-marchand-abidjan-2026)).
- WhatsApp est le canal naturel entre l'école et les familles.
- L'État lui-même numérise les paiements scolaires : l'inscription en ligne au secondaire se paie via Wave ([source](https://digitalmag.ci/comment-payer-les-frais-dinscription-lycee-et-college-avec-wave-cote-divoire/)). Les parents y sont habitués.

**Qui paie et combien.** L'école paie un abonnement par élève et par an : **500 FCFA** (Essentiel) ou **1 000 FCFA** (Recouvrement+), soit moins de 1 % des frais de scolarité. S'y ajoutent des services : mise en place, cartes scolaires et, plus tard, une commission sur les paiements en ligne.

**Objectifs (scénario de base).** 40 écoles à la fin de l'an 1, 180 à la fin de l'an 2 et 500 à la fin de l'an 3, réparties sur 3 pays. Cela représente environ **175 millions de FCFA de revenu annuel récurrent** à la fin de l'an 3, avec un résultat positif dès la première année (détails au §11).

**Mise de départ.** 0,5 à 1,5 million de FCFA. L'application existe déjà (elle est dans ce dépôt) : l'argent sert à vendre, pas à développer.

**Le facteur clé de succès.** Vendre sur le terrain, fournir un service irréprochable aux 20 premières écoles et en tirer des témoignages chiffrés.

---

## 2. Le problème, en détail

### Pour le fondateur ou la direction

| Douleur | Ce que ça coûte |
|---|---|
| **Impayés et retards** | Trésorerie tendue en fin de mois, salaires des enseignants payés en retard, et des montants qui ne sont jamais récupérés. |
| **Relances manuelles** | La secrétaire passe des heures à téléphoner. On ne sait jamais qui a été relancé, ni quand. |
| **Fraude à la caisse** | Reçus de complaisance, espèces encaissées sans être enregistrées. Le fondateur souvent absent n'a aucun moyen de contrôle. |
| **Aucune visibilité** | « Combien a-t-on encaissé cette semaine ? Qui doit encore la 1re tranche ? » Il faut des heures pour répondre. |
| **Litiges** | « J'ai déjà payé ! » Le parent a perdu son reçu, l'école a perdu sa trace. |

### Pour le parent

- Il doit se déplacer et faire la queue pour payer, souvent en espèces.
- Il ne connaît pas toujours le montant exact qui reste à payer.
- Il reçoit des reçus papier qui se perdent.
- Il aimerait payer petit à petit, par mobile money, au moment où il a l'argent.

### Hypothèses à valider sur le terrain

Les **20 premiers entretiens** (voir le [kit commercial](03-kit-commercial.md)) doivent permettre de chiffrer :

1. la part des frais exigibles qui n'est pas encaissée à temps (taux de recouvrement actuel) ;
2. le temps consacré chaque semaine aux relances et à la caisse ;
3. l'existence de cas de fraude ou de litiges dans l'année ;
4. le consentement à payer : 500 ou 1 000 FCFA par élève et par an, est-ce accepté ?

> Si moins de 5 écoles sur 30 se disent prêtes à tester, il faut revoir le positionnement (voir les règles d'arrêt dans le [plan 90 jours](02-plan-90-jours.md)).

---

## 3. La solution

ScolaPay est une application web : elle fonctionne sur n'importe quel téléphone ou ordinateur, sans installation. Elle est dans ce dépôt et déjà utilisable.

| Fonction | Ce que ça change pour l'école |
|---|---|
| **Barèmes et échéanciers** (inscription, tranches, remises) | Chaque élève a un solde exact et à jour. |
| **Tableau de bord** : taux de recouvrement, impayés par classe, encaissements du jour, du mois et par mode de paiement | Le fondateur suit tout depuis son téléphone, où qu'il soit. |
| **Relances WhatsApp en un clic** : le message est déjà rédigé avec le montant, l'échéance et un lien de paiement | Une relance prend 5 secondes au lieu de 5 minutes, et chacune est tracée. |
| **Reçus numérotés avec QR code**, envoyés au parent sur WhatsApp | Les fausses quittances et les litiges disparaissent. Un reçu ne peut pas être supprimé : seule la direction peut l'annuler, avec un motif. |
| **Journal de caisse** par caissier et par mode de paiement | Le contrôle du soir prend 2 minutes. |
| **Espace parent** (lien personnel) : solde, échéancier, reçus | Moins d'appels au secrétariat et des parents rassurés. |
| **Paiement en ligne par mobile money** (via un agrégateur) | Le parent paie à 22 h depuis chez lui. L'argent arrive sur le compte marchand de l'école. |
| **Import Excel, réinscriptions, années scolaires** | Une école est opérationnelle en 48 heures. |

**Ce que ScolaPay ne fait pas (volontairement).** Pas de bulletins de notes, d'emplois du temps ni de gestion des enseignants. L'école garde ses outils pour la pédagogie. ScolaPay se concentre sur une seule chose : **faire rentrer l'argent**. C'est ce qui le différencie des logiciels de gestion scolaire complets, qui sont nombreux et vendus bon marché.

**Feuille de route du produit (selon les retours des clients).**
1. Relances SMS automatiques programmées (J-3, J+1, J+7) par un fournisseur de SMS local.
2. Rapport hebdomadaire automatique envoyé au fondateur sur WhatsApp ou par e-mail.
3. Groupes scolaires multi-sites, avec une vue consolidée.
4. Autres frais : cantine, transport, tenues, fournitures.
5. Cartes scolaires avec QR code (impression sous-traitée, revendue avec marge).
6. Paiement fractionné financé par un partenaire agréé (microfinance ou banque), rémunéré par une commission d'apport.

---

## 4. Le marché

### Côte d'Ivoire (marché de départ)

- **Secondaire général** : 76,6 % des établissements sont privés et accueillent 64 % des élèves ([source](https://www.agenceecofin.com/actualites-services/2205-138688-education-en-cote-d-ivoire-le-secteur-prive-face-au-controle-de-l-etat)), soit de l'ordre de 3 000 établissements privés. Il y a plus de 3 établissements privés pour 1 public (chiffres détaillés sur les [données ouvertes du ministère](https://data.gouv.ci/datasets/statistiques-de-lenseignement-secondaire-entre-2008-et-2018)).
- **Primaire** : environ 19 900 écoles (public et privé) et plus de 4,8 millions d'élèves en 2023-2024. Il faut y ajouter le préscolaire et l'enseignement technique privé.
- **Cœur de cible** : les écoles privées laïques de 200 à 1 500 élèves à Abidjan (Yopougon, Abobo, Cocody, Koumassi, Marcory, Port-Bouët, Bingerville…), puis à Bouaké, San-Pédro, Yamoussoukro, Daloa et Korhogo.

### Taille du marché (ordres de grandeur, hypothèses prudentes)

| | Hypothèse | Résultat |
|---|---|---|
| Écoles privées ciblables en CI | 4 000 (sur environ 3 000 établissements secondaires privés et plusieurs milliers d'écoles primaires et maternelles privées) | — |
| Revenu moyen par école | 350 élèves × 750 FCFA (mix des deux offres) | ≈ 262 500 FCFA par an |
| **Marché adressable en CI (abonnements seuls)** | 4 000 × 262 500 | **≈ 1 milliard de FCFA par an** |
| Flux de scolarités en CI | 4 000 × 350 élèves × 150 000 FCFA | ≈ 210 milliards de FCFA par an |
| Afrique francophone (Sénégal, Cameroun, Bénin, Togo, Burkina, Mali, Guinée…) | 3 à 4 fois la CI | ≈ 3 à 4 milliards de FCFA par an d'abonnements |

Le marché des abonnements est sain mais limité. **La vraie valeur à long terme est dans les flux de paiement** (des centaines de milliards de FCFA) et dans les services financiers associés, qui deviennent possibles une fois que l'on est l'outil de paiement des écoles.

### Pourquoi l'Afrique francophone se prête au passage à l'échelle

- **Un même droit des affaires** dans 17 pays (OHADA) et **une même monnaie** dans l'UEMOA (8 pays, FCFA) et la CEMAC (6 pays).
- La même langue et la même organisation scolaire (tranches, inscriptions, réinscriptions).
- Les mêmes agrégateurs de paiement présents dans plusieurs pays.
- L'application gère déjà les indicatifs téléphoniques et les monnaies de 12 pays.

---

## 5. Concurrence et positionnement

| Type d'acteur | Exemples | Leur force | Leur faiblesse face à ScolaPay |
|---|---|---|---|
| **Statu quo** : cahier, Excel, caisse | La majorité des écoles | Gratuit et connu | Impayés, fraude, aucune visibilité. **C'est le vrai concurrent.** |
| **Logiciels de gestion scolaire complets** | Novacole (200 à 500 FCFA/élève/an, 6 pays), EvalScol (29 990 à 59 990 FCFA/mois), Innova School, SchoolExpert, KiboERP… ([source](https://novacole.com/)) | Couvrent tout : notes, bulletins, emplois du temps | Généralistes, mise en place lourde, recouvrement traité comme un module parmi d'autres |
| **Passerelles de paiement pour écoles** | CentralBill, agrégateurs (CinetPay, etc.) | Font très bien le paiement | Ne gèrent pas l'échéancier, les relances ni le pilotage de la direction |

**Positionnement : « On ne vend pas un logiciel, on vend de l'argent encaissé. »**

Ce qui fait la différence :
1. **Spécialiste du recouvrement.** L'application est simple : une caissière la maîtrise en 15 minutes.
2. **Pensé pour WhatsApp**, là où se trouvent les parents.
3. **Anti-fraude** : reçus non supprimables, QR de vérification, journal par caissier. C'est l'argument qui convainc les fondateurs.
4. **Mise en place faite pour l'école** en 48 heures, à partir de son fichier Excel.
5. **Présence sur le terrain et support WhatsApp** avec une réponse en moins de 2 heures.
6. **Compatible avec l'existant** : l'école garde son logiciel de notes. Pas de grand remplacement à décider.

> Le prix d'entrée (500 FCFA) reste dans les prix du marché. L'offre premium (1 000 FCFA) se justifie par le retour sur investissement (voir §6), pas par le nombre de fonctions.

---

## 6. Modèle économique

### Les offres

| | **Essentiel** | **Recouvrement+** |
|---|---|---|
| Prix | **500 FCFA par élève et par an** (minimum 75 000 FCFA) | **1 000 FCFA par élève et par an** (minimum 150 000 FCFA) |
| Échéanciers, soldes, tableau de bord | ✓ | ✓ |
| Reçus QR, journal de caisse, anti-fraude | ✓ | ✓ |
| Relances WhatsApp en un clic, espace parent | ✓ | ✓ |
| Paiement en ligne par mobile money | — | ✓ |
| Relances SMS automatiques, rapport hebdo au fondateur | — | ✓ (feuille de route) |
| Revue mensuelle des impayés avec un conseiller | — | ✓ |

- **Mise en place** (import, paramétrage, formation de 2 heures) : 25 000 à 50 000 FCFA. Offerte aux 10 premières écoles.
- **Paiement de l'abonnement en 3 fois**, au rythme des tranches des parents. L'objection « trésorerie » disparaît.
- **Garantie** : si, après un trimestre, le taux de recouvrement ne s'est pas amélioré, le 2e versement est offert.

### Revenus complémentaires (à partir de l'an 2)

| Source | Mécanisme | Ordre de grandeur |
|---|---|---|
| Cartes scolaires QR | Vendues 1 000 FCFA, coût d'impression d'environ 450 FCFA | Environ 190 000 FCFA de marge pour une école de 350 élèves |
| Paiements en ligne | Petite marge sur la commission de l'agrégateur partenaire ou frais de service transparents | 0,3 à 0,5 % du flux en ligne |
| Packs SMS | Revente avec marge | Accessoire |
| Financement de la scolarité (partenaire agréé) | Commission d'apport | Fort potentiel, à structurer avec un établissement agréé |

### Le calcul qui convainc un fondateur

Prenons une école de **400 élèves** dont la scolarité moyenne est de **150 000 FCFA**. Elle attend **60 millions de FCFA** par an.

- Si ScolaPay fait gagner **5 points** de recouvrement, l'école encaisse **3 millions de FCFA** de plus.
- Recouvrement+ lui coûte 400 × 1 000 = **400 000 FCFA**.
- **Retour sur investissement : 7,5 fois**, sans compter le temps gagné et la fraude évitée.

---

## 7. Économie unitaire (par école)

| Indicateur | Hypothèse | Valeur |
|---|---|---|
| Revenu moyen par école (ARPA) | 350 élèves × 750 FCFA, plus des services | ≈ 300 000 FCFA par an |
| Coût de service | Hébergement, SMS, environ 2 h de support par mois | ≈ 40 000 FCFA par an |
| **Marge brute** | | **≈ 87 %** |
| Coût d'acquisition (CAC) | Commission commerciale (20 % de la 1re année), transport, démo | ≈ 80 000 FCFA |
| Délai de remboursement du CAC | | **≈ 3 à 4 mois** |
| Attrition (écoles qui partent) | Hypothèse : 10 % par an | Durée de vie moyenne ≈ 5 ans et plus |
| **Valeur d'une école sur sa durée de vie (LTV)** | 300 000 × 87 % × 5 | **≈ 1,3 million de FCFA** |
| **Ratio LTV / CAC** | | **≈ 16** (un très bon business se situe au-dessus de 3) |

---

## 8. Stratégie commerciale

### Le client idéal

Une école privée laïque de **200 à 1 500 élèves**, en ville, avec un fondateur joignable. Elle a un problème d'impayés reconnu, elle utilise déjà le mobile money et elle compte au moins une secrétaire ou une caissière qui a un smartphone.

### Les canaux, par ordre de priorité

1. **Terrain** : visite et démonstration de 10 minutes sur téléphone, avec l'école de démo intégrée (`python manage.py demo`). Objectif : 8 à 10 écoles visitées par jour.
2. **Recommandation** : remise de 20 % sur l'année suivante pour chaque école recommandée qui signe. Les fondateurs se connaissent tous.
3. **Associations et réseaux de fondateurs d'écoles privées** : présentations lors de leurs réunions, offre groupée.
4. **Contenu WhatsApp et Facebook** : témoignages chiffrés (« +12 points de recouvrement en 1 trimestre »), courtes vidéos de démonstration.
5. **Partenaires prescripteurs** : comptables d'écoles, imprimeurs de cartes, librairies scolaires, agences bancaires (elles veulent les comptes des écoles), commerciaux des agrégateurs de paiement.

### Le calendrier scolaire est le calendrier commercial

| Période | Ce qui se passe à l'école | Action |
|---|---|---|
| Août à octobre | Inscriptions et 1re tranche | Gros effort de vente et mises en place express |
| Novembre à janvier | 2e tranche, premiers gros retards | « Récupérez vos impayés avant les congés » |
| Février à avril | 3e tranche, retards accumulés | Témoignages et recommandations |
| Mai à juillet | Préparation de l'année suivante | Signatures pour la rentrée, réabonnements |

### Entonnoir cible (hypothèses à vérifier)

100 écoles visitées → 40 démonstrations → 15 pilotes gratuits → **8 à 10 clients payants**.

---

## 9. Opérations et équipe

| Phase | Équipe | Rôle du fondateur |
|---|---|---|
| **0 à 6 mois** | Le fondateur, 1 commercial à la commission et un développeur freelance ponctuel | Il vend, installe et assure le support lui-même : c'est ainsi qu'il apprend le métier. |
| **6 à 18 mois** | 3 ou 4 commerciaux, 1 ou 2 chargés de mise en place et de support, 1 développeur à mi-temps | Il recrute, forme et définit les process. |
| **18 à 36 mois** | Un responsable pays dans 2 nouveaux pays, une équipe produit de 2 personnes | Il gère les partenariats (paiement, financement) et lève des fonds. |

**Process clés** (à documenter dès la 1re école) :
- une **check-list de mise en place en 48 heures** (voir le [guide école](06-guide-ecole.md)) ;
- un **support WhatsApp Business** avec des réponses types et un délai de réponse de moins de 2 heures ;
- une **revue mensuelle** avec chaque fondateur : taux de recouvrement, relances et retards ;
- des **sauvegardes quotidiennes** de la base de données (voir le [guide technique](05-guide-technique.md)).

---

## 10. Juridique et conformité

- **Statut** : commencer comme entreprenant (statut OHADA simplifié) ou en SARL unipersonnelle dès qu'il faut signer avec un agrégateur de paiement. Le guichet unique s'appelle **CEPICI** en Côte d'Ivoire, **APIX** au Sénégal, **CFCE** au Cameroun, **APIEx** au Bénin, **CFE** au Togo et **CEFORE** au Burkina Faso.
- **Fiscalité** : se faire accompagner par un expert-comptable dès la création. Le régime fiscal dépend du chiffre d'affaires.
- **Marque** : un seul dépôt à l'**OAPI** protège la marque dans 17 pays.
- **Données personnelles** (élèves mineurs et téléphones des parents) : déclarer le traitement auprès de l'autorité compétente (**ARTCI** en Côte d'Ivoire, **CDP** au Sénégal…). Il faut aussi un contrat d'abonnement qui précise que l'école reste propriétaire de ses données, des accès par rôle et des sauvegardes.
- **Paiements** : **ne jamais détenir l'argent des parents.** Les paiements passent par un agrégateur agréé et arrivent directement sur le compte marchand de l'école. ScolaPay facture son abonnement séparément. Sans cette séparation, l'activité relèverait d'un établissement de paiement soumis à l'agrément de la BCEAO ou de la BEAC.
- **Éthique** : les relances restent courtoises et l'outil encourage le paiement fractionné. Le message aux écoles : « moins d'enfants renvoyés pour impayés, plus d'argent encaissé ».

---

## 11. Prévisions financières (scénario de base, en FCFA)

Hypothèses : environ 350 élèves par école, un prix moyen de 750 FCFA par élève (mix Essentiel et Recouvrement+), des écoles signées au fil de l'année (d'où un revenu calculé sur le nombre moyen d'écoles actives). Le détail est dans le [modèle financier](04-modele-financier.md) et dans le tableur [`modele-financier.xlsx`](modele-financier.xlsx), où toutes les hypothèses sont modifiables.

| | **An 1** | **An 2** | **An 3** |
|---|---:|---:|---:|
| Écoles clientes en fin d'année | 40 | 180 | 500 |
| Pays | CI | CI + Sénégal | CI + SN + 1 pays |
| Écoles actives en moyenne sur l'année | 24 | 110 | 340 |
| Revenu moyen par école | 300 000 | 320 000 | 350 000 |
| **Chiffre d'affaires** | **≈ 7,7 M** | **≈ 38,7 M** | **≈ 127 M** |
| Charges (équipe, commissions, terrain, technique, marketing, juridique, lancement de pays) | ≈ 5,0 M | ≈ 30,3 M | ≈ 85,8 M |
| **Résultat avant impôt** | **≈ +2,6 M** | **≈ +8,4 M** | **≈ +41 M** |
| Revenu annuel récurrent en fin d'année | 12 M | 58 M | **175 M** |

**Besoin de trésorerie** : le point bas calculé mois par mois est d'environ **0,4 million de FCFA**, atteint en novembre et décembre de l'an 1, avant que les pilotes ne deviennent payants. Prévoir **1 million de FCFA** pour garder une marge de sécurité.

### Trois scénarios à 3 ans

| | Prudent | **Base** | Ambitieux |
|---|---:|---:|---:|
| Écoles en fin d'an 3 | 200 | **500** | 1 000 |
| Revenu annuel récurrent en fin d'an 3 | 60 M | **175 M** | 400 M |

### La vraie richesse : la valeur de l'entreprise

Avec 2 000 à 3 000 écoles dans 6 à 8 pays (horizon de 5 à 7 ans), le revenu annuel récurrent dépasse **700 millions à 1 milliard de FCFA**, sans compter les revenus de paiement et de financement. Une entreprise de logiciel à revenus récurrents, rentable et en croissance, se valorise **plusieurs fois son revenu annuel**. Le fondateur qui en détient la majorité possède alors un **actif de plusieurs milliards de FCFA**, en plus de son salaire et de ses dividendes.

C'est un scénario, pas une promesse. Il dépend entièrement de l'exécution commerciale.

---

## 12. Financement

1. **Fonds propres (0,5 à 1,5 M FCFA)** : l'application existe déjà, l'argent sert au terrain.
2. **Autofinancement** : les abonnements payés d'avance (en 3 tranches) financent la croissance.
3. **Subventions et concours** (sans perte de capital) : le programme de la **Tony Elumelu Foundation** offre 5 000 USD non remboursables, une formation et du mentorat, et il est ouvert aux 54 pays africains (candidatures sur TEFConnect, habituellement du 1er janvier au 1er mars ; [source](https://www.tonyelumelufoundation.org/press-releases/apply-tef-entrepreneurship-programme-2026)). On peut aussi viser les prix d'innovation des opérateurs télécoms (par exemple le prix Orange de l'entrepreneur social) et les incubateurs locaux.
4. **Investisseurs (business angels, fonds d'amorçage)** : seulement une fois atteints 50 à 100 M FCFA de revenu annuel récurrent. La valorisation sera meilleure et le fondateur gardera plus de parts.
5. **À éviter au démarrage** : les crédits chers et les associés qui apportent de l'argent sans apporter de ventes.

---

## 13. Risques et parades

| Risque | Probabilité | Parade |
|---|---|---|
| Les écoles adoptent lentement (méfiance, habitudes) | Élevée | Pilote gratuit d'un trimestre, ROI chiffré, mise en place faite pour l'école, témoignages de fondateurs |
| Concurrence de logiciels moins chers | Moyenne | Spécialisation recouvrement et anti-fraude, service, compatibilité avec l'existant, prix d'entrée aligné sur le marché |
| Saisonnalité des ventes | Certaine | Calendrier commercial (§8), abonnements payés en 3 fois, ventes de mi-année pour les tranches 2 et 3 |
| Les caissiers résistent (perte de contrôle sur les espèces) | Moyenne | Vendre au fondateur, former la caisse, présenter l'outil comme une protection contre les accusations |
| Panne ou perte de données | Faible | Hébergement sérieux, sauvegardes quotidiennes testées, procédure de restauration |
| Les API de paiement évoluent ou l'agrégateur est défaillant | Moyenne | Architecture multi-agrégateurs (déjà prévue dans le code), paiement direct sur les numéros marchands toujours disponible |
| Réglementation (données, paiements) | Faible | Ne jamais détenir les fonds, déclarations de traitement, contrats propres |
| Le fondateur s'épuise ou dépend trop de lui-même | Moyenne | Process écrits dès le début, recrutements par commissions, revue hebdomadaire des indicateurs |

---

## 14. Indicateurs à suivre chaque semaine

- **Vente** : écoles visitées, démonstrations, pilotes lancés, signatures, taux de conversion à chaque étape.
- **Valeur pour le client** : taux de recouvrement de chaque école (avant et après), relances envoyées par semaine, part des paiements en ligne.
- **Santé de l'entreprise** : revenu annuel récurrent, attrition, coût d'acquisition, délai de remboursement de ce coût, **taux d'encaissement de ses propres factures** (montrer l'exemple).
- **Service** : délai de réponse au support, écoles « à risque » (qui n'ont pas utilisé l'outil depuis 14 jours).

---

## 15. Conclusion

ScolaPay coche les cases d'un business qui peut rendre riche en Afrique francophone :

- un **besoin vital et récurrent** : l'argent des écoles ;
- une **mise de départ faible**, car le produit existe déjà ;
- des **marges élevées** et des **revenus qui reviennent chaque année** ;
- une **même solution vendable dans plus de 15 pays** ;
- une **porte d'entrée vers les flux financiers**, là où se crée la plus grande valeur.

Le reste dépend de l'exécution : visiter des écoles dès demain matin.
