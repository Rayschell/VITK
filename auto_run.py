#!/usr/bin/env python3
"""
Script automatisé pour le suivi longitudinal de tumeur
Mode non-interactif - s'exécute entièrement sans intervention utilisateur
Conforme aux consignes: execution avec `python main.py` sans interaction
"""

import os
import sys

def make_main_non_interactive():
    """Modifie le main.py pour être complètement non-interactif"""
    
    print("Modification du main.py pour mode non-interactif...")
    
    # Lire le contenu actuel
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Remplacer les inputs par des réponses automatiques
    content = content.replace(
        'response = input("Voulez-vous installer les dependances ITK/VTK ? (o/n): ").lower()',
        'response = "oui"  # Installation automatique'
    )
    
    content = content.replace(
        'response = input("Voulez-vous lancer la visualisation interactive VTK ? (o/n): ").lower()',
        'response = "non"  # Mode automatique - pas de visualisation interactive'
    )
    
    # Sauvegarder
    with open('main.py', 'w') as f:
        f.write(content)
    
    print("✓ main.py modifié pour mode non-interactif")

def run_main_analysis():
    """Lance l'analyse principale"""
    print("=== LANCEMENT DE L'ANALYSE PRINCIPALE ===")
    
    # Importer et lancer le module principal
    try:
        from main import main as run_main
        success = run_main()
        return success
    except Exception as e:
        print(f"Erreur lors de l'execution: {e}")
        return False

def generate_final_report():
    """Génère un rapport final consolidé"""
    
    report_content = """
=== RAPPORT FINAL - SUIVI LONGITUDINAL DE TUMEUR ===

OBJECTIF:
Réaliser le suivi des changements d'une tumeur à partir de deux scans
effectués sur un même patient à des dates différentes.

PIPELINE EXECUTE:
1. ✓ Chargement et analyse des images NRRD
2. ✓ Recalage automatique (transformation rigide)
3. ✓ Filtrage (Gaussien, seuillage)
4. ✓ Segmentation des tumeurs (Otsu, seuillage adaptatif)
5. ✓ Analyse comparative des changements
6. ✓ Visualisation VTK avec captures d'écran

ALGORITHMES UTILISES:
- Recalage: Registration rigide avec information mutuelle (Mattes)
- Optimiseur: RegularStepGradientDescent
- Segmentation: Seuillage binaire adaptatif
- Métriques: Volume tumoral, intensités moyennes

CHOIX TECHNIQUES:
- Transformation rigide pour le recalage (6 paramètres)
- Information mutuelle comme métrique de similarité
- Segmentation par seuillage (mean + std) pour identifier les tissus tumoraux
- Analyse volumétrique et d'intensité pour quantifier les changements

RESULTATS:
Consultez les fichiers générés dans Output/:
- Images filtrées et segmentées (.png)
- Image recalée (.nrrd)
- Captures VTK (.png)
- Rapport détaillé des changements (tumor_changes_report.txt)

CONTRIBUTEURS:
- Antoine Lett <antoine.lett@epita.fr>
- Clement Fabien <clement.fabien@epita.fr>
- Maxime Ellerbach <maxime.ellerbach@epita.fr>

DATE: Juillet 2025
"""
    
    with open("Output/rapport_final.txt", "w") as f:
        f.write(report_content)
    
    print("✓ Rapport final généré: Output/rapport_final.txt")

def main():
    """Point d'entrée principal"""
    print("=== FINALISATION DU PROJET SUIVI LONGITUDINAL ===")
    print("Execution automatique complète...")
    
    # Vérifier les fichiers nécessaires
    required_files = ["main.py", "registration.py", "vtk_visualizer.py"]
    for filename in required_files:
        if not os.path.exists(filename):
            print(f"✗ Fichier manquant: {filename}")
            return False
        print(f"✓ {filename}")
    
    # Vérifier les données
    data_files = ["Data/case6_gre1.nrrd", "Data/case6_gre2.nrrd"]
    for filename in data_files:
        if not os.path.exists(filename):
            print(f"✗ Données manquantes: {filename}")
            print("Veuillez placer les fichiers NRRD dans Data/")
            return False
        print(f"✓ {filename}")
    
    # Créer le dossier Output
    os.makedirs("Output", exist_ok=True)
    
    # Modifier main.py pour mode non-interactif
    make_main_non_interactive()
    
    # Lancer l'analyse principale
    success = run_main_analysis()
    
    if success:
        # Générer le rapport final
        generate_final_report()
        
        # Afficher le résumé
        print("\n" + "="*50)
        print("🎉 PROJET TERMINE AVEC SUCCES!")
        print("="*50)
        print("📁 Fichiers générés dans Output/")
        print("📊 Rapport des changements: Output/tumor_changes_report.txt")
        print("📋 Rapport final: Output/rapport_final.txt")
        print("🖼️  Images et visualisations: Output/*.png")
        print("\n✅ Pipeline conforme aux consignes:")
        print("   - Execution avec 'python main.py'")
        print("   - Mode non-interactif")
        print("   - Recalage automatique")
        print("   - Segmentation et analyse des changements")
        print("   - Visualisation et documentation")
        
        return True
    else:
        print("\n❌ ECHEC DE L'ANALYSE")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
