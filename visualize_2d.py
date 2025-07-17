#!/usr/bin/env python3
"""
Script pour visualiser les coupes 2D des tumeurs
"""

from pathlib import Path
import sys
import json
import matplotlib.pyplot as plt
import itk
import numpy as np

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))


def load_nrrd_slice(image_path, slice_index=None):
    """Load a specific slice from a NRRD file"""
    image = itk.imread(str(image_path))
    array = itk.array_from_image(image)
    
    if slice_index is None:
        slice_index = array.shape[0] // 2  # Middle slice
    
    return array[slice_index], slice_index


def visualize_2d_comparison():
    # Setup paths
    project_root = Path(__file__).parent
    data_dir = project_root / "Data"
    results_dir = project_root / "results"
    
    # Input files
    image1_path = data_dir / "case6_gre1.nrrd"
    image2_path = results_dir / "registered_case6_gre2.nrrd"
    tumor1_mask_path = results_dir / "tumor_mask_scan1.nrrd"
    tumor2_mask_path = results_dir / "tumor_mask_scan2.nrrd"
    analysis_file = results_dir / "tumor_analysis.json"
    
    # Check if files exist
    missing_files = []
    for file_path in [image1_path, image2_path, tumor1_mask_path, tumor2_mask_path, analysis_file]:
        if not file_path.exists():
            missing_files.append(str(file_path))
    
    if missing_files:
        print("ERREUR: Fichiers manquants. Executez d'abord le pipeline principal :")
        print("   python main.py")
        return
    
    # Load analysis results
    with open(analysis_file, 'r') as f:
        analysis_results = json.load(f)
    
    # Load images and masks
    print("Chargement des images...")
    
    # Find a slice with tumor for better visualization
    tumor1_mask = itk.imread(str(tumor1_mask_path))
    tumor1_array = itk.array_from_image(tumor1_mask)
    
    # Find slice with maximum tumor area
    tumor_areas = [np.sum(tumor1_array[i] > 0) for i in range(tumor1_array.shape[0])]
    best_slice = np.argmax(tumor_areas)
    
    # Load all slices
    image1_slice, _ = load_nrrd_slice(image1_path, best_slice)
    image2_slice, _ = load_nrrd_slice(image2_path, best_slice)
    mask1_slice, _ = load_nrrd_slice(tumor1_mask_path, best_slice)
    mask2_slice, _ = load_nrrd_slice(tumor2_mask_path, best_slice)
    
    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Analyse Longitudinale de Tumeur - Coupe 2D', fontsize=16, fontweight='bold')
    
    # Scan initial
    axes[0, 0].imshow(image1_slice, cmap='gray', alpha=0.8)
    axes[0, 0].imshow(mask1_slice, cmap='Reds', alpha=0.5)
    axes[0, 0].set_title('Scan Initial + Tumeur (Rouge)', fontweight='bold')
    axes[0, 0].axis('off')
    
    # Scan de suivi
    axes[0, 1].imshow(image2_slice, cmap='gray', alpha=0.8)
    axes[0, 1].imshow(mask2_slice, cmap='Greens', alpha=0.5)
    axes[0, 1].set_title('Scan de Suivi + Tumeur (Vert)', fontweight='bold')
    axes[0, 1].axis('off')
    
    # Superposition des tumeurs
    axes[1, 0].imshow(image1_slice, cmap='gray', alpha=0.6)
    axes[1, 0].imshow(mask1_slice, cmap='Reds', alpha=0.6, label='Initial')
    axes[1, 0].imshow(mask2_slice, cmap='Greens', alpha=0.6, label='Suivi')
    axes[1, 0].set_title('Superposition des Tumeurs', fontweight='bold')
    axes[1, 0].axis('off')
    
    # Résultats quantitatifs
    axes[1, 1].axis('off')
    
    # Extract results
    volume1 = analysis_results['tumor1']['volume_mm3']
    volume2 = analysis_results['tumor2']['volume_mm3']
    volume_change = analysis_results['comparison']['volume_change_percent']
    dice_score = analysis_results['comparison']['dice_coefficient']
    hausdorff_dist = analysis_results['comparison']['hausdorff_distance_mm']
    
    # Text summary
    summary_text = f"""
RÉSULTATS DE L'ANALYSE

Volume Initial:
{volume1:,.0f} mm³

Volume de Suivi:
{volume2:,.0f} mm³

Changement de Volume:
{volume_change:+.1f}%

Qualité du Recalage:
• Dice: {dice_score:.3f}
• Hausdorff: {hausdorff_dist:.1f} mm

Coupe: {best_slice + 1}/{tumor1_array.shape[0]}

INTERPRÉTATION:
"""
    
    if abs(volume_change) < 2:
        interpretation = "Volume stable"
    elif volume_change > 10:
        interpretation = "Croissance significative"
    elif volume_change > 2:
        interpretation = "Croissance modérée"
    elif volume_change < -10:
        interpretation = "Réduction significative"
    else:
        interpretation = "Réduction modérée"
    
    summary_text += interpretation
    
    axes[1, 1].text(0.1, 0.9, summary_text, transform=axes[1, 1].transAxes, 
                   fontsize=11, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', alpha=0.6, label='Tumeur initiale'),
        Patch(facecolor='green', alpha=0.6, label='Tumeur suivi'),
        Patch(facecolor='yellow', alpha=0.6, label='Superposition')
    ]
    fig.legend(handles=legend_elements, loc='lower right', bbox_to_anchor=(0.98, 0.02))
    
    plt.tight_layout()
    
    # Save the figure
    output_path = results_dir / "tumor_comparison_2d.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Visualisation sauvegardee : {output_path}")
    
    # Show the plot
    print("Affichage de la visualisation 2D...")
    print("   Fermez la fenetre pour terminer.")
    plt.show()


if __name__ == "__main__":
    visualize_2d_comparison()
