# Mode de rapport d'équipe — RundiNova

## 1. Rapport d'une tâche (obligatoire, court)

Chaque personne met à jour **sa tâche** directement dans `Projets & livraison > Tâches`.

1. Au démarrage, choisir `Working`.
2. À la fin du travail, renseigner `Résultat de recette` : `Validé`, `À corriger`, `Bloqué` ou `Non applicable`.
3. Renseigner `Résumé de mise à jour` avec une phrase courte, visible immédiatement dans la liste des tâches.
4. Écrire dans `Constat / anomalie` un rapport court : ce qui a été fait, le résultat observé et la suite éventuelle.
5. `Mis à jour par` est rempli automatiquement lors de l'enregistrement ; il ne faut pas le modifier.
6. Une capture, un fichier ou un lien est ajouté seulement lorsqu'il apporte une preuve utile. Il n'est pas obligatoire pour une tâche qui peut être expliquée et validée sans pièce jointe.
7. Pour une tâche validée : mettre `Status = Completed` et `Résultat de recette = Validé`.
8. Pour une anomalie : mettre `Résultat de recette = À corriger`, garder ou remettre la tâche en `Working`, et créer une tâche de correction si elle est distincte.
9. Pour un blocage : mettre `Résultat de recette = Bloqué` et indiquer clairement qui ou quoi est attendu.

### Modèle à coller dans « Constat / anomalie »

```text
Date :
Travail / scénario réalisé :
Résultat observé :
Décision : Validé / À corriger / Bloqué
Suite ou personne attendue :
```

Exemple sans capture :

```text
Date : 30/10/2026
Travail / scénario réalisé : création d'un patient, triage puis consultation infirmière.
Résultat observé : le parcours s'est déroulé normalement ; dossier et timeline corrects.
Décision : Validé
Suite ou personne attendue : aucune.
```

## 2. Rapport hebdomadaire ou de recette

Un rapport qui concerne plusieurs tâches se crée dans `Documents & fichiers` :

1. `Nouveau document`
2. Titre : `[Medicare] Rapport de recette — semaine du 30/10/2026`
3. Type de document : `Report`
4. Projet : `Medicare`
5. Responsable, date, confidentialité `Internal`, statut `Active`
6. Dans Notes : synthèse, tâches validées, anomalies, blocages, décisions et prochaines actions.
7. Ajouter un PDF seulement lorsqu'il est nécessaire ; le rapport peut aussi exister dans Notes.

## 3. Décision prise en réunion

Dans `Décisions & réunions`, créer une décision lorsque l'équipe prend une direction, accepte une livraison, fixe une échéance ou arbitre un blocage.

- Type : `Project Review` ou `Team Meeting`
- Projet : le projet concerné
- Décision prise : formulation claire et vérifiable
- Responsable + date de suivi
- Tâche de suivi : lier ou créer la tâche qui exécute la décision

## 4. Règle de pilotage

La plateforme est la source de vérité. Le groupe WhatsApp/Telegram sert à prévenir, mais toute avancée, validation, blocage ou décision doit être reportée dans RundiNova le même jour.

Le CEO suit les tâches depuis la liste sans ouvrir chaque fiche : `Status` indique l'avancement et `Résultat de recette` indique si le travail est réellement validé.
