# Langue

Ce document fixe la langue de chaque type d'artefact du monorepo. La règle tient en une phrase : **le contenu des fichiers Markdown est en français, tout le reste est en anglais.**

## Sommaire

1. [Fichiers versionnés](#1-fichiers-versionnés)
2. [Écrits GitHub](#2-écrits-github)
3. [Pourquoi l'anglais pour le code](#3-pourquoi-langlais-pour-le-code)

---

## 1. Fichiers versionnés

| Artefact | Langue |
|---|---|
| Contenu des fichiers `.md` | français |
| Code source | anglais |
| Commentaires dans le code | anglais |
| Chaînes affichées à un humain (noms de jobs CI, messages d'erreur, `help` des tâches `poe`) | anglais |
| Identifiants (noms de fichiers, de branches, de variables, de fonctions) | anglais |

**Aucune exception.** La frontière est le *format du fichier*, jamais la nature du texte qu'il contient : c'est précisément ce qui rend la règle applicable en revue sans arbitrage au cas par cas.

Conséquence assumée : les chaînes visibles dans l'interface GitHub — le `name:` d'un job, le message d'erreur du linter de titre — sont en anglais, alors qu'elles s'affichent à côté de pull requests rédigées en français. Elles encadrent de toute façon du vocabulaire anglais (`feat`, `scope`, `squash`) et vivent dans un fichier de configuration. Les excepter rouvrirait la question « ce texte est-il destiné à un humain ? » sur chaque ligne ajoutée.

## 2. Écrits GitHub

| Artefact | Langue |
|---|---|
| Titre de pull request | anglais |
| Corps de pull request | français |
| Issues | français |
| Commentaires de revue | français |

Le titre de PR est en anglais parce que le squash merge en fait le message de commit sur `main` : c'est un artefact versionné, soumis à la convention de commits (voir [git-workflow.md §3](git-workflow.md#3-convention-de-commits)). Le corps, lui, ne l'est pas — c'est de la discussion d'équipe, elle se tient dans la langue de l'équipe.

## 3. Pourquoi l'anglais pour le code

- **Le code ne se lit jamais seul.** Il se lit mêlé à celui des dépendances, aux messages d'erreur des bibliothèques et à leur documentation, tous en anglais. Un commentaire français au milieu d'une pile anglophone est une rupture de registre à chaque lecture.
- **Ce dépôt est un boilerplate**, destiné à être cloné et réutilisé, potentiellement hors de l'équipe. Du code anglais voyage, du code français non.
- **C'était déjà le cas.** Au moment d'écrire cette règle, le seul français hors Markdown tenait dans deux fichiers de workflow ; tout le reste — commentaires Python, `alembic.ini`, `.gitignore`, `pyproject.toml` — était en anglais, hérité des templates Alembic et Vite. Formaliser la règle aligne la documentation sur la pratique, ça ne demande pas de migration.
