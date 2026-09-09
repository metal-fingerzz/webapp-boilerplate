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

**Après la fusion, la branche est supprimée**, en local comme sur le remote. Une branche fusionnée qui subsiste n'est plus qu'un doublon figé de `main`, dont personne ne sait dire s'il reste utile.

Attention au piège : `git branch --merged` n'en détecte aucune. La fusion se faisant en squash (voir [§4](#4-fusion-des-pull-requests)), le tip d'une branche fusionnée n'est jamais un ancêtre de `main`. C'est l'état de la pull request qui fait foi :

```bash
gh pr list --state merged --json headRefName --jq '.[].headRefName'
```

## 2. Protection de la branche `main`

Règles activées sur `main` :

- Merge impossible sans **au moins une revue approuvée**.
- Merge bloqué si un **check CI échoue** (tests, lint, build) — aucune exception, y compris en urgence.
- **Branche à jour avant fusion** (rebase requis sur `main`) : évite les régressions silencieuses entre deux PR fusionnées en parallèle.

Les checks bloquants tiennent dans un seul workflow, `.github/workflows/ci.yml`, en trois jobs indépendants qui démarrent en même temps — un backend rouge laisse quand même voir le verdict du frontend :

| Job | Étapes |
|---|---|
| `Backend` | `poe backend-lint` → `poe backend-test` → `poe backend-schema` |
| `Frontend` | `poe frontend-lint` → `poe frontend-test` → `poe schema` → `poe frontend-build` |
| `Release check` | `poe release-check` |

Chaque étape appelle une tâche `poe`, jamais l'outil directement : ce qui échoue sur une pull request se rejoue à l'identique en local, où `poe lint`, `poe test` et `poe build` lancent les deux piles d'un coup.

Le troisième job n'appartient à aucune des deux piles : il **répète à blanc la release** du [§8](#8-versioning-sémantique) sur le résultat de la fusion. La CI ne joue autrement que le lint, les tests et le build — jamais la release. Sans ce job, une montée de version de l'outil de release passerait au vert, se fusionnerait, et ne casserait qu'à la fusion suivante, sur `main`, au moment où plus personne ne regarde. Le numéro de version qu'il affiche n'est en revanche pas une prédiction : la branche porte encore ses commits de travail informels, que le squash remplacera par le titre. Ce qui est testé, c'est la mécanique, pas le chiffre.

Deux autres choix méritent une justification. Le backend ne produit aucun bundle, c'est donc **le dump du schéma OpenAPI qui tient lieu de build** : il importe l'application entière — il échoue sur ce que la suite de tests ne traverse pas — et produit l'artefact dont le frontend tire ses types. Et le job `Frontend` régénère ce schéma pour son propre compte, car `frontend/src/api/schema.d.ts` est généré, donc non versionné, et `tsc -b` échoue sans lui ; le faire passer par un artefact aurait rendu le frontend dépendant du backend, et donc invisible chaque fois que celui-ci est rouge.

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

**Une correction hors du scope annoncé n'entre pas dans la pull request**, quelle que soit sa taille — une ligne comprise. Le titre devient le message de commit sur `main` (voir [§4](#4-fusion-des-pull-requests)) : glisser un changement `api` sous un titre `chore(ci)` rend l'historique menteur, et le changelog automatique du [§8](#8-versioning-sémantique) ne verra jamais passer ce changement. La proximité dans le diff — « le fichier est déjà ouvert » — n'est pas un argument, c'est le mécanisme même de la dérive de périmètre.

Ces corrections deviennent des issues, puis se regroupent par scope dans une pull request de nettoyage (`chore(api): remove leftovers from the uv init skeleton`), plutôt qu'une branche par ligne. C'est une commodité contre la cérémonie, pas une condition : une correction prête n'attend jamais qu'une seconde apparaisse.

Une trouvaille qui **empêche la tâche d'aboutir** n'est en revanche pas hors scope : c'est une dépendance, elle entre dans la pull request et le corps l'explique.

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

[SemVer](https://semver.org/) : `MAJOR.MINOR.PATCH`. Le type du titre de la pull request — donc du commit de squash, voir [§3](#3-convention-de-commits) — détermine le bump :

| Type | Impact |
|---|---|
| `fix` | PATCH (+0.0.1) |
| `feat` | MINOR (+0.1.0) |
| `!` après le scope | MAJOR (+1.0.0) |
| `chore`, `docs`, `refactor`, `test` | **aucun** |

La dernière ligne n'est pas un oubli. **La majorité des fusions ne produit aucune release**, et c'est le comportement correct : une version n'a de sens que si elle change quelque chose pour qui consomme le code. Ces commits ne disparaissent pas pour autant — ils sont reportés sur la release suivante, dont les notes listent tous les types.

**Un changement cassant se déclare par un `!` dans le titre** : `feat(api)!: replace the session cookie with a bearer token`. Pas par un footer `BREAKING CHANGE:`. La raison est mécanique : le corps du commit de squash est composé par GitHub à la fusion, personne ne garantit ce qu'il contient, alors que le titre est la seule chose que la CI valide ([§3](#3-convention-de-commits)). Un footer déposé dans la description d'une pull request ne survit pas forcément au squash ; un `!` dans le titre, si.

### Ce qui est automatisé

Chaque squash merge sur `main` déclenche `.github/workflows/release.yml`, **une fois la CI verte** : analyse des commits depuis le dernier tag → calcul du bump → **tag annoté** → release GitHub dont les notes regroupent les changements par type, avec un lien vers chaque pull request. Il n'y a plus rien à poser à la main.

**Le rendu des notes est celui de l'outil, tel quel.** Les sections sont classées par ordre alphabétique — *Chores* avant *Features* — et les descriptions y apparaissent capitalisées, alors que les titres de pull request s'écrivent en minuscules ([§3](#3-convention-de-commits)). Les deux sont assumés : les corriger imposerait de versionner des templates Jinja et de les maintenir à chaque montée de version de l'outil, pour un gain purement cosmétique.

Le workflow s'enchaîne sur la CI plutôt que de tourner à côté : `main` n'est jamais releasée sur un verdict rouge. Deux fusions coup sur coup annulent le premier run de CI et ne releasent donc rien — la suivante rattrape les deux, puisque l'analyse porte toujours sur l'intervalle depuis le dernier tag, jamais sur un commit isolé.

### La version vit dans le tag, nulle part ailleurs

Aucun `CHANGELOG.md` versionné, aucun commit de bot sur `main`, et **aucun manifeste ne porte la version**. Le changelog, c'est la page des releases GitHub ; le numéro de version, c'est `git tag`.

Les deux manifestes sont traités différemment, parce que leur outillage ne laisse pas la même marge :

| Fichier | État | Raison |
|---|---|---|
| `frontend/package.json` | aucun champ `version` | Le paquet est `private`, npm n'en exige pas |
| `backend/pyproject.toml` | `version = "0.0.0"`, figé | `uv_build` refuse de construire sans ce champ. `uv.lock` en recopie la valeur |

`0.0.0` n'est pas une version : c'est la valeur qui n'affirme rien, choisie pour qu'un champ impossible à supprimer ne puisse pas non plus être pris pour la version publiée. Un commentaire sur place le dit.

Ce choix a une contrepartie assumée et un bénéfice qui la dépasse. Écrire la version dans les fichiers imposerait de pousser un commit sur `main` — donc de contourner sa protection ([§2](#2-protection-de-la-branche-main)) avec un jeton personnel ou une GitHub App. En restant sur le tag, le pipeline n'a besoin que du `GITHUB_TOKEN` que GitHub Actions fabrique à chaque run : **rien à provisionner**, ce qui compte d'autant plus que ce dépôt est un template. Un dépôt créé depuis lui release correctement dès la première fusion, sans que personne n'ait eu à créer de secret, et sa première release est une `0.1.0`.

### Aperçu local

Depuis `main`, à jour :

```bash
poe release-check
```

Elle affiche la version qui serait publiée et les notes qui l'accompagneraient, sans rien écrire ni rien pousser. C'est la même tâche que joue le job `Release check` de la CI ([§2](#2-protection-de-la-branche-main)).

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
