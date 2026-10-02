# Guide de l'école : mise en place et utilisation

Ce guide sert deux fois : **à toi**, pour installer une école en 48 heures, et **à l'école**, que tu peux imprimer pour la direction et la caisse.

---

## Partie 1 : mise en place en 48 heures (par le conseiller ScolaPay)

### À demander à l'école la veille

- [ ] La **liste des élèves** dans Excel : nom, prénoms, classe, et si possible matricule, nom et téléphone du parent.
- [ ] Les **tarifs** de chaque niveau : inscription et tranches, avec leurs dates limites.
- [ ] La liste des **remises** accordées (fratrie, bourses, enfants du personnel).
- [ ] Les **paiements déjà reçus** depuis la rentrée (cahier de caisse ou Excel).
- [ ] Les **numéros marchands** Wave et Orange Money de l'école, s'ils existent.
- [ ] Les noms des personnes qui auront un compte (direction, caisse).

### Jour 1 : paramétrage (environ 2 heures)

1. **Ouvrir le compte** : `python manage.py creer_ecole --nom "…" --directeur …` (voir le [guide technique](05-guide-technique.md#3-gérer-tes-écoles-clientes)).
2. Se connecter avec le compte de la direction, puis **créer l'année scolaire** (par exemple 2026-2027).
3. **Classes et frais → + Barème** : créer un barème par niveau (Maternelle, Primaire, Collège…), avec toutes les échéances.
4. **Élèves → Importer** :
   - dans Excel, ajouter si besoin les colonnes `Nom`, `Prénoms`, `Classe`, `Matricule`, `Parent`, `Téléphone`, `Remise` ;
   - enregistrer en « CSV (séparateur : point-virgule) » ;
   - importer en laissant cochée la création automatique des classes.
5. **Classes et frais** : affecter le bon barème à chaque classe (bouton « Modifier »).
6. **Saisir les paiements déjà reçus**, avec leur vraie date. Chacun reçoit un numéro de reçu.
7. **Paramètres** : renseigner l'adresse, le téléphone, « Comment payer » (numéros marchands, motif à indiquer), la mention en bas des reçus et, au besoin, adapter le message de relance.
8. **Paramètres → Personnel** : créer un compte pour chaque caissier ou caissière. Jamais de compte partagé.
9. Vérifier le **tableau de bord** : le total attendu et les impayés doivent correspondre à ce que la direction connaît. Faire une capture d'écran : c'est la photo « avant ».

### Jour 2 : formation (1 heure sur place)

- **Caisse (30 min)** : rechercher un élève, encaisser, imprimer ou envoyer le reçu sur WhatsApp, puis relancer depuis la page « Relances ». La faire pratiquer sur 3 vrais paiements.
- **Direction (30 min)** : lire le tableau de bord, consulter le journal de caisse du jour, annuler un reçu (avec motif), accorder une remise, ajouter un membre du personnel.
- Créer le **groupe WhatsApp de support** avec la direction et la caisse.
- Envoyer aux parents le **message d'annonce** (modèle dans le [kit commercial](03-kit-commercial.md#8-messages-whatsapp-prêts-à-lemploi)).

---

## Partie 2 : utilisation au quotidien (à imprimer pour l'école)

### Pour la caisse et le secrétariat

**Encaisser un paiement**
1. **Élèves** → rechercher le nom → **Encaisser**.
2. Saisir le montant (le montant en retard est proposé par défaut), le mode de paiement et, pour le mobile money, la **référence de la transaction**.
3. **Valider** : le reçu s'affiche. Imprimez-le ou cliquez sur **« Envoyer le reçu au parent (WhatsApp) »**.

**Relancer les retardataires** (idéalement chaque lundi)
1. **Relances** → choisir une classe ou toutes les classes.
2. Cliquer sur **WhatsApp** à côté de chaque élève : la conversation s'ouvre avec le message déjà rédigé. Appuyer sur **Envoyer**.
3. La relance est enregistrée : la date de la dernière relance s'affiche dans la liste.

**Bonnes pratiques**
- Enregistrez **chaque** paiement **au moment** où vous le recevez.
- Pour un paiement Wave ou Orange Money reçu sur le numéro de l'école, notez toujours la **référence** : c'est votre preuve.
- En cas d'erreur, ne refaites pas un paiement en double : demandez à la direction d'annuler le reçu erroné.

### Pour la direction et le fondateur

**Chaque soir (2 minutes)** : **Caisse** → journal du jour. Le total « Espèces » de chaque caissier doit correspondre à l'argent remis.

**Chaque semaine (10 minutes)** :
- **Tableau de bord** : le taux de recouvrement progresse-t-il ? Quelles classes sont en retard ?
- **Relances** : les retardataires ont-ils été relancés cette semaine ?

**Ce que vous seuls pouvez faire** : annuler un reçu (avec un motif ; il reste visible, barré), accorder une remise, modifier les barèmes et les paramètres, créer ou désactiver des comptes.

### Questions fréquentes

| Question | Réponse |
|---|---|
| Un parent dit avoir déjà payé. | Ouvrez la fiche de l'élève : tous les paiements et leurs reçus y sont. Demandez au parent son numéro de reçu ou sa référence de transaction. |
| Un parent veut payer en plusieurs fois. | Encaissez chaque versement : les échéances se soldent dans l'ordre automatiquement. |
| Un élève change de classe. | Fiche élève → Modifier → nouvelle classe. Les paiements restent. |
| Un élève quitte l'école. | Direction : Fiche élève → Modifier → décocher « Toujours inscrit(e) ». Il disparaît des listes et des relances ; ses paiements sont conservés. |
| Comment le parent voit-il son solde ? | Par le lien « Espace parent » de la fiche élève, inclus automatiquement dans chaque relance. |
| L'année prochaine ? | **Paramètres → Nouvelle année** (en copiant les classes et barèmes), puis **Classes et frais → Réinscriptions**. Les arriérés de l'année passée restent visibles. |
| Internet est coupé. | Notez les paiements sur papier et saisissez-les au retour, avec la vraie date du paiement. |
