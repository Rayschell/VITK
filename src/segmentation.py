import itk
import numpy as np
from pathlib import Path
import scipy.ndimage as ndi


class TumorSegmentation:
    def __init__(self):
        self.PixelType = itk.F
        self.Dimension = 3
        self.ImageType = itk.Image[self.PixelType, self.Dimension]
        
    def load_image(self, image_path):
        reader = itk.ImageFileReader[self.ImageType].New()
        reader.SetFileName(str(image_path))
        reader.Update()
        return reader.GetOutput()
    
    def segment_tumor_automatic(self, image_path, output_path=None):
        image = self.load_image(image_path)
        
        # Convert to numpy for processing
        image_array = itk.GetArrayFromImage(image)
        
        # Preprocessing: Gaussian smoothing
        smoothed = ndi.gaussian_filter(image_array, sigma=1.5)
        
        # Step 1: Advanced brain extraction with skull stripping
        # Remove background (air/noise)
        background_mask = smoothed > np.percentile(smoothed[smoothed > 0], 5)
        
        # Detect skull using very high intensity threshold (top 1% of foreground)
        foreground_intensities = smoothed[background_mask]
        skull_threshold = np.percentile(foreground_intensities, 99)
        skull_mask = smoothed > skull_threshold
        
        # Brain tissue detection using histogram analysis
        # Brain tissue typically has intermediate intensities
        brain_low = np.percentile(foreground_intensities, 15)
        brain_high = np.percentile(foreground_intensities, 85)
        
        # Initial brain mask: intermediate intensities, no skull
        potential_brain = (smoothed >= brain_low) & (smoothed <= brain_high) & ~skull_mask
        
        # Morphological operations to get clean brain region
        from scipy.ndimage import binary_opening, binary_closing, binary_fill_holes, label, binary_erosion, binary_dilation
        
        # Clean up the brain mask
        potential_brain = binary_opening(potential_brain, structure=np.ones((3,3,3)))
        potential_brain = binary_closing(potential_brain, structure=np.ones((7,7,7)))
        potential_brain = binary_fill_holes(potential_brain)
        
        # Keep largest connected component (main brain)
        labeled_brain, num_brain = label(potential_brain)
        if num_brain > 0:
            brain_sizes = [np.sum(labeled_brain == i) for i in range(1, num_brain + 1)]
            largest_brain = np.argmax(brain_sizes) + 1
            brain_mask = labeled_brain == largest_brain
        else:
            print("Warning: No brain tissue detected")
            brain_mask = potential_brain
        
        # Step 2: Aggressive skull stripping - erode deeply into brain
        # Use multiple erosion steps to ensure we're well inside brain tissue
        inner_brain_mask = binary_erosion(brain_mask, structure=np.ones((9,9,9)))
        
        # If erosion is too aggressive, use smaller kernel
        if np.sum(inner_brain_mask) < 0.1 * np.sum(brain_mask):
            inner_brain_mask = binary_erosion(brain_mask, structure=np.ones((5,5,5)))
        
        # Final safety check
        if np.sum(inner_brain_mask) == 0:
            print("Warning: Brain mask too restrictive, using moderate erosion")
            inner_brain_mask = binary_erosion(brain_mask, structure=np.ones((3,3,3)))
        
        # Step 3: Tumor detection using statistical outlier analysis
        if np.sum(inner_brain_mask) == 0:
            print("Error: No valid brain tissue found")
            # Return empty mask
            mask_image = itk.GetImageFromArray(np.zeros_like(image_array, dtype=np.uint8))
            mask_image.SetOrigin(image.GetOrigin())
            mask_image.SetSpacing(image.GetSpacing())
            mask_image.SetDirection(image.GetDirection())
            
            if output_path:
                writer = itk.ImageFileWriter[itk.Image[itk.UC, self.Dimension]].New()
                writer.SetFileName(str(output_path))
                writer.SetInput(mask_image)
                writer.Update()
            return mask_image
        
        brain_intensities = smoothed[inner_brain_mask]
        brain_mean = np.mean(brain_intensities)
        brain_std = np.std(brain_intensities)
        
        # Very conservative tumor detection: 3 standard deviations above mean
        # This should only catch truly abnormal tissue
        tumor_threshold = brain_mean + 3.0 * brain_std
        
        # Also use top 0.5% of brain intensities as alternative threshold
        percentile_threshold = np.percentile(brain_intensities, 99.5)
        
        # Use the more conservative (higher) threshold
        final_threshold = max(tumor_threshold, percentile_threshold)
        
        print(f"Brain mean: {brain_mean:.1f}, std: {brain_std:.1f}")
        print(f"Tumor threshold: {final_threshold:.1f}")
        
        # Apply tumor detection only within deeply eroded brain mask
        tumor_candidates = (smoothed > final_threshold) & inner_brain_mask
        
        # Step 4: Very strict size and shape filtering
        labeled_tumors, num_features = label(tumor_candidates)
        
        # Realistic tumor size constraints
        min_tumor_size = 20    # Minimum meaningful tumor size
        max_tumor_size = 2000  # Maximum realistic tumor size
        final_mask = np.zeros_like(labeled_tumors, dtype=bool)
        
        valid_tumors = 0
        for i in range(1, num_features + 1):
            component = labeled_tumors == i
            component_size = np.sum(component)
            
            # Size filtering
            if not (min_tumor_size <= component_size <= max_tumor_size):
                continue
            
            # Shape analysis
            coords = np.where(component)
            if len(coords[0]) == 0:
                continue
                
            z_range = coords[0].max() - coords[0].min() + 1
            y_range = coords[1].max() - coords[1].min() + 1
            x_range = coords[2].max() - coords[2].min() + 1
            
            # Avoid very elongated structures (vessels, artifacts)
            ranges = [z_range, y_range, x_range]
            max_range = max(ranges)
            min_range = min(ranges)
            
            if max_range == 0:
                continue
                
            aspect_ratio = min_range / max_range
            
            # Stricter aspect ratio for tumor-like shapes
            if aspect_ratio < 0.4:
                continue
            
            # Additional compactness check
            # Tumors should be relatively compact
            bounding_volume = z_range * y_range * x_range
            compactness = component_size / bounding_volume if bounding_volume > 0 else 0
            
            if compactness < 0.1:  # Too sparse/elongated
                continue
            
            # Check if region is near brain center (avoid peripheral artifacts)
            z_center = np.mean(coords[0])
            y_center = np.mean(coords[1])
            x_center = np.mean(coords[2])
            
            # Get brain bounds
            brain_coords = np.where(brain_mask)
            brain_z_center = np.mean(brain_coords[0])
            brain_y_center = np.mean(brain_coords[1])
            brain_x_center = np.mean(brain_coords[2])
            
            # Distance from brain center
            distance_from_center = np.sqrt(
                (z_center - brain_z_center)**2 + 
                (y_center - brain_y_center)**2 + 
                (x_center - brain_x_center)**2
            )
            
            # Brain radius estimate
            brain_z_range = brain_coords[0].max() - brain_coords[0].min()
            brain_y_range = brain_coords[1].max() - brain_coords[1].min()
            brain_x_range = brain_coords[2].max() - brain_coords[2].min()
            brain_radius = np.mean([brain_z_range, brain_y_range, brain_x_range]) / 3
            
            # Reject regions too close to brain edge (likely artifacts)
            if distance_from_center > 0.7 * brain_radius:
                continue
            
            # If all checks pass, add to final mask
            final_mask |= component
            valid_tumors += 1
        
        print(f"Detected {valid_tumors} validated tumor regions")
        
        # Step 5: Final morphological refinement
        if np.sum(final_mask) > 0:
            # Light smoothing to remove jagged edges
            final_mask = binary_closing(final_mask, structure=np.ones((2,2,2)))
            final_mask = binary_opening(final_mask, structure=np.ones((2,2,2)))
        
        # Convert back to ITK image
        mask_image = itk.GetImageFromArray(final_mask.astype(np.uint8))
        mask_image.SetOrigin(image.GetOrigin())
        mask_image.SetSpacing(image.GetSpacing())
        mask_image.SetDirection(image.GetDirection())
        
        if output_path:
            writer = itk.ImageFileWriter[itk.Image[itk.UC, self.Dimension]].New()
            writer.SetFileName(str(output_path))
            writer.SetInput(mask_image)
            writer.Update()
        
        return mask_image
    
    def segment_tumor_region_growing(self, image_path, seed_points, output_path=None):
        image = self.load_image(image_path)
        
        # Region growing segmentation
        segmenter = itk.ConnectedThresholdImageFilter[self.ImageType, self.ImageType].New()
        segmenter.SetInput(image)
        
        # Set seed points
        for seed in seed_points:
            segmenter.AddSeed([int(seed[0]), int(seed[1]), int(seed[2])])
        
        # Automatic threshold estimation from seed region
        image_array = itk.GetArrayFromImage(image)
        seed_intensities = []
        for seed in seed_points:
            z, y, x = int(seed[2]), int(seed[1]), int(seed[0])
            if (0 <= z < image_array.shape[0] and 
                0 <= y < image_array.shape[1] and 
                0 <= x < image_array.shape[2]):
                seed_intensities.append(image_array[z, y, x])
        
        if seed_intensities:
            mean_intensity = np.mean(seed_intensities)
            std_intensity = np.std(seed_intensities)
            lower_threshold = mean_intensity - 2 * std_intensity
            upper_threshold = mean_intensity + 2 * std_intensity
        else:
            lower_threshold = 100
            upper_threshold = 1000
        
        segmenter.SetLower(lower_threshold)
        segmenter.SetUpper(upper_threshold)
        segmenter.SetReplaceValue(1)
        segmenter.Update()
        
        mask_image = segmenter.GetOutput()
        
        if output_path:
            writer = itk.ImageFileWriter[self.ImageType].New()
            writer.SetFileName(str(output_path))
            writer.SetInput(mask_image)
            writer.Update()
        
        return mask_image
    
    def refine_segmentation(self, mask_image, original_image):
        # Post-processing to refine segmentation
        mask_array = itk.GetArrayFromImage(mask_image)
        
        # Morphological closing to fill holes
        from scipy.ndimage import binary_closing, binary_fill_holes
        refined_mask = binary_closing(mask_array > 0, structure=np.ones((3,3,3)))
        refined_mask = binary_fill_holes(refined_mask)
        
        # Convert back to ITK
        refined_image = itk.GetImageFromArray(refined_mask.astype(np.uint8))
        refined_image.SetOrigin(mask_image.GetOrigin())
        refined_image.SetSpacing(mask_image.GetSpacing())
        refined_image.SetDirection(mask_image.GetDirection())
        
        return refined_image
