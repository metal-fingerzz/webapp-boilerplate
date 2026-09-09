# Conventions de travail

Ce document porte les conventions propres au travail avec un agent sur ce dépôt. Il ne remplace ni n'assouplit celles de [docs/](docs/) — [workflow Git](docs/git-workflow.md), [tests](docs/testing.md), [langue](docs/language.md) — qui s'imposent à tout contributeur, humain ou agent, et sont à lire avant toute contribution.

## Sommaire

1. [Discuter avant d'agir](#1-discuter-avant-dagir)
2. [Ce qui reste en suspens devient une issue](#2-ce-qui-reste-en-suspens-devient-une-issue)
3. [Les trouvailles annexes](#3-les-trouvailles-annexes)
4. [Clore une tâche](#4-clore-une-tâche)

---

## 1. Discuter avant d'agir

**Toute approche se valide avant de s'exécuter, systématiquement.**

Exposer l'analyse, les frictions réelles trouvées dans l'existant, et une recommandation argumentée. Présenter les arbitrages comme des options tranchées avec leurs contreparties, jamais comme un survol exhaustif. Puis attendre l'accord avant d'écrire quoi que ce soit.

**L'accord porte sur ce qui a été relu, jamais sur ce qui vient après.** Valider une approche n'autorise pas à fusionner : la pull request s'ouvre, la CI tourne, l'agent s'arrête là et le signale au [§4](#4-clore-une-tâche). La relecture du diff est une seconde barrière, distincte de la première — un diff d'une ligne aux checks verts l'exige autant qu'un gros. La fusion, puis la suppression des branches, suivent l'accord explicite, jamais la seule couleur des checks.

**Pourquoi.** Un agent produit du code bien plus vite qu'un humain ne le relit. Une mécompréhension ne coûte donc pas une correction : elle coûte tout ce qui a été généré par-dessus une prémisse fausse, plus les jetons dépensés à le défaire. La discussion préalable est aussi le seul moment où l'agent peut encore changer d'avis — après, il défend ce qu'il a déjà écrit.

## 2. Ce qui reste en suspens devient une issue

Une question posée trois fois dans une conversation et jamais tranchée n'existe nulle part une fois la conversation close. À la clôture d'une tâche, ce qui est resté en suspens est donc listé, avec un brouillon d'issue prêt — **et c'est la personne qui valide sa création.**

| Situation | Traitement |
|---|---|
| Question posée, restée sans réponse | Listing + brouillon, création après validation |
| Report explicite (« plus tard »), quelle qu'en soit l'origine | Idem |
| Question tranchée par « non » | Rien : c'est une décision, pas une dette |
| Idée dont l'absence ne coûte rien | Une phrase dans la conclusion, rien de plus |

Le brouillon porte le constat vérifié, une preuve reproductible, la raison pour laquelle ce n'était pas dans la pull request, et l'arbitrage qui reste à faire. Un renvoi à la conversation ne vaut rien : personne ne la relira.

## 3. Les trouvailles annexes

Ce qu'on remarque en passant, sans jamais en faire une question : le critère d'entrée dans la pull request en cours est **le scope de son titre**, jamais la taille du correctif. La règle et sa justification sont au [§3 du workflow Git](docs/git-workflow.md#3-convention-de-commits).

| Nature de la trouvaille | Traitement |
|---|---|
| Elle empêche la tâche d'aboutir | Entre dans la pull request : c'est une dépendance, pas une trouvaille |
| Elle tient dans le scope du titre | Entre dans la pull request, et le corps la signale |
| Elle est hors scope | Issue, selon le §2 ci-dessus |
| Son absence ne coûte rien | Une phrase dans la conclusion |

## 4. Clore une tâche

Une tâche close — menée à son terme, abandonnée ou bloquée — se termine par un état des lieux en quatre rubriques, **toujours affichées, même vides** : « rien à nettoyer » prouve qu'on a regardé, le silence ne prouve rien.

| Rubrique | Contenu |
|---|---|
| **Fait** | Les livrables avec leur preuve — un numéro de commit, l'état des checks — pas « c'est terminé » |
| **À toi** | Ce que l'agent ne doit pas faire sans toi — au premier chef la fusion d'une pull request ([§1](#1-discuter-avant-dagir)) — et ce qu'il ne peut pas faire : droits, décisions, réglages d'interface |
| **À tracer** | Les brouillons d'issues en attente de validation (§2) |
| **Nettoyé** | Branches supprimées, processus arrêtés, et ce qui reste sale faute d'avoir pu le faire |

Le déclencheur est la clôture d'une tâche, pas la fin de chaque message : autrement le rituel devient un tic administratif.

Deux règles tiennent dans la dernière rubrique. Tout processus lancé pendant la tâche — serveur de développement, conteneur — est arrêté à la fin. Un processus qu'on n'a pas lancé soi-même ne se tue jamais sans demander : il appartient peut-être à la session de travail en cours.
