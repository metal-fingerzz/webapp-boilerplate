# Base de données de développement

Ce document décrit la base PostgreSQL locale : comment la lancer, ce que chaque tâche `poe` fait réellement, et les choix inscrits dans `compose.yaml`. Il ne traite pas des tests contre une base — cette question reste ouverte, voir [testing.md §9](testing.md#9-tests-base-de-données).

## Sommaire

1. [Commandes](#1-commandes)
2. [Cycle de vie des données](#2-cycle-de-vie-des-données)
3. [Identifiants et configuration](#3-identifiants-et-configuration)
4. [Choix de l'image](#4-choix-de-limage)
5. [Le chemin du volume](#5-le-chemin-du-volume)

---

## 1. Commandes

Sur un clone neuf, l'ordre est le suivant :

```bash
uv sync              # dépendances Python
poe db-up            # démarre PostgreSQL
poe migrate          # applique les migrations
poe backend-dev      # lance l'API
```

| Tâche | Commande | Effet |
|---|---|---|
| `poe db-up` | `docker compose up --detach --wait` | Démarre le conteneur et **ne rend la main qu'au healthcheck vert** |
| `poe db-down` | `docker compose down` | Arrête et supprime le conteneur, conserve les données |
| `poe db-reset` | `docker compose down --volumes` puis `up` | Détruit le volume et repart d'une base vide |

`--wait` n'est pas un détail de confort : sans lui, `docker compose up --detach` rend la main dès que le conteneur démarre, alors que PostgreSQL n'accepte pas encore de connexion. Un `poe migrate` enchaîné derrière échoue alors sur une connexion refusée, une fois sur deux, et l'erreur pointe vers Alembic plutôt que vers l'attente manquante. Le `healthcheck` de `compose.yaml` (`pg_isready`) est ce que `--wait` observe.

**`poe backend-dev` ne démarre pas la base**, volontairement. La lier au serveur de développement couplerait l'API au démon Docker et casserait le lancement pour qui pointe `DATABASE_URL` vers une instance locale ou distante. `poe db-up` est un geste explicite, à faire une fois par session de travail.

**Le port 5432 est publié sur l'hôte.** Une instance PostgreSQL déjà installée sur la machine occupe ce port, et `poe db-up` échoue alors sur un bind impossible — arrêter le service local, ou changer le port publié dans `compose.yaml` **et** dans `backend/.env.development`, qui doivent rester d'accord.

## 2. Cycle de vie des données

Les données vivent dans un volume Docker nommé, pas dans le conteneur : `poe db-down` puis `poe db-up` retrouve la base telle qu'elle était.

C'est un choix, pas un défaut de l'outil. Une base jetable à chaque arrêt rendrait toute migration triviale à passer, puisqu'elle s'appliquerait toujours sur une base vide — alors qu'une migration se joue en production sur une base qui porte déjà l'état précédent. Le volume conserve cet état, et `poe db-reset` reste là pour repartir de zéro quand c'est ce qu'on veut.

## 3. Identifiants et configuration

`backend/.env.development` est le fichier que l'application lit :

```
DATABASE_URL=postgresql+asyncpg://app:app@localhost:5432/app
```

`compose.yaml` réécrit les mêmes valeurs dans `POSTGRES_USER`, `POSTGRES_PASSWORD` et `POSTGRES_DB`. Cette duplication est assumée : les deux fichiers ne parlent pas le même vocabulaire — une URL d'un côté, trois variables de l'autre — et les réconcilier demanderait un troisième fichier d'environnement à la racine, lu par les deux. Trois chaînes de développement dupliquées, commentées de part et d'autre, coûtent moins que ce fichier supplémentaire. En cas de divergence, c'est `.env.development` qui fait foi : le compose se cale dessus.

Ces identifiants sont versionnés en clair parce qu'ils ne donnent accès qu'à une base locale, jetable, sans donnée réelle. Rien de ce fichier ne vaut pour un déploiement.

## 4. Choix de l'image

`postgres:18` — l'image Debian officielle, pas la variante `alpine`.

L'écart de taille joue en faveur d'Alpine (114 Mo contre 155 Mo compressés, mesurés sur les manifestes), mais il se paie une fois par machine. En face, musl n'offre pas de véritable support des locales : le tri texte y retombe sur l'ordre des octets, et un `ORDER BY` sur des chaînes accentuées ne rend plus le même résultat qu'une instance managée, toutes bâties sur glibc. Les extensions usuelles (`pgvector`, PostGIS) sont par ailleurs packagées pour Debian et se compilent sur Alpine.

C'est le même raisonnement que le refus de SQLite pour les tests ([testing.md §9](testing.md#9-tests-base-de-données)) : une base de développement n'a de valeur que si elle se comporte comme celle de production, et 41 Mo n'achètent pas cette divergence.

**Le major est épinglé, le patch ne l'est pas.** `postgres:18` prend les correctifs 18.x au prochain `docker compose pull`, et Dependabot proposera le passage au major suivant — l'écosystème `docker-compose` est déclaré dans [`.github/dependabot.yml`](../.github/dependabot.yml) pour ça. Épingler `18.6` figerait une version que personne ne remonterait : le robot suit les tags, il verrait `19` et laisserait dormir `18.7`.

## 5. Le chemin du volume

```yaml
volumes:
  - db-data:/var/lib/postgresql
```

PostgreSQL 18 a déplacé `PGDATA` vers `/var/lib/postgresql/18/docker`, et l'image déclare désormais son volume sur `/var/lib/postgresql` — **pas** sur le `/var/lib/postgresql/data` que la majorité des exemples en circulation montent encore.

Monter l'ancien chemin ne produit aucune erreur. Les données partent simplement dans un volume anonyme, que `docker compose down` supprime, et la base revient vide au démarrage suivant sans qu'aucun message n'ait signalé quoi que ce soit. C'est le genre de configuration qu'on ne débogue qu'après avoir perdu un jeu de données de test.
