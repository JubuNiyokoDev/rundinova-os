# Analyse initiale du projet — 2026-10-03

## Résumé

RundiNova OS est un monorepo qui combine l’infrastructure `frappe_docker` avec l’application Frappe `apps/rundinova_tech`. Le socle utilise Frappe v16, ERPNext v16, HRMS v16, CRM `main`, MariaDB, Redis, Nginx proxy et Docker Compose.

## Compréhension acquise

- `compose.yaml` définit les services Frappe de base : configurator, backend, frontend, websocket, workers RQ et scheduler.
- `overrides/` ajoute MariaDB, Redis, proxy/TLS, sauvegardes, multi-bench et le profil de développement RundiNova.
- `images/rundinova/Containerfile` construit une image immuable avec l’application custom, installe ses dépendances et lance `bench build`.
- `apps/rundinova_tech` fournit 19 DocTypes métier couvrant budgets et dépenses alimentaires, dépenses générales, trésorerie, actifs, documents, décisions, objectifs/KPI, risques, bureaux, partenariats, impact communautaire, opportunités et dépôts GitHub.
- `setup.py` provisionne rôles, permissions, cartes, graphiques, dashboards et workspace ; `bootstrap.py` initialise de manière idempotente le type d’entrepôt Transit, la société RundiNova Tech et le seed.
- L’intégration GitHub est en lecture seule : métadonnées publiques et cinq commits récents sont récupérés via l’API REST ; le seul test existant cible ce module.
- La page d’onboarding est en lecture seule et expose une checklist de préparation avant production.
- La documentation définit une cible V1 plus large que le code custom : plusieurs éléments restent de la configuration ERPNext/HRMS/CRM ou sont encore à construire, notamment workflows complets, restrictions par branche, comptabilité complète, activités CRM et restauration de sauvegardes.

## État Git au début de l’analyse

Des changements non commités existaient déjà dans `desktop.py`, `hooks.py` et `setup.py`, ainsi que plusieurs fichiers non suivis liés à la configuration Claude, au branding, au bootstrap, à la documentation et au compose de développement. Aucun de ces changements n’a été supprimé ni réinitialisé.
