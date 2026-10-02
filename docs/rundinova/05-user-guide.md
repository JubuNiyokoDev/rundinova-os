---
title: RundiNova OS - Guide utilisateur complet
---

# RundiNova OS — Guide utilisateur complet

## Principe fondamental

RundiNova OS installe tous les composants nécessaires, mais n'expose aux
utilisateurs que les fonctions dont ils ont besoin. Chaque module peut être
activé ou désactivé sans toucher au code.

---

## Comment activer / désactiver un module

### Via l'interface (sans code)

1. Allez dans **Workspace** (icône carré en haut à gauche).
2. Cliquez sur **RundiNova Tech**.
3. Les liens visibles sont les modules actifs.
4. Pour masquer un module : **Settings > Workspace > RundiNova Tech** et
   décochez le lien correspondant.

### Via les rôles (contrôle d'accès)

Chaque module est lié à des rôles. Si un utilisateur n'a pas le rôle,
il ne voit pas le module.

| Module | Rôles requis |
| --- | --- |
| Budget alimentaire | Director, Finance Manager, Team Member |
| Dépenses générales | Director, Finance Manager |
| Trésorerie | Director, Finance Manager |
| Biens/Équipements | Director, Finance Manager, Project Lead |
| Projets/Tâches | Director, Project Lead, Team Member |
| Repositories GitHub | Director, Project Lead |
| Décisions | Director, Project Lead, Communications |
| Documents | Tous les rôles |
| Goals/KPI | Director, Project Lead, Team Member |
| CRM | Director, Communications |
| Dashboard | Selon le dashboard (voir ci-dessous) |

---

## Modules et leur utilisation

### 1. Équipe et rôles

**Où** : HRMS > Employee List
**Quoi** : 5 employés avec leurs rôles, département, date d'entrée.
**Activation** : Automatique via HRMS. Créez les employés dans l'interface.

### 2. Projets et tâches

**Où** : Projects > Project List / Task List
**Quoi** : Chaque projet a des tâches avec propriétaire, deadline, statut.
**Activation** : Standard ERPNext. Créez un projet, ajoutez des tâches.
**Désactivation** : Masquez le workspace "Projects".

### 3. Intégration GitHub

**Où** : RundiNova Tech > RundiNova Repository
**Quoi** : Enregistrez vos repos GitHub. Cliquez "Sync from GitHub" pour
mettre à jour les stats (issues, stars, forks, dernier push).
**Activation** : Créez un record "RundiNova Repository" avec l'URL du repo.
**Note** : Lecture seule. Ne modifie jamais rien sur GitHub.

### 4. Budget alimentaire

**Où** : RundiNova Tech > RundiNova Food Budget
**Quoi** : Budget mensuel de 1 150 000 FBu. Chaque achat est un
"RundiNova Food Expense" avec date, catégorie, article, quantité, montant,
fournisseur, payeur, reçu.
**Activation** : Créez un budget pour le mois, puis enregistrez les achats.
**Règle** : Les achats peuvent changer (viande → poisson). L'historique
reste intact.

### 5. Dépenses générales

**Où** : RundiNova Tech > RundiNova Expense
**Quoi** : Dépenses non-alimentaires avec approbation et justificatif.
**Activation** : Créez une dépense, attachez le reçu, soumettez pour approbation.

### 6. Trésorerie / Comptabilité de base

**Où** : RundiNova Tech > RundiNova Cash Account / Cash Movement
**Quoi** : Comptes cash (caisse, banque, mobile money) et mouvements.
**Activation** : Créez les comptes, puis enregistrez les entrées/sorties.
**Solde** : Calculé automatiquement à chaque mouvement approuvé.

### 7. Biens et équipements

**Où** : RundiNova Tech > RundiNova Asset
**Quoi** : Ordinateurs, meubles, licences, avec responsable et statut.
**Activation** : Créez un asset avec nom, catégorie, responsable, valeur.

### 8. CRM et communication interne

**Où** : CRM (workspace dédié)
**Quoi** : Contacts, opportunités, activités, notes de réunion.
Sert aussi de communication interne : décisions, annonces, suivi.
**Activation** : Standard Frappe CRM. Créez des contacts et activités.

### 9. KPI et objectifs

**Où** : RundiNova Tech > RundiNova Goal
**Quoi** : Objectifs mesurables avec cible, valeur actuelle, %.
**Activation** : Créez un goal avec titre, type, owner, période, cible.
Le % se calcule automatiquement.

### 10. Documents et rapports

**Où** : RundiNova Tech > RundiNova Document
**Quoi** : Registre documentaire : contrats, factures, rapports, médias.
**Activation** : Créez un document avec titre, catégorie, propriétaire.

### 11. Tableau de bord de direction

**Où** : RundiNova Tech workspace > Dashboards
**Quoi** : 5 dashboards (Executive, Finance, People, Delivery, Ecosystem).
**Activation** : Automatique après `seed()`. Visibles selon les rôles.

### 12. Sécurité et audit

**Où** : Settings > Audit Log / Activity Log
**Quoi** : Toute modification est tracée (qui, quoi, quand).
**Activation** : Standard Frappe. Toujours actif.

### 13. Page d'onboarding

**Où** : /app/rundinova-onboarding
**Quoi** : Checklist de préparation avant production.
**Activation** : Toujours disponible. Lecture seule.

---

## Ce qui est désactivé par défaut

Les modules ERPNext suivants sont installés mais NON exposés :

- Manufacturing
- Stock / Inventory
- Payroll
- Marketing avancé
- Multi-company accounting
- Quality Management
- Education

Ils restent accessibles si un besoin futur est validé.

---

## Commandes utiles

```bash
# Lancer le serveur
docker compose up -d

# Accéder au site
http://localhost:18080

# Migrer après mise à jour du code
docker compose exec backend bench --site all migrate

# Réinstaller l'app (attention : efface les données de l'app)
docker compose exec backend bench --site all uninstall-app rundinova_tech
docker compose exec backend bench --site all install-app rundinova_tech

# Lancer les tests
cd apps/rundinova_tech && python3 -m pytest rundinova_tech/tests/ -v
```

---

## Prochaines étapes

1. Valider les 5 utilisateurs et leurs rôles.
2. Créer le premier projet et lier les repos GitHub.
3. Tester le budget alimentaire avec de vrais achats.
4. Configurer les comptes de trésorerie.
5. Vérifier les dashboards.
6. Déployer en production (voir 03-rollout.md).
