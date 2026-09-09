# Présence — pointeuse locale Windows

Application locale de pointage avec PC attribué, code personnel par employé, jours fériés, week-end vendredi–samedi et rapports PDF mensuels.

## Ce que fait l’application

### Sur le PC de l’employé

- Le PC est attribué une seule fois à son employé par le responsable.
- L’employé ouvre le raccourci **Pointeuse** placé sur son Bureau.
- Il saisit son **prénom**, son **nom** et son **code PIN personnel**.
- Il clique sur **Pointer l’arrivée**, **Début de pause**, **Reprendre le travail** ou **Pointer le départ**.
- Un autre employé ne peut pas pointer depuis ce PC avec son propre code.
- Une **horloge** en direct s’affiche en haut de l’écran.

### Dans l’administration

- Menu latéral à gauche avec accès direct à chaque rubrique.
- Tableau journalier : nom et prénom, heure d’arrivée, début de pause, reprise, départ, **heures travaillées**, **retard** et **heures en plus** (8 h/jour, pause comprise).
- Consultation de n’importe quelle date.
- Ajout et retrait d’employés.
- Définition et modification des codes personnels.
- Date de début modifiable pour chaque employé ; les dates antérieures restent vides.
- Attribution et dissociation des PC.
- Ajout et suppression des jours fériés.
- **Horaires de travail** : réglage des heures d’arrivée, de début de pause, de reprise et de départ (l’heure d’arrivée sert de référence au calcul des retards).
- Ajout de périodes de congé par employé, avec date de début, date de fin et motif.
- Vendredi et samedi automatiquement considérés comme week-end.
- Export CSV journalier.
- Correction administrative : définir, modifier ou supprimer séparément une arrivée ou un départ.
- Rapport PDF mensuel détaillé avec les pointages horaires et une ligne de total par employé.
- Calcul automatique des jours travaillés, des absences, des **heures travaillées** (norme 8 h/jour, pause comprise) et des **retards cumulés** en heures et minutes.

## Rapports mensuels complets

Chaque tableau couvre le mois civil complet, du 1er au dernier jour réel :

- février : 28 ou 29 jours ;
- avril, juin, septembre et novembre : 30 jours ;
- les autres mois : 31 jours.

Le 28, l’application crée un **aperçu provisoire** du mois courant. Le 1er du mois suivant, elle crée le **rapport final** du mois terminé. Exemple : l’aperçu d’août va du 1er au 31 août, puis le rapport final d’août est créé le 1er septembre.

Les lignes antérieures à la date de début de l’employé, la journée actuelle sans pointage et les jours futurs restent vides.

Le PDF contient une page par employé avec les colonnes suivantes :

1. Nom et prénom ;
2. Date du jour ;
3. Heure d’arrivée ;
4. Début de pause ;
5. Reprise ;
6. Heure de sortie ;
7. **Heures** travaillées ce jour-là (8 h/jour, pause comprise) ;
8. **En plus** : les minutes au-delà de la norme de 8 h (heures supplémentaires).

Une ligne **TOTAL** au bas de chaque tableau indique les **heures travaillées du mois**, les **retards cumulés** (en heures et minutes), le nombre de journées travaillées et le nombre de jours d’absence. Les retards sont comptés par rapport à l’heure d’arrivée prévue. Les congés, jours fériés, vendredis et samedis sont exclus du calcul des absences.

Le serveur vérifie les rapports toutes les heures. S’il était éteint le 28, le rapport manquant est généré au prochain démarrage. Les fichiers sont conservés dans `rapports`.

## Installation rapide

### 1. Sur le PC serveur

1. Installez Python 3 en cochant **Add Python to PATH**.
2. Décompressez ce dossier dans un emplacement fixe, par exemple `C:\Pointeuse`.
3. Double-cliquez sur `demarrer_pointeuse.bat`.
4. Ouvrez `http://localhost:8000/admin`.
5. Connectez-vous avec le code initial **1234**, puis changez-le.
6. Ajoutez chaque employé avec son PIN individuel et sa date de début. Cette date détermine à partir de quand les absences peuvent être calculées.

### 2. Sur chaque PC employé

1. Copiez uniquement `installer_raccourci_employe.bat` sur le PC.
2. Double-cliquez dessus.
3. Saisissez l’adresse affichée sur le PC serveur, par exemple `192.168.1.20:8000`.
4. Un raccourci **Pointeuse** apparaît sur le Bureau.
5. La première fois, le responsable choisit l’employé propriétaire du PC et saisit le code administrateur.
6. Ensuite, l’employé ouvre simplement le raccourci et saisit son identité et son PIN.

Consultez `INSTALLATION_WINDOWS.md` pour les étapes détaillées et le pare-feu Windows.

## Fichiers et données

- `app.py` : application et serveur local.
- `pointeuse.db` : employés, pointages et jours fériés.
- `pointeuse.secret` : clé interne des sessions.
- `rapports` : rapports mensuels PDF.
- `installer_raccourci_employe.bat` : création du raccourci sur un PC employé.
- `sauvegarder_donnees.bat` : sauvegarde des données et rapports.

L’application n’a besoin d’aucune bibliothèque Python supplémentaire.

## Codes de démonstration

Uniquement avec l’option `--demo` :

- Amine Benali : `1111`
- Sarah Mansouri : `2222`
- Yacine Haddad : `3333`

Code administrateur initial : `1234`.

## Important

L’attribution du PC repose sur une clé conservée dans le navigateur. Le raccourci doit toujours être utilisé avec le même profil Edge. Si les données du navigateur sont effacées, le responsable devra attribuer le PC à nouveau.

« Absent » signifie qu’aucune arrivée n’est enregistrée pendant un jour ouvré passé, à partir de la date de début de l’employé. Les vendredis, samedis, jours fériés et périodes de congé enregistrées ne sont pas comptés comme absences. Une journée d’absence correspond à 8 heures (norme quotidienne, pause comprise). Avant la date de début, aujourd’hui sans pointage et dans le futur, les cellules restent vides.

Les **heures travaillées** d’une journée correspondent au temps de présence entre l’arrivée et la sortie, **pause incluse** (la norme est de 8 h par jour). Exemple : une arrivée à 9 h 00 au lieu de 8 h 30 donne 7 h 30 de travail ce jour-là. Le **retard** est compté en minutes après l’heure d’arrivée prévue ; il est ensuite cumulé et affiché en heures et minutes dans la ligne de total. La colonne **« En plus »** indique les minutes au-delà de la norme de 8 h (par exemple : 8 h 45 de présence → **+0 h 45**).

La page employé ne contient aucun lien vers l’administration. L’administration est accessible uniquement en saisissant directement l’adresse `http://ADRESSE-DU-SERVEUR:8000/admin`.
