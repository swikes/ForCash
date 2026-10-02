# Guide technique

L'application est écrite en **Python / Django** : une technologie solide, répandue, et pour laquelle on trouve facilement des développeurs en Afrique francophone. Il n'y a pas d'application mobile à publier : tout fonctionne dans le navigateur du téléphone.

---

## 1. Lancer l'application sur ton ordinateur (10 minutes)

> `http://127.0.0.1:8000` ne fonctionne que **sur l'ordinateur où l'application tourne**, et tant que le serveur est lancé.

**Le plus simple : les lanceurs.** Après avoir installé [Python 3.10 ou plus récent](https://www.python.org/downloads/) (sous Windows, coche « Add python.exe to PATH »), double-clique sur `demarrer.bat` (Windows) ou lance `sh demarrer.sh` (Mac/Linux). Le lanceur crée l'environnement Python, installe les dépendances, prépare la base et l'école de démo, puis ouvre le navigateur. Identifiants : `directeur.demo` ou `caisse.demo`, mot de passe `Demo-ScolaPay-2026`. Les lancements suivants prennent quelques secondes et conservent tes données.

**Sans rien installer** : GitHub Codespaces (bouton dans le README). La configuration se trouve dans `.devcontainer/devcontainer.json`, et l'adresse du codespace est autorisée automatiquement (`scolapay/hosts.py`).

**À la main** (pour les développeurs) :

```bash
# 1. Récupérer le code
git clone https://github.com/swikes/ForCash.git
cd ForCash

# 2. Créer un environnement isolé et installer les dépendances
python -m venv .venv
# Windows :  .venv\Scripts\activate
# Mac/Linux : source .venv/bin/activate
pip install -r requirements.txt

# 3. Configuration locale
cp .env.example .env        # Windows : copy .env.example .env

# 4. Créer la base de données et l'école de démonstration
python manage.py migrate
python manage.py demo --password "ChoisisUnMotDePasse"

# 5. Démarrer
python manage.py runserver
```

Ouvre <http://127.0.0.1:8000> et connecte-toi avec `directeur.demo` (vue direction) ou `caisse.demo` (vue caisse), avec le mot de passe choisi.

**Pour faire la démo sur ton téléphone** (même Wi-Fi que l'ordinateur) : lance `python manage.py runserver 0.0.0.0:8000`, ajoute l'adresse IP de l'ordinateur dans `DJANGO_ALLOWED_HOSTS` du fichier `.env`, puis ouvre `http://<ip-de-l-ordinateur>:8000` sur le téléphone.

### Lancer les tests

```bash
python manage.py test
```

Ils sont 52. Ils couvrent les calculs de soldes, le cloisonnement entre écoles, les reçus, les annulations, l'import Excel, les relances, le portail parent, le paiement en ligne (démo et CinetPay simulé) et la connexion derrière les proxys de Codespaces et de Render. Lance-les avant chaque mise en ligne.

---

## 2. Mettre en ligne

Il faut un **nom de domaine** (par exemple `app.tonentreprise.ci`) et un **serveur**.

### Option A : un petit serveur VPS (recommandé, quelques milliers de FCFA par mois)

N'importe quel VPS Linux (Ubuntu) avec 1 Go de RAM suffit pour des centaines d'écoles.

```bash
# Sur le serveur (une seule fois)
curl -fsSL https://get.docker.com | sh
git clone https://github.com/swikes/ForCash.git && cd ForCash
cp .env.example .env
nano .env   # voir les réglages ci-dessous
docker compose up -d --build
docker compose exec app python manage.py createsuperuser
```

Réglages du `.env` en production :

```ini
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<une longue chaîne aléatoire : python -c "import secrets; print(secrets.token_urlsafe(50))">
DJANGO_ALLOWED_HOSTS=app.tonentreprise.ci
DJANGO_CSRF_TRUSTED_ORIGINS=https://app.tonentreprise.ci
DOMAIN=app.tonentreprise.ci
```

Fais pointer le DNS du domaine (enregistrement A) vers l'adresse IP du serveur. Le certificat HTTPS est obtenu automatiquement par Caddy ([`deploy/Caddyfile`](../deploy/Caddyfile)).

**Mettre à jour** après une modification du code : `git pull && docker compose up -d --build`. Les migrations s'appliquent automatiquement au démarrage.

### Option B : une plateforme gérée (Render, Railway, Fly.io…)

1. Crée un service web à partir de ce dépôt. Le `Dockerfile` et le `Procfile` sont fournis.
2. Ajoute une base **PostgreSQL** gérée et renseigne `DATABASE_URL`. Ajoute aussi `psycopg[binary]` dans `requirements.txt` (la ligne est déjà présente en commentaire).
3. Définis les mêmes variables d'environnement que ci-dessus (sans `DOMAIN`). Sur Render, l'adresse `….onrender.com` est autorisée automatiquement.

> Sur ces plateformes, le disque est effacé à chaque redéploiement : **n'y utilise pas SQLite**, prends PostgreSQL.

**Démo en ligne en un clic (Render, offre gratuite).** Le fichier `render.yaml` décrit une démo prête à l'emploi : le bouton « Deploy to Render » du README crée le service, génère la clé secrète et demande un mot de passe (`SCOLAPAY_DEMO_PASSWORD`). Au démarrage, `deploy/entrypoint.sh` applique les migrations et crée l'école de démo si elle n'existe pas. En offre gratuite, la base SQLite est effacée à chaque redémarrage : c'est parfait pour une démo, mais **inadapté à de vraies écoles**.

### Variables d'environnement

| Variable | Rôle | Exemple |
|---|---|---|
| `DJANGO_DEBUG` | `1` en local uniquement | `0` |
| `DJANGO_SECRET_KEY` | Clé secrète (obligatoire en production) | chaîne aléatoire de 50 caractères |
| `DJANGO_ALLOWED_HOSTS` | Domaines autorisés | `app.tonentreprise.ci` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Origines HTTPS des formulaires | `https://app.tonentreprise.ci` |
| `DATABASE_URL` | Base de données (SQLite par défaut) | `postgres://user:mdp@hote:5432/scolapay` |
| `TIME_ZONE` | Fuseau horaire | `Africa/Abidjan`, `Africa/Dakar`, `Africa/Douala` |
| `DJANGO_HSTS_SECONDS` | Active HSTS une fois le HTTPS confirmé | `31536000` |
| `PAYMENT_HTTP_TIMEOUT` | Délai maximal des appels aux agrégateurs (secondes) | `20` |
| `SCOLAPAY_DEMO_PASSWORD` | Démo en ligne uniquement : crée l'école de démo au démarrage, avec ce mot de passe | `UnMotDePasseSolide` |

---

## 3. Gérer tes écoles clientes

Toi, l'opérateur, tu as deux outils :

**L'administration** (`/admin`, avec le compte créé par `createsuperuser`) : liste des écoles, nombre d'élèves de l'année en cours, montant annuel à facturer, date de fin d'abonnement, suspension d'une école (case « active »), comptes du personnel.

**La ligne de commande**, pour ouvrir une nouvelle école en une ligne :

```bash
python manage.py creer_ecole --nom "Groupe Scolaire La Réussite" --ville Yopougon \
    --pays CI --directeur kone.awa --telephone "07 07 07 07 07" --prix 1000
# (avec Docker : docker compose exec app python manage.py creer_ecole ...)
```

La commande affiche l'identifiant et un mot de passe provisoire à transmettre au directeur. Celui-ci le change ensuite depuis le lien « mot de passe » de l'application. À la première connexion, l'application demande de créer l'année scolaire, puis de suivre la [check-list de mise en place](06-guide-ecole.md).

Pays gérés (indicatif téléphonique, format des numéros et monnaie) : Côte d'Ivoire, Sénégal, Cameroun, Bénin, Togo, Burkina Faso, Mali, Niger, Guinée, Congo-Brazzaville, RD Congo, Madagascar. La liste se trouve dans `ecoles/utils.py`.

---

## 4. Sauvegardes (non négociable)

Les données de tes clients sont leur argent. **Une sauvegarde par jour, conservée hors du serveur.**

- **SQLite avec Docker** : [`deploy/sauvegarde.sh`](../deploy/sauvegarde.sh) fait une copie à chaud de la base et garde 30 jours d'historique. Planifie-le avec `crontab -e` :
  ```
  0 2 * * * /home/ubuntu/ForCash/deploy/sauvegarde.sh >> /home/ubuntu/sauvegarde.log 2>&1
  ```
  Copie ensuite le dossier `backups/` ailleurs (rclone vers Google Drive, un autre serveur…).
- **PostgreSQL** : active les sauvegardes automatiques de ton hébergeur, ou planifie `pg_dump`.
- **Teste une restauration une fois par trimestre.** Une sauvegarde jamais testée n'est pas une sauvegarde.

---

## 5. Paiement en ligne (mobile money)

### Principe

Chaque école utilise **son propre compte marchand** chez un agrégateur. Les parents paient, l'argent arrive chez l'école. ScolaPay ne fait que **vérifier** le paiement auprès de l'agrégateur, puis enregistrer le reçu. Tu ne détiens jamais les fonds, donc tu n'as pas besoin d'agrément d'établissement de paiement.

Dans **Paramètres → Paiement en ligne**, l'école choisit :
- **Désactivé** : les parents paient sur les numéros marchands affichés dans « Comment payer », et la caisse enregistre le paiement avec sa référence ;
- **Démonstration** : simule un opérateur, pour les rendez-vous commerciaux, sans argent réel ;
- **CinetPay** : agrégateur couvrant Orange Money, MTN, Moov, Wave… dans plusieurs pays.

### Activer CinetPay pour une école

1. L'école ouvre un compte marchand sur cinetpay.com (il faut les documents de l'entreprise).
2. Elle récupère son **apikey** et son **site_id** et les saisit dans Paramètres.
3. L'URL de notification à déclarer si besoin est affichée sur la page Paramètres (`/paiement/notification/cinetpay/`).
4. **Teste avec de vrais petits montants** (100 FCFA, puis 200 FCFA), vérifie que le reçu apparaît, puis ouvre le service aux parents.

> ⚠️ L'intégration suit l'API Checkout v2 de CinetPay, telle que décrite dans sa documentation (initialisation, notification, puis vérification systématique du statut). CinetPay déploie aussi une nouvelle API (clés `sk_test_…` / `sk_live_…`). Si le compte de l'école fournit ce type de clés, il faudra adapter la classe `CinetPayProvider` de `ecoles/payments.py` (environ 50 lignes) : le reste de l'application ne change pas.

### Ajouter un autre agrégateur (Wave Business, PayDunya, FedaPay…)

Écris une classe avec deux méthodes dans `ecoles/payments.py` :
- `start(request, tx)` : crée le paiement chez l'agrégateur et renvoie l'URL de paiement ;
- `check(tx)` : interroge l'agrégateur et renvoie `accepte`, `refuse` ou `en_attente`, avec le montant.

Ajoute ensuite le choix dans `School.PROVIDER_CHOICES` et dans `get_provider()`. Les règles de sécurité (revérification, idempotence, contrôle du montant) sont déjà gérées par `refresh_transaction()`.

---

## 6. Sécurité : la check-list

- [ ] `DJANGO_DEBUG=0` et une `DJANGO_SECRET_KEY` longue et secrète en production.
- [ ] HTTPS obligatoire (automatique avec Caddy). Active ensuite `DJANGO_HSTS_SECONDS=31536000`.
- [ ] Un compte par personne : jamais de compte partagé entre caissiers.
- [ ] Des mots de passe solides : l'application refuse les mots de passe trop simples.
- [ ] Les sauvegardes quotidiennes fonctionnent et ont été testées.
- [ ] Le serveur est mis à jour chaque mois (`apt upgrade`) ; l'application l'est quand Django publie un correctif.
- [ ] Les accès `/admin` sont réservés à toi.

**Ce que l'application garantit déjà :**
- **Cloisonnement** : chaque école ne voit que ses données. C'est vérifié par des tests automatiques.
- **Traçabilité** : un reçu ne peut pas être supprimé. Seule la direction peut l'annuler, avec un motif, et il reste visible, barré.
- **Liens publics** (espace parent, reçus) : jetons aléatoires impossibles à deviner, non indexés par les moteurs de recherche.
- **Rôles** : le caissier ne peut ni annuler un reçu, ni accorder de remise, ni modifier les paramètres.

---

## 7. Organisation du code

```
ForCash/
├── manage.py
├── demarrer.bat, demarrer.sh lanceurs en un clic (Windows, Mac/Linux)
├── requirements.txt, Dockerfile, docker-compose.yml, Procfile, render.yaml
├── .devcontainer/           essai sans installation (GitHub Codespaces)
├── deploy/                  entrypoint.sh, Caddyfile (HTTPS), sauvegarde.sh
├── scolapay/                configuration Django (settings, urls, hosts)
├── ecoles/                  l'application métier
│   ├── models.py            écoles, années, barèmes, classes, élèves, paiements, relances
│   ├── finance.py           calcul des soldes, retards et taux de recouvrement
│   ├── views.py             écrans de la direction et de la caisse
│   ├── public_views.py      espace parent, reçus publics, paiement en ligne
│   ├── payments.py          agrégateurs de paiement (démo, CinetPay)
│   ├── importer.py          import Excel/CSV
│   ├── access.py            cloisonnement et rôles
│   ├── utils.py             pays, monnaies, téléphones, montants en lettres
│   ├── management/commands/ demo, creer_ecole
│   ├── templates/, static/  pages et style (aucune dépendance externe)
│   └── tests/               52 tests automatiques
└── docs/                    business plan, plan 90 jours, kit commercial, finances, guides
```

## 8. Feuille de route technique

Dans l'ordre, et **seulement quand des clients le demandent** :

1. Relances SMS automatiques (J-3, J+1, J+7) par un fournisseur local, avec une tâche planifiée.
2. Rapport hebdomadaire automatique au fondateur.
3. Groupes scolaires multi-sites, avec une vue consolidée.
4. Frais annexes : cantine, transport, tenues.
5. Mode hors ligne pour la caisse (application web progressive).
6. Chiffrement des clés d'API des agrégateurs dans la base.
