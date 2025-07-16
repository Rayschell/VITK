# ITK/VTK Mini-Project - Traitement d'Images Médicales

## Description du Projet
Ce projet démontre les capacités de traitement d'images médicales en utilisant l'Insight Toolkit (ITK) et le Visualization Toolkit (VTK).

## Objectifs
- Charger et analyser des images NRRD
- Appliquer différents filtres de traitement
- Effectuer la segmentation d'images
- Visualiser les résultats en 3D

## Structure du Projet
```
VITK/
├── main.py                 # Script principal
├── requirements.txt        # Dépendances Python
├── README.md              # Ce fichier
├── Data/                  # Images d'entrée
│   ├── case6_gre1.nrrd   
│   └── case6_gre2.nrrd   
└── Output/               # Images de sortie
```

## Installation
```bash
# Créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation
```bash
python main.py
```
