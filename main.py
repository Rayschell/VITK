"""
ITK/VTK Mini-Project - Étape 1
Script principal pour le traitement d'images médicales
"""

import os
import sys

def main():
    """Fonction principale"""
    print("=" * 60)
    print("ITK/VTK Mini-Project - Traitement d'Images Médicales")
    print("=" * 60)
    
    # Vérifier la structure des dossiers
    directories = ["Data", "Output"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Dossier créé: {directory}")
        else:
            print(f"✓ Dossier existant: {directory}")
    
    # Vérifier les fichiers de données
    data_files = [
        "Data/case6_gre1.nrrd",
        "Data/case6_gre2.nrrd"
    ]
    
    print("\nVérification des fichiers de données:")
    for file_path in data_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✓ {file_path} ({size:,} bytes)")
        else:
            print(f"✗ {file_path} - MANQUANT")
    
    print("\n" + "=" * 60)
    print("Configuration initiale terminée!")
    print("Prochaine étape: Installation des dépendances")
    print("=" * 60)

if __name__ == "__main__":
    main()
