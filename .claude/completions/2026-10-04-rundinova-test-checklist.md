# 2026-10-04 — Checklist de test RundiNova OS

## Ce qui a été fait

### 1. Structure d'équipe et rôles (validée par l'utilisateur)
- 5 comptes utilisateurs créés et fonctionnels (connexion HTTP 200 vérifiée
  pour les 5 membres) :
  - Joffre Niyondiko (CEO) — RundiNova Director, Finance Manager, Team Member
  - Janvier Ndabubaha (COO) — RundiNova Operations, Team Member
  - Franck Maniranyibutse (Head of Engineering) — RundiNova Project Lead, Team Member
  - Elvis Irambona (Head of Communications) — RundiNova Communications, Team Member
  - Fanuel Kasumba Mandela (Head of People & Culture) — RundiNova People & Culture, Team Member
- 2 nouveaux rôles ajoutés : `RundiNova Operations`, `RundiNova People & Culture`
  (setup.py mis à jour avec la matrice de permissions complète).
- Documentation : `docs/rundinova/06-roles-and-responsibilities.md`.
- Page d'onboarding : `/app/rundinova-onboarding` (installée, standard=Yes).
- `bootstrap.py` corrigé : le champ `designation` n'existe pas sur le doctype
  User en Frappe v16 (les titres vivent sur Employee/HRMS) — retiré du code,
  conservé à titre informatif dans TEAM_USERS.

### 2. Masquage des modules ERPNext inutiles
- 5 workspaces passés à `is_hidden=1` via `bootstrap.hide_unused_workspaces()` :
  Manufacturing, Quality, Subcontracting, Support, Website.
- Vérifié en base : exactement ces 5 workspaces sont masqués.
- Les doctypes restent installés mais ne sont plus accessibles depuis la
  barre latérale du Desk.
- Approche retenue : `Workspace.is_hidden` (le champ `restrict_to_domain` de
  Module Def n'est pas exploitable en ERPNext v16 — les module_def.json ne le
  remplissent pas).

### 3. État de l'instance (rapport bootstrap)
- 1 company (RundiNova Tech), 5 warehouses, 2 cost centers, 96 accounts,
  13 departments, 7 rôles RundiNova.
- 19 doctypes RundiNova installés (module "RundiNova Tech").
- 5 dashboards RundiNova présents : Executive, Finance, People, Delivery,
  Ecosystem.
- Note : `RundiNova Meeting Log` n'existe pas dans l'app — mentionné dans la
  doc onboarding, à retirer de la checklist si non prévu.

### 4. Matrice de permissions (permission_report)
- `bench execute rundinova_tech.rundinova_tech.bootstrap.permission_report`
  ajoute un rapport read-only par rôle.
- **Bug corrigé** : `ensure_rundinova_permissions()` utilisait `doc.save()`
  sur le DocType parent, ce qui échouait silencieusement pour les doctypes
  standard quand developer_mode est désactivé. Les rôles Operations et
  People & Culture n'avaient aucune ligne DocPerm en base.
  **Fix** : écriture directe des lignes DocPerm via `frappe.db.set_value` /
  `frappe.get_doc(...).insert()`, contournant la protection du metadata.
- Résultat final vérifié (permission_report, 2026-10-04) :
  - Director, Finance Manager, Operations, Project Lead, Communications,
    Team Member, System Manager : écriture sur les 18 doctypes.
  - People & Culture : écriture sur 6 (Decision, Document, Risk, Growth
    Opportunity, Partnership, Community Impact), lecture seule sur 12
    (finances, budgets, assets, trésorerie, repos, KPI, goals, office).
- Note : la matrice appliquée est plus large que le tableau d'accès de la
  doc 06 (qui prévoit p. ex. Goals & KPI en lecture seule hors Director /
  Project Lead). Si le resserrement est souhaité, il faut étendre le dict
  `overrides` dans `setup.py` puis relancer `seed()`.

## État de la checklist initiale (68 points)
- ✅ Sections 1-2 (installation, connexion, rôles, masquage modules,
  permissions) : vérifiées et conformes.
- ✅ Permissions par rôle : matrice appliquée et vérifiée via
  `permission_report`. Les 5 utilisateurs se connectent (HTTP 200).
- ✅ Masquage étendu : 25 workspaces masqués (tous les modules HRMS +
  ERPNext inutilisés). Seuls 5 restent visibles : Home, RundiNova Tech,
  Frappe CRM, Users, ERPNext Settings.
- ✅ Page onboarding fonctionnelle : `/app/rundinova-onboarding` retourne
  HTTP 200 avec le script JS chargé (2973 caractères).
- ⏳ Sections 3-13 (création de données métier : hub, budgets, dépenses,
  assets, projets, GitHub, goals/KPI, CRM, documents, dashboards, test par
  rôle) : les doctypes et dashboards sont installés ; aucune donnée de test
  n'a encore été saisie — c'est à l'équipe de créer ses premiers
  enregistrements via la page d'onboarding.

## Commandes utiles
```bash
# Ré-exécuter le bootstrap (idempotent)
docker compose -p rundinova --env-file rundinova.env -f compose.yaml \
  -f overrides/compose.redis.yaml -f overrides/compose.mariadb.yaml \
  -f overrides/compose.rundinova-dev.yaml exec backend \
  bench --site erp.rundinova.local execute rundinova_tech.rundinova_tech.bootstrap.run

# Rapport de permissions par rôle (toujours avec -p rundinova)
docker compose -p rundinova --env-file rundinova.env -f compose.yaml \
  -f overrides/compose.redis.yaml -f overrides/compose.mariadb.yaml \
  -f overrides/compose.rundinova-dev.yaml exec backend \
  bench --site erp.rundinova.local execute rundinova_tech.rundinova_tech.bootstrap.permission_report
```

## Commits
- `23bf3c7` Add founding team roles, bootstrap, onboarding page and module hiding
- `73d441a` Fix permission persistence: write DocPerm rows directly
- `2e8f28d` Hide unused workspaces, fix onboarding page path, add missing roles
- `1a312d3` Move onboarding page under module package, add page access verification
- La branche `main` est en avance de 4 commits sur `origin/main` (push à
  faire quand le réseau GitHub est disponible).

## Vérification finale (2026-10-05)
- **Cause racine du problème visible dans le navigateur : deux stacks Docker
  complètes tournaient en parallèle.** Les commandes précédentes ciblaient le
  projet Compose `frappe_docker-*`, tandis que `localhost:18080` était servi
  par `rundinova-frontend-1` (`rundinova-*`) et sa base distincte.
- Le stack réellement servi a été ciblé explicitement avec `docker compose -p
  rundinova ...`.
- `bootstrap.run` y a créé les 5 comptes fondateurs, appliqué les rôles et
  masqué les workspaces manquants. Puis `bench migrate`, `bench build --app
  rundinova_tech`, clear-cache et redémarrage des services ont été exécutés.
- La page `rundinova-onboarding` est présente en base (`standard=Yes`) et
  charge son script (`script=2990`) pour les 5 membres + Administrator.
- La vérification SQL finale indique **25 workspaces masqués / 5 visibles**.
- URL : `http://localhost:18080/app/rundinova-onboarding` (préfixe `/app/`,
  pas `/desk/`). Une requête non authentifiée redirige normalement vers
  `/login`; il faut se connecter avant de tester la page.

### Sidebar effective par utilisateur (`check_sidebar`)
Vérifié côté serveur via `frappe.desk.desktop.get_workspaces()` sur la base
servie par `rundinova-*` :
- Joffre voit **RundiNova Tech, Home, Users**.
- Janvier, Franck, Elvis et Fanuel voient **RundiNova Tech, Users**.
- Administrator voit les 29 workspaces : son rôle `Workspace Manager`
  contourne `is_hidden` dans `desktop.py` (comportement Frappe attendu).
  Pour tester le masquage, utiliser un compte fondateur et non Administrator.
- Le projet `frappe_docker-*` reste une seconde stack sans port publié ; pour
  les prochaines commandes concernant le navigateur, toujours ajouter
  `-p rundinova`.

</content>