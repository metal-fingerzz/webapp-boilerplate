# Tests

Ce document décrit les conventions de test du monorepo : outillage, emplacement, nommage et configuration. Il ne couvre pour l'instant que le backend ; le frontend suivra avec sa propre suite.

## Sommaire

1. [Outillage](#1-outillage)
2. [Emplacement et nommage](#2-emplacement-et-nommage)
3. [Tests asynchrones](#3-tests-asynchrones)
4. [Tester les routes HTTP](#4-tester-les-routes-http)
5. [Configuration des tests](#5-configuration-des-tests)
6. [Couverture](#6-couverture)
7. [Tests base de données](#7-tests-base-de-données)

---

## 1. Outillage

`pytest`, `pytest-asyncio` et `pytest-cov`, déclarés dans le groupe `dev` de `backend/pyproject.toml`. La configuration vit dans la section `[tool.pytest.ini_options]` du même fichier — pas de `pytest.ini` ni de `setup.cfg` séparé.

Point d'entrée unique :

```bash
poe backend-test
```

## 2. Emplacement et nommage

`backend/tests/` **calque l'arborescence de `backend/src/api/`** : le module `src/api/routes/health_check.py` est testé par `tests/routes/test_health_check.py`. La correspondance est mécanique, on trouve les tests d'un module sans chercher.

Pas de fichiers `__init__.py` dans `tests/`. C'est permis par `--import-mode=importlib` : en mode d'import historique, pytest aurait exigé que les noms de fichiers de test soient uniques dans toute l'arborescence, ce qui interdit deux `test_config.py` dans deux sous-dossiers.

**Le nom d'un test décrit le comportement vérifié, pas la fonction appelée.** `test_logging_level_maps_log_level_to_stdlib_constant` dit ce qui est attendu ; `test_logging_level` ne dit rien. Un test échoué doit être diagnosticable depuis son nom seul, sans ouvrir le fichier.

Un comportement par test. La structure arrange / act / assert se lit d'elle-même par une ligne vide avant les assertions — pas de commentaires `# Arrange`, `# Act`, `# Assert`, qui n'ajoutent rien sur des tests de cette taille.

Pas de découpage `unit/` / `integration/` pour l'instant : sur deux fichiers, c'est de la cérémonie. À réévaluer quand les tests base de données arriveront (voir [§7](#7-tests-base-de-données)).

## 3. Tests asynchrones

```toml
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

Le mode `auto` dispense d'écrire `@pytest.mark.asyncio` sur chaque test. Le backend étant asynchrone de bout en bout, ce marqueur figurerait sur la quasi-totalité des tests : il ne distinguerait rien et ne serait plus qu'un rite. Les tests synchrones restent parfaitement supportés — `tests/test_config.py` en est un.

`asyncio_default_fixture_loop_scope` est fixé explicitement : non défini, `pytest-asyncio` émet un avertissement de dépréciation. La portée `function` donne à chaque test son propre event loop, donc aucun état de boucle partagé entre deux tests.

## 4. Tester les routes HTTP

La fixture `client` (dans `tests/conftest.py`) expose un `httpx.AsyncClient` branché sur l'application via `ASGITransport` :

```python
async def test_health_check_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health-check")

    assert response.status_code == 200
    assert response.json() == "OK"
```

`ASGITransport` court-circuite la couche réseau : les requêtes sont passées directement à l'application, sans port ouvert ni serveur lancé.

**Pourquoi pas `fastapi.testclient.TestClient`** — il est synchrone et gère son propre event loop en interne. Il entrerait en conflit avec les fixtures asynchrones, à commencer par la future session de base de données, et forcerait à mélanger tests synchrones et asynchrones dans la même suite.

## 5. Configuration des tests

`backend/.env.test` est **versionné** et ne contient que des valeurs factices : la suite n'ouvre aucune connexion, ces valeurs existent uniquement pour que `Settings` passe la validation.

La variable `ENV` est forcée à `test` en tête de `tests/conftest.py`, **avant tout import de `api`** :

```python
import os

os.environ["ENV"] = "test"

from api.main import api
```

Cette gymnastique n'est pas un caprice. `api/config.py` instancie `settings = Settings()` au niveau module et lit `ENV` au moment de l'import : toute solution qui définirait la variable après coup arriverait trop tard, et la collecte échouerait sur une `ValidationError`. `conftest.py` étant chargé par pytest avant tout module de test, c'est le seul point d'ancrage sûr.

Aucune dérogation de lint n'est nécessaire pour autant : `ruff` exempte de la règle `E402` (« import non situé en tête de fichier ») les imports précédés d'une manipulation d'`os.environ`, précisément pour ce cas d'usage. L'exemption est ciblée — la même construction avec une affectation ordinaire ou un appel de fonction à la place déclenche bien `E402`.

L'avantage est que la suite se lance de la même façon partout — en ligne de commande, depuis VSCode ou en CI — sans qu'aucune variable d'environnement n'ait à être fournie de l'extérieur.

> **Limite connue.** Le jour où `settings` deviendra injectable (un `get_settings()` mis en cache, exposé comme dépendance FastAPI), cette contrainte disparaîtra : `.env.test` et la manipulation d'`os.environ` pourront alors être supprimés.

## 6. Couverture

Les options de couverture sont portées par la tâche `poe backend-test`, pas par `addopts` :

```
pytest --cov=api --cov-report=term-missing
```

Ainsi un `pytest -k <motif>` lancé à la main pendant le développement reste rapide et son affichage lisible ; la couverture ne se paie que sur une exécution complète.

**Aucun seuil bloquant pour l'instant.** Un plancher de couverture sur une poignée de tests ne mesure rien, et l'expérience veut qu'il finisse abaissé au premier échec gênant plutôt que corrigé. Le verrou se posera avec les checks CI bloquants, sur une base de tests réelle.

## 7. Tests base de données

**À définir.** Il n'existe aujourd'hui ni engine, ni sessionmaker, ni modèle : `api/database/` ne contient que la classe `Base`. Concevoir des fixtures contre une couche de persistance qui n'existe pas reviendrait à figer des suppositions qu'il faudrait réécrire à la première migration.

À trancher lorsque cette couche arrivera :

- base réelle partagée ou conteneur jetable par exécution ;
- isolation par rollback transactionnel à chaque test, ou recréation du schéma ;
- constitution des données de départ (fixtures explicites ou fabriques).

Un point est en revanche déjà acquis : **ne pas substituer SQLite à PostgreSQL**. Le projet cible PostgreSQL via `asyncpg`, et les divergences de types, de contraintes et de DDL rendraient les tests non représentatifs de ce qui tourne en production — précisément là où un test de persistance a de la valeur.
