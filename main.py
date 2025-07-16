"""
ITK/VTK Mini-Project - Étape 1
Script principal pour le traitement d'images médicales
"""

import os
import sys
import subprocess

def check_python_environment():
    """Vérifier l'environnement Python"""
    print("\nVérification de l'environnement Python:")
    print(f"✓ Python {sys.version}")
    
    # Vérifier si pip est disponible
    try:
        subprocess.run(["pip", "--version"], capture_output=True, check=True)
        print("✓ pip disponible")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ pip non disponible")
        return False

def install_dependencies():
    """Installer les dépendances ITK/VTK"""
    print("\nInstallation des dépendances:")
    
    dependencies = [
        "itk>=5.4.0",
        "vtk>=9.3.0", 
        "numpy>=1.21.0",
        "matplotlib>=3.5.0",
        "scipy>=1.7.0"
    ]
    
    for dep in dependencies:
        print(f"Installation de {dep}...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], check=True, capture_output=True)
            print(f"✓ {dep} installé avec succès")
        except subprocess.CalledProcessError as e:
            print(f"✗ Erreur lors de l'installation de {dep}")
            print(f"  Erreur: {e}")
            return False
    
    return True

def verify_imports():
    """Vérifier que les modules peuvent être importés"""
    print("\nVérification des imports:")
    
    modules = [
        ("itk", "Insight Toolkit"),
        ("vtk", "Visualization Toolkit"),
        ("numpy", "NumPy"),
        ("matplotlib", "Matplotlib")
    ]
    
    all_success = True
    
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✓ {description} ({module_name}) - OK")
        except ImportError as e:
            print(f"✗ {description} ({module_name}) - ERREUR: {e}")
            all_success = False
    
    return all_success

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
    
    # Vérifier l'environnement Python
    if not check_python_environment():
        print("❌ Problème avec l'environnement Python")
        return False
    
    # Demander si installer les dépendances
    print("\n" + "=" * 40)
    response = input("Voulez-vous installer les dépendances ITK/VTK ? (o/n): ").lower()
    
    if response == 'o' or response == 'oui':
        if install_dependencies():
            print("✅ Toutes les dépendances installées avec succès!")
        else:
            print("❌ Erreur lors de l'installation des dépendances")
            return False
    
    # Vérifier les imports
    if verify_imports():
        print("\n✅ Tous les modules sont disponibles!")
    else:
        print("\n❌ Certains modules ne sont pas disponibles")
        print("Essayez d'installer les dépendances manuellement:")
        print("pip install -r requirements.txt")
    
    print("\n" + "=" * 60)
    print("Configuration initiale terminée!")
    print("Prochaine étape: Chargement et analyse des images NRRD")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
