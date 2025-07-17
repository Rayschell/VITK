import itk
import numpy as np
from pathlib import Path
import json


class TumorAnalysis:
    def __init__(self):
        self.PixelType = itk.F
        self.Dimension = 3
        self.ImageType = itk.Image[self.PixelType, self.Dimension]
        
    def load_image(self, image_path):
        reader = itk.ImageFileReader[self.ImageType].New()
        reader.SetFileName(str(image_path))
        reader.Update()
        return reader.GetOutput()
    
    def load_mask(self, mask_path):
        reader = itk.ImageFileReader[itk.Image[itk.UC, self.Dimension]].New()
        reader.SetFileName(str(mask_path))
        reader.Update()
        return reader.GetOutput()
    
    def calculate_volume(self, mask_image):
        mask_array = itk.GetArrayFromImage(mask_image)
        spacing = mask_image.GetSpacing()
        voxel_volume = spacing[0] * spacing[1] * spacing[2]
        tumor_voxels = np.sum(mask_array > 0)
        volume_mm3 = tumor_voxels * voxel_volume
        return volume_mm3
    
    def calculate_intensity_statistics(self, image, mask_image):
        image_array = itk.GetArrayFromImage(image)
        mask_array = itk.GetArrayFromImage(mask_image)
        
        tumor_intensities = image_array[mask_array > 0]
        
        if len(tumor_intensities) == 0:
            return {
                'mean': 0,
                'std': 0,
                'min': 0,
                'max': 0,
                'median': 0
            }
        
        return {
            'mean': float(np.mean(tumor_intensities)),
            'std': float(np.std(tumor_intensities)),
            'min': float(np.min(tumor_intensities)),
            'max': float(np.max(tumor_intensities)),
            'median': float(np.median(tumor_intensities))
        }
    
    def calculate_dice_coefficient(self, mask1, mask2):
        array1 = itk.GetArrayFromImage(mask1)
        array2 = itk.GetArrayFromImage(mask2)
        
        intersection = np.sum((array1 > 0) & (array2 > 0))
        total = np.sum(array1 > 0) + np.sum(array2 > 0)
        
        if total == 0:
            return 1.0
        
        dice = 2.0 * intersection / total
        return float(dice)
    
    def calculate_hausdorff_distance(self, mask1, mask2):
        from scipy.spatial.distance import directed_hausdorff
        
        array1 = itk.GetArrayFromImage(mask1)
        array2 = itk.GetArrayFromImage(mask2)
        
        # Get surface points
        points1 = np.array(np.where(array1 > 0)).T
        points2 = np.array(np.where(array2 > 0)).T
        
        if len(points1) == 0 or len(points2) == 0:
            return float('inf')
        
        # Calculate Hausdorff distance
        hausdorff_1to2 = directed_hausdorff(points1, points2)[0]
        hausdorff_2to1 = directed_hausdorff(points2, points1)[0]
        
        spacing = mask1.GetSpacing()
        voxel_size = min(spacing)
        
        return float(max(hausdorff_1to2, hausdorff_2to1) * voxel_size)
    
    def compare_tumors(self, image1_path, mask1_path, image2_path, mask2_path):
        image1 = self.load_image(image1_path)
        mask1 = self.load_mask(mask1_path)
        image2 = self.load_image(image2_path)
        mask2 = self.load_mask(mask2_path)
        
        # Volume analysis
        volume1 = self.calculate_volume(mask1)
        volume2 = self.calculate_volume(mask2)
        volume_change = volume2 - volume1
        volume_change_percent = (volume_change / volume1 * 100) if volume1 > 0 else 0
        
        # Intensity analysis
        stats1 = self.calculate_intensity_statistics(image1, mask1)
        stats2 = self.calculate_intensity_statistics(image2, mask2)
        
        # Overlap analysis
        dice_score = self.calculate_dice_coefficient(mask1, mask2)
        
        try:
            hausdorff_dist = self.calculate_hausdorff_distance(mask1, mask2)
        except:
            hausdorff_dist = None
        
        analysis_results = {
            'tumor1': {
                'volume_mm3': volume1,
                'intensity_stats': stats1
            },
            'tumor2': {
                'volume_mm3': volume2,
                'intensity_stats': stats2
            },
            'comparison': {
                'volume_change_mm3': volume_change,
                'volume_change_percent': volume_change_percent,
                'dice_coefficient': dice_score,
                'hausdorff_distance_mm': hausdorff_dist,
                'intensity_change': {
                    'mean_change': stats2['mean'] - stats1['mean'],
                    'std_change': stats2['std'] - stats1['std']
                }
            }
        }
        
        return analysis_results
    
    def save_analysis_report(self, analysis_results, output_path):
        with open(output_path, 'w') as f:
            json.dump(analysis_results, f, indent=2)
        
        # Also create a readable text report
        text_report_path = output_path.with_suffix('.txt')
        with open(text_report_path, 'w') as f:
            f.write("TUMOR EVOLUTION ANALYSIS REPORT\n")
            f.write("=" * 40 + "\n\n")
            
            f.write(f"Initial Tumor Volume: {analysis_results['tumor1']['volume_mm3']:.2f} mm³\n")
            f.write(f"Follow-up Tumor Volume: {analysis_results['tumor2']['volume_mm3']:.2f} mm³\n")
            f.write(f"Volume Change: {analysis_results['comparison']['volume_change_mm3']:.2f} mm³ ")
            f.write(f"({analysis_results['comparison']['volume_change_percent']:.1f}%)\n\n")
            
            f.write(f"Dice Coefficient (Overlap): {analysis_results['comparison']['dice_coefficient']:.3f}\n")
            if analysis_results['comparison']['hausdorff_distance_mm']:
                f.write(f"Hausdorff Distance: {analysis_results['comparison']['hausdorff_distance_mm']:.2f} mm\n")
            
            f.write(f"\nIntensity Changes:\n")
            f.write(f"  Mean intensity change: {analysis_results['comparison']['intensity_change']['mean_change']:.2f}\n")
            f.write(f"  Std intensity change: {analysis_results['comparison']['intensity_change']['std_change']:.2f}\n")
        
        return text_report_path
    
    def create_execution_report(self, analysis_results, output_dir):
        """Create a timestamped execution report"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_path = output_dir / f"execution_report_{timestamp}.md"
        
        volume1 = analysis_results['tumor1']['volume_mm3']
        volume2 = analysis_results['tumor2']['volume_mm3']
        volume_change = analysis_results['comparison']['volume_change_percent']
        dice_score = analysis_results['comparison']['dice_coefficient']
        
        # Interpretation logic
        if abs(volume_change) < 5:
            growth_status = "stable"
        elif volume_change > 50:
            growth_status = "significant growth"
        elif volume_change > 10:
            growth_status = "moderate growth"
        elif volume_change < -50:
            growth_status = "significant reduction"
        elif volume_change < -10:
            growth_status = "moderate reduction"
        else:
            growth_status = "minimal change"
        
        with open(report_path, 'w') as f:
            f.write(f"# Tumor Analysis Execution Report\n\n")
            f.write(f"**Execution Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Quantitative Results\n\n")
            f.write(f"- **Initial Volume**: {volume1:.1f} mm³\n")
            f.write(f"- **Follow-up Volume**: {volume2:.1f} mm³\n")
            f.write(f"- **Volume Change**: {volume_change:+.1f}%\n")
            f.write(f"- **Dice Coefficient**: {dice_score:.3f}\n\n")
            
            f.write(f"## Interpretation\n\n")
            f.write(f"**Status**: {growth_status.title()}\n\n")
            
            if dice_score < 0.1:
                f.write("The very low Dice coefficient suggests the detected regions are largely different between scans. ")
                f.write("This could indicate:\n")
                f.write("- Significant tumor evolution\n")
                f.write("- New tumor locations\n")
                f.write("- Different tissue characteristics\n\n")
            elif dice_score > 0.7:
                f.write("High spatial overlap indicates good registration and similar tumor locations.\n\n")
            else:
                f.write("Moderate overlap suggests partial tumor persistence with some changes.\n\n")
            
            f.write("## Generated Files\n\n")
            f.write("This execution generated the following output files:\n")
            for file_path in sorted(output_dir.glob("*")):
                if file_path.name != report_path.name:  # Don't include self
                    f.write(f"- `{file_path.name}`\n")
            
            f.write(f"\n## Pipeline Configuration\n\n")
            f.write("- **Registration**: Versor Rigid 3D Transform\n")
            f.write("- **Segmentation**: Statistical outlier detection (3+ std dev)\n")
            f.write("- **Validation**: Size (20-2000 voxels), shape, and location filtering\n")
            f.write("- **Visualization**: Enhanced 3D rendering with interactive controls\n")
        
        return report_path
