# Recette de production — RundiNova Tech

Ce document sert à vérifier les parcours réellement utilisables par l’équipe sur `https://workspace.rundinova.com`. Il ne contient ni mot de passe, ni secret, ni donnée fictive à importer.

## Règles de recette

- Chaque membre se connecte avec son propre compte et vérifie les opérations autorisées pour son rôle.
- Utiliser uniquement des projets, achats, dépenses, partenaires et documents réels de RundiNova.
- Ne pas créer de faux paiement, mouvement bancaire, dépense ou consommation pour « tester ».
- Avant de soumettre une opération financière, vérifier le justificatif, le montant, la devise FBU, le budget et le compte de paiement.
- Pour chaque anomalie, noter l’utilisateur, l’URL, l’heure, les étapes, le résultat attendu et le résultat obtenu. Ne jamais joindre de mot de passe ni de secret.

## Comptes et identité de l’équipe

Les membres utilisent leur adresse réelle et leur propre compte. Cette recette ne
contient aucun mot de passe. Les rôles ci-dessous décrivent les parcours à
vérifier; ils ne donnent pas implicitement accès aux données confidentielles.

| Membre                | Adresse de connexion           | Parcours métier                                                       |
| --------------------- | ------------------------------ | --------------------------------------------------------------------- |
| Joffre Niyondiko      | `joffre.niyondiko@kit-hub.com` | Direction, pilotage, projets et validations selon ses rôles attribués |
| Janvier Ndabubaha     | `ndabubahajanvier@gmail.com`   | Écosystème, partenariats et opportunités                              |
| Elvis Presira         | `presira857@gmail.com`         | Communication et activités CRM autorisées                             |
| Franck Maniranyibutse | `maniranyibutsef@gmail.com`    | Croissance, prospects et opportunités                                 |
| Fanuel Mandela        | `mandela.fanuel.1@gmail.com`   | Relations communautaires, activités et impact                         |
| Housekeeping          | `vyamungucharif410@gmail.com` | Opérations de son poste et libre-service limité                       |

Le rôle `RundiNova Director` ne transforme pas Joffre en compte système
`Administrator`. La recette doit confirmer les autorisations effectives de
chaque compte dans la version en production avant d'enregistrer une opération.

## Parcours commun — chaque membre

| Contrôle                              | Résultat attendu                                                                             | Fait / anomalie |
| ------------------------------------- | -------------------------------------------------------------------------------------------- | --------------- |
| Connexion à son compte nominatif      | Le compte s’ouvre et affiche le bon nom et la bonne adresse                                  |                 |
| Changement du mot de passe temporaire | Le membre définit un mot de passe individuel et peut se reconnecter                          |                 |
| Profil utilisateur                    | Nom, photo et coordonnées modifiables selon les droits accordés                              |                 |
| Accueil RundiNova                     | Les raccourcis visibles ouvrent les bonnes pages, sans « Page not found »                    |                 |
| Navigation et recherche               | Le membre trouve les fonctions nécessaires depuis le menu ou la recherche                    |                 |
| Droits                                | Les pages autorisées s’ouvrent ; les données confidentielles hors rôle restent inaccessibles |                 |
| Notifications                         | Les alertes dans l’application sont visibles et ouvrent le bon document                      |                 |

## Recette par rôle

### Direction — Joffre, RundiNova Director / Project Lead

- Ouvrir les tableaux de bord exécutif et RundiNova ; vérifier que les KPI et montants affichés correspondent aux données réelles.
- Consulter les budgets, projets, tâches, partenariats et rapports auxquels la Direction a accès.
- Créer ou mettre à jour un projet réel, lui associer son responsable et ses premières tâches réelles.
- Vérifier les validations financières et les historiques d’activité.
- Contrôler que les fiches des autres employés sont visibles seulement si le rôle de Direction le prévoit.
- Vérifier les réglages réservés à l’administration : le rôle `RundiNova Director` n’est pas le compte superutilisateur `Administrator`.

### Écosystème — Janvier Ndabubaha, RundiNova Ecosystem Lead

Compte : `ndabubahajanvier@gmail.com`.

- Ouvrir les partenariats et opportunités réellement suivis.
- Créer ou actualiser une fiche réelle avec organisation, contact, statut, responsable et prochaine action.
- Vérifier les tableaux de bord Écosystème et les indicateurs associés.
- Confirmer qu’il ne peut pas modifier les paramètres financiers ou les comptes utilisateurs hors de son rôle.

### Croissance — Franck Maniranyibutse, RundiNova Growth Lead

Compte : `maniranyibutsef@gmail.com`.

- Ouvrir les pistes, opportunités et activités de croissance réellement suivies.
- Mettre à jour le statut, le responsable, la prochaine action et les notes d’un dossier réel.
- Vérifier l’accès aux projets et tâches qui lui sont attribués.
- Confirmer les limites d’accès aux informations RH et financières.

### Relations communautaires — Fanuel Mandela, RundiNova Community Relations

Compte : `mandela.fanuel.1@gmail.com`.

- Ouvrir les programmes, activités, participants et bénéficiaires réels relevant de son travail.
- Enregistrer une activité ou mettre à jour une fiche réelle, avec date et responsable.
- Vérifier les tableaux de bord d’impact et leurs filtres.
- Confirmer qu’aucune donnée personnelle non nécessaire n’est visible ou exportable.

### Communication — Elvis Presira, RundiNova Communications / Team Member

Compte : `presira857@gmail.com`.

- Ouvrir les contacts, activités et documents de communication autorisés.
- Créer ou mettre à jour une activité réelle et vérifier son historique.
- Vérifier les notifications internes.
- Lorsque l’envoi et la réception de courriels seront configurés, envoyer un message interne de recette puis vérifier la réponse entrante et son rattachement au bon contact.

### Housekeeping — RundiNova Team Member

- Se connecter avec l’identifiant `vyamungucharif410@gmail.com`.
- Vérifier que la fiche Housekeeping est liée au compte et que le membre ne voit pas les dossiers RH confidentiels de l’équipe.
- Confirmer que seuls les raccourcis opérationnels du rôle Team Member sont accessibles.

## Parcours métier de bout en bout

### Projets et tâches

1. Enregistrer un projet réellement approuvé, son responsable, son état et ses dates.
2. Ajouter les premières tâches réellement convenues, avec responsable, échéance et priorité.
3. Mettre une tâche à jour, ajouter un commentaire utile et vérifier l’historique.
4. Vérifier les vues Projet, Tâches et le tableau de bord Projets & livraison.

### GitHub — PartenerWanje

Le dépôt `JubuNiyokoDev/PartenerWanje` est privé et sa branche principale est
`main`. La synchronisation GitHub de RundiNova est en lecture seule : elle
affiche les métadonnées et les cinq derniers commits. Elle ne crée pas de
tâches et ne modifie pas le dépôt.

1. Après configuration du token restreint sur le serveur, ouvrir la fiche
   `RundiNova Repository` liée à PartenerWanje et lancer la synchronisation.
2. Vérifier le nom, la branche et le dernier commit, sans afficher ni copier le
   token dans l'interface.
3. Confirmer que le bouton n'écrit rien sur GitHub et qu'aucune tâche n'est
   créée automatiquement.
4. Examiner ensemble la feuille de route réelle du dépôt, puis décider des
   premières tâches à suivre dans RundiNova et/ou GitHub pour éviter les
   doublons.

### Budget alimentaire et achat

1. Vérifier le budget réel, sa période, ses lignes et son solde avant achat.
2. Enregistrer un achat uniquement à partir d’un achat réel : date, article, quantité, montant FBU, fournisseur et justificatif disponible.
3. Vérifier que l’achat apparaît dans les achats alimentaires et que les consommations et soldes sont recalculés une seule fois.
4. Faire approuver/soumettre l’opération selon le processus défini par RundiNova.

### Dépenses, caisse et banque

1. Vérifier les comptes de caisse et le compte bancaire KCB configurés, leur devise FBU et leur solde d’ouverture confirmé.
2. Saisir uniquement une dépense ou un mouvement réel, avec justificatif, catégorie, compte et approbateur.
3. Vérifier le solde avant/après et le rapprochement avec le reçu ou le relevé.
4. Ne jamais enregistrer un solde estimé comme mouvement réel.

### RH et équipe

1. Vérifier les cinq comptes nominatifs et leurs fiches Employé liées.
2. Confirmer l’identité, le département, la fonction, l’agence et le responsable de chaque fiche.
3. Tester la consultation du profil et les modifications personnelles permises.
4. Vérifier qu’un membre ne peut pas consulter les dossiers RH confidentiels d’un autre sans autorisation.

### Communication par courriel

- Le test d’envoi/réception est en attente de configuration d’un fournisseur de courrier sortant et entrant.
- Une fois configuré, vérifier l’envoi, la réception, les réponses, les notifications et les journaux d’erreur.
- Ne pas inscrire de mot de passe Gmail dans un ticket ou dans ce document.

### GitHub et suivi des dépôts

1. Ajouter uniquement les dépôts RundiNova prioritaires, avec leur URL et leur équipe responsable.
2. Vérifier que le lien du dépôt s’ouvre pour les membres autorisés.
3. Associer un projet réel à son dépôt et créer des tâches à partir du travail réellement planifié.
4. Si une intégration automatisée est activée, tester d’abord sur un dépôt non critique et vérifier les permissions OAuth minimales.

## Compte rendu de chaque test

| Date / heure | Utilisateur et rôle | Parcours | Résultat (OK / anomalie / bloqué) | URL ou référence | Détail sans secret |
| ------------ | ------------------- | -------- | --------------------------------- | ---------------- | ------------------ |
|              |                     |          |                                   |                  |                    |

## Critères de démarrage

- Les cinq membres peuvent se connecter avec leur propre compte et ont changé le mot de passe commun temporaire.
- Les fonctions importantes de chaque rôle s’ouvrent et les restrictions de confidentialité sont vérifiées.
- Les parcours projet/tâche et finance ont été vérifiés avec des opérations réelles et leurs justificatifs.
- L’envoi/réception de courriels est validé avant de dépendre des courriels de réinitialisation ou des notifications.
- Les dépôts GitHub prioritaires et leurs responsables sont confirmés.
- Les anomalies bloquantes sont corrigées avant d’étendre l’utilisation à toute l’équipe.
