# SARL AYRIS — Gestionnaire de Parc

Application de bureau Python destinée à la gestion du parc d'engins, des pièces de rechange, des bons de livraison, des sorties et des prix.

## Installation rapide

1. Créer un environnement virtuel
2. Installer les dépendances :
   `pip install -r requirements.txt`
3. Lancer l’application :
   `python main.py`

## Structure du projet

- `database/db_manager.py` : gestion SQLite, schéma et CRUD
- `auth/auth_manager.py` : authentification et rôles
- `ui/` : écrans CustomTkinter
- `services/` : config JSON, PDF, export Excel
- `assets/` : logo AYRIS

## Emplacement de la base de données

La base SQLite est créée automatiquement dans :
`C:\Users\<Utilisateur>\AppData\Local\SARL_Ayris_Parc\ayris_parc.db`

## Fonctionnalités principales

- Authentification admin/opérateur
- Gestion des engins
- Gestion des pièces et familles
- Comparateur ancien/nouveau prix
- Bons de livraison et bons de sortie
- Dashboard analytique avec KPI et graphiques
- Configuration PDF / imprimante / sauvegarde

## Compilation

Exécuter :
`python build.py`

La sortie PyInstaller est produite dans le dossier `dist/`.

## Dépendances

- customtkinter
- reportlab
- matplotlib
- openpyxl
- Pillow
- pyinstaller

## Schéma base de données

Tables principales :
- `utilisateurs`
- `engins`
- `familles_pieces`
- `pieces`
- `bons_livraison`
- `bons_sortie`

## Données de démonstration

Au premier lancement, l’application crée un compte admin par défaut :
- utilisateur : `admin`
- mot de passe : `admin`

Des engins, familles et quelques pièces de démonstration sont également ajoutés si la base est vide.
