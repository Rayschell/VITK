#!/usr/bin/env python3
"""
Script de synthèse et rapport des résultats ITK/VTK
Génère un rapport détaillé des traitements effectués
"""

import os
import sys
import subprocess
from datetime import datetime

def generate_report():
    """Génère un rapport de synthèse"""
    
    print("Génération du rapport de synthèse ITK/VTK")
    print("=" * 50)
    
    # Informations générales
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Répertoire: {os.getcwd()}")
    
    # Vérification des fichiers d'entrée
    print("\nFichiers d'entrée:")
    data_files = [
        "Data/case6_gre1.nrrd",
        "Data/case6_gre2.nrrd"
    ]
    
    for file_path in data_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✓ {file_path} ({size:,} bytes)")
        else:
            print(f"  ✗ {file_path} - MANQUANT")
    
    # Vérification des fichiers de sortie
    print("\nFichiers de sortie générés:")
    output_dir = "Output"
    
    if os.path.exists(output_dir):
        output_files = sorted([f for f in os.listdir(output_dir) if f.endswith('.png')])
        
        if output_files:
            # Organiser par type de traitement
            original_files = [f for f in output_files if '_original' in f]
            gaussian_files = [f for f in output_files if '_gaussian' in f]
            threshold_files = [f for f in output_files if '_threshold' in f]
            binary_files = [f for f in output_files if '_binary_seg' in f]
            adaptive_files = [f for f in output_files if '_adaptive_seg' in f]
            
            print(f"  Images originales: {len(original_files)}")
            for f in original_files:
                size = os.path.getsize(os.path.join(output_dir, f))
                print(f"    - {f} ({size:,} bytes)")
            
            print(f"  Filtrage Gaussien: {len(gaussian_files)}")
            for f in gaussian_files:
                size = os.path.getsize(os.path.join(output_dir, f))
                print(f"    - {f} ({size:,} bytes)")
            
            print(f"  Seuillage simple: {len(threshold_files)}")
            for f in threshold_files:
                size = os.path.getsize(os.path.join(output_dir, f))
                print(f"    - {f} ({size:,} bytes)")
            
            print(f"  Segmentation binaire: {len(binary_files)}")
            for f in binary_files:
                size = os.path.getsize(os.path.join(output_dir, f))
                print(f"    - {f} ({size:,} bytes)")
            
            print(f"  Segmentation adaptative: {len(adaptive_files)}")
            for f in adaptive_files:
                size = os.path.getsize(os.path.join(output_dir, f))
                print(f"    - {f} ({size:,} bytes)")
            
            print(f"\nTotal: {len(output_files)} fichiers générés")
        else:
            print("  Aucun fichier de sortie trouvé")
    else:
        print("  Répertoire de sortie non trouvé")
    
    # Informations sur les dépendances
    print("\nDépendances installées:")
    try:
        result = subprocess.run([sys.executable, "-c", "import itk; print(f'ITK: {itk.Version.GetITKVersion()}')"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ {result.stdout.strip()}")
        else:
            print("  ✗ ITK non disponible")
    except:
        print("  ✗ ITK non disponible")
    
    try:
        result = subprocess.run([sys.executable, "-c", "import vtk; print(f'VTK: {vtk.vtkVersion.GetVTKVersion()}')"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ {result.stdout.strip()}")
        else:
            print("  ✗ VTK non disponible")
    except:
        print("  ✗ VTK non disponible")
    
    try:
        result = subprocess.run([sys.executable, "-c", "import numpy; print(f'NumPy: {numpy.__version__}')"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ {result.stdout.strip()}")
        else:
            print("  ✗ NumPy non disponible")
    except:
        print("  ✗ NumPy non disponible")
    
    # Historique Git
    print("\nHistorique des commits:")
    try:
        result = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
        else:
            print("  Impossible de récupérer l'historique Git")
    except:
        print("  Git non disponible")
    
    print("\n" + "=" * 50)
    print("Rapport de synthèse terminé")

def main():
    """Fonction principale"""
    generate_report()

if __name__ == "__main__":
    main()
