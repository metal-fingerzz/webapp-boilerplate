# Tests

Ce document décrit les conventions de test du monorepo : outillage, emplacement, nommage et configuration. Les principes — un comportement par test, un nom qui décrit ce comportement, une arborescence de tests qui calque celle des sources — sont communs aux deux piles ; les sections qui ne valent que pour l'une ou l'autre le signalent dans leur titre.

## Sommaire

1. [Outillage](#1-outillage)
2. [Emplacement et nommage](#2-emplacement-et-nommage)
3. [Tests asynchrones (backend)](#3-tests-asynchrones-backend)
4. [Tester les routes HTTP (backend)](#4-tester-les-routes-http-backend)
5. [Tester les composants React (frontend)](#5-tester-les-composants-react-frontend)
6. [Simuler l'API avec MSW (frontend)](#6-simuler-lapi-avec-msw-frontend)
7. [Configuration des tests](#7-configuration-des-tests)
8. [Couverture](#8-couverture)
9. [Tests base de données](#9-tests-base-de-données)

---

## 1. Outillage

**Backend** — `pytest`, `pytest-asyncio` et `pytest-cov`, déclarés dans le groupe `dev` de `backend/pyproject.toml`. La configuration vit dans la section `[tool.pytest.ini_options]` du même fichier — pas de `pytest.ini` ni de `setup.cfg` séparé.

**Frontend** — `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`, `msw` et `@vitest/coverage-v8`, en `devDependencies` de `frontend/package.json`. La configuration vit dans le bloc `test` de `frontend/vite.config.ts` — pas de `vitest.config.ts` séparé : l'alias `@/`, les plugins et le chargement des fichiers `.env` y sont déjà résolus, et un second fichier obligerait à les tenir synchronisés.

Points d'entrée :

```bash
poe backend-test     # pytest
poe frontend-test    # vitest
poe test             # les deux, dans cet ordre
```

Les deux autres checks bloquants ont les leurs : `poe lint`, décliné en `backend-lint` (`ruff check` puis `ruff format --check`) et `frontend-lint` (ESLint puis Prettier), et `poe build`, qui régénère le schéma avant de construire le bundle — le backend n'ayant pas de build propre, `poe backend-schema` en tient lieu. La CI n'appelle rien d'autre que ces tâches, voir [git-workflow.md §2](git-workflow.md#2-protection-de-la-branche-main).

**Pourquoi Vitest plutôt que Jest** — il réutilise la configuration et le pipeline de transformation de Vite. Jest demanderait de redéclarer l'alias `@/`, d'installer une chaîne de transformation pour le TSX et de reproduire la substitution d'`import.meta.env` : trois occasions de diverger de ce que le bundler fait réellement.

**Pourquoi `jsdom` plutôt que `happy-dom`** — `happy-dom` est plus rapide, mais son implémentation du DOM est partielle et les écarts se découvrent en plein débogage, sur un test qui échoue pour une raison sans rapport avec le code testé. Sur une suite de cette taille, les quelques centaines de millisecondes gagnées ne valent pas ce risque.

**Pas de `globals: true`.** `it` et `expect` sont importés explicitement depuis `vitest`. L'option `globals` existe surtout pour faciliter la migration depuis Jest ; l'activer imposerait d'ajouter `vitest/globals` aux `types` du `tsconfig` et de déclarer ces noms à ESLint, pour économiser une ligne d'import par fichier. Conséquence à connaître : le nettoyage automatique du DOM entre deux tests dépend de ces globales, il est donc appelé à la main dans `tests/setup.ts` (voir [§5](#5-tester-les-composants-react-frontend)).

## 2. Emplacement et nommage

Les tests vivent dans un dossier `tests/` séparé qui **calque l'arborescence des sources** :

```
backend/src/api/routes/health_check.py  →  backend/tests/routes/test_health_check.py
frontend/src/api/index.ts               →  frontend/tests/api/index.test.ts
frontend/src/App.tsx                    →  frontend/tests/App.test.tsx
```

La correspondance est mécanique, on trouve les tests d'un module sans chercher.

Le frontend ne colocalise donc pas les tests à côté des sources, contrairement à l'usage majoritaire de l'écosystème React. Le dossier séparé aligne les deux moitiés du monorepo sur une seule règle et garde `src/` limité à ce qui est réellement livré au navigateur : aucun motif d'exclusion à maintenir dans la configuration de build, de lint ou de couverture.

Côté backend, pas de fichiers `__init__.py` dans `tests/`. C'est permis par `--import-mode=importlib` : en mode d'import historique, pytest aurait exigé que les noms de fichiers de test soient uniques dans toute l'arborescence, ce qui interdit deux `test_config.py` dans deux sous-dossiers.

**Le nom d'un test décrit le comportement vérifié, pas la fonction appelée.** `test_logging_level_maps_log_level_to_stdlib_constant` dit ce qui est attendu ; `test_logging_level` ne dit rien. Un test échoué doit être diagnosticable depuis son nom seul, sans ouvrir le fichier. La règle vaut telle quelle pour le premier argument d'`it()` : `it("displays the payload returned by a successful health check")`, pas `it("renders")`.

Un comportement par test. La structure arrange / act / assert se lit d'elle-même par une ligne vide avant les assertions — pas de commentaires `# Arrange`, `# Act`, `# Assert`, qui n'ajoutent rien sur des tests de cette taille.

Les fichiers de test frontend n'ouvrent pas de bloc `describe` tant qu'ils ne couvrent qu'un module : le nom du fichier porte déjà cette information, et le `describe` n'ajouterait qu'un niveau d'indentation.

Pas de découpage `unit/` / `integration/` pour l'instant : sur une poignée de fichiers, c'est de la cérémonie. À réévaluer quand les tests base de données arriveront (voir [§9](#9-tests-base-de-données)).

## 3. Tests asynchrones (backend)

```toml
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

Le mode `auto` dispense d'écrire `@pytest.mark.asyncio` sur chaque test. Le backend étant asynchrone de bout en bout, ce marqueur figurerait sur la quasi-totalité des tests : il ne distinguerait rien et ne serait plus qu'un rite. Les tests synchrones restent parfaitement supportés — `tests/test_config.py` en est un.

`asyncio_default_fixture_loop_scope` est fixé explicitement : non défini, `pytest-asyncio` émet un avertissement de dépréciation. La portée `function` donne à chaque test son propre event loop, donc aucun état de boucle partagé entre deux tests.

## 4. Tester les routes HTTP (backend)

La fixture `client` (dans `tests/conftest.py`) expose un `httpx.AsyncClient` branché sur l'application via `ASGITransport` :

```python
async def test_health_check_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health-check")

    assert response.status_code == 200
    assert response.json() == "OK"
```

`ASGITransport` court-circuite la couche réseau : les requêtes sont passées directement à l'application, sans port ouvert ni serveur lancé.

**Pourquoi pas `fastapi.testclient.TestClient`** — il est synchrone et gère son propre event loop en interne. Il entrerait en conflit avec les fixtures asynchrones, à commencer par la session de base de données du [§9](#9-tests-base-de-données), et forcerait à mélanger tests synchrones et asynchrones dans la même suite.

## 5. Tester les composants React (frontend)

Le rendu passe par `@testing-library/react`, les assertions sur le DOM par les matchers de `@testing-library/jest-dom` :

```tsx
it("displays the payload returned by a successful health check", async () => {
  server.use(http.get(HEALTH_CHECK, () => HttpResponse.json("OK")));

  render(<App />);

  expect(await screen.findByText("OK")).toBeInTheDocument();
});
```

Les requêtes portent sur ce que l'utilisateur voit — un texte, un rôle, un libellé — jamais sur une classe CSS ni sur la structure des balises. Un test qui interroge `.health-check__status` casse au premier changement de style, sans qu'aucun comportement n'ait bougé.

`tests/setup.ts` est chargé avant chaque fichier de test (`setupFiles` dans `vite.config.ts`). Il enregistre les matchers de `jest-dom` et appelle `cleanup()` en `afterEach` : sans `globals: true`, Testing Library ne peut pas installer ce nettoyage elle-même, et le DOM du test précédent resterait monté — `getByText` échouerait alors sur plusieurs correspondances.

`@testing-library/user-event` n'est **pas installé** : aucun composant n'a d'interaction à ce stade, et une dépendance sans usage se périme sans que personne le remarque. À ajouter avec le premier test qui clique ou saisit — c'est le compagnon standard de Testing Library pour ça, `fireEvent` ne reproduisant pas la séquence d'événements réelle d'un navigateur.

## 6. Simuler l'API avec MSW (frontend)

Les réponses de l'API sont simulées par [MSW](https://mswjs.io/), qui intercepte au niveau de `fetch` :

```tsx
const HEALTH_CHECK = `${import.meta.env.VITE_API_URL}/health-check`;

server.use(
  http.get(HEALTH_CHECK, () =>
    HttpResponse.json({ detail: "Boom" }, { status: 500 }),
  ),
);
```

**Pourquoi pas un `vi.mock("@/api")`** — remplacer le module par un double ne testerait plus que le composant. Le client `openapi-fetch`, l'URL de base, la désérialisation et le code de statut ne seraient jamais exercés, et le double dériverait silencieusement le jour où la signature du client change. MSW laisse tout ce chemin s'exécuter et ne coupe qu'à la sortie réseau — même principe que l'`ASGITransport` du backend ([§4](#4-tester-les-routes-http-backend)), qui évite le réseau sans court-circuiter l'application.

`tests/server.ts` crée le serveur **sans handler par défaut**, et `setup.ts` le démarre avec `onUnhandledRequest: "error"`. Chaque test déclare donc les réponses dont il a besoin, et une requête que personne n'a simulée échoue bruyamment au lieu de retomber sur un comportement partagé que le test ne mentionne pas.

Trois pièges valent d'être signalés.

**Le serveur démarre au chargement du module, pas dans un `beforeAll`.** Les fichiers de `setupFiles` sont évalués *avant* l'import du fichier de test, alors que les hooks ne s'exécutent qu'après. Or `openapi-fetch` capture `globalThis.fetch` au moment où le module client est importé pour la première fois : depuis un `beforeAll`, MSW patcherait le global trop tard et le client garderait une référence au `fetch` d'origine. Toutes les requêtes passeraient à côté de l'intercepteur — et, celui-ci n'ayant jamais été atteint, sans le moindre avertissement de MSW.

**Les handlers sont déclarés sur une URL absolue.** Le joker `*/health-check`, longtemps idiomatique, ne correspond plus à rien depuis que MSW s'appuie sur `path-to-regexp` v8, où `*` n'est plus un motif valide. L'échec est silencieux : la requête part pour de bon et le test échoue sur une erreur de réseau, pas sur l'absence de handler.

**Le message d'un échec réseau appartient à l'implémentation de `fetch`.** `HttpResponse.error()` produit `fetch failed` sous Node et `Failed to fetch` dans un navigateur. Le test qui couvre ce chemin filtre donc sur `/fetch/i` plutôt que sur une chaîne exacte.

## 7. Configuration des tests

Les deux piles versionnent un fichier d'environnement de test ne contenant que des valeurs factices.

**Backend** — `backend/.env.test` : `DATABASE_URL` nomme la base que la suite crée sur le serveur du compose (voir [§9](#9-tests-base-de-données)). Les autres valeurs existent seulement pour que `Settings` passe la validation, et aucun mail ne sort de la suite. La variable `ENV` est forcée à `test` en tête de `tests/conftest.py`, **avant tout import de `api`** :

```python
import os

os.environ["ENV"] = "test"

from api.main import api
```

Cette gymnastique n'est pas un caprice. `api/config.py` instancie `settings = Settings()` au niveau module et lit `ENV` au moment de l'import : toute solution qui définirait la variable après coup arriverait trop tard, et la collecte échouerait sur une `ValidationError`. `conftest.py` étant chargé par pytest avant tout module de test, c'est le seul point d'ancrage sûr.

Aucune dérogation de lint n'est nécessaire pour autant : `ruff` exempte de la règle `E402` (« import non situé en tête de fichier ») les imports précédés d'une manipulation d'`os.environ`, précisément pour ce cas d'usage. L'exemption est ciblée — la même construction avec une affectation ordinaire ou un appel de fonction à la place déclenche bien `E402`.

> **Limite connue.** Le jour où `settings` deviendra injectable (un `get_settings()` mis en cache, exposé comme dépendance FastAPI), cette contrainte disparaîtra : `.env.test` et la manipulation d'`os.environ` pourront alors être supprimés.

**Frontend** — `frontend/.env.test` déclare `VITE_API_URL=http://api.test`. Vitest lance Vite en mode `test`, qui charge `.env.test` comme `pnpm dev` charge `.env.development` : aucun réglage supplémentaire, et le client refuse de se construire sans cette variable. L'origine est volontairement fictive — un `localhost` laisserait passer une requête réellement partie vers le serveur de développement qui tourne à côté.

L'avantage, des deux côtés, est que la suite se lance de la même façon partout — en ligne de commande, depuis VSCode ou en CI — sans qu'aucune variable d'environnement n'ait à être fournie de l'extérieur.

## 8. Couverture

Les options de couverture sont portées par les tâches `poe`, pas par la configuration des runners :

```
pytest --cov=api --cov-report=term-missing
vitest run --coverage
```

Ainsi un `pytest -k <motif>` ou un `vitest <fichier>` lancé à la main pendant le développement reste rapide et son affichage lisible ; la couverture ne se paie que sur une exécution complète.

Côté frontend, `src/main.tsx` est exclu du rapport : ce point d'entrée ne fait que monter `<App />` dans un document réel, il n'a aucune branche qu'un test pourrait exercer, et l'y laisser afficherait une ligne rouge que personne ne peut corriger — le meilleur moyen d'apprendre à l'équipe à ignorer le rapport.

**Aucun seuil bloquant pour l'instant.** Un plancher de couverture sur une poignée de tests ne mesure rien, et l'expérience veut qu'il finisse abaissé au premier échec gênant plutôt que corrigé. La CI exécute bien les deux suites de façon bloquante (voir [git-workflow.md §2](git-workflow.md#2-protection-de-la-branche-main)), mais elle ne regarde que leur verdict : le rapport de couverture s'affiche dans ses logs sans jamais faire échouer un job. Le plancher viendra sur une base de tests réelle.

> **Limite connue (frontend).** Un test qui provoque volontairement l'échec de l'évaluation d'un module — typiquement `await expect(import("@/api")).rejects.toThrow()` pour vérifier une garde de configuration — fait **disparaître le fichier concerné du rapport de couverture** au lieu de l'y faire figurer partiellement. Le comportement est identique avec les providers `v8` et `istanbul`. C'est pourquoi la garde sur `VITE_API_URL` n'est pas testée : un fichier source escamoté sans bruit du rapport induit plus en erreur que la ligne non couverte qu'on gagnerait.

## 9. Tests base de données

Ce qui passe par la base se teste contre PostgreSQL, sur une base créée pour l'exécution. Chaque test écrit dans une transaction que sa fin annule, et les données de départ s'écrivent avec des fonctions ordinaires. Les fixtures sont dans `tests/conftest.py`, et `tests/routes/auth/test_register.py` est le premier fichier qui s'en sert.

```python
async def test_register_with_a_taken_username_returns_409_whatever_its_case(
    client: AsyncClient,
    database_session: AsyncSession,
) -> None:
    await add_existing_user(database_session, email="ada@example.com", username="Ada")

    response = await client.post(
        "/register", json=new_user_data(email="grace@example.com", username="ada")
    )

    assert response.status_code == 409
    assert await count_users(database_session) == 1
```

**Un test qui touche la base doit avoir un serveur qui répond** : `poe db-up` avant `poe backend-test`. Les tests qui ne demandent aucune fixture de base, comme `test_config.py`, passent sans serveur.

### Une base par exécution, sur le serveur du compose

La fixture de session `database` supprime une éventuelle base `test` laissée par une exécution interrompue, la recrée, applique les migrations, puis la supprime en fin d'exécution. La base s'appelle `test` parce que c'est le nom que déclare `backend/.env.test`.

- **Le schéma vient des migrations, pas de `metadata.create_all`.** Les migrations créent aussi les rôles de départ, et la route d'inscription en a besoin. Construire le schéma à partir des modèles laisserait en plus passer une migration qui ne correspond plus aux modèles.
- **Alembic est lancé sans `alembic.ini`.** Si `env.py` reçoit ce fichier, il en passe la section logging à `fileConfig`, qui désactive tous les loggers déjà créés, y compris ceux de l'application. Un test qui lirait leurs messages ne verrait plus rien.
- **Ne pas substituer SQLite à PostgreSQL.** Le projet cible PostgreSQL via `asyncpg`, et les différences de types, de contraintes et de DDL rendraient les tests non représentatifs de la production. C'est précisément là qu'un test de persistance a de la valeur.

`compose.yaml` ne crée pas cette base, et c'est voulu :

- **La CI ne passe pas par le compose.** Le job `backend` démarre un conteneur de service `postgres:18` avec les mêmes identifiants. Ce conteneur démarre avant le checkout du dépôt : il ne peut exécuter aucun script d'initialisation versionné. Une base créée par le compose existerait en local et manquerait en CI. Créée par la suite, elle existe partout où un serveur répond.
- **Les scripts d'initialisation de l'image ne tournent que sur un volume vide.** Un script `docker-entrypoint-initdb.d` ajouté après coup ne s'exécuterait jamais chez qui a déjà un volume `db-data`, et rien ne le signalerait. C'est le même genre d'échec silencieux que le chemin du volume (voir [database.md §5](database.md#5-le-chemin-du-volume)).

Testcontainers est écarté : la base recréée apporte déjà l'isolation qu'il donnerait, sans démarrer un conteneur par exécution. Le rôle `usr` a le droit de créer une base, puisque l'image fait du rôle `POSTGRES_USER` un superutilisateur.

### Isolation : une transaction annulée par test

La fixture `database_connection` ouvre une connexion et y démarre une transaction, que la fin du test annule. Tout ce que le test et ses requêtes ont écrit disparaît avec elle. L'autre option, recréer le schéma à chaque test, a été écartée : il faudrait rejouer toutes les migrations à chaque fois, et le coût grandirait avec chaque migration ajoutée.

**Les routes committent, et c'est ce qui impose le mode savepoint.** Chaque session est ouverte avec `join_transaction_mode="create_savepoint"`. Le `commit()` d'une route ne valide alors qu'un savepoint, et la transaction du test reste ouverte. Le mode compte aussi pour les erreurs : dans PostgreSQL, une requête en erreur, comme l'`INSERT` qui viole une contrainte d'unicité, rend toute la transaction inutilisable. Le savepoint limite les dégâts à la requête HTTP, et la session du test peut encore lire la base. Sans lui, les tests de doublon de `test_register.py` échouent.

**Chaque requête reçoit sa propre session**, ouverte sur cette connexion, comme elle en recevrait une du pool. `get_database_session` est remplacée par `dependency_overrides` pendant le test. Il n'y a pas d'autre moyen : `ASGITransport` ne lance pas le `lifespan`, et la fabrique de sessions de `app.state` n'existe donc pas en test. **Le test lit avec sa propre session**, `database_session`. Il relit ainsi la base, et pas ce que la requête a laissé en mémoire.

**L'engine est créé et fermé par test**, sans pool. Une connexion `asyncpg` est liée à la boucle asyncio qui l'a ouverte, et chaque test a la sienne (voir [§3](#3-tests-asynchrones-backend)).

**Règle qui en découle : un test n'ouvre jamais sa propre connexion** en dehors de ces fixtures. Ce qu'elle écrirait ne serait pas annulé et passerait au test suivant.

### Données de départ : des fonctions, pas de fabriques

Les données de départ s'écrivent avec des fonctions ordinaires, dans le fichier de test qui s'en sert, par exemple `add_existing_user(session, email=…, username=…)`. Elles passent par les contrôleurs de l'application, avec un `commit()` comme une route. Ce qu'un test prépare se lit donc dans le test lui-même.

Une bibliothèque de fabriques comme `factory_boy` a été écartée. Elle gère mal les sessions asynchrones, et avec trois tables elle coûterait plus qu'elle ne rapporte. Une fonction qui sert à plusieurs fichiers remontera dans `conftest.py` au deuxième usage, pas avant.

### Les mails

La fixture `sent_emails` s'applique à tous les tests. Elle remplace `api.email.send_email` par un enregistreur et renvoie la liste des mails qu'il a reçus. Sans elle, faute de serveur SMTP, chaque inscription attendrait toutes les tentatives de renvoi, soit 30 secondes. Le remplacement vise `send_email` plutôt que la fonction appelée par chaque route : tout envoi passe par elle, quel que soit le nom sous lequel une route l'a importée.
