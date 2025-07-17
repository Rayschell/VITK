#!/usr/bin/env python3

from pathlib import Path
import sys
import os

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from registration import ImageRegistration
from segmentation import TumorSegmentation
from analysis import TumorAnalysis
from visualization import TumorVisualization


def main():
    # Setup paths
    project_root = Path(__file__).parent
    data_dir = project_root / "Data"
    results_dir = project_root / "results"
    
    # Input files
    image1_path = data_dir / "case6_gre1.nrrd"
    image2_path = data_dir / "case6_gre2.nrrd"
    
    # Output files
    registered_image_path = results_dir / "registered_case6_gre2.nrrd"
    tumor1_mask_path = results_dir / "tumor_mask_scan1.nrrd"
    tumor2_mask_path = results_dir / "tumor_mask_scan2.nrrd"
    transform_path = results_dir / "registration_transform.tfm"
    analysis_report_path = results_dir / "tumor_analysis.json"
    screenshot_path = results_dir / "tumor_evolution_3d.png"
    
    # Create results directory
    results_dir.mkdir(exist_ok=True)
    
    print("Starting tumor evolution analysis pipeline...")
    
    # Step 1: Image Registration
    print("1. Performing image registration...")
    registrator = ImageRegistration()
    registered_image, transform = registrator.register_images(
        image1_path, image2_path, registered_image_path
    )
    
    if transform:
        registrator.save_transform(transform, transform_path)
        print(f"   Registration completed. Registered image saved to: {registered_image_path}")
    else:
        print("   Registration failed, using original image")
        registered_image_path = image2_path
    
    # Step 2: Tumor Segmentation
    print("2. Segmenting tumors...")
    segmenter = TumorSegmentation()
    
    # Segment tumor in first scan
    tumor1_mask = segmenter.segment_tumor_automatic(image1_path, tumor1_mask_path)
    print(f"   Tumor segmentation for scan 1 completed: {tumor1_mask_path}")
    
    # Segment tumor in registered second scan
    tumor2_mask = segmenter.segment_tumor_automatic(registered_image_path, tumor2_mask_path)
    print(f"   Tumor segmentation for scan 2 completed: {tumor2_mask_path}")
    
    # Step 3: Quantitative Analysis
    print("3. Performing quantitative analysis...")
    analyzer = TumorAnalysis()
    analysis_results = analyzer.compare_tumors(
        image1_path, tumor1_mask_path,
        registered_image_path, tumor2_mask_path
    )
    
    text_report_path = analyzer.save_analysis_report(analysis_results, analysis_report_path)
    print(f"   Analysis completed. Report saved to: {text_report_path}")
    
    # Generate timestamped execution report
    execution_report_path = analyzer.create_execution_report(analysis_results, results_dir)
    print(f"   Execution report saved to: {execution_report_path}")
    
    # Print key results
    volume1 = analysis_results['tumor1']['volume_mm3']
    volume2 = analysis_results['tumor2']['volume_mm3']
    volume_change = analysis_results['comparison']['volume_change_percent']
    dice_score = analysis_results['comparison']['dice_coefficient']
    
    print(f"   Key Results:")
    print(f"   - Initial tumor volume: {volume1:.1f} mm³")
    print(f"   - Follow-up tumor volume: {volume2:.1f} mm³")
    print(f"   - Volume change: {volume_change:.1f}%")
    print(f"   - Dice coefficient: {dice_score:.3f}")
    
    # Step 4: 3D Visualization (screenshot only)
    print("4. Creating 3D visualization...")
    try:
        visualizer = TumorVisualization()
        visualizer.visualize_tumor_evolution(
            image1_path, tumor1_mask_path, tumor2_mask_path, analysis_results
        )
        
        # Save screenshot only (avoid interactive mode)
        visualizer.save_screenshot(screenshot_path)
        print(f"   3D visualization screenshot saved to: {screenshot_path}")
        
    except Exception as e:
        print(f"   Visualization warning: {e}")
        print("   Continuing without interactive visualization...")
    
    print("Tumor evolution analysis pipeline completed successfully!")
    print(f"Results saved in: {results_dir}")
    print("Generated files:")
    for file_path in sorted(results_dir.glob("*")):
        print(f"  - {file_path.name}")


if __name__ == "__main__":
    main()