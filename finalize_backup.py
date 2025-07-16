#!/usr/bin/env python3
"""
Script automatisé pour le suivi longitudinal de tumeur
Mode non-interactif - s'exécute entièrement sans intervention utilisateur
"""

import os
import sys
import subprocess

# Import du module principal
from main import (
    check_python_environment, 
    verify_imports, 
    install_dependencies,
    load_and_analyze_images,
    apply_registration,
    apply_filters,
    apply_segmentation,
    apply_vtk_visualization,
    analyze_tumor_changes
)

def run_automated_analysis():
    """Exécute l'analyse complète en mode automatisé"""
    print("=== SUIVI LONGITUDINAL DE TUMEUR - MODE AUTOMATISE ===")
    print("Execution sans interaction utilisateur...")
    
    # Créer les dossiers nécessaires
    directories = ["Data", "Output"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Dossier cree: {directory}")
    
    # Vérifier les fichiers de données
    data_files = [
        "Data/case6_gre1.nrrd",
        "Data/case6_gre2.nrrd"
    ]
    
    print("\nVerification des fichiers de donnees:")
    missing_files = []
    for file_path in data_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✓ {file_path} ({size:,} bytes)")
        else:
            print(f"✗ {file_path} - MANQUANT")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\nERREUR: {len(missing_files)} fichier(s) manquant(s)")
        print("Veuillez placer les fichiers NRRD dans le dossier Data/")
        return False
    
    # Vérifier l'environnement Python
    if not check_python_environment():
        print("\nERREUR: Probleme avec l'environnement Python")
        return False
    
    # Vérifier les modules ou les installer automatiquement
    if not verify_imports():
        print("\nModules ITK/VTK manquants - Installation automatique...")
        if install_dependencies():
            print("✓ Dependances installees avec succes!")
            if not verify_imports():
                print("✗ Probleme persistant avec les imports")
                return False
        else:
            print("✗ Erreur lors de l'installation automatique")
            return False
    
    print("\n=== ETAPE 1: CHARGEMENT ET ANALYSE DES IMAGES ===")
    results = load_and_analyze_images()
    if not results:
        print("✗ Echec du chargement des images")
        return False
    print("✓ Images chargees et analysees")
    
    print("\n=== ETAPE 2: RECALAGE AUTOMATIQUE ===")
    registered_results = apply_registration(results)
    print("✓ Recalage termine")
    
    print("\n=== ETAPE 3: FILTRAGE DES IMAGES ===")
    filters = apply_filters(registered_results)
    if not filters:
        print("✗ Echec du filtrage")
        return False
    print("✓ Filtrage termine")
    
    print("\n=== ETAPE 4: SEGMENTATION DES TUMEURS ===")
    segmentations = apply_segmentation(registered_results)
    if not segmentations:
        print("✗ Echec de la segmentation")
        return False
    print("✓ Segmentation terminee")
    
    print("\n=== ETAPE 5: ANALYSE DES CHANGEMENTS TUMORAUX ===")
    changes_report = analyze_tumor_changes(registered_results, segmentations)
    if not changes_report:
        print("✗ Echec de l'analyse des changements")
        return False
    print("✓ Analyse des changements terminee")
    
    print("\n=== ETAPE 6: VISUALISATION VTK ===")
    vtk_results = apply_vtk_visualization(registered_results)
    if not vtk_results:
        print("✗ Echec de la visualisation VTK")
        return False
    print("✓ Visualisation VTK terminee")
    
    # Résumé final
    print("\n=== RESUME DE L'ANALYSE ===")
    
    if changes_report:
        scan1_name = changes_report['scan1']['name']
        scan2_name = changes_report['scan2']['name']
        volume_change = changes_report['changes']['volume_change_percent']
        
        print(f"Images analysees: {scan1_name} -> {scan2_name}")
        print(f"Recalage applique: {'Oui' if changes_report['scan2']['registered'] else 'Non'}")
        print(f"Changement de volume: {volume_change:+.1f}%")
        
        if volume_change > 10:
            status = "AUGMENTATION SIGNIFICATIVE"
        elif volume_change < -10:
            status = "DIMINUTION SIGNIFICATIVE"
        else:
            status = "STABILITE RELATIVE"
        
        print(f"Interpretation: {status}")
    
    # Lister les fichiers générés
    print(f"\nFichiers generes dans Output/:")
    output_files = []
    if os.path.exists("Output"):
        for filename in sorted(os.listdir("Output")):
            if filename.endswith(('.png', '.nrrd', '.txt')):
                filepath = os.path.join("Output", filename)
                size = os.path.getsize(filepath)
                print(f"  {filename} ({size:,} bytes)")
                output_files.append(filename)
    
    print(f"\n✓ ANALYSE COMPLETE - {len(output_files)} fichier(s) genere(s)")
    print("✓ Pipeline execute avec succes en mode automatise")
    
    return True

def main():
    """Point d'entrée principal du script automatisé"""
    try:
        success = run_automated_analysis()
        if success:
            print("\n🎉 SUCCES: Analyse longitudinale terminee avec succes!")
            print("📊 Consultez le rapport: Output/tumor_changes_report.txt")
            print("🖼️  Images generees dans: Output/")
            sys.exit(0)
        else:
            print("\n❌ ECHEC: L'analyse n'a pas pu etre completee")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Analyse interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

def display_summary():
    """Affiche un résumé final du projet"""
    
    print("\nRÉSUMÉ FINAL DU PROJET")
    print("=" * 40)
    print("Fonctionnalités implémentées:")
    print("  ✓ Chargement d'images NRRD")
    print("  ✓ Analyse statistique des images")
    print("  ✓ Filtrage Gaussien")
    print("  ✓ Seuillage binaire")
    print("  ✓ Segmentation adaptative")
    print("  ✓ Conversion et sauvegarde PNG")
    print("  ✓ Rapport automatique")
    print("  ✓ Système de commit Git personnalisé")
    
    print("\nUtilisation:")
    print("  python main.py        # Traitement principal")
    print("  python rapport.py     # Génération de rapport")
    print("  ./git_commit_custom.sh # Commit avec identité")
    
    print("\nContributeurs:")
    print("  - Antoine Lett <antoine.lett@epita.fr>")
    print("  - Clement Fabien <clement.fabien@epita.fr>")
    print("  - Maxime Ellerbach <maxime.ellerbach@epita.fr>")

def main():
    """Fonction principale"""
    
    success = cleanup_project()
    
    if success:
        display_summary()
        print(f"\n{'='*40}")
        print("PROJET ITK/VTK TERMINÉ AVEC SUCCÈS!")
        print(f"{'='*40}")
        return True
    else:
        print("Erreur lors de la finalisation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
