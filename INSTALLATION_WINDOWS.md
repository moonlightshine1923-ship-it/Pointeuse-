# Installation exacte sur les PC Windows

## A. Installer le serveur

Le serveur est le PC qui conserve toutes les données. Il doit rester allumé pendant les heures de pointage.

1. Installez Python 3 depuis le site officiel.
2. Pendant l’installation, cochez **Add python.exe to PATH**.
3. Placez le dossier dans un emplacement fixe, par exemple `C:\Pointeuse`.
4. Double-cliquez sur `demarrer_pointeuse.bat`.
5. Ne fermez pas la fenêtre noire pendant la journée.

La fenêtre affiche deux adresses :

```text
Administration : http://localhost:8000/admin
Adresse pour les PC employés : http://192.168.1.20:8000
```

L’adresse `192.168…` est celle à utiliser sur les autres PC.

## B. Première configuration administrateur

1. Sur le serveur, ouvrez `http://localhost:8000/admin`.
2. Saisissez le code initial `1234`.
3. Dans **Sécurité et correction**, changez immédiatement ce code.
4. Dans **Employés et PC attribués**, saisissez prénom, nom, date de début et PIN individuel.
5. Communiquez chaque PIN uniquement à son employé.

La date de début détermine le premier jour suivi. Les dates antérieures seront visibles dans le tableau mensuel, mais leurs cellules resteront vides. Cette date peut être modifiée ensuite depuis l’administration.

Un PIN doit comporter au moins quatre caractères. N’utilisez pas le même PIN pour tout le monde.

## C. Autoriser le réseau local

Si les autres PC n’ouvrent pas l’adresse :

1. Ouvrez **Sécurité Windows**.
2. Choisissez **Pare-feu et protection réseau**.
3. Choisissez **Autoriser une application via le pare-feu**.
4. Autorisez Python sur les réseaux **privés** uniquement.

Les PC employés et le serveur doivent être connectés au même réseau.

## D. Créer le raccourci sur chaque PC employé

Pour chaque employé, répétez exactement ceci :

1. Copiez `installer_raccourci_employe.bat` sur son PC.
2. Double-cliquez sur le fichier.
3. À la question « Adresse affichée par le serveur », saisissez par exemple :

```text
192.168.1.20:8000
```

4. Le script crée une icône **Pointeuse** sur le Bureau.
5. La page s’ouvre pour la première configuration.
6. Le responsable choisit le propriétaire de ce PC dans la liste.
7. Le responsable saisit le code administrateur.
8. Il clique sur **Attribuer ce PC**.

Cette attribution empêche l’utilisation du code d’un autre employé sur ce poste.

## E. Utilisation par l’employé

### Arrivée

1. L’employé allume son PC et ouvre sa session Windows.
2. Il double-clique sur **Pointeuse** sur le Bureau.
3. Une petite fenêtre Edge dédiée s’ouvre.
4. Il saisit son prénom, son nom et son PIN personnel.
5. Il clique sur **Pointer l’arrivée**.
6. L’heure enregistrée s’affiche immédiatement.

### Départ

1. Il ouvre de nouveau le raccourci **Pointeuse**.
2. Il saisit son prénom, son nom et son PIN.
3. Il clique sur **Pointer le départ**.

Une arrivée ou un départ ne peut pas être enregistré deux fois le même jour.

## F. Jours fériés et week-ends

Dans la rubrique **Jours fériés** :

1. choisissez la date ;
2. saisissez un libellé, par exemple « Fête nationale » ;
3. cliquez sur **Ajouter**.

Vendredi et samedi sont automatiquement classés comme week-end. Une absence n’est donc pas comptée ces jours-là. Si un employé travaille exceptionnellement pendant un week-end ou un jour férié, il peut pointer et sera classé Présent.

## G. Congés des employés

Dans **Congés des employés** :

1. choisissez l’employé ;
2. saisissez la date de début et la date de fin ;
3. saisissez le motif, par exemple « Congé annuel » ;
4. cliquez sur **Ajouter le congé**.

Les jours ouvrés compris dans cette période apparaissent comme **Congé** et ne sont pas comptés comme absences. Les vendredis, samedis et jours fériés gardent leur propre statut, même lorsqu’ils sont compris dans une période de congé.

## H. Rapports mensuels : aperçu le 28 et final le 1er

Le tableau couvre toujours le mois entier, du 1er au dernier jour réel : 28 ou 29 jours en février, 30 ou 31 jours pour les autres mois.

- le 28 : création d’un aperçu provisoire du mois courant ;
- le 1er du mois suivant : création du rapport final du mois terminé.

Exemple : l’aperçu d’août contient les lignes du 1er au 31 août. Le rapport final d’août est créé le 1er septembre. Les dates antérieures au début de l’employé, la journée actuelle sans pointage et les dates futures restent vides.

Le rapport indique à la fin du tableau de chaque employé :

- le total des jours travaillés ;
- le total des heures travaillées ;
- le total des jours d’absence ;
- le total des heures d’absence, sur une base de 7 heures par jour ;
- les jours de congé, week-ends et jours fériés.

Dans **Rapports PDF**, vous pouvez télécharger l’aperçu du mois courant, télécharger le dernier rapport final et ouvrir les anciens fichiers. Du 28 à la fin du mois, l’aperçu est actualisé. Le 1er, le mois précédent est finalisé.

Pour la génération automatique, le serveur doit être lancé. S’il était éteint, le rapport manquant est rattrapé dès son prochain démarrage.

## I. Sauvegarde

Double-cliquez sur `sauvegarder_donnees.bat`. La sauvegarde contient :

- la base SQLite ;
- la clé interne ;
- les rapports PDF existants.

Copiez régulièrement le dossier `sauvegardes` sur un support externe.

## J. En cas de problème

### Le PC demande une nouvelle attribution

Le cookie du navigateur a probablement été supprimé. Recommencez l’étape D avec le code administrateur.

### Un employé oublie son code

Dans l’administration, utilisez **Changer un code employé**. Les codes ne sont jamais affichés en clair.

### Une heure est incorrecte

Sélectionnez la date dans le tableau, choisissez l’employé dans **Sécurité et correction**, puis cliquez sur **Remettre à zéro**. L’employé pourra pointer à nouveau.

### L’adresse du serveur change

Relancez `installer_raccourci_employe.bat` sur les PC pour recréer le raccourci avec la nouvelle adresse. Pour éviter cela, réservez une adresse IP fixe au serveur dans le routeur.
