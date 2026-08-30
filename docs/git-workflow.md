# Workflow Git

Ce document décrit les conventions Git de l'équipe : stratégie de branches, règles de fusion, convention de commits, versioning et gestion des urgences. Il s'applique à l'ensemble du monorepo (`api` et `web`).

## Sommaire

1. [Stratégie de branches](#1-stratégie-de-branches)
2. [Protection de la branche `main`](#2-protection-de-la-branche-main)
3. [Convention de commits](#3-convention-de-commits)
4. [Fusion des pull requests](#4-fusion-des-pull-requests)
5. [Taille des pull requests](#5-taille-des-pull-requests)
6. [Suivi des tâches](#6-suivi-des-tâches)
7. [Correctifs urgents](#7-correctifs-urgents)
8. [Versioning sémantique](#8-versioning-sémantique)
9. [Exemple complet](#9-exemple-complet)

---

## 1. Stratégie de branches

Modèle **trunk-based simplifié** (inspiré de GitHub Flow). Choisi plutôt que Git Flow : l'équipe est petite (2-5 personnes) et ne maintient pas plusieurs versions en parallèle, donc les branches `develop`/`release`/`hotfix` de Git Flow n'apportent que de la friction supplémentaire.

- `main` est **toujours déployable**. Personne n'y pousse directement.
- Chaque tâche part d'une branche courte, vécue idéalement **2-3 jours maximum**.
- Toute branche fusionne dans `main` via une pull request (PR), avec au moins une revue.

**Nommage des branches** :

| Préfixe | Usage |
|---|---|
| `feature/` | nouvelle fonctionnalité |
| `fix/` | correction de bug |
| `chore/` | tâche technique sans impact fonctionnel |
| `docs/` | documentation uniquement |
| `refactor/` | changement de code sans changement de comportement |
| `test/` | ajout ou modification de tests |

Exemple : `feature/api-user-preferences`, `fix/web-cart-total`.

Chaque préfixe correspond au type de commit attendu (voir [§3](#3-convention-de-commits)), à la seule exception de `feature/`, qui répond au type `feat`.

## 2. Protection de la branche `main`

Règles activées sur `main` :

- Merge impossible sans **au moins une revue approuvée**.
- Merge bloqué si un **check CI échoue** (tests, lint, build) — aucune exception, y compris en urgence.
- **Branche à jour avant fusion** (rebase requis sur `main`) : évite les régressions silencieuses entre deux PR fusionnées en parallèle.

## 3. Convention de commits

Basée sur [Conventional Commits](https://www.conventionalcommits.org/) : `type(scope): description`.

Comme la fusion se fait en squash (voir [§4](#4-fusion-des-pull-requests)), **c'est le titre de la pull request** qui doit respecter cette convention — pas nécessairement chaque commit individuel sur la branche de travail, qui peut rester informel pendant le développement.

**Types** :

| Type | Usage |
|---|---|
| `feat` | nouvelle fonctionnalité |
| `fix` | correction de bug |
| `chore` | tâche technique (dépendances, config...) |
| `docs` | documentation uniquement |
| `refactor` | changement de code sans changement de comportement |
| `test` | ajout ou modification de tests |

**Scope obligatoire**, liste fermée (validée par `commitlint`, règle `scope-enum`) :

| Scope | Périmètre |
|---|---|
| `api` | backend FastAPI |
| `web` | frontend React |
| `db` | migrations Alembic, modèles |
| `ci` | workflows, pipeline |
| `deps` | montées de version de dépendances |
| `repo` | tooling transverse (poe, config monorepo) |

Cette liste peut être étendue si de nouveaux modules apparaissent dans le monorepo.

Le titre est rédigé en anglais, comme tout artefact versionné ; le corps de la pull request reste en français. Voir [language.md](language.md).

## 4. Fusion des pull requests

**Squash merge systématique.** Tous les commits de la branche sont compressés en un seul commit sur `main`, dont le message est le titre de la PR. Le numéro de PR est ajouté automatiquement par GitHub (`(#47)`), ce qui permet de retrouver l'historique détaillé et la discussion associée.

Bénéfices : historique de `main` lisible (une ligne = un changement complet), `git bisect` efficace, changelog automatisable.

## 5. Taille des pull requests

Pas de blocage automatique — une grosse PR peut être légitime (migration, refactor). À la place : étiquetage automatique (`size/XS` à `size/XL`, via une action CI sur les lignes modifiées, fichiers générés exclus).

**Repère indicatif** : ~400 lignes de diff net. Au-delà, l'auteur explique pourquoi dans la description ou envisage de scinder la PR.

## 6. Suivi des tâches

**GitHub Issues + GitHub Projects** (vue kanban). Choisi plutôt que Jira ou Linear : déjà intégré à GitHub, zéro outil supplémentaire, lien natif avec les PR.

- Une tâche = une issue.
- La PR référence l'issue avec un mot-clé de fermeture automatique : `Closes #42`.
- L'issue se ferme automatiquement à la fusion de la PR.

## 7. Correctifs urgents

Pas de branche `hotfix` dédiée — un seul chemin de fusion, accéléré humainement mais jamais techniquement :

1. Branche `fix/nom-court` depuis `main`, comme d'habitude.
2. CI **non négociable** : aucun bypass des tests, même en urgence.
3. Revue réduite à une approbation rapide d'un(e) coéquipier(ère) disponible, plutôt qu'une revue approfondie.
4. Une fois mergé, le tag et le déploiement suivent le pipeline normal.
5. Post-mortem léger après coup (un ticket "incident" suffit) pour éviter la récidive.

## 8. Versioning sémantique

[SemVer](https://semver.org/) : `MAJOR.MINOR.PATCH`.

| Type de commit | Impact |
|---|---|
| `fix:` | PATCH (+0.0.1) |
| `feat:` | MINOR (+0.1.0) |
| `BREAKING CHANGE:` en footer | MAJOR (+1.0.0) |

**Tags annotés** uniquement (jamais de tag léger) :

```bash
git tag -a v1.1.0 -m "Add Google login"
git push origin v1.1.0
```

**État actuel : manuel.** Le tag est posé à la main après plusieurs merges sur `main`, le temps de bien ancrer la convention de commits dans les habitudes de l'équipe.

**Cible future : automatisation via `semantic-release`.** Une fois les habitudes prises, chaque squash merge sur `main` déclenchera automatiquement : analyse des commits depuis le dernier tag → calcul du bump de version → génération du changelog → création du tag et de la release GitHub → déclenchement du déploiement CI/CD. Cette bascule est jugée peu risquée car le seul point d'application de la convention est le titre de la PR (un verrou unique, facile à vérifier en CI).

## 9. Exemple complet

**Branche**
```
feature/api-user-preferences
```

**Commits de travail** (libres, pas de convention stricte requise)
```
wip: add UserPreferences model
fix migration
add GET endpoint
add pydantic validation
```

**Titre de la PR** (doit respecter la convention)
```
feat(api): add user preferences management
```

**Résultat après squash merge sur `main`**
```
feat(api): add user preferences management (#47)
```