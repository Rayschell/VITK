#!/usr/bin/env python3
"""
Script pour lancer la visualisation 3D interactive des tumeurs
"""

from pathlib import Path
import sys
import json

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from visualization import TumorVisualization


def main():
    # Setup paths
    project_root = Path(__file__).parent
    results_dir = project_root / "results"
    
    # Input files (results from the pipeline)
    brain_image = project_root / "Data" / "case6_gre1.nrrd"
    tumor1_mask = results_dir / "tumor_mask_scan1.nrrd"
    tumor2_mask = results_dir / "tumor_mask_scan2.nrrd"
    analysis_file = results_dir / "tumor_analysis.json"
    
    # Check if all files exist
    missing_files = []
    for file_path in [brain_image, tumor1_mask, tumor2_mask, analysis_file]:
        if not file_path.exists():
            missing_files.append(str(file_path))
    
    if missing_files:
        print("ERREUR: Fichiers manquants. Executez d'abord le pipeline principal :")
        print("   python main.py")
        print(f"\nFichiers manquants :")
        for file in missing_files:
            print(f"   - {file}")
        return
    
    # Load analysis results
    with open(analysis_file, 'r') as f:
        analysis_results = json.load(f)
    
    print("Lancement de la visualisation 3D interactive amelioree...")
    print("\nResultats de l'analyse :")
    volume1 = analysis_results['tumor1']['volume_mm3']
    volume2 = analysis_results['tumor2']['volume_mm3']
    volume_change = analysis_results['comparison']['volume_change_percent']
    dice_score = analysis_results['comparison']['dice_coefficient']
    
    print(f"   - Volume initial: {volume1:.0f} mm3")
    print(f"   - Volume suivi: {volume2:.0f} mm3")
    print(f"   - Changement: {volume_change:+.1f}%")
    print(f"   - Dice coefficient: {dice_score:.3f}")
    
    print("\nAmeliorations de la visualisation :")
    print("   - Cerveau ultra-transparent pour voir les tumeurs")
    print("   - Tumeurs avec eclairage ameliore et contours")
    print("   - Controles clavier pour ajuster la transparence")
    print("   - Fenetre plus grande (1000x800) pour plus de details")
    
    print("\nControles de la visualisation :")
    print("   - Clic gauche + glisser : Rotation")
    print("   - Molette : Zoom")
    print("   - Clic droit + glisser : Translation")
    print("   - Touches + et - : Ajuster transparence cerveau")
    print("   - Touche r : Reinitialiser la vue")
    print("   - Touche h : Aide")
    print("   - Fermer la fenetre pour quitter")
    
    print("\nLegende des couleurs :")
    print("   - Rouge brillant : Tumeur scan initial")
    print("   - Vert brillant : Tumeur scan de suivi")
    print("   - Gris tres transparent : Cerveau")
    
    # Create and start visualization
    try:
        visualizer = TumorVisualization()
        
        # Setup the 3D scene
        visualizer.visualize_tumor_evolution(
            brain_image, tumor1_mask, tumor2_mask, analysis_results
        )
        
        print("\nFenetre de visualisation ouverte !")
        print("   (La fenetre peut mettre quelques secondes a apparaitre)")
        
        # Start interactive session
        visualizer.start_interaction()
        
        print("\nVisualisation fermee.")
        
    except Exception as e:
        print(f"\nERREUR lors de la visualisation : {e}")
        print("\nVerifiez que :")
        print("   - VTK est installe correctement")
        print("   - Vous avez un affichage graphique disponible")
        print("   - Les fichiers de resultats sont valides")


if __name__ == "__main__":
    main()
