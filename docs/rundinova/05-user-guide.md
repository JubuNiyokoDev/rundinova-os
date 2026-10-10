---
title: RundiNova OS - Guide utilisateur complet
---

# RundiNova OS — Guide utilisateur complet

## Principe fondamental

RundiNova OS installe tous les composants nécessaires, mais n'expose aux
utilisateurs que les fonctions dont ils ont besoin. Chaque module peut être
activé ou désactivé sans toucher au code.

---

## Navigation et espaces de travail

La page `/desk` ouvre directement **RundiNova Tech**. C’est l’espace de travail
principal de tous les rôles RundiNova; les liens visibles et les données restent
filtrés par les permissions du compte. Les cinq dashboards apparaissent en haut,
puis les raccourcis sont groupés par organisation, finance et achats, projets et
livraison, communication et partenariats, équipe et gouvernance. Les liens **Projets**, **Tâches**, **Budget
alimentaire**, **Achats alimentaires**, **Dépenses générales**, **Comptes de
trésorerie** et **Mouvements de trésorerie** ouvrent directement les listes.

Le menu latéral reste visible depuis les dashboards et reprend les destinations
opérationnelles. Il évite de mémoriser les URL. La page **Configuration
RundiNova** est accessible depuis la section Administration du menu; elle
regroupe les réglages de l’entreprise, des articles et des utilisateurs.

Pour ouvrir son compte, cliquer sur son avatar, son nom ou son adresse e-mail en
bas du menu latéral. **Mon profil** ouvre sa propre fiche utilisateur. Le champ
**User Image** permet de téléverser la photo; les coordonnées et préférences
personnelles modifiables y sont disponibles. Les rôles et accès restent gérés
par l’administration.

| Espace                      | Qui le voit                                  | Usage                                                                    |
| --------------------------- | -------------------------------------------- | ------------------------------------------------------------------------ |
| **RundiNova Tech**          | Tous les rôles RundiNova                     | Accueil commun; dashboards et raccourcis filtrés selon les autorisations |
| **Configuration RundiNova** | Direction, Finance, Operations, Project Lead | Page dédiée aux paramètres de base; accessible depuis Administration     |

Les espaces internes Finance, Dashboards et Équipe ne sont pas affichés comme
des destinations supplémentaires. Les paramètres restent groupés dans
**Configuration RundiNova**, sans mélanger les listes de travail quotidien et
les écrans de configuration ERPNext.

Un raccourci visible ne remplace jamais la permission du document. Chaque
liste, fiche, carte KPI et graphique reste filtré par les permissions du
compte. Un utilisateur ayant uniquement le rôle Team Member n'accède pas aux
espaces Finance et Dashboards; ses dépenses restent limitées aux
enregistrements qu'il a créés ou qui lui sont affectés.

Les espaces, raccourcis et icônes du lanceur sont synchronisés par
l'application pendant `bench migrate`. Pour changer durablement la
navigation, modifier `rundinova_tech.rundinova_tech.provisioning.workspaces`;
une modification manuelle dans Desk sera remplacée à la prochaine migration.

---

## Modules et leur utilisation

### 1. Équipe et rôles

**Où** : HRMS > Employee List
**Quoi** : 5 employés avec leurs rôles, département, date d'entrée.
**Activation** : Automatique via HRMS. Créez les employés dans l'interface.

### 2. Projets et tâches

**Où** : RundiNova Tech > **Projets** / **Tâches**.
**Quoi** : Chaque projet peut regrouper des tâches avec responsable, échéance
et statut.
**Activation** : un Project Lead ou Operations crée le projet et les tâches;
les collaborateurs consultent les tâches autorisées depuis RundiNova Équipe.

### 3. Intégration GitHub

**Où** : RundiNova Tech > RundiNova Repository
**Quoi** : Enregistrez vos repos GitHub. Cliquez "Sync from GitHub" pour
mettre à jour les stats (issues, stars, forks, dernier push).
**Activation** : Créez un record "RundiNova Repository" avec l'URL du repo.
**Note** : Lecture seule. Ne modifie jamais rien sur GitHub.

### 4. Budget alimentaire

**Où** : Dans **RundiNova Tech**, ouvrez **Progression Food** et utilisez le
bouton **Acheter** sur la ligne de l’article. Depuis un budget ouvert, le bouton
**Enregistrer un achat** ouvre le même parcours rapide. La création générique
depuis la liste **Achats alimentaires** demande d’abord le budget et l’article.

**Achat au marché sans facture fournisseur** : choisissez l’article, puis
saisissez la quantité et le montant total. L’unité vient du budget; la date du
jour et le paiement comptant sont proposés par défaut. Le fournisseur, le reçu
et la note sont facultatifs. Pour 5 kg de riz payés comptant,
indiquez par exemple Article « Riz », Quantité `5`, Unité `Kg`, Paiement
« Cash » et Statut « Paid ». Le fournisseur et le reçu peuvent être ajoutés
s'ils sont disponibles; les notes peuvent préciser le nom du marché.
La date de l'achat doit appartenir à la période du budget sélectionné; créez
d'abord le budget du mois si aucun budget ne couvre cette date.

**Accès au budget** : Finance ou un Director doit affecter le budget aux
collaborateurs concernés avec l'action **Assigner**. Un Team Member ne voit
dans le formulaire que les budgets dont il est propriétaire ou auquel il est
affecté. Sans affectation, il ne peut pas sélectionner le budget obligatoire
de l'achat.

**Avant le premier règlement en caisse** : un Director ou Finance Manager crée
un compte dans **Comptes de trésorerie** (type, devise, date et solde réel à la
date de départ). Ne remplacez pas un solde inconnu par `0` : le solde initial
doit correspondre à l'argent réellement présent.

Après avoir enregistré l'achat au statut **Paid**, Finance ouvre
**Mouvements de trésorerie**, choisit l'achat et le compte utilisé, puis joint
le reçu ou une autre preuve de paiement. Les détails de l'achat sont repris
automatiquement. La preuve est obligatoire pour soumettre le mouvement; le
solde de caisse ne change qu'une fois le mouvement **Approved** ou
**Reconciled**. L'équipe peut saisir l'achat, tandis que Finance enregistre et
valide le mouvement de caisse.

La **Progression Food** correspondante est créée automatiquement au premier
achat d'un article du budget. Le **Compte de trésorerie** est une configuration
à créer une fois pour chaque vraie caisse, banque ou porte-monnaie mobile. Un
**Mouvement de trésorerie** est créé pour chaque entrée ou sortie réelle; il
n'est pas inventé automatiquement depuis un achat alimentaire. Une **Revue de
budget** est créée lors d'une revue effective (par exemple en fin de mois), pas
pour chaque achat. Une **Dépense générale** est créée pour chaque dépense réelle
hors alimentation.

**Achat avec facture fournisseur** : créez la facture dans **Purchase Invoice**
et renseignez le budget alimentaire. À la soumission, chaque ligne d'article
est synchronisée comme achat alimentaire. Ne saisissez pas une deuxième fois
les mêmes lignes dans **Achats alimentaires**.

Les achats aux statuts **Submitted**, **Approved** et **Paid** sont comptés
dans le budget engagé; **Paid** alimente aussi le montant réellement payé.
Les statuts **Rejected** et **Cancelled** ne sont pas comptés. L'article et la
quantité restent dans l'historique, même si le menu change plus tard.

### 5. Dépenses générales

**Où** : RundiNova Tech > RundiNova Expense
**Quoi** : Dépenses non-alimentaires avec approbation et justificatif.
**Activation** : Créez une dépense, attachez le reçu, soumettez pour approbation.

### 6. Trésorerie / Comptabilité de base

**Où** : Finance & trésorerie > Comptes de trésorerie / Mouvements de trésorerie
**Quoi** : Comptes cash (caisse, banque, mobile money) et mouvements.
**Mise en service** : enregistrez le vrai solde initial et sa date avant de
rapprocher les achats. Seuls les mouvements approuvés ou rapprochés sont
comptés dans le solde courant.
**Activation** : Créez les comptes, puis enregistrez les entrées/sorties.
**Solde** : Calculé automatiquement à chaque mouvement approuvé.

### 7. Biens et équipements

**Où** : RundiNova Tech > RundiNova Asset
**Quoi** : Ordinateurs, meubles, licences, avec responsable et statut.
**Activation** : Créez un asset avec nom, catégorie, responsable, valeur.

### 8. CRM et communication

**Où** : RundiNova Tech > **Communication & partenariats**. Le lien **CRM &
communications** ouvre Frappe CRM; les raccourcis **Opportunités**,
**Partenariats** et **Activités communautaires** ouvrent les registres RundiNova.
**Quoi** : contacts et échanges commerciaux dans le CRM; pipeline et partenaires
dans les registres RundiNova; décisions et réunions dans **Décisions & réunions**.
Les entrées CRM sont des fiches opérationnelles à créer au fil des relations,
pas des écrans de configuration.

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

**Où** : RundiNova Tech > Tableaux de bord (également dans RundiNova Dashboards)
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
