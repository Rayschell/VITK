import os
import sys
import subprocess

# Import du module de recalage
try:
    import registration
except ImportError:
    registration = None

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

def apply_registration(image_data):
    """Applique le recalage automatique entre les deux volumes"""
    print("Application du recalage automatique")
    
    if not registration:
        print("Module de recalage non disponible")
        return image_data
    
    if len(image_data) < 2:
        print("Recalage impossible: moins de 2 images")
        return image_data
    
    try:
        import itk
        
        # Récupérer les deux images
        keys = list(image_data.keys())
        image1_key = keys[0] 
        image2_key = keys[1]
        
        image1 = image_data[image1_key]['image']
        image2 = image_data[image2_key]['image']
        
        print(f"Recalage: {image1_key} (fixe) <- {image2_key} (mobile)")
        
        # Effectuer le recalage rigide
        registered_image, transform, metric_value = registration.register_images(
            image1, image2, registration_type="rigid"
        )
        
        if registered_image is not None:
            print(f"Recalage reussi - Metrique finale: {metric_value:.6f}")
            
            # Mettre à jour les données avec l'image recalée
            image_data[image2_key]['image'] = registered_image
            image_data[image2_key]['registered'] = True
            image_data[image2_key]['transform'] = transform
            image_data[image2_key]['metric_value'] = metric_value
            
            # Sauvegarder l'image recalée
            base_name = os.path.splitext(os.path.basename(image_data[image2_key]['filepath']))[0]
            registered_filename = f"Output/{base_name}_registered.nrrd"
            
            # Conversion en type original pour sauvegarde
            OriginalType = type(image_data[image1_key]['image'])
            FloatImageType = itk.Image[itk.F, 3]
            
            caster = itk.CastImageFilter[FloatImageType, OriginalType].New()
            caster.SetInput(registered_image)
            caster.Update()
            
            itk.imwrite(caster.GetOutput(), registered_filename)
            print(f"Image recalee sauvegardee: {registered_filename}")
            
        else:
            print("Echec du recalage - conservation des images originales")
        
        return image_data
        
    except Exception as e:
        print(f"Erreur lors du recalage: {e}")
        return image_data

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

def apply_vtk_visualization(image_data):
    print("Application de la visualisation VTK")
    
    try:
        import vtk_visualizer
        
        vtk_results = {}
        
        for key, data in image_data.items():
            filepath = data['filepath']
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            
            print(f"Visualisation VTK {key}...")
            
            # Sauvegarde d'une capture d'ecran VTK
            screenshot_file = f"Output/{base_name}_vtk_screenshot.png"
            success = vtk_visualizer.save_vtk_screenshot(filepath, screenshot_file)
            
            if success:
                vtk_results[key] = {
                    'screenshot': screenshot_file,
                    'filepath': filepath
                }
                print(f"Capture VTK {key} terminee")
            else:
                print(f"Echec capture VTK {key}")
        
        print(f"Visualisation VTK terminee pour {len(vtk_results)} image(s)")
        return vtk_results
        
    except Exception as e:
        print(f"Erreur lors de la visualisation VTK: {e}")
        return None

def analyze_tumor_changes(image_data, segmentation_data):
    """Analyse les changements entre les tumeurs segmentées"""
    print("Analyse des changements tumoraux")
    
    if len(image_data) < 2 or len(segmentation_data) < 2:
        print("Analyse impossible: données insuffisantes")
        return None
    
    try:
        import itk
        import numpy as np
        
        keys = list(image_data.keys())
        key1, key2 = keys[0], keys[1]
        
        # Récupérer les segmentations
        seg1 = segmentation_data[key1]['adaptive']
        seg2 = segmentation_data[key2]['adaptive']
        
        # Calculer les volumes tumoraux
        def calculate_tumor_volume(segmentation, spacing):
            # Convertir en array numpy
            array = itk.array_from_image(segmentation)
            
            # Compter les voxels de tumeur (valeur 255)
            tumor_voxels = np.sum(array == 255)
            
            # Calculer le volume physique
            voxel_volume = spacing[0] * spacing[1] * spacing[2]
            tumor_volume = tumor_voxels * voxel_volume
            
            return tumor_volume, tumor_voxels
        
        vol1, voxels1 = calculate_tumor_volume(seg1, image_data[key1]['spacing'])
        vol2, voxels2 = calculate_tumor_volume(seg2, image_data[key2]['spacing'])
        
        # Calculer les changements
        volume_change = vol2 - vol1
        volume_change_percent = (volume_change / vol1) * 100 if vol1 > 0 else 0
        
        # Analyser les intensités dans les régions tumorales
        def analyze_tumor_intensity(image, segmentation):
            img_array = itk.array_from_image(image)
            seg_array = itk.array_from_image(segmentation)
            
            # Masquer les intensités de tumeur
            tumor_intensities = img_array[seg_array == 255]
            
            if len(tumor_intensities) > 0:
                return {
                    'mean': np.mean(tumor_intensities),
                    'std': np.std(tumor_intensities),
                    'min': np.min(tumor_intensities),
                    'max': np.max(tumor_intensities),
                    'median': np.median(tumor_intensities)
                }
            return None
        
        intensity1 = analyze_tumor_intensity(image_data[key1]['image'], seg1)
        intensity2 = analyze_tumor_intensity(image_data[key2]['image'], seg2)
        
        # Calculer les changements d'intensité
        intensity_change = None
        if intensity1 and intensity2:
            intensity_change = {
                'mean_change': intensity2['mean'] - intensity1['mean'],
                'mean_change_percent': ((intensity2['mean'] - intensity1['mean']) / intensity1['mean']) * 100 if intensity1['mean'] != 0 else 0
            }
        
        # Créer un rapport des changements
        changes_report = {
            'scan1': {
                'name': os.path.basename(image_data[key1]['filepath']),
                'volume_mm3': vol1,
                'volume_cm3': vol1 / 1000,
                'voxel_count': voxels1,
                'intensity': intensity1
            },
            'scan2': {
                'name': os.path.basename(image_data[key2]['filepath']),
                'volume_mm3': vol2,
                'volume_cm3': vol2 / 1000,
                'voxel_count': voxels2,
                'intensity': intensity2,
                'registered': image_data[key2].get('registered', False)
            },
            'changes': {
                'volume_change_mm3': volume_change,
                'volume_change_cm3': volume_change / 1000,
                'volume_change_percent': volume_change_percent,
                'intensity_change': intensity_change
            }
        }
        
        # Afficher le rapport
        print("\n=== RAPPORT D'ANALYSE DES CHANGEMENTS TUMORAUX ===")
        print(f"Scan 1 ({changes_report['scan1']['name']}):")
        print(f"  Volume: {changes_report['scan1']['volume_cm3']:.2f} cm³")
        print(f"  Voxels: {changes_report['scan1']['voxel_count']:,}")
        if intensity1:
            print(f"  Intensité moyenne: {intensity1['mean']:.2f} ± {intensity1['std']:.2f}")
        
        print(f"\nScan 2 ({changes_report['scan2']['name']}):")
        print(f"  Volume: {changes_report['scan2']['volume_cm3']:.2f} cm³")
        print(f"  Voxels: {changes_report['scan2']['voxel_count']:,}")
        if intensity2:
            print(f"  Intensité moyenne: {intensity2['mean']:.2f} ± {intensity2['std']:.2f}")
        print(f"  Recalé: {'Oui' if changes_report['scan2']['registered'] else 'Non'}")
        
        print(f"\nChangements:")
        print(f"  Volume: {changes_report['changes']['volume_change_cm3']:+.2f} cm³ ({changes_report['changes']['volume_change_percent']:+.1f}%)")
        if intensity_change:
            print(f"  Intensité moyenne: {intensity_change['mean_change']:+.2f} ({intensity_change['mean_change_percent']:+.1f}%)")
        
        # Interprétation
        print(f"\nInterprétation:")
        if volume_change_percent > 10:
            print("  → Augmentation significative du volume tumoral")
        elif volume_change_percent < -10:
            print("  → Diminution significative du volume tumoral")
        else:
            print("  → Volume tumoral relativement stable")
        
        # Sauvegarder le rapport
        report_file = "Output/tumor_changes_report.txt"
        with open(report_file, 'w') as f:
            f.write("=== RAPPORT D'ANALYSE DES CHANGEMENTS TUMORAUX ===\n\n")
            f.write(f"Scan 1 ({changes_report['scan1']['name']}):\n")
            f.write(f"  Volume: {changes_report['scan1']['volume_cm3']:.2f} cm³\n")
            f.write(f"  Voxels: {changes_report['scan1']['voxel_count']:,}\n")
            if intensity1:
                f.write(f"  Intensité moyenne: {intensity1['mean']:.2f} ± {intensity1['std']:.2f}\n")
            
            f.write(f"\nScan 2 ({changes_report['scan2']['name']}):\n")
            f.write(f"  Volume: {changes_report['scan2']['volume_cm3']:.2f} cm³\n")
            f.write(f"  Voxels: {changes_report['scan2']['voxel_count']:,}\n")
            if intensity2:
                f.write(f"  Intensité moyenne: {intensity2['mean']:.2f} ± {intensity2['std']:.2f}\n")
            f.write(f"  Recalé: {'Oui' if changes_report['scan2']['registered'] else 'Non'}\n")
            
            f.write(f"\nChangements:\n")
            f.write(f"  Volume: {changes_report['changes']['volume_change_cm3']:+.2f} cm³ ({changes_report['changes']['volume_change_percent']:+.1f}%)\n")
            if intensity_change:
                f.write(f"  Intensité moyenne: {intensity_change['mean_change']:+.2f} ({intensity_change['mean_change_percent']:+.1f}%)\n")
            
            f.write(f"\nInterprétation:\n")
            if volume_change_percent > 10:
                f.write("  → Augmentation significative du volume tumoral\n")
            elif volume_change_percent < -10:
                f.write("  → Diminution significative du volume tumoral\n")
            else:
                f.write("  → Volume tumoral relativement stable\n")
        
        print(f"\nRapport sauvegardé: {report_file}")
        return changes_report
        
    except Exception as e:
        print(f"Erreur lors de l'analyse des changements: {e}")
        return None

def launch_interactive_visualization(image_data):
    """Lance la visualisation interactive VTK"""
    print("Lancement de la visualisation interactive VTK...")
    
    try:
        import vtk_visualizer
        
        # Prendre la première image pour la démonstration
        first_key = list(image_data.keys())[0]
        filepath = image_data[first_key]['filepath']
        
        print(f"Visualisation interactive de: {os.path.basename(filepath)}")
        print("Controles VTK:")
        print("- Clic gauche + glisser: Rotation")
        print("- Clic droit + glisser: Zoom")
        print("- Clic milieu + glisser: Pan")
        print("- Touche 'q': Quitter")
        
        # Lancer la visualisation interactive
        vtk_visualizer.visualize_volume(filepath, mode="volume")
        
    except Exception as e:
        print(f"Erreur visualisation interactive: {e}")

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
        print("Installation automatique des dependances...")
        
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
        
        # Appliquer le recalage automatique
        registered_results = apply_registration(results)
        print("Recalage termine!")
        
        filters = apply_filters(registered_results)
        if filters:
            print("Filtrage termine!")
            
            # Appliquer la segmentation
            segmentations = apply_segmentation(registered_results)
            if segmentations:
                print("Segmentation termine!")
                
                # Analyser les changements tumoraux
                changes_report = analyze_tumor_changes(registered_results, segmentations)
                if changes_report:
                    print("Analyse des changements tumoraux terminee!")
                
                # Appliquer la visualisation VTK
                vtk_results = apply_vtk_visualization(registered_results)
                if vtk_results:
                    print("Visualisation VTK terminee!")
                    
                    print("\nPour visualisation interactive, utilisez:")
                    print("python -c \"from main import launch_interactive_visualization, load_and_analyze_images; launch_interactive_visualization(load_and_analyze_images())\"")
                    
                    return True
                else:
                    print("Echec de la visualisation VTK")
                    return False
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
