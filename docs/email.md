# Mails de développement

Ce document décrit comment l'API envoie ses mails en local sans qu'aucun ne quitte la machine : le capteur SMTP lancé par `compose.yaml`, les tâches `poe` qui le pilotent, et les choix derrière sa configuration. Il ne traite pas de l'envoi en production, qui dépend du fournisseur SMTP retenu au déploiement.

## Sommaire

1. [Commandes](#1-commandes)
2. [Lire les mails](#2-lire-les-mails)
3. [Configuration](#3-configuration)
4. [Choix de l'outil](#4-choix-de-loutil)

---

## 1. Commandes

| Tâche | Commande | Effet |
|---|---|---|
| `poe mail-up` | `docker compose up --detach --wait mailpit` | Démarre Mailpit et **ne rend la main qu'au healthcheck vert** |
| `poe mail-down` | `docker compose down mailpit` | Arrête et supprime le conteneur, **avec les mails reçus** |

Il n'y a pas de `mail-reset` : Mailpit n'a pas de volume, donc `poe mail-down` puis `poe mail-up` repart d'une boîte vide. Pour vider la boîte sans redémarrer, l'interface a un bouton dédié.

Comme pour la base, **chaque tâche nomme son service** : `compose.yaml` déclare aussi `db`, et un `docker compose down` nu arrêterait les deux (voir [database.md §1](database.md#1-commandes)).

**`poe backend-dev` ne démarre pas Mailpit**, pour la même raison qu'il ne démarre pas la base. Sans Mailpit, l'API démarre et répond normalement. Seul l'envoi échoue : les tentatives s'épuisent sur une connexion refusée, puis l'échec est écrit dans les logs par `send_email_in_the_background`. Aucune route ne renvoie d'erreur, donc **un mail manquant se cherche d'abord dans les logs de l'API**.

## 2. Lire les mails

L'interface est sur **http://localhost:8025**. Elle affiche le rendu HTML, la version texte, les en-têtes et la source brute de chaque mail. C'est là qu'on vérifie un template, puisque le client de messagerie n'est plus dans la boucle.

Mailpit accepte tous les destinataires : une adresse inventée à l'inscription reçoit son mail comme une vraie. Rien n'est relayé vers l'extérieur.

Les mêmes données sont exposées par une API REST, par exemple `GET http://localhost:8025/api/v1/messages`. C'est le point d'appui d'un futur test d'intégration qui lirait le lien reçu pour l'appeler. Aucun test ne l'utilise aujourd'hui, et la suite ne demande pas `poe mail-up`.

## 3. Configuration

`backend/.env.development` et `backend/.env.test` pointent déjà sur les ports par défaut de Mailpit :

```
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_TLS=none
```

**Les identifiants sont vides, et c'est significatif.** Mailpit n'annonce pas l'extension `AUTH`. Si l'API tentait de s'authentifier, `aiosmtplib` lèverait une erreur non transitoire et le mail serait perdu. Or `aiosmtplib` s'authentifie dès que le nom d'utilisateur n'est pas `None`, même s'il est vide. C'est pourquoi `api/config.py` règle `env_parse_none_str=""` : une variable vide dans un fichier `.env` devient `None`, pas une chaîne vide.

Les ports publiés sur l'hôte sont `1025` pour SMTP et `8025` pour l'interface. Si l'un d'eux est déjà pris, changer le port dans `compose.yaml` **et** dans les deux fichiers `.env`, qui doivent rester d'accord.

## 4. Choix de l'outil

`axllent/mailpit:v1` : seule la version majeure est fixée, comme pour `postgres:18`. `docker compose pull` récupère les correctifs et les versions mineures.

| Outil | Pourquoi pas |
|---|---|
| MailHog | Plus maintenu depuis 2020. Mailpit est son successeur de fait, avec les mêmes ports |
| smtp4dev | Image .NET bien plus lourde, pour des fonctions (relais, IMAP) dont on n'a pas besoin |
| GreenMail | Pensé pour les tests Java, sans interface pour relire le rendu HTML |
| `aiosmtpd` dans pytest | Utile pour les tests, mais inutilisable en développement manuel |

L'image fournit son propre healthcheck (`/mailpit readyz`), que `--wait` observe. Rien à déclarer dans `compose.yaml`, contrairement à PostgreSQL.
