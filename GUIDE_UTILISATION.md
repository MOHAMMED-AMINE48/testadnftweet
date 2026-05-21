# Guide d'utilisation - Plateforme CMF React

Ce guide explique comment utiliser la plateforme CMF modernisée en React avec son API FastAPI et sa base SQLite isolée dans `react-worked-files`.

## 1. Acces a la plateforme

### URLs principales

- Interface React : `http://localhost:5175/`
- API FastAPI : `http://localhost:8001/api`
- Base de donnees SQLite : `react-worked-files/cmf_app/data/cmf.db`

### Connexion

Au lancement, l'utilisateur arrive sur l'ecran de connexion.

Champs disponibles :

- Email
- Password

Compte administrateur par defaut :

- Email : `admin@cmf.local`
- Mot de passe : `admin123`

Apres connexion, le role de l'utilisateur determine automatiquement les onglets visibles dans le menu lateral.

## 2. Regles globales d'acces

La plateforme est multi-utilisateurs.

Tous les utilisateurs peuvent :

- visualiser tous les projets ;
- visualiser tous les records CMF ;
- utiliser `View All Data` ;
- consulter la roadmap vehicules.

Les utilisateurs ne peuvent modifier que les projets ou ils sont affectes.

Regle d'edition :

- Buyer : peut modifier uniquement les projets ou il est affecte comme Buyer.
- SQD : peut modifier uniquement les projets ou il est affecte comme SQD.
- Capacity Manager : peut modifier uniquement les projets ou il est affecte comme Capacity Manager.
- Admin : peut tout voir et tout modifier.

Si l'utilisateur n'est pas affecte au projet selectionne, les formulaires passent en lecture seule et les boutons de sauvegarde/import sont bloques.

## 3. Navigation generale

Le menu lateral reste fixe pendant le scroll.

La barre superieure affiche :

- le projet courant ;
- l'utilisateur connecte et son role ;
- le selecteur de projet ;
- l'etat de l'API ;
- le bouton Logout ;
- l'avatar utilisateur.

Pour changer de projet, utiliser le selecteur dans la barre superieure.

## 4. Roles et onglets disponibles

### Buyer

Onglets :

- Command Center
- View All Data
- Part Data
- Weekly Contracted Capacity
- VEHICULES ROAD MAP

### Capacity Manager

Onglets :

- Command Center
- View All Data
- Manage Projects
- Create Project
- CAPACITY SIZING
- CAPACITY WORKSHOP (STEP 2)
- VEHICULES ROAD MAP

### SQD

Onglets :

- Command Center
- View All Data
- PART DATA
- SUPPLIER INFORMATION
- CAPACITY WORKSHOP (STEP 2)
- CAT
- VEHICULES ROAD MAP

### Admin

Onglets :

- Command Center
- View All Data
- Manage Projects
- Create Project
- Buyer Page
- Capacity Page
- SQD Page
- VEHICULES ROAD MAP
- Admin Users
- Data Manager

## 5. Command Center

Le `Command Center` donne une vue synthetique du projet selectionne.

KPI affiches :

- Number of Parts : nombre total de part numbers.
- Number of Red Parts : nombre de parts en risque rouge.
- Number of Orange Parts : nombre de parts en risque orange.
- Number of Green Parts : nombre de parts en vert.

La couleur d'une part est calculee avec la hierarchie CAT/GOR :

- Si CAT ou GOR est `R`, la part est rouge.
- Sinon si CAT ou GOR est `O`, la part est orange.
- Sinon, si CAT et GOR sont `G`, la part est verte.

Section `Workstream Readiness` :

- Part number : pourcentage de part numbers existants.
- Requested Capacity : pourcentage de records avec capacite demandee remplie.
- Contracted : pourcentage de records avec capacite contractee remplie.
- Mesured : pourcentage de records avec capacite mesuree remplie.

Section `Priority Records` :

- tableau type Excel ;
- filtres par colonne ;
- clic sur cellule pour copier la valeur ;
- lecture rapide des colonnes principales.

## 6. View All Data

Cet onglet affiche le CMF complet du projet selectionne.

Vue initiale :

- N° SOURCING, RFQ, ODM, FETE ...
- APQP GRID
- USE CASES
- PART NUMBER
- WEEKLY CAPACITY CONTRACTED (Parts/Week)
- GOR
- CAT1/2/3 VALUATION

Les autres colonnes existent mais sont masquees par defaut.

Fonctions disponibles :

- filtre global sur toutes les colonnes ;
- filtres individuels par colonne, comme Excel ;
- selection des colonnes visibles via les cases a cocher ;
- `Reset columns` pour revenir a la vue initiale ;
- clic sur une cellule pour copier sa valeur ;
- coloration automatique des cellules G/O/R :
  - `G` en vert ;
  - `O` en orange ;
  - `R` en rouge ;
- `Export CMF` pour exporter le CMF au format Excel.

## 7. Select Part Number

Dans tous les formulaires ou un part number doit etre choisi, le champ `Select Part Number` fonctionne comme une recherche intelligente.

Utilisation :

1. Cliquer dans le champ.
2. Taper le debut du PN, par exemple `9` ou `95`.
3. Choisir une suggestion dans la liste.

Le champ remplace l'ancien fonctionnement avec deux barres separees.

## 8. Buyer - Part Data

Objectif : remplir ou completer les donnees Buyer liees aux parts.

Fonctions :

- creation d'un nouveau part number si la section l'autorise ;
- completion d'un part existant ;
- import de fichier Excel/CSV/TSV/TXT ;
- mapping des colonnes avant import ;
- saisie manuelle via formulaire.

Regle d'acces :

- le Buyer doit etre affecte au projet pour sauvegarder ;
- sinon la page reste en lecture seule.

## 9. Buyer - Weekly Contracted Capacity

Objectif : renseigner les informations de capacite contractee.

Flux :

1. Selectionner le projet.
2. Aller dans `Weekly Contracted Capacity`.
3. Choisir un part number existant.
4. Remplir les champs affiches.
5. Cliquer sur `Save record`.

Import :

- cliquer sur `Import file` ;
- choisir un fichier Excel, CSV, TSV ou TXT ;
- mapper les colonnes CMF avec les colonnes du fichier ;
- cliquer sur `Import mapped rows`.

## 10. Capacity Manager - Create Project

Objectif : creer un nouveau CMF.

Champs principaux :

- Projet
- Part of Project
- Capacity Manager
- Buyer
- SQD
- Status

Regle d'unicite :

- Un meme couple `Projet / Part of Project` ne peut pas etre cree deux fois.
- Un projet peut avoir plusieurs `Part of Project`.

Colonnes personnalisees :

1. Cliquer sur `Add customized column`.
2. Saisir le nom de la colonne.
3. Choisir le role proprietaire :
   - BUYER
   - SQD
   - CAPACITY_MANAGER
   - ADMIN
4. Creer le projet.

Import d'un CMF deja rempli :

1. Dans `Import completed CMF`, cliquer sur `Browse`.
2. Importer un fichier Excel/CSV/TSV/TXT.
3. Mapper chaque colonne CMF avec la colonne du fichier.
4. Cliquer sur `Create project`.

Le systeme cree le projet puis importe les records du fichier.

## 11. Capacity Manager - Manage Projects

Objectif : modifier les affectations et parametres d'un projet.

Actions possibles :

- changer `Part of Project` ;
- affecter ou changer le Capacity Manager ;
- affecter ou changer le Buyer ;
- affecter ou changer le SQD ;
- definir le fournisseur ;
- changer le statut :
  - ACTIVE
  - PAUSED
  - ARCHIVED
- ajouter des colonnes personnalisees au projet.

Important :

- seul le Capacity Manager affecte, ou l'Admin, peut modifier le projet ;
- les autres utilisateurs voient les informations en lecture seule.

## 12. Capacity Manager - Capacity Sizing

Objectif : renseigner les donnees de sizing capacitaire.

Flux :

1. Selectionner le projet.
2. Aller dans `CAPACITY SIZING`.
3. Selectionner un part number existant.
4. Completer les champs affiches.
5. Sauvegarder.

La page utilise les colonnes autorisees pour le role `CAPACITY_MANAGER` et la section `CAPACITY SIZING`.

## 13. Capacity Workshop (STEP 2)

Cet onglet existe pour Capacity Manager et SQD.

Pour Capacity Manager :

- edition des colonnes capacity-owned de l'etape workshop ;
- selection obligatoire d'un part number existant.

Pour SQD :

- edition des colonnes SQD-owned de l'etape workshop ;
- selection obligatoire d'un part number existant.

La logique d'acces reste basee sur l'affectation au projet.

## 14. SQD - PART DATA

Objectif : permettre au SQD de completer les donnees part.

Deux modes sont disponibles :

- `Complete existing Part Number` : completer une part deja creee par le Buyer.
- `Create new SQD Part` : creer une nouvelle part lorsque c'est autorise.

Le SQD peut aussi importer un fichier avec mapping des colonnes.

## 15. SQD - SUPPLIER INFORMATION

Objectif : renseigner les informations fournisseur.

Flux :

1. Selectionner le projet.
2. Aller dans `SUPPLIER INFORMATION`.
3. Selectionner un part number existant.
4. Remplir les champs fournisseur.
5. Sauvegarder.

## 16. SQD - CAT

L'onglet CAT est divise en deux sections.

### Section A: CAT Planning - Forecast Dates

Champs :

- Select Part Number
- CAT1 FORECASTED DATE (YYCWxx)
- CAT3 FORECASTED DATE (YYCWxx)
- CAT2 FORECASTED DATE (YYCWxx)

Utilisation :

1. Choisir le part number.
2. Remplir les dates forecast.
3. Cliquer sur `Save Section A`.

### Section B: CAT Results & Measurements

Champs :

- Select Part Number
- CAT Number
- CAT REALISED DATE (YYCWxx)
- CAT1/2/3 TYPE
- WEEKLY CAPACITY ESTIMATED
- Comments
- WEEKLY CAPACITY MEASURED
- SHARED FOLDER - link

Regle importante :

Le champ `CAT Number` determine la colonne standard mise a jour.

Exemples :

- CAT Number = 1 + CAT REALISED DATE = 26CW10 -> la colonne `CAT1 REALISED DATE (YYCWxx)` est mise a jour.
- CAT Number = 2 + CAT REALISED DATE = 26CW10 -> la colonne `CAT2 REALISED DATE (YYCWxx)` est mise a jour.
- CAT Number = 3 + CAT REALISED DATE = 26CW10 -> la colonne `CAT3 REALISED DATE (YYCWxx)` est mise a jour.

## 17. VEHICULES ROAD MAP

Objectif : voir si un part number existe dans un seul projet ou dans plusieurs projets.

Colonnes principales :

- APQP
- Part Name
- Part Number
- CarryOver - Adapted
- une colonne par projet existant

Regle :

- si le part number existe dans un seul projet, la valeur est `Adapted` ;
- si le part number existe dans plusieurs projets, la valeur est `CarryOver`.

Des KPI indiquent :

- nombre de part numbers ;
- nombre de parts Adapted ;
- nombre de parts CarryOver ;
- nombre de projets.

## 18. Admin Users

Onglet reserve a l'Admin.

Actions possibles :

- ajouter un utilisateur ;
- definir son email ;
- definir son nom complet ;
- choisir son role ;
- definir son mot de passe ;
- modifier le role d'un utilisateur existant ;
- modifier le mot de passe ;
- supprimer un utilisateur.

Roles disponibles :

- BUYER
- CAPACITY_MANAGER
- SQD
- ADMIN

Regle mot de passe :

- minimum 6 caracteres.

## 19. Data Manager

Onglet reserve a l'Admin.

Le Data Manager donne un acces direct a la base de donnees pour le projet selectionne.

Actions projet :

- `Reset CMF records` : supprime tous les records du CMF selectionne.
- `Delete Project` : supprime le projet CMF.

Direct Database Editor :

- selectionner un record existant ;
- modifier le part number ;
- modifier APQP GRID ;
- renseigner une colonne CMF quelconque ;
- renseigner la valeur ;
- `Add / Upsert` pour creer ou mettre a jour ;
- `Modify selected` pour modifier le record selectionne ;
- `Delete selected` pour supprimer le record selectionne.

Audit Logs :

- affiche les dernieres actions admin ;
- inclut utilisateur, action, entite, projet et nouvelle valeur.

## 20. Import et mapping des colonnes

Les imports acceptent :

- Excel `.xlsx`
- Excel macro `.xlsm`
- CSV `.csv`
- TSV `.tsv`
- TXT `.txt`

Principe du mapping :

- les colonnes CMF restent fixes ;
- l'utilisateur choisit, pour chaque colonne CMF, la colonne correspondante du fichier importe ;
- une colonne peut etre ignoree avec `Skip`.

Pour importer correctement :

1. Importer le fichier.
2. Verifier le mapping automatique propose.
3. Corriger les correspondances si necessaire.
4. Lancer l'import.

## 21. Export CMF

Dans `View All Data`, le bouton `Export CMF` genere un fichier Excel.

L'export utilise la structure CMF standard et reprend les donnees du projet selectionne.

## 22. Messages et erreurs courants

### Read-only: you are not assigned to this project

Cause :

- l'utilisateur essaie de modifier un projet auquel il n'est pas affecte.

Solution :

- demander a l'Admin ou au Capacity Manager d'affecter l'utilisateur au projet dans `Manage Projects`.

### Part Number not found

Cause :

- la section impose de choisir un part number existant.

Solution :

- verifier que le PN existe dans le projet selectionne ;
- utiliser la recherche PN ;
- creer le PN dans une section qui autorise la creation.

### This Projet / Part of Project combination already exists

Cause :

- tentative de creation d'un couple Projet / Part of Project deja existant.

Solution :

- changer le nom du projet ou le Part of Project ;
- utiliser `Manage Projects` si le CMF existe deja.

### Unsupported file type

Cause :

- le fichier importe n'est pas dans un format supporte.

Solution :

- utiliser `.xlsx`, `.xlsm`, `.csv`, `.tsv` ou `.txt`.

## 23. Bonnes pratiques

- Toujours selectionner le bon projet dans la barre superieure avant de saisir ou importer.
- Verifier les affectations Buyer/SQD/Capacity Manager lors de la creation du projet.
- Utiliser `View All Data` pour verifier les valeurs apres import.
- Utiliser les filtres de colonnes pour retrouver rapidement un PN ou une valeur.
- Avant un import massif, verifier que la colonne `PART NUMBER` est correctement mappee.
- Pour les donnees critiques, privilegier l'import via mapping plutot qu'un copier-coller manuel.
- L'Admin doit utiliser `Data Manager` avec prudence, car les suppressions agissent directement sur la base.

