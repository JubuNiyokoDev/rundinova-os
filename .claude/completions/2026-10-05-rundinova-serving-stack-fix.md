# 2026-10-05 — Correction de la stack qui sert le port 18080

## Cause
Deux projets Compose Frappe tournaient en parallèle : `frappe_docker-*` et
`rundinova-*`. Le navigateur utilisait `rundinova-frontend-1` sur
`localhost:18080`, mais les premières commandes de bootstrap ciblaient la base
de `frappe_docker-*`.

## Correction appliquée sur `rundinova-*`
- `bootstrap.run` exécuté avec `docker compose -p rundinova`.
- Les cinq comptes fondateurs et leurs rôles ont été créés dans la base servie.
- `bench migrate` exécuté : page standard `rundinova-onboarding` présente.
- `bench build --app rundinova_tech` exécuté.
- Caches Frappe et website vidés.
- `rundinova.env` reçoit `COMPOSE_PROJECT_NAME=rundinova`, donc les commandes
  utilisant `--env-file rundinova.env` ciblent désormais cette stack par défaut.
- backend, frontend, websocket, workers et scheduler redémarrés.

## Vérifications
- Tous les services `rundinova-*` sont `running`.
- `rundinova-frontend-1` publie bien `0.0.0.0:18080->8080/tcp`.
- Base : **25 workspaces masqués / 5 visibles**.
- Membres :
  - Joffre : `RundiNova Tech`, `Home`, `Users`.
  - Janvier, Franck, Elvis, Fanuel : `RundiNova Tech`, `Users`.
- `check_page_access` : les 5 membres + Administrator chargent la page,
  `OK (script=2990)`.
- Administrator conserve 29 workspaces parce que son rôle Frappe
  `Workspace Manager` contourne `is_hidden`; ce comportement est normal.
- Les routes publiques testées redirigent vers `/login` tant qu'aucune session
  n'est ouverte, ce qui est normal.

## Test navigateur
1. Ouvrir `http://localhost:18080/login`.
2. Se connecter avec un compte fondateur, pas Administrator, pour vérifier le
   masquage de la sidebar.
3. Ouvrir directement `http://localhost:18080/app/rundinova-onboarding`.
4. Si l'ancien affichage persiste : déconnexion, DevTools → Application →
   Storage → **Clear site data**, puis **Unregister service worker**, et
   recharger.
5. Pour les prochaines commandes sur l'instance du navigateur, conserver
   `docker compose -p rundinova ...`; sans `-p rundinova`, Compose cible le
   projet `frappe_docker-*`.
