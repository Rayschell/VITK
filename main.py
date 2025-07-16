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

def apply_filters(image_data):
    print("Application des filtres d'images")
    
    try:
        import itk
        
        filtered_results = {}
        
        for key, data in image_data.items():
            image = data['image']
            print(f"Filtrage {key}...")
            
            base_name = os.path.splitext(os.path.basename(data['filepath']))[0]
            
            # Conversion en 8-bit pour sauvegarde
            rescaler = itk.RescaleIntensityImageFilter.New(image)
            rescaler.SetOutputMinimum(0)
            rescaler.SetOutputMaximum(255)
            rescaler.Update()
            
            # Sauvegarde originale en PNG
            itk.imwrite(rescaler.GetOutput(), f"Output/{base_name}_original.png")
            
            # Filtrage Gaussien sur l'image float
            ImageType = type(image)
            FloatImageType = itk.Image[itk.F, 3]
            
            cast_to_float = itk.CastImageFilter[ImageType, FloatImageType].New()
            cast_to_float.SetInput(image)
            cast_to_float.Update()
            float_image = cast_to_float.GetOutput()
            
            gaussian_filter = itk.SmoothingRecursiveGaussianImageFilter[FloatImageType, FloatImageType].New()
            gaussian_filter.SetInput(float_image)
            gaussian_filter.SetSigma(2.0)
            gaussian_filter.Update()
            
            # Sauvegarde Gaussien
            gauss_rescaler = itk.RescaleIntensityImageFilter[FloatImageType, FloatImageType].New()
            gauss_rescaler.SetInput(gaussian_filter.GetOutput())
            gauss_rescaler.SetOutputMinimum(0)
            gauss_rescaler.SetOutputMaximum(255)
            gauss_rescaler.Update()
            
            UC3ImageType = itk.Image[itk.UC, 3]
            gauss_caster = itk.CastImageFilter[FloatImageType, UC3ImageType].New()
            gauss_caster.SetInput(gauss_rescaler.GetOutput())
            gauss_caster.Update()
            
            itk.imwrite(gauss_caster.GetOutput(), f"Output/{base_name}_gaussian.png")
            
            # Seuillage binaire
            threshold_filter = itk.BinaryThresholdImageFilter[FloatImageType, UC3ImageType].New()
            threshold_filter.SetInput(float_image)
            threshold_filter.SetLowerThreshold(data['mean_val'])
            threshold_filter.SetUpperThreshold(data['max_val'])
            threshold_filter.SetInsideValue(255)
            threshold_filter.SetOutsideValue(0)
            threshold_filter.Update()
            
            itk.imwrite(threshold_filter.GetOutput(), f"Output/{base_name}_threshold.png")
            
            filtered_results[key] = {
                'original': rescaler.GetOutput(),
                'gaussian': gauss_caster.GetOutput(),
                'threshold': threshold_filter.GetOutput()
            }
            
            print(f"Filtrage {key} termine")
        
        print(f"Filtrage termine pour {len(filtered_results)} image(s)")
        return filtered_results
        
    except Exception as e:
        print(f"Erreur lors du filtrage: {e}")
        return None

def apply_segmentation(image_data):
    print("Application de la segmentation")
    
    try:
        import itk
        
        segmentation_results = {}
        
        for key, data in image_data.items():
            image = data['image']
            print(f"Segmentation {key}...")
            
            base_name = os.path.splitext(os.path.basename(data['filepath']))[0]
            
            # Types d'images
            ImageType = type(image)
            FloatImageType = itk.Image[itk.F, 3]
            UC3ImageType = itk.Image[itk.UC, 3]
            
            # Conversion en float
            cast_to_float = itk.CastImageFilter[ImageType, FloatImageType].New()
            cast_to_float.SetInput(image)
            cast_to_float.Update()
            float_image = cast_to_float.GetOutput()
            
            # Seuillage binaire simple
            threshold_value = float(data['mean_val'] + data['std_dev'])
            
            binary_filter = itk.BinaryThresholdImageFilter[FloatImageType, UC3ImageType].New()
            binary_filter.SetInput(float_image)
            binary_filter.SetLowerThreshold(threshold_value)
            binary_filter.SetUpperThreshold(float(data['max_val']))
            binary_filter.SetInsideValue(255)
            binary_filter.SetOutsideValue(0)
            binary_filter.Update()
            
            itk.imwrite(binary_filter.GetOutput(), f"Output/{base_name}_binary_seg.png")
            
            # Seuillage adaptatif
            adaptive_lower = float(data['mean_val'])
            adaptive_upper = float(data['mean_val'] + 2 * data['std_dev'])
            
            adaptive_filter = itk.BinaryThresholdImageFilter[FloatImageType, UC3ImageType].New()
            adaptive_filter.SetInput(float_image)
            adaptive_filter.SetLowerThreshold(adaptive_lower)
            adaptive_filter.SetUpperThreshold(adaptive_upper)
            adaptive_filter.SetInsideValue(255)
            adaptive_filter.SetOutsideValue(0)
            adaptive_filter.Update()
            
            itk.imwrite(adaptive_filter.GetOutput(), f"Output/{base_name}_adaptive_seg.png")
            
            segmentation_results[key] = {
                'binary': binary_filter.GetOutput(),
                'adaptive': adaptive_filter.GetOutput()
            }
            
            print(f"Segmentation {key} terminee")
        
        print(f"Segmentation terminee pour {len(segmentation_results)} image(s)")
        return segmentation_results
        
    except Exception as e:
        print(f"Erreur lors de la segmentation: {e}")
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
        
        filters = apply_filters(results)
        if filters:
            print("Filtrage termine!")
            
            # Appliquer la segmentation
            segmentations = apply_segmentation(results)
            if segmentations:
                print("Segmentation termine!")
                return True
            else:
                print("Echec de la segmentation")
                return False
        else:
            print("Echec du filtrage")
            return False
    else:
        print("Echec de l'analyse des images")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
