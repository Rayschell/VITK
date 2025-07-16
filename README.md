# Projet Suivi Longitudinal de Tumeur - ITK/VTK

## Description du Projet
Ce projet réalise le suivi des changements d'une tumeur à partir de deux scans effectués sur un même patient à des dates différentes (étude longitudinale). Il utilise les bibliothèques ITK (Insight Segmentation and Registration Toolkit) et VTK (Visualization Toolkit) pour effectuer le recalage des volumes, la segmentation des tumeurs et la visualisation des changements.

## 🎯 Objectifs
- **Recalage automatique** des deux volumes avec transformation rigide
- **Segmentation des tumeurs** avec méthodes de seuillage adaptatif
- **Analyse quantitative** des changements (volume, intensité)
- **Visualisation 3D** avec VTK et génération de rapports
- **Pipeline automatisé** exécutable sans interaction utilisateur

## 🏗️ Structure du Projet
```
VITK/
├── main.py                      # 🚀 Script principal (point d'entrée)
├── registration.py              # 🔗 Module de recalage d'images
├── vtk_visualizer.py           # 📊 Module de visualisation VTK
├── auto_run.py                 # 🤖 Script d'exécution automatisée
├── requirements.txt            # 📦 Dépendances Python
├── README.md                   # 📚 Documentation
├── git_commit_custom.sh        # 🔧 Script de commit personnalisé
├── Data/                       # 📁 Images d'entrée
│   ├── case6_gre1.nrrd        #    Premier scan
│   └── case6_gre2.nrrd        #    Second scan (suivi)
└── Output/                     # 📁 Résultats générés
    ├── *.png                   #    Images filtrées et segmentées
    ├── *_registered.nrrd       #    Volume recalé
    ├── *_vtk_screenshot.png    #    Captures VTK
    └── tumor_changes_report.txt #   📋 Rapport des changements
```

## 🔧 Installation et Configuration
```bash
# Cloner le projet
git clone <URL_DU_DEPOT>
cd VITK

# Placer les fichiers de données
# Copier case6_gre1.nrrd et case6_gre2.nrrd dans Data/

# Le script installe automatiquement les dépendances
# Ou manuel:
pip install itk>=5.4.0 vtk>=9.3.0 numpy matplotlib scipy
```

## 🚀 Utilisation

### Mode Principal (Conforme aux Consignes)
```bash
python main.py
```

**Pipeline automatique exécuté:**
1. ✅ Vérification et installation automatique des dépendances
2. ✅ Chargement et analyse des images NRRD
3. ✅ **Recalage automatique** (transformation rigide, information mutuelle)
4. ✅ Filtrage des images (Gaussien, seuillage)
5. ✅ **Segmentation des tumeurs** (seuillage adaptatif)
6. ✅ **Analyse comparative** des changements tumoraux
7. ✅ Visualisation VTK avec captures d'écran automatiques

### Mode Entièrement Automatisé
```bash
python auto_run.py
```

### Visualisation Interactive (Optionnelle)
```bash
# Après exécution du pipeline principal
python -c "from main import launch_interactive_visualization, load_and_analyze_images; launch_interactive_visualization(load_and_analyze_images())"
```

## 🔬 Algorithmes et Méthodes Techniques

### Recalage d'Images
- **Type**: Transformation rigide (6 paramètres: 3 rotations + 3 translations)
- **Métrique**: Information mutuelle de Mattes (50 bins)
- **Optimiseur**: RegularStepGradientDescent (300 itérations)
- **Interpolation**: Linéaire
- **Sampling**: Aléatoire (20% des voxels)

### Segmentation
- **Méthode principale**: Seuillage binaire adaptatif
- **Seuils**: Moyenne + 1-2 écarts-types pour cibler les tissus tumoraux
- **Validation**: Seuillage Otsu pour comparaison

### Analyse des Changements
- **Volume tumoral**: Comptage des voxels segmentés × volume physique
- **Intensités**: Statistiques (moyenne, écart-type, médiane) dans les régions tumorales
- **Métriques**: Pourcentage de changement volumétrique et d'intensité

## 📊 Résultats et Interprétation

Le script génère automatiquement:
- **Images filtrées**: Visualisation des étapes de préprocessing
- **Segmentations**: Masques binaires des tumeurs détectées
- **Volume recalé**: Image du second scan alignée sur le premier
- **Rapport détaillé**: Analyse quantitative des changements

**Interprétation automatique:**
- **Augmentation significative**: +10% de volume tumoral
- **Diminution significative**: -10% de volume tumoral  
- **Stabilité relative**: Changement < ±10%

## 🎛️ Choix Techniques et Justifications

### Recalage Rigide
- **Avantage**: Rapide, robuste, préserve les formes anatomiques
- **Limitation**: Ne corrige pas les déformations non-rigides
- **Justification**: Approprié pour les scans de suivi à court terme

### Segmentation par Seuillage
- **Avantage**: Simple, reproductible, automatisable
- **Limitation**: Sensible aux variations d'intensité
- **Amélioration possible**: Segmentation par région croissante ou level-sets

### Visualisation VTK
- **Rendu volumique**: Visualisation 3D complète des données
- **Isosurfaces**: Surfaces tumorales extractibles
- **Captures automatiques**: Documentation reproductible

## ⚠️ Difficultés Rencontrées et Solutions

1. **Types d'images ITK**: Gestion des conversions float/int pour la compatibilité des filtres
2. **Paramètres de recalage**: Ajustement des échelles d'optimisation pour translations vs rotations
3. **Seuils de segmentation**: Adaptation automatique basée sur les statistiques d'image
4. **Mode non-interactif**: Suppression des inputs utilisateur pour conformité aux consignes

## 👥 Contributeurs

- **Antoine Lett** <antoine.lett@epita.fr>
- **Clement Fabien** <clement.fabien@epita.fr>  
- **Maxime Ellerbach** <maxime.ellerbach@epita.fr>

## 📅 Informations Projet

- **Date limite**: 18 juillet 2025
- **Durée**: 1 mois
- **Encadrement**: ITK/VTK Mini-Project
- **Conformité**: ✅ Exécution avec `python main.py` sans interaction utilisateur

---

*Ce projet démontre une application complète de traitement d'images médicales avec ITK/VTK, incluant recalage automatique, segmentation, analyse comparative et visualisation 3D pour le suivi longitudinal de tumeurs.*
