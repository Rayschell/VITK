import os
import sys
import subprocess

def check_python_environment():
    try:
        subprocess.run(["pip", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("pip non disponible")
        return False

def install_dependencies():
    print("Installation des dependances...")
    dependencies = [
        "itk>=5.4.0",
        "vtk>=9.3.0", 
        "numpy>=1.21.0",
        "matplotlib>=3.5.0",
        "scipy>=1.7.0"
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print(f"Erreur installation {dep}")
            return False
    
    return True

def verify_imports():
    modules = [
        ("itk", "ITK"),
        ("vtk", "VTK"),
        ("numpy", "NumPy"),
        ("matplotlib", "Matplotlib")
    ]
    
    all_success = True
    
    for module_name, description in modules:
        try:
            __import__(module_name)
        except ImportError:
            print(f"{description} non disponible")
            all_success = False
    
    return all_success

def load_and_analyze_images():
    print("Chargement et analyse des images NRRD")
    
    try:
        import itk
        import numpy as np
        
        image_files = [
            "Data/case6_gre1.nrrd",
            "Data/case6_gre2.nrrd"
        ]
        
        results = {}
        
        for i, filepath in enumerate(image_files, 1):
            if not os.path.exists(filepath):
                print(f"Fichier non trouve: {filepath}")
                continue
                
            print(f"Analyse image {i}: {os.path.basename(filepath)}")
            
            try:
                image = itk.imread(filepath)
                
                size = image.GetLargestPossibleRegion().GetSize()
                spacing = image.GetSpacing()
                origin = image.GetOrigin()
                
                print(f"Dimensions: {size}")
                print(f"Espacement: {spacing}")
                
                stats_filter = itk.StatisticsImageFilter.New(image)
                stats_filter.Update()
                
                min_val = stats_filter.GetMinimum()
                max_val = stats_filter.GetMaximum()
                mean_val = stats_filter.GetMean()
                variance = stats_filter.GetVariance()
                std_dev = np.sqrt(variance)
                
                print(f"Intensites: min={min_val:.2f}, max={max_val:.2f}, moy={mean_val:.2f}")
                
                voxel_volume = spacing[0] * spacing[1] * spacing[2]
                total_voxels = size[0] * size[1] * size[2]
                physical_volume = voxel_volume * total_voxels
                
                print(f"Volume: {physical_volume/1000:.2f} cm³")
                
                results[f"image_{i}"] = {
                    'filepath': filepath,
                    'image': image,
                    'size': size,
                    'spacing': spacing,
                    'origin': origin,
                    'min_val': min_val,
                    'max_val': max_val,
                    'mean_val': mean_val,
                    'std_dev': std_dev,
                    'physical_volume': physical_volume
                }
                
            except Exception as e:
                print(f"Erreur chargement image: {e}")
        
        print(f"Analyse terminee pour {len(results)} image(s)")
        return results
        
    except ImportError as e:
        print(f"Modules ITK non disponibles: {e}")
        return None

def main():
    print("ITK/VTK Mini-Project - Traitement d'Images Medicales")
    
    directories = ["Data", "Output"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Dossier cree: {directory}")
    
    data_files = [
        "Data/case6_gre1.nrrd",
        "Data/case6_gre2.nrrd"
    ]
    
    print("Verification des fichiers de donnees:")
    for file_path in data_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"{file_path} ({size:,} bytes)")
        else:
            print(f"{file_path} - MANQUANT")
    
    if not check_python_environment():
        print("Probleme avec l'environnement Python")
        return False
    
    if not verify_imports():
        print("Certains modules ne sont pas disponibles")
        
        response = input("Voulez-vous installer les dependances ITK/VTK ? (o/n): ").lower()
        
        if response == 'o' or response == 'oui':
            if install_dependencies():
                print("Dependances installees avec succes!")
                
                if not verify_imports():
                    print("Probleme persistant avec les imports")
                    return False
            else:
                print("Erreur lors de l'installation")
                return False
    
    results = load_and_analyze_images()
    
    if results:
        print("Configuration et analyse terminees!")
        return True
    else:
        print("Echec de l'analyse des images")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
